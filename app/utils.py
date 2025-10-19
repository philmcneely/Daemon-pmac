# mypy: ignore-errors
"""
Module: utils
Description: Utility functions for backup operations, monitoring, health checks,
             and general application support functions

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28

Dependencies:
- sqlalchemy: 2.0+ - Database operations for backups
- psutil: 5.9.0+ - System monitoring for health checks
- datetime: 3.9+ - Timestamp and date operations
"""

import html
import json
import logging
import os
import re
import shutil
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union, cast

import psutil
from sqlalchemy.orm import Session

from app.database import User  # type: ignore

from .config import settings  # type: ignore
from .schemas import BackupResponse  # type: ignore

# Exported symbols
__all__ = [
    "mask_sensitive_data",
    "sanitize_data_dict",
    "sanitize_input",
    "is_sensitive_field",
    "validate_url",
    "get_backup_files_to_delete",
    "sanitize_data_entry",
    "validate_endpoint_name",
    "get_client_identifier",
    "should_rate_limit",
]

# Setup logging
logging.basicConfig(level=getattr(logging, settings.logging_level.upper()))


def get_structured_logger(name: str) -> logging.LoggerAdapter[Any]:  # type: ignore
    """
    Return a logger configured to emit JSON‑formatted log records.
    """
    try:
        from pythonjsonlogger import jsonlogger  # type: ignore

        json_handler = logging.StreamHandler()
        json_formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(service)s",
            timestamp=True,
        )
        json_handler.setFormatter(json_formatter)
        structured_logger = logging.getLogger(name)
        structured_logger.setLevel(getattr(logging, settings.logging_level.upper()))
        if not any(
            isinstance(h, logging.StreamHandler) for h in structured_logger.handlers
        ):
            structured_logger.addHandler(json_handler)
        structured_logger = logging.LoggerAdapter(
            structured_logger, {"service": settings.app_name}
        )
        return structured_logger
    except Exception:
        fallback_logger = logging.getLogger(name)
        fallback_logger.setLevel(getattr(logging, settings.logging_level.upper()))
        return logging.LoggerAdapter(fallback_logger, {})


logger = get_structured_logger(__name__)  # type: ignore


def _reescape_quotes_in_code_blocks(text: str) -> str:
    """Replace double quotes with HTML entity only inside markdown code fences."""

    def replace(match):
        block = match.group(0)
        # Preserve the code fence markers
        if block.startswith("```") and block.endswith("```"):
            # Extract the content inside the code fence
            content = block[3:-3]
            # Replace double quotes with HTML entities
            content = content.replace('"', '"')
            # Reconstruct the code fence with preserved markers
            return f"```{content}```"
        else:
            # This shouldn't happen, but just in case
            return block.replace('"', '"')

    return re.sub(r"```.*?```", replace, text, flags=re.DOTALL)


def create_backup() -> BackupResponse:
    """Create a backup of the database."""
    os.makedirs(settings.backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"daemon_backup_{timestamp}.db"
    backup_path = os.path.join(settings.backup_dir, backup_filename)

    db_path = settings.database_url.replace("sqlite:///", "")
    if db_path.startswith("./"):
        db_path = db_path[2:]

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    shutil.copy2(db_path, backup_path)
    backup_size = os.path.getsize(backup_path)
    logger.info(f"Backup created: {backup_filename} ({backup_size} bytes)")

    return BackupResponse(
        filename=backup_filename, size_bytes=backup_size, created_at=datetime.now()
    )


def cleanup_old_backups() -> Dict[str, Union[int, str, None]]:
    """Remove old backup files based on retention policy."""
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

        if deleted_count:
            logger.info(f"Cleaned up {deleted_count} old backup files")
        return {"deleted_count": deleted_count, "error": None}
    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}")
        return {"deleted_count": 0, "error": str(e)}


def validate_json_schema(data: Dict[str, Any], schema: Any) -> List[str]:
    """Basic JSON schema validation."""
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
                    f"Field '{field_name}' must be at least {field_schema['min_length']} characters"
                )
            if "max_length" in field_schema and len(value) > field_schema["max_length"]:
                errors.append(
                    f"Field '{field_name}' must be at most {field_schema['max_length']} characters"
                )

        # Number range validation
        if field_type in ("integer", "number") and isinstance(value, (int, float)):
            if "minimum" in field_schema and value < field_schema["minimum"]:
                errors.append(
                    f"Field '{field_name}' must be at least {field_schema['minimum']}"
                )
            if "maximum" in field_schema and value > field_schema["maximum"]:
                errors.append(
                    f"Field '{field_name}' must be at most {field_schema['maximum']}"
                )
    return errors


