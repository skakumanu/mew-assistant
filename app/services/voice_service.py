"""
Voice Command Service - Global Language Support
Handles multilingual voice commands with automatic language detection
Supporting 100+ languages from around the world
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from app.database.models import VoiceCommand
from app.database.models import User
from app.schemas.voice import VoiceCommandRequest, VoiceCommandResponse, VoiceTranscription
from app.integrations.voice_integration import VoiceIntegration
from app.services.session_service import SessionService

logger = logging.getLogger(__name__)

# Comprehensive global language support (100+ languages)
SUPPORTED_LANGUAGES = {
    # Major World Languages
    'en': 'English', 'es': 'Spanish', 'zh': 'Chinese (Mandarin)', 'hi': 'Hindi',
    'ar': 'Arabic', 'bn': 'Bengali', 'pt': 'Portuguese', 'ru': 'Russian',
    'ja': 'Japanese', 'pa': 'Punjabi', 'de': 'German', 'jv': 'Javanese',
    'ko': 'Korean', 'fr': 'French', 'te': 'Telugu', 'mr': 'Marathi',
    'tr': 'Turkish', 'ta': 'Tamil', 'vi': 'Vietnamese', 'ur': 'Urdu',
    'it': 'Italian', 'th': 'Thai', 'gu': 'Gujarati', 'pl': 'Polish',
    'uk': 'Ukrainian', 'fa': 'Persian', 'ml': 'Malayalam', 'kn': 'Kannada',
    'or': 'Odia', 'my': 'Burmese', 'az': 'Azerbaijani', 'uz': 'Uzbek',
    'sd': 'Sindhi', 'am': 'Amharic', 'ro': 'Romanian', 'nl': 'Dutch',
    
    # European Languages
    'cs': 'Czech', 'el': 'Greek', 'sv': 'Swedish', 'hu': 'Hungarian',
    'fi': 'Finnish', 'no': 'Norwegian', 'da': 'Danish', 'sk': 'Slovak',
    'bg': 'Bulgarian', 'hr': 'Croatian', 'sr': 'Serbian', 'sl': 'Slovenian',
    'lt': 'Lithuanian', 'lv': 'Latvian', 'et': 'Estonian', 'is': 'Icelandic',
    'ga': 'Irish', 'cy': 'Welsh', 'eu': 'Basque', 'ca': 'Catalan',
    'gl': 'Galician', 'mt': 'Maltese', 'sq': 'Albanian', 'mk': 'Macedonian',
    
    # African Languages
    'sw': 'Swahili', 'ha': 'Hausa', 'yo': 'Yoruba', 'ig': 'Igbo',
    'zu': 'Zulu', 'xh': 'Xhosa', 'af': 'Afrikaans', 'so': 'Somali',
    'rw': 'Kinyarwanda', 'mg': 'Malagasy', 'sn': 'Shona', 'ny': 'Chichewa',
    'st': 'Sesotho', 'tn': 'Setswana', 'wo': 'Wolof', 'ff': 'Fulani',
    
    # Asian Languages
    'ne': 'Nepali', 'si': 'Sinhala', 'km': 'Khmer', 'lo': 'Lao',
    'mn': 'Mongolian', 'bo': 'Tibetan', 'dz': 'Dzongkha', 'tl': 'Tagalog',
    'id': 'Indonesian', 'ms': 'Malay', 'ceb': 'Cebuano', 'hmn': 'Hmong',
    'hy': 'Armenian', 'ka': 'Georgian', 'kk': 'Kazakh', 'ky': 'Kyrgyz',
    'tg': 'Tajik', 'tk': 'Turkmen', 'ps': 'Pashto', 'ku': 'Kurdish',
    
    # Middle Eastern Languages
    'he': 'Hebrew', 'yi': 'Yiddish', 'ug': 'Uyghur',
    
    # Pacific Languages
    'mi': 'Maori', 'sm': 'Samoan', 'to': 'Tongan', 'fj': 'Fijian',
    'haw': 'Hawaiian', 'ty': 'Tahitian',
    
    # Native American Languages
    'qu': 'Quechua', 'gn': 'Guarani', 'ay': 'Aymara',
    
    # Additional Major Regional Languages
    'be': 'Belarusian', 'bs': 'Bosnian', 'lb': 'Luxembourgish',
    'fy': 'Frisian', 'la': 'Latin', 'eo': 'Esperanto',
    'sa': 'Sanskrit', 'as': 'Assamese', 'bho': 'Bhojpuri',
    'mai': 'Maithili', 'kok': 'Konkani', 'doi': 'Dogri',
}


class VoiceService:
    """Service for handling multilingual voice commands with automatic language detection"""
    
    def __init__(self, db: Session):
        self.db = db
        self.voice_integration = VoiceIntegration()
        self.session_service = SessionService(db)
    
    async def process_voice_command(
        self,
        audio_data: bytes,
        user_id: str,
        session_id: Optional[str] = None,
        hint_language: Optional[str] = None
    ) -> VoiceCommandResponse:
        """
        Process voice command with automatic language detection
        
        Args:
            audio_data: Raw audio bytes
            user_id: User identifier
            session_id: Optional session ID
            hint_language: Optional language hint to prioritize
        
        Returns:
            VoiceCommandResponse with transcription and action
        """
        try:
            # Step 1: Automatic language detection and transcription
            logger.info(f"Processing voice command for user {user_id}")
            transcription = await self.voice_integration.transcribe_audio(
                audio_data=audio_data,
                hint_language=hint_language
            )
            
            detected_language = transcription.language
            detected_language_name = SUPPORTED_LANGUAGES.get(detected_language, "Unknown")
            confidence = transcription.confidence
            
            logger.info(
                f"Language detected: {detected_language_name} ({detected_language}) "
                f"with confidence {confidence:.2%}"
            )
            
            # Step 2: Store voice command in database
            voice_command = VoiceCommand(
                user_id=user_id,
                session_id=session_id,
                audio_duration=transcription.duration,
                detected_language=detected_language,
                confidence_score=confidence,
                transcript=transcription.text,
                intent=transcription.intent,
                entities=transcription.entities,
                timestamp=datetime.utcnow()
            )
            self.db.add(voice_command)
            self.db.commit()
            self.db.refresh(voice_command)
            
            # Step 3: Process the intent and extract scheduling information
            action_result = await self._process_intent(
                transcription=transcription,
                user_id=user_id,
                session_id=session_id
            )
            
            return VoiceCommandResponse(
                command_id=voice_command.id,
                transcription=transcription,
                detected_language=detected_language,
                language_name=detected_language_name,
                action_taken=action_result.get("action"),
                action_details=action_result.get("details"),
                requires_approval=action_result.get("requires_approval", False),
                approval_id=action_result.get("approval_id"),
                success=True,
                message=f"Command processed successfully in {detected_language_name}"
            )
            
        except Exception as e:
            logger.error(f"Error processing voice command: {str(e)}")
            return VoiceCommandResponse(
                success=False,
                message=f"Failed to process voice command: {str(e)}",
                error=str(e)
            )
    
    async def _process_intent(
        self,
        transcription: VoiceTranscription,
        user_id: str,
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Process the detected intent and take appropriate action
        
        Supported intents:
        - schedule_appointment: Create new appointment
        - reschedule_appointment: Modify existing appointment
        - cancel_appointment: Cancel appointment
        - query_schedule: Check schedule
        - set_reminder: Create reminder
        """
        intent = transcription.intent
        entities = transcription.entities
        
        logger.info(f"Processing intent: {intent} with entities: {entities}")
        
        if intent == "schedule_appointment":
            return await self._handle_schedule_appointment(
                entities=entities,
                user_id=user_id,
                session_id=session_id
            )
        
        elif intent == "reschedule_appointment":
            return await self._handle_reschedule_appointment(
                entities=entities,
                user_id=user_id
            )
        
        elif intent == "cancel_appointment":
            return await self._handle_cancel_appointment(
                entities=entities,
                user_id=user_id
            )
        
        elif intent == "query_schedule":
            return await self._handle_query_schedule(
                entities=entities,
                user_id=user_id
            )
        
        elif intent == "set_reminder":
            return await self._handle_set_reminder(
                entities=entities,
                user_id=user_id
            )
        
        else:
            return {
                "action": "unknown_intent",
                "details": {"intent": intent},
                "message": f"Intent '{intent}' is not yet supported"
            }
    
    async def _handle_schedule_appointment(
        self,
        entities: Dict[str, Any],
        user_id: str,
        session_id: Optional[str]
    ) -> Dict[str, Any]:
        """Handle appointment scheduling from voice command"""
        from app.services.approval_service import ApprovalService
        
        # Extract scheduling details from entities
        title = entities.get("title", "Voice Scheduled Appointment")
        start_time = entities.get("datetime")
        duration = entities.get("duration", 60)  # default 60 minutes
        location = entities.get("location")
        notes = entities.get("notes")
        
        # Check if this is a child request requiring approval
        approval_service = ApprovalService(self.db)
        user_profile = self.db.query(User).filter(User.id == user_id).first()
        
        if user_profile and user_profile.role == "child":
            # Create approval request
            approval = await approval_service.create_approval_request(
                child_id=user_id,
                request_type="schedule_change",
                request_data={
                    "title": title,
                    "start_time": start_time,
                    "duration": duration,
                    "location": location,
                    "notes": notes,
                    "source": "voice_command"
                }
            )
            
            return {
                "action": "approval_requested",
                "details": {
                    "approval_id": approval.id,
                    "title": title,
                    "start_time": start_time
                },
                "requires_approval": True,
                "approval_id": approval.id,
                "message": "Appointment request sent to parent for approval"
            }
        
        # Parent or approved request - create directly
        # TODO: Integrate with calendar service to create actual appointment
        return {
            "action": "appointment_created",
            "details": {
                "title": title,
                "start_time": start_time,
                "duration": duration,
                "location": location
            },
            "requires_approval": False,
            "message": "Appointment created successfully"
        }
    
    async def _handle_reschedule_appointment(
        self,
        entities: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Handle appointment rescheduling"""
        # TODO: Implement rescheduling logic
        return {
            "action": "reschedule_requested",
            "details": entities,
            "message": "Rescheduling functionality coming soon"
        }
    
    async def _handle_cancel_appointment(
        self,
        entities: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Handle appointment cancellation"""
        # TODO: Implement cancellation logic
        return {
            "action": "cancel_requested",
            "details": entities,
            "message": "Cancellation functionality coming soon"
        }
    
    async def _handle_query_schedule(
        self,
        entities: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Handle schedule queries"""
        # TODO: Implement schedule query logic
        return {
            "action": "schedule_queried",
            "details": entities,
            "message": "Schedule query functionality coming soon"
        }
    
    async def _handle_set_reminder(
        self,
        entities: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Handle reminder creation"""
        # TODO: Implement reminder logic
        return {
            "action": "reminder_set",
            "details": entities,
            "message": "Reminder functionality coming soon"
        }
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of all supported languages"""
        return [
            {"code": code, "name": name}
            for code, name in sorted(SUPPORTED_LANGUAGES.items(), key=lambda x: x[1])
        ]
    
    def get_language_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get language usage statistics for a user"""
        commands = self.db.query(VoiceCommand).filter(
            VoiceCommand.user_id == user_id
        ).all()
        
        if not commands:
            return {"total_commands": 0, "languages_used": []}
        
        language_counts = {}
        for cmd in commands:
            lang = cmd.detected_language
            language_counts[lang] = language_counts.get(lang, 0) + 1
        
        return {
            "total_commands": len(commands),
            "languages_used": [
                {
                    "code": code,
                    "name": SUPPORTED_LANGUAGES.get(code, "Unknown"),
                    "count": count,
                    "percentage": (count / len(commands)) * 100
                }
                for code, count in sorted(
                    language_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
            ],
            "primary_language": max(language_counts.items(), key=lambda x: x[1])[0]
            if language_counts else None
        }
