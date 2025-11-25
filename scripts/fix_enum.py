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

conn = None
try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Check if 'parent' exists in userrole enum
    cur.execute("""
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'parent' 
        AND enumtypid = 'userrole'::regtype
    """)
    exists = cur.fetchone()
    
    if not exists:
        # ALTER TYPE must be run outside a transaction block
        conn.commit()
        cur.execute("ALTER TYPE userrole ADD VALUE 'parent';")
        print("✅ Added 'parent' to userrole enum")
    else:
        print("ℹ️ 'parent' already exists in userrole enum")
    
    conn.commit()
    print("✅ Database enum fixed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
finally:
    if conn:
        conn.close()