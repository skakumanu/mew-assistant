"""
Authentication router for Mew Assistant.
Handles user registration, login, token refresh, and profile management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.connection import get_db
from app.database.models import User
from app.schemas.auth import (
    UserCreate, UserResponse, UserUpdate,
    LoginRequest, LoginResponse, Token,
    RefreshTokenRequest, PasswordChange
)
from app.utils.auth import (
    get_password_hash, authenticate_user,
    create_access_token, create_refresh_token, decode_token,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    Creates a new user with hashed password. Email must be unique.
    Username is auto-generated from email if not provided.
    
    **Example Request:**
    ```json
    {
        "email": "parent@example.com",
        "password": "SecureP@ssw0rd",
        "full_name": "John Doe",
        "role": "parent"
    }
    ```
    """
    # Auto-generate username from email if not provided
    username = user_data.username
    if not username:
        username = user_data.email.split('@')[0]
        # Ensure uniqueness by appending number if needed
        base_username = username
        counter = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}{counter}"
            counter += 1
    
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == username)
    ).first()
    
    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Create new user
    db_user = User(
        email=user_data.email,
        username=username,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        phone=user_data.phone,
        timezone=user_data.timezone,
        is_active=True,
        is_superuser=False
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return access tokens.
    
    Returns both access token (30 min) and refresh token (7 days).
    
    **Example Request:**
    ```json
    {
        "email": "parent@example.com",
        "password": "SecureP@ssw0rd"
    }
    ```
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
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user
    }


@router.post("/login/form", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible login endpoint.
    
    This endpoint is compatible with OAuth2PasswordBearer and can be used
    with FastAPI's automatic interactive docs authentication.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    **Example Request:**
    ```json
    {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
    """
    try:
        payload = decode_token(refresh_data.refresh_token)
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Verify user exists and is active
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token = create_access_token(data={"sub": email})
    new_refresh_token = create_refresh_token(data={"sub": email})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's profile.
    
    Requires valid JWT token in Authorization header:
    ```
    Authorization: Bearer <access_token>
    ```
    """
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.
    
    **Example Request:**
    ```json
    {
        "full_name": "John Smith",
        "phone": "+1234567890",
        "timezone": "America/Los_Angeles"
    }
    ```
    """
    # Update only provided fields
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
    db: Session = Depends(get_db)
):
    """
    Change user password.
    
    Requires current password for verification.
    
    **Example Request:**
    ```json
    {
        "current_password": "OldP@ssw0rd",
        "new_password": "NewSecureP@ssw0rd123"
    }
    ```
    """
    from app.utils.auth import verify_password
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user.
    
    Note: JWT tokens are stateless, so this is just a placeholder.
    Clients should delete their stored tokens.
    """
    return {"message": "Logged out successfully. Please delete your tokens on the client side."}

# CAPTCHA endpoints for bot protection
from app.middleware.bot_protection import captcha_verifier

@router.get("/captcha/challenge")
async def get_captcha_challenge(user_id: str = None):
    """Generate a CAPTCHA challenge for critical operations"""
    challenge = captcha_verifier.generate_challenge(user_id or "anonymous")
    return challenge

@router.post("/captcha/verify")
async def verify_captcha(challenge_id: str, response: str):
    """Verify CAPTCHA response"""
    is_valid = captcha_verifier.verify_response(challenge_id, response)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired CAPTCHA"
        )
    return {"verified": True}
