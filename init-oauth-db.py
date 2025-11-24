"""
Initialize database schema for OAuth users.
Run this script to update the database to support OAuth authentication.
"""
import os
import sys
from sqlalchemy import create_engine, text

def main():
    # Get database URL from environment
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    # Convert asyncpg to psycopg2 for sync operations
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    try:
        engine = create_engine(db_url)
        with engine.begin() as conn:
            # Make hashed_password nullable for OAuth users
            conn.execute(text("ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL"))
            print("✓ Database schema updated successfully")
            print("✓ hashed_password column is now nullable for OAuth users")
    except Exception as e:
        print(f"✗ Error updating database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
