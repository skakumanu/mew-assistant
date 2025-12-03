"""OAuth2/OIDC Federated Authentication Service"""
from authlib.integrations.starlette_client import OAuth
from authlib.jose import jwt
from sqlalchemy.orm import Session
from typing import Optional, Dict
import httpx
from datetime import datetime, timedelta
import time

from app.database.models import User, OAuthProvider, UserRole
from app.utils.auth import create_access_token
from app.utils.config import settings

# Initialize OAuth client
oauth = OAuth()

def generate_apple_client_secret():
    """Generate Apple client secret JWT"""
    if not all([settings.APPLE_TEAM_ID, settings.APPLE_KEY_ID, settings.APPLE_PRIVATE_KEY]):
        return None
    
    headers = {
        'kid': settings.APPLE_KEY_ID,
        'alg': 'ES256'
    }
    
    payload = {
        'iss': settings.APPLE_TEAM_ID,
        'iat': int(time.time()),
        'exp': int(time.time()) + 86400 * 180,  # 6 months
        'aud': 'https://appleid.apple.com',
        'sub': settings.APPLE_CLIENT_ID
    }
    
    client_secret = jwt.encode(headers, payload, settings.APPLE_PRIVATE_KEY)
    return client_secret.decode('utf-8') if isinstance(client_secret, bytes) else client_secret

# Register OAuth providers
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

oauth.register(
    name='microsoft',
    client_id=settings.MICROSOFT_CLIENT_ID,
    client_secret=settings.MICROSOFT_CLIENT_SECRET,
    server_metadata_url='https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# Apple OAuth requires dynamic client secret generation
if settings.APPLE_CLIENT_ID:
    apple_client_secret = generate_apple_client_secret()
    if apple_client_secret:
        oauth.register(
            name='apple',
            client_id=settings.APPLE_CLIENT_ID,
            client_secret=apple_client_secret,
            server_metadata_url='https://appleid.apple.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'name email',
                'response_mode': 'form_post'  # Apple requires form_post
            }
        )

oauth.register(
    name='facebook',
    client_id=settings.FACEBOOK_CLIENT_ID,
    client_secret=settings.FACEBOOK_CLIENT_SECRET,
    authorize_url='https://www.facebook.com/v12.0/dialog/oauth',
    access_token_url='https://graph.facebook.com/v12.0/oauth/access_token',
    userinfo_endpoint='https://graph.facebook.com/me?fields=id,name,email',
    client_kwargs={'scope': 'email public_profile'}
)


