"""
Pytest configuration and shared fixtures for Mew Assistant tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.database.models import User


# Use in-memory SQLite for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    """Create test database tables and provide a database session."""
    # Drop all tables first to ensure clean state
    Base.metadata.drop_all(bind=engine)
    # Create fresh tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db, monkeypatch):
    """Create test client with database override and test mode enabled."""
    # Set test mode to bypass strict compliance checks
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("ENVIRONMENT", "test")
    
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def db_session(test_db):
    """Alias fixture so tests can request `db_session` explicitly."""
    return test_db


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a persisted test user for scheduler tests."""
    user = User(email="scheduler_tester@example.com", hashed_password="test", full_name="Scheduler Tester")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_user():
    """Sample user data for testing."""
    return {
        "user_id": "test_user_001",
        "email": "test@example.com",
        "phone": "+1234567890",
        "name": "Test User"
    }


@pytest.fixture
def sample_ingest_data():
    """Sample ingestion data for testing."""
    return {
        "channel": "email",
        "sender": "parent@example.com",
        "body": "Can we schedule a tutoring session for tomorrow at 3pm?",
        "subject": "Tutoring Request"
    }


@pytest.fixture
def sample_confirmation_data():
    """Sample confirmation data for testing."""
    return {
        "session_id": "sess_12345",
        "user_id": "test_user_001",
        "action_type": "schedule_tutoring",
        "details": {
            "date": "2024-01-16",
            "time": "15:00",
            "subject": "Math",
            "duration_minutes": 60
        }
    }
