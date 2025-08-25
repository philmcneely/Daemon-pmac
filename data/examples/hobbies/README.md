# Hobbies Data Examples

This directory contains examples for the hobbies endpoint.

## Files

- `hobbies_example.json` - Example hobbies data structure

## API Endpoints

**Single User Mode:**
- `GET /api/v1/hobbies` - Get hobbies data
- `POST /api/v1/hobbies` - Update hobbies data

**Multi-User Mode:**
- `GET /api/v1/hobbies/users/{username}` - Get specific user's hobbies
- `POST /api/v1/hobbies/users/{username}` - Update specific user's hobbies

## Data Structure

```json
{
  "hobbies": [
    {
      "name": "Photography",
      "description": "Landscape and street photography",
      "skill_level": "Intermediate",
      "time_spent": "Weekends"
    }
  ],
  "interests": ["Technology", "Travel", "Music"]
}
```

## File Locations

**Examples:** `data/examples/hobbies/`
**Private Data:** `data/private/{username}/hobbies/`
