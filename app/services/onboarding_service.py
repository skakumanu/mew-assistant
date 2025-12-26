"""
Onboarding Service - Unified Easy Registration
Handles seamless registration across all channels with minimal friction
"""

import re
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Family, User, UserRole
from app.utils.logger import get_logger
from app.utils.notifications import NotificationService

logger = get_logger(__name__)


class OnboardingService:
    """
    Unified onboarding service for seamless registration
    - One-tap social login
    - Magic link email/SMS
    - Voice-initiated registration
    - No password required initially
    """

    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService()

    async def initiate_quick_registration(
        self,
        channel: str,
        identifier: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Start quick registration from any channel

        Args:
            channel: email, phone, voice, siri, alexa, grok, etc.
            identifier: email address, phone number, or device ID
            name: Optional user name
            metadata: Additional context (language, timezone, etc.)
        """
        logger.info(f"Quick registration initiated via {channel}: {identifier}")

        # Check if user already exists
        existing_user = await self._find_existing_user(identifier)
        if existing_user:
            return {
                "status": "existing_user",
                "user_id": existing_user.id,
                "message": f"Welcome back! Found your account via {channel}",
                "requires_setup": not existing_user.onboarding_completed,
            }

        # Generate magic token (valid for 15 minutes)
        magic_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=15)

        # Create pending registration
        pending = {
            "channel": channel,
            "identifier": identifier,
            "name": name,
            "magic_token": magic_token,
            "expires_at": expires_at,
            "metadata": metadata or {},
        }

        # Send magic link/code based on channel
        if channel in ["email", "gmail", "outlook"]:
            await self._send_magic_link_email(identifier, magic_token, name)
        elif channel in ["phone", "sms", "whatsapp"]:
            await self._send_magic_code_sms(identifier, magic_token)
        elif channel in ["voice", "siri", "alexa", "grok"]:
            await self._send_voice_confirmation(identifier, magic_token, metadata)

        return {
            "status": "pending",
            "message": f"Check your {channel} for a quick sign-in link",
            "magic_token": magic_token,
            "expires_in": 900,  # 15 minutes
        }

    async def complete_magic_link_registration(
        self, magic_token: str, additional_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete registration using magic link/code
        """
        # In production, store pending registrations in Redis/cache
        # For now, simplified flow

        # Create user account
        user = await self._create_quick_user(magic_token, additional_info)

        return {
            "status": "success",
            "user_id": user.id,
            "message": "Welcome to Mew! Let's set up your family schedule.",
            "next_step": "family_setup",
            "access_token": await self._generate_access_token(user),
        }

    async def voice_initiated_registration(
        self,
        platform: str,
        device_id: str,
        voice_print: Optional[str] = None,
        detected_language: str = "en",
    ) -> Dict[str, Any]:
        """
        Register via voice command
        Example: "Hey Siri, set up Mew Assistant"
        """
        logger.info(f"Voice registration from {platform}, device: {device_id}")

        # Check if device is already registered
        existing = await self._find_user_by_device(device_id)
        if existing:
            return {
                "status": "recognized",
                "user_id": existing.id,
                "voice_response": self._get_welcome_back_message(detected_language),
            }

        # Generate voice confirmation code
        voice_code = self._generate_voice_friendly_code()

        return {
            "status": "pending_confirmation",
            "voice_code": voice_code,
            "voice_response": self._get_registration_prompt(
                voice_code, detected_language
            ),
            "platform": platform,
            "device_id": device_id,
        }

    async def social_login_registration(
        self,
        provider: str,
        provider_user_id: str,
        email: str,
        name: str,
        profile_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        One-tap social login (Google, Apple, Microsoft)
        """
        logger.info(f"Social login via {provider}: {email}")

        # Check existing user
        existing_user = await self._find_existing_user(email)
        if existing_user:
            # Link social account
            await self._link_social_account(
                existing_user.id, provider, provider_user_id
            )
            return {
                "status": "linked",
                "user_id": existing_user.id,
                "message": f"Connected your {provider} account!",
            }

        # Create new user from social login
        user = User(
            email=email,
            full_name=name,
            role=UserRole.PARENT,
            is_active=True,
            email_verified=True,  # Trust social provider verification
            auth_provider=provider,
            auth_provider_id=provider_user_id,
            language_preference=profile_data.get("locale", "en"),
            timezone=profile_data.get("timezone", "UTC"),
            onboarding_completed=False,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return {
            "status": "success",
            "user_id": user.id,
            "message": f"Welcome! Signed in with {provider}",
            "next_step": "family_setup",
            "access_token": await self._generate_access_token(user),
        }

    async def complete_family_setup(
        self, user_id: int, family_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Quick family setup wizard
        """
        family = Family(
            name=family_data.get("name", "My Family"),
            primary_user_id=user_id,
            timezone=family_data.get("timezone", "UTC"),
            language=family_data.get("language", "en"),
            settings={
                "auto_approve_minor_changes": True,
                "notification_preferences": family_data.get("notifications", {}),
                "voice_enabled": True,
            },
        )

        self.db.add(family)

        # Mark onboarding complete
        user = await self.db.get(User, user_id)
        user.onboarding_completed = True
        user.family_id = family.id

        await self.db.commit()

        return {
            "status": "complete",
            "family_id": family.id,
            "message": "Setup complete! You're ready to start scheduling.",
            "quick_actions": [
                "Add family members",
                "Connect calendar",
                "Enable voice commands",
            ],
        }

    # Helper methods

    async def _find_existing_user(self, identifier: str) -> Optional[User]:
        """Find user by email or phone"""
        if self._is_email(identifier):
            result = await self.db.execute(select(User).where(User.email == identifier))
        else:
            result = await self.db.execute(select(User).where(User.phone == identifier))
        return result.scalar_one_or_none()

    async def _find_user_by_device(self, device_id: str) -> Optional[User]:
        """Find user by registered device"""
        # Implementation depends on device tracking
        return None

    def _is_email(self, identifier: str) -> bool:
        """Check if identifier is email"""
        return re.match(r"[^@]+@[^@]+\.[^@]+", identifier) is not None

    async def _send_magic_link_email(self, email: str, token: str, name: Optional[str]):
        """Send magic link via email"""
        magic_link = f"https://mew-assistant.app/auth/magic?token={token}"

        await self.notification_service.send_email(
            to=email,
            subject="✨ Your Mew Assistant Magic Link",
            body=f"""
            Hi {name or 'there'}!
            
            Click below to sign in to Mew Assistant (no password needed):
            
            {magic_link}
            
            This link expires in 15 minutes.
            
            Welcome aboard! 🎉
            """,
            html=True,
        )

    async def _send_magic_code_sms(self, phone: str, token: str):
        """Send magic code via SMS"""
        code = token[:6].upper()  # Short code for SMS

        await self.notification_service.send_sms(
            to=phone, message=f"Your Mew Assistant code: {code}\nExpires in 15 min."
        )

    async def _send_voice_confirmation(
        self, identifier: str, token: str, metadata: Dict[str, Any]
    ):
        """Handle voice platform confirmation"""
        # Platform-specific handling

    def _generate_voice_friendly_code(self) -> str:
        """Generate easy-to-say code (e.g., 'Charlie-7-Delta-3')"""
        import random

        phonetic = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot"]
        return f"{random.choice(phonetic)}-{random.randint(1,9)}-{random.choice(phonetic)}-{random.randint(1,9)}"

    def _get_welcome_back_message(self, language: str) -> str:
        """Localized welcome back message"""
        messages = {
            "en": "Welcome back! How can I help with your schedule today?",
            "es": "¡Bienvenido de nuevo! ¿Cómo puedo ayudar con tu horario hoy?",
            "fr": "Bon retour! Comment puis-je vous aider avec votre emploi du temps?",
            # Add more languages
        }
        return messages.get(language, messages["en"])

    def _get_registration_prompt(self, code: str, language: str) -> str:
        """Voice registration prompt"""
        prompts = {
            "en": f"To register, please say your confirmation code: {code}",
            "es": f"Para registrarte, di tu código de confirmación: {code}",
            # Add more languages
        }
        return prompts.get(language, prompts["en"])

    async def _create_quick_user(
        self, magic_token: str, additional_info: Optional[Dict[str, Any]]
    ) -> User:
        """Create user from magic link"""
        # Implementation

    async def _generate_access_token(self, user: User) -> str:
        """Generate JWT access token"""
        from app.utils.auth import create_access_token

        return create_access_token({"sub": str(user.id)})

    async def _link_social_account(
        self, user_id: int, provider: str, provider_user_id: str
    ):
        """Link social account to existing user"""
        user = await self.db.get(User, user_id)
        if user:
            user.auth_provider = provider
            user.auth_provider_id = provider_user_id
            await self.db.commit()
