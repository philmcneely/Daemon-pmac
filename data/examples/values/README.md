# Values Data Examples

This directory contains examples for the "values" endpoint, which stores core values and guiding principles using the content/meta format.

## Purpose

The values endpoint documents your fundamental beliefs and guiding principles that inform decision-making in both personal and professional contexts. It provides insight into what drives your choices and approach to work and relationships.

## Schema

The values endpoint uses the flexible content/meta schema:

```json
{
  "content": "string (required) - Markdown content with values and principles",
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

The `values_example.json` file contains sample data showing:

1. **Core Values**: Fundamental principles like curiosity, integrity, impact
2. **Practical Application**: How values translate into daily actions and decisions
3. **Real Examples**: Specific situations demonstrating values in practice
4. **Personal Philosophy**: How different values work together as a system

## Content Structure

The `content` field supports rich markdown formatting including:

- **Value Statements**: Clear articulation of each core principle
- **Practical Implementation**: How values guide daily decisions and actions
- **Concrete Examples**: Real situations where values influenced choices
- **Value Interactions**: How different principles work together or create tension
- **Evolution**: How your values have developed or changed over time
- **Professional Application**: How values inform work decisions and relationships

## Meta Field Descriptions

- **title**: Display title for the values document
- **date**: When values were documented or last updated
- **tags**: Categories like ["values", "principles", "personal-philosophy", "character", "ethics"]
- **status**: Document status (active, evolving, under review)
- **visibility**:
  - `public`: Visible to everyone
  - `unlisted`: Accessible via direct link only
  - `private`: Only visible to owner

## Usage

### Add Values Data

```bash
curl -X POST "http://localhost:8000/api/v1/values" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @values_example.json
```

### Get Values Data

```bash
# Get all values entries
curl "http://localhost:8000/api/v1/values"

# In multi-user mode, get specific user's values
curl "http://localhost:8000/api/v1/values/users/username"
```

## Privacy Levels

The values endpoint supports privacy filtering:

- **business_card**: Professional values only (work-relevant principles)
- **professional**: Work-related values and some personal principles
- **public_full**: Complete values and personal philosophy
- **ai_safe**: Safe for AI assistants (removes highly personal beliefs)

## Best Practices

- Be authentic and honest about what truly drives your decisions
- Include specific examples of how values translate into action
- Explain the reasoning behind each value and why it matters to you
- Address how you handle conflicts between different values
- Update regularly as your values evolve with experience
- Consider how your values align with or differ from organizational values
- Use clear, concrete language rather than abstract concepts
- Show how values inform both professional and personal choices

**Examples:** `data/examples/values/`
