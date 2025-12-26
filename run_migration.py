import os
import sys

import psycopg2

# Get database URL from environment or Azure
db_url = os.getenv("DATABASE_URL", "")

if not db_url:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

print(f"Connecting to database...")

try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    print("Running migration...")

    # Add OAuth token columns
    cursor.execute(
        """
        ALTER TABLE federated_identities 
        ADD COLUMN IF NOT EXISTS access_token TEXT,
        ADD COLUMN IF NOT EXISTS refresh_token TEXT,
        ADD COLUMN IF NOT EXISTS token_expires_at TIMESTAMP;
    """
    )

    conn.commit()
    print("✓ Migration completed successfully!")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
