"""
Database connection and session management for PostgreSQL.
Handles connection pooling and session lifecycle.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Database URL from environment variable
# Format: postgresql://user:password@host:port/database
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://mew_user:mew_password@localhost:5432/mew_assistant"
)

# Fly Postgres (and Heroku, and others) hand out DATABASE_URL with the
# postgres:// scheme, which SQLAlchemy 1.4+ no longer recognizes as a
# dialect - it needs postgresql://. Normalize rather than requiring every
# deployment target to hand-edit the secret to match.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine with connection pooling
# For SQLite, use different settings
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Needed for SQLite
        echo=False,  # Set to True for SQL query debugging
    )
else:
    # Azure PostgreSQL requires SSL
    connect_args = {}
    # Check for Azure PostgreSQL using proper URL parsing to avoid substring bypass
    try:
        from urllib.parse import urlparse
        parsed_url = urlparse(DATABASE_URL)
        # Check if hostname ends with Azure PostgreSQL domain
        if parsed_url.hostname and parsed_url.hostname.endswith(".postgres.database.azure.com"):
            connect_args = {"sslmode": "require"}
    except Exception:
        # Fallback to substring check if URL parsing fails
        if "postgres.database.azure.com" in DATABASE_URL:
            connect_args = {"sslmode": "require"}

    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # Verify connections before using them
        echo=False,  # Set to True for SQL query debugging
        connect_args=connect_args,
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


def get_db():
    """
    Dependency to get database session.
    Usage in FastAPI endpoints: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """Initialize database tables"""
    import logging

    logger = logging.getLogger(__name__)

    try:
        from .models import Base as ModelsBase

        # To avoid races when multiple processes/containers try to create the
        # schema concurrently (which can cause duplicate CREATE TYPE errors in
        # PostgreSQL), acquire a PostgreSQL advisory lock before running
        # `create_all`. The lock is a no-op for SQLite.
        if not DATABASE_URL.startswith("sqlite"):
            try:
                with engine.connect() as conn:
                    # Use a stable advisory lock key. Use pg_try_advisory_lock
                    # to avoid blocking CI indefinitely; if lock not available,
                    # wait a short time and retry a few times.
                    acquired = False
                    import time

                    for _ in range(5):
                        res = conn.execute(
                            text("SELECT pg_try_advisory_lock(436901387)")
                        ).scalar()
                        if res:
                            acquired = True
                            break
                        time.sleep(1)

                    if not acquired:
                        logger.warning("Could not acquire advisory lock; proceeding without lock")
                    else:
                        try:
                            ModelsBase.metadata.create_all(bind=engine)
                        finally:
                            conn.execute(text("SELECT pg_advisory_unlock(436901387)"))
                        logger.info("Database tables created successfully (with advisory lock)")
            except Exception as ex:
                logger.warning(f"Schema initialization attempt failed: {ex}")
                logger.info("Database tables will be created when connection is available.")
        else:
            # SQLite or other file-based DBs: run create_all directly
            ModelsBase.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully (sqlite)")
    except Exception as e:
        logger.warning(f"Could not initialize database: {e}")
        logger.info("Database tables will be created when connection is available.")


def verify_schema() -> None:
    """
    Raise if init_db() did not actually create the schema.

    init_db() deliberately swallows its own exceptions so a container that
    boots before the database is reachable doesn't crash forever - but that
    tolerance is exactly what let a real bug (SQLAlchemy 2.0 rejecting a raw
    SQL string) ship a build that silently ran with zero tables for as long
    as nobody happened to hit an endpoint that queried them. This is the
    other half of that tradeoff: once init_db() has had its attempt, the
    core schema must actually exist, or the app should fail to start rather
    than serve traffic against a database it never initialized.
    """
    from sqlalchemy import inspect

    if "users" not in inspect(engine).get_table_names():
        raise RuntimeError(
            "Database schema is not initialized (no 'users' table found) - "
            "init_db() ran but did not create the schema. Check the logs "
            "above for 'Schema initialization attempt failed' or "
            "'Could not initialize database'."
        )
