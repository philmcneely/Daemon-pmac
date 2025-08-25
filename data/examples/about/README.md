# About Data Examples

This directory contains examples for the "about" endpoint, which stores basic information about a person or entity.

## Schema

The about endpoint supports the following fields:

```json
{
  "name": "string (required)",
  "title": "string (optional)",
  "bio": "string (optional)", 
  "location": "string (optional)",
  "website": "string (optional)",
  "social_links": "object (optional)"
}
```

## Example Data

The `about_example.json` file contains sample data showing:

1. **Personal Profile**: Individual developer with social links
2. **Company Profile**: Business entity with multiple locations

## Field Descriptions

- **name**: Full name of person or entity (required)
- **title**: Job title, role, or company description
- **bio**: Detailed biography or description
- **location**: Geographic location or address
- **website**: Primary website URL
- **social_links**: Object containing social media and professional links

## Social Links Structure

```json
{
  "social_links": {
    "linkedin": "https://linkedin.com/in/username",
    "github": "https://github.com/username", 
    "twitter": "https://twitter.com/username",
    "mastodon": "https://mastodon.social/@username",
    "blog": "https://blog.example.com",
    "youtube": "https://youtube.com/@channel",
    "instagram": "https://instagram.com/username"
  }
}
```

## Usage

### Add About Information

```bash
curl -X POST "http://localhost:8000/api/v1/about" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @about_example.json
```

### Get About Information

```bash
# Get all about entries
curl "http://localhost:8000/api/v1/about"

# In multi-user mode, get specific user's about info
curl "http://localhost:8000/api/v1/about/users/username"
```

## Privacy Levels

The about endpoint supports privacy filtering:

- **business_card**: Name, title, basic contact
- **professional**: Full professional information
- **public_full**: All information marked as public
- **ai_safe**: Safe for AI assistants (removes sensitive data)

**Examples:** `data/examples/about/`
