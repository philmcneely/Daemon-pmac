"""
Management routes for admin operations
"""

import os
import shutil
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import generate_api_key, get_current_admin_user
from ..config import settings
from ..database import ApiKey, AuditLog, DataEntry, Endpoint, User, get_db
from ..schemas import (
    ApiKeyCreate,
    ApiKeyResponse,
    BackupResponse,
    BulkOperationResponse,
    EndpointResponse,
    UserResponse,
)
from ..utils import cleanup_old_backups, create_backup

router = APIRouter(prefix="/admin", tags=["Administration"])


# User management
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)
):
    """List all users"""
    users = db.query(User).all()
    return users


@router.put("/users/{user_id}/toggle")
async def toggle_user_status(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Toggle user active status"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate yourself"
        )

    user.is_active = not user.is_active
    db.commit()

    return {"message": f"User {'activated' if user.is_active else 'deactivated'}"}


@router.put("/users/{user_id}/admin")
async def toggle_admin_status(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Toggle user admin status"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.is_admin = not user.is_admin
    db.commit()

    return {"message": f"User admin status {'granted' if user.is_admin else 'revoked'}"}


# API Key management
@router.get("/api-keys")
async def list_api_keys(
    current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)
):
    """List all API keys"""
    api_keys = db.query(ApiKey).all()
    return [
        {
            "id": key.id,
            "name": key.name,
            "user_id": key.user_id,
            "username": key.user.username,
            "is_active": key.is_active,
            "expires_at": key.expires_at,
            "last_used": key.last_used,
            "created_at": key.created_at,
        }
        for key in api_keys
    ]


@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    key_data: ApiKeyCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Create a new API key"""
    api_key, key_hash = generate_api_key()

    api_key_obj = ApiKey(
        name=key_data.name,
        key_hash=key_hash,
        user_id=current_user.id,
        expires_at=key_data.expires_at,
    )

    db.add(api_key_obj)
    db.commit()
    db.refresh(api_key_obj)

    return ApiKeyResponse(
        id=api_key_obj.id,
        name=api_key_obj.name,
        key=api_key,  # Only returned on creation
        expires_at=api_key_obj.expires_at,
        created_at=api_key_obj.created_at,
    )


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Delete an API key"""
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    db.delete(api_key)
    db.commit()

    return {"message": "API key deleted"}


# Endpoint management
@router.get("/endpoints", response_model=List[EndpointResponse])
async def list_all_endpoints(
    current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)
):
    """List all endpoints including inactive ones"""
    endpoints = db.query(Endpoint).all()
    return endpoints


@router.put("/endpoints/{endpoint_id}/toggle")
async def toggle_endpoint_status(
    endpoint_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Toggle endpoint active status"""
    endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found"
        )

    endpoint.is_active = not endpoint.is_active
    db.commit()

    # Clear OpenAPI schema cache to refresh endpoint dropdowns
    # (since active status affects available endpoints)
    from .. import main

    if hasattr(main.app, "openapi_schema"):
        main.app.openapi_schema = None

    return {
        "message": f"Endpoint {'activated' if endpoint.is_active else 'deactivated'}"
    }


@router.delete("/endpoints/{endpoint_id}")
async def delete_endpoint(
    endpoint_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Delete an endpoint and all its data"""
    endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found"
        )

    # Delete all associated data entries
    db.query(DataEntry).filter(DataEntry.endpoint_id == endpoint_id).delete()

    # Store endpoint name for response
    endpoint_name = endpoint.name

    # Delete the endpoint
    db.delete(endpoint)
    db.commit()

    # Clear OpenAPI schema cache to refresh endpoint dropdowns
    from .. import main

    if hasattr(main.app, "openapi_schema"):
        main.app.openapi_schema = None

    return {"message": f"Endpoint '{endpoint_name}' and all its data deleted"}


# Data management
@router.get("/data/stats")
async def get_data_stats(
    current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)
):
    """Get statistics about stored data"""
    stats = {}

    # Count total entries per endpoint
    endpoints = db.query(Endpoint).all()
    for endpoint in endpoints:
        active_count = (
            db.query(DataEntry)
            .filter(DataEntry.endpoint_id == endpoint.id, DataEntry.is_active == True)
            .count()
        )

        total_count = (
            db.query(DataEntry).filter(DataEntry.endpoint_id == endpoint.id).count()
        )

        stats[endpoint.name] = {
            "active": active_count,
            "total": total_count,
            "deleted": total_count - active_count,
        }

    # Overall stats
    total_active = db.query(DataEntry).filter(DataEntry.is_active == True).count()
    total_all = db.query(DataEntry).count()

    return {
        "endpoints": stats,
        "totals": {
            "active_entries": total_active,
            "total_entries": total_all,
            "deleted_entries": total_all - total_active,
            "endpoints_count": len(endpoints),
        },
    }


