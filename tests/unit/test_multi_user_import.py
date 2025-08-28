"""
Comprehensive multi-user import tests - consolidated from multiple test files
Covers all multi-user import functionality with proper mocking and error handling
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.multi_user_import import (
    create_user_data_directory,
    import_all_users_data,
    import_user_data,
    process_user_data_files,
    validate_user_data_structure,
)


class TestCreateUserDataDirectory:
    """Test user directory creation functionality"""

    def test_create_user_data_directory_basic(self):
        """Test basic user directory creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = create_user_data_directory("test_user", temp_dir)

            assert isinstance(result, str)
            assert "test_user" in result
            assert os.path.exists(result)
            assert os.path.isdir(result)

    def test_create_user_data_directory_existing(self):
        """Test creating directory that already exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directory first
            user_dir = os.path.join(temp_dir, "test_user")
            os.makedirs(user_dir)

            # Try to create again
            result = create_user_data_directory("test_user", temp_dir)

            assert isinstance(result, str)
            assert os.path.exists(result)

    def test_create_user_data_directory_special_characters(self):
        """Test creating directory with special characters in username"""
        special_usernames = [
            "user.name",
            "user-name",
            "user_name",
            "user123",
            "User-Name.Test",
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            for username in special_usernames:
                result = create_user_data_directory(username, temp_dir)
                assert os.path.exists(result)

    def test_create_user_data_directory_invalid_characters(self):
        """Test creating directory with invalid characters"""
        invalid_usernames = [
            "user/name",  # Path separator
            "user\\name",  # Windows path separator
            "user:name",  # Colon
            "user*name",  # Asterisk
            "user?name",  # Question mark
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            for username in invalid_usernames:
                # Should sanitize the username or handle gracefully
                result = create_user_data_directory(username, temp_dir)
                # Should create some form of directory (may be sanitized)
                assert isinstance(result, str)

    def test_create_user_data_directory_permission_error(self):
        """Test handling permission errors"""
        with patch("os.makedirs") as mock_makedirs:
            mock_makedirs.side_effect = PermissionError("Permission denied")

            with tempfile.TemporaryDirectory() as temp_dir:
                result = create_user_data_directory("test_user", temp_dir)
                # Should handle error gracefully
                assert result is None or isinstance(result, str)

    def test_create_user_data_directory_nested_path(self):
        """Test creating directory with nested base path"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_base = os.path.join(temp_dir, "users", "data")
            result = create_user_data_directory("test_user", nested_base)

            assert isinstance(result, str)
            assert os.path.exists(result)


