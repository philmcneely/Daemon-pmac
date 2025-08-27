"""
Debug test for favorite_books HTML unescaping
"""

import pytest
from fastapi.testclient import TestClient


def test_debug_favorite_books_html(client: TestClient, auth_headers):
    """Debug test to see what's happening with HTML content"""
    book_data = {
        "content": "### Code &amp; Algorithms\n\nThis book covers algorithms &gt; data structures &lt; performance.",
        "meta": {"title": "Code Test", "author": "Test Author"},
    }

    print(f"\nSending data: {book_data['content']}")

    response = client.post(
        "/api/v1/favorite_books", json=book_data, headers=auth_headers
    )
    print(f"Response status: {response.status_code}")

    if response.status_code == 200:
        created_book = response.json()
        content = created_book["data"]["content"]
        print(f"Received content: {content}")
        print(f"Contains &amp;: {'&amp;' in content}")
        print(f"Contains &gt;: {'&gt;' in content}")
        print(f"Contains &lt;: {'&lt;' in content}")
    else:
        print(f"Error response: {response.text}")


if __name__ == "__main__":
    # This would need to be run with pytest
    print(
        "Run with: python -m pytest debug_favorite_books_html.py::test_debug_favorite_books_html -v -s"
    )
