"""
Tests for database models and operations.
"""
import pytest
from datetime import datetime
from app.models import Session, User, Message


def test_create_user(test_db):
    """Test creating a user in database."""
    user = User(
        user_id="test_001",
        email="test@example.com",
        phone="+1234567890",
        name="Test User"
    )
    test_db.add(user)
    test_db.commit()
    
    retrieved = test_db.query(User).filter(User.user_id == "test_001").first()
    assert retrieved is not None
    assert retrieved.email == "test@example.com"


def test_create_session(test_db):
    """Test creating a session in database."""
    session = Session(
        session_id="sess_001",
        user_id="user_001",
        status="pending",
        action_type="schedule_tutoring",
        created_at=datetime.utcnow()
    )
    test_db.add(session)
    test_db.commit()
    
    retrieved = test_db.query(Session).filter(Session.session_id == "sess_001").first()
    assert retrieved is not None
    assert retrieved.status == "pending"


def test_create_message(test_db):
    """Test creating a message in database."""
    message = Message(
        message_id="msg_001",
        session_id="sess_001",
        channel="email",
        sender="test@example.com",
        content="Test message",
        received_at=datetime.utcnow()
    )
    test_db.add(message)
    test_db.commit()
    
    retrieved = test_db.query(Message).filter(Message.message_id == "msg_001").first()
    assert retrieved is not None
    assert retrieved.channel == "email"


def test_session_user_relationship(test_db):
    """Test relationship between session and user."""
    user = User(
        user_id="user_002",
        email="user2@example.com",
        name="User Two"
    )
    test_db.add(user)
    test_db.commit()
    
    session = Session(
        session_id="sess_002",
        user_id="user_002",
        status="confirmed",
        action_type="generate_summary"
    )
    test_db.add(session)
    test_db.commit()
    
    retrieved_session = test_db.query(Session).filter(Session.session_id == "sess_002").first()
    assert retrieved_session.user_id == "user_002"


def test_query_sessions_by_user(test_db):
    """Test querying sessions for a specific user."""
    user = User(user_id="user_003", email="user3@example.com", name="User Three")
    test_db.add(user)
    
    sessions = [
        Session(session_id=f"sess_{i}", user_id="user_003", status="completed", action_type="tutoring")
        for i in range(3)
    ]
    for session in sessions:
        test_db.add(session)
    test_db.commit()
    
    retrieved = test_db.query(Session).filter(Session.user_id == "user_003").all()
    assert len(retrieved) == 3


def test_update_session_status(test_db):
    """Test updating session status."""
    session = Session(
        session_id="sess_004",
        user_id="user_004",
        status="pending",
        action_type="schedule"
    )
    test_db.add(session)
    test_db.commit()
    
    session.status = "confirmed"
    test_db.commit()
    
    retrieved = test_db.query(Session).filter(Session.session_id == "sess_004").first()
    assert retrieved.status == "confirmed"


def test_delete_session(test_db):
    """Test deleting a session."""
    session = Session(
        session_id="sess_005",
        user_id="user_005",
        status="cancelled",
        action_type="appointment"
    )
    test_db.add(session)
    test_db.commit()
    
    test_db.delete(session)
    test_db.commit()
    
    retrieved = test_db.query(Session).filter(Session.session_id == "sess_005").first()
    assert retrieved is None
