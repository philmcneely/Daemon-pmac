import json

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_mcp_list_tools():
    """Ensure the MCP tools list endpoint returns a valid response with at least the info tool."""
    payload = {"jsonrpc": "2.0", "method": "list", "params": {}}
    response = client.post("/mcp/tools/list", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "tools" in data["result"]
    tool_names = [tool["name"] for tool in data["result"]["tools"]]
    # The info tool should always be present
    assert any("info" in name for name in tool_names)


def test_mcp_call_info():
    """Call the MCP info tool and verify a well‑formed JSON‑RPC response."""
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {"name": "mcp_info", "arguments": {}},
    }
    response = client.post("/mcp/tools/call", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "content" in data["result"]
    # The content should be a list with a single text entry containing JSON
    content = data["result"]["content"]
    assert isinstance(content, list) and len(content) == 1
    assert content[0]["type"] == "text"
    # Verify that the text field contains valid JSON
    try:
        json.loads(content[0]["text"])
    except json.JSONDecodeError:
        assert False, "MCP info tool returned invalid JSON"
