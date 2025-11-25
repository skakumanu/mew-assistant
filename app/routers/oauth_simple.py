"""
Simple, bulletproof OAuth 2.0 implementation
No complex libraries - just direct HTTP calls
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
import logging
import httpx
from urllib.parse import urlencode, parse_qs

from ..database.connection import get_db
from ..database.models import User, FederatedIdentity, UserRole
from ..utils.config import settings
from ..utils.auth import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["OAuth Simple"])

# OAuth configurations
GOOGLE_CONFIG = {
    'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
    'token_url': 'https://oauth2.googleapis.com/token',
    'userinfo_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
    'client_id': settings.GOOGLE_CLIENT_ID,
    'client_secret': settings.GOOGLE_CLIENT_SECRET,
    'scope': 'openid email profile'
}

MICROSOFT_CONFIG = {
    'auth_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
    'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
    'userinfo_url': 'https://graph.microsoft.com/v1.0/me',
    'client_id': settings.MICROSOFT_CLIENT_ID,
    'client_secret': settings.MICROSOFT_CLIENT_SECRET,
    'scope': 'openid email profile User.Read'
}


@router.get("/simple/login")
async def simple_login_page():
    """Simple OAuth login page"""
    base_url = settings.BASE_URL or "http://localhost:8888"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mew Assistant - Login</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }}
            .container {{
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 400px;
                width: 100%;
            }}
            h1 {{
                color: #667eea;
                margin-bottom: 10px;
                font-size: 32px;
                text-align: center;
            }}
            .subtitle {{
                color: #666;
                text-align: center;
                margin-bottom: 30px;
                font-size: 16px;
            }}
            .btn {{
                width: 100%;
                padding: 15px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                transition: transform 0.2s, box-shadow 0.2s;
                text-decoration: none;
                color: white;
            }}
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }}
            .btn-google {{
                background: #4285f4;
            }}
            .btn-microsoft {{
                background: #00a4ef;
            }}
            .icon {{
                width: 20px;
                height: 20px;
                background: white;
                border-radius: 3px;
                padding: 2px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🐱 Mew Assistant</h1>
            <p class="subtitle">Your AI-powered family assistant</p>
            <a href="{base_url}/auth/simple/google" class="btn btn-google">
                <span class="icon">G</span>
                Sign in with Google
            </a>
            <a href="{base_url}/auth/simple/microsoft" class="btn btn-microsoft">
                <span class="icon">M</span>
                Sign in with Microsoft
            </a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/simple/google")
async def google_login():
    """Initiate Google OAuth flow"""
    base_url = settings.BASE_URL or "http://localhost:8888"
    redirect_uri = f"{base_url}/auth/simple/google/callback"
    
    params = {
        'client_id': GOOGLE_CONFIG['client_id'],
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': GOOGLE_CONFIG['scope'],
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    auth_url = f"{GOOGLE_CONFIG['auth_url']}?{urlencode(params)}"
    logger.info(f"Redirecting to Google OAuth: {auth_url}")
    return RedirectResponse(url=auth_url)


@router.get("/simple/google/callback")
async def google_callback(request: Request, code: str = None, error: str = None, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    try:
        if error:
            raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
        
        if not code:
            raise HTTPException(status_code=400, detail="No authorization code received")
        
        logger.info(f"Received authorization code: {code[:10]}...")
        
        # Exchange code for token
        base_url = settings.BASE_URL or "http://localhost:8888"
        redirect_uri = f"{base_url}/auth/simple/google/callback"
        
        token_data = {
            'client_id': GOOGLE_CONFIG['client_id'],
            'client_secret': GOOGLE_CONFIG['client_secret'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        
        logger.info(f"Exchanging code for token at {GOOGLE_CONFIG['token_url']}")
        
        async with httpx.AsyncClient() as client:
            # Get access token
            token_response = await client.post(
                GOOGLE_CONFIG['token_url'],
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            logger.info(f"Token response status: {token_response.status_code}")
            logger.info(f"Token response: {token_response.text[:200]}")
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to get access token: {token_response.text}"
                )
            
            token_json = token_response.json()
            access_token = token_json.get('access_token')
            
            if not access_token:
                raise HTTPException(
                    status_code=400,
                    detail=f"No access token in response: {token_json}"
                )
            
            logger.info("Successfully obtained access token")
            
            # Get user info
            userinfo_response = await client.get(
                GOOGLE_CONFIG['userinfo_url'],
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if userinfo_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to get user info: {userinfo_response.text}"
                )
            
            user_info = userinfo_response.json()
            logger.info(f"User info retrieved: {user_info.get('email')}")
        
        # Find or create user
        email = user_info.get('email')
        if not email:
            raise HTTPException(status_code=400, detail="No email in user info")
        
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Create new user
            user = User(
                email=email,
                full_name=user_info.get('name', email.split('@')[0]),
                role=UserRole.PARENT,
                is_active=True
            )
            db.add(user)
            db.flush()
            
            # Create federated identity
            fed_identity = FederatedIdentity(
                user_id=user.id,
                provider='google',
                provider_user_id=user_info.get('sub') or user_info.get('id'),
                email=email
            )
            db.add(fed_identity)
            db.flush()
            db.refresh(fed_identity)
            db.commit()
            logger.info(f"Created new user: {email}")
        else:
            # Update federated identity if needed
            fed_identity = db.query(FederatedIdentity).filter(
                FederatedIdentity.user_id == user.id,
                FederatedIdentity.provider == 'google'
            ).first()
            
            if not fed_identity:
                fed_identity = FederatedIdentity(
                    user_id=user.id,
                    provider='google',
                    provider_user_id=user_info.get('sub') or user_info.get('id'),
                    email=email
                )
                db.add(fed_identity)
                db.flush()
                db.refresh(fed_identity)
                db.commit()
            
            logger.info(f"User logged in: {email}")
        
        # Generate JWT token
        # auth_service = AuthService(db)
        token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
        jwt_token = create_access_token(token_data)
        
        # Return success page with token
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Successful</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }}
                .container {{
                    background: white;
                    border-radius: 20px;
                    padding: 40px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    max-width: 600px;
                    width: 100%;
                    text-align: center;
                }}
                h1 {{ color: #667eea; margin-bottom: 20px; }}
                .success {{ color: #10b981; font-size: 64px; margin-bottom: 20px; }}
                .token {{ 
                    background: #f3f4f6;
                    padding: 15px;
                    border-radius: 10px;
                    word-break: break-all;
                    margin: 20px 0;
                    font-family: monospace;
                    font-size: 12px;
                }}
                .copy-btn {{
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 600;
                }}
                .copy-btn:hover {{ background: #5568d3; }}
                .info {{ color: #666; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">✅</div>
                <h1>Login Successful!</h1>
                <p>Welcome, {user.full_name}!</p>
                <p class="info">Your access token (save this):</p>
                <div class="token" id="token">{jwt_token}</div>
                <button class="copy-btn" onclick="copyToken()">Copy Token</button>
                <p class="info" style="margin-top: 20px;">
                    You can now use this token to access the Mew Assistant API.
                </p>
            </div>
            <script>
                function copyToken() {{
                    const token = document.getElementById('token').textContent;
                    navigator.clipboard.writeText(token).then(() => {{
                        alert('Token copied to clipboard!');
                    }});
                }}
                // Auto-save to localStorage
                localStorage.setItem('mew_token', '{jwt_token}');
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OAuth authentication failed: {str(e)}")


@router.get("/simple/microsoft")
async def microsoft_login():
    """Initiate Microsoft OAuth flow"""
    base_url = settings.BASE_URL or "http://localhost:8888"
    redirect_uri = f"{base_url}/auth/simple/microsoft/callback"
    
    params = {
        'client_id': MICROSOFT_CONFIG['client_id'],
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': MICROSOFT_CONFIG['scope'],
        'response_mode': 'query'
    }
    
    auth_url = f"{MICROSOFT_CONFIG['auth_url']}?{urlencode(params)}"
    logger.info(f"Redirecting to Microsoft OAuth: {auth_url}")
    return RedirectResponse(url=auth_url)


@router.get("/simple/microsoft/callback")
async def microsoft_callback(request: Request, code: str = None, error: str = None, db: Session = Depends(get_db)):
    """Handle Microsoft OAuth callback"""
    try:
        if error:
            raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
        
        if not code:
            raise HTTPException(status_code=400, detail="No authorization code received")
        
        logger.info(f"Received authorization code: {code[:10]}...")
        
        # Exchange code for token
        base_url = settings.BASE_URL or "http://localhost:8888"
        redirect_uri = f"{base_url}/auth/simple/microsoft/callback"
        
        token_data = {
            'client_id': MICROSOFT_CONFIG['client_id'],
            'client_secret': MICROSOFT_CONFIG['client_secret'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        
        logger.info(f"Exchanging code for token at {MICROSOFT_CONFIG['token_url']}")
        
        async with httpx.AsyncClient() as client:
            # Get access token
            token_response = await client.post(
                MICROSOFT_CONFIG['token_url'],
                data=token_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            logger.info(f"Token response status: {token_response.status_code}")
            logger.info(f"Token response: {token_response.text[:200]}")
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to get access token: {token_response.text}"
                )
            
            token_json = token_response.json()
            access_token = token_json.get('access_token')
            
            if not access_token:
                raise HTTPException(
                    status_code=400,
                    detail=f"No access token in response: {token_json}"
                )
            
            logger.info("Successfully obtained access token")
            
            # Get user info
            userinfo_response = await client.get(
                MICROSOFT_CONFIG['userinfo_url'],
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if userinfo_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to get user info: {userinfo_response.text}"
                )
            
            user_info = userinfo_response.json()
            logger.info(f"User info retrieved: {user_info.get('mail') or user_info.get('userPrincipalName')}")
        
        # Find or create user
        email = user_info.get('mail') or user_info.get('userPrincipalName')
        if not email:
            raise HTTPException(status_code=400, detail="No email in user info")
        
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            # Create new user
            user = User(
                email=email,
                full_name=user_info.get('displayName', email.split('@')[0]),
                role='PARENT',
                is_active=True
            )
            db.add(user)
            db.flush()
            
            # Create federated identity
            fed_identity = FederatedIdentity(
                user_id=user.id,
                provider='microsoft',
                provider_user_id=user_info.get('id'),
                email=email
            )
            db.add(fed_identity)
            db.commit()
            logger.info(f"Created new user: {email}")
        else:
            # Update federated identity if needed
            fed_identity = db.query(FederatedIdentity).filter(
                FederatedIdentity.user_id == user.id,
                FederatedIdentity.provider == 'microsoft'
            ).first()
            
            if not fed_identity:
                fed_identity = FederatedIdentity(
                    user_id=user.id,
                    provider='microsoft',
                    provider_user_id=user_info.get('id'),
                    email=email
                )
                db.add(fed_identity)
                db.commit()
            
            logger.info(f"User logged in: {email}")
        
        # Generate JWT token
        # auth_service = AuthService(db)
        token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
        jwt_token = create_access_token(token_data)
        
        # Return success page with token
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Successful</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 20px;
                }}
                .container {{
                    background: white;
                    border-radius: 20px;
                    padding: 40px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    max-width: 600px;
                    width: 100%;
                    text-align: center;
                }}
                h1 {{ color: #667eea; margin-bottom: 20px; }}
                .success {{ color: #10b981; font-size: 64px; margin-bottom: 20px; }}
                .token {{ 
                    background: #f3f4f6;
                    padding: 15px;
                    border-radius: 10px;
                    word-break: break-all;
                    margin: 20px 0;
                    font-family: monospace;
                    font-size: 12px;
                }}
                .copy-btn {{
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 600;
                }}
                .copy-btn:hover {{ background: #5568d3; }}
                .info {{ color: #666; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">✅</div>
                <h1>Login Successful!</h1>
                <p>Welcome, {user.full_name}!</p>
                <p class="info">Your access token (save this):</p>
                <div class="token" id="token">{jwt_token}</div>
                <button class="copy-btn" onclick="copyToken()">Copy Token</button>
                <p class="info" style="margin-top: 20px;">
                    You can now use this token to access the Mew Assistant API.
                </p>
            </div>
            <script>
                function copyToken() {{
                    const token = document.getElementById('token').textContent;
                    navigator.clipboard.writeText(token).then(() => {{
                        alert('Token copied to clipboard!');
                    }});
                }}
                // Auto-save to localStorage
                localStorage.setItem('mew_token', '{jwt_token}');
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OAuth authentication failed: {str(e)}")
