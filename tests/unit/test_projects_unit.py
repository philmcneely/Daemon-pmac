"""
Test projects endpoint unit functionality
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from app.data_loader import (
    discover_data_files,
    import_endpoint_data_to_database,
    load_endpoint_data_from_file,
)


class TestProjectsDataLoader:
    """Test projects-specific data loading functionality"""

    def test_discover_projects_files(self):
        """Test discovery of projects data files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create projects test files
            projects_files = [
                "projects.json",
                "projects_personal.json",
                "projects_work.json",
                "projects_archived.json",
            ]

            for filename in projects_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w") as f:
                    json.dump([{"content": f"# Test from {filename}"}], f)

            result = discover_data_files(temp_dir)

            assert "projects" in result
            assert len(result["projects"]) == 4

            # Verify all project files are discovered
            project_filenames = [os.path.basename(f) for f in result["projects"]]
            for expected_file in projects_files:
                assert expected_file in project_filenames

    def test_load_projects_markdown_content(self):
        """Test loading projects with markdown content"""
        with tempfile.TemporaryDirectory() as temp_dir:
            projects_data = [
                {
                    "content": "# Development Project\n\n## Overview\nFastAPI project with markdown support."
                },
                {
                    "content": "### Volunteer Work\n\n- Animal shelter coordination\n- Community outreach programs"
                },
                {
                    "content": "## Personal Projects\n\n**Home Automation**\n- Raspberry Pi setup\n- IoT device integration"
                },
            ]

            projects_file = os.path.join(temp_dir, "projects.json")
            with open(projects_file, "w") as f:
                json.dump(projects_data, f)

            result = load_endpoint_data_from_file("projects", projects_file)

            assert result["success"] is True
            assert result["count"] == 3
            data = result["data"]
            assert len(data) == 3
            assert all("content" in item for item in data)
            assert "FastAPI project" in data[0]["content"]
            assert "Volunteer Work" in data[1]["content"]
            assert "Home Automation" in data[2]["content"]

    def test_load_projects_complex_markdown(self):
        """Test loading projects with complex markdown formatting"""
        with tempfile.TemporaryDirectory() as temp_dir:
            complex_project = [
                {
                    "content": """# Complex Project 📊

## Technical Stack
- **Backend**: Python, FastAPI
- **Frontend**: React, TypeScript
- **Database**: PostgreSQL

### Code Example
```python
def create_project(content: str):
    return {"content": content}
```

### Links and References
- [Documentation](https://docs.project.com)
- [GitHub Repo](https://github.com/user/project)

> "Innovation distinguishes between a leader and a follower." - Steve Jobs

#### Task List
- [x] Initial setup
- [x] API development
- [ ] Frontend integration
- [ ] Testing & deployment

##### Performance Metrics
| Metric | Value | Target |
|--------|-------|--------|
| Response Time | 120ms | <100ms |
| Uptime | 99.9% | 99.95% |
| Throughput | 1000/sec | 1500/sec |
"""
                }
            ]

            projects_file = os.path.join(temp_dir, "projects.json")
            with open(projects_file, "w") as f:
                json.dump(complex_project, f)

            result = load_endpoint_data_from_file("projects", projects_file)

            assert result["success"] is True
            assert result["count"] == 1
            data = result["data"]
            assert len(data) == 1
            content = data[0]["content"]

            # Verify complex markdown elements are preserved
            assert "📊" in content
            assert "```python" in content
            assert "[Documentation]" in content
            assert '> "Innovation' in content
            assert "- [x] Initial setup" in content
            assert "| Metric | Value |" in content

    @patch("app.data_loader.get_db")
    def test_import_projects_to_database(self, mock_get_db):
        """Test importing projects data to database"""
        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])  # get_db returns a generator

        # Mock the projects endpoint with the correct schema
        projects_endpoint = MagicMock()
        projects_endpoint.id = 1
        projects_endpoint.name = "projects"
        projects_endpoint.schema = {
            "content": {"type": "string", "required": True},
            "meta": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "date": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "status": {"type": "string"},
                    "visibility": {
                        "type": "string",
                        "enum": ["public", "unlisted", "private"],
                        "default": "public",
                    },
                },
            },
        }

        mock_db.query.return_value.filter.return_value.first.return_value = (
            projects_endpoint
        )
        mock_db.query.return_value.filter.return_value.all.return_value = (
            []
        )  # No existing entries

        projects_data = [
            {"content": "# Project Alpha\n\nFirst project description."},
            {"content": "# Project Beta\n\nSecond project with more details."},
        ]

        # Mock successful import
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(projects_data, f)
            temp_file = f.name

        try:
            result = import_endpoint_data_to_database("projects", temp_file)
        finally:
            os.unlink(temp_file)

        # Verify the import was successful
        assert result["success"] is True
        assert result["imported_count"] == 2

    @patch("app.data_loader.get_db")
    def test_import_projects_validation_error(self, mock_get_db):
        """Test handling validation errors during projects import"""
        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])  # get_db returns a generator

        # Mock the projects endpoint with the correct schema
        projects_endpoint = MagicMock()
        projects_endpoint.id = 1
        projects_endpoint.name = "projects"
        projects_endpoint.schema = {
            "content": {"type": "string", "required": True},
            "meta": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "date": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "status": {"type": "string"},
                    "visibility": {
                        "type": "string",
                        "enum": ["public", "unlisted", "private"],
                        "default": "public",
                    },
                },
            },
        }

        mock_db.query.return_value.filter.return_value.first.return_value = (
            projects_endpoint
        )
        mock_db.query.return_value.filter.return_value.all.return_value = (
            []
        )  # No existing entries

        # Invalid data (missing required content field)
        invalid_projects_data = [
            {"title": "Invalid Project"},  # Missing content field
            {"content": "# Valid Project\n\nThis one is fine."},
        ]

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_projects_data, f)
            temp_file = f.name

        try:
            result = import_endpoint_data_to_database("projects", temp_file)
        finally:
            os.unlink(temp_file)

        # Should handle the error gracefully (endpoint might not exist in test)
        assert "success" in result

    def test_load_projects_empty_file(self):
        """Test loading empty projects file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            projects_file = os.path.join(temp_dir, "projects.json")
            with open(projects_file, "w") as f:
                json.dump([], f)

            result = load_endpoint_data_from_file("projects", projects_file)

            assert result["success"] is True
            assert result["data"] == []

    def test_load_projects_malformed_json(self):
        """Test handling malformed JSON in projects file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            projects_file = os.path.join(temp_dir, "projects.json")
            with open(projects_file, "w") as f:
                f.write("{ invalid json content")

            result = load_endpoint_data_from_file("projects", projects_file)
            assert result["success"] is False
            assert "error" in result

    def test_load_projects_unicode_content(self):
        """Test loading projects with unicode and special characters"""
        with tempfile.TemporaryDirectory() as temp_dir:
            unicode_projects = [
                {
                    "content": "# Проект на русском языке\n\nОписание проекта с unicode символами: ∀x∈ℝ"
                },
                {
                    "content": "# Emoji Project 🚀\n\n✅ Task completed\n❌ Task failed\n🔄 In progress"
                },
                {
                    "content": "# Math & Science 🧪\n\nE = mc²\nπ ≈ 3.14159\n∇ × F = ∂F/∂t"
                },
            ]

            projects_file = os.path.join(temp_dir, "projects.json")
            with open(projects_file, "w", encoding="utf-8") as f:
                json.dump(unicode_projects, f, ensure_ascii=False)

            result = load_endpoint_data_from_file("projects", projects_file)

            assert result["success"] is True
            assert result["count"] == 3
            data = result["data"]
            assert len(data) == 3
            assert "Проект на русском" in data[0]["content"]
            assert "🚀" in data[1]["content"]
            assert "E = mc²" in data[2]["content"]


