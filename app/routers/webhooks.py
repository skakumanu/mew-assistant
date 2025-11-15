"""
Webhook endpoints for receiving external messages (SMS, WhatsApp, Email).
"""

from fastapi import APIRouter, Request, Form, HTTPException
from typing import Optional
from datetime import datetime

from app.integrations import SMSIntegration, WhatsAppIntegration
from app.services.message_service import MessageService
from app.utils.logger import logger

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

sms_integration = SMSIntegration()
whatsapp_integration = WhatsAppIntegration()
message_service = MessageService()


@router.post("/sms/incoming")
async def receive_sms(
    request: Request,
    MessageSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    NumMedia: Optional[str] = Form("0"),
):
    """
    Webhook endpoint for receiving incoming SMS from Twilio.
    
    This endpoint is called by Twilio when an SMS is received.
    Configure in Twilio Console: Account > Phone Numbers > Your Number > Messaging > Webhook
    """
    try:
        webhook_data = {
            "MessageSid": MessageSid,
            "From": From,
            "To": To,
            "Body": Body,
            "NumMedia": NumMedia,
        }
        
        parsed_data = sms_integration.parse_incoming_sms(webhook_data)
        
        logger.info(f"Received SMS from {From}: {Body[:50]}...")
        
        # Process the message
        response = await message_service.process_incoming_message(
            source="sms",
            from_contact=parsed_data["from_number"],
            message_body=parsed_data["body"],
            message_id=parsed_data["message_sid"],
        )
        
        # Return TwiML response
        twiml_response = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{response.get("reply", "Message received")}</Message></Response>'
        
        return twiml_response

    except Exception as e:
        logger.error(f"Error processing incoming SMS: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process SMS")


@router.post("/whatsapp/incoming")
async def receive_whatsapp(
    request: Request,
    MessageSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    NumMedia: Optional[str] = Form("0"),
    ProfileName: Optional[str] = Form(None),
):
    """
    Webhook endpoint for receiving incoming WhatsApp messages from Twilio.
    
    Configure in Twilio Console: Programmable Messaging > WhatsApp > Sandbox Settings
    """
    try:
        webhook_data = {
            "MessageSid": MessageSid,
            "From": From,
            "To": To,
            "Body": Body,
            "NumMedia": NumMedia,
            "ProfileName": ProfileName,
        }
        
        parsed_data = whatsapp_integration.parse_incoming_message(webhook_data)
        
        logger.info(f"Received WhatsApp from {ProfileName or From}: {Body[:50]}...")
        
        # Process the message
        response = await message_service.process_incoming_message(
            source="whatsapp",
            from_contact=parsed_data["from_number"],
            message_body=parsed_data["body"],
            message_id=parsed_data["message_sid"],
            profile_name=parsed_data.get("profile_name"),
        )
        
        # Return TwiML response
        twiml_response = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{response.get("reply", "Message received")}</Message></Response>'
        
        return twiml_response

    except Exception as e:
        logger.error(f"Error processing incoming WhatsApp: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process WhatsApp message")


@router.get("/sms/status")
async def sms_status(
    MessageSid: str,
    MessageStatus: str,
    ErrorCode: Optional[str] = None,
):
    """
    Webhook endpoint for SMS delivery status updates from Twilio.
    """
    try:
        logger.info(f"SMS {MessageSid} status: {MessageStatus}")
        
        if ErrorCode:
            logger.error(f"SMS {MessageSid} error: {ErrorCode}")
        
        return {"status": "received"}

    except Exception as e:
        logger.error(f"Error processing SMS status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process status")


@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoints."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": [
            "/webhooks/sms/incoming",
            "/webhooks/whatsapp/incoming",
            "/webhooks/sms/status",
        ],
    }
