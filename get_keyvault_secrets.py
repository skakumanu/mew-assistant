#!/usr/bin/env python3
"""Retrieve OAuth secrets from Azure Key Vault"""

import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

# Key Vault configuration
KEYVAULT_NAME = "mew-assistant-kv-dev"
KEYVAULT_URL = f"https://{KEYVAULT_NAME}.vault.azure.net/"

def get_secret(secret_name):
    """Retrieve a secret from Azure Key Vault"""
    try:
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=KEYVAULT_URL, credential=credential)
        secret = client.get_secret(secret_name)
        return secret.value
    except Exception as e:
        print(f"Error retrieving {secret_name}: {e}")
        return None

if __name__ == "__main__":
    print("Retrieving OAuth credentials from Azure Key Vault...")
    print(f"Key Vault: {KEYVAULT_URL}")
    print()
    
    # Get Google credentials
    google_client_id = get_secret("google-client-id")
    google_client_secret = get_secret("google-client-secret")
    
    # Get Microsoft credentials
    microsoft_client_id = get_secret("microsoft-client-id")
    microsoft_client_secret = get_secret("microsoft-client-secret")
    
    # Display results
    if google_client_id:
        print(f"✅ Google Client ID: {google_client_id}")
    if google_client_secret:
        print(f"✅ Google Client Secret: {google_client_secret[:10]}...{google_client_secret[-10:]}")
        print()
        print("To update .env file:")
        print(f"GOOGLE_CLIENT_ID={google_client_id}")
        print(f"GOOGLE_CLIENT_SECRET={google_client_secret}")
    
    if microsoft_client_id:
        print()
        print(f"✅ Microsoft Client ID: {microsoft_client_id}")
    if microsoft_client_secret:
        print(f"✅ Microsoft Client Secret: {microsoft_client_secret[:10]}...{microsoft_client_secret[-10:]}")
