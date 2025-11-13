"""Test main application"""
from fastapi.testclient import TestClient
from app.main import app


def test_root_endpoint():
    """Test root endpoint returns welcome message"""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Mew Assistant" in data["message"]


def test_health_endpoint():
    """Test health check endpoint"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
