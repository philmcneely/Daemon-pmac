"""
Test utility functions
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app.utils import (
    cleanup_old_backups,
    create_backup,
    get_single_user,
    get_uptime,
    health_check,
    is_single_user_mode,
)


def test_health_check(test_db_session):
    """Test health check function"""
    health_data = health_check()

    assert isinstance(health_data, dict)
    assert "status" in health_data
    assert "timestamp" in health_data
    assert "checks" in health_data
    assert health_data["status"] in ["healthy", "degraded", "unhealthy"]

    # Should have database check
    assert "database" in health_data["checks"]


def test_get_uptime():
    """Test uptime calculation"""
    uptime = get_uptime()
    assert isinstance(uptime, float)
    assert uptime >= 0


def test_is_single_user_mode(test_db_session):
    """Test single user mode detection"""
    from app.database import User

    # With no users, should be single user mode
    test_db_session.query(User).delete()
    test_db_session.commit()
    assert is_single_user_mode(test_db_session)

    # With one user, should be single user mode
    user = User(username="only_user", email="only@test.com", hashed_password="hash")
    test_db_session.add(user)
    test_db_session.commit()
    assert is_single_user_mode(test_db_session)

    # With two users, should be multi user mode
    user2 = User(
        username="second_user", email="second@test.com", hashed_password="hash"
    )
    test_db_session.add(user2)
    test_db_session.commit()
    assert is_single_user_mode(test_db_session) == False


def test_get_single_user(test_db_session):
    """Test getting single user"""
    from app.database import User

    # Clear users
    test_db_session.query(User).delete()
    test_db_session.commit()

    # No users
    assert get_single_user(test_db_session) is None

    # One user
    user = User(username="only_user", email="only@test.com", hashed_password="hash")
    test_db_session.add(user)
    test_db_session.commit()
    single_user = get_single_user(test_db_session)
    assert single_user is not None
    assert single_user.username == "only_user"

    # Multiple users - should return first active admin, or first active user
    user2 = User(
        username="admin_user",
        email="admin@test.com",
        hashed_password="hash",
        is_admin=True,
    )
    test_db_session.add(user2)
    test_db_session.commit()
    single_user = get_single_user(test_db_session)
    assert single_user.username == "admin_user"  # Should prefer admin


@patch("app.utils.os.path.exists")
@patch("app.utils.shutil.copy2")
@patch("app.utils.os.path.getsize")
def test_create_backup(mock_getsize, mock_copy, mock_exists):
    """Test backup creation"""
    mock_exists.return_value = True
    mock_getsize.return_value = 1024

    backup_info = create_backup()

    assert backup_info.filename.startswith("daemon_backup_")
    assert backup_info.filename.endswith(".db")
    assert backup_info.size_bytes == 1024
    mock_copy.assert_called_once()


def test_create_backup_file_not_found():
    """Test backup creation when database file doesn't exist"""
    with patch("app.utils.os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            create_backup()


@patch("app.utils.os.listdir")
@patch("app.utils.os.path.getmtime")
@patch("app.utils.os.unlink")
def test_cleanup_old_backups(mock_unlink, mock_getmtime, mock_listdir):
    """Test cleanup of old backup files"""
    from datetime import datetime, timedelta

    # Mock old backup files
    old_time = (datetime.now() - timedelta(days=35)).timestamp()
    recent_time = (datetime.now() - timedelta(days=5)).timestamp()

    mock_listdir.return_value = [
        "daemon_backup_old.db",
        "daemon_backup_recent.db",
        "other_file.txt",
    ]

    def mock_getmtime_func(path):
        if "old" in path:
            return old_time
        return recent_time

    mock_getmtime.side_effect = mock_getmtime_func

    result = cleanup_old_backups()

    # Should delete old backup but not recent one
    assert result["deleted_count"] == 1
    mock_unlink.assert_called_once()


@patch("psutil.disk_usage")
def test_health_check_disk_space(mock_disk_usage):
    """Test health check disk space monitoring"""
    # Mock low disk space
    mock_usage = MagicMock()
    mock_usage.total = 1000
    mock_usage.free = 50  # 5% free
    mock_disk_usage.return_value = mock_usage

    health_data = health_check()

    assert health_data["status"] in ["degraded", "unhealthy"]
    assert "disk_space" in health_data["checks"]


def test_data_validation_helpers():
    """Test data validation helper functions"""
    from app.utils import sanitize_data_entry, validate_endpoint_name

    # Valid endpoint names
    assert validate_endpoint_name("valid_name")
    assert validate_endpoint_name("validName123")

    # Invalid endpoint names
    assert validate_endpoint_name("123invalid") == False
    assert validate_endpoint_name("invalid-name") == False
    assert validate_endpoint_name("") == False

    # Data sanitization
    dirty_data = {
        "safe_field": "safe value",
        "html_field": "<script>alert('xss')</script>",
        "nested": {"dangerous": "<img src=x onerror=alert(1)>"},
    }

    clean_data = sanitize_data_entry(dirty_data)
    assert "<script>" not in str(clean_data)
    assert "safe value" in str(clean_data)


def test_backup_rotation():
    """Test backup rotation logic"""
    from datetime import datetime, timedelta

    from app.utils import get_backup_files_to_delete

    # Mock backup files with different ages
    backup_files = [
        ("backup_1.db", (datetime.now() - timedelta(days=40)).timestamp()),
        ("backup_2.db", (datetime.now() - timedelta(days=20)).timestamp()),
        ("backup_3.db", (datetime.now() - timedelta(days=5)).timestamp()),
    ]

    # Should identify old files for deletion
    files_to_delete = get_backup_files_to_delete(backup_files, retention_days=30)
    assert len(files_to_delete) == 1
    assert "backup_1.db" in files_to_delete


def test_system_metrics():
    """Test system metrics collection"""
    from app.utils import get_system_metrics

    metrics = get_system_metrics()

    assert isinstance(metrics, dict)
    assert "cpu_percent" in metrics
    assert "memory_percent" in metrics
    assert "disk_usage" in metrics

    # Validate metric ranges
    assert 0 <= metrics["cpu_percent"] <= 100
    assert 0 <= metrics["memory_percent"] <= 100


def test_privacy_helpers():
    """Test privacy-related utility functions"""
    from app.utils import is_sensitive_field, mask_sensitive_data

    # Sensitive field detection
    assert is_sensitive_field("password")
    assert is_sensitive_field("email")
    assert is_sensitive_field("ssn")
    assert is_sensitive_field("name") == False

    # Data masking
    sensitive_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "secret123",
        "phone": "555-1234",
    }

    masked_data = mask_sensitive_data(sensitive_data)
    assert masked_data["name"] == "John Doe"  # Not sensitive
    assert "*" in masked_data["email"]  # Should be masked
    assert masked_data["password"] == "[REDACTED]"  # Should be redacted


