"""
Utility functions for backup, monitoring, and other operations
"""

import html
import json
import logging
import os
import re
import shutil
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

import psutil
from sqlalchemy.orm import Session

from .config import settings
from .schemas import BackupResponse

# Setup logging
logging.basicConfig(level=getattr(logging, settings.logging_level.upper()))
logger = logging.getLogger(__name__)


def create_backup() -> BackupResponse:
    """Create a backup of the database"""
    # Ensure backup directory exists
    os.makedirs(settings.backup_dir, exist_ok=True)

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"daemon_backup_{timestamp}.db"
    backup_path = os.path.join(settings.backup_dir, backup_filename)

    # Get source database path
    db_path = settings.database_url.replace("sqlite:///", "")
    if db_path.startswith("./"):
        db_path = db_path[2:]

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    # Create backup
    shutil.copy2(db_path, backup_path)

    # Get file size
    backup_size = os.path.getsize(backup_path)

    logger.info(f"Backup created: {backup_filename} ({backup_size} bytes)")

    return BackupResponse(
        filename=backup_filename, size_bytes=backup_size, created_at=datetime.now()
    )


def cleanup_old_backups():
    """Clean up old backup files based on retention policy"""
    if not settings.backup_enabled or not os.path.exists(settings.backup_dir):
        return {"deleted_count": 0, "error": None}

    cutoff_date = datetime.now() - timedelta(days=settings.backup_retention_days)
    deleted_count = 0

    try:
        for filename in os.listdir(settings.backup_dir):
            if filename.endswith(".db"):
                filepath = os.path.join(settings.backup_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))

                if file_time < cutoff_date:
                    os.unlink(filepath)
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {filename}")

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old backup files")

        return {"deleted_count": deleted_count, "error": None}

    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}")
        return {"deleted_count": 0, "error": str(e)}


