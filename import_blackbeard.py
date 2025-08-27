#!/usr/bin/env python3
"""
Blackbeard Data Import Script
Imports all Blackbeard example data into the Daemon API
"""

import json
import os
import sys

import requests

# Configuration
API_BASE_URL = "http://localhost:8005/api/v1"
AUTH_URL = "http://localhost:8005/auth/login"
DATA_DIR = "data/examples/private/blackbeard"

# Authentication credentials
USERNAME = "blackbeard"
PASSWORD = "fearsome_pirate"

# Mapping of filenames to endpoint names
ENDPOINT_MAPPING = {
    "resume.json": "resume",
    "about.json": "about",
    "ideas.json": "ideas",
    "skills.json": "skills",
    "favorite_books.json": "favorite_books",
    "problems.json": "problems",
    "hobbies.json": "hobbies",
    "projects.json": "projects",
    "looking_for.json": "looking_for",
    "values.json": "values",
    "quotes.json": "quotes",
    "contact_info.json": "contact_info",
    "events.json": "events",
    "achievements.json": "achievements",
    "goals.json": "goals",
    "learning.json": "learning",
}


def authenticate():
    """Authenticate with the API and return access token"""
    try:
        # Prepare authentication data (form-data format)
        auth_data = {"username": USERNAME, "password": PASSWORD}

        response = requests.post(AUTH_URL, data=auth_data)

        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print(f"🔐 Authentication successful for user: {USERNAME}")
            return access_token
        else:
            print(f"❌ Authentication failed: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


def load_json_file(filepath):
    """Load and return JSON data from file"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def import_to_endpoint(endpoint_name, data, access_token):
    """Import data to specific endpoint"""
    url = f"{API_BASE_URL}/{endpoint_name}"

    # Headers with authentication
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        if isinstance(data, list):
            # Multiple items - use batch import if available
            for item in data:
                response = requests.post(url, json=item, headers=headers)
                if response.status_code in [200, 201]:
                    print(f"✅ Successfully imported item to {endpoint_name}")
                else:
                    print(
                        f"❌ Failed to import item to {endpoint_name}: "
                        f"{response.status_code} - {response.text}"
                    )
        else:
            # Single item
            response = requests.post(url, json=data, headers=headers)
            if response.status_code in [200, 201]:
                print(f"✅ Successfully imported data to {endpoint_name}")
            else:
                print(
                    f"❌ Failed to import to {endpoint_name}: "
                    f"{response.status_code} - {response.text}"
                )

    except Exception as e:
        print(f"❌ Error importing to {endpoint_name}: {e}")


def main():
    """Main import process"""
    print("🏴‍☠️ Starting Blackbeard Data Import...")
    print(f"Target API: {API_BASE_URL}")
    print(f"Data Directory: {DATA_DIR}")
    print("-" * 50)

    # Authenticate first
    access_token = authenticate()
    if not access_token:
        print("❌ Authentication failed. Cannot proceed with import.")
        sys.exit(1)

    # Check if data directory exists
    if not os.path.exists(DATA_DIR):
        print(f"❌ Data directory not found: {DATA_DIR}")
        sys.exit(1)

    # Import each file
    for filename, endpoint_name in ENDPOINT_MAPPING.items():
        filepath = os.path.join(DATA_DIR, filename)

        if os.path.exists(filepath):
            print(f"📁 Processing {filename} -> {endpoint_name}")
            data = load_json_file(filepath)

            if data is not None:
                import_to_endpoint(endpoint_name, data, access_token)
            else:
                print(f"❌ Failed to load data from {filename}")
        else:
            print(f"⚠️ File not found: {filename}")

    print("-" * 50)
    print("🏴‍☠️ Blackbeard import complete!")
    print("Visit http://localhost:8005/docs to explore the API")


if __name__ == "__main__":
    main()
