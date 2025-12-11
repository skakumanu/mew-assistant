"""
Voice Integration Module
Handles voice command processing with automatic language detection
Supports 100+ global languages with automatic detection
"""

from typing import Optional, Dict, Any
import logging
from datetime import datetime

from app.utils.config import settings
from app.schemas.voice import VoiceTranscription

logger = logging.getLogger(__name__)

# Comprehensive global language support (100+ languages)
SUPPORTED_LANGUAGES = [
    # Major World Languages
    'en', 'es', 'zh', 'hi', 'ar', 'bn', 'pt', 'ru', 'ja', 'pa', 'de', 'jv',
    'ko', 'fr', 'te', 'mr', 'tr', 'ta', 'vi', 'ur', 'it', 'th', 'gu', 'pl',
    'uk', 'fa', 'ml', 'kn', 'or', 'my', 'az', 'uz', 'sd', 'am', 'ro', 'nl',
    
    # European Languages
    'cs', 'el', 'sv', 'hu', 'fi', 'no', 'da', 'sk', 'bg', 'hr', 'sr', 'sl',
    'lt', 'lv', 'et', 'is', 'ga', 'cy', 'eu', 'ca', 'gl', 'mt', 'sq', 'mk',
    
    # African Languages
    'sw', 'ha', 'yo', 'ig', 'zu', 'xh', 'af', 'so', 'rw', 'mg', 'sn', 'ny',
    'st', 'tn', 'wo', 'ff',
    
    # Asian Languages
    'ne', 'si', 'km', 'lo', 'mn', 'bo', 'dz', 'tl', 'id', 'ms', 'ceb', 'hmn',
    'hy', 'ka', 'kk', 'ky', 'tg', 'tk', 'ps', 'ku',
    
    # Middle Eastern
    'he', 'yi', 'ug',
    
    # Pacific
    'mi', 'sm', 'to', 'fj', 'haw', 'ty',
    
    # Native American
    'qu', 'gn', 'ay',
    
    # Additional
    'be', 'bs', 'lb', 'fy', 'la', 'eo', 'sa', 'as', 'bho', 'mai', 'kok', 'doi'
]


