"""
Debug script to understand the skills API response format
"""

import json

import requests

# Authenticate
auth_response = requests.post(
    "http://localhost:8000/auth/login",
    json={"username": "testuser", "password": "testpass"},
)

if auth_response.status_code == 200:
    token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Test skills list endpoint
    print("=== Testing empty skills list ===")
    response = requests.get("http://localhost:8000/api/v1/skills", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    # Create a skill to test
    print("\n=== Creating a skill ===")
    skill_data = {
        "content": "### Python (Intermediate)\n\nTest skill content",
        "meta": {
            "title": "Python",
            "category": "Programming Languages",
            "level": "Intermediate",
        },
    }

    create_response = requests.post(
        "http://localhost:8000/api/v1/skills", json=skill_data, headers=headers
    )
    print(f"Create Status: {create_response.status_code}")
    if create_response.status_code == 200:
        created_skill = create_response.json()
        print(f"Created Response: {json.dumps(created_skill, indent=2)}")
        skill_id = created_skill.get("id")

        # Test single skill get
        print("\n=== Getting single skill ===")
        single_response = requests.get(
            f"http://localhost:8000/api/v1/skills/{skill_id}", headers=headers
        )
        print(f"Single Status: {single_response.status_code}")
        print(f"Single Response: {json.dumps(single_response.json(), indent=2)}")

        # Test skills list with items
        print("\n=== Testing skills list with items ===")
        list_response = requests.get(
            "http://localhost:8000/api/v1/skills", headers=headers
        )
        print(f"List Status: {list_response.status_code}")
        print(f"List Response: {json.dumps(list_response.json(), indent=2)}")

        # Cleanup
        delete_response = requests.delete(
            f"http://localhost:8000/api/v1/skills/{skill_id}", headers=headers
        )
        print(f"\nDelete Status: {delete_response.status_code}")
    else:
        print(f"Create Error: {json.dumps(create_response.json(), indent=2)}")

else:
    print(f"Auth failed: {auth_response.status_code}")
    print(f"Auth error: {auth_response.json()}")
