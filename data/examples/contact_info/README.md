# Contact Info Data Examples

This directory contains examples for the "contact_info" endpoint, which stores public-safe contact information using the content/meta format.

## Purpose

The contact_info endpoint is designed for sharing professional contact information in a privacy-conscious way. It allows you to control what contact details are publicly available while maintaining professional accessibility.

## Schema

The contact_info endpoint uses the flexible content/meta schema:

```json
{
  "content": "string (required) - Markdown content with contact information",
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

The `contact_info_example.json` file contains sample data showing:

1. **Professional Contact Channels**: Email, LinkedIn, social media
2. **Communication Preferences**: Response times and preferred methods
3. **Office Hours**: Availability for mentoring or consulting
4. **Privacy Guidelines**: Data handling and communication boundaries

## Content Structure

The `content` field supports rich markdown formatting including:

- **Contact Methods**: Email, social platforms, professional networks
- **Response Expectations**: Timeframes and communication preferences
- **Availability**: Office hours, consulting availability
- **Professional Services**: Speaking, mentoring, consulting offerings
- **Privacy Policies**: Data handling and communication guidelines

## Meta Field Descriptions

- **title**: Display title for the contact entry
- **date**: When contact information was last updated
- **tags**: Categories like ["contact", "professional", "communication"]
- **status**: Information status (active, limited, unavailable)
- **visibility**:
  - `public`: Visible to everyone
  - `unlisted`: Accessible via direct link only
  - `private`: Only visible to owner

## Usage

### Add Contact Information

```bash
curl -X POST "http://localhost:8000/api/v1/contact_info" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @contact_info_example.json
```

### Get Contact Information

```bash
# Get all contact info entries
curl "http://localhost:8000/api/v1/contact_info"

# In multi-user mode, get specific user's contact info
curl "http://localhost:8000/api/v1/contact_info/users/username"
```

## Privacy Levels

The contact_info endpoint supports privacy filtering:

- **business_card**: Minimal networking contact only
- **professional**: Standard professional contact details
- **public_full**: All public contact information
- **ai_safe**: Safe for AI assistants (removes sensitive contact data)

## Best Practices

- Keep contact information current and accurate
- Specify response time expectations to manage communication
- Use visibility controls to limit access as needed
- Include professional boundaries and communication preferences
- Regular updates when availability or preferences change

**Examples:** `data/examples/contact_info/`
