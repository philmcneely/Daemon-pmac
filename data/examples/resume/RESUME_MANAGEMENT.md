# Resume Management

The Daemon-pmac framework includes optional resume management functionality that allows you to easily import and manage your professional resume data.

## Quick Start

### 1. Check if Resume File Exists
```bash
# Check default location (data/resume_pmac.json)
python -m app.cli resume check

# Or check a specific file
python -m app.cli resume check --file /path/to/your/resume.json
```

### 2. Import Resume Data
```bash
# Import from default location
python -m app.cli resume import-file

# Import from specific file, replacing existing data
python -m app.cli resume import-file --file /path/to/resume.json --replace

# Associate with specific user
python -m app.cli resume import-file --user admin --replace
```

### 3. View Current Resume
```bash
# Show current resume data from database
python -m app.cli resume show

# Or via API
curl http://localhost:8000/api/v1/resume
```

## Makefile Shortcuts

For convenience, use these Makefile commands:

```bash
make check-resume    # Check resume file status
make import-resume   # Import resume (with replace)
make show-resume     # Show current resume data
```

## File Format

The resume file should be a JSON file following this structure:

```json
{
  "name": "Your Name",
  "title": "Your Professional Title",
  "summary": "Professional summary...",
  "contact": {
    "email": "your@email.com",
    "phone": "+1 (555) 123-4567",
    "location": "City, State",
    "linkedin": "https://linkedin.com/in/yourprofile"
  },
  "experience": [
    {
      "company": "Company Name",
      "position": "Job Title",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM or Present",
      "description": "Job description",
      "achievements": ["Achievement 1", "Achievement 2"],
      "technologies": ["Tech 1", "Tech 2"]
    }
  ],
  "education": [
    {
      "institution": "University Name",
      "degree": "Degree Type",
      "field": "Field of Study",
      "start_date": "YYYY",
      "end_date": "YYYY",
      "gpa": 3.8,
      "honors": ["Honor 1", "Honor 2"]
    }
  ],
  "skills": {
    "technical": ["Skill 1", "Skill 2"],
    "languages": ["Language 1", "Language 2"],
    "certifications": ["Cert 1", "Cert 2"],
    "soft_skills": ["Skill 1", "Skill 2"]
  },
  "projects": [
    {
      "name": "Project Name",
      "description": "Project description",
      "technologies": ["Tech 1", "Tech 2"],
      "url": "https://project-url.com",
      "github": "https://github.com/user/project"
    }
  ],
  "volunteer": [
    {
      "organization": "Organization Name",
      "role": "Role",
      "start_date": "YYYY-MM",
      "end_date": "YYYY-MM",
      "description": "Description of work"
    }
  ],
  "awards": ["Award 1", "Award 2"],
  "updated_at": "YYYY-MM-DD"
}
```

## Automatic Import in Development

When running the development server (`python dev.py` or `make dev`), the system will automatically:

1. Check for a resume file at `data/resume_pmac.json`
2. Import it automatically if no resume data exists in the database
3. Skip import if resume data already exists

This makes it seamless to get your resume data loaded during development without any manual steps.

## API Access

Once imported, your resume data is available via the REST API:

```bash
# Get resume data (public endpoint)
GET /api/v1/resume

# Add new resume entry (requires authentication)
POST /api/v1/resume

# Update existing resume entry (requires authentication)
PUT /api/v1/resume/{id}

# Delete resume entry (requires authentication)
DELETE /api/v1/resume/{id}
```

## Security

- Resume data can be marked as public or private via the endpoint configuration
- API access requires authentication for write operations
- File-based import is only available via CLI (not exposed through web API)
- All changes are logged in the audit trail

## Updating Your Resume

1. **Edit the JSON file**: Update `data/resume_pmac.json` with your latest information
2. **Re-import**: Run `make import-resume` or `python -m app.cli resume import-file --replace`
3. **Verify**: Check with `make show-resume` or visit the API endpoint

The `--replace` flag ensures that existing resume data is updated rather than creating duplicates.

## Integration with Other Systems

The resume endpoint supports:

- **MCP (Model Context Protocol)**: AI systems can query your resume data
- **Export formats**: JSON and CSV export available
- **Backup inclusion**: Resume data is included in automatic backups
- **Version tracking**: All changes are timestamped and audited

This provides a professional, API-first approach to managing and sharing your resume data.
