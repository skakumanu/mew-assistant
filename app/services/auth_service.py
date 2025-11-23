"""Authentication Service"""
from app.utils.auth import create_access_token, get_password_hash, verify_password
from app.database.models import User
from sqlalchemy.orm import Session

class AuthService:
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        """Authenticate user and return token"""
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            return None
        return create_access_token(data={"sub": user.email, "user_id": user.id})
    
    @staticmethod
    def create_user(db: Session, email: str, password: str, full_name: str, role: str = "parent"):
        """Create a new user"""
        hashed_password = get_password_hash(password)
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
