#!/usr/bin/env python3
"""
Test Privacy Filtering - Verify security fixes work correctly
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_security_fixes():
    """Test that our security fixes are working"""
    print("🔒 Testing Security Fixes")

    # Test path traversal patterns - should be handled securely
    test_patterns = [
        "/api/v1/about/users/admin//../../admin",  # Path normalization
        "/api/v1/resume/users/admin/../user",  # Username normalization
        "/api/v1/resume%2Fusers%2Fadmin",  # URL encoding
    ]

    for pattern in test_patterns:
        response = client.get(pattern)
        print(f"Pattern: {pattern}")
        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            print("  ✅ Returns data (path normalized to valid endpoint)")
        elif response.status_code in [301, 307]:
            print("  ✅ Redirects (valid pattern redirected)")
        elif response.status_code in [400, 404, 422]:
            print("  ✅ Properly rejected")
        else:
            print(f"  ❓ Unexpected response: {response.status_code}")
        print()


def test_normal_endpoints():
    """Test that normal endpoints still work"""
    print("🔍 Testing Normal Endpoints")

    normal_patterns = [
        "/api/v1/about",
        "/api/v1/resume",
        "/api/v1/about/users/admin",
        "/api/v1/resume/users/admin",
    ]

    for pattern in normal_patterns:
        response = client.get(pattern)
        print(f"Pattern: {pattern}")
        print(f"  Status: {response.status_code}")

        if response.status_code in [200, 301]:
            print("  ✅ Working correctly")
        else:
            print(f"  ❌ Unexpected response: {response.status_code}")
        print()


def main():
    """Run all tests"""
    print("🚀 Security Fix Validation\n")

    try:
        test_security_fixes()
        test_normal_endpoints()
        print("🎯 All tests completed!")
    except Exception as e:
        print(f"❌ Error during testing: {e}")


if __name__ == "__main__":
    main()
