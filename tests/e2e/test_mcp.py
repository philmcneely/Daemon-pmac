"""
Module: tests.e2e.test_mcp
Description: End-to-end tests for Model Context Protocol integration and tool execution

Author: pmac
Created: 2025-08-28
Modified: 2025-08-28

Dependencies:
- pytest: 7.4.3+ - Testing framework
- fastapi: 0.104.1+ - TestClient for API testing
- sqlalchemy: 2.0+ - Database operations in tests

Usage:
    pytest tests/e2e/test_mcp.py -v

Notes:
    - Complete workflow testing with database integration
    - Comprehensive test coverage with fixtures
    - Proper database isolation and cleanup
    - Authentication and authorization testing
"""

import json

import pytest


def test_mcp_tools_list(client):
    """Test MCP tools listing"""
    response = client.post(
        "/mcp/tools/list", json={"jsonrpc": "2.0", "method": "tools/list", "id": "1"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "tools" in data["result"]
    assert isinstance(data["result"]["tools"], list)

    # Check that we have expected tools
    tool_names = [tool["name"] for tool in data["result"]["tools"]]
    expected_tools = [
        "daemon_resume",
        "daemon_about",
        "daemon_ideas",
        "daemon_skills",
        "daemon_info",
    ]
    for tool in expected_tools:
        assert tool in tool_names


def test_mcp_tools_get(client):
    """Test getting MCP tools via GET endpoint"""
    response = client.get("/mcp/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert isinstance(data["tools"], list)


def test_mcp_tool_call_info(client):
    """Test MCP tool call for info"""
    response = client.post(
        "/mcp/tools/call", json={"name": "daemon_info", "arguments": {}}
    )
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "content" in data["result"]
    assert not data["result"]["is_error"]

    # Check that content contains daemon info
    content_text = data["result"]["content"][0]["text"]
    content_json = json.loads(content_text)
    assert "daemon_version" in content_json
    assert "available_endpoints" in content_json
    assert "total_endpoints" in content_json


def test_mcp_tool_call_endpoint(client, auth_headers, sample_idea_data):
    """Test MCP tool call for specific endpoint"""
    # Add some test data first
    client.post("/api/v1/ideas", headers=auth_headers, json=sample_idea_data)

    response = client.post(
        "/mcp/tools/call",
        json={"name": "daemon_ideas", "arguments": {"limit": 5, "active_only": True}},
    )
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "content" in data["result"]
    assert not data["result"]["is_error"]

    # Verify the content structure
    content_text = data["result"]["content"][0]["text"]
    content_json = json.loads(content_text)
    assert "endpoint" in content_json
    assert "data" in content_json
    assert content_json["endpoint"] == "ideas"


def test_mcp_tool_call_invalid_tool(client):
    """Test MCP tool call with invalid tool name"""
    response = client.post(
        "/mcp/tools/call", json={"name": "daemon_nonexistent", "arguments": {}}
    )
    assert response.status_code == 200  # MCP returns 200 with JSON-RPC error
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32603  # Internal error code


def test_mcp_tool_call_invalid_arguments(client):
    """Test MCP tool call with invalid arguments"""
    response = client.post(
        "/mcp/tools/call",
        json={"name": "daemon_ideas", "arguments": {"limit": -1}},
        # Invalid limit
    )
    assert response.status_code == 200  # MCP returns 200 with JSON-RPC error
    data = response.json()
    assert "error" in data
    assert "Limit must be a positive integer" in data["error"]["message"]


def test_mcp_tool_specific_endpoint(client, auth_headers, sample_book_data):
    """Test MCP tool via specific endpoint call"""
    # Add some test data first
    client.post("/api/v1/favorite_books", headers=auth_headers, json=sample_book_data)

    response = client.post(
        "/mcp/tools/daemon_favorite_books", json={"limit": 3, "active_only": True}
    )
    assert response.status_code == 200
    data = response.json()
    assert "content" in data  # REST endpoint returns result directly
    assert "is_error" in data
    assert data["is_error"] == False


def test_mcp_jsonrpc_compliance(client):
    """Test MCP JSON-RPC compliance"""
    response = client.post(
        "/mcp/tools/list",
        json={"jsonrpc": "2.0", "method": "tools/list", "id": "test-123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["id"] == "test-123"
    assert "result" in data


def test_mcp_resume_tool(client, auth_headers, sample_resume_data):
    """Test MCP resume tool specifically"""
    # Add resume data first
    client.post("/api/v1/resume", headers=auth_headers, json=sample_resume_data)

    response = client.post(
        "/mcp/tools/call", json={"name": "daemon_resume", "arguments": {"limit": 1}}
    )
    assert response.status_code == 200
    data = response.json()
    assert not data["result"]["is_error"]

    content_text = data["result"]["content"][0]["text"]
    content_json = json.loads(content_text)
    assert content_json["endpoint"] == "resume"
    assert len(content_json["data"]) >= 1


def test_mcp_skills_tool(client, auth_headers):
    """Test MCP skills tool"""
    # Add skills data first
    skills_data = {
        "name": "Python Programming",
        "category": "Programming Languages",
        "level": "advanced",
        "years_experience": 5,
        "description": "Python development and automation",
    }
    client.post("/api/v1/skills", headers=auth_headers, json=skills_data)

    response = client.post(
        "/mcp/tools/call", json={"name": "daemon_skills", "arguments": {}}
    )
    assert response.status_code == 200
    data = response.json()

    content_text = data["result"]["content"][0]["text"]
    content_json = json.loads(content_text)
    assert content_json["endpoint"] == "skills"
    assert any(item["name"] == "Python Programming" for item in content_json["data"])


def test_mcp_tool_with_limit_parameter(client, auth_headers):
    """Test MCP tool with different limit parameters"""
    # Create multiple ideas
    for i in range(5):
        client.post(
            "/api/v1/ideas",
            headers=auth_headers,
            json={
                "title": f"Idea {i}",
                "description": f"Description {i}",
                "category": "testing",
            },
        )

    # Test with limit
    response = client.post(
        "/mcp/tools/call", json={"name": "daemon_ideas", "arguments": {"limit": 2}}
    )
    assert response.status_code == 200

    content_text = response.json()["result"]["content"][0]["text"]
    content_json = json.loads(content_text)
    assert len(content_json["data"]) <= 2


def test_mcp_error_handling(client):
    """Test MCP error handling"""
    # Test malformed JSON-RPC request
    response = client.post("/mcp/tools/call", json={"invalid": "request"})
    assert response.status_code in [400, 422]


def test_mcp_rest_tools(client):
    """Test REST endpoint for MCP tools"""
    response = client.get("/mcp/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert isinstance(data["tools"], list)


def test_mcp_rest_call(client):
    """Test REST endpoint for MCP tool call"""
    response = client.post("/mcp/tools/daemon_info", json={})
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert isinstance(data["content"], list)


def test_mcp_privacy_filtering_private_data(client, auth_headers):
    """Test that MCP endpoints filter out private data"""
    # Add private idea data (using content/meta format)
    private_idea = {
        "content": "# Secret Project Idea\n\nThis is a private idea with sensitive info: 555-123-4567",
        "meta": {"visibility": "private", "title": "Secret Project"},
    }

    public_idea = {
        "content": "# Public Idea\n\nThis is a safe public idea about technology",
        "meta": {"visibility": "public", "title": "Public Idea"},
    }

    # Add both private and public data
    response1 = client.post("/api/v1/ideas", headers=auth_headers, json=private_idea)
    assert response1.status_code in [200, 201]  # Allow both create and update

    response2 = client.post("/api/v1/ideas", headers=auth_headers, json=public_idea)
    assert response2.status_code in [200, 201]  # Allow both create and update

    # Test MCP access - should only get public data and filtered
    response = client.post(
        "/mcp/tools/call", json={"name": "daemon_ideas", "arguments": {"limit": 10}}
    )
    assert response.status_code == 200
    data = response.json()

    content_text = data["result"]["content"][0]["text"]
    content_json = json.loads(content_text)

    # Should only have one entry (the public one)
    assert content_json["count"] == 1

    # Verify the returned data is filtered
    idea_data = content_json["data"][0]
    assert "Public Idea" in idea_data["content"]

    # Verify private data is not present anywhere
    assert "Secret Project" not in str(content_json)
    assert "555-123-4567" not in str(content_json)
    assert "private idea" not in str(content_json)


def test_mcp_privacy_filtering_unlisted_data(client, auth_headers):
    """Test that MCP endpoints filter out unlisted data"""
    # Add unlisted data
    unlisted_idea = {
        "title": "Secret Project",
        "description": "This should not be visible to AI",
        "category": "private thoughts",
        "meta": {"visibility": "unlisted"},
    }

    public_idea = {
        "title": "Public Idea",
        "description": "This is safe for AI consumption",
        "category": "general",
        "meta": {"visibility": "public"},
    }

    # Add both unlisted and public data
    client.post("/api/v1/ideas", headers=auth_headers, json=unlisted_idea)
    client.post("/api/v1/ideas", headers=auth_headers, json=public_idea)

    # Test MCP access
    response = client.post(
        "/mcp/tools/call", json={"name": "daemon_ideas", "arguments": {"limit": 10}}
    )
    assert response.status_code == 200
    data = response.json()

    content_text = data["result"]["content"][0]["text"]
    content_json = json.loads(content_text)

    # Should only have one entry (the public one)
    assert content_json["count"] == 1
    assert content_json["data"][0]["title"] == "Public Idea"

    # Verify unlisted data is not present
    assert "Secret Project" not in str(content_json)
    assert "private thoughts" not in str(content_json)


def test_mcp_privacy_filtering_sensitive_fields(client, auth_headers):
    """Test that MCP endpoints preserve user content while respecting visibility settings"""
    # Add data with sensitive information using content/meta schema
    contact_data = {
        "content": """
# Contact Information

**Name**: Test Person
**Email**: test@example.com
**Phone**: 555-0123
**Address**: 123 Main St
**LinkedIn**: linkedin.com/in/test
**Website**: https://test.com
        """.strip(),
        "meta": {"visibility": "public"},
    }

    client.post("/api/v1/contact_info", headers=auth_headers, json=contact_data)

    # Test MCP access
    response = client.post(
        "/mcp/tools/call",
        json={"name": "daemon_contact_info", "arguments": {"limit": 10}},
    )
    assert response.status_code == 200
    data = response.json()

    content_text = data["result"]["content"][0]["text"]
    content_json = json.loads(content_text)

    # Should have safe fields (verify content shows safe info)
    assert "Test Person" in content_text
    assert "test@example.com" in content_text
    assert "linkedin.com/in/test" in content_text
    assert "https://test.com" in content_text

    # Phone numbers and addresses in user content should be preserved (user intentionally included them)
    assert "555-0123" in content_text
    assert "123 Main St" in content_text


def test_mcp_privacy_filtering_no_meta_defaults_public(client, auth_headers):
    """Test that data without meta.visibility defaults to public and preserves user content"""
    # Add data without explicit visibility (should default to public) using ideas schema
    idea_without_meta = {
        "content": """
# Idea Without Meta

This is a test idea with some sensitive info that should be filtered.

Contact: test@example.com
Phone: 555-9999
        """.strip()
        # No meta provided - should default to public
    }

    client.post("/api/v1/ideas", headers=auth_headers, json=idea_without_meta)

    # Test MCP access
    response = client.post(
        "/mcp/tools/call", json={"name": "daemon_ideas", "arguments": {"limit": 10}}
    )
    assert response.status_code == 200
    data = response.json()

    content_text = data["result"]["content"][0]["text"]
    content_json = json.loads(content_text)

    # Should have the entry (defaults to public)
    assert content_json["count"] >= 1

    # Find our entry by checking content
    our_entry = None
    for entry in content_json["data"]:
        if "Idea Without Meta" in str(entry):
            our_entry = entry
            break

    assert our_entry is not None
    assert "test@example.com" in str(our_entry)

    # Phone numbers in user content should be preserved (user intentionally included them)
    assert "555-9999" in str(content_json)


def test_mcp_privacy_filtering_private_data_excluded(client, auth_headers):
    """Test that entries with private visibility are excluded from MCP results"""
    # Add data with private visibility (should be completely filtered out)
    private_data = {
        "content": """
# Private Contact Info

This is private information that should not be visible to AI assistants.
        """.strip(),
        "meta": {"visibility": "private"},  # Private - should be excluded
    }

    client.post("/api/v1/contact_info", headers=auth_headers, json=private_data)

    # Test MCP access
    response = client.post(
        "/mcp/tools/call",
        json={"name": "daemon_contact_info", "arguments": {"limit": 10}},
    )
    assert response.status_code == 200
    data = response.json()

    content_text = data["result"]["content"][0]["text"]
    content_json = json.loads(content_text)

    # Should have no entries since private data is excluded from MCP responses
    assert content_json["count"] == 0
    assert content_json["data"] == []


def test_mcp_privacy_rest_endpoint_filtering(client, auth_headers):
    """Test that REST-style MCP endpoints also apply privacy filtering"""
    # Add private data using skills schema
    private_skill = {
        "content": """
# Secret Skill

**Name**: Secret Skill
**Level**: expert
**Description**: This should not be visible to AI.
        """.strip(),
        "meta": {"visibility": "private"},
    }

    public_skill = {
        "content": """
# Public Skill

**Name**: Public Skill
**Level**: intermediate
**Description**: This is a safe public skill.
        """.strip(),
        "meta": {"visibility": "public"},
    }

    client.post("/api/v1/skills", headers=auth_headers, json=private_skill)
    client.post("/api/v1/skills", headers=auth_headers, json=public_skill)

    # Test REST-style MCP endpoint
    response = client.post("/mcp/tools/daemon_skills", json={"limit": 10})
    assert response.status_code == 200
    data = response.json()

    # Should only have public skill
    assert len(data["content"]) == 1
    content_text = data["content"][0]["text"]
    content_json = json.loads(content_text)

    assert content_json["count"] == 1
    assert "Public Skill" in str(content_json["data"])
    assert "Secret Skill" not in str(content_json)


def test_mcp_privacy_info_tool_not_affected(client):
    """Test that the info tool is not affected by privacy filtering (shows endpoint info only)"""
    response = client.post(
        "/mcp/tools/call", json={"name": "daemon_info", "arguments": {}}
    )
    assert response.status_code == 200
    data = response.json()

    content_text = data["result"]["content"][0]["text"]
    content_json = json.loads(content_text)

    # Info tool should work normally (doesn't access user data)
    assert "daemon_version" in content_json
    assert "available_endpoints" in content_json
    assert "total_endpoints" in content_json
