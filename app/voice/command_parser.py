"""
Natural Language Command Parser
"""

from typing import Dict, Any, Optional
import logging
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CommandParser:
    """Parse natural language commands"""
    
    INTENT_PATTERNS = {
        'schedule': [r'\b(schedule|book|set|arrange)\b', r'\b(appointment|meeting|session)\b'],
        'reschedule': [r'\b(reschedule|change|move)\b'],
        'cancel': [r'\b(cancel|delete|remove)\b'],
        'summary': [r'\b(summary|report|update)\b'],
        'tutoring': [r'\b(homework|study|learn)\b'],
        'question': [r'\b(what|when|where|how|why)\b']
    }
    
    async def parse(self, text: str, language: str, user_id: int) -> Dict[str, Any]:
        """Parse command into structured format"""
        text_lower = text.lower()
        
        intent = 'general'
        max_matches = 0
        
        for intent_name, patterns in self.INTENT_PATTERNS.items():
            matches = sum(1 for p in patterns if re.search(p, text_lower, re.I))
            if matches > max_matches:
                max_matches = matches
                intent = intent_name
        
        entities = {}
        datetime_entity = self._extract_datetime(text_lower)
        if datetime_entity:
            entities['datetime'] = datetime_entity
        
        return {
            'intent': intent,
            'entities': entities,
            'confidence': 0.8 if max_matches > 0 else 0.5,
            'action': {'type': 'general_response', 'parameters': {}}
        }
    
    def _extract_datetime(self, text: str) -> Optional[str]:
        """Extract datetime from text"""
        now = datetime.now()
        
        if 'tomorrow' in text:
            return (now + timedelta(days=1)).isoformat()
        elif 'today' in text:
            return now.isoformat()
        elif 'next week' in text:
            return (now + timedelta(weeks=1)).isoformat()
        
        return None