def export_endpoint_data(
    db_session: Session, endpoint_name: str, format: str = "json"
) -> str:
    """Export endpoint data to JSON or CSV."""
    from .database import DataEntry, Endpoint  # type: ignore

    endpoint = (
        db_session.query(Endpoint)
        .filter(Endpoint.name == endpoint_name, Endpoint.is_active == True)
        .first()
    )
    if not endpoint:
        raise ValueError(f"Endpoint '{endpoint_name}' not found")

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
        all_keys = set()
        for entry in data:
            all_keys.update(entry.keys())
        fieldnames = sorted(all_keys)
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for entry in data:
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
    db_session: Session,
    endpoint_name: str,
    data_content: str,
    format: str = "json",
    user_id: Optional[int] = None,
) -> Any:  # type: ignore
    """Import data into an endpoint."""
    from .database import DataEntry, Endpoint  # type: ignore

    endpoint = (
        db_session.query(Endpoint)
        .filter(Endpoint.name == endpoint_name, Endpoint.is_active == True)
        .first()
    )
    if not endpoint:
        raise ValueError(f"Endpoint '{endpoint_name}' not found")

    imported_count = 0
    errors: List[Dict[str, Any]] = []

    try:
        if format.lower() == "json":
            import_data = json.loads(data_content)

            if isinstance(import_data, dict):
                if "data" in import_data and isinstance(import_data["data"], list):
                    data_list = import_data["data"]
                else:
                    data_list = [import_data]
            elif isinstance(import_data, list):
                data_list = import_data
            else:
                raise ValueError("Invalid JSON structure")

            for i, item_data in enumerate(data_list):
                try:
                    schema_dict_json: Any = endpoint.schema
                    if hasattr(schema_dict_json, "type"):
                        try:
                            schema_type = schema_dict_json.type.python_type
                            schema_dict_json = json.loads(schema_type)  # type: ignore
                        except Exception:
                            schema_dict_json = {}
                    schema_errors = validate_json_schema(item_data, schema_dict_json)
                    if schema_errors:
                        errors.append(
                            {"index": i, "data": item_data, "errors": schema_errors}
                        )
                        continue

                    data_entry = DataEntry(
                        endpoint_id=endpoint.id,
                        data=item_data,
                        created_by_id=user_id,
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
                    processed_row: Dict[str, Any] = {}
                    for key, value in row.items():
                        if value == "":
                            processed_row[key] = None
                        elif isinstance(value, str) and value.startswith(("[", "{")):
                            try:
                                processed_row[key] = json.loads(value)
                            except Exception:
                                processed_row[key] = value
                        else:
                            processed_row[key] = value

                    schema_dict_csv: Any = endpoint.schema
                    if hasattr(schema_dict_csv, "type"):
                        try:
                            schema_type = schema_dict_csv.type.python_type
                            schema_dict_csv = json.loads(schema_type)  # type: ignore
                        except Exception:
                            schema_dict_csv = {}
                    schema_errors = validate_json_schema(processed_row, schema_dict_csv)
                    if schema_errors:
                        errors.append(
                            {"index": i, "data": processed_row, "errors": schema_errors}
                        )
                        continue

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

        db_session.commit()
        return {
            "imported_count": imported_count,
            "error_count": len(errors),
            "errors": errors,
        }

    except Exception as e:
        db_session.rollback()
        raise ValueError(f"Import failed: {str(e)}")


def get_system_metrics() -> Dict[str, Any]:  # type: ignore
    """Collect basic system metrics."""
    try:
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage(".")

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
    """Perform a health check of the system."""
    from .database import engine  # type: ignore

    health: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {},
    }

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

    try:
        disk = psutil.disk_usage(".")
        free_percent = (disk.free / disk.total) * 100
        if free_percent < 5:
            health["status"] = "unhealthy"
            health["checks"]["disk_space"] = {
                "status": "critical",
                "message": f"Critical disk space: {free_percent:.1f}% free",
            }
        elif free_percent < 10:
            health["status"] = "degraded"
            health["checks"]["disk_space"] = {
                "status": "warning",
                "message": f"Low disk space: {free_percent:.1f}% free",
            }
        else:
            health["checks"]["disk_space"] = {
                "status": "healthy",
                "message": f"Disk space: {free_percent:.1f}% free",
            }
    except Exception as e:
        health["checks"]["disk_space"] = {"status": "unknown", "message": str(e)}

    return health


_startup_time = datetime.now(timezone.utc)


def get_uptime() -> float:
    """Return application uptime in seconds."""
    return (datetime.now(timezone.utc) - _startup_time).total_seconds()


