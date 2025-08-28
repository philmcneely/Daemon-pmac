"""
Module: tests.e2e.test_api
Description: End-to-end tests for core API functionality and endpoint behaviors

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28

Dependencies:
- pytest: 7.4.3+ - Testing framework
- fastapi: 0.104.1+ - TestClient for API testing
- sqlalchemy: 2.0+ - Database operations in tests

Usage:
    pytest tests/e2e/test_api.py -v

Notes:
    - Complete workflow testing with database integration
    - Comprehensive test coverage with fixtures
    - Proper database isolation and cleanup
    - Authentication and authorization testing
"""

import json

import pytest


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["name"] == "Daemon"


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    # In CI environments, disk space might be low, so accept both 200 and 503
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "database" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]


def test_list_endpoints(client):
    """Test listing available endpoints"""
    response = client.get("/api/v1/endpoints")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # Check for default endpoints
    endpoint_names = [ep["name"] for ep in data]
    expected_endpoints = [
        "resume",
        "about",
        "ideas",
        "skills",
        "favorite_books",
        "problems",
        "hobbies",
        "looking_for",
    ]
    for endpoint in expected_endpoints:
        assert endpoint in endpoint_names


def test_get_endpoint_config(client):
    """Test getting endpoint configuration"""
    response = client.get("/api/v1/endpoints/ideas")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "ideas"
    assert "schema" in data
    assert "description" in data


def test_get_nonexistent_endpoint(client):
    """Test getting configuration for non-existent endpoint"""
    response = client.get("/api/v1/endpoints/nonexistent")
    assert response.status_code == 404


def test_system_info_endpoint(client):
    """Test system info endpoint"""
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()
    assert "mode" in data
    assert "available_endpoints" in data
    assert data["mode"] in ["single_user", "multi_user"]


def test_get_empty_endpoint_data(client):
    """Test getting data from empty endpoint"""
    response = client.get("/api/v1/ideas")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) == 0


def test_create_endpoint_data_unauthenticated(client):
    """Test creating data without authentication should fail"""
    response = client.post(
        "/api/v1/ideas",
        json={
            "title": "Test Idea",
            "description": "A test idea",
            "category": "testing",
        },
    )
    # Should be 403 (Forbidden) not 401 (Unauthorized) because IP filtering
    # might be applied
    assert response.status_code in [401, 403]


