"""Amazon Alexa Integration"""

import logging
from typing import Any, Dict

from app.services.message_service import MessageService

from .base_voice_platform import BaseVoicePlatform

logger = logging.getLogger(__name__)


class AlexaIntegration(BaseVoicePlatform):
    """Amazon Alexa Skill Integration"""

    INTENT_MAPPING = {
        "ScheduleAppointment": "schedule",
        "GetSummary": "summary",
        "AMAZON.HelpIntent": "help",
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.skill_id = config.get("alexa_skill_id")

    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        try:
            app_id = credentials.get("session", {}).get("application", {}).get("applicationId")
            return app_id == self.skill_id
        except Exception as e:
            logger.error(f"Alexa auth failed: {e}")
            return False

    async def handle_intent(
        self, intent: str, slots: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        action = self.INTENT_MAPPING.get(intent, "unknown")

        if action == "schedule":
            return await self._handle_schedule(slots, user_id)
        elif action == "help":
            return {"success": True, "speech": "I'm Mew, your family assistant"}

        return {"success": False, "speech": "I didn't understand"}

    async def _handle_schedule(self, slots: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        message_service = MessageService()
        activity = slots.get("Activity", {}).get("value", "")
        result = await message_service.process_scheduling_request(
            user_id=user_id, message=f"Schedule {activity}", channel="alexa"
        )
        return {"success": result["success"], "speech": f"Scheduled {activity}"}

    async def send_response(self, response: Dict[str, Any]) -> bool:
        return True

    async def register_skill(self, skill_config: Dict[str, Any]) -> bool:
        return True
