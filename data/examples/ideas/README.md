# Ideas Data Examples

This directory contains examples for the ideas endpoint.

## Files

- `ideas_example.json` - Example ideas data structure

## API Endpoints

**Single User Mode:**
- `GET /api/v1/ideas` - Get ideas data
- `POST /api/v1/ideas` - Update ideas data

**Multi-User Mode:**
- `GET /api/v1/ideas/users/{username}` - Get specific user's ideas
- `POST /api/v1/ideas/users/{username}` - Update specific user's ideas

## Data Structure

```json
{
  "ideas": [
    {
      "title": "AI-Powered Code Review Tool",
      "description": "A tool that uses AI to review code...",
      "category": "Software Development",
      "status": "concept",
      "created_date": "2023-01-15"
    }
  ],
  "categories": ["Software Development", "Business", "Personal"]
}
```

## File Locations

**Examples:** `data/examples/ideas/`
**Private Data:** `data/private/{username}/ideas/`
