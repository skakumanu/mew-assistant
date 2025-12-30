"""
Comprehensive tests for compliance middleware
"""

from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.compliance import (
    AccessControlValidator,
    ComplianceMiddleware,
    ConsentManager,
    DataMinimizationGuard,
)
from app.utils.exceptions import ComplianceViolationError


@pytest.fixture
def app():
    """Create test FastAPI app"""
    app = FastAPI()
    app.add_middleware(ComplianceMiddleware)

    @app.get("/mew/summary")
    async def get_summary():
        return {"summary": "test"}

    @app.post("/mew/ingest")
    async def ingest_data():
        return {"status": "ok"}

    @app.get("/public")
    async def public_endpoint():
        return {"data": "public"}

    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


class TestComplianceMiddleware:
    """Test compliance middleware functionality"""

    def test_missing_consent_header(self, client):
        """Test that endpoints requiring consent reject requests without consent header"""
        response = client.post("/mew/ingest")
        assert response.status_code == 403
        assert "consent" in response.json()["detail"].lower()

    def test_with_consent_header(self, client):
        """Test that request with consent header is allowed"""
        response = client.post("/mew/ingest", headers={"X-User-Consent": "true"})
        assert response.status_code == 200

    def test_public_endpoint_no_consent_required(self, client):
        """Test that public endpoints don't require consent"""
        response = client.get("/public")
        assert response.status_code == 200

    def test_security_headers_added(self, client):
        """Test that security headers are added to responses"""
        response = client.get("/public")

        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "Strict-Transport-Security" in response.headers
        assert "X-Privacy-Policy" in response.headers

    def test_audit_logging(self, client, caplog):
        """Test that audit logs are created for sensitive endpoints"""
        with caplog.at_level("INFO"):
            client.get(
                "/mew/summary",
                headers={"X-User-Consent": "true", "X-User-ID": "test-user"},
            )

        # Check audit logs were created
        audit_logs = [record for record in caplog.records if "AUDIT" in record.message]
        assert len(audit_logs) >= 2  # REQUEST and RESPONSE

    def test_ip_anonymization(self):
        """Test IP address anonymization"""
        middleware = ComplianceMiddleware(app=Mock())

        # Test IPv4
        ipv4 = "192.168.1.100"
        anonymized = middleware._anonymize_ip(ipv4)
        assert anonymized == "192.168.xxx.xxx"

        # Test IPv6
        ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        anonymized = middleware._anonymize_ip(ipv6)
        assert anonymized.endswith(":xxxx:xxxx:xxxx:xxxx")

    def test_phi_sanitization(self):
        """Test PHI sanitization in logs"""
        text = """
        Patient SSN: 123-45-6789
        Phone: 555-123-4567
        Email: patient@example.com
        DOB: 01/15/1980
        MRN: 12345
        """

        sanitized = ComplianceMiddleware.sanitize_phi(text)

        assert "123-45-6789" not in sanitized
        assert "555-123-4567" not in sanitized
        assert "patient@example.com" not in sanitized
        assert "01/15/1980" not in sanitized
        assert "[SSN_REDACTED]" in sanitized
        assert "[PHONE_REDACTED]" in sanitized
        assert "[EMAIL_REDACTED]" in sanitized


class TestDataMinimizationGuard:
    """Test data minimization compliance"""

    def test_allowed_fields_only(self):
        """Test that only allowed fields are kept"""
        data = {
            "session_id": "123",
            "user_id": "user1",
            "created_at": "2024-01-01",
            "sensitive_field": "should be removed",
            "unauthorized_data": "remove this",
        }

        filtered = DataMinimizationGuard.validate_fields("session", data)

        assert "session_id" in filtered
        assert "user_id" in filtered
        assert "created_at" in filtered
        assert "sensitive_field" not in filtered
        assert "unauthorized_data" not in filtered

    def test_invalid_entity_type(self):
        """Test error on invalid entity type"""
        with pytest.raises(ComplianceViolationError):
            DataMinimizationGuard.validate_fields("invalid_type", {})

    def test_warning_on_removed_fields(self, caplog):
        """Test warning is logged when fields are removed"""
        data = {"session_id": "123", "unauthorized": "data"}

        with caplog.at_level("WARNING"):
            DataMinimizationGuard.validate_fields("session", data)

        assert any("unauthorized" in record.message.lower() for record in caplog.records)


