# Projects Endpoint Documentation

The `/projects` endpoint provides a flexible way to store and manage project information using pure markdown content. Unlike other endpoints with structured schemas, projects support completely flexible formatting allowing users to organize their project information however makes sense to them.

## Key Features

- **Pure Markdown Content**: No rigid schema - organize projects however you prefer
- **Flexible Structure**: Support for any project format (technical specs, volunteer work, personal projects, etc.)
- **Rich Formatting**: Full markdown support including code blocks, tables, links, and media
- **Individual Management**: Add, edit, replace, or delete projects independently
- **Privacy Controls**: Automatic privacy filtering based on user settings
- **Multi-User Support**: User-specific project collections in multi-user mode

## API Endpoints

### Single User Mode
```bash
GET    /api/v1/projects              # List all projects
POST   /api/v1/projects              # Create new project
PUT    /api/v1/projects/{id}         # Update/replace project
DELETE /api/v1/projects/{id}         # Delete project
POST   /api/v1/projects/bulk         # Create multiple projects
```

### Multi-User Mode
```bash
GET    /api/v1/projects/users/{username}    # Get user's projects
POST   /api/v1/projects/users/{username}    # Create project for user
PUT    /api/v1/projects/{id}/users/{username}  # Update user's project
DELETE /api/v1/projects/{id}/users/{username}  # Delete user's project
```

## Data Structure

Projects use a simple, flexible structure with only one required field:

```json
{
  "content": "# Your Project Title\n\nAny markdown content here..."
}
```

The `content` field contains pure markdown text that can be structured however you prefer.

## Usage Examples

### Technical Project

```json
{
  "content": "# Daemon Personal API\n\n## Overview\nA FastAPI-based personal data management system with markdown support and dynamic endpoints.\n\n## Key Features\n- **Dynamic Endpoints**: Automatically generated endpoints based on data schemas\n- **Markdown Support**: Rich content formatting for flexible data presentation\n- **Multi-User Support**: Handles both single and multi-user scenarios\n- **Secure Authentication**: JWT-based authentication with role-based access\n\n## Technology Stack\n- FastAPI\n- SQLAlchemy\n- PostgreSQL/SQLite\n- pytest for testing\n- Docker for deployment\n\n## Current Status\nActive development with comprehensive test coverage and CI/CD pipeline.\n\n## Next Steps\n- [ ] Add real-time notifications\n- [ ] Implement data export features\n- [ ] Add advanced search capabilities\n- [ ] Create mobile app integration\n\n*Repository: [github.com/user/daemon-pmac](https://github.com/user/daemon-pmac)*"
}
```

### Volunteer Work

```json
{
  "content": "### Volunteer Projects\n\n#### Organization: Local Animal Shelter\n\n*   **Project 1: \"Pawsitive Adoptions\" Event Coordinator**\n    *   Organized and executed a successful adoption event, resulting in 15 animal adoptions over a single weekend.\n    *   Managed a team of 10 volunteers, delegating tasks such as animal handling, visitor registration, and information dissemination.\n    *   Coordinated with local businesses for sponsorships and donations, securing over $500 in supplies and monetary contributions.\n\n*   **Project 2: Shelter Renovation Assistant**\n    *   Assisted in the renovation of animal enclosures, including painting, minor repairs, and installation of new bedding.\n    *   Contributed to creating a cleaner and more comfortable environment for over 50 animals.\n    *   Worked collaboratively with a team of 8 volunteers, ensuring tasks were completed efficiently and safely.\n\n#### Organization: Parent-Teacher Association (PTA)\n\n*   **Project: \"School Beautification Day\" Lead Organizer**\n    *   Led the planning and execution of a school-wide beautification day, involving over 70 parent and student volunteers.\n    *   Coordinated landscaping efforts, including planting flowers, weeding gardens, and general campus cleanup.\n    *   Secured donations of plants, tools, and refreshments from local nurseries and businesses, totaling over $300 in value."
}
```

### Personal Projects

