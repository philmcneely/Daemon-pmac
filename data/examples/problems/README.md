# Problems Data Examples

This directory contains examples for the problems endpoint.

## Files

- `problems_example.json` - Example problems data structure

## API Endpoints

**Single User Mode:**
- `GET /api/v1/problems` - Get problems data
- `POST /api/v1/problems` - Update problems data

**Multi-User Mode:**
- `GET /api/v1/problems/users/{username}` - Get specific user's problems
- `POST /api/v1/problems/users/{username}` - Update specific user's problems

## Data Structure

```json
{
  "problems": [
    {
      "title": "Finding efficient data storage",
      "description": "Need a better way to store large datasets...",
      "category": "Technical",
      "priority": "high",
      "status": "investigating"
    }
  ],
  "categories": ["Technical", "Personal", "Business"]
}
```

## File Locations

**Examples:** `data/examples/problems/`
**Private Data:** `data/private/{username}/problems/`