def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Basic JSON schema validation"""
    errors = []

    for field_name, field_schema in schema.items():
        field_type = field_schema.get("type")
        required = field_schema.get("required", False)

        if required and field_name not in data:
            errors.append(f"Required field '{field_name}' is missing")
            continue

        if field_name not in data:
            continue

        value = data[field_name]

        # Type validation
        if field_type == "string" and not isinstance(value, str):
            errors.append(f"Field '{field_name}' must be a string")
        elif field_type == "integer" and not isinstance(value, int):
            errors.append(f"Field '{field_name}' must be an integer")
        elif field_type == "number" and not isinstance(value, (int, float)):
            errors.append(f"Field '{field_name}' must be a number")
        elif field_type == "boolean" and not isinstance(value, bool):
            errors.append(f"Field '{field_name}' must be a boolean")
        elif field_type == "array" and not isinstance(value, list):
            errors.append(f"Field '{field_name}' must be an array")
        elif field_type == "object" and not isinstance(value, dict):
            errors.append(f"Field '{field_name}' must be an object")

        # Enum validation
        if "enum" in field_schema and value not in field_schema["enum"]:
            errors.append(f"Field '{field_name}' must be one of {field_schema['enum']}")

        # String length validation
        if field_type == "string" and isinstance(value, str):
            if "min_length" in field_schema and len(value) < field_schema["min_length"]:
                errors.append(
                    f"Field '{field_name}' must be at least "
                    f"{field_schema['min_length']} characters"
                )
            if "max_length" in field_schema and len(value) > field_schema["max_length"]:
                errors.append(
                    f"Field '{field_name}' must be at most "
                    f"{field_schema['max_length']} characters"
                )

        # Number range validation
        if field_type in ["integer", "number"] and isinstance(value, (int, float)):
            if "minimum" in field_schema and value < field_schema["minimum"]:
                errors.append(
                    f"Field '{field_name}' must be at least {field_schema['minimum']}"
                )
            if "maximum" in field_schema and value > field_schema["maximum"]:
                errors.append(
                    f"Field '{field_name}' must be at most {field_schema['maximum']}"
                )

    return errors


def export_endpoint_data(db_session, endpoint_name: str, format: str = "json") -> str:
    """Export endpoint data to various formats"""
    from .database import DataEntry, Endpoint

    # Find endpoint
    endpoint = (
        db_session.query(Endpoint)
        .filter(Endpoint.name == endpoint_name, Endpoint.is_active == True)
        .first()
    )

    if not endpoint:
        raise ValueError(f"Endpoint '{endpoint_name}' not found")

    # Get data
    data_entries = (
        db_session.query(DataEntry)
        .filter(DataEntry.endpoint_id == endpoint.id, DataEntry.is_active == True)
        .all()
    )

    data = [entry.data for entry in data_entries]

    if format.lower() == "json":
        return json.dumps(
            {
                "endpoint": endpoint_name,
                "description": endpoint.description,
                "exported_at": datetime.now().isoformat(),
                "count": len(data),
                "data": data,
            },
            indent=2,
            default=str,
        )

    elif format.lower() == "csv":
        import csv
        import io

        if not data:
            return ""

        output = io.StringIO()

        # Get all unique keys from all entries
        all_keys = set()
        for entry in data:
            all_keys.update(entry.keys())

        fieldnames = sorted(all_keys)
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for entry in data:
            # Convert complex objects to JSON strings
            row = {}
            for key in fieldnames:
                value = entry.get(key, "")
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                row[key] = value
            writer.writerow(row)

        return output.getvalue()

    else:
        raise ValueError(f"Unsupported export format: {format}")


def import_endpoint_data(
    db_session,
    endpoint_name: str,
    data_content: str,
    format: str = "json",
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Import data into an endpoint"""
    from .database import DataEntry, Endpoint

    # Find endpoint
    endpoint = (
        db_session.query(Endpoint)
        .filter(Endpoint.name == endpoint_name, Endpoint.is_active == True)
        .first()
    )

    if not endpoint:
        raise ValueError(f"Endpoint '{endpoint_name}' not found")

    imported_count = 0
    errors = []

    try:
        if format.lower() == "json":
            import_data = json.loads(data_content)

            # Handle both single objects and arrays
            if isinstance(import_data, dict):
                if "data" in import_data and isinstance(import_data["data"], list):
                    data_list = import_data["data"]
                else:
                    data_list = [import_data]
            elif isinstance(import_data, list):
                data_list = import_data
            else:
                raise ValueError("Invalid JSON structure")

            # Import each item
            for i, item_data in enumerate(data_list):
                try:
                    # Validate against endpoint schema
                    schema_errors = validate_json_schema(item_data, endpoint.schema)
                    if schema_errors:
                        errors.append(
                            {"index": i, "data": item_data, "errors": schema_errors}
                        )
                        continue

                    # Create data entry
                    data_entry = DataEntry(
                        endpoint_id=endpoint.id, data=item_data, created_by_id=user_id
                    )
                    db_session.add(data_entry)
                    imported_count += 1

                except Exception as e:
                    errors.append({"index": i, "data": item_data, "error": str(e)})

        elif format.lower() == "csv":
            import csv
            import io

            csv_reader = csv.DictReader(io.StringIO(data_content))

            for i, row in enumerate(csv_reader):
                try:
                    # Convert string values back to appropriate types
                    processed_row = {}
                    for key, value in row.items():
                        if value == "":
                            processed_row[key] = None
                        elif value.startswith(("[", "{")):  # Try to parse JSON
                            try:
                                processed_row[key] = json.loads(value)
                            except:
                                processed_row[key] = value
                        else:
                            processed_row[key] = value

                    # Validate against endpoint schema
                    schema_errors = validate_json_schema(processed_row, endpoint.schema)
                    if schema_errors:
                        errors.append(
                            {"index": i, "data": processed_row, "errors": schema_errors}
                        )
                        continue

                    # Create data entry
                    data_entry = DataEntry(
                        endpoint_id=endpoint.id,
                        data=processed_row,
                        created_by_id=user_id,
                    )
                    db_session.add(data_entry)
                    imported_count += 1

                except Exception as e:
                    errors.append({"index": i, "data": row, "error": str(e)})

        else:
            raise ValueError(f"Unsupported import format: {format}")

        # Commit successful imports
        db_session.commit()

        return {
            "imported_count": imported_count,
            "error_count": len(errors),
            "errors": errors,
        }

    except Exception as e:
        db_session.rollback()
        raise ValueError(f"Import failed: {str(e)}")


def get_system_metrics() -> Dict[str, Any]:
    """Get basic system metrics"""
    import psutil

    try:
        # Memory usage
        memory = psutil.virtual_memory()

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Disk usage
        disk = psutil.disk_usage(".")

        # Database size
        db_path = settings.database_url.replace("sqlite:///", "")
        if db_path.startswith("./"):
            db_path = db_path[2:]

        db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
            },
            "cpu": {"percent": cpu_percent, "count": psutil.cpu_count()},
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100,
            },
            "database": {
                "size_bytes": db_size,
                "size_mb": round(db_size / (1024 * 1024), 2),
            },
        }

    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        return {"timestamp": datetime.now(timezone.utc).isoformat(), "error": str(e)}


