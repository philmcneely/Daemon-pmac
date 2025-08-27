"""
End-to-end tests for the skills endpoint with flexible markdown support.

These tests validate the skills endpoint which supports both:
1. New flexible markdown format: {content, meta}
2. Legacy structured format: {name, category, level, years_experience, description}

The endpoint should maintain backward compatibility while enabling rich markdown content.
"""

import pytest
from fastapi.testclient import TestClient


class TestSkillsEndpoint:
    """Test suite for the skills endpoint with flexible markdown support."""

    def test_skills_create_with_markdown(self, client: TestClient, auth_headers):
        """Test creating a skill with flexible markdown content"""
        skill_data = {
            "content": "### Python (Intermediate)\n\n- 5 years of practical use\n- Focus: data processing, web backends\n- Current learning: async programming\n\n**Recent Projects:**\n- FastAPI personal API system\n- Data pipeline automation",
            "meta": {
                "title": "Python",
                "category": "Programming Languages",
                "level": "Intermediate",
                "tags": ["python", "backend", "apis"],
                "visibility": "public",
            },
        }

        response = client.post("/api/v1/skills", json=skill_data, headers=auth_headers)
        assert response.status_code == 200

        created_skill = response.json()
        assert created_skill["id"]
        assert created_skill["data"]["content"] == skill_data["content"]
        assert created_skill["data"]["meta"]["title"] == "Python"
        assert created_skill["data"]["meta"]["category"] == "Programming Languages"
        assert created_skill["data"]["meta"]["level"] == "Intermediate"
        assert created_skill["data"]["meta"]["tags"] == ["python", "backend", "apis"]

    def test_skills_create_with_legacy_format(self, client: TestClient, auth_headers):
        """Test creating a skill with legacy structured format"""
        skill_data = {
            "name": "JavaScript",
            "category": "Programming Languages",
            "level": "advanced",
            "years_experience": 8,
            "description": "Full-stack JavaScript development with React and Node.js",
        }

        response = client.post("/api/v1/skills", json=skill_data, headers=auth_headers)
        assert response.status_code == 200

        created_skill = response.json()
        assert created_skill["id"]
        assert created_skill["data"]["name"] == "JavaScript"
        assert created_skill["data"]["category"] == "Programming Languages"
        assert created_skill["data"]["level"] == "advanced"
        assert created_skill["data"]["years_experience"] == 8
        assert created_skill["data"]["description"]

    def test_skills_create_with_html_entities_in_markdown(
        self, client: TestClient, auth_headers
    ):
        """Test that HTML entities in markdown content are properly handled"""
        skill_data = {
            "content": "### Docker &amp; Kubernetes\n\nContainer orchestration expertise:\n- Docker for development &amp; production\n- K8s deployments &lt; 100ms latency\n- Service mesh with Istio\n\n*Note:* Experience with &quot;cloud-native&quot; architectures.",
            "meta": {
                "title": "Docker & Kubernetes",
                "category": "DevOps",
                "tags": ["docker", "kubernetes", "devops"],
                "visibility": "public",
            },
        }

        response = client.post("/api/v1/skills", json=skill_data, headers=auth_headers)
        assert response.status_code == 200

        created_skill = response.json()
        assert "Docker & Kubernetes" in created_skill["data"]["content"]
        assert "< 100ms latency" in created_skill["data"]["content"]
        assert '"cloud-native"' in created_skill["data"]["content"]

    def test_skills_list_empty(self, client: TestClient, auth_headers):
        """Test listing skills when none exist"""
        response = client.get("/api/v1/skills", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_skills_list_with_items(self, client: TestClient, auth_headers):
        """Test listing skills after creating some"""
        # Create multiple skills
        skills = [
            {
                "content": "### React (Advanced)\n\nBuilt 10+ production apps with React",
                "meta": {"title": "React", "category": "Frontend", "level": "Advanced"},
            },
            {
                "name": "Python",
                "category": "Backend",
                "level": "intermediate",
                "years_experience": 5,
                "description": "Python for web development and data processing",
            },
        ]

        created_ids = []
        for skill_data in skills:
            response = client.post(
                "/api/v1/skills", json=skill_data, headers=auth_headers
            )
            assert response.status_code == 200
            created_ids.append(response.json()["id"])

        # List all skills
        response = client.get("/api/v1/skills", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data) >= 2
        assert any(item.get("content", "").startswith("### React") for item in data)
        assert any(item.get("name") == "Python" for item in data)

        # Cleanup
        for skill_id in created_ids:
            client.delete(f"/api/v1/skills/{skill_id}", headers=auth_headers)

    def test_skills_get_single_markdown_format(self, client: TestClient, auth_headers):
        """Test retrieving a single skill in markdown format"""
        skill_data = {
            "content": "### TypeScript (Intermediate)\n\nStrong typing for JavaScript projects:\n- Type safety in large codebases\n- Interface design patterns\n- Generic programming",
            "meta": {
                "title": "TypeScript",
                "category": "Programming Languages",
                "level": "Intermediate",
                "tags": ["typescript", "javascript", "frontend"],
            },
        }

        # Create skill
        response = client.post("/api/v1/skills", json=skill_data, headers=auth_headers)
        assert response.status_code == 200
        skill_id = response.json()["id"]

        # Retrieve skill
        response = client.get(f"/api/v1/skills/{skill_id}", headers=auth_headers)
        assert response.status_code == 200

        skill = response.json()
        assert skill["id"] == skill_id
        assert skill["content"] == skill_data["content"]
        assert skill["meta"]["title"] == "TypeScript"
        assert skill["meta"]["category"] == "Programming Languages"
        assert skill["meta"]["level"] == "Intermediate"

        # Cleanup
        client.delete(f"/api/v1/skills/{skill_id}", headers=auth_headers)

    def test_skills_get_single_legacy_format(self, client: TestClient, auth_headers):
        """Test retrieving a single skill in legacy format"""
        skill_data = {
            "name": "SQL",
            "category": "Databases",
            "level": "advanced",
            "years_experience": 6,
            "description": "Complex queries, performance optimization, database design",
        }

        # Create skill
        response = client.post("/api/v1/skills", json=skill_data, headers=auth_headers)
        assert response.status_code == 200
        skill_id = response.json()["id"]

        # Retrieve skill
        response = client.get(f"/api/v1/skills/{skill_id}", headers=auth_headers)
        assert response.status_code == 200

        skill = response.json()
        assert skill["id"] == skill_id
        assert skill["name"] == "SQL"
        assert skill["category"] == "Databases"
        assert skill["level"] == "advanced"
        assert skill["years_experience"] == 6

        # Cleanup
        client.delete(f"/api/v1/skills/{skill_id}", headers=auth_headers)

    def test_skills_update_markdown_format(self, client: TestClient, auth_headers):
        """Test updating a skill with markdown content"""
        # Create initial skill
        initial_data = {
            "content": "### Go (Beginner)\n\nJust started learning Go for microservices",
            "meta": {
                "title": "Go",
                "category": "Programming Languages",
                "level": "Beginner",
            },
        }

        response = client.post(
            "/api/v1/skills", json=initial_data, headers=auth_headers
        )
        assert response.status_code == 200
        skill_id = response.json()["id"]

        # Update skill
        updated_data = {
            "content": "### Go (Intermediate)\n\nBuilt several microservices with Go:\n- REST APIs with Gin\n- gRPC services\n- Concurrent programming with goroutines",
            "meta": {
                "title": "Go",
                "category": "Programming Languages",
                "level": "Intermediate",
                "tags": ["go", "microservices", "grpc"],
            },
        }

        response = client.put(
            f"/api/v1/skills/{skill_id}", json=updated_data, headers=auth_headers
        )
        assert response.status_code == 200

        updated_skill = response.json()
        assert updated_skill["data"]["content"] == updated_data["content"]
        assert updated_skill["data"]["meta"]["level"] == "Intermediate"
        assert updated_skill["data"]["meta"]["tags"] == ["go", "microservices", "grpc"]

        # Cleanup
        client.delete(f"/api/v1/skills/{skill_id}", headers=auth_headers)

    def test_skills_update_legacy_format(self, client: TestClient, auth_headers):
        """Test updating a skill with legacy format"""
        # Create initial skill
        initial_data = {
            "name": "AWS",
            "category": "Cloud Platforms",
            "level": "beginner",
            "years_experience": 1,
            "description": "Basic EC2 and S3 usage",
        }

        response = client.post(
            "/api/v1/skills", json=initial_data, headers=auth_headers
        )
        assert response.status_code == 200
        skill_id = response.json()["id"]

        # Update skill
        updated_data = {
            "name": "AWS",
            "category": "Cloud Platforms",
            "level": "intermediate",
            "years_experience": 3,
            "description": "EC2, S3, Lambda, RDS, CloudFormation deployment experience",
        }

        response = client.put(
            f"/api/v1/skills/{skill_id}", json=updated_data, headers=auth_headers
        )
        assert response.status_code == 200

        updated_skill = response.json()
        assert updated_skill["data"]["level"] == "intermediate"
        assert updated_skill["data"]["years_experience"] == 3
        assert "CloudFormation" in updated_skill["data"]["description"]

        # Cleanup
        client.delete(f"/api/v1/skills/{skill_id}", headers=auth_headers)

    def test_skills_delete(self, client: TestClient, auth_headers):
        """Test deleting a skill"""
        skill_data = {
            "content": "### Rust (Learning)\n\nCurrently exploring systems programming with Rust",
            "meta": {"title": "Rust", "category": "Programming Languages"},
        }

        # Create skill
        response = client.post("/api/v1/skills", json=skill_data, headers=auth_headers)
        assert response.status_code == 200
        skill_id = response.json()["id"]

        # Delete skill
        response = client.delete(f"/api/v1/skills/{skill_id}", headers=auth_headers)
        assert response.status_code == 200

        # Verify deletion
        response = client.get(f"/api/v1/skills/{skill_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_skills_create_validation_error_no_content_or_name(
        self, client: TestClient, auth_headers
    ):
        """Test validation error when neither content nor name is provided"""
        skill_data = {
            "meta": {
                "category": "Programming Languages",
                "level": "Intermediate",
            }
        }

        response = client.post("/api/v1/skills", json=skill_data, headers=auth_headers)
        assert response.status_code == 400

    def test_skills_privacy_controls(self, client: TestClient, auth_headers):
        """Test privacy controls for skills"""
        # Create private skill
        private_skill = {
            "content": "### Proprietary Framework\n\nExperience with internal company tools",
            "meta": {
                "title": "Proprietary Framework",
                "category": "Internal Tools",
                "visibility": "private",
            },
        }

        response = client.post(
            "/api/v1/skills", json=private_skill, headers=auth_headers
        )
        assert response.status_code == 200
        private_skill_id = response.json()["id"]

        # Create public skill
        public_skill = {
            "content": "### Open Source Contribution\n\nContributed to major open source projects",
            "meta": {
                "title": "Open Source",
                "category": "Community",
                "visibility": "public",
            },
        }

        response = client.post(
            "/api/v1/skills", json=public_skill, headers=auth_headers
        )
        assert response.status_code == 200
        public_skill_id = response.json()["id"]

        # Both should be visible to authenticated user
        response = client.get("/api/v1/skills", headers=auth_headers)
        assert response.status_code == 200
        skills_list = response.json()

        # Check if both skills exist in the list
        private_found = any(
            "Proprietary Framework" in item.get("content", "") for item in skills_list
        )
        public_found = any(
            "Open Source Contribution" in item.get("content", "")
            for item in skills_list
        )
        assert private_found
        assert public_found

        # Cleanup
        client.delete(f"/api/v1/skills/{private_skill_id}", headers=auth_headers)
        client.delete(f"/api/v1/skills/{public_skill_id}", headers=auth_headers)
