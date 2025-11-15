"""
Base Voice Platform Integration
Abstract class for all voice assistant platforms
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseVoicePlatform(ABC):
    """Base class for voice assistant platform integrations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.platform_name = self.__class__.__name__
        
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with the voice platform"""
        pass
    
    @abstractmethod
    async def handle_intent(self, intent: str, slots: Dict[str, Any], 
                          user_id: str) -> Dict[str, Any]:
        """Process voice intent from the platform"""
        pass
    
    @abstractmethod
    async def send_response(self, response: Dict[str, Any]) -> bool:
        """Send response back to the voice platform"""
        pass
    
    @abstractmethod
    async def register_skill(self, skill_config: Dict[str, Any]) -> bool:
        """Register/update skill on the platform"""
        pass
    
    async def log_interaction(self, user_id: str, intent: str, 
                             success: bool, metadata: Dict[str, Any] = None):
        """Log voice interaction for analytics"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "platform": self.platform_name,
            "user_id": user_id,
            "intent": intent,
            "success": success,
            "metadata": metadata or {}
        }
        logger.info(f"Voice interaction logged: {log_entry}")
        return log_entry
    
    def validate_request(self, request: Dict[str, Any]) -> bool:
        """Validate incoming request from platform"""
        required_fields = ['user_id', 'intent', 'timestamp']
        return all(field in request for field in required_fields)
