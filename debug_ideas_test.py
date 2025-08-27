"""
Debug test to see actual response format
"""

import json

import pytest
from fastapi.testclient import TestClient


def test_debug_ideas_response(client: TestClient, auth_headers):
    """Debug test to see what the ideas endpoint actually returns"""
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
