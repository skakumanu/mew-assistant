#!/usr/bin/env python3
"""Create superuser and admin accounts"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import SessionLocal
from app.database.models import User
from app.utils.auth import get_password_hash
from datetime import datetime

def create_admin_users():
    db = SessionLocal()
    try:
        # Create superuser
        superuser = db.query(User).filter(User.email == "skakumanu@gmail.com").first()
        if not superuser:
            superuser = User(
                email="skakumanu@gmail.com",
                username="skakumanu_gmail",
                hashed_password=get_password_hash("Mew@Super2024!"),
                full_name="Srinivasa Kakumanu",
                role="SUPERUSER",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(superuser)
            print("✓ Created superuser: skakumanu@gmail.com")
        else:
            superuser.role = "SUPERUSER"
            print("✓ Updated to superuser: skakumanu@gmail.com")
        
        # Create admin user
        admin = db.query(User).filter(User.email == "skakumanu@hotmail.com").first()
        if not admin:
            admin = User(
                email="skakumanu@hotmail.com",
                username="skakumanu_hotmail",
                hashed_password=get_password_hash("Mew@Admin2024!"),
                full_name="Srinivasa Kakumanu (Admin)",
                role="ADMIN",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(admin)
            print("✓ Created admin: skakumanu@hotmail.com")
        else:
            admin.role = "ADMIN"
            print("✓ Updated to admin: skakumanu@hotmail.com")
        
        db.commit()
        
        print("\n=== Admin Credentials ===")
        print(f"Superuser: skakumanu@gmail.com / Mew@Super2024!")
        print(f"Admin: skakumanu@hotmail.com / Mew@Admin2024!")
        print("\nPlease change these passwords after first login!")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_users()
