"""
Privacy Guardrails Tests
Tests for PII detection, data anonymization, and privacy compliance.
"""

import pytest

from app.utils.privacy import (DataAnonymizer, PIIDetector, PrivacyGuardrails,
                               anonymize_data, check_privacy_compliance)


class TestPIIDetector:
    """Test PII detection functionality."""

    def test_detect_email(self):
        """Test email detection."""
        text = "Contact me at john.doe@example.com"
        findings = PIIDetector.detect_pii(text)

        assert "email" in findings
        assert "john.doe@example.com" in findings["email"]

    def test_detect_phone(self):
        """Test phone number detection."""
        text = "Call me at (555) 123-4567 or 555-987-6543"
        findings = PIIDetector.detect_pii(text)

        assert "phone" in findings
        assert len(findings["phone"]) == 2

    def test_detect_ssn(self):
        """Test SSN detection."""
        text = "SSN: 123-45-6789"
        findings = PIIDetector.detect_pii(text)

        assert "ssn" in findings
        assert "123-45-6789" in findings["ssn"]

    def test_detect_credit_card(self):
        """Test credit card detection."""
        text = "Card: 1234-5678-9012-3456"
        findings = PIIDetector.detect_pii(text)

        assert "credit_card" in findings

    def test_detect_medical_record(self):
        """Test medical record number detection."""
        text = "Medical Record: MR123456"
        findings = PIIDetector.detect_pii(text)

        assert "medical_record" in findings

    def test_detect_student_id(self):
        """Test student ID detection."""
        text = "Student ID: SID789012"
        findings = PIIDetector.detect_pii(text)

        assert "student_id" in findings

    def test_detect_address(self):
        """Test address detection."""
        text = "I live at 123 Main Street"
        findings = PIIDetector.detect_pii(text)

        assert "address" in findings

    def test_detect_dob(self):
        """Test date of birth detection."""
        text = "DOB: 01/15/2010"
        findings = PIIDetector.detect_pii(text)

        assert "date_of_birth" in findings

    def test_no_pii(self):
        """Test text without PII."""
        text = "This is a normal message about scheduling"
        findings = PIIDetector.detect_pii(text)

        assert len(findings) == 0
        assert not PIIDetector.contains_pii(text)

    def test_multiple_pii_types(self):
        """Test detection of multiple PII types."""
        text = "Contact John at john@example.com or (555) 123-4567. SSN: 123-45-6789"
        findings = PIIDetector.detect_pii(text)

        assert "email" in findings
        assert "phone" in findings
        assert "ssn" in findings


class TestDataAnonymizer:
    """Test data anonymization functionality."""

    def test_anonymize_email(self):
        """Test email anonymization."""
        email = "john.doe@example.com"
        anonymized = DataAnonymizer.anonymize_email(email)

        assert anonymized.startswith("j")
        assert "@example.com" in anonymized
        assert "john.doe" not in anonymized

    def test_anonymize_short_email(self):
        """Test short email anonymization."""
        email = "ab@test.com"
        anonymized = DataAnonymizer.anonymize_email(email)

        assert anonymized.startswith("a")
        assert "@test.com" in anonymized

    def test_anonymize_phone(self):
        """Test phone anonymization."""
        phone = "(555) 123-4567"
        anonymized = DataAnonymizer.anonymize_phone(phone)

        assert anonymized.endswith("4567")
        assert "555" not in anonymized

    def test_anonymize_name(self):
        """Test name anonymization."""
        name = "John Doe"
        anonymized = DataAnonymizer.anonymize_name(name)

        # Should anonymize to "J*** D**" (accounting for length)
        assert anonymized.startswith("J***")
        assert "D" in anonymized
        assert "John" not in anonymized
        assert "Doe" not in anonymized

    def test_hash_identifier(self):
        """Test identifier hashing."""
        identifier = "user123"
        hashed1 = DataAnonymizer.hash_identifier(identifier)
        hashed2 = DataAnonymizer.hash_identifier(identifier)

        assert hashed1 == hashed2  # Deterministic
        assert len(hashed1) == 16
        assert hashed1 != identifier

    def test_hash_identifier_with_salt(self):
        """Test identifier hashing with salt."""
        identifier = "user123"
        hashed1 = DataAnonymizer.hash_identifier(identifier, salt="salt1")
        hashed2 = DataAnonymizer.hash_identifier(identifier, salt="salt2")

        assert hashed1 != hashed2  # Different salts = different hashes

    def test_anonymize_text(self):
        """Test full text anonymization."""
        text = "Contact john@example.com at (555) 123-4567. SSN: 123-45-6789"
        anonymized = DataAnonymizer.anonymize_text(text)

        assert "john@example.com" not in anonymized
        assert "(555) 123-4567" not in anonymized
        assert "123-45-6789" not in anonymized
        assert "***-**-****" in anonymized


