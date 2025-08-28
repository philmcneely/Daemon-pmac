"""
Module: multi_user_import
Description: Multi-user data import utilities for batch loading user data
             from directory structures and file collections

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28

Dependencies:
- sqlalchemy: 2.0+ - Database operations and user management
- pathlib: 3.9+ - File system path operations
- json: 3.9+ - JSON data parsing and validation

Usage:
    from app.multi_user_import import import_all_users, import_user_directory

    # Import all users from base directory
    import_all_users(db, "data/private/")

    # Import specific user's data
    import_user_directory(db, "pmac", "data/private/pmac/")

    # Batch import with progress tracking
    results = batch_import_users(db, user_directories)

Notes:
    - Handles directory-based user data organization
    - Supports multiple data formats and endpoint types
    - Automatic user creation if users don't exist
    - Transaction safety with rollback on errors
    - Progress tracking and detailed error reporting
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from .config import settings
from .database import DataEntry, Endpoint, SessionLocal, User, get_db


def import_user_data_from_directory(
    username: str,
    data_directory: Optional[str] = None,
    db: Optional[Session] = None,
    replace_existing: bool = False,
) -> Dict[str, Any]:
    """
    Import data for a specific user from their data directory

    Args:
        username: Username to import data for
        data_directory: Path to user's data directory
            (defaults to data/private/{username})
        db: Database session (optional)
        replace_existing: Whether to replace existing data entries

    Returns:
        Dict with import results
    """
    if not db:
        db = next(get_db())

    # Find the user
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return {
            "success": False,
            "error": f"User '{username}' not found",
            "username": username,
        }

    # Set default data directory
    if data_directory is None:
        data_directory = f"data/private/{username}"

    # Convert to absolute path
    if not os.path.isabs(data_directory):
        data_directory = os.path.join(os.getcwd(), data_directory)

    if not os.path.exists(data_directory):
        return {
            "success": False,
            "error": f"Data directory not found: {data_directory}",
            "username": username,
            "directory": data_directory,
        }

    results = {
        "success": True,
        "username": username,
        "directory": data_directory,
        "imported_files": [],
        "errors": [],
        "total_entries": 0,
    }

    # Find all JSON files in the directory (supports new nested structure)
    imported_files = []
    total_entries = 0
    errors = []

    # Check for new nested structure first
    endpoint_dirs = [
        "resume",
        "skills",
        "books",
        "hobbies",
        "ideas",
        "problems",
        "looking_for",
    ]

    for endpoint_name in endpoint_dirs:
        endpoint_dir = os.path.join(data_directory, endpoint_name)
        if os.path.exists(endpoint_dir):
            # Process files in endpoint directory
            for file_path in Path(endpoint_dir).glob("*.json"):
                try:
                    file_result = import_user_file(
                        username=username,
                        file_path=str(file_path),
                        endpoint_name=endpoint_name,
                        db=db,
                        replace_existing=replace_existing,
                    )

                    if file_result["success"]:
                        imported_files.append(
                            {
                                "file": str(file_path),
                                "endpoint": endpoint_name,
                                "entries": file_result.get("entries_created", 0),
                            }
                        )
                        total_entries += file_result.get("entries_created", 0)
                    else:
                        errors.append(
                            {"file": str(file_path), "error": file_result["error"]}
                        )

                except Exception as e:
                    errors.append({"file": str(file_path), "error": str(e)})

    # Also check for old flat structure files
    json_files = [f for f in Path(data_directory).glob("*.json") if f.is_file()]

    for file_path in json_files:
        try:
            # Extract endpoint name from filename
            # e.g., "resume_pmac.json" -> "resume"
            filename = file_path.stem
            endpoint_name = filename.replace(f"_{username}", "").replace(
                f"_{user.username}", ""
            )

            # If no username suffix, use the whole filename as endpoint
            if endpoint_name == filename:
                endpoint_name = filename

            # Load and import the data
            file_result = import_user_file(
                username=username,
                file_path=str(file_path),
                endpoint_name=endpoint_name,
                db=db,
                replace_existing=replace_existing,
            )

            if file_result["success"]:
                imported_files.append(
                    {
                        "file": str(file_path),
                        "endpoint": endpoint_name,
                        "entries": file_result.get("entries_created", 0),
                    }
                )
                total_entries += file_result.get("entries_created", 0)
            else:
                errors.append({"file": str(file_path), "error": file_result["error"]})

        except Exception as e:
            errors.append({"file": str(file_path), "error": str(e)})

    results = {
        "success": True,
        "username": username,
        "directory": data_directory,
        "imported_files": imported_files,
        "errors": errors,
        "total_entries": total_entries,
    }

    return results


def import_user_file(
    username: str,
    file_path: str,
    endpoint_name: str,
    db: Session,
    replace_existing: bool = False,
) -> Dict[str, Any]:
    """
    Import a single JSON file for a user

    Args:
        username: Username to import data for
        file_path: Path to JSON file
        endpoint_name: Name of the endpoint to import to
        db: Database session
        replace_existing: Whether to replace existing entries

    Returns:
        Dict with import results
    """
    # Find the user
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return {"success": False, "error": f"User '{username}' not found"}

    # Find or create endpoint
    endpoint = db.query(Endpoint).filter(Endpoint.name == endpoint_name).first()
    if not endpoint:
        # Create endpoint if it doesn't exist
        endpoint = Endpoint(
            name=endpoint_name,
            description=f"Auto-created endpoint for {endpoint_name}",
            schema={},  # Basic schema
            is_active=True,
            is_public=True,
            created_by_id=user.id,
        )
        db.add(endpoint)
        db.commit()
        db.refresh(endpoint)

    # Load JSON data
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {"success": False, "error": f"Failed to load JSON file: {str(e)}"}

    # Handle both single objects and arrays
    if isinstance(data, list):
        data_items = data
    else:
        data_items = [data]

    # Clear existing data if replace_existing is True
    if replace_existing:
        db.query(DataEntry).filter(
            DataEntry.endpoint_id == endpoint.id, DataEntry.created_by_id == user.id
        ).delete()
        db.commit()

    # Import data entries
    entries_created = 0
    for item in data_items:
        try:
            data_entry = DataEntry(
                endpoint_id=endpoint.id,
                data=item,
                created_by_id=user.id,
                is_active=True,
            )
            db.add(data_entry)
            entries_created += 1
        except Exception as e:
            return {"success": False, "error": f"Failed to create data entry: {str(e)}"}

    db.commit()

    return {
        "success": True,
        "endpoint": endpoint_name,
        "entries_created": entries_created,
        "user": username,
    }


def import_all_users_data(
    base_directory: str = "data/private",
    db: Optional[Session] = None,
    replace_existing: bool = False,
) -> Dict[str, Any]:
    """
    Import data for all users from their respective directories

    Args:
        base_directory: Base directory containing user folders
        db: Database session (optional)
        replace_existing: Whether to replace existing data

    Returns:
        Dict with overall import results
    """
    if not db:
        db = next(get_db())

    if not os.path.exists(base_directory):
        return {
            "success": False,
            "error": f"Base directory not found: {base_directory}",
        }

    results: Dict[str, Any] = {
        "success": True,
        "base_directory": base_directory,
        "users_processed": [],
        "errors": [],
        "total_users": 0,
        "total_entries": 0,
    }

    # Find all user directories
    user_directories = [
        d
        for d in os.listdir(base_directory)
        if os.path.isdir(os.path.join(base_directory, d))
    ]

    for username in user_directories:
        user_dir = os.path.join(base_directory, username)

        try:
            # Check if user exists in database
            user = db.query(User).filter(User.username == username).first()
            if not user:
                results["errors"].append(
                    {
                        "username": username,
                        "error": (
                            f"User '{username}' not found in database. "
                            "Create user first."
                        ),
                    }
                )
                continue

            # Import user data
            user_result = import_user_data_from_directory(
                username=username,
                data_directory=user_dir,
                db=db,
                replace_existing=replace_existing,
            )

            if user_result["success"]:
                results["users_processed"].append(user_result)
                results["total_entries"] += user_result.get("total_entries", 0)
            else:
                results["errors"].append(
                    {
                        "username": username,
                        "error": user_result.get("error", "Unknown error"),
                    }
                )

        except Exception as e:
            results["errors"].append({"username": username, "error": str(e)})

    results["total_users"] = len(results["users_processed"])

    return results


def create_user_data_directory(
    username: str, base_directory: str = "data/private"
) -> str:
    """
    Create a data directory for a new user and copy example files

    Args:
        username: Username to create directory for
        base_directory: Base directory for user data

    Returns:
        Path to created directory
    """
    user_dir = os.path.join(base_directory, username)
    os.makedirs(user_dir, exist_ok=True)

    # Copy example files if they exist
    examples_dir = "data/examples"
    if os.path.exists(examples_dir):
        for example_file in os.listdir(examples_dir):
            if example_file.endswith(".json"):
                src_path = os.path.join(examples_dir, example_file)

                # Create user-specific filename
                base_name = example_file.replace("_example", f"_{username}")
                dst_path = os.path.join(user_dir, base_name)

                # Copy and customize the example file
                try:
                    with open(src_path, "r", encoding="utf-8") as f:
                        example_data = json.load(f)

                    # Customize the example data for the user
                    if isinstance(example_data, dict):
                        if "name" in example_data:
                            example_data["name"] = username.title()
                        if "updated_at" in example_data:
                            from datetime import datetime

                            example_data["updated_at"] = datetime.now().isoformat()

                    with open(dst_path, "w", encoding="utf-8") as f:
                        json.dump(example_data, f, indent=2)

                except Exception as e:
                    print(f"Warning: Could not copy example file {example_file}: {e}")

    return user_dir
