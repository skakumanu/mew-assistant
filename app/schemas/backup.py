"""
Backup and Restore Schemas
"""
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime


class BackupResponse(BaseModel):
    success: bool
    message: str
    backup_name: str
    timestamp: datetime


class BackupInfo(BaseModel):
    name: str
    size: int
    created: str
    modified: str
    metadata: Optional[Dict] = None


class BackupListResponse(BaseModel):
    success: bool
    count: int
    backups: List[BackupInfo]


class RestoreRequest(BaseModel):
    backup_name: str
