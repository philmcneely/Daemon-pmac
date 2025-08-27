"""
Test projects endpoint E2E functionality
"""

import json

import pytest


def test_projects_endpoint_exists(client):
    """Test that projects endpoint is available"""
    response = client.get("/api/v1/endpoints")
    assert response.status_code == 200
    data = response.json()
    endpoint_names = [ep["name"] for ep in data]
    assert "projects" in endpoint_names


def test_get_projects_endpoint_config(client):
    """Test getting projects endpoint configuration"""
    response = client.get("/api/v1/endpoints/projects")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "projects"
    assert "schema" in data
    assert "description" in data


def test_get_empty_projects_data(client):
    """Test getting data from empty projects endpoint"""
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) == 0


def test_create_project_unauthenticated(client):
    """Test creating project without authentication should fail"""
    project_data = {
        "content": "# My Test Project\n\nThis is a test project with markdown content."
    }
    response = client.post("/api/v1/projects", json=project_data)
    # Should be 403 (Forbidden) not 401 (Unauthorized) because IP filtering might be applied
    assert response.status_code in [401, 403]


def test_create_project_authenticated(client, auth_headers):
    """Test creating project with authentication"""
    project_data = {
        "content": "# My First Project\n\nThis is a test project with **markdown** content.\n\n## Features\n- Markdown support\n- Flexible structure\n- No rigid schema"
    }

    response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["message"] == "Data added to projects"
    assert data["data"]["content"] == project_data["content"]


def test_create_volunteer_project(client, auth_headers):
    """Test creating a volunteer project like the user's example"""
    volunteer_content = """### Volunteer Projects

#### Organization: Local Animal Shelter

*   **Project 1: "Pawsitive Adoptions" Event Coordinator**
    *   Organized and executed a successful adoption event, resulting in 15 animal adoptions over a single weekend.
    *   Managed a team of 10 volunteers, delegating tasks such as animal handling, visitor registration, and information dissemination.
    *   Coordinated with local businesses for sponsorships and donations, securing over $500 in supplies and monetary contributions.

*   **Project 2: Shelter Renovation Assistant**
    *   Assisted in the renovation of animal enclosures, including painting, minor repairs, and installation of new bedding.
    *   Contributed to creating a cleaner and more comfortable environment for over 50 animals.
    *   Worked collaboratively with a team of 8 volunteers, ensuring tasks were completed efficiently and safely."""

    project_data = {"content": volunteer_content}

    response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["message"] == "Data added to projects"
    assert "Pawsitive Adoptions" in data["data"]["content"]