@router.delete("/data/cleanup")
async def cleanup_deleted_data(
    current_user: User = Depends(get_current_admin_user), db: Session = Depends(get_db)
):
    """Permanently delete soft-deleted data entries"""
    deleted_count = db.query(DataEntry).filter(DataEntry.is_active == False).count()

    # Actually delete the records
    db.query(DataEntry).filter(DataEntry.is_active == False).delete()
    db.commit()

    return {"message": f"Permanently deleted {deleted_count} soft-deleted entries"}


# Backup management
@router.post("/backup", response_model=BackupResponse)
async def create_manual_backup(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Create a manual backup"""
    try:
        backup_info = create_backup()

        # Schedule cleanup of old backups in background
        background_tasks.add_task(cleanup_old_backups)

        return backup_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup failed: {str(e)}",
        )


@router.get("/backups")
async def list_backups(current_user: User = Depends(get_current_admin_user)):
    """List available backup files"""
    backup_dir = settings.backup_dir
    if not os.path.exists(backup_dir):
        return {"backups": []}

    backups = []
    for filename in os.listdir(backup_dir):
        if filename.endswith(".db"):
            filepath = os.path.join(backup_dir, filename)
            stat_info = os.stat(filepath)
            backups.append(
                {
                    "filename": filename,
                    "size_bytes": stat_info.st_size,
                    "created_at": datetime.fromtimestamp(stat_info.st_ctime),
                }
            )

    # Sort by creation date (newest first)
    backups.sort(key=lambda x: x["created_at"], reverse=True)

    return {"backups": backups}


@router.post("/restore/{backup_filename}")
async def restore_backup(
    backup_filename: str, current_user: User = Depends(get_current_admin_user)
):
    """Restore from a backup file"""
    backup_path = os.path.join(settings.backup_dir, backup_filename)

    if not os.path.exists(backup_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backup file not found"
        )

    # Parse database URL to get the database file path
    db_path = settings.database_url.replace("sqlite:///", "")
    if db_path.startswith("./"):
        db_path = db_path[2:]

    try:
        # Create a backup of current database before restoring
        current_backup = f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        current_backup_path = os.path.join(settings.backup_dir, current_backup)
        shutil.copy2(db_path, current_backup_path)

        # Restore from backup
        shutil.copy2(backup_path, db_path)

        return {
            "message": f"Database restored from {backup_filename}",
            "current_backup": current_backup,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Restore failed: {str(e)}",
        )


# Audit log
@router.get("/audit")
async def get_audit_log(
    page: int = 1,
    size: int = 50,
    action: str = None,
    table_name: str = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Get audit log entries"""
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action.upper())

    if table_name:
        query = query.filter(AuditLog.table_name == table_name)

    # Order by most recent first
    query = query.order_by(AuditLog.created_at.desc())

    # Pagination
    offset = (page - 1) * size
    total = query.count()
    entries = query.offset(offset).limit(size).all()

    return {
        "entries": [
            {
                "id": entry.id,
                "action": entry.action,
                "table_name": entry.table_name,
                "record_id": entry.record_id,
                "old_values": entry.old_values,
                "new_values": entry.new_values,
                "username": entry.user.username if entry.user else None,
                "ip_address": entry.ip_address,
                "user_agent": entry.user_agent,
                "created_at": entry.created_at,
            }
            for entry in entries
        ],
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
            "pages": (total + size - 1) // size,
        },
    }


# System information
@router.get("/system")
async def get_system_info(current_user: User = Depends(get_current_admin_user)):
    """Get system information"""
    import sys
    from datetime import datetime

    import psutil

    # Database file size
    db_path = settings.database_url.replace("sqlite:///", "")
    if db_path.startswith("./"):
        db_path = db_path[2:]

    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

    return {
        "system": {
            "python_version": sys.version,
            "platform": sys.platform,
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage": dict(zip(["total", "used", "free"], psutil.disk_usage("."))),
        },
        "application": {
            "version": "0.1.0",
            "database_size": db_size,
            "backup_dir": settings.backup_dir,
            "backup_enabled": settings.backup_enabled,
            "rate_limit": (
                f"{settings.rate_limit_requests}/" f"{settings.rate_limit_window}s"
            ),
        },
        "timestamp": datetime.now(timezone.utc),
    }