class TestPrivacyGuardrails:
    """Test privacy guardrails system."""

    def test_coppa_compliance_adult(self):
        """Test COPPA compliance for adults."""
        guardrails = PrivacyGuardrails()
        result = guardrails.validate_coppa_compliance(user_age=18)

        assert result["compliant"]
        assert not result["requires_parental_consent"]
        assert len(result["restrictions"]) == 0

    def test_coppa_compliance_child(self):
        """Test COPPA compliance for children under 13."""
        guardrails = PrivacyGuardrails()
        result = guardrails.validate_coppa_compliance(user_age=10)

        assert result["compliant"]
        assert result["requires_parental_consent"]
        assert len(result["restrictions"]) > 0
        assert any("consent" in r.lower() for r in result["restrictions"])

    def test_ferpa_compliance_non_educational(self):
        """Test FERPA compliance for non-educational data."""
        guardrails = PrivacyGuardrails()
        result = guardrails.validate_ferpa_compliance(is_educational_record=False)

        assert result["compliant"]
        assert not result["requires_consent"]

    def test_ferpa_compliance_educational(self):
        """Test FERPA compliance for educational records."""
        guardrails = PrivacyGuardrails()
        result = guardrails.validate_ferpa_compliance(is_educational_record=True)

        assert result["compliant"]
        assert result["requires_consent"]
        assert len(result["restrictions"]) > 0

    def test_scan_and_protect_with_pii(self):
        """Test scanning data with PII."""
        guardrails = PrivacyGuardrails()
        data = {
            "message": "Contact me at john@example.com",
            "phone": "(555) 123-4567",
            "notes": "Regular message",
        }

        result = guardrails.scan_and_protect(data, anonymize=False)

        assert result["pii_detected"]
        assert "message" in result["findings"] or "phone" in result["findings"]

    def test_scan_and_protect_with_anonymization(self):
        """Test scanning and anonymizing data."""
        guardrails = PrivacyGuardrails()
        data = {"message": "Contact me at john@example.com", "phone": "(555) 123-4567"}

        result = guardrails.scan_and_protect(data, anonymize=True)

        assert result["pii_detected"]
        assert result["anonymized"]
        assert "john@example.com" not in str(result["data"])

    def test_scan_without_pii(self):
        """Test scanning data without PII."""
        guardrails = PrivacyGuardrails()
        data = {
            "message": "Schedule a tutoring session for tomorrow",
            "topic": "Math homework",
        }

        result = guardrails.scan_and_protect(data, anonymize=True)

        assert not result["pii_detected"]
        assert result["data"] == data

    def test_data_minimization_compliant(self):
        """Test compliant data minimization."""
        guardrails = PrivacyGuardrails()
        collected = ["name", "email", "session_id"]
        required = ["name", "email", "session_id"]

        result = guardrails.validate_data_minimization(collected, required)

        assert result["compliant"]
        assert len(result["excessive_fields"]) == 0

    def test_data_minimization_violation(self):
        """Test data minimization violation."""
        guardrails = PrivacyGuardrails()
        collected = ["name", "email", "ssn", "credit_card", "session_id"]
        required = ["name", "session_id"]

        result = guardrails.validate_data_minimization(collected, required)

        assert not result["compliant"]
        assert "ssn" in result["excessive_fields"]
        assert "credit_card" in result["excessive_fields"]

    def test_privacy_summary_generation(self):
        """Test privacy summary generation."""
        guardrails = PrivacyGuardrails()
        summary = guardrails.create_privacy_summary("user123")

        assert "user_id_hash" in summary
        assert summary["user_id_hash"] != "user123"
        assert "data_collected" in summary
        assert "data_protection" in summary
        assert "user_rights" in summary
        assert "compliance_frameworks" in summary
        assert "COPPA" in str(summary["compliance_frameworks"])
        assert "FERPA" in str(summary["compliance_frameworks"])

    def test_audit_log_creation(self):
        """Test audit log creation."""
        guardrails = PrivacyGuardrails()
        data = {"message": "Test message with email@test.com"}

        guardrails.scan_and_protect(data, anonymize=True)
        audit_log = guardrails.get_audit_log()

        assert len(audit_log) > 0
        assert audit_log[-1]["action"] == "pii_scan"

    def test_audit_log_limit(self):
        """Test audit log limit."""
        guardrails = PrivacyGuardrails()

        # Generate multiple audit entries
        for i in range(10):
            data = {"message": f"Test {i}"}
            guardrails.scan_and_protect(data)

        limited_log = guardrails.get_audit_log(limit=5)
        assert len(limited_log) == 5


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_check_privacy_compliance(self):
        """Test privacy compliance check function."""
        data = {"message": "Contact john@example.com", "notes": "Normal text"}

        result = check_privacy_compliance(data)

        assert "pii_detected" in result
        assert "findings" in result
        assert not result["anonymized"]

    def test_anonymize_data_function(self):
        """Test data anonymization function."""
        data = {
            "message": "Email: john@example.com, Phone: (555) 123-4567",
            "notes": "SSN: 123-45-6789",
        }

        anonymized = anonymize_data(data)

        assert "john@example.com" not in str(anonymized)
        assert "(555) 123-4567" not in str(anonymized)
        assert "123-45-6789" not in str(anonymized)


