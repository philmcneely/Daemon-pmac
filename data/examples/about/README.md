# About Data Examples

This directory contains examples for the "about" endpoint, which stores basic information about a person or entity using the content/meta format.

## Schema

The about endpoint uses the flexible content/meta schema:

```json
{
  "content": "string (required) - Markdown content with about information",
  "meta": {
    "title": "string (optional) - Entry title",
    "date": "string (optional) - Date in YYYY-MM-DD format",
    "tags": "array (optional) - Array of tags for categorization",
    "status": "string (optional) - Entry status (draft, published, etc.)",
    "visibility": "string (optional) - public, unlisted, or private"
  }
}
```

## Example Data

The `about_example.json` file contains sample data showing:

1. **Personal Profile**: Individual developer with contact links in markdown
2. **Company Profile**: Business entity with structured information

## Content Structure

The `content` field supports rich markdown formatting including:

- **Headers**: Use `#` for main sections
- **Links**: `[Text](URL)` for social links and websites
- **Emphasis**: `**bold**` and `*italic*` text
- **Lists**: Use `-` for bullet points
- **Emojis**: 📍 🌐 💼 for visual elements

## Meta Field Descriptions

- **title**: Display title for the about entry
- **date**: When the information was last updated
- **tags**: Categories like ["personal", "developer", "company"]
- **status**: Content status (draft, published, archived)
- **visibility**:
  - `public`: Visible to everyone
  - `unlisted`: Accessible via direct link only
  - `private`: Only visible to owner

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

- **business_card**: Minimal public information only
- **professional**: Standard professional details
- **public_full**: All public information
- **ai_safe**: Safe for AI assistants (removes sensitive data)

**Examples:** `data/examples/about/`
