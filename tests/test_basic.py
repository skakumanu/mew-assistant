"""
Basic smoke tests for Mew Assistant.
Tests core functionality without requiring full implementation details.
"""

from fastapi import status


def test_app_health(client):
    """Test that the app starts and health endpoint works."""
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "Mew Assistant" in data["message"]


def test_health_check(client):
    """Test dedicated health check endpoint."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"


def test_api_returns_json(client):
    """Test that API returns proper JSON responses."""
    response = client.get("/")
    assert response.headers["content-type"] == "application/json"


def test_invalid_endpoint(client):
    """Test that invalid endpoints return 404."""
    response = client.get("/nonexistent-endpoint")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_a_browser_landing_on_the_bare_domain_goes_to_sign_in(client, monkeypatch):
    """
    Regression guard: `/` used to render its own hardcoded HTML with
    "Sign in with Google/Microsoft" buttons pointing at /auth/simple/* -
    routes that no longer exist since WorkOS AuthKit became the sign-in
    front door. A real browser (no TESTING override, an HTML Accept
    header) must be sent to the one entry point that still works.
    """
    monkeypatch.delenv("TESTING", raising=False)
    response = client.get("/", headers={"Accept": "text/html"}, follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/app/sign-in"


def test_database_models_exist():
    """Test that database models module exists."""
    from app.database import models

    assert models is not None


def test_schemas_exist():
    """Test that schema modules exist."""
    from app import schemas

    assert schemas is not None


def test_services_exist():
    """Test that service modules exist."""
    from app import services

    assert services is not None


def test_utils_exist():
    """Test that utility modules exist."""
    from app import utils

    assert utils is not None
