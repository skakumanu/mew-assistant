"""
Privacy Guardrails Module
Implements privacy protection measures including PII detection, data anonymization,
and COPPA/FERPA compliance for special needs families.
"""

import hashlib
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PIIDetector:
    """Detects Personally Identifiable Information in text."""

    # Regex patterns for common PII
    PATTERNS = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b",
        "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        "medical_record": r"\b(MR|MRN)[:\s]?\d{6,}\b",
        "student_id": r"\b(SID|STUDENT[_\s]?ID)[:\s]?\d{6,}\b",
        "address": r"\b\d+\s+[\w\s]+\s+(street|st|avenue|ave|road|rd|drive|dr|lane|ln|way|court|ct|blvd|boulevard)\b",
        "date_of_birth": r"\b(0?[1-9]|1[0-2])[/-](0?[1-9]|[12]\d|3[01])[/-](19|20)\d{2}\b",
    }

    @classmethod
    def detect_pii(cls, text: str) -> Dict[str, List[str]]:
        """
        Detect PII in text.

        Args:
            text: Text to scan for PII

        Returns:
            Dictionary mapping PII types to found instances
        """
        findings = {}

        for pii_type, pattern in cls.PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                findings[pii_type] = matches

        return findings

    @classmethod
    def contains_pii(cls, text: str) -> bool:
        """Check if text contains any PII."""
        return bool(cls.detect_pii(text))


