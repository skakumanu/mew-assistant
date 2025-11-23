"""OAuth2/OIDC Federated Authentication Service"""
from authlib.integrations.starlette_client import OAuth
from authlib.jose import jwt
from sqlalchemy.orm import Session
from typing import Optional, Dict
import httpx
from datetime import datetime

from app.database.models import User, OAuthProvider
from app.utils.auth import create_access_token
from app.utils.config import settings

# Initialize OAuth client
oauth = OAuth()

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

oauth.register(
    name='apple',
    client_id=settings.APPLE_CLIENT_ID,
    client_secret=settings.APPLE_CLIENT_SECRET,
    server_metadata_url='https://appleid.apple.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'name email'}
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
        client = oauth.create_client(provider)
        return await client.authorize_redirect_url(redirect_uri)
    
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
        token = await client.authorize_access_token(code=code, redirect_uri=redirect_uri)
        
        # Get user info from provider
        if provider == 'facebook':
            async with httpx.AsyncClient() as http_client:
                resp = await http_client.get(
                    'https://graph.facebook.com/me',
                    params={'fields': 'id,name,email', 'access_token': token['access_token']}
                )
                user_info = resp.json()
        else:
            user_info = token.get('userinfo') or await client.userinfo(token=token)
        
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
                role='parent',
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
            "sub": user.email,
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
