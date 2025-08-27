
# Problems Endpoint Documentation

## Overview
The `/problems` endpoint allows you to track, describe, and solve problems using flexible markdown content. This is ideal for documenting technical, business, or personal challenges, including investigation timelines, hypotheses, and solution frameworks.

## Key Features
- ✅ **Flexible Markdown Format**: Tables, lists, code blocks, blockquotes, and headings
- ✅ **HTML Entity Support**: Handles HTML entities in markdown content
- ✅ **Metadata Management**: Tags, titles, status, domain, priority, visibility, stakeholders
- ✅ **Complex Problem Tracking**: Multi-phase investigations, solution frameworks, and metrics
- ✅ **Privacy Controls**: Public, unlisted, and private visibility options

## API Endpoints

### POST /problems
Create a new problem entry.

**Request Body:**
```json
{
  "content": "### Problem: Reducing newsletter churn\n\n- **Observed**: 8% monthly churn rate\n- **Hypothesis**: Onboarding sequence lacks value framing\n- **Next steps**: Redesign welcome email series",
  "meta": {
    "title": "Newsletter Churn Problem",
    "tags": ["product", "retention", "email"],
    "status": "researching",
    "priority": "high",
    "domain": "marketing",
    "visibility": "private"
  }
}
```

### GET /problems
Retrieve all problems.

**Response:**
```json
{
  "problems": [
    {
      "id": 1,
      "content": "### Problem: ...",
      "meta": {...},
      "created_at": "2025-01-09T10:30:00Z",
      "updated_at": "2025-01-09T10:30:00Z"
    }
  ]
}
```

### PUT /problems/{id}
Update an existing problem entry.

### DELETE /problems/{id}
Delete a problem entry.

## Content Format Examples

### Basic Problem
```markdown
### Problem: Reducing newsletter churn

- **Observed**: 8% monthly churn rate
- **Hypothesis**: Onboarding sequence lacks value framing
- **Next steps**: Redesign welcome email series
```

### Technical Problem
```markdown
### Problem: API Performance Degradation

## Context
Our API response times have increased by **40%** over the last month.

## Symptoms
- Average response time: `250ms` → `350ms`
- 95th percentile: `500ms` → `800ms`
- Error rate: `0.1%` → `0.3%`

## Investigation Timeline
| Date | Action | Result |
|---|---|---|
| 2025-01-05 | Added monitoring | Identified DB bottleneck |
| 2025-01-06 | Query optimization | 10% improvement |
| 2025-01-07 | Index analysis | Found missing indexes |

## Code Analysis
```python
# Problematic query
users = session.query(User).filter(
    User.created_at > datetime.now() - timedelta(days=30)
).all()
```
```

### Solved Problem
```markdown
### Problem: Database Backup Failures (RESOLVED ✅)

#### Original Issue
Daily database backups were failing intermittently.

#### Solution Implemented
1. ✅ Updated retention policy to 30 days
2. ✅ Enabled backup compression
3. ✅ Added disk space monitoring alerts

#### Results
- Backup success rate: 100% for 14 days
- Disk usage reduced from 95% to 45%
```

## Metadata Options
- `title`: Short title for the problem
- `tags`: Array of tags (e.g., ["critical", "database"])
- `status`: Problem status (e.g., "solving", "solved")
- `domain`: Area affected (e.g., "engineering", "marketing")
- `priority`: Priority level (e.g., "high", "medium")
- `stakeholders`: List of involved parties
- `visibility`: "public", "unlisted", "private"

## Advanced Features
- **HTML Entity Handling**: Markdown content is double-unescaped for compatibility
- **Validation**: Content must be valid markdown; meta fields are optional but recommended
- **Error Handling**: Proper error messages for missing or invalid content

## Integration Examples
- **Incident Tracking**: Document technical outages and resolution steps
- **Business Challenges**: Track marketing, sales, or operational problems
- **Personal Development**: Record personal challenges and growth plans
- **Team Collaboration**: Share problems and solutions with stakeholders

## Best Practices
1. **Be Specific**: Clearly state the problem, context, and impact
2. **Use Markdown**: Structure content for readability and searchability
3. **Track Progress**: Update status and solution steps as you work
4. **Include Stakeholders**: List all involved parties for accountability
5. **Review Regularly**: Schedule reviews for ongoing problems

## Testing
Run the comprehensive test suite to validate functionality:
```bash
pytest tests/e2e/test_problems_e2e.py -v
```

The test suite covers:
- ✅ Basic CRUD operations
- ✅ Markdown formatting validation
- ✅ HTML entity handling
- ✅ Privacy controls
- ✅ Complex problem tracking scenarios
- ✅ Error handling and validation
