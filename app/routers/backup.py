"""
Backup and Restore API Endpoints
Manages cloud backups, restoration, and data export
"""

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.cloud.azure_storage import azure_storage
from app.database import get_db
from app.database.models import User
from app.schemas.backup import BackupListResponse, BackupResponse, RestoreRequest
from app.utils.auth import get_current_user
from app.utils.logging import get_logger

router = APIRouter(prefix="/api/backup", tags=["backup"])
logger = get_logger(__name__)


@router.post("/create", response_model=BackupResponse)
async def create_backup(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create an encrypted backup of the database in Azure Storage
    Requires admin role
    """
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.db.enc"

        # Run backup in background
        background_tasks.add_task(azure_storage.backup_database, "mew_assistant.db", backup_name)

        return BackupResponse(
            success=True,
            message="Backup initiated",
            backup_name=backup_name,
            timestamp=datetime.utcnow(),
        )
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.get("/list", response_model=BackupListResponse)
async def list_backups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    List all available backups in Azure Storage
    Requires admin role
    """
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        backups = azure_storage.list_backups()

        return BackupListResponse(success=True, count=len(backups), backups=backups)
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")


@router.post("/restore", response_model=BackupResponse)
async def restore_backup(
    request: RestoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Restore database from a backup
    Requires admin role
    WARNING: This will overwrite the current database
    """
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        success = azure_storage.restore_database(request.backup_name, "mew_assistant.db")

        if success:
            return BackupResponse(
                success=True,
                message="Database restored successfully",
                backup_name=request.backup_name,
                timestamp=datetime.utcnow(),
            )
        else:
            raise HTTPException(status_code=500, detail="Restore failed")

    except Exception as e:
        logger.error(f"Restore failed: {e}")
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


@router.delete("/cleanup")
async def cleanup_old_backups(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete backups older than specified days
    Requires admin role
    """
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        deleted_count = azure_storage.delete_old_backups(days)

        return {
            "success": True,
            "message": f"Deleted {deleted_count} old backups",
            "deleted_count": deleted_count,
        }
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.post("/export-user-data")
async def export_user_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Export current user's data (GDPR compliance)
    Creates an encrypted backup of user's personal data
    """
    try:
        # Collect user data
        user_data = {
            "user_id": current_user.id,
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat(),
            "export_date": datetime.utcnow().isoformat(),
            # Add more user data as needed
        }

        success = azure_storage.backup_user_data(current_user.id, user_data)

        if success:
            return {"success": True, "message": "User data exported successfully"}
        else:
            raise HTTPException(status_code=500, detail="Export failed")

    except Exception as e:
        logger.error(f"User data export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
