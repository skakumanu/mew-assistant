#!/usr/bin/env python3
"""
Setup script for RBAC users
Cleans existing users and creates superuser, admin, and regular user accounts

SECURITY NOTE: This script is for initial setup/testing only.
Passwords should be changed immediately after first login.
For production, use environment variables or secure password prompts.
"""
import sys
import os
import secrets
import string
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import User, Base
from app.utils.auth import get_password_hash
from app.utils.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_secure_password(length=16):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def setup_rbac_users():
    """Clean database and create RBAC users"""
    
    # Get passwords from environment or generate secure ones
    superuser_password = os.getenv('SUPERUSER_PASSWORD') or generate_secure_password()
    admin_password = os.getenv('ADMIN_PASSWORD') or generate_secure_password()
    parent_password = os.getenv('PARENT_PASSWORD') or generate_secure_password()
    
    # Connect to database
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Delete all existing users
        logger.info("Deleting all existing users...")
        deleted_count = db.query(User).delete()
        db.commit()
        logger.info(f"Deleted {deleted_count} users")
        
        # Create superuser
        superuser = User(
            email="super@mew-assistant.org",
            username="superuser",
            hashed_password=get_password_hash(superuser_password),
            full_name="System Superuser",
            role="SUPERUSER",
            is_active=True,
            email_verified=True
        )
        db.add(superuser)
        logger.info("Created superuser: super@mew-assistant.org")
        
        # Create admin user
        admin = User(
            email="admin@mew-assistant.org",
            username="admin",
            hashed_password=get_password_hash(admin_password),
            full_name="System Administrator",
            role="ADMIN",
            is_active=True,
            email_verified=True
        )
        db.add(admin)
        logger.info("Created admin: admin@mew-assistant.org")
        
        # Create your parent account
        parent = User(
            email="skakumanu@gmail.com",
            username="skakumanu",
            hashed_password=get_password_hash(parent_password),
            full_name="Srinivasa Kakumanu",
            role="PARENT",
            is_active=True,
            email_verified=True,
            phone="+1234567890"
        )
        db.add(parent)
        logger.info("Created parent: skakumanu@gmail.com")
        
        # Commit all users
        db.commit()
        
        logger.info("\n" + "="*60)
        logger.info("RBAC Users Created Successfully!")
        logger.info("="*60)
        logger.info("\nGenerated Passwords (SAVE THESE):")
        logger.info(f"Superuser (super@mew-assistant.org): {superuser_password}")
        logger.info(f"Admin (admin@mew-assistant.org): {admin_password}")
        logger.info(f"Parent (skakumanu@gmail.com): {parent_password}")
        logger.info("RBAC Users Created Successfully!")
        logger.info("="*60)
        logger.info("\nCredentials:")
        logger.info("-" * 60)
        logger.info("Superuser:")
        logger.info("  Email: super@mew-assistant.org")
        logger.info("  Password: SuperSecure123!")
        logger.info("")
        logger.info("Admin:")
        logger.info("  Email: admin@mew-assistant.org")
        logger.info("  Password: AdminSecure123!")
        logger.info("")
        logger.info("Parent (Your Account):")
        logger.info("  Email: skakumanu@gmail.com")
        logger.info("  Password: Parent@Mew2024")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error setting up RBAC users: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    setup_rbac_users()
