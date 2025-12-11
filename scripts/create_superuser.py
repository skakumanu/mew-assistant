#!/usr/bin/env python3
"""
Create superuser and admin accounts

SECURITY WARNING: This script contains default passwords for initial setup.
These should be changed immediately after first login.
For production use, set SUPERUSER_PASSWORD and ADMIN_PASSWORD environment variables.
"""
import sys
import os
import secrets
import string
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import SessionLocal
from app.database.models import User
from app.utils.auth import get_password_hash
from datetime import datetime

def generate_secure_password(length=16):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def create_admin_users():
    db = SessionLocal()
    
    # Get passwords from environment or generate secure ones
    superuser_password = os.getenv('SUPERUSER_PASSWORD') or generate_secure_password()
    admin_password = os.getenv('ADMIN_PASSWORD') or generate_secure_password()
    
    passwords_to_show = []
    
    try:
        # Create superuser
        superuser = db.query(User).filter(User.email == "skakumanu@gmail.com").first()
        if not superuser:
            superuser = User(
                email="skakumanu@gmail.com",
                username="skakumanu_gmail",
                hashed_password=get_password_hash(superuser_password),
                full_name="Srinivasa Kakumanu",
                role="SUPERUSER",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(superuser)
            print("✓ Created superuser: skakumanu@gmail.com")
            passwords_to_show.append(("skakumanu@gmail.com (SUPERUSER)", superuser_password))
        else:
            superuser.role = "SUPERUSER"
            print("✓ Updated to superuser: skakumanu@gmail.com")
        
        # Create admin user
        admin = db.query(User).filter(User.email == "skakumanu@hotmail.com").first()
        if not admin:
            admin = User(
                email="skakumanu@hotmail.com",
                username="skakumanu_hotmail",
                hashed_password=get_password_hash(admin_password),
                full_name="Srinivasa Kakumanu (Admin)",
                role="ADMIN",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(admin)
            print("✓ Created admin: skakumanu@hotmail.com")
            passwords_to_show.append(("skakumanu@hotmail.com (ADMIN)", admin_password))
        else:
            admin.role = "ADMIN"
            print("✓ Updated to admin: skakumanu@hotmail.com")
        
        db.commit()
        print("\n✓ All admin accounts created/updated successfully!")
        
        # Show generated passwords
        if passwords_to_show:
            print("\n" + "="*60)
            print("IMPORTANT: Save these generated passwords!")
            print("="*60)
            for email, password in passwords_to_show:
                print(f"{email}: {password}")
            print("="*60)
            print("\nFor production, set environment variables:")
            print("export SUPERUSER_PASSWORD='your-secure-password'")
            print("export ADMIN_PASSWORD='your-secure-password'")
            print("="*60)
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
