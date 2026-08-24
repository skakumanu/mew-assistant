"""
Pytest configuration and shared fixtures for Mew Assistant tests.
"""

import os

# Set required environment variables BEFORE importing app
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("TESTING", "true")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.database.models import User
from app.main import app

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
    # By default, skip strict rate limiting for most tests to avoid cross-test interference.
    # Tests that specifically assert rate-limiting behavior will remove this env var.
    monkeypatch.setenv("TESTING_SKIP_STRICT_RATE_LIMIT", "true")

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
    user = User(
        email="scheduler_tester@example.com",
        hashed_password="test",
        full_name="Scheduler Tester",
    )
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
        "name": "Test User",
    }


@pytest.fixture
def sample_ingest_data():
    """Sample ingestion data for testing."""
    return {
        "channel": "email",
        "sender": "parent@example.com",
        "body": "Can we schedule a tutoring session for tomorrow at 3pm?",
        "subject": "Tutoring Request",
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
            "duration_minutes": 60,
        },
    }


# ---------------------------------------------------------------------------
# Three-persona scheduling fixtures, shared by the scheduling test modules.
# ---------------------------------------------------------------------------

from datetime import datetime, time, timedelta  # noqa: E402

from app.database.models import (  # noqa: E402
    ProviderOrg,
    ProviderPerson,
    RuleSet,
    ScheduledSession,
)
from app.utils.auth import create_access_token, get_password_hash  # noqa: E402


def _token(user: User) -> str:
    return create_access_token({"sub": user.email, "user_id": user.id})


def _auth(user: User) -> dict:
    return {"Authorization": f"Bearer {_token(user)}", "Accept-Language": "en"}


@pytest.fixture
def family(db_session):
    """A parent, a child, an ABA provider with two therapists."""
    parent = User(
        email="sarah@example.com",
        username="sarah",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_kid_account=False,
        display_name="Sarah",
    )
    db_session.add(parent)
    db_session.commit()

    kid = User(
        email="ellie@example.com",
        username="ellie",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_kid_account=True,
        parent_id=parent.id,
        display_name="Ellie",
    )
    org = ProviderOrg(name="Bright Steps ABA", kind="aba", calendar_provider="google")
    db_session.add_all([kid, org])
    db_session.commit()

    dana = ProviderPerson(org_id=org.id, display_name="Dana R.")
    jordan = ProviderPerson(org_id=org.id, display_name="Jordan P.")
    db_session.add_all([dana, jordan])
    db_session.commit()

    provider_login = User(
        email="dana@brightsteps.example",
        username="dana",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_kid_account=False,
    )
    db_session.add(provider_login)
    db_session.commit()
    dana.user_id = provider_login.id
    db_session.commit()

    return {
        "parent": parent,
        "kid": kid,
        "org": org,
        "dana": dana,
        "jordan": jordan,
        "provider_login": provider_login,
    }


@pytest.fixture
def rules(db_session, family):
    """Sarah's declared defaults, with the midday block left off by default."""
    ruleset = RuleSet(
        parent_id=family["parent"].id,
        child_id=family["kid"].id,
        min_notice_hours=24,
        earliest_start=time(8, 0),
        latest_end=time(18, 0),
        require_same_provider_person=True,
        buffer_minutes=45,
        cancellation_needs_approval=True,
    )
    db_session.add(ruleset)
    db_session.commit()
    return ruleset


@pytest.fixture
def session_row(db_session, family):
    """One ABA session, comfortably far enough out to satisfy min-notice."""
    start = (datetime.utcnow() + timedelta(days=3)).replace(
        hour=15, minute=30, second=0, microsecond=0
    )
    row = ScheduledSession(
        child_id=family["kid"].id,
        provider_org_id=family["org"].id,
        provider_person_id=family["dana"].id,
        title="ABA session",
        activity_type="aba",
        start_utc=start,
        duration_minutes=90,
        source="calendar",
    )
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    return row
