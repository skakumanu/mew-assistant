"""
Language Detection Module
"""

from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Detect language from text input"""
    
    def __init__(self):
        self._init_detector()
    
    def _init_detector(self):
        try:
            from langdetect import detect_langs, LangDetectException
            self.detect_langs = detect_langs
            self.LangDetectException = LangDetectException
            self.detector_available = True
        except ImportError:
            logger.warning("langdetect not available. Install: pip install langdetect")
            self.detector_available = False
    
    async def detect(self, text: str) -> str:
        """Detect language from text"""
        if not self.detector_available:
            return "en-US"
        
        try:
            langs = self.detect_langs(text)
            if not langs:
                return "en-US"
            
            primary = langs[0]
            locale_map = {
                'en': 'en-US', 'es': 'es-ES', 'fr': 'fr-FR', 'de': 'de-DE',
                'it': 'it-IT', 'pt': 'pt-BR', 'zh-cn': 'zh-CN', 'ja': 'ja-JP',
                'ko': 'ko-KR', 'ar': 'ar-SA', 'hi': 'hi-IN', 'ru': 'ru-RU'
            }
            
            return locale_map.get(primary.lang, 'en-US')
            
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return "en-US"
