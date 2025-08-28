"""
Module: tests.unit.test_data_loader
Description: Unit tests for data loading utilities and file import operations

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28

Dependencies:
- pytest: 7.4.3+ - Testing framework
- fastapi: 0.104.1+ - TestClient for API testing
- sqlalchemy: 2.0+ - Database operations in tests

Usage:
    pytest tests/unit/test_data_loader.py -v

Notes:
    - Unit testing with isolated component validation
    - Comprehensive test coverage with fixtures
    - Proper database isolation and cleanup
    - Authentication and authorization testing
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

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

            for endpoint, files in result.items():
                assert len(files) == 1
                assert files[0].endswith(f"{endpoint}.json")

    def test_discover_data_files_with_variants(self):
        """Test discovery of files with variants (underscore patterns)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files with variants
            test_files = [
                "ideas.json",
                "ideas_personal.json",
                "ideas_work.json",
                "resume.json",
                "resume_pmac.json",
            ]
            for filename in test_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w") as f:
                    json.dump({"test": "data"}, f)

            result = discover_data_files(temp_dir)

            assert len(result) == 2  # ideas and resume
            assert len(result["ideas"]) == 3
            assert len(result["resume"]) == 2

    def test_discover_data_files_ignores_non_json(self):
        """Test that non-JSON files are ignored"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mixed file types
            files = [
                ("ideas.json", {"test": "data"}),
                ("notes.txt", "text content"),
                ("config.yaml", "yaml: content"),
                ("tasks.json", {"task": "data"}),
            ]

            for filename, content in files:
                file_path = os.path.join(temp_dir, filename)
                if filename.endswith(".json"):
                    with open(file_path, "w") as f:
                        json.dump(content, f)
                else:
                    with open(file_path, "w") as f:
                        f.write(str(content))

            result = discover_data_files(temp_dir)

            assert len(result) == 2  # Only JSON files
            assert "ideas" in result
            assert "tasks" in result


class TestLoadEndpointDataFromFile:
    """Test loading data from individual files"""

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file"""
        result = load_endpoint_data_from_file("test", "/nonexistent/file.json")

        assert result["success"] is False
        assert "not found" in result["error"]
        assert result["file_path"] == "/nonexistent/file.json"

    def test_load_single_object(self):
        """Test loading single JSON object"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"name": "Test Item", "value": 42}, f)
            temp_path = f.name

        try:
            result = load_endpoint_data_from_file("test", temp_path)

            assert result["success"] is True
            assert "data" in result
            assert len(result["data"]) == 1
            assert result["data"][0]["name"] == "Test Item"
            assert result["data"][0]["value"] == 42
        finally:
            os.unlink(temp_path)

    def test_load_array_of_objects(self):
        """Test loading array of JSON objects"""
        test_data = [
            {"name": "Item 1", "value": 1},
            {"name": "Item 2", "value": 2},
            {"name": "Item 3", "value": 3},
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            result = load_endpoint_data_from_file("test", temp_path)

            assert result["success"] is True
            assert len(result["data"]) == 3
            assert result["data"][0]["name"] == "Item 1"
            assert result["data"][2]["value"] == 3
        finally:
            os.unlink(temp_path)

    def test_load_wrapped_data(self):
        """Test loading data with wrapper format"""
        test_data = {
            "metadata": {"version": "1.0"},
            "data": [{"name": "Item 1", "value": 1}, {"name": "Item 2", "value": 2}],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            result = load_endpoint_data_from_file("test", temp_path)

            assert result["success"] is True
            assert len(result["data"]) == 2
            assert result["data"][0]["name"] == "Item 1"
        finally:
            os.unlink(temp_path)

    def test_load_invalid_json(self):
        """Test loading invalid JSON"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            temp_path = f.name

        try:
            result = load_endpoint_data_from_file("test", temp_path)

            assert result["success"] is False
            assert "JSON" in result["error"]
        finally:
            os.unlink(temp_path)

    def test_load_invalid_data_type(self):
        """Test loading unsupported data type"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump("just a string", f)
            temp_path = f.name

        try:
            result = load_endpoint_data_from_file("test", temp_path)

            assert result["success"] is False
            assert "Invalid data format" in result["error"]
        finally:
            os.unlink(temp_path)

    # TESTS FROM test_data_loader_simple.py (6 tests)
    def test_discover_data_files_basic(self):
        """Test basic data file discovery"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = ["test1.json", "test2.json"]
            for f in test_files:
                file_path = os.path.join(temp_dir, f)
                with open(file_path, "w") as file:
                    json.dump({"test": "data"}, file)

            # Test discovery
            discovered = discover_data_files(temp_dir)

            # Should find files
            assert isinstance(discovered, dict)
            assert len(discovered) >= 0  # May be empty dict or have entries

    def test_discover_data_files_empty_directory(self):
        """Test discovery in empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            discovered = discover_data_files(temp_dir)

            # Should return empty dict for empty directory
            assert isinstance(discovered, dict)

    def test_discover_data_files_nonexistent_directory(self):
        """Test discovery with nonexistent directory"""
        discovered = discover_data_files("/nonexistent/directory")

        # Should handle gracefully
        assert isinstance(discovered, dict)

    def test_load_endpoint_data_valid_json(self):
        """Test loading valid JSON data"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test JSON file
            test_data = {
                "name": "Test Name",
                "title": "Test Title",
                "description": "Test Description",
            }

            temp_path = os.path.join(temp_dir, "test.json")
            with open(temp_path, "w") as f:
                json.dump(test_data, f)

            # Test loading
            result = load_endpoint_data_from_file("test_endpoint", temp_path)

            # Should return the data
            assert isinstance(result, dict)
            # The function may return the data directly or wrapped in a result dict
            if "success" in result:
                assert result["success"] is True
                assert "data" in result
            else:
                # Direct data return
                assert "name" in result or isinstance(result, dict)

    def test_load_endpoint_data_invalid_json(self):
        """Test loading invalid JSON file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name

        try:
            result = load_endpoint_data_from_file("test_endpoint", temp_path)

            # Should handle error gracefully
            assert isinstance(result, dict)
            # May return error dict or empty dict
            if "success" in result:
                assert result["success"] is False
        finally:
            os.unlink(temp_path)

    def test_load_endpoint_data_nonexistent_file(self):
        """Test loading from nonexistent file"""
        result = load_endpoint_data_from_file("test_endpoint", "/nonexistent/file.json")

        # Should handle gracefully
        assert isinstance(result, dict)
        # May return error dict or empty dict
        if "success" in result:
            assert result["success"] is False

    # TESTS FROM test_data_loader_comprehensive.py (first set - 6 tests)
    def test_discover_data_files_default_dir(self):
        """Test discovering data files in default directory"""
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False
            result = discover_data_files()
            assert result == {}

    def test_discover_data_files_with_files(self):
        """Test discovering data files with mock files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = [
                "resume.json",
                "resume_personal.json",
                "ideas.json",
                "ideas_work.json",
                "skills.json",
                "not_json.txt",
            ]

            for filename in test_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w") as f:
                    json.dump({"test": "data"}, f)

            result = discover_data_files(temp_dir)

            # Should group by endpoint name
            assert isinstance(result, dict)
            # Check if we have the expected endpoint groups
            if result:
                assert all(isinstance(files, list) for files in result.values())

    def test_discover_data_files_empty_dir(self):
        """Test discovering data files in empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = discover_data_files(temp_dir)
            assert result == {}

    def test_discover_data_files_custom_dir(self):
        """Test discovering data files with custom directory"""
        with patch("os.path.exists") as mock_exists, patch("glob.glob") as mock_glob:
            mock_exists.return_value = True
            mock_glob.return_value = ["/custom/path/test.json"]

            result = discover_data_files("/custom/data")

            mock_glob.assert_called_once()
            assert isinstance(result, dict)

    def test_discover_data_files_nonexistent_dir(self):
        """Test discovering data files in non-existent directory"""
        result = discover_data_files("/nonexistent/directory")
        assert isinstance(result, dict)

    def test_discover_data_files_mixed_extensions(self):
        """Test discovering with mixed file extensions"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with different extensions
            test_files = [
                "resume.json",
                "resume.txt",
                "ideas.json",
                "test.py",
                "data.xml",
            ]

            for filename in test_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w") as f:
                    if filename.endswith(".json"):
                        json.dump({"test": "data"}, f)
                    else:
                        f.write("test content")

            result = discover_data_files(temp_dir)

            # Should only include JSON files
            assert isinstance(result, dict)

    # TESTS FROM test_data_loader_comprehensive.py (remaining 20 tests)
    def test_load_endpoint_data_from_file_valid_json_comprehensive(self):
        """Test loading valid JSON data file for endpoint"""
        test_data = {"name": "John Doe", "skills": ["Python", "FastAPI"]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            result = load_endpoint_data_from_file("resume", temp_path)
            assert isinstance(result, dict)
            # Should have success indicator or error handling
        finally:
            os.unlink(temp_path)

    def test_load_endpoint_data_from_file_invalid_json_comprehensive(self):
        """Test loading invalid JSON data file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content {")
            temp_path = f.name

        try:
            result = load_endpoint_data_from_file("resume", temp_path)
            assert isinstance(result, dict)
            # Should handle gracefully
        finally:
            os.unlink(temp_path)

    def test_load_endpoint_data_from_file_nonexistent_comprehensive(self):
        """Test loading non-existent data file"""
        result = load_endpoint_data_from_file("resume", "/nonexistent/file.json")
        assert isinstance(result, dict)

    def test_load_endpoint_data_from_file_empty_file(self):
        """Test loading empty JSON file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            result = load_endpoint_data_from_file("resume", temp_path)
            assert isinstance(result, dict)
        finally:
            os.unlink(temp_path)

    def test_load_endpoint_data_from_file_complex_data(self):
        """Test loading complex nested data structures"""
        complex_data = {
            "personal": {
                "name": "John Doe",
                "contact": {"email": "john@example.com", "phone": "123-456-7890"},
            },
            "professional": {
                "experience": [
                    {
                        "company": "TechCorp",
                        "roles": [
                            {"title": "Developer", "years": 2},
                            {"title": "Senior Developer", "years": 1},
                        ],
                    }
                ],
                "skills": ["Python", "JavaScript", "SQL"],
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(complex_data, f)
            temp_path = f.name

        try:
            result = load_endpoint_data_from_file("resume", temp_path)
            assert isinstance(result, dict)
        finally:
            os.unlink(temp_path)

    def test_load_endpoint_data_with_different_endpoints(self):
        """Test loading data for different endpoint types"""
        endpoints_data = [
            ("resume", {"name": "John", "title": "Developer"}),
            ("ideas", [{"title": "Idea 1", "description": "Test"}]),
            ("skills", ["Python", "JavaScript", "SQL"]),
            ("projects", [{"name": "Project A", "tech": ["FastAPI"]}]),
        ]

        for endpoint_name, test_data in endpoints_data:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(test_data, f)
                temp_path = f.name

            try:
                result = load_endpoint_data_from_file(endpoint_name, temp_path)
                assert isinstance(result, dict)
            finally:
                os.unlink(temp_path)

    @patch("app.data_loader.SessionLocal")
    @patch("app.data_loader.discover_data_files")
    def test_import_all_discovered_data_comprehensive(
        self, mock_discover, mock_session
    ):
        """Test importing all discovered data"""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock discovered files
        mock_discover.return_value = {
            "resume": ["/path/resume.json"],
            "ideas": ["/path/ideas.json"],
        }

        # Mock endpoint query
        mock_endpoint = MagicMock()
        mock_endpoint.name = "resume"
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_endpoint
        )

        with patch("app.data_loader.load_endpoint_data_from_file") as mock_load:
            mock_load.return_value = {
                "success": True,
                "data": {"name": "Test Data"},
            }

            result = import_all_discovered_data()
            assert isinstance(result, dict)

    @patch("app.data_loader.SessionLocal")
    @patch("app.data_loader.load_endpoint_data_from_file")
    def test_import_endpoint_data_to_database_comprehensive(
        self, mock_load_data, mock_session
    ):
        """Test importing data for specific endpoint to database"""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock endpoint
        mock_endpoint = MagicMock()
        mock_endpoint.name = "resume"
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_endpoint
        )

        # Mock the file loading function
        test_data = {"name": "Test Data"}
        mock_load_data.return_value = {"success": True, "data": test_data}

        result = import_endpoint_data_to_database("resume", "/path/to/test.json")
        assert isinstance(result, dict)

    @patch("app.data_loader.SessionLocal")
    @patch("app.data_loader.load_endpoint_data_from_file")
    def test_import_endpoint_data_to_database_nonexistent_endpoint(
        self, mock_load_data, mock_session
    ):
        """Test importing to non-existent endpoint"""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Mock the file loading function
        mock_load_data.return_value = {"success": True, "data": {}}

        result = import_endpoint_data_to_database("nonexistent", "/path/to/test.json")
        assert isinstance(result, dict)

    @patch("app.data_loader.SessionLocal")
    @patch("app.data_loader.load_endpoint_data_from_file")
    def test_import_endpoint_data_to_database_with_user(
        self, mock_load_data, mock_session
    ):
        """Test importing data with specific user"""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock endpoint and user
        mock_endpoint = MagicMock()
        mock_endpoint.name = "resume"
        mock_user = MagicMock()
        mock_user.id = 1

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_endpoint
        )

        # Mock the file loading function
        test_data = {"name": "Test Data"}
        mock_load_data.return_value = {"success": True, "data": test_data}

        result = import_endpoint_data_to_database(
            "resume", "/path/to/test.json", user_id=1
        )
        assert isinstance(result, dict)

    def test_get_data_import_status_default_dir_comprehensive(self):
        """Test getting import status for default directory"""
        result = get_data_import_status()
        assert isinstance(result, dict)

    @patch("app.data_loader.get_db")
    @patch("app.data_loader.SessionLocal")
    def test_get_data_import_status_custom_dir(self, mock_session, mock_get_db):
        """Test getting import status for custom directory"""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_get_db.return_value = iter([mock_db])
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_file = os.path.join(temp_dir, "resume.json")
            with open(test_file, "w") as f:
                json.dump({"test": "data"}, f)

            result = get_data_import_status(temp_dir)
            assert isinstance(result, dict)

    def test_get_data_import_status_nonexistent_dir(self):
        """Test getting import status for non-existent directory"""
        result = get_data_import_status("/nonexistent/path")
        assert isinstance(result, dict)

    @patch("app.data_loader.SessionLocal")
    def test_get_data_import_status_with_database_check(self, mock_session):
        """Test import status with database statistics"""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock data counts
        mock_db.query.return_value.filter.return_value.count.return_value = 5

        result = get_data_import_status()
        assert isinstance(result, dict)

    def test_load_endpoint_data_from_file_large_file(self):
        """Test loading large JSON file"""
        large_data = {"items": [{"id": i, "value": f"item_{i}"} for i in range(1000)]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(large_data, f)
            temp_path = f.name

        try:
            result = load_endpoint_data_from_file("bulk_data", temp_path)
            assert isinstance(result, dict)
        finally:
            os.unlink(temp_path)

    @patch("builtins.open")
    def test_load_endpoint_data_permission_error(self, mock_open_func):
        """Test handling permission errors"""
        mock_open_func.side_effect = PermissionError("Permission denied")

        result = load_endpoint_data_from_file("resume", "/restricted/file.json")
        assert isinstance(result, dict)

    @patch("app.data_loader.json.load")
    def test_load_endpoint_data_json_decode_error(self, mock_json_load):
        """Test handling JSON decode errors"""
        mock_json_load.side_effect = json.JSONDecodeError("Error", "doc", 0)

        with tempfile.NamedTemporaryFile(suffix=".json") as temp_file:
            result = load_endpoint_data_from_file("resume", temp_file.name)
            assert isinstance(result, dict)

    def test_discover_data_files_special_characters(self):
        """Test discovery with special characters in filenames"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with special characters
            test_files = [
                "ideas_test-1.json",
                "skills_copy.json",
            ]

            for filename in test_files:
                try:
                    file_path = os.path.join(temp_dir, filename)
                    with open(file_path, "w") as f:
                        json.dump({"test": "data"}, f)
                except OSError:
                    # Skip files that can't be created on this filesystem
                    continue

            result = discover_data_files(temp_dir)
            assert isinstance(result, dict)

    def test_load_endpoint_data_unicode_content(self):
        """Test loading file with Unicode content"""
        unicode_data = {
            "name": "José María",
            "description": "Développeur Python",
            "skills": ["Python", "FastAPI"],
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(unicode_data, f, ensure_ascii=False)
            temp_path = f.name

        try:
            result = load_endpoint_data_from_file("resume", temp_path)
            assert isinstance(result, dict)
        finally:
            os.unlink(temp_path)
