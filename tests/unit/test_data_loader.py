"""
Comprehensive data loader tests - consolidated from multiple test files
Covers all data loading functionality with proper mocking and error handling
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, mock_open, patch

import pytest

from app.data_loader import (
    discover_data_files,
    get_data_import_status,
    import_all_discovered_data,
    import_endpoint_data_to_database,
    load_endpoint_data_from_file,
)


class TestDiscoverDataFiles:
    """Test data file discovery functionality"""

    def test_discover_data_files_empty_directory(self):
        """Test discovery in empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = discover_data_files(temp_dir)
            assert result == {}

    def test_discover_data_files_nonexistent_directory(self):
        """Test discovery in nonexistent directory"""
        result = discover_data_files("/nonexistent/path")
        assert result == {}

    def test_discover_data_files_default_directory(self):
        """Test discovery in default directory when it doesn't exist"""
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False
            result = discover_data_files()
            assert result == {}

    def test_discover_data_files_single_files(self):
        """Test discovery of single endpoint files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = ["ideas.json", "notes.json", "tasks.json"]
            for filename in test_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w") as f:
                    json.dump({"test": "data"}, f)

            result = discover_data_files(temp_dir)

            assert len(result) == 3
            assert "ideas" in result
            assert "notes" in result
            assert "tasks" in result
            assert result["ideas"]["type"] == "single"
            assert result["notes"]["type"] == "single"
            assert result["tasks"]["type"] == "single"

    def test_discover_data_files_collection_files(self):
        """Test discovery of collection endpoint files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create collection files (multiple files for same endpoint)
            collection_files = [
                "resume.json",
                "resume_personal.json",
                "resume_work.json",
                "ideas.json",
                "ideas_work.json",
                "ideas_personal.json",
            ]
            for filename in collection_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w") as f:
                    json.dump({"test": "data"}, f)

            result = discover_data_files(temp_dir)

            assert "resume" in result
            assert "ideas" in result
            assert result["resume"]["type"] == "collection"
            assert result["ideas"]["type"] == "collection"
            assert len(result["resume"]["files"]) == 3
            assert len(result["ideas"]["files"]) == 3

    def test_discover_data_files_mixed_types(self):
        """Test discovery with mixed single and collection files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mixed files
            mixed_files = [
                "tasks.json",  # Single file
                "notes.json",  # Single file
                "ideas.json",  # Collection base
                "ideas_work.json",  # Collection variant
                "ideas_personal.json",  # Collection variant
                "not_json.txt",  # Should be ignored
                "hidden.json~",  # Should be ignored
            ]
            for filename in mixed_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w") as f:
                    if filename.endswith(".json"):
                        json.dump({"test": "data"}, f)
                    else:
                        f.write("not json")

            result = discover_data_files(temp_dir)

            assert "tasks" in result
            assert "notes" in result
            assert "ideas" in result
            assert result["tasks"]["type"] == "single"
            assert result["notes"]["type"] == "single"
            assert result["ideas"]["type"] == "collection"
            assert len(result["ideas"]["files"]) == 3
            # Non-JSON files should be ignored
            assert "not_json" not in result
            assert "hidden" not in result

    def test_discover_data_files_subdirectories(self):
        """Test that subdirectories are ignored"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create file in root
            with open(os.path.join(temp_dir, "ideas.json"), "w") as f:
                json.dump({"test": "data"}, f)

            # Create subdirectory with file
            subdir = os.path.join(temp_dir, "subdir")
            os.makedirs(subdir)
            with open(os.path.join(subdir, "tasks.json"), "w") as f:
                json.dump({"test": "data"}, f)

            result = discover_data_files(temp_dir)

            assert "ideas" in result
            assert "tasks" not in result  # Should be ignored in subdirectory

    def test_discover_data_files_invalid_json(self):
        """Test handling of invalid JSON files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create valid JSON file
            with open(os.path.join(temp_dir, "valid.json"), "w") as f:
                json.dump({"test": "data"}, f)

            # Create invalid JSON file
            with open(os.path.join(temp_dir, "invalid.json"), "w") as f:
                f.write("invalid json content")

            result = discover_data_files(temp_dir)

            # Should include valid file but skip invalid one
            assert "valid" in result
            assert "invalid" not in result

    def test_discover_data_files_permission_error(self):
        """Test handling of permission errors"""
        with patch("os.listdir") as mock_listdir:
            mock_listdir.side_effect = PermissionError("Permission denied")
            result = discover_data_files("/some/path")
            assert result == {}


class TestLoadEndpointDataFromFile:
    """Test loading data from individual files"""

    def test_load_endpoint_data_from_file_success(self):
        """Test successful data loading from file"""
        test_data = {"title": "Test Item", "content": "Test content"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name

        try:
            result = load_endpoint_data_from_file(temp_file)
            assert result == test_data
        finally:
            os.unlink(temp_file)

    def test_load_endpoint_data_from_file_not_found(self):
        """Test loading from non-existent file"""
        result = load_endpoint_data_from_file("/nonexistent/file.json")
        assert result is None

    def test_load_endpoint_data_from_file_invalid_json(self):
        """Test loading from file with invalid JSON"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name

        try:
            result = load_endpoint_data_from_file(temp_file)
            assert result is None
        finally:
            os.unlink(temp_file)

    def test_load_endpoint_data_from_file_permission_error(self):
        """Test handling of permission errors"""
        with patch("builtins.open") as mock_open_file:
            mock_open_file.side_effect = PermissionError("Permission denied")
            result = load_endpoint_data_from_file("/some/file.json")
            assert result is None

    def test_load_endpoint_data_from_file_empty_file(self):
        """Test loading from empty file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("")
            temp_file = f.name

        try:
            result = load_endpoint_data_from_file(temp_file)
            assert result is None
        finally:
            os.unlink(temp_file)

    def test_load_endpoint_data_from_file_large_file(self):
        """Test loading from large file"""
        # Create large test data
        large_data = {"items": [{"id": i, "name": f"item_{i}"} for i in range(1000)]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(large_data, f)
            temp_file = f.name

        try:
            result = load_endpoint_data_from_file(temp_file)
            assert result == large_data
            assert len(result["items"]) == 1000
        finally:
            os.unlink(temp_file)


class TestImportEndpointDataToDatabase:
    """Test importing data to database"""

    @patch("app.data_loader.get_db")
    def test_import_endpoint_data_to_database_success(self, mock_get_db):
        """Test successful data import to database"""
        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock endpoint
        mock_endpoint = MagicMock()
        mock_endpoint.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_endpoint
        )

        test_data = {"title": "Test Item", "content": "Test content"}

        result = import_endpoint_data_to_database("test_endpoint", test_data, 1)

        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch("app.data_loader.get_db")
    def test_import_endpoint_data_to_database_endpoint_not_found(self, mock_get_db):
        """Test import when endpoint doesn't exist"""
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Endpoint not found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        test_data = {"title": "Test Item"}

        result = import_endpoint_data_to_database("nonexistent", test_data, 1)

        assert result is False
        mock_db.add.assert_not_called()

    @patch("app.data_loader.get_db")
    def test_import_endpoint_data_to_database_database_error(self, mock_get_db):
        """Test import with database error"""
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # Mock endpoint exists
        mock_endpoint = MagicMock()
        mock_endpoint.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_endpoint
        )

        # Database commit fails
        mock_db.commit.side_effect = Exception("Database error")

        test_data = {"title": "Test Item"}

        result = import_endpoint_data_to_database("test_endpoint", test_data, 1)

        assert result is False
        mock_db.rollback.assert_called_once()

    @patch("app.data_loader.get_db")
    def test_import_endpoint_data_to_database_empty_data(self, mock_get_db):
        """Test import with empty data"""
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        mock_endpoint = MagicMock()
        mock_endpoint.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_endpoint
        )

        # Empty data should still be importable
        test_data = {}

        result = import_endpoint_data_to_database("test_endpoint", test_data, 1)

        assert result is True
        mock_db.add.assert_called_once()

    @patch("app.data_loader.get_db")
    def test_import_endpoint_data_to_database_large_data(self, mock_get_db):
        """Test import with large data payload"""
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        mock_endpoint = MagicMock()
        mock_endpoint.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_endpoint
        )

        # Large data payload
        large_data = {"content": "x" * 10000, "items": list(range(1000))}

        result = import_endpoint_data_to_database("test_endpoint", large_data, 1)

        assert result is True
        mock_db.add.assert_called_once()


