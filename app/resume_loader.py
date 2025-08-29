"""
Module: resume_loader
Description: Resume import utility for loading structured resume data from JSON files
             with schema validation and database persistence

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28

Dependencies:
- sqlalchemy: 2.0+ - Database operations for resume storage
- json: 3.9+ - JSON file parsing and validation
- pathlib: 3.9+ - File system operations

Usage:
    from app.resume_loader import load_resume_from_file, import_resume_to_database

    # Load resume from JSON file
    resume_data = load_resume_from_file("data/private/pmac/resume.json")

    # Import resume to database
    import_resume_to_database(db, "pmac", resume_data)

    # Auto-discover and import
    auto_import_resume(db, "pmac", "data/private/pmac/")

Notes:
    - Supports structured resume schema with validation
    - Handles contact information, experience, education, skills
    - Automatic data normalization and cleanup
    - Compatible with privacy filtering systems
    - Foundation for other data loader modules
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from .config import settings
from .database import DataEntry, Endpoint, User, get_db
from .schemas import ResumeData

# Default resume file location
DEFAULT_RESUME_FILE = "data/private/pmac/resume/resume_pmac.json"
RESUME_ENDPOINT_NAME = "resume"


def load_resume_from_file(
    file_path: Optional[str] = None,
    user_id: Optional[int] = None,
    replace_existing: bool = False,
) -> Dict[str, Any]:
    """Load and validate resume data from JSON file with database import option.

    Reads resume data from a JSON file, validates the structure and content,
    and optionally imports it directly into the database with proper user
    association and conflict resolution.

    Args:
        file_path (Optional[str]): Path to resume JSON file. Defaults to
                                 data/resume_pmac.json if not provided.
        user_id (Optional[int]): User ID to associate with resume entry.
                               If None, uses default system user.
        replace_existing (bool): Whether to replace existing resume data.
                               Defaults to False (append/update mode).

    Returns:
        Dict[str, Any]: Load results containing:
            - success: Boolean indicating if load was successful
            - data: Loaded resume data if successful
            - file_path: Resolved absolute file path used
            - import_result: Database import results if imported
            - error: Error message if load failed

    Note:
        - Supports both relative and absolute file paths
        - Validates JSON structure and resume schema compliance
        - Handles file access errors gracefully
        - Provides detailed error reporting for troubleshooting
        - Can load data without database import for validation only
    """
    if file_path is None:
        file_path = DEFAULT_RESUME_FILE

    # Convert to absolute path if relative
    if not os.path.isabs(file_path):
        file_path = os.path.join(os.getcwd(), file_path)

    if not os.path.exists(file_path):
        return {
            "success": False,
            "error": f"Resume file not found: {file_path}",
            "file_path": file_path,
        }

    try:
        # Load and validate JSON
        with open(file_path, "r", encoding="utf-8") as f:
            resume_data = json.load(f)

        # Validate against ResumeData schema
        try:
            validated_resume = ResumeData(**resume_data)
            resume_dict = validated_resume.dict(exclude_unset=True)
        except Exception as e:
            return {
                "success": False,
                "error": f"Resume data validation failed: {str(e)}",
                "file_path": file_path,
            }

        return {
            "success": True,
            "data": resume_dict,
            "file_path": file_path,
            "message": "Resume data loaded and validated successfully",
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON in resume file: {str(e)}",
            "file_path": file_path,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to load resume file: {str(e)}",
            "file_path": file_path,
        }


def import_resume_to_database(
    file_path: Optional[str] = None,
    user_id: Optional[int] = None,
    replace_existing: bool = False,
) -> Dict[str, Any]:
    """
    Load resume from file and import into database

    Args:
        file_path: Path to resume JSON file
        user_id: User ID to associate with the resume entry
        replace_existing: Whether to replace existing resume data

    Returns:
        Dict with import results
    """
    # First load the file
    load_result = load_resume_from_file(file_path)
    if not load_result["success"]:
        return load_result

    resume_data = load_result["data"]

    # Get database session
    db = next(get_db())

    try:
        # Find resume endpoint
        resume_endpoint = (
            db.query(Endpoint)
            .filter(Endpoint.name == RESUME_ENDPOINT_NAME, Endpoint.is_active == True)
            .first()
        )

        if not resume_endpoint:
            return {
                "success": False,
                "error": (
                    f"Resume endpoint '{RESUME_ENDPOINT_NAME}' " "not found or inactive"
                ),
                "file_path": load_result["file_path"],
            }

        # Check for existing resume data
        existing_entries = (
            db.query(DataEntry)
            .filter(
                DataEntry.endpoint_id == resume_endpoint.id, DataEntry.is_active == True
            )
            .all()
        )

        if existing_entries and not replace_existing:
            return {
                "success": False,
                "error": (
                    "Resume data already exists. "
                    "Use replace_existing=True to overwrite."
                ),
                "file_path": load_result["file_path"],
                "existing_entries": len(existing_entries),
            }

        # If replacing, deactivate existing entries
        if replace_existing and existing_entries:
            for entry in existing_entries:
                setattr(entry, "is_active", False)

        # Create new resume entry
        resume_entry = DataEntry(
            endpoint_id=resume_endpoint.id, data=resume_data, created_by_id=user_id
        )

        db.add(resume_entry)
        db.commit()
        db.refresh(resume_entry)

        return {
            "success": True,
            "data": resume_data,
            "file_path": load_result["file_path"],
            "entry_id": resume_entry.id,
            "replaced_entries": len(existing_entries) if replace_existing else 0,
            "message": "Resume imported successfully",
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": f"Database import failed: {str(e)}",
            "file_path": load_result["file_path"],
        }
    finally:
        db.close()


def check_resume_file_exists(file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Check if resume file exists and is readable

    Args:
        file_path: Path to resume JSON file

    Returns:
        Dict with file status information
    """
    if file_path is None:
        file_path = DEFAULT_RESUME_FILE

    if not os.path.isabs(file_path):
        file_path = os.path.join(os.getcwd(), file_path)

    exists = os.path.exists(file_path)
    readable = False
    size = 0
    modified = None

    if exists:
        try:
            readable = os.access(file_path, os.R_OK)
            stat_info = os.stat(file_path)
            size = stat_info.st_size
            modified = stat_info.st_mtime
        except (OSError, IOError):
            # Handle cases where filesystem operation fails
            # Keep default values (readable=False, size=0, modified=0)
            pass  # nosec B110

    return {
        "file_path": file_path,
        "exists": exists,
        "readable": readable,
        "size_bytes": size,
        "last_modified": modified,
        "default_location": file_path == os.path.join(os.getcwd(), DEFAULT_RESUME_FILE),
    }


def get_resume_from_database() -> Dict[str, Any]:
    """
    Get current resume data from database

    Returns:
        Dict with current resume data or error
    """
    db = next(get_db())

    try:
        # Find resume endpoint
        resume_endpoint = (
            db.query(Endpoint)
            .filter(Endpoint.name == RESUME_ENDPOINT_NAME, Endpoint.is_active == True)
            .first()
        )

        if not resume_endpoint:
            return {
                "success": False,
                "error": f"Resume endpoint '{RESUME_ENDPOINT_NAME}' not found",
            }

        # Get active resume entries
        resume_entries = (
            db.query(DataEntry)
            .filter(
                DataEntry.endpoint_id == resume_endpoint.id, DataEntry.is_active == True
            )
            .all()
        )

        if not resume_entries:
            return {
                "success": True,
                "data": [],
                "count": 0,
                "message": "No resume data found in database",
            }

        resume_data = [entry.data for entry in resume_entries]

        return {
            "success": True,
            "data": resume_data,
            "count": len(resume_data),
            "entries": [
                {"id": entry.id, "created_at": entry.created_at}
                for entry in resume_entries
            ],
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get resume from database: {str(e)}",
        }
    finally:
        db.close()
