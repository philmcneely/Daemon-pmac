"""
Debug script to test favorite_books endpoint response format
"""

import json

import requests


# Test the favorite_books endpoint to see actual response structure
def test_favorite_books_response():
    try:
        # Create test data
        book_data = {
            "content": "### Atomic Habits — James Clear\n\n*Notes:* Practical frameworks.",
            "meta": {
                "title": "Atomic Habits",
                "author": "James Clear",
                "tags": ["productivity"],
                "visibility": "public",
            },
        }

        print("Request data:")
        print(json.dumps(book_data, indent=2))

        # Note: This would require authentication in real test
        print("\nThis would be sent to POST /api/v1/favorite_books")
        print("Expected response format should match ideas endpoint pattern")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_favorite_books_response()