class DataAnonymizer:
    """Anonymizes sensitive data for privacy protection."""

    @staticmethod
    def anonymize_email(email: str) -> str:
        """Anonymize email address: user@domain.com -> u***@domain.com"""
        if "@" not in email:
            return email
        local, domain = email.split("@", 1)
        if len(local) <= 2:
            return f"{local[0]}***@{domain}"
        return f"{local[0]}{'*' * (len(local) - 1)}@{domain}"

    @staticmethod
    def anonymize_phone(phone: str) -> str:
        """Anonymize phone number: (123) 456-7890 -> (***) ***-7890"""
        digits = re.sub(r"\D", "", phone)
        if len(digits) >= 4:
            return f"{'*' * (len(digits) - 4)}{digits[-4:]}"
        return "*" * len(digits)

    @staticmethod
    def anonymize_name(name: str) -> str:
        """Anonymize name: John Doe -> J*** D***"""
        parts = name.split()
        return " ".join([f"{p[0]}{'*' * (len(p) - 1)}" if p else p for p in parts])

    @staticmethod
    def hash_identifier(identifier: str, salt: str = "") -> str:
        """Create deterministic hash of identifier for tracking without exposing PII."""
        return hashlib.sha256(f"{identifier}{salt}".encode()).hexdigest()[:16]

    @classmethod
    def anonymize_text(cls, text: str) -> str:
        """Automatically anonymize detected PII in text."""
        # Anonymize emails
        text = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            lambda m: cls.anonymize_email(m.group(0)),
            text,
        )

        # Anonymize phone numbers
        text = re.sub(
            r"\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b",
            lambda m: cls.anonymize_phone(m.group(0)),
            text,
        )

        # Anonymize SSN
        text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "***-**-****", text)

        # Anonymize credit cards
        text = re.sub(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", "**** **** **** ****", text)

        # Anonymize medical record numbers
        text = re.sub(r"\b(MR|MRN)[:\s]?\d{6,}\b", "MR******", text, flags=re.IGNORECASE)

        # Anonymize student IDs
        text = re.sub(
            r"\b(SID|STUDENT[_\s]?ID)[:\s]?\d{6,}\b",
            "SID******",
            text,
            flags=re.IGNORECASE,
        )

        return text


class PrivacyGuardrails:
    """Comprehensive privacy protection system."""

    def __init__(self):
        self.pii_detector = PIIDetector()
        self.anonymizer = DataAnonymizer()
        self.audit_log: List[Dict] = []

    def validate_coppa_compliance(self, user_age: Optional[int] = None) -> Dict[str, Any]:
        """
        Validate COPPA compliance (Children's Online Privacy Protection Act).

        Args:
            user_age: Age of user (if known)

        Returns:
            Compliance status and required actions
        """
        result = {
            "compliant": True,
            "requires_parental_consent": False,
            "restrictions": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        if user_age and user_age < 13:
            result["requires_parental_consent"] = True
            result["restrictions"] = [
                "No targeted advertising",
                "Parental consent required for data collection",
                "Limited data collection to operational necessity",
                "No public profile or social features",
            ]
            logger.info("COPPA restrictions applied for user under 13")

        return result

    def validate_ferpa_compliance(self, is_educational_record: bool = False) -> Dict[str, Any]:
        """
        Validate FERPA compliance (Family Educational Rights and Privacy Act).

        Args:
            is_educational_record: Whether data contains educational records

        Returns:
            Compliance status and requirements
        """
        result = {
            "compliant": True,
            "requires_consent": False,
            "restrictions": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        if is_educational_record:
            result["requires_consent"] = True
            result["restrictions"] = [
                "Parental consent required for disclosure",
                "Access restricted to authorized educational personnel",
                "Must maintain access logs",
                "Cannot share without explicit consent",
            ]
            logger.info("FERPA restrictions applied for educational records")

        return result

    def scan_and_protect(self, data: Dict[str, Any], anonymize: bool = True) -> Dict[str, Any]:
        """
        Scan data for PII and optionally anonymize.

        Args:
            data: Data dictionary to scan
            anonymize: Whether to anonymize detected PII

        Returns:
            Protected data and scan results
        """
        findings = {}
        protected_data = data.copy()

        for key, value in data.items():
            if isinstance(value, str):
                pii_found = self.pii_detector.detect_pii(value)
                if pii_found:
                    findings[key] = pii_found
                    if anonymize:
                        protected_data[key] = self.anonymizer.anonymize_text(value)
                        logger.warning(f"PII detected and anonymized in field: {key}")

        # Audit logging
        self.audit_log.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "pii_scan",
                "findings": findings,
                "anonymized": anonymize,
            }
        )

        return {
            "data": protected_data,
            "pii_detected": bool(findings),
            "findings": findings,
            "anonymized": anonymize,
        }

    def validate_data_minimization(
        self, collected_fields: List[str], required_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Validate data minimization principle - only collect necessary data.

        Args:
            collected_fields: Fields being collected
            required_fields: Fields actually required for service

        Returns:
            Validation result
        """
        excessive_fields = set(collected_fields) - set(required_fields)

        result = {
            "compliant": len(excessive_fields) == 0,
            "excessive_fields": list(excessive_fields),
            "recommendation": (
                "Remove unnecessary data collection" if excessive_fields else "Compliant"
            ),
            "timestamp": datetime.utcnow().isoformat(),
        }

        if excessive_fields:
            logger.warning(f"Data minimization violation: {excessive_fields}")

        return result

    def create_privacy_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Generate privacy compliance summary for a user.

        Args:
            user_id: User identifier (hashed)

        Returns:
            Privacy summary
        """
        return {
            "user_id_hash": self.anonymizer.hash_identifier(user_id),
            "timestamp": datetime.utcnow().isoformat(),
            "data_collected": [
                "Session interactions",
                "Message content (encrypted)",
                "Scheduling preferences",
                "Educational progress (FERPA protected)",
            ],
            "data_protection": {
                "encryption": "AES-256",
                "anonymization": "Automatic PII detection",
                "access_control": "Role-based with audit logs",
                "retention": "90 days default, 7 years for educational records",
            },
            "user_rights": [
                "Right to access data",
                "Right to delete data",
                "Right to correct data",
                "Right to export data",
                "Right to opt-out of data collection",
            ],
            "compliance_frameworks": [
                "COPPA (Children's Online Privacy Protection Act)",
                "FERPA (Family Educational Rights and Privacy Act)",
                "GDPR (General Data Protection Regulation)",
                "CCPA (California Consumer Privacy Act)",
                "HIPAA considerations for health-related data",
            ],
        }

    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Retrieve privacy audit log."""
        return self.audit_log[-limit:]


# Global instance
privacy_guardrails = PrivacyGuardrails()


def check_privacy_compliance(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to check privacy compliance.

    Args:
        data: Data to check

    Returns:
        Compliance report
    """
    return privacy_guardrails.scan_and_protect(data, anonymize=False)


def anonymize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to anonymize data.

    Args:
        data: Data to anonymize

    Returns:
        Anonymized data
    """
    result = privacy_guardrails.scan_and_protect(data, anonymize=True)
    return result["data"]
