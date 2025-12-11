"""
Voice Platform Router
Handles requests from Siri, Alexa, Google Assistant, Tesla, etc.
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, Dict, Any
import logging

from app.schemas.voice_platform import (
    VoicePlatformResponse,
    SiriRequest,
    AlexaRequest,
    GoogleAssistantRequest,
    TeslaRequest
)
from app.integrations.voice_platforms import (
    SiriIntegration,
    AlexaIntegration,
    GoogleAssistantIntegration,
    TeslaIntegration
)
from app.middleware.auth import verify_api_key

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/voice", tags=["Voice Platforms"])


# Initialize integrations (in production, use dependency injection)
siri = SiriIntegration(config={})
alexa = AlexaIntegration(config={})
google = GoogleAssistantIntegration(config={})
tesla = TeslaIntegration(config={})


@router.post("/siri/webhook", response_model=VoicePlatformResponse)
async def siri_webhook(
    request: SiriRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Apple Siri webhook endpoint
    Receives SiriKit intents and iOS Shortcuts
    """
    try:
        # Authenticate request
        auth_valid = await siri.authenticate({
            "signature": authorization,
            "body": request.json()
        })
        
        if not auth_valid:
            raise HTTPException(status_code=401, detail="Invalid Siri signature")
        
        # Process intent
        result = await siri.handle_intent(
            intent=request.intent,
            slots=request.slots,
            user_id=request.user_id
        )
        
        # Send response
        await siri.send_response(result)
        
        return VoicePlatformResponse(
            platform="siri",
            success=result.get('success', False),
            response=result.get('speech', ''),
            data=result
        )
        
    except Exception as e:
        logger.error(f"Siri webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alexa/webhook", response_model=VoicePlatformResponse)
async def alexa_webhook(request: AlexaRequest):
    """
    Amazon Alexa skill endpoint
    Receives Alexa skill requests
    """
    try:
        # Authenticate request
        auth_valid = await alexa.authenticate({
            "session": request.session,
            "request": request.request
        })
        
        if not auth_valid:
            raise HTTPException(status_code=401, detail="Invalid Alexa request")
        
        # Extract intent and slots
        intent_name = request.request.get('intent', {}).get('name', '')
        slots = request.request.get('intent', {}).get('slots', {})
        user_id = request.session.get('user', {}).get('userId', '')
        
        # Process intent
        result = await alexa.handle_intent(
            intent=intent_name,
            slots=slots,
            user_id=user_id
        )
        
        # Send response
        await alexa.send_response(result)
        
        return VoicePlatformResponse(
            platform="alexa",
            success=result.get('success', False),
            response=result.get('speech', ''),
            data=result
        )
        
    except Exception as e:
        logger.error(f"Alexa webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/google/webhook", response_model=VoicePlatformResponse)
async def google_assistant_webhook(request: GoogleAssistantRequest):
    """
    Google Assistant Actions endpoint
    Receives conversational actions requests
    """
    try:
        # Authenticate request
        auth_valid = await google.authenticate({
            "token": request.user.get('accessToken')
        })
        
        if not auth_valid:
            raise HTTPException(status_code=401, detail="Invalid Google request")
        
        # Extract intent and parameters
        intent_name = request.inputs[0].get('intent', '') if request.inputs else ''
        parameters = request.inputs[0].get('arguments', []) if request.inputs else []
        user_id = request.user.get('userId', '')
        
        # Convert parameters to slots
        slots = {p.get('name'): p.get('value') for p in parameters}
        
        # Process intent
        result = await google.handle_intent(
            intent=intent_name,
            slots=slots,
            user_id=user_id
        )
        
        # Send response
        await google.send_response(result)
        
        return VoicePlatformResponse(
            platform="google_assistant",
            success=result.get('success', False),
            response=result.get('speech', ''),
            data=result
        )
        
    except Exception as e:
        logger.error(f"Google Assistant webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tesla/webhook", response_model=VoicePlatformResponse)
async def tesla_webhook(
    request: TeslaRequest,
    x_tesla_signature: Optional[str] = Header(None)
):
    """
    Tesla voice command endpoint
    Receives voice commands from Tesla vehicles
    """
    try:
        # Authenticate request
        auth_valid = await tesla.authenticate({
            "vehicle_id": request.vehicle_id,
            "token": x_tesla_signature
        })
        
        if not auth_valid:
            raise HTTPException(status_code=401, detail="Invalid Tesla request")
        
        # Process command
        result = await tesla.handle_intent(
            intent=request.command,
            slots=request.parameters,
            user_id=request.user_id
        )
        
        # Send response
        await tesla.send_response(result)
        
        return VoicePlatformResponse(
            platform="tesla",
            success=result.get('success', False),
            response=result.get('speech', ''),
            data=result
        )
        
    except Exception as e:
        logger.error(f"Tesla webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platforms", response_model=Dict[str, Any])
async def list_platforms():
    """
    List all supported voice platforms and their status
    """
    return {
        "platforms": [
            {
                "name": "Apple Siri",
                "id": "siri",
                "status": "active",
                "webhook": "/api/v1/voice/siri/webhook",
                "features": ["SiriKit", "Shortcuts", "HomePod", "Apple Watch"]
            },
            {
                "name": "Amazon Alexa",
                "id": "alexa",
                "status": "active",
                "webhook": "/api/v1/voice/alexa/webhook",
                "features": ["Custom Skills", "Smart Home", "Flash Briefing"]
            },
            {
                "name": "Google Assistant",
                "id": "google_assistant",
                "status": "active",
                "webhook": "/api/v1/voice/google/webhook",
                "features": ["Actions", "Smart Home", "Routines"]
            },
            {
                "name": "Tesla",
                "id": "tesla",
                "status": "active",
                "webhook": "/api/v1/voice/tesla/webhook",
                "features": ["Voice Commands", "Navigation", "In-Vehicle"]
            }
        ]
    }


@router.post("/register/{platform}")
async def register_platform(
    platform: str,
    config: Dict[str, Any],
    api_key: str = Depends(verify_api_key)
):
    """
    Register or update voice platform integration
    """
    try:
        if platform == "siri":
            success = await siri.register_skill(config)
        elif platform == "alexa":
            success = await alexa.register_skill(config)
        elif platform == "google_assistant":
            success = await google.register_skill(config)
        elif platform == "tesla":
            success = await tesla.register_skill(config)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown platform: {platform}")
        
        if success:
            return {"status": "success", "platform": platform}
        else:
            raise HTTPException(status_code=500, detail="Registration failed")
            
    except Exception as e:
        logger.error(f"Platform registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