class TestPrivacyIntegration:
    """Test privacy guardrails integration scenarios."""

    def test_child_with_educational_records(self):
        """Test privacy for child with educational records."""
        guardrails = PrivacyGuardrails()

        coppa = guardrails.validate_coppa_compliance(user_age=10)
        ferpa = guardrails.validate_ferpa_compliance(is_educational_record=True)

        assert coppa["requires_parental_consent"]
        assert ferpa["requires_consent"]

        # Both require parental consent
        assert coppa["compliant"] and ferpa["compliant"]

    def test_full_privacy_workflow(self):
        """Test complete privacy protection workflow."""
        guardrails = PrivacyGuardrails()

        # 1. Check compliance requirements
        coppa = guardrails.validate_coppa_compliance(user_age=12)
        ferpa = guardrails.validate_ferpa_compliance(is_educational_record=True)

        # 2. Scan incoming data
        data = {
            "student_name": "Jane Doe",
            "email": "parent@example.com",
            "notes": "Math tutoring needed. Phone: (555) 123-4567",
            "progress": "Struggling with fractions",
        }

        scan_result = guardrails.scan_and_protect(data, anonymize=True)

        # 3. Check data minimization
        collected = list(data.keys())
        required = ["student_name", "notes", "progress"]
        minimization = guardrails.validate_data_minimization(collected, required)

        # 4. Generate privacy summary
        summary = guardrails.create_privacy_summary("student123")

        # Verify workflow results
        assert coppa["requires_parental_consent"]
        assert ferpa["requires_consent"]
        assert scan_result["pii_detected"]
        assert scan_result["anonymized"]
        assert not minimization["compliant"]  # email not required
        assert "COPPA" in str(summary["compliance_frameworks"])
        assert "FERPA" in str(summary["compliance_frameworks"])

    def test_sensitive_health_data(self):
        """Test handling of sensitive health-related data."""
        guardrails = PrivacyGuardrails()

        data = {
            "message": "Child has autism diagnosis. Contact Dr. Smith at (555) 123-4567",
            "medical_record": "MR123456",
            "notes": "Requires sensory breaks",
        }

        result = guardrails.scan_and_protect(data, anonymize=True)

        assert result["pii_detected"]
        # Should detect medical record number
        assert "medical_record" in result["findings"]
        # Original data should be anonymized
        assert "MR123456" not in str(result["data"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