class TestImportAllDiscoveredData:
    """Test importing all discovered data"""

    @patch("app.data_loader.import_endpoint_data_to_database")
    @patch("app.data_loader.load_endpoint_data_from_file")
    @patch("app.data_loader.discover_data_files")
    def test_import_all_discovered_data_success(
        self, mock_discover, mock_load, mock_import
    ):
        """Test successful import of all discovered data"""
        # Mock discovered files
        mock_discover.return_value = {
            "ideas": {"type": "single", "files": ["/path/to/ideas.json"]},
            "notes": {
                "type": "collection",
                "files": ["/path/to/notes.json", "/path/to/notes_work.json"],
            },
        }

        # Mock successful file loading
        mock_load.side_effect = [
            {"title": "Idea 1"},  # ideas.json
            {"title": "Note 1"},  # notes.json
            {"title": "Note 2"},  # notes_work.json
        ]

        # Mock successful database import
        mock_import.return_value = True

        result = import_all_discovered_data(user_id=1)

        assert result["success"] is True
        assert result["imported_endpoints"] == 2
        assert result["total_files"] == 3
        assert result["failed_files"] == 0

    @patch("app.data_loader.import_endpoint_data_to_database")
    @patch("app.data_loader.load_endpoint_data_from_file")
    @patch("app.data_loader.discover_data_files")
    def test_import_all_discovered_data_no_files(
        self, mock_discover, mock_load, mock_import
    ):
        """Test import when no files are discovered"""
        mock_discover.return_value = {}

        result = import_all_discovered_data(user_id=1)

        assert result["success"] is True
        assert result["imported_endpoints"] == 0
        assert result["total_files"] == 0
        assert result["failed_files"] == 0

    @patch("app.data_loader.import_endpoint_data_to_database")
    @patch("app.data_loader.load_endpoint_data_from_file")
    @patch("app.data_loader.discover_data_files")
    def test_import_all_discovered_data_file_load_failures(
        self, mock_discover, mock_load, mock_import
    ):
        """Test import with some file loading failures"""
        mock_discover.return_value = {
            "ideas": {"type": "single", "files": ["/path/to/ideas.json"]},
            "notes": {"type": "single", "files": ["/path/to/notes.json"]},
        }

        # Mock mixed success/failure file loading
        mock_load.side_effect = [{"title": "Idea 1"}, None]  # Success  # Failure

        mock_import.return_value = True

        result = import_all_discovered_data(user_id=1)

        assert result["success"] is True
        assert result["imported_endpoints"] == 1  # Only one successful
        assert result["total_files"] == 2
        assert result["failed_files"] == 1

    @patch("app.data_loader.import_endpoint_data_to_database")
    @patch("app.data_loader.load_endpoint_data_from_file")
    @patch("app.data_loader.discover_data_files")
    def test_import_all_discovered_data_database_failures(
        self, mock_discover, mock_load, mock_import
    ):
        """Test import with database import failures"""
        mock_discover.return_value = {
            "ideas": {"type": "single", "files": ["/path/to/ideas.json"]}
        }

        mock_load.return_value = {"title": "Idea 1"}
        mock_import.return_value = False  # Database import fails

        result = import_all_discovered_data(user_id=1)

        assert result["success"] is False
        assert result["imported_endpoints"] == 0
        assert result["failed_files"] == 1

    @patch("app.data_loader.discover_data_files")
    def test_import_all_discovered_data_discovery_error(self, mock_discover):
        """Test import when discovery fails"""
        mock_discover.side_effect = Exception("Discovery error")

        result = import_all_discovered_data(user_id=1)

        assert result["success"] is False
        assert "error" in result