def format_bytes(bytes_value: int) -> str:
    """Human-readable byte formatting."""
    value: float = float(bytes_value)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024.0:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} PB"


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe filesystem usage."""
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    filename = re.sub(r"\s+", "_", filename)
    filename = filename.strip(".")
    if len(filename) > 255:
        filename = filename[:255]
    return filename


def is_single_user_mode(db: Session) -> bool:
    """Determine if the system is in single-user mode."""
    if settings.multi_user_mode == "single":
        return True
    if settings.multi_user_mode == "multi":
        return False
    return db.query(User).filter(User.is_active == True).count() <= 1


def get_single_user(db: Session) -> Any:
    """Return the single user or preferred admin user."""
    from .database import User  # type: ignore

    count = db.query(User).filter(User.is_active == True).count()
    if count == 0:
        return None
    if count == 1:
        return db.query(User).filter(User.is_active == True).first()
    admin_user = (
        db.query(User).filter(User.is_active == True, User.is_admin == True).first()
    )
    return admin_user or db.query(User).filter(User.is_active == True).first()


def _sanitize_input_impl(value: Any) -> Any:
    """Sanitize input while preserving HTML entities like \"\"."""
    if isinstance(value, str):
        # Prevent path traversal attempts
        if any(
            pattern in value for pattern in ["../", "..\\", "%2e%2e%2f", "%2e%2e\\"]
        ):
            value = re.sub(r"\.\.[/\\]", "", value, flags=re.IGNORECASE)
            value = re.sub(r"%2e%2e[/\\]", "", value, flags=re.IGNORECASE)

        # Prevent command injection attempts
        dangerous_patterns = [
            r";\s*[a-zA-Z_][a-zA-Z0-9_]*",
            r"\$\{.*?\}",
            r"\$\((.*?)\)",
            r"\{\{.*?\}\}",
        ]
        for pattern in dangerous_patterns:
            value = re.sub(pattern, "", value, flags=re.IGNORECASE)

        # Handle backticks separately to preserve code fences
        # Remove standalone backticks but not those in code fences (``` or `.*?`)
        # Only remove backticks that are not part of inline code or code fences
        # This pattern is more complex to avoid removing backticks in inline code
        # Remove single backticks that are not part of inline code patterns
        # This is a simple approach: remove backticks that are not preceded by a non-whitespace character
        # and not followed by a non-whitespace character
        # This will remove standalone backticks but preserve inline code
        value = re.sub(
            r"(?<=\s)`(?=\s)", "", value
        )  # Remove backticks surrounded by whitespace
        value = re.sub(
            r"^`(?=\s)", "", value
        )  # Remove backtick at start of string followed by whitespace
        value = re.sub(
            r"(?<=\s)`$", "", value
        )  # Remove backtick at end of string preceded by whitespace

        # Prevent SQL injection attempts
        # Note: SQL injection should be prevented at the database level with parameterized queries
        # This is a basic check to prevent obvious attempts in user-facing content
        sql_patterns = [
            r'[\'"]\s*(OR|AND)\s*[\'"]',
            r"--\s*$",
            r"/\*.*?\*/",
        ]
        for pattern in sql_patterns:
            value = re.sub(pattern, "", value, flags=re.IGNORECASE)

        # Prevent XSS attempts
        xss_patterns = [
            r"<script.*?>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe.*?>.*?</iframe>",
            r"<object.*?>.*?</object>",
            r"<embed.*?>.*?</embed>",
            r"<\?xml.*?\?>",
        ]
        for pattern in xss_patterns:
            value = re.sub(pattern, "", value, flags=re.IGNORECASE)

        # Remove XML entity declarations
        value = re.sub(
            r"<!\[CDATA\[.*?\]\]>", "", value, flags=re.DOTALL | re.IGNORECASE
        )
        value = re.sub(r"<!ENTITY.*?>", "", value, flags=re.IGNORECASE)
        value = re.sub(r"<!DOCTYPE.*?>", "", value, flags=re.IGNORECASE)

        # Validate URLs
        url_pattern = r"[a-zA-Z][a-zA-Z0-9+.-]*://[^\s]+"
        for url in re.findall(url_pattern, value):
            if not validate_url(url):
                value = value.replace(url, "[URL_REMOVED]")

        # Remove javascript: protocol
        value = re.sub(r"javascript:", "", value, flags=re.IGNORECASE)

        # Strip <script> tags (allowed elsewhere)
        value = re.sub(
            r"<script.*?</script>", "", value, flags=re.DOTALL | re.IGNORECASE
        )

        # Process HTML entities: unescape outside code fences, keep code fences unchanged
        def process_entities(text: str) -> str:
            # Split on markdown code fences and process each segment.
            parts = re.split(r"(```.*?```)", text, flags=re.DOTALL)
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    # Outside code fences: Remove HTML tags first, then unescape HTML entities
                    # Remove HTML tags
                    part = re.sub(r"<[^>]*>", "", part)
                    # Unescape HTML entities
                    part = html.unescape(part)
                    parts[i] = part
                else:
                    # Inside code fences: unescape then re‑escape double quotes as HTML entity.
                    # But preserve the code fence markers
                    if part.startswith("```") and part.endswith("```"):
                        # Extract the content inside the code fence
                        content = part[3:-3]
                        # Unescape the content
                        content = html.unescape(content)
                        # Re-escape double quotes
                        content = content.replace('"', '"')
                        # Reconstruct the code fence with preserved markers
                        parts[i] = f"```{content}```"
                    else:
                        # This shouldn't happen, but just in case
                        part = html.unescape(part)
                        part = part.replace('"', '"')
                        parts[i] = part
            return "".join(parts)

        # Apply processing
        value = process_entities(value)

        # After processing, replace literal double quotes inside code fences with HTML entity
        def replace_quotes_in_code_fences(txt: str) -> str:
            def repl(match):
                block = match.group(0)
                # Preserve the code fence markers
                if block.startswith("```") and block.endswith("```"):
                    # Extract the content inside the code fence
                    content = block[3:-3]
                    # Replace double quotes with HTML entities
                    content = content.replace('"', '"')
                    # Reconstruct the code fence with preserved markers
                    return f"```{content}```"
                else:
                    # This shouldn't happen, but just in case
                    return block.replace('"', '"')

            return re.sub(r"```.*?```", repl, txt, flags=re.DOTALL)

        value = replace_quotes_in_code_fences(value)

        return value
    return value