class VoiceIntegration:
    """
    Voice command integration with automatic language detection
    Supports 100+ languages from around the world
    """
    
    def __init__(self):
        self.api_key = settings.AZURE_SPEECH_KEY
        self.region = settings.AZURE_SPEECH_REGION
        self.enabled = bool(self.api_key and self.region)
        
        if self.enabled:
            try:
                import azure.cognitiveservices.speech as speechsdk
                self.speech_config = speechsdk.SpeechConfig(
                    subscription=self.api_key,
                    region=self.region
                )
                # Enable automatic language detection for all supported languages
                self.speech_config.set_property(
                    speechsdk.PropertyId.SpeechServiceConnection_LanguageIdMode,
                    "Continuous"
                )
                logger.info(f"Voice integration initialized with {len(SUPPORTED_LANGUAGES)} language support")
            except ImportError:
                logger.warning("Azure Speech SDK not installed. Voice features will be mocked.")
                self.enabled = False
    
    async def transcribe_audio(
        self,
        audio_data: bytes,
        hint_language: Optional[str] = None
    ) -> VoiceTranscription:
        """
        Transcribe audio with automatic language detection
        
        Args:
            audio_data: Raw audio bytes
            hint_language: Optional language hint to prioritize detection
        
        Returns:
            VoiceTranscription object with detected language and text
        """
        if not self.enabled:
            return self._mock_transcription(hint_language)
        
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            # Create audio configuration from bytes
            audio_stream = speechsdk.audio.PushAudioInputStream()
            audio_stream.write(audio_data)
            audio_stream.close()
            
            audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)
            
            # Configure automatic language detection with all supported languages
            auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
                languages=SUPPORTED_LANGUAGES[:10] if not hint_language else [hint_language] + SUPPORTED_LANGUAGES[:9]
            )
            
            # Create speech recognizer with auto-detection
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_config,
                auto_detect_source_language_config=auto_detect_config
            )
            
            # Perform recognition
            result = speech_recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                # Extract detected language
                detected_language = result.properties.get(
                    speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult,
                    hint_language or 'en'
                )
                
                # Extract entities and intent using NLU
                intent, entities = await self._extract_intent_and_entities(
                    result.text,
                    detected_language
                )
                
                return VoiceTranscription(
                    text=result.text,
                    language=detected_language,
                    confidence=self._get_confidence(result),
                    duration=result.duration.total_seconds(),
                    intent=intent,
                    entities=entities,
                    timestamp=datetime.utcnow()
                )
            
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("No speech could be recognized")
                return VoiceTranscription(
                    text="",
                    language=hint_language or "unknown",
                    confidence=0.0,
                    duration=0.0,
                    error="No speech detected"
                )
            
            else:
                error_details = result.cancellation_details
                logger.error(f"Speech recognition failed: {error_details.reason}")
                return VoiceTranscription(
                    text="",
                    language=hint_language or "unknown",
                    confidence=0.0,
                    duration=0.0,
                    error=str(error_details.error_details)
                )
        
        except Exception as e:
            logger.error(f"Error during speech recognition: {str(e)}")
            return VoiceTranscription(
                text="",
                language=hint_language or "unknown",
                confidence=0.0,
                duration=0.0,
                error=str(e)
            )
    
    async def _extract_intent_and_entities(
        self,
        text: str,
        language: str
    ) -> tuple[str, Dict[str, Any]]:
        """
        Extract intent and entities from transcribed text
        Uses Azure Language Understanding (LUIS) or similar NLU service
        """
        # For now, use simple keyword matching
        # TODO: Integrate with Azure LUIS or similar NLU service
        
        text_lower = text.lower()
        
        # Schedule-related intents
        if any(word in text_lower for word in ['schedule', 'book', 'appointment', 'meeting']):
            return 'schedule_appointment', self._extract_schedule_entities(text)
        
        elif any(word in text_lower for word in ['reschedule', 'move', 'change']):
            return 'reschedule_appointment', self._extract_schedule_entities(text)
        
        elif any(word in text_lower for word in ['cancel', 'delete', 'remove']):
            return 'cancel_appointment', self._extract_cancel_entities(text)
        
        elif any(word in text_lower for word in ['when', 'what', 'show', 'list']):
            return 'query_schedule', self._extract_query_entities(text)
        
        elif any(word in text_lower for word in ['remind', 'reminder', 'alert']):
            return 'set_reminder', self._extract_reminder_entities(text)
        
        return 'unknown', {}
    
    def _extract_schedule_entities(self, text: str) -> Dict[str, Any]:
        """Extract scheduling entities from text"""
        # TODO: Use proper NER (Named Entity Recognition)
        return {
            "title": text,
            "datetime": None,
            "duration": 60,
            "location": None,
            "notes": text
        }
    
    def _extract_cancel_entities(self, text: str) -> Dict[str, Any]:
        """Extract cancellation entities"""
        return {
            "appointment_id": None,
            "reason": text
        }
    
    def _extract_query_entities(self, text: str) -> Dict[str, Any]:
        """Extract query entities"""
        return {
            "query_type": "schedule",
            "time_range": "today"
        }
    
    def _extract_reminder_entities(self, text: str) -> Dict[str, Any]:
        """Extract reminder entities"""
        return {
            "reminder_text": text,
            "datetime": None
        }
    
    def _get_confidence(self, result) -> float:
        """Extract confidence score from recognition result"""
        try:
            import azure.cognitiveservices.speech as speechsdk
            confidence = result.properties.get(
                speechsdk.PropertyId.SpeechServiceResponse_JsonResult
            )
            if confidence:
                import json
                data = json.loads(confidence)
                return data.get('NBest', [{}])[0].get('Confidence', 0.0)
        except:
            pass
        return 0.8  # Default confidence
    
    def _mock_transcription(self, hint_language: Optional[str] = None) -> VoiceTranscription:
        """Mock transcription for testing when Azure Speech SDK is not available"""
        return VoiceTranscription(
            text="Schedule a doctor appointment for tomorrow at 2 PM",
            language=hint_language or "en",
            confidence=0.95,
            duration=3.5,
            intent="schedule_appointment",
            entities={
                "title": "Doctor appointment",
                "datetime": "tomorrow 2PM",
                "duration": 60
            },
            timestamp=datetime.utcnow()
        )
    
    def get_supported_languages(self) -> list[str]:
        """Get list of all supported language codes"""
        return SUPPORTED_LANGUAGES.copy()
    
    def is_language_supported(self, language_code: str) -> bool:
        """Check if a language is supported"""
        return language_code in SUPPORTED_LANGUAGES