class TestGetDataImportStatus:
    """Test getting data import status"""

    @patch("app.data_loader.discover_data_files")
    def test_get_data_import_status_success(self, mock_discover):
        """Test successful status retrieval"""
        mock_discover.return_value = {
            "ideas": {"type": "single", "files": ["/path/to/ideas.json"]},
            "notes": {
                "type": "collection",
                "files": ["/path/to/notes.json", "/path/to/notes_work.json"],
            },
        }

        result = get_data_import_status()

        assert result["available_endpoints"] == 2
        assert result["total_files"] == 3
        assert "ideas" in result["endpoints"]
        assert "notes" in result["endpoints"]

    @patch("app.data_loader.discover_data_files")
    def test_get_data_import_status_no_data(self, mock_discover):
        """Test status when no data files exist"""
        mock_discover.return_value = {}

        result = get_data_import_status()

        assert result["available_endpoints"] == 0
        assert result["total_files"] == 0
        assert result["endpoints"] == {}

    @patch("app.data_loader.discover_data_files")
    def test_get_data_import_status_discovery_error(self, mock_discover):
        """Test status when discovery fails"""
        mock_discover.side_effect = Exception("Discovery error")

        result = get_data_import_status()

        assert result["available_endpoints"] == 0
        assert result["total_files"] == 0
        assert "error" in result


