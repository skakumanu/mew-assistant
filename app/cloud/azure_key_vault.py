"""
Azure Key Vault Integration
Securely stores and retrieves secrets, API keys, and credentials
"""
import os
from typing import Optional
from app.utils.logging import get_logger

logger = get_logger(__name__)


class AzureKeyVaultClient:
    """Manages secrets in Azure Key Vault"""
    
    def __init__(self):
        vault_url = os.getenv("AZURE_KEY_VAULT_URL")
        if not vault_url:
            logger.warning("AZURE_KEY_VAULT_URL not set, using local .env fallback")
            self.client = None
            return
        
        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient
            
            credential = DefaultAzureCredential()
            self.client = SecretClient(vault_url=vault_url, credential=credential)
            logger.info(f"Connected to Azure Key Vault: {vault_url}")
        except ImportError:
            logger.warning("Azure SDK not installed, using local .env fallback")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to connect to Key Vault: {e}")
            self.client = None
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """Retrieve a secret from Key Vault, falls back to environment variables"""
        if self.client:
            try:
                secret = self.client.get_secret(secret_name)
                return secret.value
            except Exception as e:
                logger.warning(f"Failed to get secret {secret_name} from Key Vault: {e}")
        return os.getenv(secret_name)
    
    def set_secret(self, secret_name: str, secret_value: str) -> bool:
        """Store a secret in Key Vault"""
        if not self.client:
            logger.warning("Key Vault not available, cannot store secret")
            return False
        try:
            self.client.set_secret(secret_name, secret_value)
            logger.info(f"Secret {secret_name} stored successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to store secret {secret_name}: {e}")
            return False


key_vault_client = AzureKeyVaultClient()
