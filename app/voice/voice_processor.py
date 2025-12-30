"""
Voice Processor - Handles speech-to-text with multilingual support
Uses Azure Speech Services for enterprise-grade recognition
"""

import logging
from datetime import datetime
from typing import Dict, Optional

try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    speechsdk = None

from app.database import get_db
from app.database.models import VoiceCommand
from app.schemas.voice import VoiceCommandResponse
from app.utils.config import settings

from .command_parser import CommandParser
from .language_detector import LanguageDetector

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """Process voice commands with multilingual support"""

    SUPPORTED_LANGUAGES = {
        "en-US": "English (US)",
        "en-GB": "English (UK)",
        "es-ES": "Spanish (Spain)",
        "es-MX": "Spanish (Mexico)",
        "fr-FR": "French",
        "de-DE": "German",
        "it-IT": "Italian",
        "pt-BR": "Portuguese (Brazil)",
        "zh-CN": "Chinese (Simplified)",
        "zh-TW": "Chinese (Traditional)",
        "ja-JP": "Japanese",
        "ko-KR": "Korean",
        "ar-SA": "Arabic",
        "hi-IN": "Hindi",
        "ru-RU": "Russian",
        "nl-NL": "Dutch",
        "pl-PL": "Polish",
        "tr-TR": "Turkish",
        "vi-VN": "Vietnamese",
        "th-TH": "Thai",
    }

    def __init__(self):
        self.language_detector = LanguageDetector()
        self.command_parser = CommandParser()
        self._init_azure_speech()

    def _init_azure_speech(self):
        """Initialize Azure Speech Services"""
        if not speechsdk:
            logger.warning(
                "Azure Speech SDK not available. Install with: pip install azure-cognitiveservices-speech"
            )
            self.speech_config = None
            return

        try:
            self.speech_config = speechsdk.SpeechConfig(
                subscription=settings.AZURE_SPEECH_KEY,
                region=settings.AZURE_SPEECH_REGION,
            )
            self.speech_config.set_property(
                speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs,
                "5000",
            )
            logger.info("Azure Speech Services initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Azure Speech: {e}")
            self.speech_config = None

    async def process_voice_input(
        self,
        audio_data: bytes,
        user_id: int,
        session_id: Optional[str] = None,
        preferred_language: Optional[str] = None,
    ) -> VoiceCommandResponse:
        """Process voice input and convert to actionable command"""
        try:
            transcription = await self._speech_to_text(audio_data, preferred_language)

            if not transcription:
                return VoiceCommandResponse(
                    success=False,
                    error="Could not transcribe audio",
                    detected_language=preferred_language,
                )

            detected_language = preferred_language or await self.language_detector.detect(
                transcription
            )
            parsed_command = await self.command_parser.parse(
                text=transcription, language=detected_language, user_id=user_id
            )

            db = next(get_db())
            voice_command = VoiceCommand(
                user_id=user_id,
                session_id=session_id,
                transcription=transcription,
                detected_language=detected_language,
                confidence_score=parsed_command.get("confidence", 0.0),
                intent=parsed_command.get("intent"),
                entities=parsed_command.get("entities", {}),
                raw_audio_path=await self._store_audio(audio_data, user_id),
            )
            db.add(voice_command)
            db.commit()
            db.refresh(voice_command)

            return VoiceCommandResponse(
                success=True,
                command_id=voice_command.id,
                transcription=transcription,
                detected_language=detected_language,
                intent=parsed_command.get("intent"),
                entities=parsed_command.get("entities"),
                confidence=parsed_command.get("confidence"),
                suggested_action=parsed_command.get("action"),
            )

        except Exception as e:
            logger.error(f"Voice processing error: {e}", exc_info=True)
            return VoiceCommandResponse(success=False, error=str(e))

    async def _speech_to_text(
        self, audio_data: bytes, language: Optional[str] = None
    ) -> Optional[str]:
        """Convert speech to text with automatic language detection"""
        if not self.speech_config:
            return await self._whisper_fallback(audio_data)

        try:
            # Enable automatic language detection if no language specified
            if not language:
                auto_detect_source_language_config = (
                    speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
                        languages=list(self.SUPPORTED_LANGUAGES.keys())
                    )
                )

                stream = speechsdk.audio.PushAudioInputStream()
                stream.write(audio_data)
                stream.close()

                audio_config = speechsdk.audio.AudioConfig(stream=stream)
                speech_recognizer = speechsdk.SpeechRecognizer(
                    speech_config=self.speech_config,
                    auto_detect_source_language_config=auto_detect_source_language_config,
                    audio_config=audio_config,
                )

                result = speech_recognizer.recognize_once()

                if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    detected_lang = result.properties.get(
                        speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult
                    )
                    logger.info(f"Auto-detected language: {detected_lang}")
                    return result.text

                return None
            else:
                # Use specified language
                if language in self.SUPPORTED_LANGUAGES:
                    self.speech_config.speech_recognition_language = language

                stream = speechsdk.audio.PushAudioInputStream()
                stream.write(audio_data)
                stream.close()

                audio_config = speechsdk.audio.AudioConfig(stream=stream)
                speech_recognizer = speechsdk.SpeechRecognizer(
                    speech_config=self.speech_config, audio_config=audio_config
                )

                result = speech_recognizer.recognize_once()

                if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    return result.text

                return None

        except Exception as e:
            logger.error(f"Azure Speech error: {e}")
            return await self._whisper_fallback(audio_data)

    async def _whisper_fallback(self, audio_data: bytes) -> Optional[str]:
        """Fallback to OpenAI Whisper with automatic language detection"""
        try:
            from io import BytesIO

            import openai

            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            audio_file = BytesIO(audio_data)
            audio_file.name = "audio.wav"

            # Whisper automatically detects language when not specified
            transcription = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",  # Get language detection info
            )

            if hasattr(transcription, "language"):
                logger.info(f"Whisper detected language: {transcription.language}")

            return transcription.text if hasattr(transcription, "text") else str(transcription)

        except Exception as e:
            logger.error(f"Whisper fallback error: {e}")
            return None

    async def _store_audio(self, audio_data: bytes, user_id: int) -> str:
        """Store audio file for audit"""
        try:
            import hashlib
            from pathlib import Path

            audio_dir = Path("data/voice_recordings") / str(user_id)
            audio_dir.mkdir(parents=True, exist_ok=True)

            audio_hash = hashlib.sha256(audio_data).hexdigest()[:16]
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{audio_hash}.wav"
            filepath = audio_dir / filename

            with open(filepath, "wb") as f:
                f.write(audio_data)

            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to store audio: {e}")
            return ""

    async def get_supported_languages(self) -> Dict[str, str]:
        return self.SUPPORTED_LANGUAGES
