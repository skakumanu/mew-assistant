"""
Content Filter
Safety filters for kid-friendly content
Ensures appropriate language and detects concerning messages
"""
import re


class ContentFilter:
    """Content filtering and safety checks for kid interactions"""
    
    # Words that indicate potential safety concerns
    DISTRESS_KEYWORDS = [
        "hurt", "scared", "afraid", "help me", "emergency",
        "don't feel safe", "someone hurt me", "in danger",
        "very sick", "can't breathe", "bleeding"
    ]
    
    # Inappropriate words to filter
    INAPPROPRIATE_WORDS = [
        # Add inappropriate words here - keeping list minimal for example
        "hate", "stupid", "dumb", "shut up"
    ]
    
    def is_kid_safe(self, text: str) -> bool:
        """
        Check if content is appropriate for kids
        
        Args:
            text: Input text to check
            
        Returns:
            True if content is safe, False otherwise
        """
        if not text:
            return True
        
        text_lower = text.lower()
        
        # Check for inappropriate words
        for word in self.INAPPROPRIATE_WORDS:
            if word in text_lower:
                return False
        
        # Check for excessive caps (shouting)
        if len(text) > 10 and text.isupper():
            return False
        
        return True
    
    def detect_distress(self, text: str) -> bool:
        """
        Detect if message indicates distress or safety concern
        
        Args:
            text: Input text to analyze
            
        Returns:
            True if distress is detected, False otherwise
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check for distress keywords
        for keyword in self.DISTRESS_KEYWORDS:
            if keyword in text_lower:
                return True
        
        # Check for multiple question marks or exclamation points (urgency)
        if text.count('!') >= 3 or text.count('?') >= 3:
            return True
        
        return False
    
    def sanitize_kid_input(self, text: str) -> str:
        """
        Clean and sanitize kid input
        
        Args:
            text: Input text to sanitize
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Remove excessive punctuation
        text = re.sub(r'([!?.]){3,}', r'\1\1', text)
        
        # Remove excessive spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Trim
        text = text.strip()
        
        return text
    
    def get_age_appropriate_response(self, age: int, response_type: str) -> str:
        """
        Get age-appropriate response message
        
        Args:
            age: Child's age
            response_type: Type of response needed
            
        Returns:
            Age-appropriate message
        """
        responses = {
            "success": {
                "5-7": "Yay! Great job! 🌟",
                "8-10": "Awesome work! Keep it up! ⭐",
                "11-13": "Nice! You're doing great! 👍"
            },
            "error": {
                "5-7": "Oops! Let's try again together! 🤗",
                "8-10": "Something went wrong. Want to try again? 💙",
                "11-13": "That didn't work. Let's figure it out! 💡"
            },
            "waiting": {
                "5-7": "Just a moment! Almost ready! ⏰",
                "8-10": "Hang tight! Working on it! 🔄",
                "11-13": "Processing... Won't be long! ⚙️"
            }
        }
        
        # Determine age group
        if age <= 7:
            age_group = "5-7"
        elif age <= 10:
            age_group = "8-10"
        else:
            age_group = "11-13"
        
        return responses.get(response_type, {}).get(age_group, "Got it! 👍")
    
    def mask_sensitive_info(self, text: str) -> str:
        """
        Mask potential sensitive information in kid's messages
        
        Args:
            text: Input text
            
        Returns:
            Text with sensitive info masked
        """
        # Mask potential phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[phone]', text)
        
        # Mask potential email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[email]', text)
        
        # Mask potential addresses with street numbers
        text = re.sub(r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b', '[address]', text, flags=re.IGNORECASE)
        
        return text