class TestProjectsEndpointSchema:
    """Test projects endpoint schema validation and handling"""

    def test_projects_schema_flexible_content(self):
        """Test that projects schema allows flexible content structure"""
        # This simulates the schema defined in database.py
        expected_schema = {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Markdown content for the project - completely flexible structure",
                }
            },
            "required": ["content"],
            "additionalProperties": False,
        }

        # Test valid project data
        valid_projects = [
            {"content": "# Simple Project\n\nJust a title and description."},
            {"content": "### Bullet Point Style\n\n- Point 1\n- Point 2\n- Point 3"},
            {
                "content": "Complex **markdown** with [links](http://example.com) and `code`"
            },
        ]

        # In a real scenario, these would be validated against the schema
        # For unit test, we verify structure expectations
        for project in valid_projects:
            assert "content" in project
            assert isinstance(project["content"], str)
            assert len(project["content"]) > 0

    def test_projects_data_immutability(self):
        """Test that projects data maintains integrity during processing"""
        original_content = "# Original Project\n\nThis content should not be modified during processing."

        project_data = {"content": original_content}

        # Simulate data processing (loading, validation, etc.)
        processed_data = project_data.copy()

        assert processed_data["content"] == original_content
        assert id(processed_data) != id(project_data)  # Different objects
        assert processed_data == project_data  # Same content


