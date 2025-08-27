# Favorite Books Data Examples

This directory contains examples for the favorite_books endpoint with flexible markdown support.

## Files

- `favorite_books_example.json` - Example favorite books data with both flexible markdown and legacy formats

## API Endpoints

**Single User Mode:**
- `GET /api/v1/favorite_books` - Get favorite books
- `GET /api/v1/favorite_books/{id}` - Get specific book
- `POST /api/v1/favorite_books` - Create new book entry
- `PUT /api/v1/favorite_books/{id}` - Update book entry
- `DELETE /api/v1/favorite_books/{id}` - Delete book entry

**Multi-User Mode:**
- `GET /api/v1/favorite_books/users/{username}` - Get specific user's books
- `POST /api/v1/favorite_books/users/{username}` - Create book for specific user

## Data Structure

### New Flexible Markdown Format (Recommended)

```json
{
  "content": "### Atomic Habits — James Clear\n\n*Notes:* Practical frameworks for habit formation...",
  "meta": {
    "title": "Atomic Habits",
    "author": "James Clear",
    "date": "2024-08-15",
    "tags": ["productivity", "psychology"],
    "visibility": "public"
  }
}
```

### Legacy Structured Format (Backward Compatible)

```json
{
  "title": "The Pragmatic Programmer",
  "author": "David Thomas, Andrew Hunt",
  "isbn": "978-0135957059",
  "rating": 5,
  "review": "Essential reading for any developer...",
  "genres": ["programming", "career-development"],
  "date_read": "2023-01-10"
}
  ],
  "currently_reading": [],
  "want_to_read": []
}
```

## File Locations

**Examples:** `data/examples/books/`
**Private Data:** `data/private/{username}/books/`
