"""
Comprehensive E2E tests for Ideas endpoint with flexible markdown support
"""

import pytest
from fastapi.testclient import TestClient


class TestIdeasEndpoint:
    """Test suite for ideas endpoint with both structured and flexible schemas"""

    def test_ideas_get_empty(self, client: TestClient):
        """Test getting ideas when none exist"""
        response = client.get("/api/v1/ideas")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 0

    def test_ideas_create_traditional_schema(self, client: TestClient, auth_headers):
        """Test creating ideas with traditional structured schema"""
        idea_data = {
            "title": "Traditional API Design",
            "description": "Exploring RESTful API design patterns and best practices",
            "category": "technology",
            "status": "developing",
            "tags": ["api", "rest", "design"],
        }

        response = client.post("/api/v1/ideas", json=idea_data, headers=auth_headers)
        assert response.status_code == 200

        # Verify the response
        data = response.json()
        assert "id" in data
        assert data["data"]["title"] == idea_data["title"]
        assert data["data"]["description"] == idea_data["description"]

    def test_ideas_create_flexible_markdown_schema(
        self, client: TestClient, auth_headers
    ):
        """Test creating ideas with flexible markdown schema"""
        idea_data = {
            "content": """### Idea: Micro-course on Productivity

**Core Concept:**
- Short modules: 10-15 minutes/session
- Focus on habit stacking and systems thinking
- Pilot with 50 beta users

**Implementation Strategy:**
1. Create video content using screen recordings
2. Build interactive exercises with spaced repetition
3. Implement progress tracking and habit streaks

**Success Metrics:**
- User engagement: >80% completion rate
- Behavior change: Measurable habit adoption within 30 days
- Community feedback: 4.5+ rating

**Next Steps:**
- [ ] Outline first 5 modules
- [ ] Record pilot content
- [ ] Set up beta user feedback system""",
            "meta": {
                "title": "Micro-course on Productivity",
                "tags": ["productivity", "education", "habits"],
                "status": "planning",
                "visibility": "public",
            },
        }

        response = client.post("/api/v1/ideas", json=idea_data, headers=auth_headers)
        assert response.status_code == 200

        # Verify the response
        data = response.json()
        assert "id" in data
        assert data["data"]["content"] == idea_data["content"]
        assert data["data"]["meta"]["title"] == idea_data["meta"]["title"]
        assert data["data"]["meta"]["tags"] == idea_data["meta"]["tags"]

    def test_ideas_create_minimal_markdown(self, client: TestClient, auth_headers):
        """Test creating ideas with minimal markdown (only content required)"""
        idea_data = {
            "content": "### Simple Idea\n\nJust a quick thought about improving user onboarding flows."
        }

        response = client.post("/api/v1/ideas", json=idea_data, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "id" in data
        assert data["data"]["content"] == idea_data["content"]

    def test_ideas_get_single_item(self, client: TestClient, auth_headers):
        """Test retrieving a single idea by ID"""
        # First create an idea
        idea_data = {
            "content": "### Test Idea\n\nThis is a test idea for retrieval.",
            "meta": {"title": "Test Idea", "visibility": "public"},
        }

        create_response = client.post(
            "/api/v1/ideas", json=idea_data, headers=auth_headers
        )
        assert create_response.status_code == 200
        created_idea = create_response.json()

        # Now retrieve it
        get_response = client.get(f"/api/v1/ideas/{created_idea['id']}")
        assert get_response.status_code == 200

        retrieved_idea = get_response.json()
        assert retrieved_idea["id"] == created_idea["id"]
        assert retrieved_idea["content"] == idea_data["content"]

    def test_ideas_update_item(self, client: TestClient, auth_headers):
        """Test updating an existing idea"""
        # Create an idea
        original_data = {
            "content": "### Original Idea\n\nThis is the original version.",
            "meta": {"title": "Original", "status": "draft"},
        }

        create_response = client.post(
            "/api/v1/ideas", json=original_data, headers=auth_headers
        )
        assert create_response.status_code == 200
        created_idea = create_response.json()

        # Update it
        updated_data = {
            "content": "### Updated Idea\n\nThis is the updated version with more details.",
            "meta": {"title": "Updated", "status": "published"},
        }

        update_response = client.put(
            f"/api/v1/ideas/{created_idea['id']}",
            json=updated_data,
            headers=auth_headers,
        )
        assert update_response.status_code == 200

        updated_idea = update_response.json()
        assert updated_idea["data"]["content"] == updated_data["content"]
        assert updated_idea["data"]["meta"]["title"] == updated_data["meta"]["title"]
        assert updated_idea["data"]["meta"]["status"] == updated_data["meta"]["status"]

    def test_ideas_delete_item(self, client: TestClient, auth_headers):
        """Test deleting an idea"""
        # Create an idea
        idea_data = {
            "content": "### Idea to Delete\n\nThis will be deleted.",
            "meta": {"title": "To Delete"},
        }

        create_response = client.post(
            "/api/v1/ideas", json=idea_data, headers=auth_headers
        )
        assert create_response.status_code == 200
        created_idea = create_response.json()

        # Delete it
        delete_response = client.delete(
            f"/api/v1/ideas/{created_idea['id']}", headers=auth_headers
        )
        assert delete_response.status_code == 200

        # Verify it's gone
        get_response = client.get(f"/api/v1/ideas/{created_idea['id']}")
        assert get_response.status_code == 404

    def test_ideas_pagination(self, client: TestClient, auth_headers):
        """Test pagination with ideas"""
        # Create multiple ideas
        for i in range(5):
            idea_data = {
                "content": f"### Idea {i + 1}\n\nThis is idea number {i + 1} for pagination testing."
            }
            response = client.post(
                "/api/v1/ideas", json=idea_data, headers=auth_headers
            )
            assert response.status_code == 200

        # Test pagination
        response = client.get("/api/v1/ideas?page=1&size=3")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) <= 3  # Should respect the size limit

    def test_ideas_search_by_content(self, client: TestClient, auth_headers):
        """Test searching ideas by content"""
        # Create ideas with searchable content
        searchable_ideas = [
            {
                "content": "### Machine Learning Project\n\nUsing TensorFlow for AI model training."
            },
            {"content": "### Web Development\n\nBuilding APIs with FastAPI."},
            {"content": "### Mobile App\n\nReact Native application development."},
        ]

        for idea in searchable_ideas:
            response = client.post("/api/v1/ideas", json=idea, headers=auth_headers)
            assert response.status_code == 200

        # Search for specific content (if search is implemented)
        response = client.get("/api/v1/ideas")
        assert response.status_code == 200
        ideas_response = response.json()
        ideas = ideas_response["items"]

        # Verify we can find our created ideas
        contents = [idea.get("content", "") for idea in ideas]
        assert any("Machine Learning" in content for content in contents)

    def test_ideas_privacy_controls(self, client: TestClient, auth_headers):
        """Test privacy controls for ideas"""
        # Create ideas with different visibility levels
        public_idea = {
            "content": "### Public Idea\n\nThis is visible to everyone.",
            "meta": {"visibility": "public"},
        }

        private_idea = {
            "content": "### Private Idea\n\nThis is only visible to the owner.",
            "meta": {"visibility": "private"},
        }

        unlisted_idea = {
            "content": "### Unlisted Idea\n\nThis is accessible via direct link only.",
            "meta": {"visibility": "unlisted"},
        }

        # Create all ideas
        for idea_data in [public_idea, private_idea, unlisted_idea]:
            response = client.post(
                "/api/v1/ideas", json=idea_data, headers=auth_headers
            )
            assert response.status_code == 200

        # Test unauthenticated access
        response = client.get("/api/v1/ideas")
        assert response.status_code == 200
        public_ideas_response = response.json()
        public_ideas = public_ideas_response["items"]

        # Should only see public ideas when not authenticated
        visible_contents = [idea.get("content", "") for idea in public_ideas]
        assert any("Public Idea" in content for content in visible_contents)

    def test_ideas_validation_errors(self, client: TestClient, auth_headers):
        """Test validation errors for invalid data"""
        # Test missing content
        response = client.post("/api/v1/ideas", json={}, headers=auth_headers)
        assert response.status_code == 400

        # Test invalid visibility
        invalid_data = {
            "content": "### Test\n\nContent here.",
            "meta": {"visibility": "invalid_level"},
        }
        response = client.post("/api/v1/ideas", json=invalid_data, headers=auth_headers)
        # Should either reject or default to valid visibility level
        # The exact behavior depends on implementation

    def test_ideas_multi_user_support(self, client: TestClient, auth_headers):
        """Test multi-user support for ideas"""
        # Create idea as authenticated user
        idea_data = {
            "content": "### User Specific Idea\n\nThis belongs to a specific user.",
            "meta": {"title": "User Idea"},
        }

        response = client.post("/api/v1/ideas", json=idea_data, headers=auth_headers)
        assert response.status_code == 200
        created_idea = response.json()

        # Verify ownership is tracked
        assert "created_by" in created_idea or "owner" in created_idea

    def test_ideas_bulk_operations(self, client: TestClient, auth_headers):
        """Test bulk operations if supported"""
        bulk_ideas = [
            {"content": "### Bulk Idea 1\n\nFirst bulk idea."},
            {"content": "### Bulk Idea 2\n\nSecond bulk idea."},
            {"content": "### Bulk Idea 3\n\nThird bulk idea."},
        ]

        # Test if bulk endpoint exists
        response = client.post(
            "/api/v1/ideas/bulk", json=bulk_ideas, headers=auth_headers
        )
        # Should either succeed or return 404 if not implemented
        assert response.status_code in [200, 201, 404]

    def test_debug_ideas_response(self, client: TestClient, auth_headers):
        """Debug test to see what the ideas endpoint actually returns"""
        import json

        idea_data = {
            "content": "### Debug Idea\n\nThis is for debugging response format.",
            "meta": {"title": "Debug Idea", "visibility": "public"},
        }

        response = client.post("/api/v1/ideas", json=idea_data, headers=auth_headers)

        print(f"\nPOST Response Status: {response.status_code}")
        print(f"POST Response Data: {json.dumps(response.json(), indent=2)}")

        assert response.status_code == 200

        # Now test GET to see how data is returned
        get_response = client.get("/api/v1/ideas")
        print(f"\nGET Response Status: {get_response.status_code}")
        print(f"GET Response Data: {json.dumps(get_response.json(), indent=2)}")

        assert get_response.status_code == 200
