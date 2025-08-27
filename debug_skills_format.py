"""Debug script to understand skills API response format"""

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Get auth token
auth_response = client.post(
    "/auth/login", data={"username": "admin", "password": "testpassword"}
)

if auth_response.status_code == 200:
    token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print("=== Test empty list ===")
    list_response = client.get("/api/v1/skills", headers=headers)
    print(f"Status: {list_response.status_code}")
    print(f"Response: {json.dumps(list_response.json(), indent=2)}")

    print("\n=== Test create skill ===")
    skill_data = {
        "content": "### Python (Intermediate)\n\nTest skill content",
        "meta": {
            "title": "Python",
            "category": "Programming Languages",
            "level": "Intermediate",
        },
    }
    create_response = client.post("/api/v1/skills", json=skill_data, headers=headers)
    print(f"Create Status: {create_response.status_code}")
    print(f"Create Response: {json.dumps(create_response.json(), indent=2)}")

    if create_response.status_code == 200:
        skill_id = create_response.json()["id"]

        print("\n=== Test get single skill ===")
        get_response = client.get(f"/api/v1/skills/{skill_id}", headers=headers)
        print(f"Get Status: {get_response.status_code}")
        print(f"Get Response: {json.dumps(get_response.json(), indent=2)}")

        print("\n=== Test list with items ===")
        list_response = client.get("/api/v1/skills", headers=headers)
        print(f"List Status: {list_response.status_code}")
        print(f"List Response: {json.dumps(list_response.json(), indent=2)}")

        # Cleanup
        client.delete(f"/api/v1/skills/{skill_id}", headers=headers)
    else:
        print(f"Create Error: {json.dumps(create_response.json(), indent=2)}")
else:
    print(f"Auth failed: {auth_response.status_code} - {auth_response.text}")