def test_update_project_data(client, auth_headers):
    """Test updating existing project"""
    # First create a project
    original_content = "# Original Project\n\nThis is the original content."
    create_response = client.post(
        "/api/v1/projects", json={"content": original_content}, headers=auth_headers
    )
    assert create_response.status_code == 200
    project_id = create_response.json()["id"]

    # Then update it
    updated_content = "# Updated Project\n\nThis is the **updated** content with more details.\n\n## New Section\n- Added features\n- Improved documentation"
    update_response = client.put(
        f"/api/v1/projects/{project_id}",
        json={"content": updated_content},
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["data"]["content"] == updated_content
    assert "Updated Project" in data["data"]["content"]


def test_replace_project_content(client, auth_headers):
    """Test completely replacing project content"""
    # Create initial project
    initial_content = """# Development Project

## Status: Planning

Just an idea at this stage."""

    create_response = client.post(
        "/api/v1/projects", json={"content": initial_content}, headers=auth_headers
    )
    assert create_response.status_code == 200
    project_id = create_response.json()["id"]

    # Replace with completely different content
    replacement_content = """### Personal Projects

*   **Project: Home Automation System**
    *   Built custom smart home dashboard using Raspberry Pi
    *   Integrated 20+ IoT devices across home
    *   Achieved 25% reduction in energy costs
    *   Technologies: Python, Home Assistant, React Native"""

    replace_response = client.put(
        f"/api/v1/projects/{project_id}",
        json={"content": replacement_content},
        headers=auth_headers,
    )
    assert replace_response.status_code == 200
    data = replace_response.json()
    assert data["data"]["content"] == replacement_content
    assert "Home Automation" in data["data"]["content"]
    assert "Development Project" not in data["data"]["content"]


def test_delete_project(client, auth_headers):
    """Test soft deleting a project"""
    # First create a project
    project_content = "# Project to Delete\n\nThis project will be removed."
    create_response = client.post(
        "/api/v1/projects", json={"content": project_content}, headers=auth_headers
    )
    assert create_response.status_code == 200
    project_id = create_response.json()["id"]

    # Then delete it
    delete_response = client.delete(
        f"/api/v1/projects/{project_id}", headers=auth_headers
    )
    assert delete_response.status_code == 200
    assert "deleted" in delete_response.json()["message"].lower()


def test_bulk_create_projects(client, auth_headers):
    """Test bulk project creation"""
    bulk_projects = [
        {"content": "# Project Alpha\n\nFirst project in bulk creation."},
        {
            "content": "# Project Beta\n\nSecond project with different content structure.\n\n## Features\n- Feature 1\n- Feature 2"
        },
        {
            "content": "### Quick Project Notes\n\n- Simple bullet point format\n- No formal structure required\n- Flexible markdown content"
        },
    ]

    response = client.post(
        "/api/v1/projects/bulk", json=bulk_projects, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success_count"] == 3
    assert data["error_count"] == 0
    assert len(data["created_items"]) == 3


def test_get_projects_after_creation(client, auth_headers):
    """Test retrieving projects after creating some"""
    # Create a few projects
    projects = [
        {"content": "# Project 1\n\nFirst test project."},
        {"content": "# Project 2\n\nSecond test project."},
    ]

    for project in projects:
        response = client.post("/api/v1/projects", json=project, headers=auth_headers)
        assert response.status_code == 200

    # Get all projects
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "items" in data
    projects_list = data["items"]
    assert len(projects_list) >= 2  # At least the ones we just created


def test_projects_pagination(client, auth_headers):
    """Test pagination with projects"""
    # Create several projects for pagination testing
    for i in range(5):
        project_data = {
            "content": f"# Project {i + 1}\n\nThis is project number {i + 1} for pagination testing."
        }
        response = client.post(
            "/api/v1/projects", json=project_data, headers=auth_headers
        )
        assert response.status_code == 200

    # Test pagination using page and size parameters
    response = client.get("/api/v1/projects?page=1&size=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 3  # Should respect the size limit


def test_projects_search_by_content(client, auth_headers):
    """Test searching projects by content"""
    # Create projects with searchable content
    searchable_projects = [
        {
            "content": "# Machine Learning Project\n\nUsing TensorFlow and Python for AI model training."
        },
        {"content": "# Web Development\n\nBuilding APIs with FastAPI and Python."},
        {"content": "# Mobile App\n\nReact Native application for iOS and Android."},
    ]

    for project in searchable_projects:
        response = client.post("/api/v1/projects", json=project, headers=auth_headers)
        assert response.status_code == 200

    # Search for Python-related projects
    response = client.get("/api/v1/projects?search=Python")
    assert response.status_code == 200
    data = response.json()
    projects_list = data["items"]
    # Should find projects containing "Python"
    python_projects = [p for p in projects_list if "Python" in p.get("content", "")]
    assert len(python_projects) >= 2


def test_projects_single_user_vs_multi_user(client, auth_headers):
    """Test projects work in both single and multi-user modes"""
    # This test ensures projects work regardless of system mode
    project_data = {
        "content": "# System Mode Test\n\nThis project should work in both single and multi-user modes."
    }

    response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
    assert response.status_code == 200

    # Verify we can retrieve it
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    projects_list = data["items"]
    assert any("System Mode Test" in item.get("content", "") for item in projects_list)


def test_projects_markdown_special_characters(client, auth_headers):
    """Test projects with special markdown characters and formatting"""
    complex_markdown = """# Complex Project 📊

## Overview
This project contains **various** markdown elements:

### Code Blocks
```python
def hello_world():
    print("Hello, World!")
    return True
```

### Lists and Links
- [GitHub Repository](https://github.com/user/project)
- **Bold text** and *italic text*
- `inline code` snippets

### Tables
| Feature | Status | Priority |
|---------|--------|----------|
| Authentication | ✅ Complete | High |
| API Endpoints | 🔄 In Progress | Medium |
| Documentation | ❌ Pending | Low |

### Special Characters
- Emoji support: 🚀 🎯 💡
- Mathematical expressions: E = mc²
- Unicode: ∀x∈ℝ, x² ≥ 0

> Blockquote: "The best way to predict the future is to invent it." - Alan Kay
"""

    project_data = {"content": complex_markdown}
    response = client.post("/api/v1/projects", json=project_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "📊" in data["data"]["content"]
    assert "```python" in data["data"]["content"]
    assert "GitHub Repository" in data["data"]["content"]
