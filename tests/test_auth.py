"""
Tests for authentication endpoints.
"""

import pytest
from fastapi.testclient import TestClient


def test_register_user(client: TestClient):
    """Test user registration"""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "SecureP@ssw0rd123",
        "full_name": "Test User",
        "user_type": "parent",
    }

    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "hashed_password" not in data  # Password should not be in response
    assert data["is_active"] is True


def test_register_duplicate_email(client: TestClient):
    """Test registration with duplicate email"""
    user_data = {
        "email": "duplicate@example.com",
        "username": "user1",
        "password": "SecureP@ssw0rd123",
    }

    # Register first time
    client.post("/auth/register", json=user_data)

    # Try to register again with same email
    user_data["username"] = "user2"  # Different username
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_login_success(client: TestClient):
    """Test successful login"""
    # Register user first
    register_data = {
        "email": "login@example.com",
        "username": "loginuser",
        "password": "SecureP@ssw0rd123",
    }
    client.post("/auth/register", json=register_data)

    # Login
    login_data = {"email": "login@example.com", "password": "SecureP@ssw0rd123"}

    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == login_data["email"]


def test_login_wrong_password(client: TestClient):
    """Test login with wrong password"""
    # Register user
    register_data = {
        "email": "wrongpass@example.com",
        "username": "wrongpass",
        "password": "CorrectPassword123",
    }
    client.post("/auth/register", json=register_data)

    # Try login with wrong password
    login_data = {"email": "wrongpass@example.com", "password": "WrongPassword123"}

    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401


def test_login_nonexistent_user(client: TestClient):
    """Test login with non-existent email"""
    login_data = {"email": "nonexistent@example.com", "password": "SomePassword123"}

    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401


def test_get_current_user(client: TestClient):
    """Test getting current user profile"""
    # Register and login
    register_data = {
        "email": "profile@example.com",
        "username": "profileuser",
        "password": "SecureP@ssw0rd123",
        "full_name": "Profile User",
    }
    client.post("/auth/register", json=register_data)

    login_response = client.post(
        "/auth/login",
        json={"email": "profile@example.com", "password": "SecureP@ssw0rd123"},
    )
    token = login_response.json()["access_token"]

    # Get profile
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "profile@example.com"
    assert data["full_name"] == "Profile User"


def test_get_current_user_no_token(client: TestClient):
    """Test accessing protected route without token"""
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_get_current_user_invalid_token(client: TestClient):
    """Test accessing protected route with invalid token"""
    response = client.get(
        "/auth/me", headers={"Authorization": "Bearer invalid_token_here"}
    )
    assert response.status_code == 401


def test_update_profile(client: TestClient):
    """Test updating user profile"""
    # Register and login
    client.post(
        "/auth/register",
        json={
            "email": "update@example.com",
            "username": "updateuser",
            "password": "SecureP@ssw0rd123",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "update@example.com", "password": "SecureP@ssw0rd123"},
    )
    token = login_response.json()["access_token"]

    # Update profile
    update_data = {
        "full_name": "Updated Name",
        "phone": "+1234567890",
        "timezone": "America/New_York",
    }

    response = client.patch(
        "/auth/me", json=update_data, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["phone"] == "+1234567890"
    assert data["timezone"] == "America/New_York"


def test_change_password(client: TestClient):
    """Test password change"""
    # Register and login
    client.post(
        "/auth/register",
        json={
            "email": "changepass@example.com",
            "username": "changepass",
            "password": "OldPassword123",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "changepass@example.com", "password": "OldPassword123"},
    )
    token = login_response.json()["access_token"]

    # Change password
    response = client.post(
        "/auth/change-password",
        json={"current_password": "OldPassword123", "new_password": "NewPassword456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    # Try logging in with new password
    new_login = client.post(
        "/auth/login",
        json={"email": "changepass@example.com", "password": "NewPassword456"},
    )
    assert new_login.status_code == 200


def test_change_password_wrong_current(client: TestClient):
    """Test password change with wrong current password"""
    # Register and login
    client.post(
        "/auth/register",
        json={
            "email": "wrongcurrent@example.com",
            "username": "wrongcurrent",
            "password": "CorrectPassword123",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "wrongcurrent@example.com", "password": "CorrectPassword123"},
    )
    token = login_response.json()["access_token"]

    # Try to change password with wrong current password
    response = client.post(
        "/auth/change-password",
        json={"current_password": "WrongPassword123", "new_password": "NewPassword456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


def test_refresh_token(client: TestClient):
    """Test token refresh"""
    # Register and login
    client.post(
        "/auth/register",
        json={
            "email": "refresh@example.com",
            "username": "refreshuser",
            "password": "SecureP@ssw0rd123",
        },
    )

    login_response = client.post(
        "/auth/login",
        json={"email": "refresh@example.com", "password": "SecureP@ssw0rd123"},
    )
    refresh_token = login_response.json()["refresh_token"]

    # Refresh access token
    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
