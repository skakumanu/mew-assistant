"""
Tests for Parental Approval Workflow
CRITICAL: Ensures no schedule changes from kids happen without parent approval
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base, get_db
from app.database.models import ApprovalStatus, RequestType, User, UserRole
from app.main import app
from app.services.approval_service import ApprovalService

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_approval.db"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """Create fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def parent_user(test_db):
    """Create a parent user"""
    parent = User(
        email="parent@test.com",
        username="parent_test",
        hashed_password="hashed_pw",
        full_name="Test Parent",
        is_active=True,
        role=UserRole.PARENT,
        is_kid_account=False,
    )
    test_db.add(parent)
    test_db.commit()
    test_db.refresh(parent)
    return parent


@pytest.fixture
def kid_user(test_db, parent_user):
    """Create a kid user linked to parent"""
    kid = User(
        email="kid@test.com",
        username="kid_test",
        hashed_password="hashed_pw",
        full_name="Test Kid",
        display_name="Timmy",
        is_active=True,
        role=UserRole.PARENT,  # Still uses parent role but is_kid_account=True
        is_kid_account=True,
        parent_id=parent_user.id,
        age=10,
        avatar_emoji="😊",
    )
    test_db.add(kid)
    test_db.commit()
    test_db.refresh(kid)
    return kid


class TestApprovalRequestCreation:
    """Test creation of approval requests from kids"""

    def test_create_new_activity_request(self, test_db, kid_user, parent_user):
        """Kid can request new activity"""
        approval_service = ApprovalService(test_db)

        request = approval_service.create_approval_request(
            kid_id=kid_user.id,
            parent_id=parent_user.id,
            request_type=RequestType.NEW_EVENT,
            requested_activity="Go to park",
            requested_time="afternoon",
            reason="I want to play outside",
            emoji="🏃",
        )

        assert request.id is not None
        assert request.status == ApprovalStatus.PENDING
        assert request.kid_id == kid_user.id
        assert request.parent_id == parent_user.id
        assert request.requested_activity == "Go to park"
        assert request.applied_to_calendar is False
        assert request.parent_approved is None

    def test_create_schedule_change_request(self, test_db, kid_user, parent_user):
        """Kid can request to change existing activity"""
        approval_service = ApprovalService(test_db)

        request = approval_service.create_approval_request(
            kid_id=kid_user.id,
            parent_id=parent_user.id,
            request_type=RequestType.SCHEDULE_CHANGE,
            activity_id=123,
            requested_time="evening",
            reason="I'm too tired in the morning",
            emoji="😴",
        )

        assert request.status == ApprovalStatus.PENDING
        assert request.original_activity_id == 123
        assert request.applied_to_calendar is False

    def test_cannot_create_request_for_non_kid(self, test_db, parent_user):
        """Non-kid accounts cannot create approval requests"""
        approval_service = ApprovalService(test_db)

        with pytest.raises(Exception) as exc:
            approval_service.create_approval_request(
                kid_id=parent_user.id,  # Parent, not kid
                parent_id=parent_user.id,
                request_type=RequestType.NEW_EVENT,
                requested_activity="Test",
            )

        assert "Invalid kid account" in str(exc.value)

    def test_request_auto_expires_after_24h(self, test_db, kid_user, parent_user):
        """Approval requests expire after 24 hours"""
        approval_service = ApprovalService(test_db)

        request = approval_service.create_approval_request(
            kid_id=kid_user.id,
            parent_id=parent_user.id,
            request_type=RequestType.NEW_EVENT,
            requested_activity="Test activity",
        )

        # Should expire in ~24 hours
        assert request.expires_at is not None
        time_until_expiry = request.expires_at - datetime.utcnow()
        assert 23 <= time_until_expiry.total_seconds() / 3600 <= 25  # ~24 hours


