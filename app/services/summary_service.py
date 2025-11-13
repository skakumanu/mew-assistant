"""
Summary service layer for caregiver summary generation.
Provides insights and recommendations for special needs families.
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
import json
from ..database.models import (
    CaregiverSummary as SummaryModel,
    Session as SessionModel,
    Message as MessageModel
)
from ..schemas.summary import SummaryRequest


class SummaryService:
    """Service class for caregiver summary generation."""
    
    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db
    
    def generate_summary(self, request: SummaryRequest) -> SummaryModel:
        """
        Generate a caregiver summary based on session data.
        
        Args:
            request: Summary generation request
            
        Returns:
            Generated summary object
            
        Example:
            >>> service = SummaryService(db)
            >>> summary = service.generate_summary(request)
        """
        # Get sessions for the period
        sessions = self._get_sessions_for_period(
            request.user_id,
            request.period_start,
            request.period_end,
            request.session_id
        )
        
        if not sessions:
            raise ValueError("No sessions found for the specified period")
        
        # Generate summary text
        summary_text = self._create_summary_text(sessions)
        
        # Extract key points
        key_points = self._extract_key_points(sessions)
        
        # Generate recommendations if requested
        recommendations = None
        if request.include_recommendations:
            recommendations = self._generate_recommendations(sessions)
        
        # Create summary record
        # Use the first session or the specified session
        target_session_id = request.session_id or sessions[0].id
        
        db_summary = SummaryModel(
            session_id=target_session_id,
            user_id=request.user_id,
            summary_text=summary_text,
            key_points=json.dumps(key_points) if key_points else None,
            recommendations=json.dumps(recommendations) if recommendations else None,
            period_start=request.period_start,
            period_end=request.period_end,
            generated_at=datetime.utcnow()
        )
        
        self.db.add(db_summary)
        self.db.commit()
        self.db.refresh(db_summary)
        
        return db_summary
    
    def get_summary(self, summary_id: int) -> Optional[SummaryModel]:
        """Get summary by ID."""
        return self.db.query(SummaryModel).filter(
            SummaryModel.id == summary_id
        ).first()
    
    def get_user_summaries(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[SummaryModel]:
        """
        Get all summaries for a user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of summaries to return
            
        Returns:
            List of summaries
        """
        return self.db.query(SummaryModel).filter(
            SummaryModel.user_id == user_id
        ).order_by(SummaryModel.generated_at.desc()).limit(limit).all()
    
    def _get_sessions_for_period(
        self,
        user_id: str,
        period_start: Optional[datetime],
        period_end: Optional[datetime],
        session_id: Optional[int]
    ) -> List[SessionModel]:
        """Get sessions for summary period."""
        if session_id:
            # Get specific session
            session = self.db.query(SessionModel).filter(
                SessionModel.id == session_id,
                SessionModel.user_id == user_id
            ).first()
            return [session] if session else []
        
        # Get sessions within period
        query = self.db.query(SessionModel).filter(
            SessionModel.user_id == user_id
        )
        
        if period_start:
            query = query.filter(SessionModel.created_at >= period_start)
        
        if period_end:
            query = query.filter(SessionModel.created_at <= period_end)
        
        return query.order_by(SessionModel.created_at.asc()).all()
    
    def _create_summary_text(self, sessions: List[SessionModel]) -> str:
        """
        Create summary text from sessions.
        This is a simple implementation - in production, use AI/LLM for better summaries.
        """
        session_count = len(sessions)
        
        # Count by type
        type_counts = {}
        for session in sessions:
            type_counts[session.session_type] = type_counts.get(session.session_type, 0) + 1
        
        # Build summary
        summary_parts = [
            f"Summary of {session_count} session(s) for the specified period."
        ]
        
        for session_type, count in type_counts.items():
            summary_parts.append(f"{count} {session_type} session(s) completed.")
        
        # Add status info
        completed = sum(1 for s in sessions if s.status.value == "completed")
        if completed > 0:
            summary_parts.append(f"{completed} session(s) successfully completed.")
        
        return " ".join(summary_parts)
    
    def _extract_key_points(self, sessions: List[SessionModel]) -> List[str]:
        """
        Extract key points from sessions.
        In production, use AI/NLP for better extraction.
        """
        key_points = []
        
        # Total sessions
        key_points.append(f"Total sessions: {len(sessions)}")
        
        # Sessions by type
        type_counts = {}
        for session in sessions:
            type_counts[session.session_type] = type_counts.get(session.session_type, 0) + 1
        
        for session_type, count in type_counts.items():
            key_points.append(f"{session_type.title()}: {count} sessions")
        
        # Completion rate
        completed = sum(1 for s in sessions if s.status.value == "completed")
        if len(sessions) > 0:
            completion_rate = (completed / len(sessions)) * 100
            key_points.append(f"Completion rate: {completion_rate:.0f}%")
        
        return key_points
    
    def _generate_recommendations(self, sessions: List[SessionModel]) -> List[str]:
        """
        Generate recommendations based on session data.
        In production, use AI for personalized recommendations.
        """
        recommendations = []
        
        # Check for consistency
        if len(sessions) >= 3:
            recommendations.append("Great job maintaining regular sessions!")
        else:
            recommendations.append("Consider scheduling more regular sessions for better outcomes")
        
        # Type-specific recommendations
        type_counts = {}
        for session in sessions:
            type_counts[session.session_type] = type_counts.get(session.session_type, 0) + 1
        
        if "tutoring" in type_counts:
            recommendations.append("Continue daily practice between tutoring sessions")
        
        if "scheduling" in type_counts:
            recommendations.append("Try to schedule sessions at consistent times for routine building")
        
        return recommendations
