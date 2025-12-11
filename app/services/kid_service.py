"""
Kid Service
Business logic for kid-friendly features
Handles activity suggestions, schedule changes, rewards, and parent-kid communication
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import random

from ..database.models import User
from ..schemas.kid_friendly import TimeOfDay, ActivityItem, ChangeReason


class KidService:
    """Service for kid-friendly operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_activity_suggestion(
        self,
        kid_id: int,
        activity: str,
        description: str,
        preferred_time: TimeOfDay,
        emoji: str
    ) -> Dict[str, Any]:
        """Create a new activity suggestion from kid"""
        suggestion = {
            "id": self._generate_id(),
            "kid_id": kid_id,
            "activity": activity,
            "description": description,
            "preferred_time": preferred_time,
            "emoji": emoji,
            "status": "pending_approval",
            "created_at": datetime.utcnow()
        }
        
        # In real implementation, save to database
        # For now, return the suggestion object
        return type('Suggestion', (), suggestion)
    
    def get_parent(self, kid_id: int) -> Optional[User]:
        """Get parent associated with kid account"""
        kid = self.db.query(User).filter(User.id == kid_id).first()
        if not kid or not kid.parent_id:
            return None
        
        return self.db.query(User).filter(User.id == kid.parent_id).first()
    
    def get_kid_schedule(self, kid_id: int) -> Dict[str, List[ActivityItem]]:
        """Get kid's schedule in simplified format"""
        # Mock data - in real implementation, fetch from database
        today = [
            ActivityItem(
                id=1,
                name="Math Practice",
                emoji="📚",
                time="morning",
                is_fun=False,
                description="30 minutes of fun math games"
            ),
            ActivityItem(
                id=2,
                name="Park Time",
                emoji="🏃",
                time="afternoon",
                is_fun=True,
                description="Play at the park!"
            ),
            ActivityItem(
                id=3,
                name="Reading Time",
                emoji="📖",
                time="evening",
                is_fun=True,
                description="Story time with your favorite book"
            )
        ]
        
        tomorrow = [
            ActivityItem(
                id=4,
                name="Music Class",
                emoji="🎵",
                time="morning",
                is_fun=True,
                description="Learn a new song!"
            ),
            ActivityItem(
                id=5,
                name="Art Project",
                emoji="🎨",
                time="afternoon",
                is_fun=True,
                description="Create something beautiful"
            )
        ]
        
        this_week = [
            ActivityItem(
                id=6,
                name="Swimming",
                emoji="🏊",
                time="afternoon",
                is_fun=True,
                description="Splash and have fun! (Wednesday)"
            ),
            ActivityItem(
                id=7,
                name="Doctor Visit",
                emoji="👨‍⚕️",
                time="morning",
                is_fun=False,
                description="Quick checkup (Thursday)"
            ),
            ActivityItem(
                id=8,
                name="Movie Night",
                emoji="🎬",
                time="evening",
                is_fun=True,
                description="Family movie time! (Friday)"
            )
        ]
        
        return {
            "today": today,
            "tomorrow": tomorrow,
            "this_week": this_week
        }
    
    def get_daily_fun_fact(self) -> str:
        """Return a random kid-friendly fun fact"""
        facts = [
            "Did you know? A group of flamingos is called a 'flamboyance'! 🦩",
            "Fun fact: Honey never spoils! Ancient honey is still edible! 🍯",
            "Amazing: Butterflies taste with their feet! 🦋",
            "Wow: A cloud can weigh more than a million pounds! ☁️",
            "Cool: Penguins propose with pebbles! 🐧",
            "Neat: An octopus has three hearts! 🐙",
            "Awesome: You're doing great today! Keep being amazing! ⭐"
        ]
        return random.choice(facts)
    
    def record_activity_reaction(
        self,
        kid_id: int,
        activity_id: int,
        emoji: str,
        feeling: Optional[str] = None
    ):
        """Record kid's emotional reaction to an activity"""
        reaction = {
            "kid_id": kid_id,
            "activity_id": activity_id,
            "emoji": emoji,
            "feeling": feeling,
            "recorded_at": datetime.utcnow()
        }
        
        # In real implementation, save to database and analyze patterns
        return reaction
    
    def create_change_request(
        self,
        kid_id: int,
        activity_id: int,
        reason: ChangeReason,
        preferred_alternative: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a request to change scheduled activity"""
        request = {
            "id": self._generate_id(),
            "kid_id": kid_id,
            "activity_id": activity_id,
            "reason": reason,
            "preferred_alternative": preferred_alternative,
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        return type('ChangeRequest', (), request)
    
    def get_sticker_collection(self, kid_id: int) -> Dict[str, Any]:
        """Get kid's earned stickers and rewards"""
        # Mock data - in real implementation, fetch from database
        stickers = [
            {"id": "star", "emoji": "⭐", "name": "Superstar", "count": 5},
            {"id": "rainbow", "emoji": "🌈", "name": "Rainbow Achiever", "count": 3},
            {"id": "heart", "emoji": "💝", "name": "Kindness Award", "count": 8},
            {"id": "trophy", "emoji": "🏆", "name": "Champion", "count": 2}
        ]
        
        total = sum(s["count"] for s in stickers)
        
        return {
            "count": total,
            "collection": stickers,
            "next_reward": {
                "at": 25,
                "remaining": max(0, 25 - total),
                "reward": "Mystery Sticker! 🎁"
            }
        }
    
    def award_sticker(self, kid_id: int, activity_id: int, sticker_type: str):
        """Award a sticker for completing an activity"""
        # In real implementation, save to database
    
    def _generate_id(self) -> int:
        """Generate a unique ID"""
        import time
        return int(time.time() * 1000) % 100000000
