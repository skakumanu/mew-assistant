"""
Scheduler service for managing appointments and sessions.
"""
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4


class SchedulerService:
    """Service for scheduling sessions and appointments."""
    
    def __init__(self):
        """Initialize scheduler service."""
        self.sessions = {}
    
    def schedule_session(
        self,
        user_id: str,
        session_type: str,
        date: str,
        time: str,
        duration: int
    ) -> Dict:
        """
        Schedule a new session.
        
        Args:
            user_id: User ID
            session_type: Type of session (tutoring, therapy, etc.)
            date: Session date (YYYY-MM-DD)
            time: Session time (HH:MM)
            duration: Duration in minutes
            
        Returns:
            Dictionary with session details
        """
        session_id = f"sess_{uuid4().hex[:8]}"
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "session_type": session_type,
            "date": date,
            "time": time,
            "duration": duration,
            "status": "scheduled",
            "created_at": datetime.utcnow().isoformat()
        }
        self.sessions[session_id] = session_data
        return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID."""
        return self.sessions.get(session_id)
    
    def list_sessions(self, user_id: str) -> List[Dict]:
        """List all sessions for a user."""
        return [
            session for session in self.sessions.values()
            if session["user_id"] == user_id
        ]
    
    def cancel_session(self, session_id: str) -> bool:
        """Cancel a session."""
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "cancelled"
            return True
        return False
