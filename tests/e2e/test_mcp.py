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
