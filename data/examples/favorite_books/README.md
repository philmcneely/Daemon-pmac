# Favorite Books Data Examples

This directory contains examples for the favorite_books endpoint.

## Files

- `favorite_books_example.json` - Example favorite books data structure

## API Endpoints

**Single User Mode:**
- `GET /api/v1/books` - Get favorite books
- `POST /api/v1/books` - Update favorite books

**Multi-User Mode:**
- `GET /api/v1/books/users/{username}` - Get specific user's books
- `POST /api/v1/books/users/{username}` - Update specific user's books

## Data Structure

```json
{
  "favorite_books": [
    {
      "title": "The Pragmatic Programmer",
      "author": "David Thomas, Andrew Hunt",
      "genre": "Technology",
      "rating": 5,
      "review": "Essential reading for any developer..."
    }
  ],
  "currently_reading": [],
  "want_to_read": []
}
```

## File Locations

**Examples:** `data/examples/books/`
**Private Data:** `data/private/{username}/books/`
