"""
Test resume loader functionality
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app.resume_loader import (
    DEFAULT_RESUME_FILE,
    RESUME_ENDPOINT_NAME,
    check_resume_file_exists,
    get_resume_from_database,
    import_resume_to_database,
    load_resume_from_file,
)


class TestLoadResumeFromFile:
    """Test loading resume data from file"""

    def test_load_resume_from_nonexistent_file(self):
        """Test loading from nonexistent file"""
        result = load_resume_from_file("/nonexistent/resume.json")

        assert result["success"] is False
        assert "Failed to load resume file" in result["error"]
        assert result["file_path"] == "/nonexistent/resume.json"

    def test_load_resume_valid_json(self):
        """Test loading valid resume JSON"""
        resume_data = {
            "personal": {
                "name": "Test User",
                "email": "test@example.com",
                "phone": "555-1234",
            },
            "experience": [
                {
                    "company": "Test Corp",
                    "position": "Developer",
                    "duration": "2020-2023",
                }
            ],
            "education": [
                {"institution": "Test University", "degree": "CS", "year": "2020"}
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(resume_data, f)
            temp_path = f.name

        try:
            result = load_resume_from_file(temp_path)

            assert result["success"] is True
            assert "data" in result
            assert result["data"]["personal"]["name"] == "Test User"
            assert len(result["data"]["experience"]) == 1
            assert result["file_path"] == temp_path
        finally:
            os.unlink(temp_path)

    def test_load_resume_invalid_json(self):
        """Test loading invalid JSON"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json content }")
            temp_path = f.name

        try:
            result = load_resume_from_file(temp_path)

            assert result["success"] is False
            assert "Invalid JSON" in result["error"]
        finally:
            os.unlink(temp_path)

    def test_load_resume_validation_failure(self):
        """Test resume data that fails validation"""
        # Invalid resume structure
        invalid_data = {"not_a_resume": "invalid structure"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_data, f)
            temp_path = f.name

        try:
            result = load_resume_from_file(temp_path)

            # Should handle validation gracefully
            assert "success" in result
        finally:
            os.unlink(temp_path)

    def test_load_resume_default_file(self):
        """Test loading from default file path"""
        # Test with None file_path (should use default)
        result = load_resume_from_file(None)

        # Should attempt to load from default location
        assert "file_path" in result
        assert result["file_path"].endswith(DEFAULT_RESUME_FILE)


