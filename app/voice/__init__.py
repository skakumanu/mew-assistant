"""
Voice Command Processing Module
Supports multilingual speech recognition and natural language understanding
"""

from .command_parser import CommandParser
from .language_detector import LanguageDetector
from .voice_processor import VoiceProcessor

__all__ = ["VoiceProcessor", "LanguageDetector", "CommandParser"]