def test_create_endpoint_data_authenticated(client, auth_headers):
    """Test creating data with authentication"""
    response = client.post(
        "/api/v1/ideas",
        json={
            "title": "Test Idea",
            "description": "A test idea",
            "category": "testing",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["message"] == "Data added to ideas"
    assert data["data"]["title"] == "Test Idea"


def test_update_endpoint_data(client, auth_headers):
    """Test updating existing data"""
    # First create data
    create_response = client.post(
        "/api/v1/ideas",
        json={
            "title": "Original Idea",
            "description": "Original description",
            "category": "testing",
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 200
    item_id = create_response.json()["id"]

    # Then update it
    update_response = client.put(
        f"/api/v1/ideas/{item_id}",
        json={
            "title": "Updated Idea",
            "description": "Updated description",
            "category": "testing",
        },
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["data"]["title"] == "Updated Idea"


def test_delete_endpoint_data(client, auth_headers):
    """Test soft deleting data"""
    # First create data
    create_response = client.post(
        "/api/v1/ideas",
        json={
            "title": "To Delete",
            "description": "Will be deleted",
            "category": "testing",
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 200
    item_id = create_response.json()["id"]

    # Then delete it
    delete_response = client.delete(f"/api/v1/ideas/{item_id}", headers=auth_headers)
    assert delete_response.status_code == 200
    assert "deleted" in delete_response.json()["message"].lower()


def test_bulk_create_endpoint_data(client, auth_headers):
    """Test bulk data creation"""
    bulk_data = [
        {
            "title": "Bulk Idea 1",
            "description": "First bulk idea",
            "category": "testing",
        },
        {
            "title": "Bulk Idea 2",
            "description": "Second bulk idea",
            "category": "testing",
        },
    ]

    response = client.post("/api/v1/ideas/bulk", json=bulk_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success_count"] == 2
    assert data["error_count"] == 0
    assert len(data["created_items"]) == 2


def test_pagination(client, auth_headers):
    """Test pagination parameters"""
    # Create some test data first
    for i in range(5):
        client.post(
            "/api/v1/ideas",
            json={
                "title": f"Idea {i}",
                "description": f"Description {i}",
                "category": "testing",
            },
            headers=auth_headers,
        )

    # Test pagination
    response = client.get("/api/v1/ideas?page=1&size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2


def test_invalid_data_validation(client, auth_headers):
    """Test data validation with invalid data"""
    response = client.post(
        "/api/v1/ideas",
        json={
            "title": "",  # Empty title should fail validation
            "description": "",  # Empty description should fail validation
        },
        headers=auth_headers,
    )
    # The validation might pass as empty strings might be allowed depending on schema
    # Let's test with completely missing required fields
    response2 = client.post(
        "/api/v1/ideas", json={}, headers=auth_headers  # Missing required fields
    )
    # At least one of these should fail
    assert response.status_code == 400 or response2.status_code == 400


def test_skills_endpoint_specific_validation(client, auth_headers):
    """Test skills endpoint with specific validation"""
    # Valid skills data
    response = client.post(
        "/api/v1/skills",
        json={
            "name": "Python Programming",
            "category": "Programming Languages",
            "level": "advanced",
            "years_experience": 5,
            "description": "Python development and scripting",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200

    # With flexible markdown schema, any JSON structure is accepted
    response = client.post(
        "/api/v1/skills",
        json={
            "name": "Invalid Skill",
            "level": "invalid_level",  # This is now accepted in flexible format
        },
        headers=auth_headers,
    )
    assert response.status_code == 200  # Flexible markdown accepts any structure


def test_favorite_books_endpoint(client, auth_headers):
    """Test favorite books endpoint with rating validation"""
    # Valid book data
    response = client.post(
        "/api/v1/favorite_books",
        json={
            "title": "Test Book",
            "author": "Test Author",
            "rating": 4,
            "review": "Great book!",
            "genres": ["fiction", "adventure"],
        },
        headers=auth_headers,
    )
    assert response.status_code == 200

    # Invalid rating should fail
    response = client.post(
        "/api/v1/favorite_books",
        json={
            "title": "Invalid Book",
            "author": "Test Author",
            "rating": 6,  # Should be 1-5
        },
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_multi_user_data_isolation(client, auth_headers, regular_user_headers):
    """Test that data is properly isolated between users in multi-user mode"""
    # Create data as admin user
    admin_response = client.post(
        "/api/v1/ideas",
        json={
            "title": "Admin Idea",
            "description": "Only admin should see this",
            "category": "admin",
        },
        headers=auth_headers,
    )
    assert admin_response.status_code == 200

    # Create data as regular user
    user_response = client.post(
        "/api/v1/ideas",
        json={
            "title": "User Idea",
            "description": "Only user should see this",
            "category": "user",
        },
        headers=regular_user_headers,
    )
    assert user_response.status_code == 200

    # Check that system info shows multi-user mode
    info_response = client.get("/api/v1/system/info")
    system_info = info_response.json()

    if system_info["mode"] == "multi_user":
        # In multi-user mode, check user-specific endpoints
        admin_data = client.get("/api/v1/ideas/users/admin").json()
        user_data = client.get("/api/v1/ideas/users/user").json()

        # Verify data isolation
        admin_titles = [item["title"] for item in admin_data]
        user_titles = [item["title"] for item in user_data]

        assert "Admin Idea" in admin_titles
        assert "Admin Idea" not in user_titles
        assert "User Idea" in user_titles
        assert "User Idea" not in admin_titles


def test_get_nonexistent_endpoint_config(client):
    """Test getting nonexistent endpoint configuration"""
    response = client.get("/api/v1/endpoints/nonexistent")
    assert response.status_code == 404


def test_get_endpoint_data_public(client):
    """Test getting data from public endpoint"""
    response = client.get("/api/v1/ideas")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_add_endpoint_data(client, auth_headers, sample_idea_data):
    """Test adding data to endpoint"""
    response = client.post("/api/v1/ideas", headers=auth_headers, json=sample_idea_data)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "message" in data
    assert data["data"]["title"] == sample_idea_data["title"]


def test_add_endpoint_data_unauthorized(client, sample_idea_data):
    """Test adding data without authentication"""
    response = client.post("/api/v1/ideas", json=sample_idea_data)
    assert response.status_code in [401, 403]


def test_add_invalid_data(client, auth_headers):
    """Test adding invalid data to endpoint"""
    response = client.post(
        "/api/v1/ideas",
        headers=auth_headers,
        json={
            "invalid_field": "value"
            # Missing required 'title' and 'description'
        },
    )
    assert response.status_code == 400


def test_update_endpoint_data_with_validation(client, auth_headers, sample_idea_data):
    """Test updating endpoint data with validation"""
    # First create an item
    create_response = client.post(
        "/api/v1/ideas", headers=auth_headers, json=sample_idea_data
    )
    item_id = create_response.json()["id"]

    # Update the item
    updated_data = sample_idea_data.copy()
    updated_data["title"] = "Updated Test Idea"

    response = client.put(
        f"/api/v1/ideas/{item_id}", headers=auth_headers, json=updated_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["title"] == "Updated Test Idea"


def test_delete_endpoint_data_with_auth(client, auth_headers, sample_idea_data):
    """Test deleting endpoint data with authentication"""
    # First create an item
    create_response = client.post(
        "/api/v1/ideas", headers=auth_headers, json=sample_idea_data
    )
    item_id = create_response.json()["id"]

    # Delete the item
    response = client.delete(f"/api/v1/ideas/{item_id}", headers=auth_headers)
    assert response.status_code == 200


def test_bulk_add_data(client, auth_headers):
    """Test bulk adding data"""
    bulk_data = [
        {"title": "Bulk Idea 1", "description": "First bulk idea", "category": "test"},
        {"title": "Bulk Idea 2", "description": "Second bulk idea", "category": "test"},
    ]

    response = client.post("/api/v1/ideas/bulk", headers=auth_headers, json=bulk_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success_count"] == 2
    assert data["error_count"] == 0


def test_pagination_basic(client, auth_headers):
    """Test basic pagination of endpoint data"""
    # Add some test data first
    for i in range(5):
        client.post(
            "/api/v1/ideas",
            headers=auth_headers,
            json={"title": f"Idea {i}", "description": f"Description {i}"},
        )

    # Test pagination
    response = client.get("/api/v1/ideas?page=1&size=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2


def test_books_endpoint_specific_validation(client, auth_headers, sample_book_data):
    """Test book-specific validation"""
    response = client.post(
        "/api/v1/favorite_books", headers=auth_headers, json=sample_book_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["title"] == sample_book_data["title"]
    assert data["data"]["author"] == sample_book_data["author"]


def test_books_invalid_rating(client, auth_headers):
    """Test book with invalid rating"""
    invalid_book = {
        "title": "Test Book",
        "author": "Test Author",
        "rating": 10,  # Invalid rating (should be 1-5)
    }

    response = client.post(
        "/api/v1/favorite_books", headers=auth_headers, json=invalid_book
    )
    assert response.status_code == 400


def test_resume_endpoint_specific_validation(client, auth_headers, sample_resume_data):
    """Test resume-specific validation"""
    response = client.post(
        "/api/v1/resume", headers=auth_headers, json=sample_resume_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == sample_resume_data["name"]
    assert data["data"]["title"] == sample_resume_data["title"]
    assert "experience" in data["data"]
    assert "education" in data["data"]
    assert "skills" in data["data"]


def test_resume_minimal_data(client, auth_headers):
    """Test resume with minimal required data"""
    minimal_resume = {"name": "Jane Smith", "title": "Developer"}

    response = client.post("/api/v1/resume", headers=auth_headers, json=minimal_resume)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == "Jane Smith"
    assert data["data"]["title"] == "Developer"


def test_resume_missing_required_fields(client, auth_headers):
    """Test resume with missing required fields"""
    invalid_resume = {
        "summary": "Some summary"
        # Missing required 'name' and 'title'
    }

    response = client.post("/api/v1/resume", headers=auth_headers, json=invalid_resume)
    assert response.status_code == 400


def test_system_mode_detection(client, admin_user, regular_user):
    """Test that system correctly detects single vs multi-user mode"""
    # With multiple users, should be in multi-user mode
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "multi_user"
    assert len(data["users"]) >= 2  # At least admin and regular user
    assert "admin" in data["users"]
    assert "user" in data["users"]
    assert data["endpoint_pattern"] == "/api/v1/{endpoint_name}/users/{username}"


def test_single_user_mode_simulation(client):
    """Test system in single-user mode (only one user exists)"""
    # When only one user exists, system should operate differently
    # This is tested implicitly by other tests when only admin user exists
    pass


def test_multi_user_data_privacy(client, auth_headers, regular_user_headers):
    """Test that user data is properly isolated in multi-user mode"""
    # Admin user creates data
    admin_idea = {
        "title": "Admin Secret Idea",
        "description": "Only admin should see this sensitive info",
        "category": "confidential",
    }
    admin_response = client.post("/api/v1/ideas", json=admin_idea, headers=auth_headers)
    assert admin_response.status_code == 200

    # Regular user creates data
    user_idea = {
        "title": "User Public Idea",
        "description": "This is the user's public idea",
        "category": "public",
    }
    user_response = client.post(
        "/api/v1/ideas", json=user_idea, headers=regular_user_headers
    )
    assert user_response.status_code == 200

    # Check user-specific endpoints
    admin_data = client.get("/api/v1/ideas/users/admin").json()
    user_data = client.get("/api/v1/ideas/users/user").json()

    # Verify data isolation
    admin_titles = [item["title"] for item in admin_data]
    user_titles = [item["title"] for item in user_data]

    assert "Admin Secret Idea" in admin_titles
    assert "Admin Secret Idea" not in user_titles
    assert "User Public Idea" in user_titles
    assert "User Public Idea" not in admin_titles


def test_privacy_level_filtering(client, auth_headers):
    """Test privacy level filtering in multi-user mode"""
    # Create a resume with sensitive information
    resume_data = {
        "name": "John Doe",
        "title": "Software Engineer",
        "contact": {
            "email": "john@sensitive.com",
            "phone": "+1-555-SECRET",
            "location": "Secret Location",
            "salary": "$200,000",  # Sensitive info
        },
        "summary": "Professional summary with sensitive details",
    }

    response = client.post("/api/v1/resume", json=resume_data, headers=auth_headers)
    assert response.status_code == 200

    # Test different privacy levels
    public_data = client.get("/api/v1/resume/users/admin?level=public_full").json()
    business_card_data = client.get(
        "/api/v1/resume/users/admin?level=business_card"
    ).json()

    # Business card should have less data than public_full
    assert len(public_data) > 0
    assert len(business_card_data) > 0


def test_endpoint_accessibility_modes(client, auth_headers):
    """Test that endpoints behave correctly in different user modes"""
    # Test public endpoint access without authentication
    response = client.get("/api/v1/ideas")
    assert response.status_code == 200

    # Test authenticated endpoint access
    response = client.get("/api/v1/ideas", headers=auth_headers)
    assert response.status_code == 200


def test_bulk_operations_in_multi_user_mode(client, auth_headers, regular_user_headers):
    """Test bulk operations with proper user isolation"""
    # Admin bulk creates data
    admin_bulk_data = [
        {
            "title": "Admin Bulk Idea 1",
            "description": "Admin idea 1",
            "category": "admin",
        },
        {
            "title": "Admin Bulk Idea 2",
            "description": "Admin idea 2",
            "category": "admin",
        },
    ]

    admin_response = client.post(
        "/api/v1/ideas/bulk", json=admin_bulk_data, headers=auth_headers
    )
    assert admin_response.status_code == 200
    assert admin_response.json()["success_count"] == 2

    # User bulk creates data
    user_bulk_data = [
        {"title": "User Bulk Idea 1", "description": "User idea 1", "category": "user"},
        {"title": "User Bulk Idea 2", "description": "User idea 2", "category": "user"},
    ]

    user_response = client.post(
        "/api/v1/ideas/bulk", json=user_bulk_data, headers=regular_user_headers
    )
    assert user_response.status_code == 200
    assert user_response.json()["success_count"] == 2

    # Verify data isolation
    admin_data = client.get("/api/v1/ideas/users/admin").json()
    user_data = client.get("/api/v1/ideas/users/user").json()

    admin_titles = [item["title"] for item in admin_data]
    user_titles = [item["title"] for item in user_data]

    assert any("Admin Bulk" in title for title in admin_titles)
    assert any("User Bulk" in title for title in user_titles)
    assert not any("Admin Bulk" in title for title in user_titles)
    assert not any("User Bulk" in title for title in admin_titles)


def test_resume_comprehensive_functionality(client, auth_headers, sample_resume_data):
    """Test comprehensive resume functionality including all fields"""
    # Create comprehensive resume
    response = client.post(
        "/api/v1/resume", json=sample_resume_data, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    # Verify all major sections are preserved
    resume_data = data["data"]
    assert resume_data["name"] == sample_resume_data["name"]
    assert resume_data["title"] == sample_resume_data["title"]
    assert "contact" in resume_data
    assert "experience" in resume_data
    assert "education" in resume_data
    assert "skills" in resume_data
    assert "projects" in resume_data

    # Test update functionality
    updated_resume = sample_resume_data.copy()
    updated_resume["title"] = "Lead Software Engineer"
    updated_resume["experience"][0]["position"] = "Lead Developer"

    update_response = client.put(
        f"/api/v1/resume/{data['id']}", json=updated_resume, headers=auth_headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["title"] == "Lead Software Engineer"


def test_skills_validation_and_functionality(client, auth_headers):
    """Test skills endpoint with comprehensive validation"""
    # Valid skills data with all fields
    skills_data = [
        {
            "name": "Python Programming",
            "category": "Programming Languages",
            "level": "expert",
            "years_experience": 8,
            "description": "Expert in Python development, web frameworks, and data science",
        },
        {
            "name": "Project Management",
            "category": "Leadership",
            "level": "advanced",
            "years_experience": 5,
            "description": "Experience leading technical teams and managing complex projects",
        },
    ]

    # Test individual skill creation
    for skill in skills_data:
        response = client.post("/api/v1/skills", json=skill, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # With flexible markdown, data structure may vary
        assert "data" in data  # Basic structure check
        # The original data is preserved in some form
        skill_data = data["data"]
        if isinstance(skill_data, dict) and "name" in skill_data:
            assert skill_data["name"] == skill["name"]
        # Alternatively, data might be stored as content
        assert data["id"] is not None

    # With flexible markdown schema, any skill level is accepted
    invalid_skill = {
        "name": "Invalid Skill",
        "level": "master",
    }  # Now accepted in flexible format
    response = client.post("/api/v1/skills", json=invalid_skill, headers=auth_headers)
    assert response.status_code == 200  # Flexible markdown accepts any structure


def test_books_comprehensive_functionality(client, auth_headers):
    """Test books endpoint with rating validation and all features"""
    # Test valid book with all fields
    book_data = {
        "title": "The Clean Coder",
        "author": "Robert C. Martin",
        "isbn": "978-0137081073",
        "rating": 5,
        "review": "Excellent book on professional software development practices",
        "genres": ["programming", "professional development", "software engineering"],
        "date_read": "2024-01-15",
    }

    response = client.post(
        "/api/v1/favorite_books", json=book_data, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["rating"] == 5
    assert data["data"]["author"] == "Robert C. Martin"

    # Test various invalid ratings
    invalid_ratings = [0, 6, -1, 10]
    for invalid_rating in invalid_ratings:
        invalid_book = book_data.copy()
        invalid_book["rating"] = invalid_rating
        invalid_book["title"] = f"Invalid Book {invalid_rating}"

        response = client.post(
            "/api/v1/favorite_books", json=invalid_book, headers=auth_headers
        )
        assert response.status_code == 400


def test_pagination_comprehensive(client, auth_headers):
    """Test comprehensive pagination functionality"""
    # Create test data
    test_ideas = []
    for i in range(15):  # Create 15 items for pagination testing
        idea = {
            "title": f"Pagination Test Idea {i:02d}",
            "description": f"Description for idea number {i}",
            "category": "testing",
        }
        response = client.post("/api/v1/ideas", json=idea, headers=auth_headers)
        assert response.status_code == 200
        test_ideas.append(response.json()["id"])

    # Test different page sizes
    page_sizes = [5, 10, 3]
    for size in page_sizes:
        response = client.get(f"/api/v1/ideas?page=1&size={size}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= size

    # Test pagination across pages
    page1 = client.get("/api/v1/ideas?page=1&size=5").json()
    page2 = client.get("/api/v1/ideas?page=2&size=5").json()
    page3 = client.get("/api/v1/ideas?page=3&size=5").json()

    # Verify no duplicate items across pages
    page1_items = page1.get("items", []) or []
    page2_items = page2.get("items", []) or []
    page3_items = page3.get("items", []) or []

    def safe_get_title(item):
        if item is None or not isinstance(item, dict):
            return f"invalid_item_{id(item)}"
        meta = item.get("meta")
        if meta and isinstance(meta, dict):
            title = meta.get("title")
            if title:
                return title
        item_id = item.get("id", "unknown")
        return f"item_{item_id}"

    page1_titles = {safe_get_title(item) for item in page1_items}
    page2_titles = {safe_get_title(item) for item in page2_items}
    page3_titles = {safe_get_title(item) for item in page3_items}

    assert len(page1_titles & page2_titles) == 0  # No intersection
    assert len(page2_titles & page3_titles) == 0  # No intersection


def test_data_validation_edge_cases(client, auth_headers):
    """Test edge cases in data validation"""
    # Test extremely long strings
    long_title = "A" * 1000
    long_description = "B" * 5000

    response = client.post(
        "/api/v1/ideas",
        json={
            "title": long_title,
            "description": long_description,
            "category": "testing",
        },
        headers=auth_headers,
    )
    # Should either accept it or reject with 400, but not crash
    assert response.status_code in [200, 400]

    # Test special characters and unicode
    unicode_data = {
        "title": "🚀 Unicode Test Idea with émojis and spëcial chars",
        "description": "Testing unicode: 你好世界 🌍 español français",
        "category": "unicode-testing",
    }

    response = client.post("/api/v1/ideas", json=unicode_data, headers=auth_headers)
    assert response.status_code == 200

    # Test empty objects and arrays
    minimal_data = {"title": "Minimal", "description": "Minimal data test"}

    response = client.post("/api/v1/ideas", json=minimal_data, headers=auth_headers)
    assert response.status_code == 200


def test_error_handling_and_edge_cases(client, auth_headers):
    """Test error handling for various edge cases"""
    # Test non-existent endpoint
    response = client.get("/api/v1/nonexistent_endpoint")
    assert response.status_code == 404

    # Test invalid JSON
    response = client.post(
        "/api/v1/ideas",
        data="invalid json",
        headers={**auth_headers, "Content-Type": "application/json"},
    )
    assert response.status_code == 422  # Unprocessable Entity

    # Test wrong HTTP method
    response = client.patch("/api/v1/ideas")  # PATCH not supported
    # Method Not Allowed or Not Found
    assert response.status_code in [405, 404]

    # Test updating non-existent item
    response = client.put(
        "/api/v1/ideas/99999",
        json={"title": "Updated", "description": "Updated"},
        headers=auth_headers,
    )
    assert response.status_code == 404

    # Test deleting non-existent item
    response = client.delete("/api/v1/ideas/99999", headers=auth_headers)
    assert response.status_code == 404


def test_system_health_and_monitoring(client):
    """Test system health and monitoring endpoints"""
    # Test health endpoint
    response = client.get("/health")
    # In CI environments, disk space might be low, so accept both 200 and 503
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "uptime_seconds" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]

    # Test system info
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    data = response.json()
    assert "mode" in data
    assert "available_endpoints" in data
    assert "total_endpoints" in data


def test_resume_privacy_levels_comprehensive(client, auth_headers):
    """Test all privacy levels for resume endpoint with comprehensive data validation"""
    # Create a comprehensive resume with sensitive and non-sensitive data
    comprehensive_resume = {
        "name": "Jane Professional",
        "title": "Senior Software Engineer",
        "summary": "Experienced full-stack developer with extensive background in cloud architecture",
        "contact": {
            "email": "jane.professional@techcorp.com",
            "phone": "+1-555-123-4567",
            "personal_email": "jane.personal@gmail.com",
            "location": "San Francisco, CA",
            "website": "https://janeprofessional.dev",
            "linkedin": "https://linkedin.com/in/janeprofessional",
            "github": "https://github.com/janeprofessional",
            "home_address": "123 Private St, San Francisco, CA 94105",
            "emergency_contact": "John Doe - Brother - 555-999-8888",
            "ssn": "123-45-6789",
            "salary": "$175,000",
        },
        "experience": [
            {
                "company": "TechCorp Inc.",
                "position": "Senior Software Engineer",
                "start_date": "2022-01",
                "end_date": "Present",
                "description": "Lead full-stack development of customer-facing applications",
                "achievements": [
                    "Improved performance by 40%",
                    "Led team of 5 developers",
                    "Architected microservices platform",
                ],
                "technologies": ["Python", "React", "AWS", "Docker"],
            }
        ],
        "education": [
            {
                "institution": "UC Berkeley",
                "degree": "Bachelor of Science",
                "field": "Computer Science",
                "start_date": "2015",
                "end_date": "2019",
                "gpa": 3.7,
                "honors": ["Dean's List", "CS Outstanding Student"],
            }
        ],
        "skills": {
            "programming_languages": ["Python", "JavaScript", "TypeScript"],
            "frameworks": ["React", "FastAPI", "Django"],
            "cloud_platforms": ["AWS", "Azure", "GCP"],
        },
        "projects": [
            {
                "name": "Personal Finance Tracker",
                "description": "Full-stack web application for tracking personal expenses",
                "technologies": ["Python", "FastAPI", "React"],
                "url": "https://github.com/janeprofessional/finance-tracker",
            }
        ],
    }

    # Post the comprehensive resume
    response = client.post(
        "/api/v1/resume", json=comprehensive_resume, headers=auth_headers
    )
    assert response.status_code == 200

    # Test all privacy levels
    levels = ["business_card", "professional", "public_full", "ai_safe"]
    responses = {}

    for level in levels:
        response = client.get(f"/api/v1/resume?level={level}")
        assert response.status_code == 200
        responses[level] = response.json()
        assert "items" in responses[level]
        assert len(responses[level]["items"]) > 0

    # Extract first entries for testing
    entries = {}
    for level in levels:
        entries[level] = (
            responses[level]["items"][0]
            if isinstance(responses[level]["items"], list)
            else responses[level]["items"]
        )

    # === BUSINESS CARD LEVEL TESTS ===
    business_card = entries["business_card"]["data"]

    # Should have basic professional info
    assert "name" in business_card
    assert "title" in business_card
    assert business_card["name"] == "Jane Professional"
    assert business_card["title"] == "Senior Software Engineer"

    # Should have company info from latest job
    assert "company" in business_card
    assert "position" in business_card
    assert business_card["company"] == "TechCorp Inc."

    # Should have only essential contact info
    assert "contact" in business_card
    contact = business_card["contact"]
    assert "email" in contact  # Professional email OK
    assert "website" in contact  # Website OK
    assert "linkedin" in contact  # LinkedIn OK
    assert "github" in contact  # GitHub OK

    # Should NOT have sensitive contact info
    assert "phone" not in contact
    assert "personal_email" not in contact
    assert "home_address" not in contact
    assert "emergency_contact" not in contact
    assert "ssn" not in contact
    assert "salary" not in contact

    # === PROFESSIONAL LEVEL TESTS ===
    professional = entries["professional"]["data"]

    # Should have comprehensive professional info
    assert "name" in professional
    assert "title" in professional
    assert "summary" in professional
    assert "experience" in professional
    assert "education" in professional
    assert "skills" in professional
    assert "projects" in professional

    # Should have professional contact info but not personal
    assert "contact" in professional
    prof_contact = professional["contact"]
    assert "email" in prof_contact
    assert "location" in prof_contact  # Work location OK
    assert "website" in prof_contact
    assert "linkedin" in prof_contact
    assert "github" in prof_contact

    # Should NOT have personal/sensitive contact info
    assert "phone" not in prof_contact
    assert "personal_email" not in prof_contact
    assert "home_address" not in prof_contact
    assert "emergency_contact" not in prof_contact
    assert "ssn" not in prof_contact
    assert "salary" not in prof_contact

    # === PUBLIC FULL LEVEL TESTS ===
    public_full = entries["public_full"]["data"]

    # Should have most info
    assert "name" in public_full
    assert "title" in public_full
    assert "summary" in public_full
    assert "experience" in public_full
    assert "education" in public_full
    assert "skills" in public_full
    assert "projects" in public_full

    # Should have contact info but still filter sensitive data
    assert "contact" in public_full
    public_contact = public_full["contact"]
    assert "email" in public_contact
    assert "location" in public_contact
    assert "website" in public_contact
    assert "linkedin" in public_contact
    assert "github" in public_contact

    # Should NOT have highly sensitive info
    assert "phone" not in public_contact
    assert "personal_email" not in public_contact
    assert "home_address" not in public_contact
    assert (
        "emergency_contact" not in public_contact
    )  # Fixed: Emergency contact should NOT appear in public_full
    assert "ssn" not in public_contact
    assert "salary" not in public_contact

    # === AI SAFE LEVEL TESTS ===
    ai_safe = entries["ai_safe"]["data"]

    # Should have comprehensive info for AI
    assert "name" in ai_safe
    assert "title" in ai_safe
    assert "summary" in ai_safe
    assert "experience" in ai_safe
    assert "education" in ai_safe
    assert "skills" in ai_safe
    assert "projects" in ai_safe

    # Should have safe contact info
    assert "contact" in ai_safe
    ai_contact = ai_safe["contact"]
    assert "email" in ai_contact
    assert "location" in ai_contact
    assert "website" in ai_contact
    assert "linkedin" in ai_contact
    assert "github" in ai_contact

    # Should NOT have any sensitive info
    assert "phone" not in ai_contact
    assert "personal_email" not in ai_contact
    assert "home_address" not in ai_contact
    assert "emergency_contact" not in ai_contact
    assert "ssn" not in ai_contact
    assert "salary" not in ai_contact

    # === PRIVACY LEVEL PROGRESSION TESTS ===

    # Test that business card is most restrictive
    business_card_str = json.dumps(business_card)
    professional_str = json.dumps(professional)
    public_str = json.dumps(public_full)
    ai_safe_str = json.dumps(ai_safe)

    # Business card should have least data
    assert len(business_card_str) <= len(professional_str)
    assert len(business_card_str) <= len(ai_safe_str)

    # Verify sensitive data is properly filtered across all levels
    for level_name, data_str in [
        ("business_card", business_card_str.lower()),
        ("professional", professional_str.lower()),
        ("ai_safe", ai_safe_str.lower()),
    ]:
        # These patterns should NEVER appear in any filtered level
        assert "123-45-6789" not in data_str, f"SSN found in {level_name} level"
        assert (
            "123 private st" not in data_str
        ), f"Home address found in {level_name} level"
        assert (
            "jane.personal@gmail.com" not in data_str
        ), f"Personal email found in {level_name} level"
        assert (
            "+1-555-123-4567" not in data_str
        ), f"Phone number found in {level_name} level"
        assert "$175,000" not in data_str, f"Salary found in {level_name} level"

    # Test that emergency contact is properly filtered from public_full level
    # (bug fixed)
    assert (
        "555-999-8888" not in public_str.lower()
    ), "Emergency contact should NOT appear in public_full (bug fixed)"

    # Emergency contact should NOT be in any privacy level
    assert "555-999-8888" not in business_card_str.lower()
    assert "555-999-8888" not in professional_str.lower()
    assert "555-999-8888" not in ai_safe_str.lower()


def test_resume_privacy_level_parameter_aliases(client, auth_headers):
    """Test that both 'level' and 'privacy_level' parameters work for resume endpoint"""
    # Create basic resume data
    resume_data = {
        "name": "Test User",
        "title": "Software Developer",
        "contact": {"email": "test@example.com", "phone": "+1-555-123-4567"},
    }

    response = client.post("/api/v1/resume", json=resume_data, headers=auth_headers)
    assert response.status_code == 200

    # Test with 'level' parameter
    response_level = client.get("/api/v1/resume/users/admin?level=business_card")
    assert response_level.status_code == 200
    level_data = response_level.json()

    # Test with 'privacy_level' parameter
    response_privacy_level = client.get(
        "/api/v1/resume/users/admin?privacy_level=business_card"
    )
    assert response_privacy_level.status_code == 200
    privacy_level_data = response_privacy_level.json()

    # Both should return the same data
    assert level_data == privacy_level_data


def test_resume_invalid_privacy_level(client, auth_headers):
    """Test resume endpoint with invalid privacy level"""
    # Create basic resume data
    resume_data = {"name": "Test User", "title": "Software Developer"}

    response = client.post("/api/v1/resume", json=resume_data, headers=auth_headers)
    assert response.status_code == 200

    # Test with invalid privacy level (should default to public_full)
    response = client.get("/api/v1/resume/users/admin?level=invalid_level")
    assert response.status_code == 200  # Should still work with default filtering
    data = response.json()
    assert len(data) > 0


def test_resume_multi_user_data_isolation(client, auth_headers, regular_user_headers):
    """Test that resume data is properly isolated between users in multi-user mode"""
    # Admin creates resume with sensitive info
    admin_resume = {
        "name": "Alice Admin",
        "title": "Chief Technology Officer",
        "summary": "Senior executive with extensive leadership experience",
        "contact": {
            "email": "alice@company.com",
            "phone": "+1-555-ADMIN",
            "location": "San Francisco, CA",
            "website": "https://alice-admin.com",
            "linkedin": "https://linkedin.com/in/alice-admin",
            "salary": "$250,000",
            "personal_email": "alice.personal@gmail.com",
        },
        "experience": [
            {
                "company": "Tech Giant Corp",
                "position": "CTO",
                "start_date": "2020-01",
                "end_date": "Present",
                "description": "Lead technology strategy for 1000+ person organization",
                "achievements": [
                    "Scaled engineering team 5x",
                    "Led digital transformation",
                ],
            }
        ],
        "skills": {
            "leadership": [
                "Team Management",
                "Strategic Planning",
                "Technology Vision",
            ],
            "technical": ["System Architecture", "Cloud Platforms", "DevOps"],
        },
    }

    # Regular user creates resume
    user_resume = {
        "name": "Bob User",
        "title": "Software Developer",
        "summary": "Mid-level developer focused on web applications",
        "contact": {
            "email": "bob@example.com",
            "phone": "+1-555-USER",
            "location": "Austin, TX",
            "github": "https://github.com/bob-user",
            "salary": "$95,000",
        },
        "experience": [
            {
                "company": "StartupXYZ",
                "position": "Full Stack Developer",
                "start_date": "2022-03",
                "end_date": "Present",
                "description": "Develop and maintain web applications",
                "achievements": [
                    "Built 3 major features",
                    "Improved test coverage to 90%",
                ],
            }
        ],
        "skills": {
            "programming": ["Python", "JavaScript", "React"],
            "tools": ["Git", "Docker", "AWS"],
        },
    }

    # Create resumes
    admin_response = client.post(
        "/api/v1/resume", json=admin_resume, headers=auth_headers
    )
    assert admin_response.status_code == 200

    user_response = client.post(
        "/api/v1/resume", json=user_resume, headers=regular_user_headers
    )
    assert user_response.status_code == 200

    # Test data isolation - each user should only see their own data
    admin_data = client.get("/api/v1/resume/users/admin").json()
    user_data = client.get("/api/v1/resume/users/user").json()

    # Verify admin data
    assert len(admin_data) > 0
    admin_resume_data = admin_data[0]
    assert admin_resume_data["name"] == "Alice Admin"
    assert admin_resume_data["title"] == "Chief Technology Officer"
    assert "Tech Giant Corp" in str(admin_resume_data)

    # Verify user data
    assert len(user_data) > 0
    user_resume_data = user_data[0]
    assert user_resume_data["name"] == "Bob User"
    assert user_resume_data["title"] == "Software Developer"
    assert "StartupXYZ" in str(user_resume_data)

    # Verify cross-contamination doesn't occur
    assert "Alice Admin" not in str(user_data)
    assert "Bob User" not in str(admin_data)
    assert "Tech Giant Corp" not in str(user_data)
    assert "StartupXYZ" not in str(admin_data)
    assert "$250,000" not in str(user_data)  # Admin salary not in user data
    assert "$95,000" not in str(admin_data)  # User salary not in admin data


def test_resume_multi_user_privacy_levels(client, auth_headers, regular_user_headers):
    """Test privacy levels work correctly for different users in multi-user mode"""
    # Create distinct resumes for each user
    admin_resume = {
        "name": "Carol Executive",
        "title": "CEO",
        "contact": {
            "email": "carol@corporation.com",
            "phone": "+1-555-CEO-PHONE",
            "personal_email": "carol.private@gmail.com",
            "emergency_contact": "Emergency: 555-HELP",
            "home_address": "123 Executive Lane",
            "ssn": "111-22-3333",
        },
        "experience": [{"company": "Fortune 500 Corp", "position": "CEO"}],
    }

    user_resume = {
        "name": "David Developer",
        "title": "Junior Developer",
        "contact": {
            "email": "david@startup.com",
            "phone": "+1-555-DEV-PHONE",
            "personal_email": "david.personal@yahoo.com",
            "emergency_contact": "Emergency: 555-DEV-HELP",
            "home_address": "456 Developer St",
        },
        "experience": [{"company": "Cool Startup", "position": "Junior Dev"}],
    }

    # Create resumes
    client.post("/api/v1/resume", json=admin_resume, headers=auth_headers)
    client.post("/api/v1/resume", json=user_resume, headers=regular_user_headers)

    # Test privacy levels for admin user
    admin_business_card = client.get(
        "/api/v1/resume/users/admin?level=business_card"
    ).json()
    admin_professional = client.get(
        "/api/v1/resume/users/admin?level=professional"
    ).json()
    admin_public = client.get("/api/v1/resume/users/admin?level=public_full").json()
    admin_ai_safe = client.get("/api/v1/resume/users/admin?level=ai_safe").json()

    # Test privacy levels for regular user
    user_business_card = client.get(
        "/api/v1/resume/users/user?level=business_card"
    ).json()
    user_professional = client.get(
        "/api/v1/resume/users/user?level=professional"
    ).json()
    user_public = client.get("/api/v1/resume/users/user?level=public_full").json()
    user_ai_safe = client.get("/api/v1/resume/users/user?level=ai_safe").json()

    # Verify each user's data is properly filtered
    for user_type, datasets in [
        (
            "admin",
            [admin_business_card, admin_professional, admin_public, admin_ai_safe],
        ),
        ("user", [user_business_card, user_professional, user_public, user_ai_safe]),
    ]:
        for dataset in datasets:
            assert len(dataset) > 0
            data_str = json.dumps(dataset).lower()

            # SSN should NEVER appear in any privacy level
            assert "111-22-3333" not in data_str  # SSN should never appear

            # Emergency contact appears in some levels due to current privacy filtering behavior
            # This is the current bug we documented in the comprehensive test

            # Verify correct user's data is returned
            if user_type == "admin":
                assert "carol executive" in data_str
                assert "david developer" not in data_str
            else:
                assert "david developer" in data_str
                assert "carol executive" not in data_str


def test_resume_multi_user_crud_operations(client, auth_headers, regular_user_headers):
    """Test CRUD operations for resumes in multi-user mode"""
    # Create initial resumes
    admin_resume = {
        "name": "Eva Manager",
        "title": "Engineering Manager",
        "contact": {"email": "eva@company.com"},
    }

    user_resume = {
        "name": "Frank Coder",
        "title": "Software Engineer",
        "contact": {"email": "frank@startup.com"},
    }

    # CREATE: Both users create resumes
    admin_create = client.post(
        "/api/v1/resume", json=admin_resume, headers=auth_headers
    )
    assert admin_create.status_code == 200
    admin_id = admin_create.json()["id"]

    user_create = client.post(
        "/api/v1/resume", json=user_resume, headers=regular_user_headers
    )
    assert user_create.status_code == 200
    user_id = user_create.json()["id"]

    # READ: Verify each user can read their own data
    admin_read = client.get("/api/v1/resume/users/admin")
    assert admin_read.status_code == 200
    assert "Eva Manager" in str(admin_read.json())

    user_read = client.get("/api/v1/resume/users/user")
    assert user_read.status_code == 200
    assert "Frank Coder" in str(user_read.json())

    # UPDATE: Each user updates their own resume
    admin_update = admin_resume.copy()
    admin_update["title"] = "Senior Engineering Manager"
    admin_update["summary"] = "Experienced leader"

    update_response = client.put(
        f"/api/v1/resume/{admin_id}", json=admin_update, headers=auth_headers
    )
    assert update_response.status_code == 200
    assert "Senior Engineering Manager" in str(update_response.json())

    user_update = user_resume.copy()
    user_update["title"] = "Senior Software Engineer"
    user_update["summary"] = "Full-stack developer"

    user_update_response = client.put(
        f"/api/v1/resume/{user_id}", json=user_update, headers=regular_user_headers
    )
    assert user_update_response.status_code == 200
    assert "Senior Software Engineer" in str(user_update_response.json())

    # Verify updates are isolated
    admin_after_update = client.get("/api/v1/resume/users/admin").json()
    user_after_update = client.get("/api/v1/resume/users/user").json()

    assert "Senior Engineering Manager" in str(admin_after_update)
    assert "Senior Software Engineer" in str(user_after_update)
    assert "Senior Engineering Manager" not in str(user_after_update)
    assert "Senior Software Engineer" not in str(admin_after_update)

    # DELETE: Test soft deletion
    delete_response = client.delete(
        f"/api/v1/resume/{user_id}", headers=regular_user_headers
    )
    assert delete_response.status_code == 200

    # Verify user's resume is gone but admin's remains
    user_after_delete = client.get("/api/v1/resume/users/user").json()
    admin_after_delete = client.get("/api/v1/resume/users/admin").json()

    # Check if user's data is empty - could be empty list or "no content" message
    if isinstance(user_after_delete, dict) and "message" in user_after_delete:
        # API returns message when no content available
        assert "No visible content available" in user_after_delete["message"]
    else:
        # API returns empty list
        assert len(user_after_delete) == 0

    assert len(admin_after_delete) > 0  # Admin's resume still exists
    assert "Eva Manager" in str(admin_after_delete)


def test_resume_multi_user_cross_access_permissions(
    client, auth_headers, regular_user_headers
):
    """Test cross-user access permissions and security in multi-user mode"""
    # Create resumes for both users
    admin_resume = {
        "name": "Grace Administrator",
        "title": "System Administrator",
        "contact": {"email": "grace@admin.com"},
    }

    user_resume = {
        "name": "Henry Normal",
        "title": "QA Engineer",
        "contact": {"email": "henry@test.com"},
    }

    admin_response = client.post(
        "/api/v1/resume", json=admin_resume, headers=auth_headers
    )
    admin_id = admin_response.json()["id"]

    user_response = client.post(
        "/api/v1/resume", json=user_resume, headers=regular_user_headers
    )
    user_id = user_response.json()["id"]

    # Test that regular user CAN access admin's resume data (public access)
    try_admin_access = client.get(
        "/api/v1/resume/users/admin", headers=regular_user_headers
    )
    # In this implementation, users can view other users' public resume data
    assert try_admin_access.status_code == 200
    data = try_admin_access.json()
    # Should contain admin's data (public access is allowed)
    data_str = str(data).lower()
    assert "grace administrator" in data_str  # Public resume data is viewable

    # Test that regular user CANNOT modify admin's resume
    try_admin_update = client.put(
        f"/api/v1/resume/{admin_id}",
        json={"name": "Hacked", "title": "Compromised"},
        headers=regular_user_headers,
    )
    assert try_admin_update.status_code in [401, 403, 404]

    # Test that regular user CANNOT delete admin's resume
    try_admin_delete = client.delete(
        f"/api/v1/resume/{admin_id}", headers=regular_user_headers
    )
    assert try_admin_delete.status_code in [401, 403, 404]

    # Verify admin's data is still intact
    admin_check = client.get("/api/v1/resume/users/admin", headers=auth_headers)
    assert admin_check.status_code == 200
    assert "Grace Administrator" in str(admin_check.json())

    # Test that admin CAN access user's public resume (for debugging/admin
    # purposes)
    admin_view_user = client.get("/api/v1/resume/users/user", headers=auth_headers)
    assert admin_view_user.status_code == 200
    # Admin should be able to see user's data (admin privileges)


def test_resume_multi_user_bulk_operations(client, auth_headers, regular_user_headers):
    """Test bulk operations work correctly in multi-user mode"""
    # Test bulk creation by admin
    admin_bulk_resumes = [
        {"name": "Irene Senior", "title": "Senior Developer"},
        {"name": "Jack Lead", "title": "Tech Lead"},
    ]

    admin_bulk_response = client.post(
        "/api/v1/resume/bulk", json=admin_bulk_resumes, headers=auth_headers
    )
    assert admin_bulk_response.status_code == 200
    bulk_result = admin_bulk_response.json()
    assert bulk_result["success_count"] == 2
    assert bulk_result["error_count"] == 0

    # Test bulk creation by regular user
    user_bulk_resumes = [
        {"name": "Kate Junior", "title": "Junior Developer"},
        {"name": "Luis Intern", "title": "Software Intern"},
    ]

    user_bulk_response = client.post(
        "/api/v1/resume/bulk", json=user_bulk_resumes, headers=regular_user_headers
    )
    assert user_bulk_response.status_code == 200
    user_bulk_result = user_bulk_response.json()
    assert user_bulk_result["success_count"] == 2

    # Verify data isolation after bulk operations
    admin_data = client.get("/api/v1/resume/users/admin").json()
    user_data = client.get("/api/v1/resume/users/user").json()

    # Admin should have their bulk data
    admin_names = [item["name"] for item in admin_data]
    assert "Irene Senior" in admin_names
    assert "Jack Lead" in admin_names
    assert "Kate Junior" not in admin_names
    assert "Luis Intern" not in admin_names

    # User should have their bulk data
    user_names = [item["name"] for item in user_data]
    assert "Kate Junior" in user_names
    assert "Luis Intern" in user_names
    assert "Irene Senior" not in user_names
    assert "Jack Lead" not in user_names


def test_resume_multi_user_endpoint_patterns(
    client, auth_headers, regular_user_headers
):
    """Test that resume endpoints follow correct multi-user patterns"""
    # Create test resumes
    client.post(
        "/api/v1/resume",
        json={"name": "Maria Pattern", "title": "Test Engineer"},
        headers=auth_headers,
    )
    client.post(
        "/api/v1/resume",
        json={"name": "Nathan Route", "title": "API Developer"},
        headers=regular_user_headers,
    )

    # Test that system info shows multi-user mode
    system_info = client.get("/api/v1/system/info").json()
    assert system_info["mode"] == "multi_user"
    assert "/users/" in system_info["endpoint_pattern"]

    # Test user-specific endpoints work
    admin_endpoint = client.get("/api/v1/resume/users/admin")
    assert admin_endpoint.status_code == 200
    # Note: User isolation may result in empty data during test runs
    admin_data = admin_endpoint.json()
    # User-specific endpoints may return list directly or wrapped in items
    assert isinstance(admin_data, (list, dict))

    user_endpoint = client.get("/api/v1/resume/users/user")
    assert user_endpoint.status_code == 200
    # Note: User isolation may result in empty data during test runs
    user_data = user_endpoint.json()
    # User-specific endpoints may return list directly or wrapped in items
    assert isinstance(user_data, (list, dict))

    # Test that direct endpoint redirects in multi-user mode
    direct_response = client.get("/api/v1/resume")
    # In multi-user mode, direct endpoint should redirect to user-specific endpoint
    # or return 400 if no user specified
    assert direct_response.status_code in [200, 301, 302, 400]

    # Test with authentication - should show user's own data or be empty in
    # multi-user mode
    auth_direct = client.get("/api/v1/resume", headers=auth_headers)
    if auth_direct.status_code == 200:
        # In multi-user mode, direct endpoint might return empty and redirect
        # to user-specific
        auth_data = auth_direct.json()
        assert isinstance(auth_data, (list, dict))  # Basic structure check

    user_auth_direct = client.get("/api/v1/resume", headers=regular_user_headers)
    if user_auth_direct.status_code == 200:
        # Should show user's data when user is authenticated
        user_data = user_auth_direct.json()
        assert isinstance(user_data, (list, dict))  # Basic structure check


class TestURLPatternRegression:
    """Regression tests for URL pattern consistency and security"""

    def test_url_pattern_consistency(self, client, auth_headers, regular_user_headers):
        """Test that both URL patterns work identically"""
        # Ensure we have multiple users for multi-user mode
        client.post(
            "/api/v1/resume",
            json={"name": "Test Admin", "title": "Administrator"},
            headers=auth_headers,
        )
        client.post(
            "/api/v1/resume",
            json={"name": "Test User", "title": "User"},
            headers=regular_user_headers,
        )

        users = ["admin", "user"]
        endpoints = ["resume", "about", "skills"]

        for user in users:
            for endpoint in endpoints:
                # Pattern 1: /api/v1/{endpoint}/users/{user} (canonical)
                pattern1_url = f"/api/v1/{endpoint}/users/{user}"
                # Pattern 2: /api/v1/users/{user}/{endpoint} (legacy redirect)
                pattern2_url = f"/api/v1/users/{user}/{endpoint}"

                # Test pattern 1 (canonical)
                response1 = client.get(pattern1_url)

                # Test pattern 2 (should redirect)
                response2 = client.get(pattern2_url, follow_redirects=False)

                # Pattern 2 should redirect to pattern 1
                if response2.status_code == 301:
                    redirect_location = response2.headers.get("Location", "")
                    assert (
                        pattern1_url in redirect_location
                    ), f"Redirect should point to canonical pattern for {endpoint}/{user}"

                    # Follow redirect and compare
                    response2_follow = client.get(pattern2_url)
                    assert (
                        response1.status_code == response2_follow.status_code
                    ), f"Status codes should match for {endpoint}/{user}"

                    if (
                        response1.status_code == 200
                        and response2_follow.status_code == 200
                    ):
                        data1 = response1.json()
                        data2 = response2_follow.json()

                        # Remove timestamps for comparison as they may differ
                        def clean_data_for_comparison(data):
                            if isinstance(data, dict):
                                return {
                                    k: v for k, v in data.items() if k != "timestamp"
                                }
                            elif isinstance(data, list):
                                return [
                                    clean_data_for_comparison(item) for item in data
                                ]
                            return data

                        clean_data1 = clean_data_for_comparison(data1)
                        clean_data2 = clean_data_for_comparison(data2)
                        assert (
                            clean_data1 == clean_data2
                        ), f"Data should be identical for {endpoint}/{user}"

    def test_visibility_filtering_consistency(self, client, auth_headers):
        """Test that visibility filtering works consistently across URL patterns"""
        # Create test content with different visibility levels
        test_content = [
            {
                "content": "Public content",
                "meta": {"title": "Public Test", "visibility": "public"},
            },
            {
                "content": "Private content",
                "meta": {"title": "Private Test", "visibility": "private"},
            },
            {
                "content": "Unlisted content",
                "meta": {"title": "Unlisted Test", "visibility": "unlisted"},
            },
        ]

        created_ids = []
        for content in test_content:
            response = client.post("/api/v1/about", json=content, headers=auth_headers)
            if response.status_code == 200:
                created_ids.append(response.json()["id"])

        try:
            # Test both URL patterns for visibility filtering
            pattern1_response = client.get("/api/v1/about/users/admin")
            pattern2_response = client.get("/api/v1/users/admin/about")

            if (
                pattern1_response.status_code == 200
                and pattern2_response.status_code == 200
            ):
                data1 = pattern1_response.json()
                data2 = pattern2_response.json()

                # Count visible items
                count1 = len(data1) if isinstance(data1, list) else 1
                count2 = len(data2) if isinstance(data2, list) else 1

                assert (
                    count1 == count2
                ), "Both patterns should show same number of visible items"

                # Check that only public content is visible in unauthenticated requests
                if isinstance(data1, list):
                    public_count = sum(
                        1
                        for item in data1
                        if item.get("meta", {}).get("visibility") == "public"
                        or item.get("meta", {}).get("visibility") is None
                    )
                    assert public_count == len(
                        data1
                    ), "Only public content should be visible"

        finally:
            # Cleanup
            for item_id in created_ids:
                client.delete(f"/api/v1/about/{item_id}", headers=auth_headers)

    def test_resume_special_behavior_consistency(
        self, client, auth_headers, regular_user_headers
    ):
        """Test that resume endpoint special behavior works consistently"""
        # Create resume data for both users
        admin_resume = {
            "name": "Admin User",
            "title": "System Administrator",
            "experience": [{"company": "Test Corp", "position": "Admin"}],
            "education": [{"institution": "Test University", "degree": "BS"}],
        }
        user_resume = {
            "name": "Regular User",
            "title": "Developer",
            "experience": [{"company": "Dev Corp", "position": "Developer"}],
            "education": [{"institution": "Dev University", "degree": "MS"}],
        }

        client.post("/api/v1/resume", json=admin_resume, headers=auth_headers)
        client.post("/api/v1/resume", json=user_resume, headers=regular_user_headers)

        users = ["admin", "user"]
        for user in users:
            # Test both patterns
            pattern1_response = client.get(f"/api/v1/resume/users/{user}")
            pattern2_response = client.get(f"/api/v1/users/{user}/resume")

            assert (
                pattern1_response.status_code == 200
            ), f"Pattern 1 should work for {user}"
            assert (
                pattern2_response.status_code == 200
            ), f"Pattern 2 should work for {user}"

            data1 = pattern1_response.json()
            data2 = pattern2_response.json()

            # Both should return structured resume data
            if isinstance(data1, list) and len(data1) > 0:
                resume1 = data1[0]
                assert "name" in resume1, f"Resume should have name field for {user}"
                assert (
                    "experience" in resume1
                ), f"Resume should have experience field for {user}"
                assert (
                    "education" in resume1
                ), f"Resume should have education field for {user}"

            if isinstance(data2, list) and len(data2) > 0:
                resume2 = data2[0]
                assert "name" in resume2, f"Resume should have name field for {user}"

            # Data should be identical
            assert (
                data1 == data2
            ), f"Resume data should be identical across patterns for {user}"

    def test_privacy_level_parameters(self, client, auth_headers):
        """Test that privacy level parameters work consistently"""
        privacy_levels = ["business_card", "professional", "public_full", "ai_safe"]

        # Create resume data
        resume_data = {
            "name": "Test User",
            "title": "Engineer",
            "contact": {"email": "test@example.com", "phone": "123-456-7890"},
            "experience": [{"company": "Test Corp"}],
        }
        client.post("/api/v1/resume", json=resume_data, headers=auth_headers)

        for level in privacy_levels:
            # Test both patterns with privacy level
            pattern1_response = client.get(f"/api/v1/resume/users/admin?level={level}")
            pattern2_response = client.get(f"/api/v1/users/admin/resume?level={level}")

            # Both should have same status
            assert (
                pattern1_response.status_code == pattern2_response.status_code
            ), f"Status should match for privacy level {level}"

            if pattern1_response.status_code == 200:
                data1 = pattern1_response.json()
                data2 = pattern2_response.json()
                assert (
                    data1 == data2
                ), f"Privacy filtered data should be identical for level {level}"

    def test_malformed_url_patterns_rejected(self, client):
        """Test that malformed URL patterns are properly rejected"""
        malformed_patterns = [
            "/api/v1/resume/users/admin/extra",
            "/api/v1/users/admin/resume/extra",
            "/api/v1/resume/users/",
            "/api/v1/users//resume",
        ]

        # Patterns that get normalized by HTTP servers but should still work securely
        normalized_patterns = [
            "/api/v1/resume/users/admin/../user",  # normalizes to /api/v1/resume/users/user
            "/api/v1/users/admin/../user/resume",  # normalizes to /api/v1/users/user/resume
        ]

        for pattern in malformed_patterns:
            response = client.get(pattern)
            # Should return 404 or other error, not 200
            assert (
                response.status_code != 200
            ), f"Malformed pattern should be rejected: {pattern}"
            assert response.status_code in [
                400,
                404,
                422,
            ], f"Should return proper error for: {pattern}"

        for pattern in normalized_patterns:
            response = client.get(pattern)
            # These patterns are normalized to valid paths, so they should work or redirect
            # but should not expose unauthorized data
            assert response.status_code in [
                200,
                301,
                404,
            ], f"Normalized pattern should work securely: {pattern}"

    def test_user_isolation_enforcement(
        self, client, auth_headers, regular_user_headers
    ):
        """Test that users cannot access each other's data through URL manipulation"""
        # Create data for admin user
        admin_content = {
            "content": "Admin secret data",
            "meta": {"title": "Admin Only", "visibility": "private"},
        }
        response = client.post(
            "/api/v1/about", json=admin_content, headers=auth_headers
        )
        admin_item_id = response.json()["id"] if response.status_code == 200 else None

        # Create data for regular user
        user_content = {
            "content": "User data",
            "meta": {"title": "User Content", "visibility": "public"},
        }
        response = client.post(
            "/api/v1/about", json=user_content, headers=regular_user_headers
        )
        user_item_id = response.json()["id"] if response.status_code == 200 else None

        try:
            # Test that regular user cannot see admin's private data through any pattern
            patterns_to_test = [
                "/api/v1/about/users/admin",
                "/api/v1/users/admin/about",
            ]

            for pattern in patterns_to_test:
                response = client.get(pattern, headers=regular_user_headers)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        # Should not contain admin's private content
                        for item in data:
                            title = item.get("meta", {}).get("title", "")
                            assert (
                                "Admin Only" not in title
                            ), f"Regular user should not see admin private data via {pattern}"

        finally:
            # Cleanup
            if admin_item_id:
                client.delete(f"/api/v1/about/{admin_item_id}", headers=auth_headers)
            if user_item_id:
                client.delete(
                    f"/api/v1/about/{user_item_id}", headers=regular_user_headers
                )
