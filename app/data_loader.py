"""
Module: data_loader
Description: Generic data loader for all endpoints with JSON file support,
             extending resume loader functionality for dynamic endpoints

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28

Dependencies:
- sqlalchemy: 2.0+ - Database operations and queries
- json: 3.9+ - JSON file parsing and validation
- typing: 3.9+ - Type hints for data structures

Usage:
    from app.data_loader import load_data_from_file, import_user_data

    # Load data from JSON file
    data = load_data_from_file("data/private/pmac/ideas.json")

    # Import all user data from directory
    import_user_data(db, "pmac", "data/private/pmac/")

    # Load specific endpoint data
    ideas_data = load_endpoint_data(db, "ideas", "pmac")

Notes:
    - Supports all dynamic endpoints with flexible JSON schemas
    - Automatic file discovery and data validation
    - Batch import operations with transaction safety
    - Compatible with both single-user and multi-user data structures
    - Extends resume loader patterns for consistency
"""

import glob
import json
import os
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from .database import DataEntry, Endpoint, SessionLocal, get_db
from .schemas import get_endpoint_model

# Default data directory
DEFAULT_DATA_DIR = "data"
SUPPORTED_FORMATS = [".json"]


def discover_data_files(data_dir: Optional[str] = None) -> Dict[str, List[str]]:
    """Discover and catalog data files for all available endpoints.

    Scans the specified directory (or default ./data) for JSON data files
    that match endpoint naming patterns. Groups files by endpoint type
    for batch processing and validation.

    Args:
        data_dir (Optional[str]): Directory path to search for data files.
                                Defaults to './data' if not specified.

    Returns:
        Dict[str, List[str]]: Dictionary mapping endpoint names to lists
                            of discovered data file paths for each endpoint.

    Note:
        - Searches for JSON files matching endpoint patterns
        - Handles nested directory structures
        - Returns empty dict if directory doesn't exist
        - Used for bulk data import operations
    """
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR

    if not os.path.exists(data_dir):
        return {}

    # Pattern: {endpoint_name}.json or {endpoint_name}_*.json
    discovered: Dict[str, List[str]] = {}

    for file_path in glob.glob(os.path.join(data_dir, "*.json")):
        filename = os.path.basename(file_path)
        name_part = filename.split(".")[0]  # Remove .json

        # Handle patterns like "ideas.json", "ideas_personal.json",
        # "resume_pmac.json"
        if "_" in name_part:
            endpoint_name = name_part.split("_")[0]
        else:
            endpoint_name = name_part

        if endpoint_name not in discovered:
            discovered[endpoint_name] = []

        discovered[endpoint_name].append(file_path)

    return discovered


def load_endpoint_data_from_file(endpoint_name: str, file_path: str) -> Dict[str, Any]:
    """Load and validate endpoint data from a JSON file.

    Reads JSON data from the specified file, validates it against the
    endpoint's schema, and returns structured load results with validation
    status and any encountered errors.

    Args:
        endpoint_name (str): Name of the target endpoint for data validation.
        file_path (str): Absolute or relative path to the JSON data file.

    Returns:
        Dict[str, Any]: Load results containing:
            - success: Boolean indicating if load was successful
            - data: Loaded JSON data if successful
            - error: Error message if load failed
            - file_info: File metadata (size, modification time)

    Note:
        - Validates JSON syntax and endpoint schema compliance
        - Returns detailed error information for debugging
        - Handles file access errors gracefully
        - Used for both single-file and batch import operations
    """
    if not os.path.exists(file_path):
        return {
            "success": False,
            "error": f"Data file not found: {file_path}",
            "file_path": file_path,
        }

    try:
        # Load JSON data
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # Handle both single items and arrays
        if isinstance(raw_data, list):
            data_items = raw_data
        elif isinstance(raw_data, dict):
            # Check if it's a wrapper format with a "data" key
            if "data" in raw_data and isinstance(raw_data["data"], list):
                data_items = raw_data["data"]
            else:
                data_items = [raw_data]
        else:
            return {
                "success": False,
                "error": f"Invalid data format. Expected object or array, got "
                f"{type(raw_data)}",
                "file_path": file_path,
            }

        # Validate each item if we have a specific model
        endpoint_model: Optional[Type[BaseModel]] = get_endpoint_model(endpoint_name)
        validated_items = []

        for i, item in enumerate(data_items):
            try:
                if endpoint_model:
                    validated_item = endpoint_model(**item)
                    validated_items.append(
                        validated_item.model_dump(exclude_unset=True)
                    )
                else:
                    # No specific model, just ensure it's a dict
                    if not isinstance(item, dict):
                        return {
                            "success": False,
                            "error": f"Item {i} is not a valid object",
                            "file_path": file_path,
                        }
                    validated_items.append(item)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Validation failed for item {i}: {str(e)}",
                    "file_path": file_path,
                }

        return {
            "success": True,
            "data": validated_items,
            "count": len(validated_items),
            "file_path": file_path,
            "message": f"Loaded {len(validated_items)} items for {endpoint_name}",
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON: {str(e)}",
            "file_path": file_path,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to load file: {str(e)}",
            "file_path": file_path,
        }


