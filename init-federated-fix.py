from sqlalchemy import create_engine, text
import os

db_url = f"postgresql://mewadmin:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:5432/mew_db?sslmode=require"
engine = create_engine(db_url)

with engine.connect() as conn:
    conn.execute(text("""
        ALTER TABLE federated_identities ALTER COLUMN id SET DEFAULT nextval('federated_identities_id_seq');
    """))
    conn.commit()
    print("✅ Fixed federated_identities table")
