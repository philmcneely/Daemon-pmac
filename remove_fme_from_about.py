#!/usr/bin/env python3
"""
Remove FME from Blackbeard's About Content
Script to remove the "FME" prefix from about content using the API
"""

import requests

# API Configuration
BASE_URL = "http://localhost:8005"
USERNAME = "blackbeard"
PASSWORD = "testpass123"


def login():
    """Login and get JWT token"""
    login_data = {"username": USERNAME, "password": PASSWORD}

    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login successful")
        return token
    else:
        print(f"❌ Login failed: {response.status_code} {response.text}")
        return None


def get_about_content(token):
    """Get current about content"""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(f"{BASE_URL}/api/v1/about", headers=headers)
    if response.status_code == 200:
        items = response.json()["items"]
        if items:
            return items[0]  # Get the first (and likely only) about item
        else:
            print("❌ No about content found")
            return None
    else:
        print(f"❌ Failed to get about content: {response.status_code} {response.text}")
        return None


def update_about_content(token, item_id, current_content):
    """Update about content to remove FME prefix"""
    headers = {"Authorization": f"Bearer {token}"}

    # Remove "FME " from the beginning of the content if it exists
    updated_content = current_content
    if updated_content.startswith("FME "):
        updated_content = updated_content[4:]  # Remove "FME " (4 characters)
        print(f"✅ Removing 'FME ' prefix from content")
    else:
        print(f"ℹ️  No 'FME ' prefix found in content")
        return False

    update_data = {"content": updated_content}

    response = requests.put(
        f"{BASE_URL}/api/v1/about/{item_id}", headers=headers, json=update_data
    )

    if response.status_code == 200:
        print(f"✅ About content updated successfully")
        print(f"📝 New content: {updated_content[:100]}...")
        return True
    else:
        print(
            f"❌ Failed to update about content: "
            f"{response.status_code} {response.text}"
        )
        return False


def main():
    """Main function to remove FME from about content"""
    print("🔧 Removing FME from Blackbeard's about content...")

    # Step 1: Login
    token = login()
    if not token:
        return

    # Step 2: Get current about content
    about_item = get_about_content(token)
    if not about_item:
        return

    print(f"📖 Current content: {about_item['content'][:100]}...")

    # Step 3: Update content to remove FME
    success = update_about_content(token, about_item["id"], about_item["content"])

    if success:
        print("\n🎉 Successfully removed FME from about content!")
    else:
        print("\n❌ Failed to remove FME from about content")


if __name__ == "__main__":
    main()
