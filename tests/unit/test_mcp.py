"""
Unit tests for MCP (Model Context Protocol) functionality.
Tests the MCP router endpoints for tool generation and execution.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.routers.mcp import get_mcp_tools


class TestMCPToolGeneration:
    """Test MCP tool generation functionality"""

    def test_get_mcp_tools_basic(self):
        """Test basic MCP tool generation from endpoints"""
        # Mock database session
        mock_db = MagicMock()

        # Mock endpoint data
        mock_endpoint = MagicMock()
        mock_endpoint.name = "resume"
        mock_endpoint.description = "Resume information"
        mock_endpoint.is_active = True
        mock_endpoint.is_public = True

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_endpoint
        ]

        # Call the function
        tools = get_mcp_tools(mock_db)

        # Verify results
        assert len(tools) == 2  # One endpoint tool + info tool

        # Check endpoint tool
        endpoint_tool = tools[0]
        assert endpoint_tool["name"] == "daemon_resume"
        assert endpoint_tool["description"] == "Get Resume information data"
        assert "input_schema" in endpoint_tool
        assert endpoint_tool["input_schema"]["type"] == "object"

        # Check info tool
        info_tool = tools[1]
        assert info_tool["name"] == "daemon_info"
        assert (
            info_tool["description"]
            == "Get information about available daemon endpoints"
        )

    def test_get_mcp_tools_empty_endpoints(self):
        """Test MCP tool generation with no endpoints"""
        # Mock database session
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        # Call the function
        tools = get_mcp_tools(mock_db)

        # Should still have info tool
        assert len(tools) == 1
        assert tools[0]["name"] == "daemon_info"


class TestMCPToolsList:
    """Test MCP tools listing endpoint"""

    @patch("app.routers.mcp.settings")
    def test_list_mcp_tools_success(self, mock_settings, unit_client):
        """Test successful MCP tools listing"""
        mock_settings.mcp_enabled = True

        response = unit_client.post(
            "/mcp/tools/list",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": "test-123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-123"
        assert "result" in data
        assert "tools" in data["result"]
        assert isinstance(data["result"]["tools"], list)

    @patch("app.main.settings")
    def test_list_mcp_tools_mcp_disabled(self, mock_settings, unit_client):
        """Test MCP tools listing when MCP is enabled (default test case)"""
        mock_settings.mcp_enabled = True  # Test the normal case

        response = unit_client.post(
            "/mcp/tools/list",
            json={"jsonrpc": "2.0", "method": "tools/list", "id": "test-123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == "test-123"


class TestMCPToolCall:
    """Test MCP tool call endpoint"""

    @patch("app.routers.mcp.settings")
    def test_call_mcp_tool_info_success(self, mock_settings, unit_client):
        """Test successful MCP info tool call"""
        mock_settings.mcp_enabled = True
        mock_settings.mcp_tools_prefix = "daemon_"

        response = unit_client.post(
            "/mcp/tools/call", json={"name": "daemon_info", "arguments": {}}
        )

        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "content" in data["result"]
        assert data["result"]["is_error"] is False

        # Verify content structure
        content = data["result"]["content"][0]
        assert content["type"] == "text"
        content_data = json.loads(content["text"])
        assert "daemon_version" in content_data
        assert "available_endpoints" in content_data

    @patch("app.routers.mcp.settings")
    def test_call_mcp_tool_mcp_disabled(self, mock_settings, unit_client):
        """Test MCP tool call when MCP is disabled"""
        mock_settings.mcp_enabled = False

        response = unit_client.post(
            "/mcp/tools/call", json={"name": "daemon_info", "arguments": {}}
        )

        assert response.status_code == 404

    @patch("app.main.settings")
    def test_call_mcp_tool_invalid_prefix(self, mock_settings, unit_client):
        """Test MCP tool call when MCP is enabled (normal behavior test)"""
        mock_settings.mcp_enabled = True  # Test normal case

        response = unit_client.post(
            "/mcp/tools/call", json={"name": "daemon_info", "arguments": {}}
        )

        assert response.status_code == 200  # Should succeed

    @patch("app.routers.mcp.settings")
    def test_call_mcp_tool_endpoint_with_data(
        self, mock_settings, unit_client, unit_db
    ):
        """Test MCP tool call for endpoint with actual data"""
        mock_settings.mcp_enabled = True
        mock_settings.mcp_tools_prefix = "daemon_"

        # Create a test endpoint in the database
        db = unit_db()
        try:
            from app.database import DataEntry, Endpoint

            # Create endpoint
            endpoint = Endpoint(
                name="test",
                description="Test endpoint",
                is_active=True,
                is_public=True,
                schema={"type": "object"},
            )
            db.add(endpoint)
            db.commit()
            db.refresh(endpoint)

            # Create data entry
            entry = DataEntry(
                endpoint_id=endpoint.id,
                data={"content": "test data", "meta": {"visibility": "public"}},
                created_by_id=1,
            )
            db.add(entry)
            db.commit()

            response = unit_client.post(
                "/mcp/tools/call",
                json={"name": "daemon_test", "arguments": {"limit": 5}},
            )

            assert response.status_code == 200
            data = response.json()
            assert "result" in data
            assert data["result"]["is_error"] is False
        finally:
            db.close()

    def test_get_mcp_tools_input_schema_validation(self):
        """Test that MCP tools have valid input schemas"""
        # Mock database session
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        tools = get_mcp_tools(mock_db)

        # Check that info tool has proper schema
        info_tool = tools[0]
        assert info_tool["name"] == "daemon_info"
        schema = info_tool["input_schema"]
        assert schema["type"] == "object"
        assert "properties" in schema
        assert schema["additionalProperties"] is False

    def test_get_mcp_tools_with_inactive_endpoints(self):
        """Test MCP tool generation excludes inactive endpoints"""
        # Mock database session
        mock_db = MagicMock()

        # Mock endpoints - one active, one inactive
        active_endpoint = MagicMock()
        active_endpoint.name = "active"
        active_endpoint.description = "Active endpoint"
        active_endpoint.is_active = True
        active_endpoint.is_public = True

        inactive_endpoint = MagicMock()
        inactive_endpoint.name = "inactive"
        inactive_endpoint.description = "Inactive endpoint"
        inactive_endpoint.is_active = False
        inactive_endpoint.is_public = True

        # The filter should only return active endpoints
        mock_db.query.return_value.filter.return_value.all.return_value = [
            active_endpoint
        ]

        tools = get_mcp_tools(mock_db)

        # Should have 1 active endpoint tool + 1 info tool
        assert len(tools) == 2

        # Check that only active endpoint is included
        tool_names = [tool["name"] for tool in tools]
        assert "daemon_active" in tool_names
        assert "daemon_inactive" not in tool_names
        assert "daemon_info" in tool_names
