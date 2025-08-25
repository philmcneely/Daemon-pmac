# Looking For Data Examples

This directory contains examples for the "looking for" endpoint.

## Files

- `looking_for_example.json` - Example looking for data structure

## API Endpoints

**Single User Mode:**
- `GET /api/v1/looking_for` - Get looking for data
- `POST /api/v1/looking_for` - Update looking for data

**Multi-User Mode:**
- `GET /api/v1/looking_for/users/{username}` - Get specific user's looking for data
- `POST /api/v1/looking_for/users/{username}` - Update specific user's looking for data

## Data Structure

```json
{
  "looking_for": [
    {
      "type": "job_opportunity",
      "title": "Senior Software Engineer",
      "description": "Looking for a senior role in a tech company...",
      "requirements": ["Remote work", "Good work-life balance"],
      "status": "actively_looking"
    }
  ],
  "categories": ["job_opportunity", "collaboration", "mentorship", "learning"]
}
```

## File Locations

**Examples:** `data/examples/looking_for/`
**Private Data:** `data/private/{username}/looking_for/`
