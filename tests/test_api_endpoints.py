"""
Integration tests for API endpoints.
"""
import pytest
from fastapi import status


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_ingest_endpoint(client, sample_ingest_data):
    """Test message ingestion endpoint."""
    response = client.post("/mew/ingest", json=sample_ingest_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert "channel" in data
    assert data["channel"] == "email"
    assert data["sender"] == "parent@example.com"


def test_ingest_invalid_channel(client):
    """Test ingestion with invalid channel."""
    invalid_data = {
        "channel": "invalid_channel",
        "sender": "test@example.com",
        "content": "Test message"
    }
    response = client.post("/mew/ingest", json=invalid_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_confirm_endpoint(client, sample_confirmation_data):
    """Test confirmation endpoint."""
    response = client.post("/mew/confirm", json=sample_confirmation_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["session_id"] == sample_confirmation_data["session_id"]


def test_confirm_missing_fields(client):
    """Test confirmation with missing required fields."""
    incomplete_data = {
        "session_id": "sess_123"
    }
    response = client.post("/mew/confirm", json=incomplete_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_summary_endpoint(client, sample_user):
    """Test summary generation endpoint."""
    params = {
        "user_id": sample_user["user_id"],
        "days": 7
    }
    response = client.get("/mew/summary", params=params)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user_id"] == sample_user["user_id"]
    assert "period" in data
    assert "summary" in data


def test_summary_invalid_days(client, sample_user):
    """Test summary with invalid days parameter."""
    params = {
        "user_id": sample_user["user_id"],
        "days": 0  # Invalid
    }
    response = client.get("/mew/summary", params=params)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_summary_too_many_days(client, sample_user):
    """Test summary with days exceeding maximum."""
    params = {
        "user_id": sample_user["user_id"],
        "days": 100  # Exceeds max of 90
    }
    response = client.get("/mew/summary", params=params)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.options("/health")
    assert "access-control-allow-origin" in response.headers


def test_rate_limiting_simulation(client, sample_ingest_data):
    """Test multiple rapid requests (rate limiting detection)."""
    responses = []
    for _ in range(5):
        response = client.post("/mew/ingest", json=sample_ingest_data)
        responses.append(response.status_code)
    
    # All should succeed in test environment (no actual rate limiting)
    assert all(code == status.HTTP_200_OK for code in responses)