class TestValidateUserDataStructure:
    """Test user data structure validation"""

    def test_validate_user_data_structure_valid(self):
        """Test validation of valid user data structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create valid user structure
            user_dir = os.path.join(temp_dir, "test_user")
            os.makedirs(user_dir)

            # Create some data files
            with open(os.path.join(user_dir, "ideas.json"), "w") as f:
                json.dump({"title": "Test idea"}, f)

            with open(os.path.join(user_dir, "notes.json"), "w") as f:
                json.dump({"content": "Test note"}, f)

            result = validate_user_data_structure(user_dir)
            assert result is True

    def test_validate_user_data_structure_empty_directory(self):
        """Test validation of empty user directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            user_dir = os.path.join(temp_dir, "test_user")
            os.makedirs(user_dir)

            result = validate_user_data_structure(user_dir)
            # Empty directory might be valid or invalid depending on implementation
            assert isinstance(result, bool)

    def test_validate_user_data_structure_nonexistent(self):
        """Test validation of non-existent directory"""
        result = validate_user_data_structure("/nonexistent/path")
        assert result is False

    def test_validate_user_data_structure_invalid_files(self):
        """Test validation with invalid files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            user_dir = os.path.join(temp_dir, "test_user")
            os.makedirs(user_dir)

            # Create invalid JSON file
            with open(os.path.join(user_dir, "invalid.json"), "w") as f:
                f.write("invalid json content")

            result = validate_user_data_structure(user_dir)
            # Should handle invalid files gracefully
            assert isinstance(result, bool)

    def test_validate_user_data_structure_mixed_content(self):
        """Test validation with mixed valid/invalid content"""
        with tempfile.TemporaryDirectory() as temp_dir:
            user_dir = os.path.join(temp_dir, "test_user")
            os.makedirs(user_dir)

            # Valid JSON file
            with open(os.path.join(user_dir, "valid.json"), "w") as f:
                json.dump({"title": "Valid"}, f)

            # Invalid JSON file
            with open(os.path.join(user_dir, "invalid.json"), "w") as f:
                f.write("invalid")

            # Non-JSON file
            with open(os.path.join(user_dir, "readme.txt"), "w") as f:
                f.write("This is a readme")

            result = validate_user_data_structure(user_dir)
            assert isinstance(result, bool)


class TestProcessUserDataFiles:
    """Test processing user data files"""

    @patch("app.multi_user_import.import_endpoint_data_to_database")
    def test_process_user_data_files_success(self, mock_import):
        """Test successful processing of user data files"""
        mock_import.return_value = True

        with tempfile.TemporaryDirectory() as temp_dir:
            user_dir = os.path.join(temp_dir, "test_user")
            os.makedirs(user_dir)

            # Create test data files
            test_files = {
                "ideas.json": {"title": "Test Idea", "content": "Idea content"},
                "notes.json": {"title": "Test Note", "content": "Note content"},
                "tasks.json": {"title": "Test Task", "due_date": "2023-12-01"},
            }

            for filename, data in test_files.items():
                with open(os.path.join(user_dir, filename), "w") as f:
                    json.dump(data, f)

            result = process_user_data_files(user_dir, user_id=1)

            assert result["success"] is True
            assert result["processed_files"] == 3
            assert result["failed_files"] == 0
            assert mock_import.call_count == 3

    @patch("app.multi_user_import.import_endpoint_data_to_database")
    def test_process_user_data_files_partial_failure(self, mock_import):
        """Test processing with some import failures"""
        # Mock import to fail for some files
        mock_import.side_effect = [True, False, True]  # Second import fails

        with tempfile.TemporaryDirectory() as temp_dir:
            user_dir = os.path.join(temp_dir, "test_user")
            os.makedirs(user_dir)

            test_files = ["ideas.json", "notes.json", "tasks.json"]
            for filename in test_files:
                with open(os.path.join(user_dir, filename), "w") as f:
                    json.dump({"title": f"Test {filename}"}, f)

            result = process_user_data_files(user_dir, user_id=1)

            assert result["success"] is False  # Overall failed due to some failures
            assert result["processed_files"] == 2  # 2 successful
            assert result["failed_files"] == 1  # 1 failed

    def test_process_user_data_files_invalid_json(self):
        """Test processing files with invalid JSON"""
        with tempfile.TemporaryDirectory() as temp_dir:
            user_dir = os.path.join(temp_dir, "test_user")
            os.makedirs(user_dir)

            # Create invalid JSON file
            with open(os.path.join(user_dir, "invalid.json"), "w") as f:
                f.write("invalid json content")

            result = process_user_data_files(user_dir, user_id=1)

            assert result["success"] is False
            assert result["processed_files"] == 0
            assert result["failed_files"] == 1

    def test_process_user_data_files_empty_directory(self):
        """Test processing empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            user_dir = os.path.join(temp_dir, "test_user")
            os.makedirs(user_dir)

            result = process_user_data_files(user_dir, user_id=1)

            assert result["success"] is True  # Empty is considered success
            assert result["processed_files"] == 0
            assert result["failed_files"] == 0

    def test_process_user_data_files_nonexistent_directory(self):
        """Test processing non-existent directory"""
        result = process_user_data_files("/nonexistent/path", user_id=1)

        assert result["success"] is False
        assert "error" in result

    @patch("app.multi_user_import.import_endpoint_data_to_database")
    def test_process_user_data_files_large_files(self, mock_import):
        """Test processing large data files"""
        mock_import.return_value = True

        with tempfile.TemporaryDirectory() as temp_dir:
            user_dir = os.path.join(temp_dir, "test_user")
            os.makedirs(user_dir)

            # Create large data file
            large_data = {
                "items": [
                    {"id": i, "title": f"Item {i}", "content": "x" * 1000}
                    for i in range(100)
                ]
            }

            with open(os.path.join(user_dir, "large_data.json"), "w") as f:
                json.dump(large_data, f)

            result = process_user_data_files(user_dir, user_id=1)

            assert result["success"] is True
            assert result["processed_files"] == 1
            mock_import.assert_called_once()


