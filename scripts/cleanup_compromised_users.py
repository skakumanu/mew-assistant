#!/usr/bin/env python3
"""
Database Cleanup Script - Remove users created with compromised passwords

SECURITY: This script removes users that were created with hardcoded passwords
that were exposed in git history. OAuth federated users will be preserved.

Date: December 11, 2025
Incident: SECURITY_INCIDENT.md
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import FederatedIdentity, User
from app.utils.config import settings
from app.utils.log_sanitizer import sanitize_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Email addresses of users created with compromised passwords
COMPROMISED_USERS = [
    "super@mew-assistant.org",  # SuperSecure123!
    "admin@mew-assistant.org",  # AdminSecure123!
]

# Email addresses to PRESERVE (OAuth users)
PRESERVE_USERS = [
    "skakumanu@gmail.com",  # OAuth Google
    "skakumanu@hotmail.com",  # OAuth Microsoft
]


def list_all_users(db):
    """List all users in database with their auth type"""
    logger.info("\n" + "=" * 70)
    logger.info("Current Users in Database:")
    logger.info("=" * 70)

    users = db.query(User).all()

    for user in users:
        # Check if user has OAuth federated identity
        has_oauth = (
            db.query(FederatedIdentity)
            .filter(FederatedIdentity.user_id == user.id)
            .first()
            is not None
        )

        auth_type = "OAuth" if has_oauth else "Password"
        status = "✅ KEEP" if has_oauth or user.email in PRESERVE_USERS else "⚠️  REMOVE"

        logger.info(
            f"{status} | {sanitize_email(user.email):40s} | {user.role:10s} | {auth_type}"
        )

    logger.info("=" * 70)
    return users


def cleanup_compromised_users(db, dry_run=True):
    """
    Remove users created with compromised passwords

    Args:
        db: Database session
        dry_run: If True, only show what would be deleted (default)
    """

    mode = "DRY RUN" if dry_run else "LIVE MODE"
    logger.info(f"\n{'='*70}")
    logger.info(f"Database Cleanup - {mode}")
    logger.info(f"{'='*70}")

    # List all users first
    list_all_users(db)

    logger.info("\nAnalyzing users to remove...")
    logger.info("-" * 70)

    users_to_remove = []
    users_to_keep = []

    for email in COMPROMISED_USERS:
        user = db.query(User).filter(User.email == email).first()
        if user:
            # Check if user has OAuth (should keep if they do)
            has_oauth = (
                db.query(FederatedIdentity)
                .filter(FederatedIdentity.user_id == user.id)
                .first()
                is not None
            )

            if has_oauth:
                logger.warning(f"⚠️  {sanitize_email(email)} has OAuth - will KEEP")
                users_to_keep.append(user)
            else:
                logger.info(
                    f"🗑️  {sanitize_email(email)} - password-based - will REMOVE"
                )
                users_to_remove.append(user)
        else:
            logger.info(f"ℹ️  {sanitize_email(email)} - not found in database")

    # Also check for other password-based users
    logger.info("\nChecking for other password-based users...")
    all_users = db.query(User).all()
    for user in all_users:
        if user.email not in COMPROMISED_USERS and user.email not in PRESERVE_USERS:
            has_oauth = (
                db.query(FederatedIdentity)
                .filter(FederatedIdentity.user_id == user.id)
                .first()
                is not None
            )

            if not has_oauth:
                logger.warning(
                    f"⚠️  Found unlisted password user: {sanitize_email(user.email)}"
                )
                # Don't auto-remove, just warn

    logger.info("\n" + "=" * 70)
    logger.info(
        f"Summary: {len(users_to_remove)} users to remove, {len(users_to_keep)} to keep"
    )
    logger.info("=" * 70)

    if not users_to_remove:
        logger.info("✅ No compromised password-based users found. Database is clean!")
        return

    if dry_run:
        logger.info("\n⚠️  DRY RUN MODE - No actual changes will be made")
        logger.info("Run with --live flag to actually delete users")
        return

    # Actual deletion (only if not dry_run)
    logger.info("\n🔴 LIVE MODE - Deleting users...")

    for user in users_to_remove:
        try:
            logger.info(f"Deleting user: {sanitize_email(user.email)} (ID: {user.id})")

            # Delete associated federated identities first (if any)
            db.query(FederatedIdentity).filter(
                FederatedIdentity.user_id == user.id
            ).delete()

            # Delete the user
            db.delete(user)

            logger.info(f"✅ Deleted: {sanitize_email(user.email)}")
        except Exception as e:
            logger.error(f"❌ Error deleting {sanitize_email(user.email)}: {e}")
            raise

    db.commit()
    logger.info("\n✅ Database cleanup completed successfully!")

    # Show remaining users
    logger.info("\nRemaining users after cleanup:")
    list_all_users(db)


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Clean up compromised password users")
    parser.add_argument(
        "--live", action="store_true", help="Actually delete users (default is dry-run)"
    )
    args = parser.parse_args()

    # Connect to database
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        cleanup_compromised_users(db, dry_run=not args.live)
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        db.rollback()
        raise
    finally:
        db.close()

    logger.info("\n" + "=" * 70)
    logger.info("Script completed!")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
