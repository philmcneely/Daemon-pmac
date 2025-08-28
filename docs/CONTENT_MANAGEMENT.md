# Content Management Guide

This guide explains how to create, read, update, and delete content in the Daemon Personal API using authenticated endpoints.

## Overview

The Daemon API provides two types of endpoints for content access:

- **Public Endpoints**: Clean, user-friendly views without internal IDs (e.g., `/api/v1/about/users/blackbeard`)
- **Authenticated Endpoints**: Management views with item IDs for CRUD operations (e.g., `/api/v1/about`)

## Authentication Workflow

### 1. Login and Get JWT Token

```bash
# Login with username and password
curl -X POST "http://localhost:8005/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password"

# Response includes access token
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Use Token for Authenticated Requests

Include the JWT token in the Authorization header for all authenticated requests:

```bash
# Store token for convenience
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Use token in requests
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8005/api/v1/about"
```

## Content Management Operations

### Reading Content with Item IDs

**Authenticated endpoint** (shows item IDs for management):
```bash
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8005/api/v1/about"
```

Response includes item IDs:
```json
{
  "items": [
    {
      "id": "42",
      "content": "FME I am Edward Teach, though the world knows me better as Blackbeard...",
      "meta": {
        "title": "About Edward Teach (Blackbeard)",
        "date": "1718-06-15",
        "tags": ["biography", "personal", "history", "pirate"],
        "status": "active",
        "visibility": "public"
      },
      "data": { /* full content structure */ },
      "updated_at": "2025-08-27T17:55:32",
      "created_at": "2025-08-27T17:28:38"
    }
  ]
}
```

**Public endpoint** (clean view, no IDs):
```bash
curl "http://localhost:8005/api/v1/about/users/blackbeard"
```

Response is user-friendly:
```json
[
  {
    "content": "FME I am Edward Teach, though the world knows me better as Blackbeard...",
    "meta": {
      "title": "About Edward Teach (Blackbeard)",
      "date": "1718-06-15",
      "tags": ["biography", "personal", "history", "pirate"],
      "status": "active",
      "visibility": "public"
    }
  }
]
```

### Creating New Content

Use POST to create new content entries:

```bash
curl -X POST "http://localhost:8005/api/v1/about" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "# My New About Section\n\nThis is my updated information...",
    "meta": {
      "title": "About Me - Updated",
      "date": "2025-08-27",
      "tags": ["biography", "personal"],
      "status": "active",
      "visibility": "public"
    }
  }'
```

### Updating Existing Content

Use PUT with the item ID to update specific content:

```bash
# First, get the item ID from authenticated endpoint
ITEM_ID="42"

# Update the content
curl -X PUT "http://localhost:8005/api/v1/about/$ITEM_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "FME I am Edward Teach, updated content here...",
    "meta": {
      "title": "About Edward Teach (Blackbeard) - Updated",
      "date": "2025-08-27",
      "tags": ["biography", "personal", "history", "pirate"],
      "status": "active",
      "visibility": "public"
    }
  }'
```

### Deleting Content

Use DELETE with the item ID:

```bash
curl -X DELETE "http://localhost:8005/api/v1/about/$ITEM_ID" \
  -H "Authorization: Bearer $TOKEN"
```

## Complete Example Script

Here's a complete example of the content management workflow:

```bash
#!/bin/bash

# Configuration
API_BASE="http://localhost:8005"
USERNAME="blackbeard"
PASSWORD="testpass123"

echo "🔐 Authenticating..."
# Login and get token
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USERNAME&password=$PASSWORD")

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')

if [ "$TOKEN" = "null" ]; then
  echo "❌ Authentication failed"
  echo "$LOGIN_RESPONSE"
  exit 1
fi

echo "✅ Authentication successful"

# Get current content with item IDs
echo "📋 Getting current content..."
CONTENT_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "$API_BASE/api/v1/about")

echo "$CONTENT_RESPONSE" | jq .

# Extract item ID (assuming there's at least one item)
ITEM_ID=$(echo "$CONTENT_RESPONSE" | jq -r '.items[0].id')