def sanitize_input(value: Any) -> Any:
    """Public wrapper for input sanitization."""
    return _sanitize_input_impl(value)


def sanitize_data_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively sanitize a dict, removing keys marked as sensitive."""
    sanitized: Dict[str, Any] = {}
    for key, value in data.items():
        if is_sensitive_field(key) and key.lower() != "email":
            continue
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


def mask_sensitive_data(data: Dict[str, Any], level: str = "business_card") -> Any:
    """Mask sensitive data according to privacy level."""
    sensitive_fields = {
        "business_card": [
            "ssn",
            "credit_card",
            "password",
            "api_key",
            "private_key",
            "secret",
            "phone",
            "email",
        ],
        "professional": [
            "ssn",
            "credit_card",
            "password",
            "api_key",
            "private_key",
            "email",
        ],
        "public_full": ["password", "api_key", "private_key", "email"],
        "ai_safe": [
            "email",
            "phone",
            "personal_email",
            "home_address",
            "emergency_contact",
            "ssn",
            "salary",
        ],
    }

    sensitive_patterns = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
        "api_key": r"\b[a-zA-Z0-9]{32,}\b",
        "private_key": r"-----BEGIN [A-Z ]+PRIVATE KEY-----",
        "secret": r"secret[a-zA-Z0-9]{6,}|sk_[a-zA-Z0-9_]+",
    }

    # For all levels, mask all listed sensitive fields (including email)
    fields_to_mask = sensitive_fields.get(level, sensitive_fields["business_card"])

    def mask_string_content(text: str) -> str:
        masked = text
        for field, pattern in sensitive_patterns.items():
            if field in [f.lower() for f in fields_to_mask]:
                masked = re.sub(pattern, "***REDACTED***", masked, flags=re.IGNORECASE)
        return masked

    def recursively_mask(obj):
        if isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                if any(s in k.lower() for s in fields_to_mask):
                    if "password" in k.lower() or "secret" in k.lower():
                        result[k] = "[REDACTED]"
                    elif "email" in k.lower():
                        if isinstance(v, str) and "@" in v:
                            parts = v.split("@")
                            result[k] = f"{'*' * len(parts[0])}@{parts[1]}"
                        else:
                            result[k] = "***MASKED***"
                    else:
                        result[k] = "***REDACTED***"
                else:
                    result[k] = recursively_mask(v)
            return result
        if isinstance(obj, list):
            return [recursively_mask(i) for i in obj]
        if isinstance(obj, str):
            return mask_string_content(obj)
        return obj

    return cast(Dict[str, Any], recursively_mask(data))


def is_sensitive_field(field_name: str) -> bool:
    """Return True if the field name is considered sensitive."""
    sensitive_fields = {
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "key",
        "api_key",
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
        "email",  # email is now considered sensitive for privacy filtering
    }
    return field_name.lower() in sensitive_fields


def validate_url(url: Optional[str]) -> bool:  # type: ignore
    """Validate URL to prevent SSRF attacks."""
    if not url or not isinstance(url, str):
        return False

    url_lower = url.lower()
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

    blocked_patterns = [
        r"localhost",
        r"127\.0\.0\.1",
        r"0\.0\.0\.0",
        r"10\.\d+\.\d+\.\d+",
        r"192\.168\.\d+\.\d+",
        r"172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+",
        r"169\.254\.\d+\.\d+",
        r"::1",
        r"fe80:",
    ]
    for pattern in blocked_patterns:
        if re.search(pattern, url_lower, re.IGNORECASE):
            return False

    return True


def get_backup_files_to_delete(
    backup_files: Sequence[Union[str, Tuple[str, float]]], retention_days: int = 30
) -> List[str]:
    """Get list of backup files that should be deleted based on retention policy."""
    from datetime import datetime, timedelta

    cutoff_date = datetime.now() - timedelta(days=retention_days)
    files_to_delete = []

    for backup_item in backup_files:
        try:
            if isinstance(backup_item, tuple):
                filename, timestamp = backup_item
                file_date = datetime.fromtimestamp(timestamp)
                if file_date < cutoff_date:
                    files_to_delete.append(filename)
            else:
                file_path = backup_item
                filename = os.path.basename(file_path)
                if filename.startswith("daemon_backup_") and filename.endswith(".db"):
                    timestamp_str = filename[14:-3]
                    file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    if file_date < cutoff_date:
                        files_to_delete.append(file_path)
        except (ValueError, IndexError, OSError):
            continue

    return files_to_delete


def sanitize_data_entry(data: Any) -> Any:
    """Sanitize data entry by removing HTML tags while preserving entities."""
    if isinstance(data, str):
        # Remove HTML tags but preserve HTML entities
        import html
        import re

        # Process HTML entities: unescape outside code fences, keep code fences unchanged
        def process_entities(text: str) -> str:
            # Split on markdown code fences and process each segment.
            parts = re.split(r"(```.*?```)", text, flags=re.DOTALL)
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    # Outside code fences: Remove HTML tags first, then unescape HTML entities
                    # Remove HTML tags
                    part = re.sub(r"<[^>]*>", "", part)
                    # Unescape HTML entities
                    part = html.unescape(part)
                    parts[i] = part
                else:
                    # Inside code fences: unescape then re‑escape double quotes as HTML entity.
                    # But preserve the code fence markers
                    if part.startswith("```") and part.endswith("```"):
                        # Extract the content inside the code fence
                        content = part[3:-3]
                        # Unescape the content
                        content = html.unescape(content)
                        # Re-escape double quotes
                        content = content.replace('"', '"')
                        # Reconstruct the code fence with preserved markers
                        parts[i] = f"```{content}```"
                    else:
                        # This shouldn't happen, but just in case
                        part = html.unescape(part)
                        part = part.replace('"', '"')
                        parts[i] = part
            return "".join(parts)

        # Apply processing
        sanitized = process_entities(data)

        # Only escape quotes to prevent XSS, don't escape other HTML entities
        sanitized = sanitized.replace('"', '"').replace("'", "'")
        return sanitized
    if isinstance(data, dict):
        return {key: sanitize_data_entry(value) for key, value in data.items()}
    if isinstance(data, list):
        return [sanitize_data_entry(item) for item in data]
    return data


def validate_endpoint_name(name: Optional[str]) -> bool:  # type: ignore
    """Validate endpoint name format."""
    if not name or not isinstance(name, str):
        return False
    if not re.match(r"^[a-zA-Z_]", name):
        return False
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        return False
    return True


def get_client_identifier(request: Any) -> str:
    """Extract a client identifier (IP) from a request."""
    forwarded = getattr(request.headers, "x-forwarded-for", None)
    if forwarded:
        return forwarded.split(",")[0].strip()
    return getattr(request.client, "host", "unknown")


def should_rate_limit(client_id: str, limit: int = 100, window: int = 60) -> bool:
    """Simple in‑memory rate limiter."""
    import time
    from collections import defaultdict
    from typing import cast

    if not hasattr(should_rate_limit, "requests"):
        cast(Any, should_rate_limit).requests = defaultdict(list)

    now = time.time()
    window_seconds = window * 60
    requests = cast(Any, should_rate_limit).requests[client_id]
    requests = [t for t in requests if now - t < window_seconds]
    if len(requests) >= limit:
        return True
    requests.append(now)
    cast(Any, should_rate_limit).requests[client_id] = requests
    return False
