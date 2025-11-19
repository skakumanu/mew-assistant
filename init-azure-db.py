#!/usr/bin/env python3
"""
Initialize Azure PostgreSQL database with tables
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Azure PostgreSQL connection
DATABASE_URL = "postgresql://mewadmin:HlfXcZoloKm5wp4I@mew-db-dev.postgres.database.azure.com:5432/mew_db?sslmode=require"

def init_database():
    """Initialize database tables"""
    print("Connecting to Azure PostgreSQL...")
    try:
        engine = create_engine(DATABASE_URL, echo=True)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ Connected to PostgreSQL: {version}")
        
        # Import models to trigger table creation
        sys.path.insert(0, '/home/srinu/mew-assistant')
        from app.database.models import Base
        
        print("\nCreating database tables...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database initialized successfully!")
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema='public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"\n📋 Created tables: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
