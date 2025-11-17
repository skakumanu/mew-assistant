"""
Onboarding Router - Easy Registration Endpoints
All channels lead to simple, unified registration
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.services.onboarding_service import OnboardingService
from app.schemas.onboarding import (
    QuickRegistrationRequest,
    MagicLinkRequest,
    VoiceRegistrationRequest,
    SocialLoginRequest,
    FamilySetupRequest,
    OnboardingResponse
)
from app.utils.logger import get_logger

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])
logger = get_logger(__name__)


@router.post("/quick-register", response_model=OnboardingResponse)
async def quick_register(
    request: QuickRegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    🚀 Quick registration from any channel
    
    Examples:
    - Email: "user@example.com"
    - Phone: "+1234567890"
    - Voice: Device ID from Siri/Alexa
    
    No password needed! We'll send a magic link/code.
    """
    service = OnboardingService(db)
    
    result = await service.initiate_quick_registration(
        channel=request.channel,
        identifier=request.identifier,
        name=request.name,
        metadata=request.metadata
    )
    
    return OnboardingResponse(**result)


@router.post("/magic-link/verify", response_model=OnboardingResponse)
async def verify_magic_link(
    request: MagicLinkRequest,
    db: Session = Depends(get_db)
):
    """
    ✨ Complete registration with magic link/code
    
    User clicks link from email or enters code from SMS
    """
    service = OnboardingService(db)
    
    try:
        result = await service.complete_magic_link_registration(
            magic_token=request.magic_token,
            additional_info=request.additional_info
        )
        return OnboardingResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/voice-register", response_model=OnboardingResponse)
async def voice_register(
    request: VoiceRegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    🎤 Voice-initiated registration
    
    Example: "Hey Siri, set up Mew Assistant"
    
    Supports:
    - Apple Siri
    - Amazon Alexa
    - Tesla Grok
    - Google Assistant
    - Any voice platform
    """
    service = OnboardingService(db)
    
    result = await service.voice_initiated_registration(
        platform=request.platform,
        device_id=request.device_id,
        voice_print=request.voice_print,
        detected_language=request.language
    )
    
    return OnboardingResponse(**result)


@router.post("/social-login", response_model=OnboardingResponse)
async def social_login(
    request: SocialLoginRequest,
    db: Session = Depends(get_db)
):
    """
    👤 One-tap social login
    
    Supported providers:
    - Google (Sign in with Google)
    - Apple (Sign in with Apple)
    - Microsoft (Microsoft Account)
    - Facebook (optional)
    """
    service = OnboardingService(db)
    
    result = await service.social_login_registration(
        provider=request.provider,
        provider_user_id=request.provider_user_id,
        email=request.email,
        name=request.name,
        profile_data=request.profile_data
    )
    
    return OnboardingResponse(**result)


@router.post("/family-setup", response_model=OnboardingResponse)
async def family_setup(
    request: FamilySetupRequest,
    db: Session = Depends(get_db)
):
    """
    👨‍👩‍👧‍👦 Quick family setup (takes < 2 minutes)
    
    Minimal info needed:
    - Family name (optional, defaults to "My Family")
    - Timezone
    - Language preference
    """
    service = OnboardingService(db)
    
    result = await service.complete_family_setup(
        user_id=request.user_id,
        family_data=request.family_data
    )
    
    return OnboardingResponse(**result)


@router.get("/status/{user_id}")
async def onboarding_status(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    📊 Check onboarding completion status
    
    Returns what steps are remaining
    """
    from app.database.models import User
    from sqlalchemy import select
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": user.id,
        "onboarding_completed": user.onboarding_completed,
        "steps_remaining": _get_remaining_steps(user),
        "estimated_time": "2 minutes"
    }


def _get_remaining_steps(user) -> list:
    """Determine what setup steps remain"""
    steps = []
    
    if not user.email_verified and not user.phone_verified:
        steps.append("verify_contact")
    
    if not user.family_id:
        steps.append("family_setup")
    
    if not user.timezone:
        steps.append("set_timezone")
    
    return steps
