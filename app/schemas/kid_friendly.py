"""
Kid-Friendly Schemas
Pydantic models for kid-friendly endpoints with simple, intuitive fields
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TimeOfDay(str, Enum):
    """Simple time descriptions kids understand"""
    MORNING = "morning"
    LUNCH_TIME = "lunch_time"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    BEDTIME = "bedtime"


class ActivityEmoji(str, Enum):
    """Pre-approved emoji for activities"""
    HAPPY = "😊"
    LOVE = "😍"
    SAD = "😢"
    WORRIED = "😟"
    TIRED = "😴"
    EXCITED = "🤩"
    SICK = "🤒"
    THINKING = "🤔"
    THUMBS_UP = "👍"
    HEART = "💙"


class ChangeReason(str, Enum):
    """Simple reasons kids can select"""
    TIRED = "I'm tired"
    NOT_FEELING_GOOD = "I don't feel good"
    WANT_DIFFERENT = "I want to do something different"
    TOO_HARD = "It's too hard"
    SCARED = "I'm scared"
    NEED_BREAK = "I need a break"


class KidActivitySuggestion(BaseModel):
    """Request to suggest a new activity"""
    activity_name: str = Field(..., max_length=100, description="What do you want to do?")
    activity_description: str = Field(..., max_length=500, description="Tell us more!")
    when: TimeOfDay = Field(..., description="When would you like to do this?")
    emoji: str = Field(default="😊", description="Pick an emoji!")
    
    @validator('activity_name', 'activity_description')
    def validate_content(cls, v):
        """Basic content validation"""
        if not v or not v.strip():
            raise ValueError("Please tell us what you'd like to do!")
        return v.strip()


class KidScheduleRequest(BaseModel):
    """Request to change scheduled activity"""
    activity_id: int = Field(..., description="Which activity?")
    reason: ChangeReason = Field(..., description="Why do you want to change it?")
    alternative: Optional[str] = Field(None, max_length=200, description="What would you rather do?")


class ActivityItem(BaseModel):
    """Simplified activity display for kids"""
    id: int
    name: str
    emoji: str
    time: str  # Simple format like "morning" or "after lunch"
    is_fun: bool = False  # Highlight fun activities
    can_change: bool = True
    description: Optional[str] = None


class KidScheduleResponse(BaseModel):
    """Kid's schedule in simple format"""
    greeting: str
    today: List[ActivityItem]
    tomorrow: List[ActivityItem]
    this_week: List[ActivityItem]
    fun_fact: str  # Daily fun fact to engage kids


class EmojiReaction(BaseModel):
    """Kid reacts to an activity with emoji"""
    activity_id: int
    emoji: str = Field(..., description="How do you feel about this?")
    feeling: Optional[str] = Field(None, max_length=100, description="Want to tell us more?")
    
    @validator('emoji')
    def validate_emoji(cls, v):
        """Ensure only approved emoji"""
        approved = ["😊", "😍", "😢", "😟", "😴", "🤩", "🤒", "😰", "😡", "🥳", "😇"]
        if v not in approved:
            raise ValueError(f"Please use one of these: {', '.join(approved)}")
        return v


class SimplifiedResponse(BaseModel):
    """Simple, encouraging response for kids"""
    success: bool
    message: str  # Always positive and encouraging
    emoji: str
    data: Optional[Dict[str, Any]] = None


class ParentApprovalRequest(BaseModel):
    """Parent reviews kid's request"""
    request_id: int
    approved: bool
    parent_note: Optional[str] = None
    alternative_suggestion: Optional[str] = None


class StickerReward(BaseModel):
    """Sticker earned for completing activity"""
    sticker_id: str
    emoji: str
    name: str
    earned_at: datetime
    activity_completed: str


class KidProfile(BaseModel):
    """Kid's profile with preferences"""
    id: int
    display_name: str
    avatar_emoji: str = "😊"
    favorite_activities: List[str] = []
    total_stickers: int = 0
    level: int = 1
    parent_id: int
    communication_style: str = "visual"  # visual, simple_text, audio
    
    class Config:
        from_attributes = True
