#!/usr/bin/env python3
"""Fix database enum types"""
import os
import sys
import psycopg2

# Get database URL from environment
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Add 'parent' to userrole enum if it doesn't exist
    cur.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'parent' AND enumtypid = 'userrole'::regtype) THEN
                ALTER TYPE userrole ADD VALUE 'parent';
                RAISE NOTICE 'Added parent to userrole enum';
            ELSE
                RAISE NOTICE 'parent already exists in userrole enum';
            END IF;
        END $$;
    """)
    
    conn.commit()
    print("✅ Database enum fixed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
finally:
    if conn:
        conn.close()
