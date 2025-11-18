# Comprehensive Fix Plan

## Critical Issues to Fix

### 1. Database Models
- Models don't accept keyword arguments in __init__
- Need to add __init__ methods or use factory functions
- Tests expect models to accept kwargs

### 2. Missing Service Implementations
- TutorService - needs full implementation
- CaregiverService - needs full implementation  
- PriorityManager - needs full implementation
- CalendarIntegration - stub methods need implementation
- MobileIntegration - stub methods need implementation

### 3. Middleware Issues
- ComplianceMiddleware not applied to app
- SecurityMiddleware rate limiting not working
- CSRF protection not implemented

### 4. Test Fixtures
- Need proper database session fixtures
- Need auth token fixtures
- Need user/session factories

## Fix Order
1. Fix database models __init__ methods
2. Implement missing services
3. Apply middleware correctly
4. Fix test fixtures
5. Run tests incrementally