def health_check() -> Dict[str, Any]:
    """Perform a health check of the system"""
    from .database import engine

    health = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {},
    }

    # Database connectivity
    try:
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful",
        }
    except Exception as e:
        health["status"] = "unhealthy"
        health["checks"]["database"] = {"status": "unhealthy", "message": str(e)}

    # Backup directory
    try:
        if settings.backup_enabled:
            if os.path.exists(settings.backup_dir) and os.access(
                settings.backup_dir, os.W_OK
            ):
                health["checks"]["backup_dir"] = {
                    "status": "healthy",
                    "message": "Backup directory accessible",
                }
            else:
                health["status"] = "degraded"
                health["checks"]["backup_dir"] = {
                    "status": "degraded",
                    "message": "Backup directory not accessible",
                }
        else:
            health["checks"]["backup_dir"] = {
                "status": "disabled",
                "message": "Backup functionality disabled",
            }
    except Exception as e:
        health["status"] = "degraded"
        health["checks"]["backup_dir"] = {"status": "unhealthy", "message": str(e)}

    # Disk space
    try:
        disk = psutil.disk_usage(".")
        free_percent = (disk.free / disk.total) * 100
        if free_percent < 10:
            health["status"] = "degraded"
            health["checks"]["disk_space"] = {
                "status": "warning",
                "message": f"Low disk space: {free_percent:.1f}% free",
            }
        elif free_percent < 5:
            health["status"] = "unhealthy"
            health["checks"]["disk_space"] = {
                "status": "critical",
                "message": f"Critical disk space: {free_percent:.1f}% free",
            }
        else:
            health["checks"]["disk_space"] = {
                "status": "healthy",
                "message": f"Disk space: {free_percent:.1f}% free",
            }
    except Exception as e:
        health["checks"]["disk_space"] = {"status": "unknown", "message": str(e)}

    return health


# Application startup time tracking
_startup_time = datetime.now(timezone.utc)


def get_uptime() -> float:
    """Get application uptime in seconds"""
    return (datetime.now(timezone.utc) - _startup_time).total_seconds()


def format_bytes(bytes_value: int) -> str:
    """Format bytes into human readable format"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe filesystem operations"""
    import re

    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    filename = re.sub(r"\s+", "_", filename)
    filename = filename.strip(".")

    # Limit length
    if len(filename) > 255:
        filename = filename[:255]

    return filename


def is_single_user_mode(db: Session) -> bool:
    """
    Check if the system is running in single-user mode.
    Returns True if there's only one active user in the system.

    Modes:
    - "auto": Automatically detect based on user count (default)
    - "single": Force single-user mode
    - "multi": Force multi-user mode
    """
    from .config import settings
    from .database import User

    if settings.multi_user_mode == "single":
        return True
    elif settings.multi_user_mode == "multi":
        return False
    else:  # "auto" mode
        user_count = db.query(User).filter(User.is_active == True).count()
        return user_count <= 1


def get_single_user(db: Session) -> Optional[Any]:
    """
    Get the single user if system is in single-user mode,
    or the preferred user (admin) in multi-user mode.
    Returns None if there are no users.
    """
    from .database import User

    # Check if there are any users
    user_count = db.query(User).filter(User.is_active == True).count()
    if user_count == 0:
        return None
    elif user_count == 1:
        return db.query(User).filter(User.is_active == True).first()
    else:
        # Multiple users - prefer admin user
        admin_user = (
            db.query(User).filter(User.is_active == True, User.is_admin == True).first()
        )
        if admin_user:
            return admin_user
        # If no admin, return first active user
        return db.query(User).filter(User.is_active == True).first()


