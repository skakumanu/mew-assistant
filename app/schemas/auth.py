"""
Pydantic schemas for authentication endpoints.
Handles user registration, login, and token management.
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional


from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    CAREGIVER = "caregiver"
    PARENT = "parent"
    THERAPIST = "therapist"
    EDUCATOR = "educator"


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    role: UserRole = Field(default=UserRole.PARENT, description="User role")
    phone: Optional[str] = Field(None, max_length=20)
    timezone: str = Field("UTC", max_length=50)


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=100, description="Password (min 8 characters)")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "email": "parent@example.com",
            "username": "john_doe",
            "password": "SecureP@ssw0rd",
            "full_name": "John Doe",
            "user_type": "parent",
            "phone": "+1234567890",
            "timezone": "America/New_York"
        }
    })


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "full_name": "John Smith",
            "phone": "+1234567890",
            "timezone": "America/Los_Angeles"
        }
    })


class UserResponse(UserBase):
    """Schema for user data in responses."""
    id: int
    is_active: bool
    is_verified: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "email": "parent@example.com",
                "username": "john_doe",
                "full_name": "John Doe",
                "user_type": "parent",
                "phone": "+1234567890",
                "timezone": "America/New_York",
                "is_active": True,
                "is_superuser": False,
                "created_at": "2024-11-15T10:00:00Z",
                "updated_at": "2024-11-15T10:00:00Z",
                "last_login": "2024-11-15T12:30:00Z"
            }
        }
    )


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Token expiration in seconds")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 1800
        }
    })


class TokenData(BaseModel):
    """Data extracted from JWT token."""
    email: Optional[str] = None


class LoginRequest(BaseModel):
    """Login credentials."""
    email: EmailStr
    password: str
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "email": "parent@example.com",
            "password": "SecureP@ssw0rd"
        }
    })


class LoginResponse(BaseModel):
    """Login response with tokens and user info."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 1800,
            "user": {
                "id": 1,
                "email": "parent@example.com",
                "username": "john_doe",
                "full_name": "John Doe",
                "user_type": "parent",
                "is_active": True,
                "is_superuser": False
            }
        }
    })


class RefreshTokenRequest(BaseModel):
    """Request to refresh access token."""
    refresh_token: str
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
    })


class PasswordChange(BaseModel):
    """Request to change password."""
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "current_password": "OldP@ssw0rd",
            "new_password": "NewSecureP@ssw0rd123"
        }
    })


class APIKeyCreate(BaseModel):
    """API key creation request"""
    key_name: str = Field(..., min_length=1, max_length=100)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)
    scopes: Optional[list[str]] = Field(default=["read"])


class APIKeyResponse(BaseModel):
    """API key response schema"""
    id: int
    key_name: str
    key_prefix: str
    api_key: Optional[str] = None
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime
    last_used: Optional[datetime]
    scopes: list[str]
    
    model_config = ConfigDict(from_attributes=True)
