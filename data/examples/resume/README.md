# Resume Data Examples

This directory contains examples and documentation for the resume endpoint.

## Files

- `resume_example.json` - Example resume data structure
- `RESUME_MANAGEMENT.md` - Detailed guide for managing resume data
- `RESUME_IMPORT_SUMMARY.md` - Summary of resume import functionality

## API Endpoints

**Single User Mode:**
- `GET /api/v1/resume` - Get resume data
- `POST /api/v1/resume` - Update resume data

**Multi-User Mode:**
- `GET /api/v1/resume/users/{username}` - Get specific user's resume
- `POST /api/v1/resume/users/{username}` - Update specific user's resume

## Privacy Levels

Resume data supports 4 privacy levels:
- `business_card` - Basic contact info only
- `professional` - Full professional info (no personal details)
- `public_full` - All non-sensitive information
- `ai_safe` - All information for AI assistant use

## Data Structure

```json
{
  "personal_info": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "555-123-4567",
    "location": "City, State"
  },
  "summary": "Professional summary...",
  "experience": [...],
  "education": [...],
  "skills": [...]
}
```

## File Locations

**Examples:** `data/examples/resume/`
**Private Data:** `data/private/{username}/resume/`

The system automatically looks for resume files in the user's private directory.