def sanitize_input(value: Any) -> Any:
    """
    Sanitize input to prevent XSS and other injection attacks
    """
    if isinstance(value, str):
        # Check for URLs and validate them to prevent SSRF
        url_pattern = (
            r"[a-zA-Z][a-zA-Z0-9+.-]*://[^\s]+"  # More comprehensive URL pattern
        )
        if re.search(url_pattern, value):
            # Extract URLs and validate them
            urls = re.findall(url_pattern, value)
            for url in urls:
                if not validate_url(url):
                    # If URL validation fails, replace the URL
                    value = value.replace(url, "[URL_REMOVED]")

        # HTML escape special characters
        value = html.escape(value)

        # Remove or escape dangerous patterns
        # Remove javascript: protocol
        value = re.sub(r"javascript:", "", value, flags=re.IGNORECASE)

        # Remove script tags
        value = re.sub(
            r"<script[^>]*>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL
        )

        # Remove dangerous HTML attributes
        value = re.sub(r"on\w+\s*=", "", value, flags=re.IGNORECASE)

        # Remove template injection patterns
        value = re.sub(r"\{\{.*?\}\}", "[TEMPLATE_REMOVED]", value)
        value = re.sub(r"\{%.*?%\}", "[TEMPLATE_REMOVED]", value)

        # Prevent path traversal
        value = value.replace("../", "").replace("..\\", "")

        # Remove null bytes
        value = value.replace("\x00", "")

    return value


