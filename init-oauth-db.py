#!/usr/bin/env python3
"""
Initialize database with OAuth token columns
Run this once to add missing columns to federated_identities table
"""

import os
import sys

import psycopg2


def run_migration():
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    print("🔧 Running OAuth token migration...")

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'federated_identities'
            AND column_name IN ('access_token', 'refresh_token', 'token_expires_at');
        """
        )

        existing_columns = [row[0] for row in cursor.fetchall()]

        if len(existing_columns) == 3:
            print("✅ OAuth token columns already exist, skipping migration")
            return

        print(
            f"📝 Adding missing columns: {set(['access_token', 'refresh_token', 'token_expires_at']) - set(existing_columns)}"
        )

        # Add columns if they don't exist
        cursor.execute(
            """
            ALTER TABLE federated_identities
            ADD COLUMN IF NOT EXISTS access_token TEXT,
            ADD COLUMN IF NOT EXISTS refresh_token TEXT,
            ADD COLUMN IF NOT EXISTS token_expires_at TIMESTAMP;
        """
        )

        print("✅ OAuth token columns added successfully!")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_migration()
