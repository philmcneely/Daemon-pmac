#!/usr/bin/env python3
"""
Test URL Pattern Consistency
Verify that both URL patterns work identically for visibility and special behavior
"""

import json
import sys

import requests

# API Configuration
BASE_URL = "http://localhost:8005"
USERNAME = "admin"
PASSWORD = "admin123"


def login():
    """Login and get JWT token"""
    login_data = {"username": USERNAME, "password": PASSWORD}

    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful")
        return token
    else:
        print(f"❌ Login failed: {response.status_code} {response.text}")
        return None


def create_test_content(token):
    """Create test content with different visibility levels"""
    headers = {"Authorization": f"Bearer {token}"}

    # Create public about content
    public_content = {
        "content": "This is public about content",
        "meta": {"title": "Public About", "visibility": "public"},
    }

    # Create private about content
    private_content = {
        "content": "This is private about content - should be hidden",
        "meta": {"title": "Private About", "visibility": "private"},
    }

    # Create unlisted about content
    unlisted_content = {
        "content": "This is unlisted about content - should be hidden",
        "meta": {"title": "Unlisted About", "visibility": "unlisted"},
    }

    results = {}

    content_types = [
        ("public", public_content),
        ("private", private_content),
        ("unlisted", unlisted_content),
    ]

    for name, content in content_types:
        response = requests.post(
            f"{BASE_URL}/api/v1/about", json=content, headers=headers
        )
        if response.status_code == 200:
            item_id = response.json()["id"]
            results[name] = item_id
            print(f"✅ Created {name} about content with ID {item_id}")
        else:
            print(
                f"❌ Failed to create {name} about content: "
                f"{response.status_code} {response.text}"
            )

    return results


def test_pattern_consistency(endpoint, username):
    """Test both URL patterns for the same endpoint and user"""
    print(f"\n🔍 Testing pattern consistency for {endpoint}/{username}:")

    # Pattern 1: /api/v1/{endpoint}/users/{username}
    pattern1_url = f"{BASE_URL}/api/v1/{endpoint}/users/{username}"

    # Pattern 2: /api/v1/users/{username}/{endpoint} (should redirect)
    pattern2_url = f"{BASE_URL}/api/v1/users/{username}/{endpoint}"

    print(f"   Pattern 1: {pattern1_url}")
    print(f"   Pattern 2: {pattern2_url}")

    # Test pattern 1
    response1 = requests.get(pattern1_url)
    print(f"   Pattern 1 Status: {response1.status_code}")

    # Test pattern 2
    response2 = requests.get(pattern2_url, allow_redirects=False)
    print(f"   Pattern 2 Status: {response2.status_code}")

    if response2.status_code == 301:
        redirect_location = response2.headers.get("Location", "")
        print(f"   Pattern 2 Redirect: {redirect_location}")

        # Follow redirect
        response2_follow = requests.get(pattern2_url)
        print(f"   Pattern 2 After Redirect: {response2_follow.status_code}")

        # Compare data
        if response1.status_code == 200 and response2_follow.status_code == 200:
            try:
                data1 = response1.json()
                data2 = response2_follow.json()

                if data1 == data2:
                    print("   ✅ Both patterns return identical data")
                else:
                    print("   ❌ Patterns return different data")
                    print(
                        f"      Pattern 1 items: "
                        f"{len(data1) if isinstance(data1, list) else 'not a list'}"
                    )
                    print(
                        f"      Pattern 2 items: "
                        f"{len(data2) if isinstance(data2, list) else 'not a list'}"
                    )
            except json.JSONDecodeError:
                print("   ❓ Could not parse JSON response")

    return response1, response2


