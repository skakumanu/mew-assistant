"""
Tests for Kid-Friendly Features
Ensures kid accounts, content filtering, and parent-kid communication work correctly
"""

from datetime import datetime, timedelta

import pytest
from fastapi import status

from app.schemas.kid_friendly import (ChangeReason, EmojiReaction,
                                      KidActivitySuggestion, TimeOfDay)
from app.utils.content_filter import ContentFilter


class TestContentFilter:
    """Test content filtering for kid safety"""

    def setup_method(self):
        self.filter = ContentFilter()

    def test_safe_content(self):
        """Test that appropriate content passes"""
        assert self.filter.is_kid_safe("I want to go to the park")
        assert self.filter.is_kid_safe("Can we play games?")
        assert self.filter.is_kid_safe("I love reading books!")

    def test_inappropriate_content(self):
        """Test that inappropriate content is blocked"""
        assert not self.filter.is_kid_safe("I hate this")
        assert not self.filter.is_kid_safe("That's stupid")

    def test_distress_detection(self):
        """Test detection of distress signals"""
        assert self.filter.detect_distress("I'm scared")
        assert self.filter.detect_distress("Someone hurt me")
        assert self.filter.detect_distress("Help me!!!")
        assert not self.filter.detect_distress("I'm having fun")

    def test_sanitization(self):
        """Test input sanitization"""
        assert self.filter.sanitize_kid_input("Hello!!!!!!") == "Hello!!"
        assert (
            self.filter.sanitize_kid_input("  Too   many   spaces  ")
            == "Too many spaces"
        )

    def test_sensitive_info_masking(self):
        """Test masking of sensitive information"""
        result = self.filter.mask_sensitive_info("Call me at 555-123-4567")
        assert "[phone]" in result
        assert "555-123-4567" not in result

        result = self.filter.mask_sensitive_info("Email me at test@example.com")
        assert "[email]" in result
        assert "test@example.com" not in result


class TestKidActivitySuggestion:
    """Test kid activity suggestion endpoint"""

    def test_create_activity_suggestion(self, client, kid_user_token):
        """Test creating an activity suggestion"""
        suggestion = {
            "activity_name": "Go to the zoo",
            "activity_description": "I want to see the animals!",
            "when": "afternoon",
            "emoji": "😊",
        }

        response = client.post(
            "/kid/suggest-activity",
            json=suggestion,
            headers={"Authorization": f"Bearer {kid_user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "suggestion_id" in data["data"]

    def test_inappropriate_suggestion(self, client, kid_user_token):
        """Test that inappropriate suggestions are rejected"""
        suggestion = {
            "activity_name": "Something bad",
            "activity_description": "I hate everything",
            "when": "afternoon",
            "emoji": "😊",
        }

        response = client.post(
            "/kid/suggest-activity",
            json=suggestion,
            headers={"Authorization": f"Bearer {kid_user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is False
        assert "nice words" in data["message"].lower()


class TestKidSchedule:
    """Test kid schedule endpoints"""

    def test_get_kid_schedule(self, client, kid_user_token):
        """Test retrieving kid's schedule"""
        response = client.get(
            "/kid/my-schedule", headers={"Authorization": f"Bearer {kid_user_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "greeting" in data
        assert "today" in data
        assert "tomorrow" in data
        assert "fun_fact" in data

    def test_schedule_requires_kid_account(self, client, regular_user_token):
        """Test that regular users cannot access kid endpoints"""
        response = client.get(
            "/kid/my-schedule",
            headers={"Authorization": f"Bearer {regular_user_token}"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestKidReactions:
    """Test emoji reaction system"""

    def test_positive_reaction(self, client, kid_user_token):
        """Test positive emoji reaction"""
        reaction = {"activity_id": 1, "emoji": "😊", "feeling": "I'm excited!"}

        response = client.post(
            "/kid/react",
            json=reaction,
            headers={"Authorization": f"Bearer {kid_user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "glad" in data["message"].lower()

    def test_negative_reaction_notifies_parent(self, client, kid_user_token):
        """Test that negative reactions notify parent"""
        reaction = {"activity_id": 1, "emoji": "😢", "feeling": "I don't want to"}

        response = client.post(
            "/kid/react",
            json=reaction,
            headers={"Authorization": f"Bearer {kid_user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        # Parent should be notified (check notification system)


class TestKidChangeRequests:
    """Test schedule change request system"""

    def test_create_change_request(self, client, kid_user_token):
        """Test creating a schedule change request"""
        request = {
            "activity_id": 1,
            "reason": "I'm tired",
            "alternative": "Can we rest instead?",
        }

        response = client.post(
            "/kid/change-request",
            json=request,
            headers={"Authorization": f"Bearer {kid_user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "request_id" in data["data"]


class TestKidHelp:
    """Test help request system"""

    def test_regular_help_request(self, client, kid_user_token):
        """Test regular help request"""
        response = client.post(
            "/kid/help",
            params={"message": "I need help with homework"},
            headers={"Authorization": f"Bearer {kid_user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    def test_urgent_help_request(self, client, kid_user_token):
        """Test urgent help request triggers immediate alert"""
        response = client.post(
            "/kid/help",
            params={"message": "I'm scared"},
            headers={"Authorization": f"Bearer {kid_user_token}"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        # Should trigger urgent parent notification


class TestStickerRewards:
    """Test gamification sticker system"""

    def test_get_sticker_collection(self, client, kid_user_token):
        """Test retrieving sticker collection"""
        response = client.get(
            "/kid/stickers", headers={"Authorization": f"Bearer {kid_user_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "total_stickers" in data
        assert "stickers" in data
        assert "next_reward" in data


# Fixtures
@pytest.fixture
def kid_user_token(client, db_session):
    """Create a kid user and return auth token"""
    from app.database.models import User
    from app.utils.auth import create_access_token, get_password_hash

    # Create parent user
    parent = User(
        email="parent@example.com",
        username="parent",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_kid_account=False,
    )
    db_session.add(parent)
    db_session.commit()

    # Create kid user
    kid = User(
        email="kid@example.com",
        username="kiduser",
        hashed_password=get_password_hash("kidpass123"),
        is_active=True,
        is_kid_account=True,
        parent_id=parent.id,
        display_name="Timmy",
        age=8,
    )
    db_session.add(kid)
    db_session.commit()

    # Generate token
    token = create_access_token({"sub": kid.email})
    return token


@pytest.fixture
def regular_user_token(client, db_session):
    """Create a regular user and return auth token"""
    from app.database.models import User
    from app.utils.auth import create_access_token, get_password_hash

    user = User(
        email="regular@example.com",
        username="regular",
        hashed_password=get_password_hash("password123"),
        is_active=True,
        is_kid_account=False,
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token({"sub": user.email})
    return token