def test_rate_limiting_helpers():
    """Test rate limiting utility functions"""
    from unittest.mock import MagicMock

    from app.utils import get_client_identifier, should_rate_limit

    # Mock request
    mock_request = MagicMock()
    mock_request.client.host = "192.168.1.1"
    mock_request.headers = {"user-agent": "test-client"}

    client_id = get_client_identifier(mock_request)
    assert client_id == "192.168.1.1"

    # Rate limiting should start as False
    assert should_rate_limit(client_id, limit=10, window=60) == False
    assert format_bytes(500) == "500.0 B"


def test_sanitize_filename():
    """Test filename sanitization"""
    assert sanitize_filename("test file.txt") == "test_file.txt"
    assert sanitize_filename("test<>file") == "test__file"
    assert sanitize_filename("test:file") == "test_file"
    assert sanitize_filename("...test...") == "test"


def test_health_check():
    """Test health check function"""
    health = health_check()
    assert "status" in health
    assert "timestamp" in health
    assert "checks" in health
    assert "database" in health["checks"]


def test_export_import_json(test_db_session):
    """Test JSON export and import"""
    from app.database import DataEntry, Endpoint

    # Create test endpoint
    endpoint = Endpoint(
        name="test_export",
        description="Test endpoint for export",
        schema={"name": {"type": "string"}},
    )
    test_db_session.add(endpoint)
    test_db_session.commit()
    test_db_session.refresh(endpoint)

    # Add test data
    data_entry = DataEntry(endpoint_id=endpoint.id, data={"name": "Test Item"})
    test_db_session.add(data_entry)
    test_db_session.commit()

    # Export data
    exported = export_endpoint_data(test_db_session, "test_export", "json")
    assert "test_export" in exported
    assert "Test Item" in exported

    # Import data back
    result = import_endpoint_data(test_db_session, "test_export", exported, "json")
    assert result["imported_count"] >= 0
    assert result["error_count"] == 0


def test_export_csv(test_db_session):
    """Test CSV export"""
    from app.database import DataEntry, Endpoint

    # Create test endpoint
    endpoint = Endpoint(
        name="test_csv",
        description="Test CSV endpoint",
        schema={"name": {"type": "string"}, "value": {"type": "integer"}},
    )
    test_db_session.add(endpoint)
    test_db_session.commit()
    test_db_session.refresh(endpoint)

    # Add test data
    data_entry = DataEntry(
        endpoint_id=endpoint.id, data={"name": "Item1", "value": 100}
    )
    test_db_session.add(data_entry)
    test_db_session.commit()

    # Export to CSV
    exported = export_endpoint_data(test_db_session, "test_csv", "csv")
    assert "name,value" in exported or "value,name" in exported
    assert "Item1" in exported
    assert "100" in exported


def test_import_invalid_endpoint(test_db_session):
    """Test importing to nonexistent endpoint"""
    with pytest.raises(ValueError, match="not found"):
        import_endpoint_data(test_db_session, "nonexistent", "{}", "json")
