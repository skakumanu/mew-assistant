import base64
import io
import secrets
from datetime import datetime, timedelta
from typing import Optional

import qrcode
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.models import Session as SessionModel
from ..database.models import User, UserRole
from ..schemas.auth import UserCreate
from ..services.auth_service import AuthService
from ..utils.notifications import NotificationService

notification_service = NotificationService()

router = APIRouter(prefix="/onboard", tags=["onboarding"])


class QuickOnboard(BaseModel):
    """Minimal info needed - we'll guide the rest"""

    contact: EmailStr  # Can be email or phone
    name: str
    preferred_language: str = "en"
    channel: str = "web"  # web, sms, whatsapp, voice, alexa, siri, google


class OnboardingStatus(BaseModel):
    onboarding_token: str
    user_id: int
    step: str
    next_action: str
    magic_link: Optional[str] = None
    qr_code: Optional[str] = None
    simple_instructions: str


@router.post("/quick", response_model=OnboardingStatus)
async def quick_onboard(
    data: QuickOnboard, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """
    One-click onboarding - user just provides name and email/phone
    System handles everything else automatically
    """

    # Generate secure tokens
    temp_password = secrets.token_urlsafe(12)
    onboarding_token = secrets.token_urlsafe(32)
    magic_token = secrets.token_urlsafe(32)

    # Create user account automatically
    user_data = UserCreate(
        email=data.contact if "@" in data.contact else f"{data.contact}@temp.mew",
        password=temp_password,
        full_name=data.name,
        role=UserRole.PARENT,
        phone=data.contact if "@" not in data.contact else None,
    )

    auth_service = AuthService(db)
    user = await auth_service.register_user(user_data)

    # Create magic link for passwordless login
    magic_link = f"https://mew-app-eastus2.azurewebsites.net/onboard/magic/{magic_token}"

    # Generate QR code for mobile setup
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(magic_link)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    # Store onboarding session (mapped to `sessions` table)
    session = SessionModel(
        user_id=str(user.id),
        session_id=onboarding_token,
        title="Onboarding",
        description=f"Onboarding via {data.channel}",
        scheduled_at=datetime.utcnow() + timedelta(hours=24),
    )
    db.add(session)
    db.commit()

    # Send magic link based on channel
    if data.channel in ["sms", "whatsapp"]:
        background_tasks.add_task(
            notification_service.send_sms,
            data.contact,
            f"Welcome to Mew! 🐱 Click to finish setup: {magic_link}",
        )
    else:
        background_tasks.add_task(
            notification_service.send_email,
            data.contact,
            "Welcome to Mew Assistant! 🐱",
            f"""
            <h2>Welcome {data.name}!</h2>
            <p>Your Mew Assistant is ready! Click the button below to complete setup:</p>
            <a href="{magic_link}" style="background: #4CAF50; color: white; padding: 15px 32px;
               text-decoration: none; display: inline-block; margin: 4px 2px; cursor: pointer;
               border-radius: 4px;">Complete Setup</a>
            <p>Or scan this QR code with your phone:</p>
            <img src="data:image/png;base64,{qr_base64}" alt="Setup QR Code" />
            <p>Questions? Just reply to this email or text "help" to get started!</p>
            """,
        )

    return OnboardingStatus(
        onboarding_token=onboarding_token,
        user_id=user.id,
        step="magic_link_sent",
        next_action="check_email_or_sms",
        magic_link=magic_link,
        qr_code=f"data:image/png;base64,{qr_base64}",
        simple_instructions=f"""
        🎉 You're almost there, {data.name}!

        We sent you a magic link to {data.contact}

        ✅ Just click the link or scan the QR code
        ✅ Connect your calendar (optional - takes 2 clicks)
        ✅ Start using Mew!

        No passwords to remember. No complicated setup.
        """,
    )


@router.get("/magic/{token}")
async def magic_link_login(token: str, db: Session = Depends(get_db)):
    """Magic link that logs user in and completes onboarding"""

    # Verify token (simplified - in production use proper token validation)
    session = (
        db.query(SessionModel)
        .filter(
            SessionModel.session_id == token,
            SessionModel.scheduled_at > datetime.utcnow(),
        )
        .first()
    )

    if not session:
        return HTMLResponse(
            """
        <html>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h2>⚠️ This link has expired</h2>
                <p>Please request a new one at <a href="/">mew-assistant.org</a></p>
            </body>
        </html>
        """
        )

    user = db.query(User).filter(User.id == session.user_id).first()

    # Use auto-escaping template to prevent XSS
    username = user.username if user and user.username else "User"
    email = user.email if user and user.email else ""

    # Generate HTML with proper escaping via template
    from jinja2 import Template, select_autoescape
    template_str = r"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Welcome to Mew Assistant</title>
        <style>
            body { font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }
            .welcome { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                      color: white; padding: 40px; border-radius: 10px; text-align: center; }
            h1 { margin: 0 0 10px 0; }
            .card { background: white; padding: 30px; border-radius: 10px;
                   box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 20px 0; }
            .step { margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }
            .step h3 { margin-top: 0; color: #667eea; }
            button, .button { background: #667eea; color: white; border: none;
                             padding: 12px 30px; border-radius: 5px; cursor: pointer;
                             text-decoration: none; display: inline-block; font-size: 16px; }
            button:hover, .button:hover { background: #764ba2; }
            .info { background: #e3f2fd; padding: 15px; border-radius: 5px;
                   border-left: 4px solid #2196f3; margin: 20px 0; }
            code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px;
                  font-family: monospace; }
        </style>
    </head>
    <body>
        <div class="welcome">
            <h1>🐱 Welcome to Mew Assistant!</h1>
            <p>Your AI-powered family scheduling companion</p>
        </div>

        <div class="card">
            <h2>Hello, {{ username }}!</h2>
            <p>Your account ({{ email }}) is ready. Let's get you set up.</p>

            <div class="step">
                <h3>Step 1: Connect Your Calendar</h3>
                <p>Link Google Calendar or Microsoft Outlook to sync your family's schedule.</p>
                <a href="/auth/oauth/google" class="button">Connect Google Calendar</a>
                <a href="/auth/oauth/microsoft" class="button">Connect Outlook</a>
            </div>

            <div class="step">
                <h3>Step 2: Set Up Voice Commands</h3>
                <p>Configure Siri or Google Assistant for hands-free scheduling.</p>
                <a href="/docs/siri-setup" class="button">View Setup Guide</a>
            </div>

            <div class="step">
                <h3>Step 3: Add Family Members</h3>
                <p>Create profiles for kids and caregivers.</p>
                <a href="/dashboard#family" class="button">Add Family Members</a>
            </div>

            <div class="info">
                <strong>Need Help?</strong><br>
                Check out our <a href="/docs">documentation</a> or contact support.
            </div>
        </div>
    </body>
    </html>
    """
    
    template = Template(template_str, autoescape=select_autoescape(['html', 'xml']))
    html_content = template.render(username=username, email=email)
    
    return HTMLResponse(html_content)


@router.get("/sms-setup")
async def sms_onboard_flow():
    """SMS-based onboarding instructions"""
    return {
        "instructions": """
        SMS Onboarding (Super Simple!):

        1. Text: "START <your name>" to +1-XXX-MEW-HELP
        2. Reply with your preferred language (or skip)
        3. Done! You'll get a link to connect your calendar

        Example:
        You: "START John Smith"
        Mew: "Hi John! 👋 Reply with your language (English/Spanish/French) or say SKIP"
        You: "English"
        Mew: "Perfect! Click here to connect your calendar: [link] Or text HELP for voice commands!"
        """
    }


@router.get("/voice-setup")
async def voice_onboard_flow():
    """Voice-based onboarding instructions"""
    return {
        "alexa": {
            "steps": [
                "Open Alexa app",
                "Search for 'Mew Assistant' skill",
                "Tap 'Enable to Use'",
                "Say 'Alexa, open Mew Assistant'",
                "Follow voice prompts to link account",
            ],
            "first_command": "Alexa, ask Mew to schedule therapy for tomorrow at 3pm",
        },
        "siri": {
            "steps": [
                "Open Safari on iPhone",
                "Visit: mew-assistant.org/siri",
                "Tap 'Add to Siri'",
                "Say 'Hey Siri, setup Mew'",
                "Follow prompts to complete",
            ],
            "first_command": "Hey Siri, ask Mew to show my schedule",
        },
        "google": {
            "steps": [
                "Say 'Hey Google, talk to Mew Assistant'",
                "Follow prompts to link your account",
                "Grant calendar permissions",
                "You're ready!",
            ],
            "first_command": "Hey Google, ask Mew to reschedule today's appointment",
        },
    }


@router.post("/complete")
async def complete_onboarding(token: str, db: Session = Depends(get_db)):
    """Mark onboarding as complete"""

    session = db.query(SessionModel).filter(SessionModel.session_id == token).first()

    if not session:
        raise HTTPException(status_code=404, detail="Invalid onboarding token")

    user = db.query(User).filter(User.id == session.user_id).first()
    user.is_active = True
    db.commit()

    return {
        "success": True,
        "message": f"Welcome aboard, {user.full_name}! 🎉",
        "next_steps": [
            "Try: 'Schedule therapy appointment for tomorrow at 2pm'",
            "Try: 'What's on my schedule today?'",
            "Try: 'Add a reminder to give medication at 8am'",
            "Need help? Just say 'Help' or text HELP anytime!",
        ],
    }
