"""
Security validation and threat detection.
"""
import re
from typing import Dict


class SecurityValidator:
    """Validate security requirements and detect threats."""
    
    def __init__(self):
        """Initialize security validator."""
        self.threat_patterns = [
            r"<script",
            r"javascript:",
            r"onerror=",
            r"onclick=",
            r"eval\(",
            r"exec\("
        ]
    
    def detect_injection(self, text: str) -> bool:
        """Detect potential injection attacks."""
        for pattern in self.threat_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def validate_input(self, data: Dict) -> Dict[str, bool]:
        """Validate input data for security threats."""
        results = {}
        for key, value in data.items():
            if isinstance(value, str):
                results[key] = not self.detect_injection(value)
            else:
                results[key] = True
        return results
    
    def sanitize_input(self, text: str) -> str:
        """Sanitize input by removing dangerous patterns."""
        for pattern in self.threat_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        return text
