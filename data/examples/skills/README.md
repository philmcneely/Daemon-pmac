# Skills Endpoint Examples

This directory contains examples for the `/skills` endpoint, which supports free-text skill descriptions, experience notes, and learning goals using flexible markdown content.

## Endpoint: `/api/v1/skills`

The skills endpoint supports both modern flexible markdown format and legacy structured format for backward compatibility.

## Flexible Markdown Format (Recommended)

The new format allows rich markdown content with optional metadata:

```json
{
  "content": "### Python (Intermediate)\n\n- 5 years of practical use\n- Focus: data processing, web backends\n- Current learning: async programming",
  "meta": {
    "title": "Python",
    "category": "Programming Languages",
    "level": "Intermediate",
    "tags": ["python", "backend", "apis"],
    "visibility": "public"
  }
}
```

### Rich Markdown Examples

Skills can include detailed formatting, lists, achievements, and goals:

```markdown
### Docker & Kubernetes

Container orchestration expertise with production experience:

#### Docker
- **Development**: Multi-stage builds, compose workflows
- **Production**: Optimized images, security scanning
- **Networking**: Custom networks, service discovery

#### Kubernetes
- **Deployments**: Rolling updates, blue-green strategies
- **Scaling**: HPA, VPA, cluster autoscaling
- **Monitoring**: Prometheus, Grafana, alerting

#### Recent Achievements
- ✅ Reduced deployment time by 75%
- ✅ Improved system reliability to 99.9% uptime
- ✅ Mentored 5 team members on K8s best practices

> *"Containerization transformed our development workflow"* — Team Lead

**Next Focus Areas:**
- Service mesh implementation (Istio)
- Advanced security policies
- Cost optimization strategies
```

## Legacy Structured Format

For backward compatibility, the traditional structured format is still supported:

```json
{
  "name": "Python",
  "category": "Programming Languages",
  "level": "expert",
  "years_experience": 15,
  "description": "Advanced Python development including FastAPI, Django, automation frameworks, and testing tools"
}
```

## API Operations

### Create Skill
```bash
POST /api/v1/skills
Content-Type: application/json

{
  "content": "### React (Advanced)\n\nBuilt 10+ production apps...",
  "meta": {
    "title": "React",
    "category": "Frontend",
    "level": "Advanced",
    "tags": ["react", "frontend", "javascript"]
  }
}
```

### List Skills
```bash
GET /api/v1/skills
```

### Get Single Skill
```bash
GET /api/v1/skills/{id}
```

### Update Skill
```bash
PUT /api/v1/skills/{id}
Content-Type: application/json

{
  "content": "### React (Expert)\n\nUpdated experience...",
  "meta": {
    "level": "Expert",
    "tags": ["react", "frontend", "javascript", "architecture"]
  }
}
```

### Delete Skill
```bash
DELETE /api/v1/skills/{id}
```

## Metadata Fields

### Core Fields
- `title`: Skill name or title
- `category`: Skill category (e.g., "Programming Languages", "DevOps", "Management")
- `level`: Proficiency level (e.g., "Beginner", "Intermediate", "Advanced", "Expert")
- `tags`: Array of skill-related tags
- `visibility`: "public", "unlisted", or "private" (defaults to "public")

### Legacy Fields (for backward compatibility)
- `name`: Skill name (required in legacy format)
- `years_experience`: Number of years of experience
- `description`: Text description of the skill

## Use Cases

### Professional Skills Portfolio
Document technical skills, experience levels, and learning goals for career development.

### Learning Progress Tracking
Track skill development over time with status updates and learning milestones.

### Team Skills Matrix
Share expertise areas within teams for better project staffing and knowledge sharing.

### Mentoring & Teaching
Document teaching experience and areas where you can mentor others.

## Content Suggestions

### Skill Categories
- **Programming Languages**: Python, JavaScript, Go, Rust, etc.
- **Frameworks & Libraries**: React, Django, FastAPI, etc.
- **DevOps & Infrastructure**: Docker, Kubernetes, AWS, etc.
- **Data & Analytics**: SQL, pandas, machine learning, etc.
- **Management & Leadership**: Team leadership, project management, etc.
- **Design & UX**: UI/UX design, prototyping, user research, etc.

### Content Structure Ideas
- Current proficiency level and experience timeline
- Specific frameworks, tools, or methodologies within the skill
- Recent projects or achievements using the skill
- Learning goals and areas for improvement
- Teaching or mentoring experience in the skill area
- Certifications or formal training completed

## Privacy Controls

Skills default to `public` visibility. Use `private` for sensitive internal skills or `unlisted` for skills you want to share via direct link only.

```json
{
  "meta": {
    "visibility": "private"  // "public", "unlisted", or "private"
  }
}
```
