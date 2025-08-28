# Personal Story Data Examples

This directory contains examples for the "personal_story" endpoint, which stores personal narrative, biography, or personal story using the content/meta format.

## Purpose

The personal_story endpoint enables sharing deeper personal narratives beyond basic biographical information. It's designed for storytelling that provides context about your journey, experiences, and the events that shaped your perspective and approach to work and life.

## Schema

The personal_story endpoint uses the flexible content/meta schema:

```json
{
  "content": "string (required) - Markdown content with personal narrative",
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

The `personal_story_example.json` file contains sample data showing:

1. **Origin Story**: How you got started in your field or passion
2. **Defining Moments**: Key experiences that shaped your perspective
3. **Career Journey**: Professional evolution and turning points
4. **Core Beliefs**: Values and principles developed through experience
5. **Future Vision**: Where you're headed and what drives you

## Content Structure

The `content` field supports rich markdown formatting including:

- **Chronological Narrative**: Life and career progression over time
- **Defining Experiences**: Pivotal moments and their impact
- **Learning Journey**: How you discovered your interests and expertise
- **Challenges Overcome**: Obstacles faced and lessons learned
- **Mentors and Influences**: People who shaped your development
- **Philosophy Development**: How your values and approach evolved
- **Future Aspirations**: Current chapter and future direction

## Meta Field Descriptions

- **title**: Display title for the personal story
- **date**: When the story was written or last updated
- **tags**: Categories like ["personal", "biography", "journey", "technology", "growth"]
- **status**: Story status (active, draft, archived)
- **visibility**:
  - `public`: Visible to everyone
  - `unlisted`: Accessible via direct link only
  - `private`: Only visible to owner

## Usage

### Add Personal Story

```bash
curl -X POST "http://localhost:8000/api/v1/personal_story" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @personal_story_example.json
```

### Get Personal Story

```bash
# Get all personal story entries
curl "http://localhost:8000/api/v1/personal_story"

# In multi-user mode, get specific user's personal story
curl "http://localhost:8000/api/v1/personal_story/users/username"
```

## Privacy Levels

The personal_story endpoint supports privacy filtering:

- **business_card**: Very high-level professional journey only
- **professional**: Career-focused narrative with limited personal details
- **public_full**: Complete personal and professional story
- **ai_safe**: Safe for AI assistants (removes highly personal information)

## Best Practices

- Focus on experiences that shaped your professional or personal development
- Include both challenges and successes for authenticity
- Explain how past experiences inform your current approach
- Balance personal details with professional relevance
- Update periodically as your story evolves
- Consider your audience when choosing visibility levels
- Use storytelling techniques to make it engaging
- Connect past experiences to current values and future goals

**Examples:** `data/examples/personal_story/`
