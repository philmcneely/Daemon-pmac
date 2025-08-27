#!/usr/bin/env python3
"""
Script to fetch all Blackbeard's data from the Daemon API and save it to a text file.
"""

import json
from datetime import datetime
from typing import Any, Dict, List

import requests

# API configuration
BASE_URL = "http://localhost:8006"
USERNAME = "blackbeard"
OUTPUT_FILE = "blackbeard_data_export.txt"


def make_api_request(url: str) -> Dict[str, Any]:
    """Make an API request and return the JSON response."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return {}


def get_all_endpoints() -> List[str]:
    """Get list of all available endpoints."""
    url = f"{BASE_URL}/api/v1/endpoints/"
    data = make_api_request(url)
    if isinstance(data, list):
        return [endpoint.get("name", "") for endpoint in data if endpoint.get("name")]
    return []


def get_endpoint_data(endpoint_name: str) -> List[Dict[str, Any]]:
    """Get all data for a specific endpoint for Blackbeard."""
    url = f"{BASE_URL}/api/v1/users/{USERNAME}/{endpoint_name}"
    data = make_api_request(url)
    return data if isinstance(data, list) else []


def format_data_for_output(endpoint_name: str, data: List[Dict[str, Any]]) -> str:
    """Format endpoint data for text output."""
    if not data:
        return f"\n=== {endpoint_name.upper()} ===\nNo data available.\n"

    output = f"\n=== {endpoint_name.upper()} ===\n"
    output += f"Total items: {len(data)}\n\n"

    for i, item in enumerate(data, 1):
        output += f"--- Item {i} ---\n"

        # Handle different data structures
        if isinstance(item, dict):
            for key, value in item.items():
                if key == "meta":
                    continue  # Skip meta for readability

                if isinstance(value, (dict, list)):
                    output += f"{key}: {json.dumps(value, indent=2)}\n"
                else:
                    output += f"{key}: {value}\n"
        else:
            output += f"Data: {item}\n"

        output += "\n"

    return output


def main():
    """Main function to export all Blackbeard's data."""
    print(f"🏴‍☠️ Fetching all data for user '{USERNAME}' from {BASE_URL}")
    print("=" * 60)

    # Get all available endpoints
    print("📋 Getting list of endpoints...")
    endpoints = get_all_endpoints()

    if not endpoints:
        print("❌ No endpoints found or unable to fetch endpoints list")
        return

    print(f"✅ Found {len(endpoints)} endpoints: {', '.join(endpoints)}")

    # Start building the output
    output_content = f"""
BLACKBEARD'S DATA EXPORT
========================
Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
API Base URL: {BASE_URL}
Username: {USERNAME}
Total Endpoints: {len(endpoints)}

"""

    # Fetch data for each endpoint
    total_items = 0
    for endpoint in endpoints:
        print(f"🔍 Fetching data for endpoint: {endpoint}")

        data = get_endpoint_data(endpoint)
        total_items += len(data)

        # Format and add to output
        formatted_data = format_data_for_output(endpoint, data)
        output_content += formatted_data

        print(f"   └── Found {len(data)} items")

    # Add summary
    summary = f"""
=== EXPORT SUMMARY ===
Total Endpoints Processed: {len(endpoints)}
Total Data Items: {total_items}
Export Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Endpoints Processed:
{chr(10).join(f"- {endpoint}" for endpoint in endpoints)}
"""

    output_content += summary

    # Write to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(output_content)

    print("=" * 60)
    print(f"✅ Export completed!")
    print(f"📄 Data saved to: {OUTPUT_FILE}")
    print(f"📊 Total items exported: {total_items}")
    print(f"🗂️  Total endpoints: {len(endpoints)}")


if __name__ == "__main__":
    main()
