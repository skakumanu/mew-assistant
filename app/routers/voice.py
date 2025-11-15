"""
Voice Command Router
Handles voice command endpoints with automatic language detection for 100+ languages
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from app.database import get_db
from app.models.user import User
from app.schemas.voice import (
    VoiceCommandResponse,
    VoiceSessionCreate,
    VoiceSessionResponse,
    SupportedLanguagesResponse,
    VoiceLanguageInfo,
    VoiceStatisticsResponse
)
from app.services.voice_service import VoiceService, SUPPORTED_LANGUAGES
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/voice", tags=["voice"])
logger = logging.getLogger(__name__)


@router.post("/command", response_model=VoiceCommandResponse)
async def process_voice_command(
    audio: UploadFile = File(..., description="Audio file (WAV, MP3, OGG, M4A, FLAC)"),
    session_id: Optional[str] = Form(None),
    hint_language: Optional[str] = Form(None, description="Optional language hint (e.g., 'es' for Spanish)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process voice command with automatic language detection for 100+ languages
    
    Supports all major world languages including:
    - **Major**: English, Spanish, Chinese, Hindi, Arabic, Bengali, Portuguese, Russian, Japanese
    - **European**: French, German, Italian, Polish, Ukrainian, Dutch, Czech, Greek, Swedish
    - **African**: Swahili, Hausa, Yoruba, Igbo, Zulu, Xhosa, Afrikaans, Somali
    - **Asian**: Korean, Vietnamese, Thai, Indonesian, Malay, Nepali, Sinhala, Khmer
    - **And 80+ more languages!**
    
    The system automatically detects the spoken language and processes commands naturally.
    
    **Examples in different languages:**
    - English: "Schedule a doctor appointment for tomorrow at 2 PM"
    - Spanish: "Programa una cita con el médico para mañana a las 2 PM"
    - French: "Planifier un rendez-vous chez le médecin demain à 14h"
    - Hindi: "कल दोपहर 2 बजे डॉक्टर की नियुक्ति निर्धारित करें"
    """
    try:
        # Validate hint language if provided
        if hint_language and hint_language not in SUPPORTED_LANGUAGES:
            raise HTTPException(
                status_code=400,
                detail=f"Language '{hint_language}' not supported. Use /voice/languages to see all 100+ supported languages."
            )
        
        # Read audio data
        audio_data = await audio.read()
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        if len(audio_data) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="Audio file too large (max 10MB)")
        
        # Process voice command with automatic language detection
        voice_service = VoiceService(db)
        result = await voice_service.process_voice_command(
            audio_data=audio_data,
            user_id=current_user.id,
            session_id=session_id,
            hint_language=hint_language
        )
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        
        logger.info(
            f"Voice command processed successfully in {result.language_name} "
            f"({result.detected_language}): {result.transcription.text}"
        )
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice command error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages", response_model=List[VoiceLanguageInfo])
async def get_supported_languages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complete list of all 100+ supported languages for voice recognition
    
    Returns language codes (ISO 639-1/639-3) and full language names.
    Use these codes as hint_language parameter for better detection accuracy.
    
    **Regions covered:**
    - Major World Languages (40+)
    - European Languages (25+)
    - African Languages (15+)
    - Asian Languages (20+)
    - Middle Eastern, Pacific, and Native American languages
    """
    voice_service = VoiceService(db)
    languages = voice_service.get_supported_languages()
    
    return [
        VoiceLanguageInfo(code=lang["code"], name=lang["name"])
        for lang in languages
    ]


@router.get("/statistics", response_model=VoiceStatisticsResponse)
async def get_voice_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get voice command usage statistics for the current user
    
    Returns:
    - Total voice commands processed
    - Languages used (with percentage breakdown)
    - Primary language detected
    - Usage patterns
    
    Helps understand multilingual usage patterns in your family!
    """
    voice_service = VoiceService(db)
    stats = voice_service.get_language_statistics(current_user.id)
    
    return VoiceStatisticsResponse(**stats)


@router.post("/session/start", response_model=VoiceSessionResponse)
async def start_voice_session(
    session_data: VoiceSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a continuous voice session for natural conversation
    
    Use this for hands-free operation where multiple commands
    will be issued in sequence without repeated authentication.
    """
    try:
        from app.models.voice import VoiceSession
        import uuid
        
        session_id = str(uuid.uuid4())
        
        voice_session = VoiceSession(
            session_id=session_id,
            user_id=current_user.id,
            language=session_data.language
        )
        
        db.add(voice_session)
        db.commit()
        db.refresh(voice_session)
        
        return VoiceSessionResponse(
            session_id=voice_session.session_id,
            user_id=voice_session.user_id,
            language=voice_session.language,
            started_at=voice_session.started_at,
            command_count=voice_session.command_count
        )
        
    except Exception as e:
        logger.error(f"Session start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/{session_id}/end")
async def end_voice_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End a voice session"""
    try:
        from app.models.voice import VoiceSession
        from datetime import datetime
        
        session = db.query(VoiceSession).filter(
            VoiceSession.session_id == session_id,
            VoiceSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.ended_at = datetime.utcnow()
        db.commit()
        
        return {"message": "Session ended", "session_id": session_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session end error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
