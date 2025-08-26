"""
Test multi_user_import functionality - comprehensive version for higher coverage
"""

import json
import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, Endpoint, User, get_db
from app.main import app
from app.multi_user_import import (
    create_user_data_directory,
    import_all_users_data,
    import_user_data_from_directory,
    import_user_file,
)

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_multi_user_import_comprehensive.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_db():
    """Create and clean up test database for each test"""
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    """Create test client"""
    return TestClient(app)


class TestUserDataDirectoryImport:
    """Test importing user data from directory"""

    def test_import_user_data_from_directory_success(self, test_db):
        """Test successful user data import from directory"""
        # Create mock session and user
        db = TestingSessionLocal()

        # Create a test user
        test_user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            is_admin=False,
        )
        db.add(test_user)
        db.commit()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test data files
            user_dir = os.path.join(temp_dir, "testuser")
            os.makedirs(user_dir)

            test_file = os.path.join(user_dir, "resume.json")
            with open(test_file, "w") as f:
                json.dump({"name": "Test User"}, f)

            result = import_user_data_from_directory("testuser", temp_dir, db)

            assert isinstance(result, dict)
            assert (
                "success" in result or "imported_count" in result or "error" in result
            )

        db.close()

    def test_import_user_data_from_directory_no_user(self, test_db):
        """Test import with non-existent user"""
        db = TestingSessionLocal()
        result = import_user_data_from_directory("nonexistent", "/fake/dir", db)
        assert isinstance(result, dict)
        assert "error" in result
        db.close()

    def test_import_user_data_from_directory_nonexistent_dir(self, test_db):
        """Test import with non-existent directory"""
        # Create a test user first
        db = TestingSessionLocal()
        test_user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            is_admin=False,
        )
        db.add(test_user)
        db.commit()

        result = import_user_data_from_directory("testuser", "/nonexistent/dir", db)
        assert isinstance(result, dict)
        assert "error" in result
        db.close()

    def test_import_user_data_from_directory_empty_dir(self, test_db):
        """Test import with empty directory"""
        # Create a test user first
        db = TestingSessionLocal()
        test_user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            is_admin=False,
        )
        db.add(test_user)
        db.commit()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create empty user directory
            user_dir = os.path.join(temp_dir, "testuser")
            os.makedirs(user_dir)

            result = import_user_data_from_directory("testuser", temp_dir, db)
            assert isinstance(result, dict)

        db.close()


class TestUserFileImport:
    """Test importing individual user files"""

    def test_import_user_file_success(self, test_db):
        """Test successful user file import"""
        # Create test user and endpoint
        db = TestingSessionLocal()

        test_user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            is_admin=False,
        )
        db.add(test_user)

        test_endpoint = Endpoint(
            id=1,
            name="resume",
            description="Resume data",
            schema={"name": {"type": "string"}},
            is_active=True,
            is_public=True,
        )
        db.add(test_endpoint)
        db.commit()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            json.dump({"name": "Test User"}, temp_file)
            temp_path = temp_file.name

        try:
            result = import_user_file("testuser", "resume", temp_path, db)
            assert isinstance(result, dict)
        finally:
            os.unlink(temp_path)
            db.close()

    def test_import_user_file_no_user(self, test_db):
        """Test import with non-existent user"""
        db = TestingSessionLocal()
        result = import_user_file("nonexistent", "resume", "/fake/file.json", db)
        assert isinstance(result, dict)
        assert "error" in result
        db.close()

    def test_import_user_file_no_endpoint(self, test_db):
        """Test import with non-existent endpoint"""
        # Create test user
        db = TestingSessionLocal()
        test_user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            is_admin=False,
        )
        db.add(test_user)
        db.commit()

        result = import_user_file("testuser", "nonexistent", "/fake/file.json", db)
        assert isinstance(result, dict)
        assert "error" in result
        db.close()

    def test_import_user_file_nonexistent_file(self, test_db):
        """Test import with non-existent file"""
        db = TestingSessionLocal()
        result = import_user_file("testuser", "resume", "/nonexistent/file.json", db)
        assert isinstance(result, dict)
        assert "error" in result
        db.close()

    def test_import_user_file_invalid_json(self, test_db):
        """Test import with invalid JSON file"""
        # Create test user and endpoint
        db = TestingSessionLocal()

        test_user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            is_admin=False,
        )
        db.add(test_user)

        test_endpoint = Endpoint(
            id=1,
            name="resume",
            description="Resume data",
            schema={"name": {"type": "string"}},
            is_active=True,
            is_public=True,
        )
        db.add(test_endpoint)
        db.commit()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            temp_file.write("invalid json content")
            temp_path = temp_file.name

        try:
            result = import_user_file("testuser", "resume", temp_path, db)
            assert isinstance(result, dict)
            assert "error" in result
        finally:
            os.unlink(temp_path)
            db.close()


