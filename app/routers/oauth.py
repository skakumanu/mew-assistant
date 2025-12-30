"""
OAuth authentication router using fastapi-sso
Proven, production-ready federated login implementation
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi_sso.sso.google import GoogleSSO
from fastapi_sso.sso.microsoft import MicrosoftSSO
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.models import FederatedIdentity, User, UserRole
from ..services.auth_service import AuthService
from ..utils.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["OAuth"])

# Initialize SSO providers
google_sso = GoogleSSO(
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    redirect_uri=f"{settings.BASE_URL}/auth/google/callback",
    allow_insecure_http=settings.ENVIRONMENT == "development",
)

microsoft_sso = MicrosoftSSO(
    client_id=settings.MICROSOFT_CLIENT_ID,
    client_secret=settings.MICROSOFT_CLIENT_SECRET,
    redirect_uri=f"{settings.BASE_URL}/auth/microsoft/callback",
    allow_insecure_http=settings.ENVIRONMENT == "development",
)


@router.get("/oauth/login")
async def oauth_login_page():
    """OAuth login page"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mew Assistant - Login</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont,
                    'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 400px;
                width: 100%;
                text-align: center;
            }
            h1 { color: #667eea; margin-bottom: 10px; font-size: 32px; }
            .subtitle { color: #666; margin-bottom: 30px; }
            .btn {
                width: 100%;
                padding: 15px;
                margin: 10px 0;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
                text-decoration: none;
            }
            .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
            .btn-google {
                background: white;
                color: #333;
                border: 2px solid #ddd;
            }
            .btn-microsoft {
                background: #00a4ef;
                color: white;
            }
            .btn-apple {
                background: #000;
                color: white;
            }
            .logo { font-size: 64px; margin-bottom: 20px; }
            .success { color: #4CAF50; margin-top: 20px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🐱</div>
            <h1>Mew Assistant</h1>
            <p class="subtitle">Sign in to manage your family schedule</p>

            <a href="/auth/google/authorize" class="btn btn-google">
                <span>Sign in with Google</span>
            </a>

            <a href="/auth/microsoft/authorize" class="btn btn-microsoft">
                <span>Sign in with Microsoft</span>
            </a>

            <div id="success-message" style="display: none;" class="success">
                ✓ Login successful! Redirecting...
            </div>
        </div>

        <script>
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('success') === 'true') {
                document.getElementById('success-message').style.display = 'block';
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/google/authorize")
async def google_authorize():
    """Initiate Google OAuth flow"""
    try:
        async with google_sso:
            return await google_sso.get_login_redirect()
    except Exception as e:
        logger.error(f"Google authorize error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Authorization failed: {str(e)}")


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    try:
        async with google_sso:
            user = await google_sso.verify_and_process(request)

        if not user:
            raise HTTPException(status_code=400, detail="Failed to authenticate with Google")

        logger.info(f"Google user authenticated: {user.email}")

        # Process federated identity
        federated_user = await process_federated_identity(
            provider="google",
            provider_user_id=user.id,
            email=user.email,
            full_name=user.display_name or user.email,
            db=db,
        )

        # Generate JWT token
        auth_service = AuthService(db)
        jwt_token = auth_service.create_access_token(data={"sub": federated_user.email})

        # Return success page with token
        html_content = f"""
        <html>
            <head><title>Login Successful</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h2 style="color: #4CAF50;">✓ Login Successful!</h2>
                <p>Welcome, {federated_user.full_name}!</p>
                <p>You can close this window and return to the app.</p>
                <script>
                    if (window.opener) {{
                        window.opener.postMessage({{
                            type: 'oauth_success',
                            token: '{jwt_token}'
                        }}, '*');
                    }}
                    localStorage.setItem('mew_token', '{jwt_token}');
                    setTimeout(() => {{
                        window.location.href = '/auth/oauth/login?success=true';
                    }}, 2000);
                </script>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OAuth authentication failed: {str(e)}")


@router.get("/microsoft/authorize")
async def microsoft_authorize():
    """Initiate Microsoft OAuth flow"""
    try:
        async with microsoft_sso:
            return await microsoft_sso.get_login_redirect()
    except Exception as e:
        logger.error(f"Microsoft authorize error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authorization failed: {str(e)}")


@router.get("/microsoft/callback")
async def microsoft_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Microsoft OAuth callback"""
    try:
        async with microsoft_sso:
            user = await microsoft_sso.verify_and_process(request)

        if not user:
            raise HTTPException(status_code=400, detail="Failed to authenticate with Microsoft")

        logger.info(f"Microsoft user authenticated: {user.email}")

        # Process federated identity
        federated_user = await process_federated_identity(
            provider="microsoft",
            provider_user_id=user.id,
            email=user.email,
            full_name=user.display_name or user.email,
            db=db,
        )

        # Generate JWT token
        auth_service = AuthService(db)
        jwt_token = auth_service.create_access_token(data={"sub": federated_user.email})

        # Return success page
        html_content = f"""
        <html>
            <head><title>Login Successful</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h2 style="color: #4CAF50;">✓ Login Successful!</h2>
                <p>Welcome, {federated_user.full_name}!</p>
                <p>You can close this window and return to the app.</p>
                <script>
                    if (window.opener) {{
                        window.opener.postMessage({{
                            type: 'oauth_success',
                            token: '{jwt_token}'
                        }}, '*');
                    }}
                    localStorage.setItem('mew_token', '{jwt_token}');
                    setTimeout(() => {{
                        window.location.href = '/auth/oauth/login?success=true';
                    }}, 2000);
                </script>
            </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OAuth authentication failed: {str(e)}")


async def process_federated_identity(
    provider: str, provider_user_id: str, email: str, full_name: str, db: Session
) -> User:
    """Process federated identity and create/update user"""

    # Check if federated identity exists
    fed_identity = (
        db.query(FederatedIdentity)
        .filter(
            FederatedIdentity.provider == provider,
            FederatedIdentity.provider_user_id == provider_user_id,
        )
        .first()
    )

    if fed_identity:
        # Return existing user
        return fed_identity.user

    # Check if user exists with this email
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Create new user
        user = User(
            email=email,
            full_name=full_name,
            role=UserRole.PARENT,  # Default role
            is_active=True,
        )
        db.add(user)
        db.flush()

    # Create federated identity link
    fed_identity = FederatedIdentity(
        user_id=user.id, provider=provider, provider_user_id=provider_user_id
    )
    db.add(fed_identity)
    db.commit()
    db.refresh(user)

    return user
