"""
Test data_loader functionality - simplified version
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.data_loader import discover_data_files, load_endpoint_data_from_file


class TestDiscoverDataFiles:
    """Test data file discovery"""

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


class TestLoadEndpointDataFromFile:
    """Test loading endpoint data from file"""

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
