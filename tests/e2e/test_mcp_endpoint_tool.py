import json

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_mcp_call_specific_endpoint():
    """Call an MCP tool for a specific endpoint (e.g., `about`) and verify the response."""
    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "name": "mcp_about",
            "arguments": {"limit": 5, "active_only": True},
        },
    }
    response = client.post("/mcp/tools/call", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    # The result should contain a JSON‑encoded text payload
    content = data["result"]["content"]
    assert isinstance(content, list) and len(content) == 1
    assert content[0]["type"] == "text"
    # The text field should be valid JSON with expected keys
    try:
        parsed = json.loads(content[0]["text"])
    except json.JSONDecodeError:
        assert False, "MCP tool response is not valid JSON"
    # Basic sanity checks on the parsed payload
    assert "endpoint" in parsed
    assert parsed["endpoint"] == "about"
    assert "data" in parsed
    assert isinstance(parsed["data"], list)
