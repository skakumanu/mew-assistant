from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User
from app.utils.auth import get_password_hash

router = APIRouter(prefix="/auth", tags=["Authentication"])


class PasswordResetRequest(BaseModel):
    email: EmailStr
    new_password: str


@router.post("/reset-password")
async def reset_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Reset user password (for admin/development use)"""
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.hashed_password = get_password_hash(request.new_password)
    db.commit()

    return {"message": "Password reset successfully", "email": request.email}