class TestImportResumeToDatabase:
    """Test importing resume data to database"""

    def test_import_resume_file_load_failure(self, test_db_session):
        """Test import when file loading fails"""
        result = import_resume_to_database("/nonexistent/file.json")

        assert result["success"] is False
        assert "Failed to load resume file" in result["error"]

    def test_import_resume_no_endpoint(self, test_db_session):
        """Test import when resume endpoint doesn't exist"""
        # Create a valid resume file
        resume_data = {
            "personal": {"name": "Test User"},
            "experience": [],
            "education": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(resume_data, f)
            temp_path = f.name

        try:
            # Mock the database session to not find resume endpoint
            with patch("app.resume_loader.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_db.query.return_value.filter.return_value.first.return_value = None
                mock_get_db.return_value = mock_db

                result = import_resume_to_database(temp_path)

                assert result["success"] is False
                assert "not found" in result["error"]
        finally:
            os.unlink(temp_path)

    def test_import_resume_with_existing_data(self, test_db_session):
        """Test import with existing resume data"""
        from app.database import DataEntry, Endpoint

        # Create resume endpoint
        resume_endpoint = Endpoint(
            name=RESUME_ENDPOINT_NAME,
            description="Resume data",
            schema={"personal": {"type": "object"}},
        )
        test_db_session.add(resume_endpoint)
        test_db_session.commit()
        test_db_session.refresh(resume_endpoint)

        # Add existing resume data
        existing_entry = DataEntry(
            endpoint_id=resume_endpoint.id, data={"personal": {"name": "Old Resume"}}
        )
        test_db_session.add(existing_entry)
        test_db_session.commit()

        # Create new resume file
        resume_data = {
            "personal": {"name": "New Resume"},
            "experience": [],
            "education": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(resume_data, f)
            temp_path = f.name

        try:
            # Import without replacing
            with patch("app.resume_loader.get_db") as mock_get_db:
                mock_get_db.return_value = test_db_session

                result = import_resume_to_database(temp_path, replace_existing=False)

                assert result["success"] is False
                assert "existing resume data" in result["error"]
        finally:
            os.unlink(temp_path)

    def test_import_resume_with_replace(self, test_db_session):
        """Test import with replace_existing=True"""
        from app.database import DataEntry, Endpoint

        # Create resume endpoint
        resume_endpoint = Endpoint(
            name=RESUME_ENDPOINT_NAME,
            description="Resume data",
            schema={"personal": {"type": "object"}},
        )
        test_db_session.add(resume_endpoint)
        test_db_session.commit()
        test_db_session.refresh(resume_endpoint)

        # Create new resume file
        resume_data = {
            "personal": {"name": "New Resume", "email": "new@example.com"},
            "experience": [{"company": "New Corp"}],
            "education": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(resume_data, f)
            temp_path = f.name

        try:
            with patch("app.resume_loader.get_db") as mock_get_db:
                mock_get_db.return_value = test_db_session

                result = import_resume_to_database(temp_path, replace_existing=True)

                assert result["success"] is True
                assert "data" in result
                assert result["data"]["personal"]["name"] == "New Resume"
        finally:
            os.unlink(temp_path)


class TestCheckResumeFileExists:
    """Test resume file existence checking functionality"""

    def test_check_file_default_location(self):
        """Test checking status for default resume file"""
        result = check_resume_file_exists()

        assert "file_path" in result
        assert "exists" in result
        assert "readable" in result

        # Should point to default file
        assert result["file_path"].endswith(DEFAULT_RESUME_FILE)

    def test_check_file_custom_location(self):
        """Test checking status for custom file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
            json.dump({"test": "data"}, f)
            f.flush()

            result = check_resume_file_exists(f.name)

            assert result["file_path"] == f.name
            assert result["exists"] is True
            assert result["readable"] is True

    def test_check_file_nonexistent(self):
        """Test checking status for nonexistent file"""
        result = check_resume_file_exists("/nonexistent/file.json")

        assert result["file_path"] == "/nonexistent/file.json"
        assert result["exists"] is False
        assert result["readable"] is False

    def test_check_file_relative_path(self):
        """Test checking status with relative path"""
        result = check_resume_file_exists("relative/path.json")

        # Should convert to absolute path
        assert os.path.isabs(result["file_path"])
        assert result["file_path"].endswith("relative/path.json")

    def test_check_file_error_handling(self):
        """Test handling filesystem errors during check operations"""
        # Create a file and then simulate access failure
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"test": "data"}, f)
            temp_path = f.name

        try:
            # Mock os.access to raise an exception
            with patch(
                "app.resume_loader.os.access", side_effect=OSError("Permission denied")
            ):
                result = check_resume_file_exists(temp_path)

                # Should handle the error gracefully
                assert result["exists"] is True  # os.path.exists should still work
                assert result["readable"] is False
        finally:
            os.unlink(temp_path)


class TestGetResumeFromDatabase:
    """Test retrieving resume from database"""

    def test_get_resume_no_endpoint(self, test_db_session):
        """Test getting resume when endpoint doesn't exist"""
        with patch("app.resume_loader.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_get_db.return_value = mock_db

            result = get_resume_from_database()

            assert result["success"] is False
            assert "not found" in result["error"]

    def test_get_resume_no_data(self, test_db_session):
        """Test getting resume when no data exists"""
        from app.database import Endpoint

        # Create resume endpoint but no data
        resume_endpoint = Endpoint(name=RESUME_ENDPOINT_NAME, description="Resume data")
        test_db_session.add(resume_endpoint)
        test_db_session.commit()

        with patch("app.resume_loader.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = (
                resume_endpoint
            )
            mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
                None
            )
            mock_get_db.return_value = mock_db

            result = get_resume_from_database()

            assert result["success"] is False
            assert "No resume data" in result["error"]

    def test_get_resume_with_data(self, test_db_session):
        """Test getting resume with existing data"""
        from app.database import DataEntry, Endpoint

        # Create resume endpoint and data
        resume_endpoint = Endpoint(name=RESUME_ENDPOINT_NAME, description="Resume data")
        test_db_session.add(resume_endpoint)
        test_db_session.commit()
        test_db_session.refresh(resume_endpoint)

        resume_data = {
            "personal": {"name": "Test User"},
            "experience": [{"company": "Test Corp"}],
        }

        resume_entry = DataEntry(endpoint_id=resume_endpoint.id, data=resume_data)
        test_db_session.add(resume_entry)
        test_db_session.commit()

        with patch("app.resume_loader.get_db") as mock_get_db:
            mock_get_db.return_value = test_db_session

            result = get_resume_from_database()

            assert result["success"] is True
            assert "data" in result
            assert result["data"]["personal"]["name"] == "Test User"
            assert len(result["data"]["experience"]) == 1