if [ "$ITEM_ID" != "null" ] && [ "$ITEM_ID" != "" ]; then
  echo "📝 Updating content with ID: $ITEM_ID"

  # Update content
  UPDATE_RESPONSE=$(curl -s -X PUT "$API_BASE/api/v1/about/$ITEM_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "content": "Updated via script: I am Edward Teach, also known as Blackbeard...",
      "meta": {
        "title": "About Edward Teach (Blackbeard) - Script Updated",
        "date": "2025-08-27",
        "tags": ["biography", "personal", "history", "pirate", "script-updated"],
        "status": "active",
        "visibility": "public"
      }
    }')

  echo "✅ Content updated:"
  echo "$UPDATE_RESPONSE" | jq .
else
  echo "ℹ️  No existing content found, creating new..."

  # Create new content
  CREATE_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/about" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "content": "Created via script: I am Edward Teach, also known as Blackbeard...",
      "meta": {
        "title": "About Edward Teach (Blackbeard) - Script Created",
        "date": "2025-08-27",
        "tags": ["biography", "personal", "history", "pirate", "script-created"],
        "status": "active",
        "visibility": "public"
      }
    }')

  echo "✅ Content created:"
  echo "$CREATE_RESPONSE" | jq .
fi

# Verify by checking public endpoint
echo "🔍 Verifying via public endpoint..."
PUBLIC_RESPONSE=$(curl -s "$API_BASE/api/v1/about/users/$USERNAME")
echo "$PUBLIC_RESPONSE" | jq .
```

## Available Endpoints

All content endpoints support the same authentication and CRUD patterns:

### Content/Meta Schema Endpoints
- `about` - Basic information about the person
- `ideas` - Ideas and thoughts
- `skills` - Skills and competencies
- `favorite_books` - Book recommendations
- `hobbies` - Personal interests and hobbies
- `looking_for` - What you're seeking (jobs, opportunities, etc.)
- `projects` - Personal and professional projects
- `values` - Personal values and principles
- `quotes` - Favorite quotes or sayings
- `contact_info` - Contact information
- `events` - Important events or milestones
- `achievements` - Accomplishments and achievements
- `goals` - Personal and professional goals
- `learning` - Current learning activities
- `problems` - Problems you're trying to solve
- `personal_story` - Your personal story or journey
- `recommendations` - Recommendations you've received

### Structured Schema Endpoints
- `resume` - Professional resume (structured format)

## Content Schema

### Content/Meta Schema
Most endpoints use a flexible content/meta schema:

```json
{
  "content": "Markdown content here...",
  "meta": {
    "title": "Optional title",
    "date": "YYYY-MM-DD",
    "tags": ["tag1", "tag2"],
    "status": "active|draft|archived",
    "visibility": "public|unlisted|private"
  }
}
```

### Resume Schema
The resume endpoint uses a structured format - see existing documentation for details.

## Privacy and Visibility

### Visibility Levels
- **public**: Visible to everyone
- **unlisted**: Not listed publicly but accessible via direct link
- **private**: Only visible to authenticated user

### Privacy Filtering
Public endpoints automatically apply privacy filtering based on user settings and visibility levels.

## Security Notes

- JWT tokens expire automatically for security
- Only authenticated users can perform create, update, and delete operations
- Users can only modify their own content (unless they're admin)
- All operations are logged in the audit trail
- Rate limiting may apply to prevent abuse

## Troubleshooting

### Common Issues

1. **"Method Not Allowed" (405)**
   - Ensure you're using the correct HTTP method (GET, POST, PUT, DELETE)
   - Check that you're hitting the right endpoint pattern

2. **"Unauthorized" (401)**
   - Your JWT token may have expired - login again
   - Ensure the Authorization header is properly formatted: `Authorization: Bearer <token>`

3. **"Forbidden" (403)**
   - You may be trying to modify content you don't own
   - Check that you're authenticated as the correct user

4. **"Not Found" (404)**
   - The endpoint or item ID doesn't exist
   - Double-check the endpoint name and item ID

### Getting Help

- Check the OpenAPI documentation at `/docs` for detailed endpoint specifications
- Review the audit logs for operation history
- Use the health check endpoint `/health` to verify API status

## Best Practices

1. **Always authenticate** before attempting content management operations
2. **Use public endpoints** for displaying content to users
3. **Use authenticated endpoints** for management operations
4. **Store JWT tokens securely** and refresh them as needed
5. **Validate content** before submitting (markdown formatting, required fields)
6. **Use meaningful metadata** (titles, tags, dates) for better organization
7. **Set appropriate visibility levels** based on content sensitivity
8. **Test operations** with small changes before bulk updates