def import_endpoint_data_to_database(
    endpoint_name: str,
    file_path: str,
    user_id: Optional[int] = None,
    replace_existing: bool = False,
) -> Dict[str, Any]:
    """
    Load data from file and import into database for specific endpoint

    Args:
        endpoint_name: Name of the endpoint
        file_path: Path to the data file
        user_id: User ID to associate with entries
        replace_existing: Whether to replace existing data

    Returns:
        Dict with import results
    """
    # First load and validate the file
    load_result = load_endpoint_data_from_file(endpoint_name, file_path)
    if not load_result["success"]:
        return load_result

    data_items = load_result["data"]

    # Get database session
    db = next(get_db())

    try:
        # Find endpoint
        endpoint = (
            db.query(Endpoint)
            .filter(Endpoint.name == endpoint_name, Endpoint.is_active)
            .first()
        )

        if not endpoint:
            return {
                "success": False,
                "error": f"Endpoint '{endpoint_name}' not found or inactive",
                "file_path": file_path,
            }

        # Check for existing data
        existing_entries = (
            db.query(DataEntry)
            .filter(DataEntry.endpoint_id == endpoint.id, DataEntry.is_active)
            .all()
        )

        if existing_entries and not replace_existing:
            return {
                "success": False,
                "error": (
                    f"Data already exists for '{endpoint_name}'. "
                    "Use replace_existing=True to overwrite."
                ),
                "file_path": file_path,
                "existing_entries": len(existing_entries),
            }

        # If replacing, deactivate existing entries
        replaced_count = 0
        if replace_existing and existing_entries:
            for entry in existing_entries:
                setattr(entry, "is_active", False)
                replaced_count += 1

        # Import new data
        created_entries = []
        for item_data in data_items:
            data_entry = DataEntry(
                endpoint_id=endpoint.id, data=item_data, created_by_id=user_id
            )
            db.add(data_entry)
            db.flush()  # Get ID without committing
            created_entries.append(data_entry.id)

        db.commit()

        return {
            "success": True,
            "endpoint_name": endpoint_name,
            "file_path": file_path,
            "imported_count": len(created_entries),
            "replaced_count": replaced_count,
            "entry_ids": created_entries,
            "message": f"Successfully imported {
                len(created_entries)} items to {endpoint_name}",
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": f"Database import failed: {str(e)}",
            "file_path": file_path,
        }
    finally:
        db.close()


def import_all_discovered_data(
    data_dir: Optional[str] = None,
    user_id: Optional[int] = None,
    replace_existing: bool = False,
) -> Dict[str, Any]:
    """
    Discover and import all data files found in the data directory

    Args:
        data_dir: Directory to search for data files
        user_id: User ID to associate with entries
        replace_existing: Whether to replace existing data

    Returns:
        Dict with overall import results
    """
    discovered_files = discover_data_files(data_dir)

    if not discovered_files:
        return {
            "success": True,
            "message": "No data files found to import",
            "imported_endpoints": {},
            "errors": [],
        }

    imported_endpoints: Dict[str, Any] = {}
    errors: List[Dict[str, Any]] = []
    total_imported = 0

    for endpoint_name, file_paths in discovered_files.items():
        for file_path in file_paths:
            try:
                result = import_endpoint_data_to_database(
                    endpoint_name=endpoint_name,
                    file_path=file_path,
                    user_id=user_id,
                    replace_existing=replace_existing,
                )

                if result["success"]:
                    if endpoint_name not in imported_endpoints:
                        imported_endpoints[endpoint_name] = []

                    imported_endpoints[endpoint_name].append(
                        {
                            "file": file_path,
                            "imported_count": result["imported_count"],
                            "replaced_count": result.get("replaced_count", 0),
                        }
                    )

                    total_imported += result["imported_count"]
                else:
                    errors.append(
                        {
                            "endpoint": endpoint_name,
                            "file": file_path,
                            "error": result["error"],
                        }
                    )

            except Exception as e:
                errors.append(
                    {"endpoint": endpoint_name, "file": file_path, "error": str(e)}
                )

    return {
        "success": len(errors) == 0,
        "imported_endpoints": imported_endpoints,
        "total_imported": total_imported,
        "errors": errors,
        "message": f"Imported {total_imported} total items across {
            len(imported_endpoints)} endpoints",
    }


def get_data_import_status(data_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Get status of all discoverable data files and their import status

    Args:
        data_dir: Directory to search for data files

    Returns:
        Dict with status information
    """
    discovered_files = discover_data_files(data_dir)
    db = next(get_db())

    try:
        status: Dict[str, Any] = {
            "data_directory": data_dir or DEFAULT_DATA_DIR,
            "directory_exists": os.path.exists(data_dir or DEFAULT_DATA_DIR),
            "discovered_files": {},
            "endpoint_status": {},
        }

        for endpoint_name, file_paths in discovered_files.items():
            # Check if endpoint exists in database
            endpoint = (
                db.query(Endpoint)
                .filter(Endpoint.name == endpoint_name, Endpoint.is_active)
                .first()
            )

            # Count existing data in database
            existing_count = 0
            if endpoint:
                existing_count = (
                    db.query(DataEntry)
                    .filter(
                        DataEntry.endpoint_id == endpoint.id,
                        DataEntry.is_active,
                    )
                    .count()
                )

            file_info = []
            for file_path in file_paths:
                load_result = load_endpoint_data_from_file(endpoint_name, file_path)
                file_info.append(
                    {
                        "file_path": file_path,
                        "valid": load_result["success"],
                        "item_count": load_result.get("count", 0),
                        "error": (
                            load_result.get("error")
                            if not load_result["success"]
                            else None
                        ),
                        "size_bytes": (
                            os.path.getsize(file_path)
                            if os.path.exists(file_path)
                            else 0
                        ),
                    }
                )

            status["discovered_files"][endpoint_name] = file_info
            status["endpoint_status"][endpoint_name] = {
                "endpoint_exists": endpoint is not None,
                "database_entries": existing_count,
                "files_found": len(file_paths),
                "needs_import": existing_count == 0 and len(file_paths) > 0,
            }

        return status

    finally:
        db.close()
