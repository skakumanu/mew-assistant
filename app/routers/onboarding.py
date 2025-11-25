from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import secrets
import qrcode
import io
import base64
from datetime import datetime, timedelta

from ..database.connection import get_db
from ..database.models import User, Session
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
    data: QuickOnboard,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
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
        role="PARENT",
        phone=data.contact if "@" not in data.contact else None
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
    img.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    # Store onboarding session
    session = UserSession(
        user_id=user.id,
        session_token=onboarding_token,
        device_info=f"Onboarding via {data.channel}",
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(session)
    db.commit()
    
    # Send magic link based on channel
    if data.channel in ["sms", "whatsapp"]:
        background_tasks.add_task(
            notification_service.send_sms,
            data.contact,
            f"Welcome to Mew! 🐱 Click to finish setup: {magic_link}"
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
            """
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
        """
    )

@router.get("/magic/{token}")
async def magic_link_login(
    token: str,
    db: Session = Depends(get_db)
):
    """Magic link that logs user in and completes onboarding"""
    
    # Verify token (simplified - in production use proper token validation)
    session = db.query(UserSession).filter(
        UserSession.session_token == token,
        UserSession.expires_at > datetime.utcnow()
    ).first()
    
    if not session:
        return HTMLResponse("""
        <html>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h2>⚠️ This link has expired</h2>
                <p>Please request a new one at <a href="/">mew-assistant.org</a></p>
            </body>
        </html>
        """)
    
    user = db.query(User).filter(User.id == session.user_id).first()
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Welcome to Mew Assistant</title>
        <style>
            body {{ font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }}
            .button {{ background: #4CAF50; color: white; padding: 15px 32px; 
                      text-decoration: none; display: inline-block; margin: 10px 0; 
                      cursor: pointer; border: none; border-radius: 4px; font-size: 16px; }}
            .option {{ border: 1px solid #ddd; padding: 20px; margin: 10px 0; border-radius: 8px; }}
            h1 {{ color: #333; }}
        </style>
    </head>
    <body>
        <h1>🎉 Welcome {user.full_name}!</h1>
        <p>Your Mew Assistant is ready to help with scheduling and caregiving tasks!</p>
        
        <h2>Quick Setup (Optional)</h2>
        
        <div class="option">
            <h3>📅 Connect Your Calendar</h3>
            <p>Let Mew help you manage schedules automatically</p>
            <button class="button" onclick="connectGoogle()">Connect Google Calendar</button>
            <button class="button" onclick="connectApple()">Connect Apple Calendar</button>
            <button class="button" onclick="skip()">Skip for now</button>
        </div>
        
        <div class="option">
            <h3>🗣️ Enable Voice Commands</h3>
            <p>Talk to Mew through Siri, Alexa, or Google Assistant</p>
            <button class="button" onclick="setupVoice()">Setup Voice</button>
            <button class="button" onclick="skip()">Skip for now</button>
        </div>
        
        <div class="option">
            <h3>👨‍👩‍👧‍👦 Add Family Members</h3>
            <p>Add kids, caregivers, or other family members</p>
            <button class="button" onclick="addFamily()">Add Family</button>
            <button class="button" onclick="skip()">Skip for now</button>
        </div>
        
        <br><br>
        <button class="button" style="background: #2196F3; font-size: 20px;" 
                onclick="startUsing()">🚀 Start Using Mew Now!</button>
        
        <script>
            const apiUrl = window.location.origin;
            const token = "{token}";
            
            function connectGoogle() {{
                window.location.href = `${{apiUrl}}/calendar/google/auth?token=${{token}}`;
            }}
            
            function connectApple() {{
                window.location.href = `${{apiUrl}}/calendar/apple/auth?token=${{token}}`;
            }}
            
            function setupVoice() {{
                window.location.href = `${{apiUrl}}/voice/setup?token=${{token}}`;
            }}
            
            function addFamily() {{
                window.location.href = `${{apiUrl}}/family/setup?token=${{token}}`;
            }}
            
            function skip() {{
                alert('No problem! You can set this up anytime from Settings.');
            }}
            
            function startUsing() {{
                window.location.href = `${{apiUrl}}/dashboard?token=${{token}}`;
            }}
        </script>
    </body>
    </html>
    """)

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
                "Follow voice prompts to link account"
            ],
            "first_command": "Alexa, ask Mew to schedule therapy for tomorrow at 3pm"
        },
        "siri": {
            "steps": [
                "Open Safari on iPhone",
                "Visit: mew-assistant.org/siri",
                "Tap 'Add to Siri'",
                "Say 'Hey Siri, setup Mew'",
                "Follow prompts to complete"
            ],
            "first_command": "Hey Siri, ask Mew to show my schedule"
        },
        "google": {
            "steps": [
                "Say 'Hey Google, talk to Mew Assistant'",
                "Follow prompts to link your account",
                "Grant calendar permissions",
                "You're ready!"
            ],
            "first_command": "Hey Google, ask Mew to reschedule today's appointment"
        }
    }

@router.post("/complete")
async def complete_onboarding(
    token: str,
    db: Session = Depends(get_db)
):
    """Mark onboarding as complete"""
    
    session = db.query(UserSession).filter(
        UserSession.session_token == token
    ).first()
    
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
            "Need help? Just say 'Help' or text HELP anytime!"
        ]
    }