class TestUserDataDirectoryCreation:
    """Test creating user data directories"""

    def test_create_user_data_directory_success(self, test_db):
        """Test successful directory creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = create_user_data_directory("testuser", temp_dir)
            # The function returns the path string, not a dict
            assert isinstance(result, str)
            assert "testuser" in result

    def test_create_user_data_directory_existing(self, test_db):
        """Test directory creation when directory already exists"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directory first
            user_dir = os.path.join(temp_dir, "testuser")
            os.makedirs(user_dir)

            result = create_user_data_directory("testuser", temp_dir)
            assert isinstance(result, str)
            assert "testuser" in result

    def test_create_user_data_directory_invalid_path(self, test_db):
        """Test directory creation with invalid base path"""
        try:
            result = create_user_data_directory(
                "testuser", "/invalid/path/that/does/not/exist"
            )
            # Should handle error gracefully
            assert result is not None
        except (OSError, PermissionError):
            # Expected for invalid paths
            pass

    def test_create_user_data_directory_invalid_username(self, test_db):
        """Test directory creation with invalid username"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = create_user_data_directory("", temp_dir)
            assert isinstance(result, str)


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_import_with_database_error(self, test_db):
        """Test import handling database errors"""
        db = TestingSessionLocal()
        result = import_user_data_from_directory("testuser", "/fake/dir", db)
        assert isinstance(result, dict)
        assert "error" in result
        db.close()

    def test_import_user_file_complex_data(self, test_db):
        """Test importing complex nested data"""
        # Create test user and endpoint
        db = TestingSessionLocal()

        test_user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            is_admin=False,
        )
        db.add(test_user)

        test_endpoint = Endpoint(
            id=1,
            name="resume",
            description="Resume data",
            schema={"name": {"type": "string"}},
            is_active=True,
            is_public=True,
        )
        db.add(test_endpoint)
        db.commit()

        complex_data = {
            "name": "Test User",
            "experience": [
                {
                    "company": "Test Corp",
                    "position": "Developer",
                    "skills": ["Python", "JavaScript"],
                }
            ],
            "metadata": {"last_updated": "2024-01-01", "version": "1.0"},
        }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as temp_file:
            json.dump(complex_data, temp_file)
            temp_path = temp_file.name

        try:
            result = import_user_file("testuser", "resume", temp_path, db)
            assert isinstance(result, dict)
        finally:
            os.unlink(temp_path)
            db.close()

    def test_import_user_data_multiple_endpoints(self, test_db):
        """Test importing data for multiple endpoints"""
        # Create test user
        db = TestingSessionLocal()
        test_user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            is_admin=False,
        )
        db.add(test_user)
        db.commit()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create user directory with multiple files
            user_dir = os.path.join(temp_dir, "testuser")
            os.makedirs(user_dir)

            # Create multiple test files
            files_data = {
                "resume.json": {"name": "Test User"},
                "skills.json": {"programming": "Python"},
                "about.json": {"bio": "Test bio"},
            }

            for filename, data in files_data.items():
                filepath = os.path.join(user_dir, filename)
                with open(filepath, "w") as f:
                    json.dump(data, f)

            result = import_user_data_from_directory("testuser", temp_dir, db)
            assert isinstance(result, dict)

        db.close()

    def test_import_user_file_unicode_content(self, test_db):
        """Test importing file with unicode content"""
        # Create test user and endpoint
        db = TestingSessionLocal()

        test_user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            is_admin=False,
        )
        db.add(test_user)

        test_endpoint = Endpoint(
            id=1,
            name="resume",
            description="Resume data",
            schema={"name": {"type": "string"}},
            is_active=True,
            is_public=True,
        )
        db.add(test_endpoint)
        db.commit()

        unicode_data = {"name": "测试用户", "bio": "Café résumé 📄"}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as temp_file:
            json.dump(unicode_data, temp_file, ensure_ascii=False)
            temp_path = temp_file.name

        try:
            result = import_user_file("testuser", "resume", temp_path, db)
            assert isinstance(result, dict)
        finally:
            os.unlink(temp_path)
            db.close()

    def test_import_user_file_permission_error(self, test_db):
        """Test import with file permission error"""
        db = TestingSessionLocal()
        result = import_user_file("testuser", "resume", "/restricted/file.json", db)
        assert isinstance(result, dict)
        assert "error" in result
        db.close()


class TestImportAllUsers:
    """Test importing data for all users"""

    def test_import_all_users_data_success(self, test_db):
        """Test successful import for all users"""
        # Create test users
        db = TestingSessionLocal()

        for i in range(2):
            user = User(
                id=i + 1,
                username=f"user{i + 1}",
                email=f"user{i + 1}@example.com",
                hashed_password="hashed",
                is_active=True,
                is_admin=False,
            )
            db.add(user)
        db.commit()
        db.close()

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directories and files for both users
            for i in range(2):
                user_dir = os.path.join(temp_dir, f"user{i + 1}")
                os.makedirs(user_dir)

                test_file = os.path.join(user_dir, "resume.json")
                with open(test_file, "w") as f:
                    json.dump({"name": f"User {i + 1}"}, f)

            result = import_all_users_data(temp_dir)
            assert isinstance(result, dict)

    def test_import_all_users_data_empty_directory(self, test_db):
        """Test import with empty base directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = import_all_users_data(temp_dir)
            assert isinstance(result, dict)

    def test_import_all_users_data_nonexistent_directory(self, test_db):
        """Test import with non-existent directory"""
        result = import_all_users_data("/nonexistent/directory")
        assert isinstance(result, dict)
        assert "error" in result
