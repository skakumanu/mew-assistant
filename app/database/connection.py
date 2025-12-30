"""
Database connection and session management for PostgreSQL.
Handles connection pooling and session lifecycle.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Database URL from environment variable
# Format: postgresql://user:password@host:port/database
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://mew_user:mew_password@localhost:5432/mew_assistant"
)

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
    if "azure" in DATABASE_URL or "postgres.database.azure.com" in DATABASE_URL:
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
                        res = conn.execute("SELECT pg_try_advisory_lock(436901387)").scalar()
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
                            conn.execute("SELECT pg_advisory_unlock(436901387)")
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
