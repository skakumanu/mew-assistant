"""
Role-Based Access Control (RBAC) System
Defines roles, permissions, and access control utilities
"""

from enum import Enum
from functools import wraps
from typing import List

from fastapi import HTTPException, status


class UserRole(str, Enum):
    """User role definitions with hierarchy"""

    SUPERUSER = "SUPERUSER"  # Full system access, can manage all users/data
    ADMIN = "ADMIN"  # Can manage organization users and settings
    PARENT = "PARENT"  # Can manage family/kids, full calendar access
    CAREGIVER = "CAREGIVER"  # Limited access to assigned families
    KID = "KID"  # Limited access, requires parent approval


class Permission(str, Enum):
    """Granular permission definitions"""

    # User Management
    MANAGE_ALL_USERS = "manage:all_users"
    MANAGE_ORG_USERS = "manage:org_users"
    MANAGE_FAMILY_USERS = "manage:family_users"
    VIEW_USERS = "view:users"

    # Calendar Management
    MANAGE_ALL_CALENDARS = "manage:all_calendars"
    MANAGE_FAMILY_CALENDAR = "manage:family_calendar"
    VIEW_CALENDAR = "view:calendar"
    SUGGEST_CALENDAR = "suggest:calendar"

    # Schedule Management
    APPROVE_SCHEDULES = "approve:schedules"
    CREATE_SCHEDULES = "create:schedules"
    MODIFY_SCHEDULES = "modify:schedules"
    VIEW_SCHEDULES = "view:schedules"

    # Data Access
    ACCESS_ALL_DATA = "access:all_data"
    ACCESS_ORG_DATA = "access:org_data"
    ACCESS_FAMILY_DATA = "access:family_data"
    ACCESS_OWN_DATA = "access:own_data"

    # System Administration
    MANAGE_SYSTEM = "manage:system"
    VIEW_LOGS = "view:logs"
    MANAGE_INTEGRATIONS = "manage:integrations"


# Role-Permission Mapping
ROLE_PERMISSIONS: dict[UserRole, List[Permission]] = {
    UserRole.SUPERUSER: [
        # Full system access
        Permission.MANAGE_ALL_USERS,
        Permission.MANAGE_ALL_CALENDARS,
        Permission.APPROVE_SCHEDULES,
        Permission.CREATE_SCHEDULES,
        Permission.MODIFY_SCHEDULES,
        Permission.VIEW_SCHEDULES,
        Permission.ACCESS_ALL_DATA,
        Permission.MANAGE_SYSTEM,
        Permission.VIEW_LOGS,
        Permission.MANAGE_INTEGRATIONS,
    ],
    UserRole.ADMIN: [
        # Organization-level access
        Permission.MANAGE_ORG_USERS,
        Permission.VIEW_USERS,
        Permission.MANAGE_FAMILY_CALENDAR,
        Permission.APPROVE_SCHEDULES,
        Permission.CREATE_SCHEDULES,
        Permission.MODIFY_SCHEDULES,
        Permission.VIEW_SCHEDULES,
        Permission.ACCESS_ORG_DATA,
        Permission.VIEW_LOGS,
        Permission.MANAGE_INTEGRATIONS,
    ],
    UserRole.PARENT: [
        # Family-level access
        Permission.MANAGE_FAMILY_USERS,
        Permission.VIEW_USERS,
        Permission.MANAGE_FAMILY_CALENDAR,
        Permission.APPROVE_SCHEDULES,
        Permission.CREATE_SCHEDULES,
        Permission.MODIFY_SCHEDULES,
        Permission.VIEW_SCHEDULES,
        Permission.ACCESS_FAMILY_DATA,
    ],
    UserRole.CAREGIVER: [
        # Limited family access
        Permission.VIEW_USERS,
        Permission.VIEW_CALENDAR,
        Permission.CREATE_SCHEDULES,
        Permission.VIEW_SCHEDULES,
        Permission.ACCESS_FAMILY_DATA,
    ],
    UserRole.KID: [
        # Minimal access with approval requirements
        Permission.VIEW_CALENDAR,
        Permission.SUGGEST_CALENDAR,
        Permission.VIEW_SCHEDULES,
        Permission.ACCESS_OWN_DATA,
    ],
}


def has_permission(user_role: UserRole, required_permission: Permission) -> bool:
    """Check if a role has a specific permission"""
    return required_permission in ROLE_PERMISSIONS.get(user_role, [])


def require_permission(permission: Permission):
    """Decorator to enforce permission requirements on endpoints"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            # Check permission
            if not has_permission(UserRole(current_user.role), permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission} required",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(required_role: UserRole):
    """Decorator to enforce role requirements on endpoints"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            user_role = UserRole(current_user.role)

            # Role hierarchy check
            role_hierarchy = {
                UserRole.SUPERUSER: 5,
                UserRole.ADMIN: 4,
                UserRole.PARENT: 3,
                UserRole.CAREGIVER: 2,
                UserRole.KID: 1,
            }

            if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient role: {required_role} or higher required",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
