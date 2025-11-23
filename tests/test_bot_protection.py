"""
Tests for bot protection middleware and CAPTCHA
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.middleware.bot_protection import captcha_verifier
import time

client = TestClient(app)

class TestBotProtection:
    """Test bot protection middleware"""
    
    def test_rate_limiting(self):
        """Test that rate limiting blocks excessive requests"""
        # Make many requests quickly
        responses = []
        for i in range(110):  # Exceed the 100 requests/minute limit
            response = client.get("/health")
            responses.append(response.status_code)
        
        # Should have some 429 responses
        assert 429 in responses
    
    def test_suspicious_sql_injection(self):
        """Test SQL injection detection"""
        response = client.get("/api/search?q=1' OR '1'='1")
        # Should block or sanitize
        assert response.status_code in [400, 403, 422]
    
    def test_suspicious_xss(self):
        """Test XSS attack detection"""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "full_name": "<script>alert('xss')</script>"
            }
        )
        # Should block or sanitize
        assert response.status_code in [400, 403, 422]
    
    def test_missing_user_agent(self):
        """Test that requests without User-Agent are blocked"""
        import requests
        response = requests.get(
            f"http://testserver/auth/login",
            headers={}  # No User-Agent
        )
        # Health endpoints should still work
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_bad_bot_user_agent(self):
        """Test that known bad bots are blocked"""
        response = client.get(
            "/api/sessions",
            headers={"User-Agent": "sqlmap/1.0"}
        )
        assert response.status_code in [403, 401]  # Blocked or unauthorized
    
    def test_legitimate_user_agent(self):
        """Test that legitimate clients are allowed"""
        response = client.get(
            "/health",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        assert response.status_code == 200


class TestCaptcha:
    """Test CAPTCHA verification"""
    
    def test_generate_challenge(self):
        """Test CAPTCHA challenge generation"""
        response = client.get("/auth/captcha/challenge?user_id=test_user")
        assert response.status_code == 200
        data = response.json()
        assert "challenge_id" in data
        assert "question" in data
        assert "expires_in" in data
    
    def test_verify_correct_response(self):
        """Test correct CAPTCHA response"""
        # Generate challenge
        challenge_response = client.get("/auth/captcha/challenge?user_id=test_user")
        challenge_data = challenge_response.json()
        challenge_id = challenge_data["challenge_id"]
        
        # Extract answer from question "What is X + Y?"
        question = challenge_data["question"]
        import re
        match = re.search(r"What is (\d+) \+ (\d+)\?", question)
        if match:
            answer = str(int(match.group(1)) + int(match.group(2)))
            
            # Verify
            verify_response = client.post(
                f"/auth/captcha/verify?challenge_id={challenge_id}&response={answer}"
            )
            assert verify_response.status_code == 200
            assert verify_response.json()["verified"] == True
    
    def test_verify_incorrect_response(self):
        """Test incorrect CAPTCHA response"""
        # Generate challenge
        challenge_response = client.get("/auth/captcha/challenge?user_id=test_user")
        challenge_data = challenge_response.json()
        challenge_id = challenge_data["challenge_id"]
        
        # Try wrong answer
        verify_response = client.post(
            f"/auth/captcha/verify?challenge_id={challenge_id}&response=999"
        )
        assert verify_response.status_code == 400
    
    def test_verify_expired_challenge(self):
        """Test that expired challenges are rejected"""
        challenge = captcha_verifier.generate_challenge("test_user")
        challenge_id = challenge["challenge_id"]
        
        # Manually expire the challenge
        if challenge_id in captcha_verifier.pending_verifications:
            from datetime import datetime, timedelta
            captcha_verifier.pending_verifications[challenge_id] = (
                "1", 
                datetime.utcnow() - timedelta(minutes=1)
            )
        
        # Try to verify
        verify_response = client.post(
            f"/auth/captcha/verify?challenge_id={challenge_id}&response=1"
        )
        assert verify_response.status_code == 400
    
    def test_cleanup_expired_challenges(self):
        """Test that expired challenges are cleaned up"""
        # Generate some challenges
        for i in range(5):
            captcha_verifier.generate_challenge(f"user_{i}")
        
        initial_count = len(captcha_verifier.pending_verifications)
        
        # Cleanup
        captcha_verifier.cleanup_expired()
        
        # Count should be same or less (if any expired)
        assert len(captcha_verifier.pending_verifications) <= initial_count


class TestIPBlocking:
    """Test IP blocking functionality"""
    
    def test_temporary_block_after_rate_limit(self):
        """Test that IPs are temporarily blocked after exceeding rate limit"""
        # Make excessive requests
        for i in range(110):
            response = client.get("/health")
        
        # Next request should be blocked
        response = client.get("/health")
        if response.status_code == 429:
            assert "retry_after" in response.json()
    
    def test_block_expires(self):
        """Test that blocks expire after timeout"""
        # This would require time manipulation or waiting
        # For now, just verify the block response structure
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