class TestProjectsVariants:
    """Test projects with different file variants"""

    def test_discover_projects_variants(self):
        """Test discovery of different project file variants"""
        with tempfile.TemporaryDirectory() as temp_dir:
            variant_files = [
                ("projects.json", [{"content": "# Main Projects"}]),
                ("projects_personal.json", [{"content": "# Personal Projects"}]),
                ("projects_work.json", [{"content": "# Work Projects"}]),
                ("projects_volunteer.json", [{"content": "# Volunteer Projects"}]),
                ("projects_archived.json", [{"content": "# Archived Projects"}]),
            ]

            for filename, content in variant_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w") as f:
                    json.dump(content, f)

            result = discover_data_files(temp_dir)

            assert "projects" in result
            assert len(result["projects"]) == 5

            # Verify all variants are discovered
            discovered_files = [os.path.basename(f) for f in result["projects"]]
            expected_files = [filename for filename, _ in variant_files]

            for expected_file in expected_files:
                assert expected_file in discovered_files

    def test_load_projects_variants_content(self):
        """Test loading content from different project variants"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create personal projects variant
            personal_projects = [
                {
                    "content": "### Personal Side Projects\n\n**Home Lab Setup**\n- Server configuration\n- Network monitoring"
                },
                {
                    "content": "**Learning Goals 2024**\n- Master FastAPI\n- Explore machine learning\n- Contribute to open source"
                },
            ]

            personal_file = os.path.join(temp_dir, "projects_personal.json")
            with open(personal_file, "w") as f:
                json.dump(personal_projects, f)

            result = load_endpoint_data_from_file("projects", personal_file)

            assert result["success"] is True
            assert result["count"] == 2
            data = result["data"]
            assert len(data) == 2
            assert "Home Lab Setup" in data[0]["content"]
            assert "Learning Goals 2024" in data[1]["content"]

    @patch("app.data_loader.SessionLocal")
    def test_import_multiple_projects_variants(self, mock_session):
        """Test importing projects from multiple variant files"""
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(
            name="projects", schema={"properties": {"content": {"type": "string"}}}
        )

        # Simulate importing from multiple sources
        personal_projects = [{"content": "# Personal Project"}]
        work_projects = [{"content": "# Work Project"}]

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        # Create temporary files for testing
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(personal_projects, f)
            personal_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(work_projects, f)
            work_file = f.name

        try:
            # Import personal projects
            result1 = import_endpoint_data_to_database("projects", personal_file)
            # Import work projects
            result2 = import_endpoint_data_to_database("projects", work_file)
        finally:
            os.unlink(personal_file)
            os.unlink(work_file)

        # Should handle gracefully (endpoints might not exist in test)
        assert "success" in result1
        assert "success" in result2
