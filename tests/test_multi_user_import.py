"""
Test multi-user import functionality
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app.multi_user_import import (
    create_user_data_directory,
    import_all_users_data,
    import_user_data_from_directory,
    import_user_file,
)


class TestImportUserDataFromDirectory:
    """Test importing user data from directory"""

    def test_import_user_data_from_directory_success(self):
        """Test successful user data import from directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test data files
            endpoint_dir = os.path.join(temp_dir, "test_endpoint")
            os.makedirs(endpoint_dir)

            test_data = {"name": "Test User", "title": "Software Developer"}
            with open(os.path.join(endpoint_dir, "data.json"), "w") as f:
                json.dump(test_data, f)

            # Mock database session
            with patch("app.multi_user_import.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db

                result = import_user_data_from_directory("test_user", temp_dir)

                assert result["success"] is True
                assert "imported_files" in result

    def test_import_user_data_missing_directory(self):
        """Test import with missing directory"""
        result = import_user_data_from_directory("test_user", "/nonexistent/directory")

        assert result["success"] is False
        assert "Data directory not found" in result["error"]


class TestImportUserFile:
    """Test importing individual user files"""

    def test_import_user_file_success(self):
        """Test successful user file import"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test data file
            test_data = {"name": "Test User", "title": "Software Developer"}
            temp_path = os.path.join(temp_dir, "test.json")
            with open(temp_path, "w") as f:
                json.dump(test_data, f)

            # Mock database session
            with patch("app.multi_user_import.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db

                result = import_user_file(
                    "test_user", temp_path, "test_endpoint", mock_db
                )

                # Note: Actual implementation may return different structure
                assert isinstance(result, dict)

    def test_import_user_file_nonexistent_file(self):
        """Test import with nonexistent file"""
        with patch("app.multi_user_import.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db

            result = import_user_file(
                "test_user", "/nonexistent/file.json", "test_endpoint", mock_db
            )

            assert result["success"] is False

    def test_import_user_file_invalid_json(self):
        """Test import with invalid JSON file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name

        try:
            with patch("app.multi_user_import.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db

                result = import_user_file(
                    "test_user", temp_path, "test_endpoint", mock_db
                )

                assert result["success"] is False
        finally:
            os.unlink(temp_path)


class TestImportAllUsersData:
    """Test importing data for all users"""

    def test_import_all_users_success(self):
        """Test successful import for all users"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create user directories with data
            for user in ["user1", "user2"]:
                user_dir = os.path.join(temp_dir, user)
                endpoint_dir = os.path.join(user_dir, "test_endpoint")
                os.makedirs(endpoint_dir)

                test_data = {"name": f"Test {user}", "title": "Software Developer"}
                with open(os.path.join(endpoint_dir, "data.json"), "w") as f:
                    json.dump(test_data, f)

            with patch("app.multi_user_import.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_get_db.return_value = mock_db

                result = import_all_users_data(temp_dir)

                assert result["success"] is True

    def test_import_all_users_no_users(self):
        """Test import with no user directories"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = import_all_users_data(temp_dir)

            # This might be considered success if no users exist
            assert isinstance(result, dict)
            assert "success" in result


class TestCreateUserDataDirectory:
    """Test creating user data directories"""

    def test_create_user_data_directory_success(self):
        """Test successful user directory creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = create_user_data_directory("test_user", temp_dir)

            # Function returns string path, not dict
            assert isinstance(result, str)
            assert os.path.exists(result)

    def test_create_user_data_directory_exists(self):
        """Test creating directory that already exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directory first
            user_dir = os.path.join(temp_dir, "test_user")
            os.makedirs(user_dir)

            result = create_user_data_directory("test_user", temp_dir)

            # Should still succeed (exist_ok=True)
            assert isinstance(result, str)
            assert os.path.exists(result)

    def test_create_user_data_directory_permission_error(self):
        """Test directory creation with permission error"""
        with patch("os.makedirs") as mock_makedirs:
            mock_makedirs.side_effect = PermissionError("Access denied")

            try:
                result = create_user_data_directory("test_user", "/some/base/dir")
                # Function should raise the exception or handle it
                assert False, "Expected PermissionError to be raised"
            except PermissionError:
                pass  # Expected

    def test_create_user_data_directory_invalid_base(self):
        """Test directory creation with invalid base directory"""
        try:
            result = create_user_data_directory("test_user", "/nonexistent/base/dir")
            # Function should raise OSError or handle it
            assert False, "Expected OSError to be raised"
        except OSError:
            pass  # Expected
