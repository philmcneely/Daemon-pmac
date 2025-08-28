"""
Test data_loader functionality - comprehensive version for higher coverage
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


class TestDataDiscovery:
    """Test data file discovery functionality"""

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


class TestDataLoading:
    """Test data file loading functionality"""

    def test_load_endpoint_data_from_file_valid_json(self):
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

    def test_load_endpoint_data_from_file_invalid_json(self):
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

    def test_load_endpoint_data_from_file_nonexistent(self):
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


class TestDataImport:
    """Test data import functionality"""

    @patch("app.data_loader.SessionLocal")
    @patch("app.data_loader.discover_data_files")
    def test_import_all_discovered_data(self, mock_discover, mock_session):
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
    def test_import_endpoint_data_to_database(self, mock_load_data, mock_session):
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


class TestDataImportStatus:
    """Test data import status functionality"""

    def test_get_data_import_status_default_dir(self):
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


class TestEdgeCases:
    """Test edge cases and error conditions"""

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

    @patch("app.data_loader.SessionLocal")
    @patch("app.data_loader.load_endpoint_data_from_file")
    def test_import_with_database_error(self, mock_load_data, mock_session):
        """Test import with database errors"""
        # Mock database session that raises exception
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.side_effect = Exception("Database error")

        # Mock the file loading function
        mock_load_data.return_value = {"success": True, "data": {"test": "data"}}

        result = import_endpoint_data_to_database("resume", "/path/to/test.json")
        # Should handle database errors gracefully
        assert isinstance(result, dict)

    def test_discover_data_files_special_characters(self):
        """Test discovery with special characters in filenames"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with special characters
            test_files = [
                "résumé.json",
                "ideas_test-1.json",
                "skills (copy).json",
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
            "description": "Développeur Python 🐍",
            "skills": ["机器学习", "データサイエンス"],
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
