"""
Encryption Service for Data at Rest - Uses Fernet symmetric encryption (AES-128)
"""

import os

from cryptography.fernet import Fernet

from app.utils.logging import get_logger

logger = get_logger(__name__)


class EncryptionService:
    """Handles encryption/decryption of data at rest"""

    def __init__(self):
        try:
            from app.cloud.azure_key_vault import key_vault_client

            encryption_key = key_vault_client.get_secret("ENCRYPTION_KEY")
        except:
            encryption_key = None

        if not encryption_key:
            encryption_key = os.getenv("ENCRYPTION_KEY")
            if not encryption_key:
                logger.warning("No encryption key found, generating new key")
                encryption_key = Fernet.generate_key().decode()
                logger.info("Store this key in Azure Key Vault or .env: ENCRYPTION_KEY")

        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()

        try:
            self.cipher = Fernet(encryption_key)
        except (ValueError, Exception) as e:
            logger.error(f"Invalid encryption key format: {e}. Generating new key...")
            encryption_key = Fernet.generate_key()
            self.cipher = Fernet(encryption_key)
            logger.warning(
                f"Generated new encryption key. Store this in production: {encryption_key.decode()}"
            )

    def encrypt_bytes(self, data: bytes) -> bytes:
        return self.cipher.encrypt(data)

    def decrypt_bytes(self, encrypted_data: bytes) -> bytes:
        return self.cipher.decrypt(encrypted_data)

    def encrypt_string(self, text: str) -> str:
        encrypted = self.cipher.encrypt(text.encode())
        return encrypted.decode()

    def decrypt_string(self, encrypted_text: str) -> str:
        decrypted = self.cipher.decrypt(encrypted_text.encode())
        return decrypted.decode()

    @staticmethod
    def generate_key() -> str:
        return Fernet.generate_key().decode()


encryption_service = EncryptionService()
