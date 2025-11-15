"""Apple Siri Integration via SiriKit and Shortcuts"""
from typing import Dict, Any
import logging
import hmac, hashlib
from .base_voice_platform import BaseVoicePlatform
from app.services.message_service import MessageService

logger = logging.getLogger(__name__)

class SiriIntegration(BaseVoicePlatform):
    """Apple Siri Integration - SiriKit intents, iOS Shortcuts, HomePod"""
    
    SUPPORTED_INTENTS = ['INCreateEventIntent', 'INSetTaskAttributeIntent', 'CustomMewIntent']
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.app_id = config.get('siri_app_id')
        self.signing_key = config.get('siri_signing_key')
        
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        try:
            signature = credentials.get('signature')
            body = credentials.get('body')
            expected = hmac.new(self.signing_key.encode(), body.encode(), hashlib.sha256).hexdigest()
            return hmac.compare_digest(signature, expected)
        except Exception as e:
            logger.error(f"Siri auth failed: {e}")
            return False
    
    async def handle_intent(self, intent: str, slots: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        if intent not in self.SUPPORTED_INTENTS:
            return {"success": False, "speech": "Unsupported action"}
        
        if intent == 'INCreateEventIntent':
            return await self._handle_create_event(slots, user_id)
        return {"success": False, "speech": "Error"}
    
    async def _handle_create_event(self, slots: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        message_service = MessageService()
        result = await message_service.process_scheduling_request(
            user_id=user_id,
            message=f"Schedule {slots.get('title')} at {slots.get('startDate')}",
            channel="siri"
        )
        return {"success": result['success'], "speech": f"Scheduled {slots.get('title')}"}
    
    async def send_response(self, response: Dict[str, Any]) -> bool:
        return True
    
    async def register_skill(self, skill_config: Dict[str, Any]) -> bool:
        logger.info(f"Registering Siri skill")
        return True