def sanitize_data_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sanitize a dictionary of data
    """
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, dict):
            sanitized[key] = sanitize_data_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_input(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            sanitized[key] = sanitize_input(value)
    return sanitized


def mask_sensitive_data(
    data: Dict[str, Any], level: str = "business_card"
) -> Dict[str, Any]:
    """
    Mask sensitive data based on privacy level
    """
    sensitive_fields = {
        "business_card": [
            "ssn",
            "credit_card",
            "password",
            "api_key",
            "private_key",
            "secret",
            "email",
            "phone",
        ],
        "professional": ["ssn", "credit_card", "password", "api_key", "private_key"],
        "public_full": ["password", "api_key", "private_key"],
        "ai_safe": [],
    }

    # Sensitive patterns to detect in any string value
    sensitive_patterns = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",  # SSN pattern
        # Credit card pattern
        "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
        # Long alphanumeric strings (potential API keys)
        "api_key": r"\b[a-zA-Z0-9]{32,}\b",
        "private_key": r"-----BEGIN [A-Z ]+PRIVATE KEY-----",  # Private key headers
        "secret": r"secret[a-zA-Z0-9]{6,}|sk_[a-zA-Z0-9_]+",  # API secret patterns
    }

    fields_to_mask = sensitive_fields.get(level, sensitive_fields["business_card"])

    def mask_string_content(text: str) -> str:
        """Mask sensitive patterns within a string"""
        if not isinstance(text, str):
            return text

        masked_text = text
        for pattern_type, pattern in sensitive_patterns.items():
            if pattern_type in [field.lower() for field in fields_to_mask]:
                masked_text = re.sub(
                    pattern, "***REDACTED***", masked_text, flags=re.IGNORECASE
                )
        return masked_text

    def recursively_mask(obj):
        """Recursively mask sensitive data in nested structures"""
        if isinstance(obj, dict):
            masked_obj = {}
            for key, value in obj.items():
                # Check if field name indicates sensitive data
                should_mask = any(
                    sensitive_field.lower() in key.lower()
                    for sensitive_field in fields_to_mask
                )
                # Debug: print what we're checking
                # print(f"Checking key '{key}' against fields {fields_to_mask}, "
                #       f"should_mask: {should_mask}")
                if should_mask:
                    # Different masking based on field type
                    if "password" in key.lower() or "secret" in key.lower():
                        masked_obj[key] = "[REDACTED]"
                    elif "email" in key.lower():
                        # Mask email while keeping format
                        if isinstance(value, str) and "@" in value:
                            parts = value.split("@")
                            if len(parts) == 2:
                                masked_obj[key] = f"{'*' * len(parts[0])}@{parts[1]}"
                            else:
                                masked_obj[key] = "***MASKED***"
                        else:
                            masked_obj[key] = "***MASKED***"
                    else:
                        masked_obj[key] = "***REDACTED***"
                else:
                    masked_obj[key] = recursively_mask(value)
            return masked_obj
        elif isinstance(obj, list):
            return [recursively_mask(item) for item in obj]
        elif isinstance(obj, str):
            return mask_string_content(obj)
        else:
            return obj

    return recursively_mask(data)


def validate_url(url: str) -> bool:
    """
    Validate URL to prevent SSRF attacks
    """
    if not url or not isinstance(url, str):
        return False

    # Convert to lowercase for pattern matching
    url_lower = url.lower()

    # Block dangerous protocols
    dangerous_protocols = [
        "file://",
        "ftp://",
        "gopher://",
        "dict://",
        "jar://",
        "netdoc://",
        "javascript:",
        "data:",
        "vbscript:",
        "jar:",
        "phar://",
    ]

    for protocol in dangerous_protocols:
        if url_lower.startswith(protocol):
            return False

    # Block localhost and internal IPs
    blocked_patterns = [
        r"localhost",
        r"127\.0\.0\.1",
        r"0\.0\.0\.0",
        r"10\.\d+\.\d+\.\d+",
        r"192\.168\.\d+\.\d+",
        r"172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+",
        r"169\.254\.\d+\.\d+",  # AWS metadata service
        r"::1",  # IPv6 localhost
        r"fe80:",  # IPv6 link-local
    ]

    for pattern in blocked_patterns:
        if re.search(pattern, url_lower, re.IGNORECASE):
            return False

    return True


def validate_endpoint_name(name: str) -> bool:
    """Validate endpoint name format"""
    if not name or not isinstance(name, str):
        return False

    # Must start with a letter or underscore
    if not re.match(r"^[a-zA-Z_]", name):
        return False

    # Can only contain letters, numbers, and underscores
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        return False

    return True


def sanitize_data_entry(data: Any) -> Any:
    """Sanitize data entry by removing dangerous content"""
    import html

    if isinstance(data, str):
        # Remove HTML tags and escape entities
        sanitized = re.sub(r"<[^>]*>", "", data)
        sanitized = html.escape(sanitized)
        return sanitized
    elif isinstance(data, dict):
        return {key: sanitize_data_entry(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_data_entry(item) for item in data]
    else:
        return data


def get_backup_files_to_delete(
    backup_files: List[Union[str, Tuple[str, float]]], retention_days: int = 30
) -> List[str]:
    """Get list of backup files that should be deleted based on retention policy"""
    from datetime import datetime, timedelta

    cutoff_date = datetime.now() - timedelta(days=retention_days)
    files_to_delete = []

    for backup_item in backup_files:
        try:
            if isinstance(backup_item, tuple):
                # Handle test format: (filename, timestamp)
                filename, timestamp = backup_item
                file_date = datetime.fromtimestamp(timestamp)
                if file_date < cutoff_date:
                    files_to_delete.append(filename)
            else:
                # Handle file path format
                file_path = backup_item
                filename = os.path.basename(file_path)
                if filename.startswith("daemon_backup_") and filename.endswith(".db"):
                    timestamp_str = filename[14:-3]  # Remove prefix and suffix
                    file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                    if file_date < cutoff_date:
                        files_to_delete.append(file_path)
        except (ValueError, IndexError, OSError):
            # Skip files that don't match expected pattern
            continue

    return files_to_delete


def is_sensitive_field(field_name: str) -> bool:
    """Check if a field name indicates sensitive data"""
    sensitive_fields = {
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "key",
        "api_key",
        "email",
        "mail",
        "address",
        "phone",
        "ssn",
        "social",
        "credit",
        "card",
        "cvv",
        "pin",
        "oauth",
        "auth",
        "session",
        "cookie",
    }

    field_lower = field_name.lower()
    return any(sensitive in field_lower for sensitive in sensitive_fields)


def get_client_identifier(request) -> str:
    """Get a unique identifier for the client making the request"""
    # Try to get real IP from headers (for proxied requests)
    forwarded_for = getattr(request.headers, "x-forwarded-for", None)
    if forwarded_for:
        # Take the first IP in the chain
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = getattr(request.client, "host", "unknown")

    return client_ip


def should_rate_limit(client_id: str, limit: int = 100, window: int = 60) -> bool:
    """Check if a client should be rate limited"""
    # This is a simple in-memory rate limiter for testing
    # In production, you'd want to use Redis or similar
    import time
    from collections import defaultdict

    if not hasattr(should_rate_limit, "requests"):
        should_rate_limit.requests = defaultdict(list)

    now = time.time()
    window_seconds = window * 60

    # Clean old requests
    should_rate_limit.requests[client_id] = [
        req_time
        for req_time in should_rate_limit.requests[client_id]
        if now - req_time < window_seconds
    ]

    # Check if limit exceeded
    if len(should_rate_limit.requests[client_id]) >= limit:
        return True

    # Add current request
    should_rate_limit.requests[client_id].append(now)
    return False
