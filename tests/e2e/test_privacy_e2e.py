#!/usr/bin/env python3
"""
End-to-End Privacy Filtering Tests
Test privacy filtering behavior across different user modes and visibility levels
"""

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
        print("✅ Login successful")
        return token
    else:
        print(f"❌ Login failed: {response.status_code} {response.text}")
        return None


def create_test_content(token):
    """Create test content with different visibility levels"""
    headers = {"Authorization": f"Bearer {token}"}

    content_items = [
        {
            "name": "public",
            "content": {
                "content": "This is public content",
                "meta": {"title": "Public Test", "visibility": "public"},
            },
        },
        {
            "name": "private",
            "content": {
                "content": "This is private content - should be hidden",
                "meta": {"title": "Private Test", "visibility": "private"},
            },
        },
        {
            "name": "unlisted",
            "content": {
                "content": "This is unlisted content - should be hidden",
                "meta": {"title": "Unlisted Test", "visibility": "unlisted"},
            },
        },
    ]

    results = {}

    for item in content_items:
        response = requests.post(
            f"{BASE_URL}/api/v1/about", json=item["content"], headers=headers
        )
        if response.status_code == 200:
            item_id = response.json()["id"]
            results[item["name"]] = item_id
            print(f"✅ Created {item['name']} content with ID {item_id}")
        else:
            print(
                f"❌ Failed to create {item['name']} content: "
                f"{response.status_code} {response.text}"
            )

    return results


def test_privacy_filtering(item_ids):
    """Test privacy filtering without authentication"""
    print("\n🔍 Testing privacy filtering (unauthenticated access):")

    # Test endpoint list (should only show public content)
    response = requests.get(f"{BASE_URL}/api/v1/about")
    if response.status_code == 200:
        items = response.json()["items"]
        visible_titles = [
            item.get("meta", {}).get("title", "No title") for item in items
        ]
        print(f"📋 Visible items in list: {visible_titles}")

        # Check if private/unlisted content is hidden
        private_visible = any("Private Test" in title for title in visible_titles)
        unlisted_visible = any("Unlisted Test" in title for title in visible_titles)
        public_visible = any("Public Test" in title for title in visible_titles)

        print(
            f"   Public content visible: {public_visible} "
            f"{'✅' if public_visible else '❌'}"
        )
        print(
            f"   Private content hidden: {not private_visible} "
            f"{'✅' if not private_visible else '❌'}"
        )
        print(
            f"   Unlisted content hidden: {not unlisted_visible} "
            f"{'✅' if not unlisted_visible else '❌'}"
        )
    else:
        print(f"❌ Failed to get about list: {response.status_code} {response.text}")

    # Test individual item access
    print("\n🔍 Testing individual item access (unauthenticated):")
    for visibility, item_id in item_ids.items():
        response = requests.get(f"{BASE_URL}/api/v1/about/{item_id}")
        if visibility == "public":
            if response.status_code == 200 and "content" in response.json():
                print(f"   {visibility.title()} item {item_id}: Accessible ✅")
            else:
                print(
                    f"   {visibility.title()} item {item_id}: "
                    f"Not accessible ❌ (should be accessible)"
                )
        else:  # private or unlisted
            if (
                response.status_code == 200
                and response.json().get("message") == "No visible content available"
            ):
                print(f"   {visibility.title()} item {item_id}: Properly hidden ✅")
            elif response.status_code == 200 and "content" in response.json():
                print(
                    f"   {visibility.title()} item {item_id}: "
                    f"Incorrectly visible ❌ (should be hidden)"
                )
            else:
                print(
                    f"   {visibility.title()} item {item_id}: "
                    f"Unexpected response ❓ {response.status_code}"
                )


def test_authenticated_access(token, item_ids):
    """Test that authenticated users can see their private content"""
    print("\n🔑 Testing authenticated access:")
    headers = {"Authorization": f"Bearer {token}"}

    for visibility, item_id in item_ids.items():
        response = requests.get(f"{BASE_URL}/api/v1/about/{item_id}", headers=headers)
        if response.status_code == 200 and "content" in response.json():
            print(f"   {visibility.title()} item {item_id}: Accessible to owner ✅")
        else:
            print(
                f"   {visibility.title()} item {item_id}: "
                f"Not accessible to owner ❌"
            )


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


def check_system_mode():
    """Check if system is in single-user mode"""
    response = requests.get(f"{BASE_URL}/api/v1/status")
    if response.status_code == 200:
        data = response.json()
        mode = data.get("mode", "unknown")
        print(f"📊 System mode: {mode}")
        return mode == "single_user"
    else:
        print("❓ Could not determine system mode")
        return False


def main():
    """Main test function"""
    print("🔒 Testing Privacy Filtering in Current Mode")

    # Check system mode
    is_single_user = check_system_mode()

    # Login
    token = login()
    if not token:
        return

    # Create test content
    item_ids = create_test_content(token)
    if not item_ids:
        print("❌ Could not create test content")
        return

    try:
        # Test privacy filtering
        test_privacy_filtering(item_ids)

        # Test authenticated access
        test_authenticated_access(token, item_ids)

        print("\n🎯 Privacy filtering test completed!")
        if is_single_user:
            print("   Tested in SINGLE-USER mode")
        else:
            print("   Tested in MULTI-USER mode")

    finally:
        # Clean up
        cleanup_test_content(token, item_ids)


if __name__ == "__main__":
    main()