class OAuthService:
    """Service for handling OAuth authentication"""
    
    @staticmethod
    async def get_authorization_url(provider: str, redirect_uri: str) -> str:
        """Get OAuth authorization URL for provider"""
        from urllib.parse import urlencode
        
        client = oauth.create_client(provider)
        
        # Generate authorization URL with redirect_uri
        metadata = await client.load_server_metadata()
        params = {
            'client_id': client.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': ' '.join(client.client_kwargs.get('scope', '').split()),
        }
        
        # Build authorization URL with proper URL encoding
        auth_url = metadata['authorization_endpoint']
        query_string = urlencode(params)
        return f"{auth_url}?{query_string}"
    
    @staticmethod
    async def handle_callback(
        provider: str, 
        code: str, 
        redirect_uri: str,
        db: Session
    ) -> Dict:
        """
        Handle OAuth callback and create/login user
        Returns user info and JWT token
        """
        client = oauth.create_client(provider)
        
        # Exchange code for token
        metadata = await client.load_server_metadata()
        async with httpx.AsyncClient() as http_client:
            token_response = await http_client.post(
                metadata['token_endpoint'],
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': redirect_uri,
                    'client_id': client.client_id,
                    'client_secret': client.client_secret,
                }
            )
            
            # Check for errors
            if token_response.status_code != 200:
                error_detail = token_response.text
                print(f"Token exchange error: {error_detail}")
                raise ValueError(f"Token exchange failed [{token_response.status_code}]: {error_detail}")
            
            try:
                token = token_response.json()
            except Exception as e:
                print(f"Failed to parse token response as JSON: {token_response.text}")
                raise ValueError(f"Invalid token response format: {str(e)}")
            
            # Log token response for debugging (remove in production)
            print(f"Token response status: {token_response.status_code}")
            print(f"Token response keys: {list(token.keys())}")
            print(f"Token response (sanitized): {', '.join(token.keys())}")
            
            # Verify access token exists
            if 'access_token' not in token:
                print(f"Missing access_token. Full response: {token}")
                # Check if it's an error response
                if 'error' in token:
                    raise ValueError(f"OAuth error: {token.get('error')} - {token.get('error_description', 'No description')}")
                raise ValueError(f"No access_token in response. Response keys: {list(token.keys())}")
        
        # Get user info from provider
        if provider == 'facebook':
            async with httpx.AsyncClient() as http_client:
                resp = await http_client.get(
                    'https://graph.facebook.com/me',
                    params={'fields': 'id,name,email', 'access_token': token['access_token']}
                )
                if resp.status_code != 200:
                    raise ValueError(f"Failed to get user info: {resp.text}")
                user_info = resp.json()
        else:
            # For OIDC providers, get userinfo from userinfo endpoint
            async with httpx.AsyncClient() as http_client:
                resp = await http_client.get(
                    metadata['userinfo_endpoint'],
                    headers={'Authorization': f"Bearer {token['access_token']}"}
                )
                if resp.status_code != 200:
                    raise ValueError(f"Failed to get user info: {resp.text}")
                user_info = resp.json()
        
        # Extract standard fields
        email = user_info.get('email')
        full_name = user_info.get('name') or f"{user_info.get('given_name', '')} {user_info.get('family_name', '')}".strip()
        provider_user_id = user_info.get('sub') or user_info.get('id')
        
        if not email:
            raise ValueError("Email not provided by OAuth provider")
        
        # Find or create user
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Create new user
            user = User(
                email=email,
                full_name=full_name,
                role=UserRole.PARENT,
                is_active=True,
                email_verified=True,  # OAuth providers verify email
                created_at=datetime.utcnow()
            )
            db.add(user)
            db.flush()  # Get user.id
        
        # Link OAuth provider to user
        oauth_link = db.query(OAuthProvider).filter(
            OAuthProvider.user_id == user.id,
            OAuthProvider.provider == provider
        ).first()
        
        if not oauth_link:
            oauth_link = OAuthProvider(
                user_id=user.id,
                provider=provider,
                provider_user_id=provider_user_id,
                access_token=token.get('access_token'),
                refresh_token=token.get('refresh_token'),
                token_expires_at=datetime.fromtimestamp(token['expires_at']) if 'expires_at' in token else None
            )
            db.add(oauth_link)
        else:
            # Update existing link
            oauth_link.access_token = token.get('access_token')
            oauth_link.refresh_token = token.get('refresh_token')
            oauth_link.token_expires_at = datetime.fromtimestamp(token['expires_at']) if 'expires_at' in token else None
            oauth_link.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        # Create JWT token
        access_token = create_access_token(data={
            "sub": str(user.id),  # Use user ID as subject, not email
            "user_id": user.id,
            "role": user.role
        })
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role
            },
            "access_token": access_token,
            "token_type": "bearer",
            "auth_method": "oauth",
            "provider": provider
        }
    
    @staticmethod
    async def link_provider(
        user_id: int,
        provider: str,
        code: str,
        redirect_uri: str,
        db: Session
    ) -> bool:
        """Link an OAuth provider to an existing user account"""
        client = oauth.create_client(provider)
        token = await client.authorize_access_token(code=code, redirect_uri=redirect_uri)
        
        if provider == 'facebook':
            async with httpx.AsyncClient() as http_client:
                resp = await http_client.get(
                    'https://graph.facebook.com/me',
                    params={'fields': 'id', 'access_token': token['access_token']}
                )
                user_info = resp.json()
        else:
            user_info = token.get('userinfo') or await client.userinfo(token=token)
        
        provider_user_id = user_info.get('sub') or user_info.get('id')
        
        # Check if already linked to another user
        existing = db.query(OAuthProvider).filter(
            OAuthProvider.provider == provider,
            OAuthProvider.provider_user_id == provider_user_id
        ).first()
        
        if existing and existing.user_id != user_id:
            raise ValueError("This OAuth account is already linked to another user")
        
        if existing:
            # Update token
            existing.access_token = token.get('access_token')
            existing.refresh_token = token.get('refresh_token')
            existing.token_expires_at = datetime.fromtimestamp(token['expires_at']) if 'expires_at' in token else None
            existing.updated_at = datetime.utcnow()
        else:
            # Create new link
            oauth_link = OAuthProvider(
                user_id=user_id,
                provider=provider,
                provider_user_id=provider_user_id,
                access_token=token.get('access_token'),
                refresh_token=token.get('refresh_token'),
                token_expires_at=datetime.fromtimestamp(token['expires_at']) if 'expires_at' in token else None
            )
            db.add(oauth_link)
        
        db.commit()
        return True
    
    @staticmethod
    def unlink_provider(user_id: int, provider: str, db: Session) -> bool:
        """Unlink an OAuth provider from user account"""
        oauth_link = db.query(OAuthProvider).filter(
            OAuthProvider.user_id == user_id,
            OAuthProvider.provider == provider
        ).first()
        
        if oauth_link:
            db.delete(oauth_link)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_linked_providers(user_id: int, db: Session) -> list:
        """Get all OAuth providers linked to a user"""
        providers = db.query(OAuthProvider).filter(
            OAuthProvider.user_id == user_id
        ).all()
        
        return [{
            "provider": p.provider,
            "linked_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat() if p.updated_at else None
        } for p in providers]
