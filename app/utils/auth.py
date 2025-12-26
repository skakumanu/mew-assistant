"""
JWT authentication utilities.
Handles token generation, validation, and password hashing.
Supports both JWT tokens and API keys for authentication.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import secrets
import hashlib
import os
import logging

from app.database.connection import get_db
from app.database.models import User, APIKey

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

# Token Expiration Configuration
# NOTE: 30-day (43200 minutes) default is intentional for OAuth-based authentication
# where users sign in via Google/Microsoft. These are federated identities with
# their own security controls. For password-based auth, consider shorter durations.
# Override with ACCESS_TOKEN_EXPIRE_MINUTES environment variable if needed.
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "43200"))  # 30 days default
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password hashing using Argon2 (more modern and secure than bcrypt)
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

# Security scheme
# Allow manual handling of missing credentials so we can return 401 instead of 403
security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash using Argon2."""
    return pwd_context.hash(password)


def verify_kid_account(user: User) -> None:
    """
    Verify that the user is a kid account.
    Raises HTTPException if not a kid account.
    
    Args:
        user: User object to verify
        
    Raises:
        HTTPException: If user is not a kid account
    """
    if not user.is_kid_account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available for kid accounts"
        )
    
    # Additional safety check: ensure kid has a linked parent
    if not user.parent_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Kid account must be linked to a parent account"
        )


def verify_parent_account(user: User) -> None:
    """
    Verify that the user is a parent account (not a kid account).
    Raises HTTPException if user is a kid account.
    
    Args:
        user: User object to verify
        
    Raises:
        HTTPException: If user is a kid account
    """
    if user.is_kid_account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available for parent/caregiver accounts"
        )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Data to encode in the token (typically {"sub": user_email})
        expires_delta: Optional custom expiration time
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token with longer expiration."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode and validate JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        logger.error("Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        logger.error(f"Invalid JWT: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    
    Use this in endpoint dependencies to require authentication:
    ```python
    @router.get("/protected")
    async def protected_route(current_user: User = Depends(get_current_user)):
        return {"user": current_user.email}
    ```
    """

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        # Prefer explicit numeric user_id in token payload; fall back to sub (email or id)
        token_user_id = payload.get("user_id")
        sub = payload.get("sub")

        logger.info(f"Token decoded successfully, user_id: {token_user_id}, sub: {sub}")

        if token_user_id is None and sub is None:
            logger.error("No user identifier in token payload")
            raise credentials_exception

        # Verify token type
        if payload.get("type") != "access":
            logger.error(f"Invalid token type: {payload.get('type')}")
            raise credentials_exception
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise credentials_exception
    
    # Get user from database by explicit user_id or by email (sub)
    user = None
    if token_user_id is not None:
        # token_user_id may be a numeric primary key or a string user_id
        try:
            # try numeric id first
            user = db.query(User).filter(User.id == int(token_user_id)).first()
        except (ValueError, TypeError):
            # fallback to string user_id column
            user = db.query(User).filter(User.user_id == str(token_user_id)).first()
    else:
        # treat sub as email
        user = db.query(User).filter(User.email == sub).first()

    if user is None:
        logger.error(f"User not found in database for token identifiers user_id={token_user_id} sub={sub}")
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (alias for compatibility)."""
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to require superuser/admin privileges."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate user with email and password.
    
    Args:
        db: Database session
        email: User email
        password: Plain text password
        
    Returns:
        User object if authentication successful, None otherwise
    """
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.
    Returns: (full_key, key_hash, key_prefix)
    """
    key = secrets.token_urlsafe(32)
    full_key = f"mew_{key}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    key_prefix = full_key[:12] + "..."
    return full_key, key_hash, key_prefix


async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Verify API key and return associated user"""
    api_key = credentials.credentials
    
    if not api_key.startswith("mew_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format"
        )
    
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    api_key_record = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.is_active == True
    ).first()
    
    if not api_key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired"
        )
    
    api_key_record.last_used = datetime.utcnow()
    db.commit()
    
    user = db.query(User).filter(User.id == api_key_record.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user


async def get_current_user_flexible(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Flexible authentication: accepts both JWT tokens and API keys.
    Automatically detects which type is provided.
    """
    token = credentials.credentials
    
    if token.startswith("mew_"):
        return await verify_api_key(credentials, db)
    
    return await get_current_user(credentials, db)


def require_role(*roles: str):
    """Dependency to require specific user roles"""
    async def role_checker(current_user: User = Depends(get_current_user_flexible)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(roles)}"
            )
        return current_user
    return role_checker
