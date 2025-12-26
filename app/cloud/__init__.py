"""
Azure Cloud Infrastructure Module
Handles Azure Key Vault, Storage, and scalability features
"""

from .azure_key_vault import AzureKeyVaultClient
from .azure_storage import AzureStorageClient
from .encryption import EncryptionService

__all__ = ["AzureKeyVaultClient", "AzureStorageClient", "EncryptionService"]
