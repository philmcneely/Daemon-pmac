"""
End-to-end tests for the favorite_books endpoint with flexible markdown support.

These tests validate the favorite_books endpoint which supports both:
1. New flexible markdown format: {content, meta}
2. Legacy structured format: {title, author, isbn, rating, review, genres, date_read}

The endpoint should maintain backward compatibility while enabling rich markdown content.
"""

import pytest
from fastapi.testclient import TestClient


class TestFavoriteBooksEndpoint:
    """Test suite for the favorite_books endpoint with flexible markdown support."""

    def test_favorite_books_create_with_markdown(
        self, client: TestClient, auth_headers
    ):
        """Test creating a favorite book with flexible markdown content"""
        book_data = {
            "content": "### Atomic Habits — James Clear\n\n*Notes:* Practical frameworks for habit formation. Key takeaway: system design beats motivation.\n\n**Rating:** ⭐⭐⭐⭐⭐",
            "meta": {
                "title": "Atomic Habits",
                "author": "James Clear",
                "tags": ["productivity", "habits", "psychology"],
                "visibility": "public",
            },
        }

        response = client.post(
            "/api/v1/favorite_books", json=book_data, headers=auth_headers
        )
        assert response.status_code == 200

        created_book = response.json()
        assert created_book["id"]
        assert created_book["data"]["content"] == book_data["content"]
        assert created_book["data"]["meta"]["title"] == "Atomic Habits"
        assert created_book["data"]["meta"]["author"] == "James Clear"
        assert created_book["data"]["meta"]["tags"] == [
            "productivity",
            "habits",
            "psychology",
        ]

    def test_favorite_books_create_with_legacy_format(
        self, client: TestClient, auth_headers
    ):
        """Test creating a favorite book with legacy structured format"""
        book_data = {
            "title": "The Pragmatic Programmer",
            "author": "David Thomas, Andrew Hunt",
            "isbn": "978-0135957059",
            "rating": 5,
            "review": "Essential reading for any developer. Timeless advice that remains relevant.",
            "genres": ["Programming", "Software Engineering"],
            "date_read": "2024-06-15",
        }

        response = client.post(
            "/api/v1/favorite_books", json=book_data, headers=auth_headers
        )
        assert response.status_code == 200

        created_book = response.json()
        assert created_book["data"]["title"] == book_data["title"]
        assert created_book["data"]["author"] == book_data["author"]
        assert created_book["data"]["rating"] == book_data["rating"]

    def test_favorite_books_get_list(self, client: TestClient, auth_headers):
        """Test retrieving list of favorite books"""
        # Create a book first
        book_data = {
            "content": "### Deep Work — Cal Newport\n\nFocus strategies for the modern workplace.",
            "meta": {"title": "Deep Work", "author": "Cal Newport"},
        }

        create_response = client.post(
            "/api/v1/favorite_books", json=book_data, headers=auth_headers
        )
        assert create_response.status_code == 200

        # Get the list
        list_response = client.get("/api/v1/favorite_books")
        assert list_response.status_code == 200

        books = list_response.json()
        assert isinstance(books, list)
        assert len(books) >= 1

        # Check that our created book is in the list
        created_book_found = any(
            book.get("content") == book_data["content"] for book in books
        )
        assert created_book_found

    def test_favorite_books_get_single_item(self, client: TestClient, auth_headers):
        """Test retrieving a single favorite book by ID"""
        book_data = {
            "content": "### Sapiens — Yuval Noah Harari\n\nA brief history of humankind. Fascinating perspectives on human evolution and society.",
            "meta": {
                "title": "Sapiens",
                "author": "Yuval Noah Harari",
                "tags": ["history", "anthropology"],
                "visibility": "public",
            },
        }

        create_response = client.post(
            "/api/v1/favorite_books", json=book_data, headers=auth_headers
        )
        assert create_response.status_code == 200
        created_book = create_response.json()

        # Now retrieve it
        get_response = client.get(f"/api/v1/favorite_books/{created_book['id']}")
        assert get_response.status_code == 200

        retrieved_book = get_response.json()
        assert retrieved_book["id"] == created_book["id"]
        assert retrieved_book["content"] == book_data["content"]

    def test_favorite_books_update_item(self, client: TestClient, auth_headers):
        """Test updating an existing favorite book"""
        # Create a book
        original_data = {
            "content": "### Original Book Review\n\nThis is the original review.",
            "meta": {"title": "Original Title", "author": "Original Author"},
        }

        create_response = client.post(
            "/api/v1/favorite_books", json=original_data, headers=auth_headers
        )
        assert create_response.status_code == 200
        created_book = create_response.json()

        # Update it
        updated_data = {
            "content": "### Updated Book Review\n\nThis is the updated review with more insights.\n\n**Key Takeaways:**\n- Point 1\n- Point 2",
            "meta": {
                "title": "Updated Title",
                "author": "Updated Author",
                "status": "completed",
            },
        }

        update_response = client.put(
            f"/api/v1/favorite_books/{created_book['id']}",
            json=updated_data,
            headers=auth_headers,
        )
        assert update_response.status_code == 200

        updated_book = update_response.json()
        assert updated_book["data"]["content"] == updated_data["content"]
        assert updated_book["data"]["meta"]["title"] == updated_data["meta"]["title"]
        assert updated_book["data"]["meta"]["author"] == updated_data["meta"]["author"]
        assert updated_book["data"]["meta"]["status"] == updated_data["meta"]["status"]

    def test_favorite_books_delete_item(self, client: TestClient, auth_headers):
        """Test deleting a favorite book"""
        # Create a book
        book_data = {
            "content": "### Book to Delete\n\nThis will be deleted.",
            "meta": {"title": "Delete Me", "author": "Test Author"},
        }

        create_response = client.post(
            "/api/v1/favorite_books", json=book_data, headers=auth_headers
        )
        assert create_response.status_code == 200
        created_book = create_response.json()

        # Delete it
        delete_response = client.delete(
            f"/api/v1/favorite_books/{created_book['id']}", headers=auth_headers
        )
        assert delete_response.status_code == 200

        # Verify it's deleted (should return 404 or empty list)
        get_response = client.get(f"/api/v1/favorite_books/{created_book['id']}")
        assert get_response.status_code == 404

    def test_favorite_books_html_unescaping(self, client: TestClient, auth_headers):
        """Test that HTML entities in markdown content are properly unescaped"""
        book_data = {
            "content": "### Code &amp; Algorithms\n\nThis book covers algorithms &gt; data structures &lt; performance.",
            "meta": {"title": "Code Test", "author": "Test Author"},
        }

        response = client.post(
            "/api/v1/favorite_books", json=book_data, headers=auth_headers
        )
        assert response.status_code == 200

        created_book = response.json()
        # HTML entities should be unescaped
        assert "&amp;" not in created_book["data"]["content"]
        assert "&gt;" not in created_book["data"]["content"]
        assert "&lt;" not in created_book["data"]["content"]
        assert (
            "algorithms > data structures < performance"
            in created_book["data"]["content"]
        )

    def test_favorite_books_validation_errors(self, client: TestClient, auth_headers):
        """Test validation errors for invalid book data"""
        # Test missing required fields
        invalid_data = {
            "meta": {"tags": ["test"]}
            # Missing both content and title+author
        }

        response = client.post(
            "/api/v1/favorite_books", json=invalid_data, headers=auth_headers
        )
        assert response.status_code == 400

        # Test invalid rating in legacy format
        invalid_rating_data = {
            "title": "Test Book",
            "author": "Test Author",
            "rating": 10,  # Invalid: should be 1-5
        }

        response = client.post(
            "/api/v1/favorite_books", json=invalid_rating_data, headers=auth_headers
        )
        assert response.status_code == 400

    def test_favorite_books_privacy_controls(self, client: TestClient, auth_headers):
        """Test privacy visibility controls for favorite books"""
        # Create books with different visibility levels
        public_book = {
            "content": "### Public Book\n\nThis is public.",
            "meta": {"title": "Public", "author": "Author", "visibility": "public"},
        }

        private_book = {
            "content": "### Private Book\n\nThis is private.",
            "meta": {"title": "Private", "author": "Author", "visibility": "private"},
        }

        # Create both books
        pub_response = client.post(
            "/api/v1/favorite_books", json=public_book, headers=auth_headers
        )
        priv_response = client.post(
            "/api/v1/favorite_books", json=private_book, headers=auth_headers
        )

        assert pub_response.status_code == 200
        assert priv_response.status_code == 200

        # Test that privacy metadata is preserved
        pub_book_data = pub_response.json()
        priv_book_data = priv_response.json()

        assert pub_book_data["data"]["meta"]["visibility"] == "public"
        assert priv_book_data["data"]["meta"]["visibility"] == "private"

    def test_favorite_books_backward_compatibility(
        self, client: TestClient, auth_headers
    ):
        """Test that legacy and new formats can coexist"""
        # Create one book with legacy format
        legacy_book = {
            "title": "Legacy Book",
            "author": "Legacy Author",
            "rating": 4,
            "review": "Good book using old format.",
        }

        # Create one book with new format
        new_book = {
            "content": "### New Format Book\n\nUsing flexible markdown content.",
            "meta": {"title": "New Book", "author": "New Author"},
        }

        # Both should work
        legacy_response = client.post(
            "/api/v1/favorite_books", json=legacy_book, headers=auth_headers
        )
        new_response = client.post(
            "/api/v1/favorite_books", json=new_book, headers=auth_headers
        )

        assert legacy_response.status_code == 200
        assert new_response.status_code == 200

        # Verify both are retrievable
        books_response = client.get("/api/v1/favorite_books")
        assert books_response.status_code == 200
        books = books_response.json()

        # Should have both books
        legacy_found = any(book.get("title") == "Legacy Book" for book in books)
        new_found = any(
            book.get("content", "").startswith("### New Format Book") for book in books
        )

        assert legacy_found
        assert new_found

    def test_favorite_books_multi_user_support(self, client: TestClient, auth_headers):
        """Test multi-user support for favorite books"""
        # Create book as authenticated user
        book_data = {
            "content": "### User Specific Book\n\nThis belongs to a specific user.",
            "meta": {"title": "User Book", "author": "Test Author"},
        }

        response = client.post(
            "/api/v1/favorite_books", json=book_data, headers=auth_headers
        )
        assert response.status_code == 200
        created_book = response.json()

        # Verify ownership is tracked
        assert "created_by" in created_book or "owner" in created_book

    def test_favorite_books_bulk_operations(self, client: TestClient, auth_headers):
        """Test bulk operations if supported"""
        bulk_books = [
            {"content": "### Bulk Book 1\n\nFirst bulk book."},
            {"content": "### Bulk Book 2\n\nSecond bulk book."},
        ]

        for book_data in bulk_books:
            response = client.post(
                "/api/v1/favorite_books", json=book_data, headers=auth_headers
            )
            assert response.status_code == 200

        # Verify all books are retrievable
        list_response = client.get("/api/v1/favorite_books")
        assert list_response.status_code == 200
        books = list_response.json()
        assert len(books) >= len(bulk_books)

    def test_favorite_books_pagination(self, client: TestClient, auth_headers):
        """Test pagination for favorite books list"""
        # Create multiple books
        for i in range(5):
            book_data = {
                "content": f"### Book {i}\n\nThis is book number {i}.",
                "meta": {"title": f"Book {i}", "author": "Test Author"},
            }
            response = client.post(
                "/api/v1/favorite_books", json=book_data, headers=auth_headers
            )
            assert response.status_code == 200

        # Test pagination
        page_response = client.get("/api/v1/favorite_books?page=1&size=3")
        assert page_response.status_code == 200
        books = page_response.json()
        assert len(books) <= 3
