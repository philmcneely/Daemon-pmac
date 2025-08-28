"""
Module: tests.e2e.test_skills_matrix_e2e
Description: End-to-end tests for skills matrix endpoint with advanced querying

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28

Dependencies:
- pytest: 7.4.3+ - Testing framework
- fastapi: 0.104.1+ - TestClient for API testing
- sqlalchemy: 2.0+ - Database operations in tests

Usage:
    pytest tests/e2e/test_skills_matrix_e2e.py -v

Notes:
    - Complete workflow testing with database integration
    - Comprehensive test coverage with fixtures
    - Proper database isolation and cleanup
    - Authentication and authorization testing
"""

import pytest
from fastapi.testclient import TestClient


class TestSkillsMatrixEndpoint:
    """Test suite for the skills_matrix endpoint with flexible markdown support."""

    def test_skills_matrix_create_with_markdown(self, client: TestClient, auth_headers):
        """Test creating a skills matrix with flexible markdown content"""
        skills_matrix_data = {
            "content": """### Skills Matrix

| Skill | Level | Notes |
|---|---:|---|
| React | Advanced | Built 10+ production apps |
| Docker | Intermediate | Deploy pipelines, orchestration |
| Python | Expert | 8+ years experience |

#### Endorsements
- **React**: Endorsed by team lead for architecture decisions
- **Python**: Mentored 5 junior developers
- **Docker**: Led containerization initiative at current company

#### Current Learning Focus
- Kubernetes advanced patterns
- GraphQL federation
- Rust for systems programming""",
            "meta": {
                "title": "Technical Skills Matrix 2025",
                "tags": ["skills", "matrix", "endorsements"],
                "visibility": "public",
            },
        }

        response = client.post(
            "/api/v1/skills_matrix", json=skills_matrix_data, headers=auth_headers
        )
        assert response.status_code == 200

        created_matrix = response.json()
        assert created_matrix["id"]
        assert created_matrix["data"]["content"] == skills_matrix_data["content"]
        assert created_matrix["data"]["meta"]["title"] == "Technical Skills Matrix 2025"
        assert created_matrix["data"]["meta"]["tags"] == [
            "skills",
            "matrix",
            "endorsements",
        ]

    def test_skills_matrix_create_with_html_entities(
        self, client: TestClient, auth_headers
    ):
        """Test that HTML entities in markdown content are properly handled"""
        skills_matrix_data = {
            "content": """### Skills &amp; Expertise Matrix

| Technology | Proficiency | Experience |
|---|---|---|
| JavaScript &lt; ES6 | Expert | Legacy codebases |
| TypeScript &gt;= 4.0 | Advanced | Modern projects |

**Note:** Comfortable with both &quot;modern&quot; and legacy JavaScript.""",
            "meta": {
                "title": "JS & TS Skills",
                "tags": ["javascript", "typescript"],
                "visibility": "public",
            },
        }

        response = client.post(
            "/api/v1/skills_matrix", json=skills_matrix_data, headers=auth_headers
        )
        assert response.status_code == 200

        created_matrix = response.json()
        assert "JavaScript < ES6" in created_matrix["data"]["content"]
        assert "TypeScript >= 4.0" in created_matrix["data"]["content"]
        assert '"modern"' in created_matrix["data"]["content"]

    def test_skills_matrix_list_empty(self, client: TestClient, auth_headers):
        """Test listing skills matrices when none exist"""
        response = client.get("/api/v1/skills_matrix", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 0

    def test_skills_matrix_list_with_items(self, client: TestClient, auth_headers):
        """Test listing skills matrices after creating some"""
        # Create multiple skills matrices
        matrices = [
            {
                "content": """### Frontend Skills

| Framework | Level |
|---|---|
| React | Expert |
| Vue | Intermediate |""",
                "meta": {"title": "Frontend Matrix", "tags": ["frontend"]},
            },
            {
                "content": """### Backend Skills

| Technology | Experience |
|---|---|
| Node.js | 5 years |
| Python | 8 years |""",
                "meta": {"title": "Backend Matrix", "tags": ["backend"]},
            },
        ]

        created_ids = []
        for matrix_data in matrices:
            response = client.post(
                "/api/v1/skills_matrix", json=matrix_data, headers=auth_headers
            )
            assert response.status_code == 200
            created_ids.append(response.json()["id"])

        # List all skills matrices
        response = client.get("/api/v1/skills_matrix", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        matrices_list = data["items"]
        assert len(matrices_list) >= 2
        assert any(
            "Frontend Skills" in item.get("content", "") for item in matrices_list
        )
        assert any(
            "Backend Skills" in item.get("content", "") for item in matrices_list
        )

        # Cleanup
        for matrix_id in created_ids:
            client.delete(f"/api/v1/skills_matrix/{matrix_id}", headers=auth_headers)

    def test_skills_matrix_get_single(self, client: TestClient, auth_headers):
        """Test retrieving a single skills matrix"""
        skills_matrix_data = {
            "content": """### Leadership Skills Matrix

| Skill | Self-Assessment | Team Feedback |
|---|---|---|
| Communication | Strong | Excellent |
| Decision Making | Good | Very Good |
| Strategic Thinking | Developing | Good |

#### Development Plan
- Focus on strategic thinking through case studies
- Seek mentorship on complex decision scenarios""",
            "meta": {
                "title": "Leadership Skills",
                "tags": ["leadership", "management", "development"],
                "visibility": "public",
            },
        }

        # Create skills matrix
        response = client.post(
            "/api/v1/skills_matrix", json=skills_matrix_data, headers=auth_headers
        )
        assert response.status_code == 200
        matrix_id = response.json()["id"]

        # Retrieve skills matrix
        response = client.get(
            f"/api/v1/skills_matrix/{matrix_id}", headers=auth_headers
        )
        assert response.status_code == 200

        matrix = response.json()
        assert matrix["id"] == matrix_id
        assert matrix["content"] == skills_matrix_data["content"]
        assert matrix["meta"]["title"] == "Leadership Skills"
        assert matrix["meta"]["tags"] == ["leadership", "management", "development"]

        # Cleanup
        client.delete(f"/api/v1/skills_matrix/{matrix_id}", headers=auth_headers)

    def test_skills_matrix_update(self, client: TestClient, auth_headers):
        """Test updating a skills matrix"""
        # Create initial skills matrix
        initial_data = {
            "content": """### DevOps Skills

| Tool | Proficiency |
|---|---|
| Docker | Intermediate |
| Kubernetes | Beginner |""",
            "meta": {"title": "DevOps Skills", "tags": ["devops"]},
        }

        response = client.post(
            "/api/v1/skills_matrix", json=initial_data, headers=auth_headers
        )
        assert response.status_code == 200
        matrix_id = response.json()["id"]

        # Update skills matrix
        updated_data = {
            "content": """### DevOps Skills

| Tool | Proficiency | Recent Projects |
|---|---|---|
| Docker | Advanced | Multi-stage builds, optimization |
| Kubernetes | Intermediate | Deployed 3 production apps |
| Terraform | Beginner | Infrastructure as code learning |

#### Recent Achievements
- Reduced deployment time by 60% with optimized Docker builds
- Successfully migrated 3 applications to Kubernetes""",
            "meta": {
                "title": "DevOps Skills - Updated",
                "tags": ["devops", "kubernetes", "docker"],
            },
        }

        response = client.put(
            f"/api/v1/skills_matrix/{matrix_id}",
            json=updated_data,
            headers=auth_headers,
        )
        assert response.status_code == 200

        updated_matrix = response.json()
        assert updated_matrix["data"]["content"] == updated_data["content"]
        assert updated_matrix["data"]["meta"]["title"] == "DevOps Skills - Updated"
        assert "Terraform" in updated_matrix["data"]["content"]

        # Cleanup
        client.delete(f"/api/v1/skills_matrix/{matrix_id}", headers=auth_headers)

    def test_skills_matrix_delete(self, client: TestClient, auth_headers):
        """Test deleting a skills matrix"""
        skills_matrix_data = {
            "content": """### Temporary Skills Matrix

| Skill | Level |
|---|---|
| Test Skill | Temporary |""",
            "meta": {"title": "Temporary Matrix"},
        }

        # Create skills matrix
        response = client.post(
            "/api/v1/skills_matrix", json=skills_matrix_data, headers=auth_headers
        )
        assert response.status_code == 200
        matrix_id = response.json()["id"]

        # Delete skills matrix
        response = client.delete(
            f"/api/v1/skills_matrix/{matrix_id}", headers=auth_headers
        )
        assert response.status_code == 200

        # Verify deletion
        response = client.get(
            f"/api/v1/skills_matrix/{matrix_id}", headers=auth_headers
        )
        assert response.status_code == 404

    def test_skills_matrix_create_validation_error_empty_content(
        self, client: TestClient, auth_headers
    ):
        """Test validation error when content is empty"""
        skills_matrix_data = {
            "content": "",
            "meta": {"title": "Empty Matrix"},
        }

        response = client.post(
            "/api/v1/skills_matrix", json=skills_matrix_data, headers=auth_headers
        )
        assert response.status_code == 400

    def test_skills_matrix_create_validation_error_missing_content(
        self, client: TestClient, auth_headers
    ):
        """Test validation error when content is missing"""
        skills_matrix_data = {
            "meta": {"title": "No Content Matrix"},
        }

        response = client.post(
            "/api/v1/skills_matrix", json=skills_matrix_data, headers=auth_headers
        )
        assert response.status_code == 400

    def test_skills_matrix_privacy_controls(self, client: TestClient, auth_headers):
        """Test privacy controls for skills matrices"""
        # Create private skills matrix
        private_matrix = {
            "content": """### Internal Skills Assessment

| Skill | Internal Rating | Notes |
|---|---|---|
| Proprietary Framework X | Expert | Company confidential |""",
            "meta": {
                "title": "Internal Assessment",
                "visibility": "private",
                "tags": ["internal"],
            },
        }

        response = client.post(
            "/api/v1/skills_matrix", json=private_matrix, headers=auth_headers
        )
        assert response.status_code == 200
        private_matrix_id = response.json()["id"]

        # Create public skills matrix
        public_matrix = {
            "content": """### Public Skills Matrix

| Skill | Level | Open Source Contributions |
|---|---|---|
| React | Advanced | 5+ projects |
| Python | Expert | Multiple libraries |""",
            "meta": {
                "title": "Public Skills",
                "visibility": "public",
                "tags": ["public", "opensource"],
            },
        }

        response = client.post(
            "/api/v1/skills_matrix", json=public_matrix, headers=auth_headers
        )
        assert response.status_code == 200
        public_matrix_id = response.json()["id"]

        # Both should be visible to authenticated user
        response = client.get("/api/v1/skills_matrix", headers=auth_headers)
        assert response.status_code == 200
        matrices_response = response.json()
        matrices_list = matrices_response["items"]

        # Check if both matrices exist in the list
        private_found = any(
            "Internal Skills Assessment" in item.get("content", "")
            for item in matrices_list
        )
        public_found = any(
            "Public Skills Matrix" in item.get("content", "") for item in matrices_list
        )
        assert private_found
        assert public_found

        # Cleanup
        client.delete(
            f"/api/v1/skills_matrix/{private_matrix_id}", headers=auth_headers
        )
        client.delete(f"/api/v1/skills_matrix/{public_matrix_id}", headers=auth_headers)

    def test_skills_matrix_complex_markdown_formatting(
        self, client: TestClient, auth_headers
    ):
        """Test complex markdown formatting in skills matrix"""
        skills_matrix_data = {
            "content": """### Comprehensive Skills Matrix

## Technical Skills

### Programming Languages
| Language | Proficiency | Years | Key Projects |
|---|---|---|---|
| **Python** | ⭐⭐⭐⭐⭐ | 8 | ML pipelines, APIs |
| **JavaScript** | ⭐⭐⭐⭐ | 6 | Frontend, Node.js |
| **Go** | ⭐⭐⭐ | 2 | Microservices |

### Frameworks & Tools
> **Note**: Ratings based on production experience and peer feedback

#### Frontend
- **React** `Advanced` - Component architecture, hooks, performance optimization
- **Vue.js** `Intermediate` - SPA development, Vuex state management

#### Backend
- **FastAPI** `Expert` - Built 10+ production APIs
- **Django** `Advanced` - E-commerce platforms, content management

#### DevOps
```bash
# Sample deployment script mastery
docker build -t app:latest .
kubectl apply -f deployment.yaml
```

## Soft Skills Assessment

| Skill | Self-Rating | 360° Feedback | Development Goal |
|---|---|---|---|
| Leadership | 8/10 | 8.5/10 | Executive presence |
| Communication | 9/10 | 9/10 | Technical writing |
| Problem Solving | 9/10 | 8.5/10 | Systems thinking |

---

*Last updated: Q3 2025*
*Next review: Q1 2026*""",
            "meta": {
                "title": "Complete Skills Assessment 2025",
                "tags": ["comprehensive", "technical", "leadership"],
                "visibility": "public",
            },
        }

        response = client.post(
            "/api/v1/skills_matrix", json=skills_matrix_data, headers=auth_headers
        )
        assert response.status_code == 200

        created_matrix = response.json()
        content = created_matrix["data"]["content"]

        # Verify complex formatting is preserved
        assert "⭐⭐⭐⭐⭐" in content  # Star ratings
        assert "`Advanced`" in content  # Inline code
        assert "```bash" in content  # Code blocks
        assert "**React**" in content  # Bold formatting
        assert "> **Note**:" in content  # Blockquotes
        assert "---" in content  # Horizontal rules
        assert "*Last updated:" in content  # Italic formatting

        # Cleanup
        matrix_id = created_matrix["id"]
        client.delete(f"/api/v1/skills_matrix/{matrix_id}", headers=auth_headers)
