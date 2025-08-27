# Skills Matrix Endpoint Documentation

## Overview
The `/skills_matrix` endpoint allows you to store and retrieve comprehensive skills assessment data in markdown format. Perfect for maintaining detailed technical and soft skills evaluations, 360-degree feedback, and professional development tracking.

## Key Features
- ✅ **Flexible Markdown Format** - Support for tables, lists, code blocks, and rich formatting
- ✅ **HTML Entity Support** - Automatically handles HTML entities in content
- ✅ **Metadata Management** - Tags, titles, status tracking, and visibility controls
- ✅ **360° Feedback Integration** - Structure for peer, manager, and self-assessments
- ✅ **Development Planning** - Track goals, achievements, and growth areas

## API Endpoints

### POST /skills_matrix
Store new skills matrix data.

**Request Body:**
```json
{
  "content": "### Skills Matrix\n\n| Skill | Level | Notes |\n|---|---:|---|\n| React | Advanced | Built 10+ apps |",
  "meta": {
    "title": "Technical Skills Matrix",
    "tags": ["skills", "matrix", "technical"],
    "visibility": "public"
  }
}
```

### GET /skills_matrix
Retrieve all skills matrix entries.

**Response:**
```json
{
  "skills_matrix": [
    {
      "id": 1,
      "content": "### Skills Matrix...",
      "meta": {...},
      "created_at": "2025-01-09T10:30:00Z",
      "updated_at": "2025-01-09T10:30:00Z"
    }
  ]
}
```

### PUT /skills_matrix/{id}
Update existing skills matrix entry.

### DELETE /skills_matrix/{id}
Delete skills matrix entry.

## Content Format Examples

### Basic Skills Matrix
```markdown
### Skills Matrix

| Skill | Level | Notes |
|---|---:|---|
| React | Advanced | Built 10+ apps |
| Docker | Intermediate | Deploy pipelines |
| Python | Expert | 8+ years experience |

#### Recent Achievements
- Led React migration for 3 legacy applications
- Optimized Docker builds reducing deploy time by 60%
- Mentored 5 developers in Python best practices
```

### Comprehensive Assessment
```markdown
### Comprehensive Skills Assessment 2025

## Technical Skills

### Programming Languages
| Language | Proficiency | Years | Key Projects |
|---|---|---|---|
| **Python** | ⭐⭐⭐⭐⭐ | 8 | ML pipelines, APIs |
| **JavaScript** | ⭐⭐⭐⭐ | 6 | Frontend, Node.js |

### Frameworks & Tools
> **Note**: Ratings based on production experience

#### Frontend
- **React** `Advanced` - Component architecture, hooks
- **Vue.js** `Intermediate` - SPA development

## Soft Skills Assessment

| Skill | Self-Rating | 360° Feedback | Development Goal |
|---|---|---|---|
| Leadership | 8/10 | 8.5/10 | Executive presence |
| Communication | 9/10 | 9/10 | Technical writing |

## Endorsements

### Technical Leadership
> *"Outstanding technical vision and ability to translate complex requirements."*
> — Sarah Chen, Engineering Director
```

### Leadership Matrix
```markdown
### Leadership Skills Matrix

| Skill | Self-Assessment | Team Feedback | Manager Feedback |
|---|---|---|---|
| **Strategic Thinking** | Good | Very Good | Excellent |
| **Team Development** | Excellent | Outstanding | Outstanding |

#### Development Areas

1. **Strategic Thinking**
   - *Focus*: Long-term vision and industry trends
   - *Action*: Quarterly strategy reviews
   - *Timeline*: Next 6 months

#### 360° Feedback Highlights

> *"Exceptional at creating psychological safety within the team."*
> — Direct Report
```

## Metadata Options

### Standard Fields
- `title`: Human-readable title for the skills matrix
- `tags`: Array of tags for categorization (e.g., ["technical", "leadership", "2025"])
- `visibility`: Control access ("public", "unlisted", "private")
- `status`: Track currency ("current", "archived", "draft")

### Use Case Examples
```json
{
  "title": "Q4 2025 Skills Assessment",
  "tags": ["quarterly", "comprehensive", "technical", "leadership"],
  "status": "current",
  "visibility": "unlisted"
}
```

## Advanced Features

### HTML Entity Handling
The endpoint automatically handles HTML entities in markdown content:
```json
{
  "content": "Skills &amp; Competencies\n\n&lt;details&gt;\n&lt;summary&gt;Technical Skills&lt;/summary&gt;"
}
```

### Validation
- Content must be valid markdown
- Meta fields are optional but recommended
- Automatic HTML entity unescaping
- Proper error handling with descriptive messages

## Integration Examples

### Career Development
Track skills progression over time with quarterly assessments.

### Performance Reviews
Integrate 360-degree feedback into structured skills evaluation.

### Team Planning
Assess team capabilities and identify skill gaps for hiring.

### Personal Branding
Maintain current skills matrix for professional profiles and portfolios.

## Best Practices

1. **Regular Updates**: Update quarterly or after major projects
2. **Specific Examples**: Include concrete achievements and metrics
3. **Balanced Assessment**: Include both technical and soft skills
4. **Growth Planning**: Document development goals and timelines
5. **Feedback Integration**: Incorporate peer and manager feedback
6. **Version Control**: Use tags and titles to track different versions

## Testing
Run the comprehensive test suite to validate functionality:
```bash
pytest tests/e2e/test_skills_matrix_e2e.py -v
```

The test suite covers:
- ✅ Basic CRUD operations
- ✅ Markdown formatting validation
- ✅ HTML entity handling
- ✅ Privacy controls
- ✅ Complex formatting scenarios
- ✅ Error handling and validation
