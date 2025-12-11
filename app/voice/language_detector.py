"""
Language Detection Module with Automatic Detection Support
Supports multiple detection backends for robustness
"""

from typing import Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


class LanguageDetector:
    """Automatically detect language from text input with confidence scoring"""
    
    # Comprehensive locale mapping for all supported languages
    LOCALE_MAP = {
        'en': 'en-US', 'es': 'es-ES', 'fr': 'fr-FR', 'de': 'de-DE',
        'it': 'it-IT', 'pt': 'pt-BR', 'zh-cn': 'zh-CN', 'zh-tw': 'zh-TW',
        'ja': 'ja-JP', 'ko': 'ko-KR', 'ar': 'ar-SA', 'hi': 'hi-IN', 
        'ru': 'ru-RU', 'nl': 'nl-NL', 'pl': 'pl-PL', 'tr': 'tr-TR',
        'vi': 'vi-VN', 'th': 'th-TH'
    }
    
    def __init__(self):
        self._init_detectors()
    
    def _init_detectors(self):
        """Initialize multiple detection backends for reliability"""
        # Primary: langdetect (fast, lightweight)
        try:
            from langdetect import detect_langs, LangDetectException
            self.detect_langs = detect_langs
            self.LangDetectException = LangDetectException
            self.langdetect_available = True
            logger.info("langdetect initialized for automatic language detection")
        except ImportError:
            logger.warning("langdetect not available. Install: pip install langdetect")
            self.langdetect_available = False
        
        # Secondary: lingua-language-detector (more accurate for short texts)
        try:
            from lingua import LanguageDetectorBuilder
            self.lingua_detector = LanguageDetectorBuilder.from_all_languages().build()
            self.lingua_available = True
            logger.info("lingua-language-detector initialized as backup")
        except ImportError:
            self.lingua_available = False
    
    async def detect(self, text: str, return_confidence: bool = False) -> str | Tuple[str, float]:
        """
        Automatically detect language from text
        
        Args:
            text: Input text to detect language from
            return_confidence: If True, returns (language, confidence) tuple
            
        Returns:
            Language code (e.g., 'en-US') or tuple with confidence score
        """
        if not text or len(text.strip()) < 3:
            return ('en-US', 0.5) if return_confidence else 'en-US'
        
        # Try primary detector
        if self.langdetect_available:
            result = await self._detect_with_langdetect(text)
            if result:
                lang, confidence = result
                return (lang, confidence) if return_confidence else lang
        
        # Fallback to secondary detector
        if self.lingua_available:
            result = await self._detect_with_lingua(text)
            if result:
                lang, confidence = result
                return (lang, confidence) if return_confidence else lang
        
        # Ultimate fallback
        logger.warning("No language detector available, defaulting to en-US")
        return ('en-US', 0.3) if return_confidence else 'en-US'
    
    async def _detect_with_langdetect(self, text: str) -> Optional[Tuple[str, float]]:
        """Detect language using langdetect"""
        try:
            langs = self.detect_langs(text)
            if not langs:
                return None
            
            primary = langs[0]
            locale = self.LOCALE_MAP.get(primary.lang, 'en-US')
            confidence = primary.prob
            
            logger.info(f"Language detected: {locale} (confidence: {confidence:.2f})")
            return (locale, confidence)
            
        except self.LangDetectException as e:
            logger.debug(f"langdetect failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return None
    
    async def _detect_with_lingua(self, text: str) -> Optional[Tuple[str, float]]:
        """Detect language using lingua (fallback)"""
        try:
            detection = self.lingua_detector.detect_language_of(text)
            if not detection:
                return None
            
            lang_code = detection.iso_code_639_1.name.lower()
            locale = self.LOCALE_MAP.get(lang_code, 'en-US')
            confidence = 0.8  # lingua doesn't provide confidence scores
            
            logger.info(f"Language detected (lingua): {locale}")
            return (locale, confidence)
            
        except Exception as e:
            logger.error(f"Lingua detection error: {e}")
            return None
    
    async def detect_multiple(self, text: str, top_n: int = 3) -> List[Tuple[str, float]]:
        """
        Detect multiple possible languages with confidence scores
        Useful for multilingual content or ambiguous text
        """
        if not self.langdetect_available:
            return [('en-US', 0.5)]
        
        try:
            langs = self.detect_langs(text)
            results = []
            
            for lang_result in langs[:top_n]:
                locale = self.LOCALE_MAP.get(lang_result.lang, 'en-US')
                results.append((locale, lang_result.prob))
            
            return results
            
        except Exception as e:
            logger.error(f"Multi-language detection error: {e}")
            return [('en-US', 0.5)]
