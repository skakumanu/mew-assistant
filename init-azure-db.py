#!/usr/bin/env python3
"""Initialize Azure PostgreSQL database with correct credentials."""
import psycopg2
import sys

# Azure PostgreSQL settings
DB_HOST = "mew-db-dev.postgres.database.azure.com"
DB_USER = "mewadmin"
DB_PASSWORD = "MewDev2024SecurePass"
DB_NAME = "mew_db"

try:
    print(f"Connecting to {DB_HOST}...")
    conn = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database="postgres",  # Connect to default DB first
        sslmode="require"
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Create database if it doesn't exist
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    if not cursor.fetchone():
        print(f"Creating database {DB_NAME}...")
        cursor.execute(f"CREATE DATABASE {DB_NAME}")
        print("✅ Database created")
    else:
        print(f"✅ Database {DB_NAME} already exists")
    
    cursor.close()
    conn.close()
    
    print("✅ Database initialization complete!")
    sys.exit(0)
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
