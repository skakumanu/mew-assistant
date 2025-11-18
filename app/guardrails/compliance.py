"""
Compliance checking for HIPAA, COPPA, GDPR.
"""
from typing import Dict, List
from datetime import datetime


class ComplianceChecker:
    """Check compliance with various regulations."""
    
    def __init__(self):
        """Initialize compliance checker."""
        self.violations = []
    
    def check_hipaa(self, data: Dict) -> bool:
        """Check HIPAA compliance."""
        required_fields = ["user_consent", "data_encryption", "audit_log"]
        return all(field in data for field in required_fields)
    
    def check_coppa(self, user_age: int) -> bool:
        """Check COPPA compliance for users under 13."""
        return user_age >= 13 or "parental_consent" in self.violations
    
    def check_gdpr(self, data: Dict) -> bool:
        """Check GDPR compliance."""
        required_fields = ["consent", "data_purpose", "retention_policy"]
        return all(field in data for field in required_fields)
    
    def validate_all(self, data: Dict, user_age: int = None) -> Dict:
        """Validate all compliance requirements."""
        results = {
            "hipaa": self.check_hipaa(data),
            "gdpr": self.check_gdpr(data),
            "timestamp": datetime.utcnow().isoformat()
        }
        if user_age is not None:
            results["coppa"] = self.check_coppa(user_age)
        return results


class HIPAAGuardrails:
    """HIPAA compliance guardrails."""
    
    def __init__(self):
        """Initialize HIPAA guardrails."""
        self.checker = ComplianceChecker()
    
    def validate(self, data: Dict) -> Dict:
        """Validate HIPAA compliance."""
        return {
            "compliant": self.checker.check_hipaa(data),
            "regulation": "HIPAA",
            "timestamp": datetime.utcnow().isoformat()
        }


class COPPAGuardrails:
    """COPPA compliance guardrails for children under 13."""
    
    def __init__(self):
        """Initialize COPPA guardrails."""
        self.checker = ComplianceChecker()
    
    def validate(self, user_age: int, has_parental_consent: bool = False) -> Dict:
        """Validate COPPA compliance."""
        compliant = user_age >= 13 or has_parental_consent
        return {
            "compliant": compliant,
            "regulation": "COPPA",
            "requires_parental_consent": user_age < 13,
            "timestamp": datetime.utcnow().isoformat()
        }


class GDPRGuardrails:
    """GDPR compliance guardrails."""
    
    def __init__(self):
        """Initialize GDPR guardrails."""
        self.checker = ComplianceChecker()
    
    def validate(self, data: Dict) -> Dict:
        """Validate GDPR compliance."""
        return {
            "compliant": self.checker.check_gdpr(data),
            "regulation": "GDPR",
            "timestamp": datetime.utcnow().isoformat()
        }
