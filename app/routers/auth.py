"""
What's left once sign-in itself moved to WorkOS AuthKit
(app/routers/oauth_workos.py): a "who am I" / profile-update pair for any
future API client, and the CAPTCHA endpoints (unrelated to password auth,
generic bot-protection utility).
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User
from app.middleware.bot_protection import captcha_verifier
from app.schemas.auth import UserResponse, UserUpdate
from app.utils.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the current user's profile."""
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.phone is not None:
        current_user.phone = user_update.phone
    if user_update.timezone is not None:
        current_user.timezone = user_update.timezone

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return current_user


@router.get("/captcha/challenge")
async def get_captcha_challenge(user_id: str = None):
    """Generate a CAPTCHA challenge for critical operations"""
    challenge = captcha_verifier.generate_challenge(user_id or "anonymous")
    return challenge


@router.post("/captcha/verify")
async def verify_captcha(challenge_id: str, response: str):
    """Verify CAPTCHA response"""
    is_valid = captcha_verifier.verify_response(challenge_id, response)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired CAPTCHA"
        )
    return {"verified": True}