def test_visibility_filtering():
    """Test visibility filtering on both URL patterns"""
    print("\n🔒 Testing visibility filtering consistency:")

    users = ["admin", "blackbeard"]
    endpoints = ["about", "resume"]

    for user in users:
        for endpoint in endpoints:
            print(f"\n--- Testing {endpoint} for user {user} ---")

            # Test both patterns
            pattern1_url = f"{BASE_URL}/api/v1/{endpoint}/users/{user}"
            pattern2_url = f"{BASE_URL}/api/v1/users/{user}/{endpoint}"

            # Test unauthenticated access
            response1 = requests.get(pattern1_url)
            response2 = requests.get(pattern2_url)  # This should redirect and follow

            print(f"Pattern 1 ({endpoint}/users/{user}): {response1.status_code}")
            print(f"Pattern 2 (users/{user}/{endpoint}): {response2.status_code}")

            # Check if both have data and same visibility rules
            if response1.status_code == 200 and response2.status_code == 200:
                try:
                    data1 = response1.json()
                    data2 = response2.json()

                    # Count visible items
                    count1 = (
                        len(data1) if isinstance(data1, list) else (1 if data1 else 0)
                    )
                    count2 = (
                        len(data2) if isinstance(data2, list) else (1 if data2 else 0)
                    )

                    print(f"   Pattern 1 visible items: {count1}")
                    print(f"   Pattern 2 visible items: {count2}")

                    if count1 == count2:
                        print("   ✅ Same visibility filtering")
                    else:
                        print("   ❌ Different visibility filtering")

                except json.JSONDecodeError:
                    print("   ❓ Could not parse JSON")


def test_special_resume_behavior():
    """Test the special resume endpoint behavior on both patterns"""
    print("\n📄 Testing special resume behavior:")

    users = ["admin", "blackbeard"]

    for user in users:
        print(f"\n--- Testing resume for user {user} ---")

        # Test both patterns
        pattern1_url = f"{BASE_URL}/api/v1/resume/users/{user}"
        pattern2_url = f"{BASE_URL}/api/v1/users/{user}/resume"

        response1 = requests.get(pattern1_url)
        response2 = requests.get(pattern2_url)

        print(f"Pattern 1: {response1.status_code}")
        print(f"Pattern 2: {response2.status_code}")

        # Check if resume data is structured correctly
        if response1.status_code == 200:
            try:
                data1 = response1.json()
                if isinstance(data1, list) and len(data1) > 0:
                    resume = data1[0]
                    has_name = "name" in resume
                    has_experience = "experience" in resume
                    has_education = "education" in resume

                    print(f"   Pattern 1 resume structure:")
                    print(f"     Has name: {has_name}")
                    print(f"     Has experience: {has_experience}")
                    print(f"     Has education: {has_education}")
                    print(f"     User name: {resume.get('name', 'No name')}")

            except (json.JSONDecodeError, KeyError, IndexError):
                print("   ❓ Could not parse resume structure")

        if response2.status_code == 200:
            try:
                data2 = response2.json()
                if isinstance(data2, list) and len(data2) > 0:
                    resume = data2[0]
                    print(f"   Pattern 2 user name: {resume.get('name', 'No name')}")

            except (json.JSONDecodeError, KeyError, IndexError):
                print("   ❓ Could not parse resume structure")


def cleanup_test_content(token, item_ids):
    """Clean up test content"""
    if not item_ids:
        return

    print("\n🧹 Cleaning up test content:")
    headers = {"Authorization": f"Bearer {token}"}

    for visibility, item_id in item_ids.items():
        response = requests.delete(
            f"{BASE_URL}/api/v1/about/{item_id}", headers=headers
        )
        if response.status_code == 200:
            print(f"   Deleted {visibility} content {item_id} ✅")
        else:
            print(f"   Failed to delete {visibility} content {item_id} ❌")


def main():
    """Main test function"""
    print("🔍 Testing URL Pattern Consistency")

    # Login
    token = login()
    if not token:
        return

    # Create test content for visibility testing
    item_ids = create_test_content(token)

    try:
        # Test pattern consistency
        test_pattern_consistency("about", "admin")
        test_pattern_consistency("resume", "blackbeard")

        # Test visibility filtering
        test_visibility_filtering()

        # Test special resume behavior
        test_special_resume_behavior()

        print(f"\n🎯 URL pattern consistency test completed!")

    finally:
        # Clean up
        cleanup_test_content(token, item_ids)


if __name__ == "__main__":
    main()
