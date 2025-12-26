"""
Voice Platform Integrations for Mew Assistant
Supports Siri, Alexa, Google Assistant, Tesla, and more
"""

from .alexa_integration import AlexaIntegration
from .base_voice_platform import BaseVoicePlatform
from .google_assistant_integration import GoogleAssistantIntegration
from .siri_integration import SiriIntegration
from .tesla_integration import TeslaIntegration

__all__ = [
    "SiriIntegration",
    "AlexaIntegration",
    "GoogleAssistantIntegration",
    "TeslaIntegration",
    "BaseVoicePlatform",
]