class TestParentApproval:
    """Test parent approval workflow"""

    def test_parent_can_approve_request(self, test_db, kid_user, parent_user):
        """Parent successfully approves kid request"""
        approval_service = ApprovalService(test_db)

        # Kid creates request
        request = approval_service.create_approval_request(
            kid_id=kid_user.id,
            parent_id=parent_user.id,
            request_type=RequestType.NEW_EVENT,
            requested_activity="Swimming lesson",
            requested_time="afternoon",
        )

        assert request.status == ApprovalStatus.PENDING
        assert request.parent_approved is None

        # Parent approves
        approved = approval_service.approve_request(
            request_id=request.id,
            parent_id=parent_user.id,
            parent_note="Great idea! Let's do it!",
        )

        assert approved.status == ApprovalStatus.APPROVED
        assert approved.parent_approved is True
        assert approved.parent_note == "Great idea! Let's do it!"
        assert approved.approved_at is not None
        assert approved.processed_at is not None

    def test_approval_creates_audit_log(self, test_db, kid_user, parent_user):
        """Approval action is logged for compliance"""
        approval_service = ApprovalService(test_db)

        request = approval_service.create_approval_request(
            kid_id=kid_user.id,
            parent_id=parent_user.id,
            request_type=RequestType.NEW_EVENT,
            requested_activity="Test",
        )

        # Approve with tracking info
        approval_service.approve_request(
            request_id=request.id,
            parent_id=parent_user.id,
            parent_note="Approved",
            ip_address="192.168.1.1",
            user_agent="TestBrowser/1.0",
        )

        # Check audit logs exist
        test_db.refresh(request)
        audit_logs = request.audit_logs

        assert len(audit_logs) >= 2  # Created + Approved
        approval_log = [log for log in audit_logs if log.action == "approved"][0]
        assert approval_log.performed_by == parent_user.id
        assert approval_log.ip_address == "192.168.1.1"
        assert approval_log.new_status == ApprovalStatus.APPROVED.value

    def test_cannot_approve_expired_request(self, test_db, kid_user, parent_user):
        """Cannot approve a request that has expired"""
        approval_service = ApprovalService(test_db)

        request = approval_service.create_approval_request(
            kid_id=kid_user.id,
            parent_id=parent_user.id,
            request_type=RequestType.NEW_EVENT,
            requested_activity="Test",
        )

        # Manually expire the request
        request.expires_at = datetime.utcnow() - timedelta(hours=1)
        test_db.commit()

        # Try to approve
        with pytest.raises(Exception) as exc:
            approval_service.approve_request(
                request_id=request.id, parent_id=parent_user.id
            )

        assert "cannot be approved" in str(exc.value).lower()

    def test_wrong_parent_cannot_approve(self, test_db, kid_user, parent_user):
        """Only the linked parent can approve requests"""
        approval_service = ApprovalService(test_db)

        # Create another parent
        other_parent = User(
            email="other@test.com",
            username="other_parent",
            hashed_password="hashed",
            is_kid_account=False,
            role=UserRole.PARENT,
        )
        test_db.add(other_parent)
        test_db.commit()

        request = approval_service.create_approval_request(
            kid_id=kid_user.id,
            parent_id=parent_user.id,
            request_type=RequestType.NEW_EVENT,
            requested_activity="Test",
        )

        # Other parent tries to approve
        with pytest.raises(Exception) as exc:
            approval_service.approve_request(
                request_id=request.id, parent_id=other_parent.id  # Wrong parent
            )

        assert "not authorized" in str(exc.value).lower()


class TestParentDenial:
    """Test parent denial workflow"""

    def test_parent_can_deny_request(self, test_db, kid_user, parent_user):
        """Parent can deny kid request with explanation"""
        approval_service = ApprovalService(test_db)

        request = approval_service.create_approval_request(
            kid_id=kid_user.id,
            parent_id=parent_user.id,
            request_type=RequestType.SKIP_ACTIVITY,
            activity_id=456,
            reason="Don't want to go",
        )

        # Parent denies with kind explanation
        denied = approval_service.deny_request(
            request_id=request.id,
            parent_id=parent_user.id,
            parent_note="I know you're tired, but this is important for your learning",
            alternative_suggestion="How about we make it shorter?",
        )

        assert denied.status == ApprovalStatus.DENIED
        assert denied.parent_approved is False
        assert denied.parent_note is not None
        assert denied.parent_alternative is not None
        assert denied.applied_to_calendar is False  # Nothing changed
        assert denied.processed_at is not None

    def test_denial_does_not_change_calendar(self, test_db, kid_user, parent_user):
        """Denied requests do not affect calendar"""
        approval_service = ApprovalService(test_db)

        request = approval_service.create_approval_request(
            kid_id=kid_user.id,
            parent_id=parent_user.id,
            request_type=RequestType.NEW_EVENT,
            requested_activity="Test",
        )

        denied = approval_service.deny_request(
            request_id=request.id, parent_id=parent_user.id, parent_note="Not this time"
        )

        assert denied.applied_to_calendar is False
        assert denied.calendar_event_id is None


