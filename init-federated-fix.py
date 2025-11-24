import os
import psycopg2
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

# Get password from Key Vault
credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://mew-assistant-kv-dev.vault.azure.net/", credential=credential)
db_password = client.get_secret("DB-PASSWORD").value

# Connect to database
conn = psycopg2.connect(
    host="mew-db-dev.postgres.database.azure.com",
    database="mew_db",
    user="mewadmin",
    password=db_password,
    sslmode="require"
)
conn.autocommit = True
cursor = conn.cursor()

# Read and execute SQL
with open('fix_federated_id.sql', 'r') as f:
    sql = f.read()
    cursor.execute(sql)

print("Successfully fixed federated_identities table!")
cursor.close()
conn.close()
