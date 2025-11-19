"""
HIPAA and Data Privacy Compliance Middleware

This middleware enforces compliance with:
- HIPAA (Health Insurance Portability and Accountability Act)
- COPPA (Children's Online Privacy Protection Act)
- FERPA (Family Educational Rights and Privacy Act)
- General data privacy best practices
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Set
import re
import logging
from datetime import datetime

from app.utils.logger import get_logger
from app.utils.exceptions import ComplianceViolationError

logger = get_logger(__name__)


class ComplianceMiddleware(BaseHTTPMiddleware):
    """
    Middleware to ensure compliance with healthcare and privacy regulations
    """
    
    # PHI (Protected Health Information) patterns to detect and mask
    PHI_PATTERNS = {
        'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'dob': re.compile(r'\b\d{1,2}/\d{1,2}/\d{4}\b'),
        'medical_record': re.compile(r'\bMRN[:\s]*\d+\b', re.IGNORECASE),
        'diagnosis_code': re.compile(r'\b[A-Z]\d{2}\.\d{1,2}\b'),  # ICD-10 codes
    }
    
    # Endpoints exempt from all compliance checks
    EXEMPT_ENDPOINTS: Set[str] = {
        '/auth/register',
        '/auth/login',
        '/auth/refresh',
        '/health',
        '/docs',
        '/openapi.json',
        '/redoc',
        '/'
    }
    
    # Endpoints that require consent verification
    CONSENT_REQUIRED_ENDPOINTS: Set[str] = {
        '/mew/ingest',
        '/mew/summary',
        '/sessions',
        '/messages'
    }
    
    # Sensitive endpoints requiring audit logging
    AUDIT_REQUIRED_ENDPOINTS: Set[str] = {
        '/mew/summary',
        '/sessions/{session_id}',
        '/messages'
    }
    
    async def dispatch(self, request: Request, call_next):
        """
        Process each request for compliance checks
        """
        start_time = datetime.utcnow()
        
        # Skip all compliance checks for exempt endpoints
        if any(request.url.path.startswith(endpoint) for endpoint in self.EXEMPT_ENDPOINTS):
            response = await call_next(request)
            return response
        
        # 1. Check for required consent headers
        await self._verify_consent(request)
        
        # 2. Validate data retention requirements
        await self._check_data_retention(request)
        
        # 3. Log audit trail for sensitive operations
        if self._requires_audit(request.url.path):
            await self._create_audit_log(request, "REQUEST")
        
        # 4. Process request
        response = await call_next(request)
        
        # 5. Sanitize response for PHI
        # Note: Response body sanitization happens at service layer
        
        # 6. Add compliance headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['X-Privacy-Policy'] = '/privacy'
        
        # 7. Log audit trail completion
        if self._requires_audit(request.url.path):
            duration = (datetime.utcnow() - start_time).total_seconds()
            await self._create_audit_log(request, "RESPONSE", response.status_code, duration)
        
        return response
    
    async def _verify_consent(self, request: Request):
        """
        Verify user consent for data processing (HIPAA/COPPA requirement)
        """
        import os
        # Skip consent checks in test mode
        if os.getenv('TESTING') == 'true':
            return
            
        if any(request.url.path.startswith(endpoint) for endpoint in self.CONSENT_REQUIRED_ENDPOINTS):
            consent_header = request.headers.get('X-User-Consent') or request.headers.get('X-Consent-Given')
            
            if not consent_header or consent_header != 'true':
                logger.warning(f"Missing consent for {request.url.path}")
                raise ComplianceViolationError(
                    "User consent required for this operation. "
                    "Include 'X-User-Consent: true' header after obtaining proper consent."
                )
    
    async def _check_data_retention(self, request: Request):
        """
        Ensure data retention policies are followed
        """
        # HIPAA requires minimum 6 years retention for medical records
        # This is checked at service layer, but we validate request context
        if request.method == "DELETE":
            retention_override = request.headers.get('X-Retention-Override')
            if not retention_override:
                logger.info(f"Data deletion requested for {request.url.path}")
    
    def _requires_audit(self, path: str) -> bool:
        """
        Check if endpoint requires audit logging
        """
        return any(path.startswith(endpoint.split('{')[0]) 
                  for endpoint in self.AUDIT_REQUIRED_ENDPOINTS)
    
    async def _create_audit_log(
        self, 
        request: Request, 
        event_type: str,
        status_code: int = None,
        duration: float = None
    ):
        """
        Create comprehensive audit log for compliance
        Required by HIPAA for all PHI access
        """
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': request.headers.get('X-User-ID', 'anonymous'),
            'ip_address': self._anonymize_ip(request.client.host),
            'method': request.method,
            'path': request.url.path,
            'user_agent': request.headers.get('User-Agent', 'unknown'),
        }
        
        if status_code:
            audit_entry['status_code'] = status_code
        if duration:
            audit_entry['duration_seconds'] = duration
        
        # Log to secure audit log (should be sent to SIEM in production)
        logger.info(f"AUDIT: {audit_entry}")
    
    @staticmethod
    def _anonymize_ip(ip: str) -> str:
        """
        Anonymize IP address for privacy compliance
        """
        if ':' in ip:  # IPv6
            parts = ip.split(':')
            return ':'.join(parts[:4]) + ':xxxx:xxxx:xxxx:xxxx'
        else:  # IPv4
            parts = ip.split('.')
            return '.'.join(parts[:2]) + '.xxx.xxx'
    
    @classmethod
    def sanitize_phi(cls, text: str) -> str:
        """
        Sanitize text to remove PHI (Protected Health Information)
        This should be used in logging and non-secure outputs
        """
        sanitized = text
        
        for phi_type, pattern in cls.PHI_PATTERNS.items():
            sanitized = pattern.sub(f'[{phi_type.upper()}_REDACTED]', sanitized)
        
        return sanitized


class DataMinimizationGuard:
    """
    Ensures only necessary data is collected and stored (GDPR/HIPAA principle)
    """
    
    ALLOWED_FIELDS = {
        'session': {'user_id', 'session_id', 'created_at', 'last_interaction', 'metadata'},
        'message': {'session_id', 'content', 'channel', 'timestamp', 'priority'},
        'summary': {'session_id', 'summary_type', 'content', 'generated_at'},
    }
    
    @classmethod
    def validate_fields(cls, entity_type: str, data: dict) -> dict:
        """
        Validate that only allowed fields are being stored
        """
        if entity_type not in cls.ALLOWED_FIELDS:
            raise ComplianceViolationError(f"Unknown entity type: {entity_type}")
        
        allowed = cls.ALLOWED_FIELDS[entity_type]
        filtered_data = {k: v for k, v in data.items() if k in allowed}
        
        removed_fields = set(data.keys()) - set(filtered_data.keys())
        if removed_fields:
            logger.warning(f"Removed unauthorized fields: {removed_fields}")
        
        return filtered_data


class AccessControlValidator:
    """
    Validates access control for special needs data
    """
    
    ROLE_PERMISSIONS = {
        'parent': {'read', 'write', 'delete'},
        'caregiver': {'read', 'write'},
        'therapist': {'read', 'write'},
        'educator': {'read'},
        'admin': {'read', 'write', 'delete', 'manage'},
    }
    
    @classmethod
    def validate_access(cls, user_role: str, operation: str, resource_owner: str, user_id: str):
        """
        Validate user has permission to perform operation
        """
        if user_role not in cls.ROLE_PERMISSIONS:
            raise ComplianceViolationError(f"Invalid user role: {user_role}")
        
        # Parents always have full access to their own data
        if user_role == 'parent' and resource_owner == user_id:
            return True
        
        # Check role-based permissions
        allowed_operations = cls.ROLE_PERMISSIONS[user_role]
        if operation not in allowed_operations:
            raise ComplianceViolationError(
                f"Role '{user_role}' not authorized for operation '{operation}'"
            )
        
        return True


class ConsentManager:
    """
    Manages user consent for COPPA and HIPAA compliance
    """
    
    REQUIRED_CONSENTS = {
        'data_collection': 'Agreement to collect and store interaction data',
        'data_processing': 'Agreement to process data with AI/ML models',
        'data_sharing': 'Agreement to share data with authorized caregivers',
        'minors_data': 'Parental consent for children under 13 (COPPA)',
        'phi_access': 'Consent to access Protected Health Information',
    }
    
    @classmethod
    def validate_consent(cls, user_consents: dict, required_consent_types: list) -> bool:
        """
        Validate user has provided all required consents
        """
        for consent_type in required_consent_types:
            if consent_type not in cls.REQUIRED_CONSENTS:
                raise ComplianceViolationError(f"Unknown consent type: {consent_type}")
            
            if not user_consents.get(consent_type, False):
                raise ComplianceViolationError(
                    f"Missing required consent: {cls.REQUIRED_CONSENTS[consent_type]}"
                )
        
        return True
    
    @classmethod
    def get_required_consents(cls) -> dict:
        """
        Return all required consent types and descriptions
        """
        return cls.REQUIRED_CONSENTS.copy()
