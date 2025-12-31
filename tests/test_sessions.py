"""Test session endpoints"""


def test_create_session(client):
    """Test creating a new session"""
    response = client.post(
        "/mew/session",
        json={
            "user_id": "test_user_001",
            "session_type": "tutoring",
            "title": "Math Homework",
            "priority": "normal",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == "test_user_001"
    assert data["session_type"] == "tutoring"
    assert data["status"] == "pending"


def test_get_session(client):
    """Test retrieving a session"""
    # Create a session first
    create_response = client.post(
        "/mew/session",
        json={
            "user_id": "test_user_002",
            "session_type": "scheduling",
            "title": "Doctor Appointment",
            "priority": "high",
        },
    )
    session_id = create_response.json()["id"]

    # Get the session
    response = client.get(f"/mew/session/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["user_id"] == "test_user_002"


def test_list_user_sessions(client):
    """Test listing sessions for a user"""
    user_id = "test_user_003"

    # Create multiple sessions
    for i in range(3):
        client.post(
            "/mew/session",
            json={
                "user_id": user_id,
                "session_type": "tutoring",
                "title": f"Session {i}",
                "priority": "normal",
            },
        )

    # List sessions
    response = client.get(f"/mew/sessions/user/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