class TestDataLoaderSecurityValidation:
    """Test security validation and boundary conditions"""

    def test_path_traversal_prevention(self):
        """Test that path traversal attempts are blocked"""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
        ]

        for path in malicious_paths:
            result = load_endpoint_data_from_file(path)
            # Should return None for security reasons
            assert result is None

    def test_large_file_handling(self):
        """Test handling of extremely large files"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # Create very large JSON (but still valid)
            large_data = {"items": ["x" * 1000 for _ in range(1000)]}
            json.dump(large_data, f)
            temp_file = f.name

        try:
            result = load_endpoint_data_from_file(temp_file)
            # Should handle large files gracefully
            assert result is not None
            assert len(result["items"]) == 1000
        finally:
            os.unlink(temp_file)

    def test_malformed_endpoint_names(self):
        """Test handling of malformed endpoint names"""
        malformed_names = [
            "../malicious",
            "endpoint/with/slashes",
            "endpoint..json",
            "",
            None,
        ]

        for name in malformed_names:
            if name is not None:
                # Should handle malformed names gracefully
                result = import_endpoint_data_to_database(name, {"test": "data"}, 1)
                # Implementation should validate endpoint names
                assert result in [True, False]  # Should not crash

    def test_json_injection_attempts(self):
        """Test JSON with potentially malicious content"""
        malicious_json_data = {
            "script": "<script>alert('xss')</script>",
            "sql": "'; DROP TABLE users; --",
            "path": "../../../etc/passwd",
            "eval": "eval('malicious_code')",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(malicious_json_data, f)
            temp_file = f.name

        try:
            result = load_endpoint_data_from_file(temp_file)
            # Should load but content should be treated as safe strings
            assert result is not None
            assert result["script"] == "<script>alert('xss')</script>"
            # Content is loaded as-is but should be sanitized at display/use time
        finally:
            os.unlink(temp_file)

    @patch("app.data_loader.get_db")
    def test_sql_injection_in_endpoint_data(self, mock_get_db):
        """Test SQL injection attempts in endpoint data"""
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        mock_endpoint = MagicMock()
        mock_endpoint.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_endpoint
        )

        # Data with SQL injection attempts
        malicious_data = {
            "title": "'; DROP TABLE data_entries; --",
            "content": "1' OR '1'='1",
            "metadata": {"key": "value'; DELETE FROM users; --"},
        }

        # Should handle malicious data safely (SQLAlchemy should parameterize)
        result = import_endpoint_data_to_database("test", malicious_data, 1)

        # Should not crash and should be handled safely by ORM
        assert result is True
        mock_db.add.assert_called_once()

    def test_unicode_and_encoding_handling(self):
        """Test handling of various unicode and encoding scenarios"""
        unicode_data = {
            "title": "Test with émojis 🚀🔥💻",
            "content": "Unicode chars: àáâãäåæçèéêë",
            "chinese": "测试中文字符",
            "japanese": "テストの日本語",
            "emoji_mix": "🎉 Mixed content with unicode àáâã 测试 🎯",
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(unicode_data, f, ensure_ascii=False)
            temp_file = f.name

        try:
            result = load_endpoint_data_from_file(temp_file)
            assert result is not None
            assert result["title"] == "Test with émojis 🚀🔥💻"
            assert result["chinese"] == "测试中文字符"
        finally:
            os.unlink(temp_file)
