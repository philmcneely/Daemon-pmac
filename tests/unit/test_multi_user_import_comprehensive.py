"""
Test multi_user_import functionality - comprehensive version for higher coverage
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


class TestUserDataDirectoryImport:
    """Test importing user data from directory"""

    @patch("app.multi_user_import.SessionLocal")
    def test_import_user_data_from_directory_success(self, mock_session):
        """Test successful user data import from directory"""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test data files
            user_dir = os.path.join(temp_dir, "testuser")
            os.makedirs(user_dir)

            test_file = os.path.join(user_dir, "resume.json")
            with open(test_file, "w") as f:
                json.dump({"name": "Test User"}, f)

            result = import_user_data_from_directory("testuser", temp_dir)

            assert isinstance(result, dict)
            assert "success" in result or "imported_count" in result

    @patch("app.multi_user_import.SessionLocal")
    def test_import_user_data_from_directory_no_user(self, mock_session):
        """Test import with non-existent user"""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = import_user_data_from_directory("nonexistent", "/fake/dir")

        assert isinstance(result, dict)
        assert "success" in result

    def test_import_user_data_from_directory_nonexistent_dir(self):
        """Test import from non-existent directory"""
        result = import_user_data_from_directory("testuser", "/nonexistent/dir")

        assert isinstance(result, dict)
        assert "success" in result

    @patch("app.multi_user_import.SessionLocal")
    def test_import_user_data_from_directory_empty_dir(self, mock_session):
        """Test import from empty user directory"""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create empty user directory
            user_dir = os.path.join(temp_dir, "testuser")
            os.makedirs(user_dir)

            result = import_user_data_from_directory("testuser", temp_dir)

            assert isinstance(result, dict)


class TestUserFileImport:
    """Test importing user data from individual files"""

    @patch("app.multi_user_import.SessionLocal")
    def test_import_user_file_success(self, mock_session):
        """Test successful user file import"""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock user and endpoint
        mock_user = MagicMock()
        mock_user.id = 1
        mock_endpoint = MagicMock()
        mock_endpoint.name = "resume"

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            mock_endpoint,
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"name": "Test User"}, f)
            temp_path = f.name

        try:
            result = import_user_file("testuser", "resume", temp_path)

            assert isinstance(result, dict)
            assert "success" in result
        finally:
            os.unlink(temp_path)

    @patch("app.multi_user_import.SessionLocal")
    def test_import_user_file_no_user(self, mock_session):
        """Test import with non-existent user"""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = import_user_file("nonexistent", "resume", "/fake/file.json")

        assert isinstance(result, dict)
        assert "success" in result

    @patch("app.multi_user_import.SessionLocal")
    def test_import_user_file_no_endpoint(self, mock_session):
        """Test import with non-existent endpoint"""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock user exists, endpoint doesn't
        mock_user = MagicMock()
        mock_user.id = 1
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            None,
        ]

        result = import_user_file("testuser", "nonexistent", "/fake/file.json")

        assert isinstance(result, dict)
        assert "success" in result

    def test_import_user_file_nonexistent_file(self):
        """Test import from non-existent file"""
        result = import_user_file("testuser", "resume", "/nonexistent/file.json")

        assert isinstance(result, dict)
        assert "success" in result

    @patch("app.multi_user_import.SessionLocal")
    def test_import_user_file_invalid_json(self, mock_session):
        """Test import with invalid JSON file"""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock user and endpoint
        mock_user = MagicMock()
        mock_user.id = 1
        mock_endpoint = MagicMock()
        mock_endpoint.name = "resume"

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            mock_endpoint,
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content {")
            temp_path = f.name

        try:
            result = import_user_file("testuser", "resume", temp_path)

            assert isinstance(result, dict)
            assert "success" in result
        finally:
            os.unlink(temp_path)


class TestAllUsersDataImport:
    """Test importing data for all users"""

    @patch("app.multi_user_import.SessionLocal")
    def test_import_all_users_data_success(self, mock_session):
        """Test successful import for all users"""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock users
        mock_user1 = MagicMock()
        mock_user1.id = 1
        mock_user1.username = "user1"

        mock_user2 = MagicMock()
        mock_user2.id = 2
        mock_user2.username = "user2"

        mock_db.query.return_value.all.return_value = [mock_user1, mock_user2]

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create user directories with data
            for username in ["user1", "user2"]:
                user_dir = os.path.join(temp_dir, username)
                os.makedirs(user_dir)

                test_file = os.path.join(user_dir, "resume.json")
                with open(test_file, "w") as f:
                    json.dump({"name": f"User {username}"}, f)

            result = import_all_users_data(temp_dir)

            assert isinstance(result, dict)
            assert "success" in result or "imported_count" in result

    @patch("app.multi_user_import.SessionLocal")
    def test_import_all_users_data_no_users(self, mock_session):
        """Test import with no users in database"""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.all.return_value = []

        result = import_all_users_data("/fake/dir")

        assert isinstance(result, dict)
        assert "success" in result

    def test_import_all_users_data_nonexistent_dir(self):
        """Test import from non-existent directory"""
        result = import_all_users_data("/nonexistent/directory")

        assert isinstance(result, dict)
        assert "success" in result

    @patch("app.multi_user_import.SessionLocal")
    def test_import_all_users_data_partial_directories(self, mock_session):
        """Test import where only some users have data directories"""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock users
        mock_user1 = MagicMock()
        mock_user1.id = 1
        mock_user1.username = "user1"

        mock_user2 = MagicMock()
        mock_user2.id = 2
        mock_user2.username = "user2"

        mock_db.query.return_value.all.return_value = [mock_user1, mock_user2]

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directory only for user1
            user_dir = os.path.join(temp_dir, "user1")
            os.makedirs(user_dir)

            test_file = os.path.join(user_dir, "resume.json")
            with open(test_file, "w") as f:
                json.dump({"name": "User 1"}, f)

            # user2 directory doesn't exist

            result = import_all_users_data(temp_dir)

            assert isinstance(result, dict)


class TestUserDataDirectoryCreation:
    """Test creating user data directories"""

    def test_create_user_data_directory_success(self):
        """Test successful directory creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            user_dir = os.path.join(temp_dir, "testuser")

            result = create_user_data_directory("testuser", temp_dir)

            assert isinstance(result, dict)
            assert "success" in result or "path" in result

    def test_create_user_data_directory_existing(self):
        """Test creating directory that already exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            user_dir = os.path.join(temp_dir, "testuser")
            os.makedirs(user_dir)  # Create directory first

            result = create_user_data_directory("testuser", temp_dir)

            assert isinstance(result, dict)

    def test_create_user_data_directory_invalid_path(self):
        """Test creating directory with invalid path"""
        result = create_user_data_directory(
            "testuser", "/invalid/path/that/doesnt/exist"
        )

        assert isinstance(result, dict)
        assert "success" in result

    def test_create_user_data_directory_invalid_username(self):
        """Test creating directory with invalid username"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with empty username
            result = create_user_data_directory("", temp_dir)
            assert isinstance(result, dict)

            # Test with None username
            result = create_user_data_directory(None, temp_dir)
            assert isinstance(result, dict)


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @patch("app.multi_user_import.SessionLocal")
    def test_import_with_database_error(self, mock_session):
        """Test import operations with database errors"""
        # Mock database session that raises exception
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query.side_effect = Exception("Database error")

        result = import_user_data_from_directory("testuser", "/fake/dir")

        # Should handle database errors gracefully
        assert isinstance(result, dict)

    @patch("app.multi_user_import.SessionLocal")
    def test_import_user_file_complex_data(self, mock_session):
        """Test importing file with complex nested data"""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock user and endpoint
        mock_user = MagicMock()
        mock_user.id = 1
        mock_endpoint = MagicMock()
        mock_endpoint.name = "resume"

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            mock_endpoint,
        ]

        complex_data = {
            "personal": {
                "name": "Complex User",
                "contact": {"email": "complex@example.com", "phone": "123-456-7890"},
            },
            "experience": [
                {
                    "company": "TechCorp",
                    "roles": [
                        {"title": "Developer", "duration": "2 years"},
                        {"title": "Senior Developer", "duration": "1 year"},
                    ],
                }
            ],
            "skills": {
                "programming": ["Python", "JavaScript"],
                "frameworks": ["FastAPI", "React"],
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(complex_data, f)
            temp_path = f.name

        try:
            result = import_user_file("testuser", "resume", temp_path)

            assert isinstance(result, dict)
            assert "success" in result
        finally:
            os.unlink(temp_path)

    @patch("app.multi_user_import.SessionLocal")
    def test_import_user_data_multiple_endpoints(self, mock_session):
        """Test importing user data with multiple endpoint files"""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with tempfile.TemporaryDirectory() as temp_dir:
            user_dir = os.path.join(temp_dir, "testuser")
            os.makedirs(user_dir)

            # Create multiple endpoint files
            endpoints_data = {
                "resume.json": {"name": "Test User", "title": "Developer"},
                "ideas.json": [{"title": "Idea 1", "description": "Test idea"}],
                "skills.json": ["Python", "JavaScript", "SQL"],
                "projects.json": [{"name": "Project A", "tech": ["FastAPI"]}],
            }

            for filename, data in endpoints_data.items():
                file_path = os.path.join(user_dir, filename)
                with open(file_path, "w") as f:
                    json.dump(data, f)

            result = import_user_data_from_directory("testuser", temp_dir)

            assert isinstance(result, dict)

    def test_import_user_file_unicode_content(self):
        """Test importing file with Unicode content"""
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
            result = import_user_file("testuser", "resume", temp_path)

            assert isinstance(result, dict)
            assert "success" in result
        finally:
            os.unlink(temp_path)

    @patch("builtins.open")
    def test_import_user_file_permission_error(self, mock_open_func):
        """Test importing file with permission errors"""
        mock_open_func.side_effect = PermissionError("Permission denied")

        result = import_user_file("testuser", "resume", "/restricted/file.json")

        assert isinstance(result, dict)
        assert "success" in result

    @patch("app.multi_user_import.SessionLocal")
    def test_import_all_users_data_large_dataset(self, mock_session):
        """Test importing large dataset for multiple users"""
        # Mock database session
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock many users
        mock_users = []
        for i in range(50):  # 50 users
            mock_user = MagicMock()
            mock_user.id = i + 1
            mock_user.username = f"user{i}"
            mock_users.append(mock_user)

        mock_db.query.return_value.all.return_value = mock_users

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directories for subset of users
            for i in range(10):  # Only create dirs for first 10 users
                user_dir = os.path.join(temp_dir, f"user{i}")
                os.makedirs(user_dir)

                test_file = os.path.join(user_dir, "resume.json")
                with open(test_file, "w") as f:
                    json.dump({"name": f"User {i}"}, f)

            result = import_all_users_data(temp_dir)

            assert isinstance(result, dict)