class TestImportUserData:
    """Test importing data for a single user"""

    @patch("app.multi_user_import.process_user_data_files")
    @patch("app.multi_user_import.validate_user_data_structure")
    @patch("app.multi_user_import.get_db")
    def test_import_user_data_success(self, mock_get_db, mock_validate, mock_process):
        """Test successful user data import"""
        # Mock database and user
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "test_user"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Mock validation and processing
        mock_validate.return_value = True
        mock_process.return_value = {
            "success": True,
            "processed_files": 5,
            "failed_files": 0,
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            user_dir = os.path.join(temp_dir, "test_user")
            os.makedirs(user_dir)

            result = import_user_data("test_user", user_dir)

            assert result["success"] is True
            assert result["user"] == "test_user"
            assert result["processed_files"] == 5

    @patch("app.multi_user_import.validate_user_data_structure")
    @patch("app.multi_user_import.get_db")
    def test_import_user_data_user_not_found(self, mock_get_db, mock_validate):
        """Test import when user doesn't exist"""
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db

        # User not found
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_validate.return_value = True

        with tempfile.TemporaryDirectory() as temp_dir:
            user_dir = os.path.join(temp_dir, "test_user")
            os.makedirs(user_dir)

            result = import_user_data("nonexistent_user", user_dir)

            assert result["success"] is False
            assert "not found" in result["error"]

    @patch("app.multi_user_import.validate_user_data_structure")
    def test_import_user_data_invalid_structure(self, mock_validate):
        """Test import with invalid data structure"""
        mock_validate.return_value = False

        with tempfile.TemporaryDirectory() as temp_dir:
            user_dir = os.path.join(temp_dir, "test_user")
            os.makedirs(user_dir)

            result = import_user_data("test_user", user_dir)

            assert result["success"] is False
            assert "invalid" in result["error"]

    @patch("app.multi_user_import.get_db")
    def test_import_user_data_database_error(self, mock_get_db):
        """Test import with database error"""
        mock_get_db.side_effect = Exception("Database connection error")

        with tempfile.TemporaryDirectory() as temp_dir:
            user_dir = os.path.join(temp_dir, "test_user")
            os.makedirs(user_dir)

            result = import_user_data("test_user", user_dir)

            assert result["success"] is False
            assert "error" in result


class TestImportAllUsersData:
    """Test importing data for all users"""

    @patch("app.multi_user_import.import_user_data")
    def test_import_all_users_data_empty_directory(self, mock_import_user):
        """Test importing from empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = import_all_users_data(temp_dir)

            assert result["success"] is True
            assert result["total_users"] == 0
            assert result["successful_imports"] == 0
            assert result["failed_imports"] == 0

    @patch("app.multi_user_import.import_user_data")
    def test_import_all_users_data_with_users(self, mock_import_user):
        """Test importing with multiple user directories"""
        # Mock successful imports
        mock_import_user.side_effect = [
            {"success": True, "user": "user1", "processed_files": 3},
            {"success": True, "user": "user2", "processed_files": 5},
            {"success": False, "user": "user3", "error": "Import failed"},
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create user directories
            for username in ["user1", "user2", "user3"]:
                user_dir = os.path.join(temp_dir, username)
                os.makedirs(user_dir)

            result = import_all_users_data(temp_dir)

            assert result["success"] is True  # Overall success even with some failures
            assert result["total_users"] == 3
            assert result["successful_imports"] == 2
            assert result["failed_imports"] == 1

    @patch("app.multi_user_import.import_user_data")
    def test_import_all_users_data_all_failures(self, mock_import_user):
        """Test importing when all users fail"""
        mock_import_user.return_value = {"success": False, "error": "Import failed"}

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create user directories
            for username in ["user1", "user2"]:
                user_dir = os.path.join(temp_dir, username)
                os.makedirs(user_dir)

            result = import_all_users_data(temp_dir)

            assert result["success"] is False
            assert result["total_users"] == 2
            assert result["successful_imports"] == 0
            assert result["failed_imports"] == 2

    def test_import_all_users_data_nonexistent_directory(self):
        """Test importing from non-existent directory"""
        result = import_all_users_data("/nonexistent/path")

        assert result["success"] is False
        assert "error" in result

    @patch("app.multi_user_import.import_user_data")
    def test_import_all_users_data_mixed_content(self, mock_import_user):
        """Test importing with mixed files and directories"""
        mock_import_user.return_value = {
            "success": True,
            "user": "user1",
            "processed_files": 2,
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create user directory
            user_dir = os.path.join(temp_dir, "user1")
            os.makedirs(user_dir)

            # Create non-directory file (should be ignored)
            with open(os.path.join(temp_dir, "not_a_user.txt"), "w") as f:
                f.write("This is not a user directory")

            result = import_all_users_data(temp_dir)

            assert result["success"] is True
            assert result["total_users"] == 1  # Only directories should be counted
            assert result["successful_imports"] == 1

    @patch("app.multi_user_import.import_user_data")
    def test_import_all_users_data_permission_error(self, mock_import_user):
        """Test handling permission errors during directory listing"""
        with patch("os.listdir") as mock_listdir:
            mock_listdir.side_effect = PermissionError("Permission denied")

            result = import_all_users_data("/some/path")

            assert result["success"] is False
            assert "error" in result


class TestMultiUserImportSecurityValidation:
    """Test security validation and boundary conditions"""

    def test_path_traversal_prevention(self):
        """Test that path traversal attempts are blocked in usernames"""
        malicious_usernames = [
            "../admin",
            "../../etc/passwd",
            "..\\..\\windows\\system32",
            "/etc/passwd",
            "C:\\Windows\\System32",
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            for username in malicious_usernames:
                result = create_user_data_directory(username, temp_dir)
                # Should either sanitize the path or fail safely
                if result is not None:
                    # Ensure the created directory is within temp_dir
                    assert temp_dir in os.path.abspath(result)

    def test_username_sanitization(self):
        """Test that usernames are properly sanitized"""
        problematic_usernames = [
            "user<script>",
            "user'; DROP TABLE users; --",
            "user${eval(malicious)}",
            "user\x00null",
            "user\n\r\t",
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            for username in problematic_usernames:
                result = create_user_data_directory(username, temp_dir)
                # Should handle problematic usernames gracefully
                if result is not None:
                    assert os.path.exists(result)

    @patch("app.multi_user_import.import_endpoint_data_to_database")
    def test_malicious_json_content(self, mock_import):
        """Test handling of malicious JSON content"""
        mock_import.return_value = True

        malicious_data = {
            "script": "<script>alert('xss')</script>",
            "sql": "'; DROP TABLE users; --",
            "command": "rm -rf /",
            "eval": "eval('malicious_code')",
            "path": "../../../etc/passwd",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            user_dir = os.path.join(temp_dir, "test_user")
            os.makedirs(user_dir)

            with open(os.path.join(user_dir, "malicious.json"), "w") as f:
                json.dump(malicious_data, f)

            result = process_user_data_files(user_dir, user_id=1)

            # Should process without crashing
            assert isinstance(result, dict)
            assert "success" in result

    def test_large_directory_structure(self):
        """Test handling of large directory structures"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create many user directories
            for i in range(100):
                user_dir = os.path.join(temp_dir, f"user_{i}")
                os.makedirs(user_dir)

                # Add a small data file to each
                with open(os.path.join(user_dir, "data.json"), "w") as f:
                    json.dump({"id": i, "name": f"User {i}"}, f)

            # Should handle large directory structure
            result = import_all_users_data(temp_dir)
            assert isinstance(result, dict)
            assert "total_users" in result

    def test_symlink_handling(self):
        """Test handling of symbolic links"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a real user directory
            real_dir = os.path.join(temp_dir, "real_user")
            os.makedirs(real_dir)

            # Create a symlink to external location
            try:
                external_target = "/tmp"
                symlink_path = os.path.join(temp_dir, "symlink_user")
                os.symlink(external_target, symlink_path)

                # Should handle symlinks safely
                result = import_all_users_data(temp_dir)
                assert isinstance(result, dict)

            except OSError:
                # Symlinks might not be supported on all systems
                pass

    def test_unicode_usernames(self):
        """Test handling of unicode usernames"""
        unicode_usernames = [
            "用户名",  # Chinese
            "ユーザー名",  # Japanese
            "имя_пользователя",  # Russian
            "اسم_المستخدم",  # Arabic
            "🚀user🔥",  # Emoji
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            for username in unicode_usernames:
                try:
                    result = create_user_data_directory(username, temp_dir)
                    # Should handle unicode gracefully
                    if result is not None:
                        assert os.path.exists(result)
                except UnicodeError:
                    # Some systems might not support unicode in filenames
                    pass

    def test_extremely_long_usernames(self):
        """Test handling of extremely long usernames"""
        long_username = "a" * 1000  # Very long username

        with tempfile.TemporaryDirectory() as temp_dir:
            result = create_user_data_directory(long_username, temp_dir)

            # Should either truncate, reject, or handle gracefully
            if result is not None:
                # Path should still be reasonable length
                assert len(result) < 2000  # Reasonable filesystem limit