class TestAccessControlValidator:
    """Test access control validation"""

    def test_parent_full_access(self):
        """Test parents have full access to their own data"""
        result = AccessControlValidator.validate_access(
            user_role="parent",
            operation="delete",
            resource_owner="user123",
            user_id="user123",
        )
        assert result is True

    def test_caregiver_limited_access(self):
        """Test caregivers have limited access"""
        # Should succeed for read/write
        result = AccessControlValidator.validate_access(
            user_role="caregiver",
            operation="read",
            resource_owner="user123",
            user_id="caregiver456",
        )
        assert result is True

        # Should fail for delete
        with pytest.raises(ComplianceViolationError):
            AccessControlValidator.validate_access(
                user_role="caregiver",
                operation="delete",
                resource_owner="user123",
                user_id="caregiver456",
            )

    def test_educator_read_only(self):
        """Test educators have read-only access"""
        result = AccessControlValidator.validate_access(
            user_role="educator",
            operation="read",
            resource_owner="user123",
            user_id="educator789",
        )
        assert result is True

        with pytest.raises(ComplianceViolationError):
            AccessControlValidator.validate_access(
                user_role="educator",
                operation="write",
                resource_owner="user123",
                user_id="educator789",
            )

    def test_invalid_role(self):
        """Test error on invalid role"""
        with pytest.raises(ComplianceViolationError):
            AccessControlValidator.validate_access(
                user_role="hacker",
                operation="read",
                resource_owner="user123",
                user_id="bad_actor",
            )


class TestConsentManager:
    """Test consent management"""

    def test_all_consents_provided(self):
        """Test validation passes when all consents provided"""
        user_consents = {
            "data_collection": True,
            "data_processing": True,
            "data_sharing": True,
            "minors_data": True,
            "phi_access": True,
        }

        result = ConsentManager.validate_consent(
            user_consents, ["data_collection", "data_processing"]
        )
        assert result is True

    def test_missing_consent(self):
        """Test validation fails when consent missing"""
        user_consents = {"data_collection": True, "data_processing": False}

        with pytest.raises(ComplianceViolationError) as exc:
            ConsentManager.validate_consent(user_consents, ["data_collection", "data_processing"])

        assert "data_processing" in str(exc.value)

    def test_coppa_compliance(self):
        """Test COPPA compliance for minors"""
        # Without parental consent
        user_consents = {"data_collection": True, "minors_data": False}

        with pytest.raises(ComplianceViolationError) as exc:
            ConsentManager.validate_consent(user_consents, ["minors_data"])

        assert "COPPA" in str(exc.value) or "minors_data" in str(exc.value)

    def test_get_required_consents(self):
        """Test getting all required consent types"""
        consents = ConsentManager.get_required_consents()

        assert "data_collection" in consents
        assert "minors_data" in consents
        assert "phi_access" in consents
        assert len(consents) >= 5

    def test_unknown_consent_type(self):
        """Test error on unknown consent type"""
        with pytest.raises(ComplianceViolationError):
            ConsentManager.validate_consent({}, ["unknown_consent_type"])


class TestHIPAACompliance:
    """Test HIPAA-specific compliance requirements"""

    def test_phi_not_in_logs(self, client, caplog):
        """Test that PHI is not logged in plain text"""
        # Make a request that might contain PHI
        with caplog.at_level("INFO"):
            client.get("/public", headers={"X-Patient-SSN": "123-45-6789"})

        # Verify SSN not in logs
        for record in caplog.records:
            assert "123-45-6789" not in record.message

    def test_minimum_necessary_principle(self):
        """Test minimum necessary data principle"""
        # Should only keep necessary fields
        full_data = {
            "session_id": "123",
            "user_id": "user1",
            "created_at": "2024-01-01",
            "medical_history": "unnecessary",
            "full_ssn": "unnecessary",
        }

        filtered = DataMinimizationGuard.validate_fields("session", full_data)

        # Should not contain unnecessary medical data
        assert "medical_history" not in filtered
        assert "full_ssn" not in filtered


class TestCOPPACompliance:
    """Test COPPA compliance for children under 13"""

    def test_parental_consent_required(self):
        """Test parental consent required for children's data"""
        child_consents = {
            "data_collection": True,
            "minors_data": False,  # Missing parental consent
        }

        with pytest.raises(ComplianceViolationError):
            ConsentManager.validate_consent(child_consents, ["data_collection", "minors_data"])


class TestFERPACompliance:
    """Test FERPA compliance for educational records"""

    def test_educator_access_control(self):
        """Test educators have appropriate access to educational records"""
        # Educators should have read access
        result = AccessControlValidator.validate_access(
            user_role="educator",
            operation="read",
            resource_owner="student123",
            user_id="educator456",
        )
        assert result is True

        # But not write access to all data
        with pytest.raises(ComplianceViolationError):
            AccessControlValidator.validate_access(
                user_role="educator",
                operation="write",
                resource_owner="student123",
                user_id="educator456",
            )
