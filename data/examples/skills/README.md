# Skills Data Examples

This directory contains examples for the skills endpoint.

## Files

- `skills_example.json` - Example skills data structure

## API Endpoints

**Single User Mode:**
- `GET /api/v1/skills` - Get skills data
- `POST /api/v1/skills` - Update skills data

**Multi-User Mode:**
- `GET /api/v1/skills/users/{username}` - Get specific user's skills
- `POST /api/v1/skills/users/{username}` - Update specific user's skills

## Data Structure

```json
{
  "technical_skills": [
    {
      "category": "Programming Languages",
      "skills": ["Python", "JavaScript", "Go"]
    }
  ],
  "soft_skills": ["Leadership", "Communication"],
  "certifications": [
    {
      "name": "AWS Certified Developer",
      "issuer": "Amazon",
      "date": "2023-01-15"
    }
  ]
}
```

## File Locations

**Examples:** `data/examples/skills/`
**Private Data:** `data/private/{username}/skills/`
