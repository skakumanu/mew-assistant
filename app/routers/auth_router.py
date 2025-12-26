"""
Authentication API endpoints.
Handles user registration, login, token refresh, and API key management.
"""

import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import APIKey, User
from app.schemas.auth import (APIKeyCreate, APIKeyResponse, LoginRequest,
                              LoginResponse, PasswordChange,
                              RefreshTokenRequest, Token, UserCreate,
                              UserResponse, UserUpdate)
from app.utils.auth import (ACCESS_TOKEN_EXPIRE_MINUTES, authenticate_user,
                            create_access_token, create_refresh_token,
                            decode_token, generate_api_key, get_current_user,
                            get_current_user_flexible, get_password_hash,
                            verify_password)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.

    - **email**: Valid email address (unique)
    - **username**: Username (unique, 3-50 characters)
    - **password**: Password (min 8 characters)
    - **role**: User role (parent, caregiver, therapist, educator, admin)
    """
    # Check if user already exists
    existing_user = (
        db.query(User)
        .filter((User.email == user_data.email) | (User.username == user_data.username))
        .first()
    )

    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
            )

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
        phone=user_data.phone,
        timezone=user_data.timezone,
        is_active=True,
        is_verified=False,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT tokens.

    Returns both access and refresh tokens.
    Access token expires in 30 minutes, refresh token in 7 days.
    """
    user = authenticate_user(db, login_data.email, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
        )

    # Create tokens
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    Provide a valid refresh token to get a new access token.
    """
    try:
        payload = decode_token(refresh_data.refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        user = db.query(User).filter(User.email == email).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Create new tokens
        access_token = create_access_token(data={"sub": user.email})
        new_refresh_token = create_refresh_token(data={"sub": user.email})

        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user_flexible),
):
    """
    Get current authenticated user information.

    Requires valid JWT token or API key in Authorization header.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update current user profile information.

    Can update: full_name, phone, timezone
    """
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.phone is not None:
        current_user.phone = user_update.phone
    if user_update.timezone is not None:
        current_user.timezone = user_update.timezone

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return current_user


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change user password.

    Requires current password for verification.
    """
    if not verify_password(
        password_data.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password"
        )

    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Password updated successfully"}


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new API key for programmatic access.

    **Important**: The full API key is only shown once during creation.
    Store it securely - you won't be able to retrieve it again.
    """
    full_key, key_hash, key_prefix = generate_api_key()

    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)

    api_key = APIKey(
        user_id=current_user.id,
        key_name=key_data.key_name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        is_active=True,
        expires_at=expires_at,
        scopes=json.dumps(key_data.scopes),
    )

    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return APIKeyResponse(
        id=api_key.id,
        key_name=api_key.key_name,
        key_prefix=api_key.key_prefix,
        api_key=full_key,  # Only shown during creation
        is_active=api_key.is_active,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        last_used=api_key.last_used,
        scopes=json.loads(api_key.scopes),
    )


@router.get("/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    List all API keys for the current user.

    Note: Full API keys are never returned, only prefixes.
    """
    api_keys = db.query(APIKey).filter(APIKey.user_id == current_user.id).all()

    return [
        APIKeyResponse(
            id=key.id,
            key_name=key.key_name,
            key_prefix=key.key_prefix,
            api_key=None,  # Never return full key
            is_active=key.is_active,
            expires_at=key.expires_at,
            created_at=key.created_at,
            last_used=key.last_used,
            scopes=json.loads(key.scopes) if key.scopes else [],
        )
        for key in api_keys
    ]


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete (revoke) an API key.

    The key will be immediately deactivated and cannot be used.
    """
    api_key = (
        db.query(APIKey)
        .filter(APIKey.id == key_id, APIKey.user_id == current_user.id)
        .first()
    )

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    db.delete(api_key)
    db.commit()

    return {"message": "API key deleted successfully"}
