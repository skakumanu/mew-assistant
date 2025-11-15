"""
Azure Blob Storage Integration - Handles encrypted backups
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional, List
from app.utils.logging import get_logger
from app.cloud.encryption import EncryptionService

logger = get_logger(__name__)


class AzureStorageClient:
    """Manages encrypted backups in Azure Blob Storage"""
    
    def __init__(self):
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER", "mew-backups")
        
        if not connection_string:
            logger.warning("AZURE_STORAGE_CONNECTION_STRING not set, cloud backups disabled")
            self.client = None
            return
        
        try:
            from azure.storage.blob import BlobServiceClient
            from azure.core.exceptions import ResourceNotFoundError
            
            self.client = BlobServiceClient.from_connection_string(connection_string)
            self.ResourceNotFoundError = ResourceNotFoundError
            self._ensure_container_exists()
            logger.info(f"Connected to Azure Blob Storage, container: {self.container_name}")
        except ImportError:
            logger.warning("Azure SDK not installed, cloud backups disabled")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to connect to Azure Storage: {e}")
            self.client = None
        
        self.encryption = EncryptionService()
    
    def _ensure_container_exists(self):
        try:
            container_client = self.client.get_container_client(self.container_name)
            container_client.get_container_properties()
        except self.ResourceNotFoundError:
            self.client.create_container(self.container_name)
            logger.info(f"Created container: {self.container_name}")
    
    def backup_database(self, db_path: str, backup_name: Optional[str] = None) -> bool:
        if not self.client or not os.path.exists(db_path):
            return False
        
        try:
            with open(db_path, 'rb') as f:
                db_data = f.read()
            
            encrypted_data = self.encryption.encrypt_bytes(db_data)
            
            if not backup_name:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}.db.enc"
            
            blob_client = self.client.get_blob_client(
                container=self.container_name, blob=backup_name
            )
            blob_client.upload_blob(encrypted_data, overwrite=True)
            
            metadata = {
                'timestamp': datetime.utcnow().isoformat(),
                'original_size': str(len(db_data)),
                'encrypted_size': str(len(encrypted_data))
            }
            blob_client.set_blob_metadata(metadata)
            
            logger.info(f"Database backed up successfully: {backup_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return False
    
    def restore_database(self, backup_name: str, restore_path: str) -> bool:
        if not self.client:
            return False
        
        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name, blob=backup_name
            )
            encrypted_data = blob_client.download_blob().readall()
            decrypted_data = self.encryption.decrypt_bytes(encrypted_data)
            
            with open(restore_path, 'wb') as f:
                f.write(decrypted_data)
            
            logger.info(f"Database restored from: {backup_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            return False
    
    def list_backups(self) -> List[dict]:
        if not self.client:
            return []
        
        try:
            container_client = self.client.get_container_client(self.container_name)
            blobs = container_client.list_blobs()
            
            return [{
                'name': blob.name,
                'size': blob.size,
                'created': blob.creation_time.isoformat(),
                'modified': blob.last_modified.isoformat(),
                'metadata': blob.metadata
            } for blob in blobs]
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []
    
    def delete_old_backups(self, days: int = 30) -> int:
        if not self.client:
            return 0
        
        try:
            container_client = self.client.get_container_client(self.container_name)
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted_count = 0
            
            for blob in container_client.list_blobs():
                if blob.last_modified < cutoff_date:
                    blob_client = self.client.get_blob_client(
                        container=self.container_name, blob=blob.name
                    )
                    blob_client.delete_blob()
                    deleted_count += 1
            
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to delete old backups: {e}")
            return 0
    
    def backup_user_data(self, user_id: int, data: dict) -> bool:
        if not self.client:
            return False
        
        try:
            json_data = json.dumps(data, indent=2).encode('utf-8')
            encrypted_data = self.encryption.encrypt_bytes(json_data)
            
            blob_name = f"user_data/{user_id}/export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json.enc"
            blob_client = self.client.get_blob_client(
                container=self.container_name, blob=blob_name
            )
            blob_client.upload_blob(encrypted_data, overwrite=True)
            
            logger.info(f"User data backed up: {blob_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup user data: {e}")
            return False


azure_storage = AzureStorageClient()
