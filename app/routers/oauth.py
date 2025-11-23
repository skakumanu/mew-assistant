"""OAuth2/OIDC Authentication Router"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.connection import get_db
from app.services.oauth_service import OAuthService
from app.utils.auth import get_current_user
from app.database.models import User

router = APIRouter(prefix="/auth/oauth", tags=["OAuth Authentication"])


class OAuthLinkRequest(BaseModel):
    """Request to link OAuth provider"""
    provider: str
    code: str
    redirect_uri: str


@router.get("/providers")
async def get_available_providers():
    """Get list of available OAuth providers"""
    return {
        "providers": [
            {
                "name": "google",
                "display_name": "Google",
                "icon": "google",
                "scopes": ["openid", "email", "profile"]
            },
            {
                "name": "microsoft",
                "display_name": "Microsoft",
                "icon": "microsoft",
                "scopes": ["openid", "email", "profile"]
            },
            {
                "name": "apple",
                "display_name": "Apple",
                "icon": "apple",
                "scopes": ["name", "email"]
            },
            {
                "name": "facebook",
                "display_name": "Facebook",
                "icon": "facebook",
                "scopes": ["email", "public_profile"]
            }
        ]
    }


@router.get("/login/{provider}")
async def oauth_login(
    provider: str,
    request: Request,
    redirect_uri: str = None
):
    """
    Initiate OAuth login flow
    
    - **provider**: OAuth provider (google, microsoft, apple, facebook)
    - **redirect_uri**: Optional custom redirect URI
    """
    if provider not in ['google', 'microsoft', 'apple', 'facebook']:
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")
    
    if not redirect_uri:
        redirect_uri = str(request.url_for('oauth_callback', provider=provider))
    
    try:
        auth_url = await OAuthService.get_authorization_url(provider, redirect_uri)
        return RedirectResponse(auth_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth initialization failed: {str(e)}")


@router.get("/callback/{provider}", name="oauth_callback")
async def oauth_callback(
    provider: str,
    code: str,
    request: Request,
    db: Session = Depends(get_db),
    state: str = None
):
    """
    Handle OAuth callback
    
    This endpoint is called by the OAuth provider after user authorization
    """
    if provider not in ['google', 'microsoft', 'apple', 'facebook']:
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")
    
    redirect_uri = str(request.url_for('oauth_callback', provider=provider))
    
    try:
        result = await OAuthService.handle_callback(
            provider=provider,
            code=code,
            redirect_uri=redirect_uri,
            db=db
        )
        
        # In production, redirect to frontend with token in query params or set cookie
        return {
            "message": "Authentication successful",
            **result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth authentication failed: {str(e)}")


@router.post("/link")
async def link_oauth_provider(
    request: OAuthLinkRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Link an OAuth provider to current user account
    
    Requires authentication. Allows users to link multiple OAuth providers
    to their account for convenient login.
    """
    if request.provider not in ['google', 'microsoft', 'apple', 'facebook']:
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")
    
    try:
        success = await OAuthService.link_provider(
            user_id=current_user.id,
            provider=request.provider,
            code=request.code,
            redirect_uri=request.redirect_uri,
            db=db
        )
        
        if success:
            return {
                "message": f"{request.provider.title()} account linked successfully",
                "provider": request.provider
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to link provider")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to link provider: {str(e)}")


@router.delete("/unlink/{provider}")
async def unlink_oauth_provider(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unlink an OAuth provider from current user account
    
    Removes the link between user account and OAuth provider.
    User can still login with password or other linked providers.
    """
    if provider not in ['google', 'microsoft', 'apple', 'facebook']:
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")
    
    success = OAuthService.unlink_provider(current_user.id, provider, db)
    
    if success:
        return {
            "message": f"{provider.title()} account unlinked successfully",
            "provider": provider
        }
    else:
        raise HTTPException(status_code=404, detail=f"{provider.title()} account not linked")


@router.get("/linked")
async def get_linked_providers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all OAuth providers linked to current user account
    """
    providers = OAuthService.get_linked_providers(current_user.id, db)
    
    return {
        "user_id": current_user.id,
        "linked_providers": providers
    }
