# Goals Data Examples

This directory contains examples for the "goals" endpoint, which stores personal or professional goals with status and notes using the content/meta format.

## Purpose

The goals endpoint provides structured goal management for both personal and professional objectives. It enables tracking progress, maintaining accountability, and organizing goals with clear metrics and timelines.

## Schema

The goals endpoint uses the flexible content/meta schema:

```json
{
  "content": "string (required) - Markdown content with goal details",
  "meta": {
    "title": "string (optional) - Entry title",
    "date": "string (optional) - Date in YYYY-MM-DD format",
    "tags": "array (optional) - Array of tags for categorization",
    "status": "string (optional) - Entry status (draft, active, completed, etc.)",
    "visibility": "string (optional) - public, unlisted, or private"
  }
}
```

## Example Data

The `goals_example.json` file contains sample data showing:

1. **Professional Goals**: Career development, skill building, business objectives
2. **Personal Goals**: Health, learning, relationships, financial targets
3. **Structured Tracking**: Metrics, timelines, and accountability systems
4. **Progress Monitoring**: Review schedules and milestone tracking

## Content Structure

The `content` field supports rich markdown formatting including:

- **Goal Categories**: Professional, personal, financial, health, learning
- **Specific Targets**: Clear, measurable objectives with deadlines
- **Action Steps**: Concrete tasks and milestones
- **Progress Tracking**: Regular review and update mechanisms
- **Accountability**: Public commitments and progress sharing
- **Metrics**: Quantifiable success indicators

## Meta Field Descriptions

- **title**: Display title for the goals set
- **date**: When goals were set or last updated
- **tags**: Categories like ["goals", "planning", "personal-development", "professional-growth"]
- **status**: Goal status (active, paused, completed, revised)
- **visibility**:
  - `public`: Visible to everyone (good for accountability)
  - `unlisted`: Accessible via direct link only
  - `private`: Only visible to owner

## Usage

### Add Goal Data

```bash
curl -X POST "http://localhost:8000/api/v1/goals" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @goals_example.json
```

### Get Goal Data

```bash
# Get all goal entries
curl "http://localhost:8000/api/v1/goals"

# In multi-user mode, get specific user's goals
curl "http://localhost:8000/api/v1/goals/users/username"
```

## Privacy Levels

The goals endpoint supports privacy filtering:

- **business_card**: Professional goals only (high-level)
- **professional**: Work-related goals and some personal development
- **public_full**: All public goals and progress tracking
- **ai_safe**: Safe for AI assistants (removes sensitive personal targets)

## Best Practices

- Set SMART goals (Specific, Measurable, Achievable, Relevant, Time-bound)
- Balance professional and personal development objectives
- Include both outcome goals and process goals
- Establish regular review and update schedules
- Use public visibility for accountability when appropriate
- Track both quantitative metrics and qualitative progress
- Celebrate achievements and learn from missed targets
- Adjust goals based on changing circumstances and priorities

**Examples:** `data/examples/goals/`