```json
{
  "content": "## Personal Projects\n\n### Home Automation System\n**Status:** Active | **Priority:** Medium\n\n**Overview:**\nBuilt a comprehensive smart home system managing 15+ IoT devices with energy monitoring and intelligent automation.\n\n**Achievements:**\n- 🔋 18% reduction in monthly electricity costs\n- 🏠 12 custom automation scenarios\n- 📱 React Native mobile app with geofencing\n- 📊 Real-time analytics dashboard\n\n**Technical Details:**\n- **Hub:** Raspberry Pi 4 running Home Assistant\n- **Devices:** 15 smart switches, 8 bulbs, 3 thermostats\n- **Protocols:** Zigbee, Z-Wave, WiFi integration\n\n**Demo:** [demo.smarthome.local](https://demo.smarthome.local)\n\n---\n\n### Backyard Storage Shed Construction\n\n*   Designed and constructed a 10x12 foot storage shed from scratch\n*   Managed all aspects: material procurement, budgeting, tool operation, safety\n*   Completed within 3-week timeframe and under budget\n*   Provided valuable outdoor storage space for tools and equipment"
}
```

## API Usage

### Creating a Project

```bash
curl -X POST \"http://localhost:8000/api/v1/projects\" \\\n  -H \"Authorization: Bearer YOUR_TOKEN\" \\\n  -H \"Content-Type: application/json\" \\\n  -d '{\n    \"content\": \"# New Project\\n\\nProject description here...\"\n  }'
```

### Updating a Project

```bash
curl -X PUT \"http://localhost:8000/api/v1/projects/123\" \\\n  -H \"Authorization: Bearer YOUR_TOKEN\" \\\n  -H \"Content-Type: application/json\" \\\n  -d '{\n    \"content\": \"# Updated Project\\n\\nCompletely new content...\"\n  }'
```

### Searching Projects

```bash
# Search for projects containing specific terms\ncurl \"http://localhost:8000/api/v1/projects?search=Python\"\n\n# Pagination\ncurl \"http://localhost:8000/api/v1/projects?limit=5&offset=10\"\n\n# Privacy filtering\ncurl \"http://localhost:8000/api/v1/projects?privacy_level=public_full\"\n```

### Bulk Creation

```bash
curl -X POST \"http://localhost:8000/api/v1/projects/bulk\" \\\n  -H \"Authorization: Bearer YOUR_TOKEN\" \\\n  -H \"Content-Type: application/json\" \\\n  -d '[\n    {\"content\": \"# Project 1\\n\\nFirst project...\"},\n    {\"content\": \"# Project 2\\n\\nSecond project...\"}\n  ]'
```

## Advanced Markdown Features

The projects endpoint supports all standard markdown features:

### Code Blocks
```python
def create_project(content: str):\n    return {\"content\": content}\n```

### Tables
| Feature | Status | Priority |\n|---------|--------|----------|\n| Authentication | ✅ Complete | High |\n| API Endpoints | 🔄 In Progress | Medium |\n| Documentation | ❌ Pending | Low |

### Links and Media
- [External Links](https://example.com)\n- ![Images](https://example.com/image.png)\n- Internal references and cross-links

### Special Characters
- Emoji support: 🚀 🎯 💡\n- Mathematical expressions: E = mc²\n- Unicode symbols: ∀x∈ℝ, x² ≥ 0

## Privacy and Security

Projects respect the same privacy controls as other endpoints:

- **business_card**: Project titles only\n- **professional**: Work-related projects, sanitized personal info\n- **public_full**: All projects with sensitive data removed\n- **ai_safe**: Full content with automatic data sanitization

## File Import

You can import projects from JSON files in the `data/examples/projects/` directory:

```bash\n# Import projects from file\npython -m app.cli import-data projects\n```

The file should contain an array of project objects with \"content\" fields.\n\n## Best Practices\n\n1. **Consistent Structure**: While flexible, maintaining some consistency helps with readability\n2. **Rich Content**: Use markdown features to make projects visually appealing\n3. **Regular Updates**: Keep project status and achievements current\n4. **Privacy Awareness**: Consider what information should be public vs. private\n5. **Searchable Content**: Include relevant keywords for easy discovery\n\n## Examples in This Repository\n\nCheck out `data/examples/projects/projects_example.json` for real examples of different project formatting styles.\n
