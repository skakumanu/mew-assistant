"""
Load testing scenarios for Mew Assistant API
"""

import json
import random

from locust import HttpUser, between, task


class MewAssistantUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Setup: Register and login"""
        # Register a test user
        self.user_id = f"testuser_{random.randint(1000, 9999)}"
        response = self.client.post(
            "/api/v1/auth/register",
            json={
                "username": self.user_id,
                "email": f"{self.user_id}@test.com",
                "password": "TestPass123!",
                "role": "parent",
            },
        )

        if response.status_code == 200:
            # Login
            login_response = self.client.post(
                "/api/v1/auth/login",
                json={"username": self.user_id, "password": "TestPass123!"},
            )

            if login_response.status_code == 200:
                self.token = login_response.json().get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def health_check(self):
        """Test health endpoint"""
        self.client.get("/health")

    @task(2)
    def create_session(self):
        """Test session creation"""
        self.client.post(
            "/api/v1/sessions/", json={"channel": "web"}, headers=self.headers
        )

    @task(5)
    def send_message(self):
        """Test message ingestion"""
        messages = [
            "Schedule dentist appointment for next Tuesday at 2pm",
            "What's on the calendar tomorrow?",
            "Can we move piano lesson to 4pm?",
            "Show me this week's schedule",
        ]

        self.client.post(
            "/api/v1/ingest",
            json={
                "content": random.choice(messages),
                "channel": "web",
                "user_id": self.user_id,
            },
            headers=self.headers,
        )

    @task(2)
    def get_summary(self):
        """Test summary generation"""
        self.client.get(
            "/api/v1/summary", params={"period": "week"}, headers=self.headers
        )

    @task(1)
    def voice_command(self):
        """Test voice command endpoint"""
        commands = [
            "What do we have today?",
            "Schedule therapy session",
            "Cancel tomorrow's appointment",
        ]

        self.client.post(
            "/api/v1/voice/command",
            json={"audio_text": random.choice(commands), "language": "en"},
            headers=self.headers,
        )


class StressTestUser(HttpUser):
    """High-load stress testing user"""

    wait_time = between(0.1, 0.5)

    @task
    def rapid_health_checks(self):
        """Rapid health check requests"""
        self.client.get("/health")