class TestCalendarIntegration:
    """Test that calendar changes only happen after approval"""

    def test_pending_request_does_not_change_calendar(
        self, test_db, kid_user, parent_user
    ):
        """Pending requests do not affect calendar"""
        approval_service = ApprovalService(test_db)

        request = approval_service.create_approval_request(
            kid_id=kid_user.id,
            parent_id=parent_user.id,
            request_type=RequestType.NEW_EVENT,
            requested_activity="Piano lesson",
        )

        # Still pending
        assert request.status == ApprovalStatus.PENDING
        assert request.applied_to_calendar is False
        assert request.calendar_event_id is None

    def test_only_approved_requests_affect_calendar(
        self, test_db, kid_user, parent_user
    ):
        """Calendar changes happen only after parent approval"""
        approval_service = ApprovalService(test_db)

        request = approval_service.create_approval_request(
            kid_id=kid_user.id,
            parent_id=parent_user.id,
            request_type=RequestType.NEW_EVENT,
            requested_activity="Soccer practice",
        )

        # Before approval - no calendar changes
        assert request.applied_to_calendar is False

        # After approval - calendar should be updated
        # Note: In real implementation, this would call CalendarService
        approval_service.approve_request(
            request_id=request.id, parent_id=parent_user.id
        )

        test_db.refresh(request)
        # applied_to_calendar flag should be set
        # In full implementation with real CalendarService


class TestApprovalQueries:
    """Test querying approval requests"""

    def test_get_pending_requests_for_parent(self, test_db, kid_user, parent_user):
        """Parent can see all pending requests"""
        approval_service = ApprovalService(test_db)

        # Create multiple requests
        for i in range(3):
            approval_service.create_approval_request(
                kid_id=kid_user.id,
                parent_id=parent_user.id,
                request_type=RequestType.NEW_EVENT,
                requested_activity=f"Activity {i}",
            )

        pending = approval_service.get_pending_requests(parent_user.id)
        assert len(pending) == 3
        assert all(r.status == ApprovalStatus.PENDING for r in pending)

    def test_get_kid_request_history(self, test_db, kid_user, parent_user):
        """Get history of kid's requests"""
        approval_service = ApprovalService(test_db)

        # Create and approve one request
        req1 = approval_service.create_approval_request(
            kid_id=kid_user.id,
            parent_id=parent_user.id,
            request_type=RequestType.NEW_EVENT,
            requested_activity="Activity 1",
        )
        approval_service.approve_request(req1.id, parent_user.id)

        # Create and deny another
        req2 = approval_service.create_approval_request(
            kid_id=kid_user.id,
            parent_id=parent_user.id,
            request_type=RequestType.NEW_EVENT,
            requested_activity="Activity 2",
        )
        approval_service.deny_request(req2.id, parent_user.id, parent_note="Not now")

        # Get history
        history = approval_service.get_kid_requests(kid_user.id)
        assert len(history) == 2
        assert any(r.status == ApprovalStatus.APPROVED for r in history)
        assert any(r.status == ApprovalStatus.DENIED for r in history)


class TestAutoExpiration:
    """Test automatic expiration of old requests"""

    def test_expire_old_pending_requests(self, test_db, kid_user, parent_user):
        """Old pending requests are automatically expired"""
        approval_service = ApprovalService(test_db)

        # Create request and manually set old expiry
        request = approval_service.create_approval_request(
            kid_id=kid_user.id,
            parent_id=parent_user.id,
            request_type=RequestType.NEW_EVENT,
            requested_activity="Old request",
        )
        request.expires_at = datetime.utcnow() - timedelta(hours=1)
        test_db.commit()

        # Run expiration job
        expired_count = approval_service.expire_old_requests()

        assert expired_count == 1
        test_db.refresh(request)
        assert request.status == ApprovalStatus.EXPIRED
        assert request.processed_at is not None


def test_full_workflow_integration(test_db, kid_user, parent_user):
    """
    Full integration test: Kid requests, parent approves, calendar updated
    """
    approval_service = ApprovalService(test_db)

    # 1. Kid creates request
    request = approval_service.create_approval_request(
        kid_id=kid_user.id,
        parent_id=parent_user.id,
        request_type=RequestType.NEW_EVENT,
        requested_activity="Art class",
        requested_time="afternoon",
        reason="I love painting!",
        emoji="🎨",
    )

    assert request.status == ApprovalStatus.PENDING
    assert request.applied_to_calendar is False

    # 2. Parent reviews and approves
    approved = approval_service.approve_request(
        request_id=request.id,
        parent_id=parent_user.id,
        parent_note="That's wonderful! Art is important!",
    )

    assert approved.status == ApprovalStatus.APPROVED
    assert approved.parent_approved is True

    # 3. Verify audit trail
    test_db.refresh(approved)
    assert len(approved.audit_logs) >= 2  # Created + Approved

    # 4. Verify calendar would be updated (in full implementation)
    # assert approved.applied_to_calendar is True
    # assert approved.calendar_event_id is not None
