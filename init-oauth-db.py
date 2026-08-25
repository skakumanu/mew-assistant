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

    # Skip migration for SQLite (development databases)
    if db_url.startswith("sqlite"):
        print("✅ SQLite database detected, skipping OAuth token migration")
        return

    print("🔧 Running OAuth token migration...")

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()

        # On a brand-new database, federated_identities doesn't exist yet at
        # all - the app's own startup (init_db() in app/main.py) creates it
        # fresh, already with these columns, right after this script exits.
        # That's not an error state; it's the normal first-deploy path.
        cursor.execute(
            """
            SELECT to_regclass('public.federated_identities');
        """
        )
        if cursor.fetchone()[0] is None:
            print("✅ federated_identities doesn't exist yet (fresh database), skipping migration")
            cursor.close()
            conn.close()
            return

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

    except psycopg2.OperationalError as e:
        # Connection error - database might not be ready yet, but app will continue
        print(f"⚠️  Could not connect to database for migration: {e}")
        print("ℹ️  Database will be initialized when it becomes available")
        # Exit with 0 so container startup doesn't fail
        return
    except Exception as e:
        # Other errors still fail (SQL syntax, etc.)
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_migration()
