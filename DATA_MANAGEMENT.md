# Multi-User Data Management Guide

This document covers data management for the Daemon multi-user system, including user creation, data import/export, and privacy controls.

## 🔄 Adaptive System Overview

The system automatically adapts between single-user and multi-user modes:

- **Single User (≤1 user)**: Simple endpoints like `/api/v1/resume`
- **Multi-User (2+ users)**: User-specific endpoints like `/api/v1/resume/users/pmac`

## 🔒 **Security & Privacy First**

Your personal data is protected by a comprehensive `.gitignore` that ensures:
- **All files in `data/` directory are ignored by git** (except examples)
- **Resume files, personal files, private files are explicitly ignored**
- **Only template files in `data/examples/` are tracked in git**
- **User-specific directories in `data/private/` are completely ignored**

## 📁 **Supported File Patterns**

The system automatically discovers JSON files using these patterns:

- `{endpoint_name}.json` - Simple format (e.g., `ideas.json`)
- `{endpoint_name}_{suffix}.json` - With suffix (e.g., `ideas_personal.json`, `resume_pmac.json`)

## 🚀 **Quick Start**

### 1. **Discover Available Templates**
```bash
# See what example files are available
ls data/examples/
```

### 2. **Copy and Customize**
```bash
# Copy example file to your personal version
cp data/examples/ideas_example.json data/ideas.json
cp data/examples/skills_example.json data/skills.json

# Edit with your personal data
nano data/ideas.json
nano data/skills.json
```

### 3. **Check Discovery**
```bash
# See what files the system found
make discover-data

# Or use CLI directly
python -m app.cli data discover
```

### 4. **Check Import Status**
```bash
# See what needs importing
make data-status

# Shows file validation and database status
```

### 5. **Import All Data**
```bash
# Import everything at once
make import-all-data

# Or import specific endpoint
python -m app.cli data import ideas --file data/ideas.json --replace
```

## 📊 **Available Endpoints**

All based on Daniel Miessler's original Daemon project:

| Endpoint | File Pattern | Description |
|----------|--------------|-------------|
| `resume` | `resume*.json` | Professional resume and work history |
| `about` | `about*.json` | Basic personal information |
| `ideas` | `ideas*.json` | Ideas, thoughts, and concepts |
| `skills` | `skills*.json` | Skills and areas of expertise |
| `favorite_books` | `favorite_books*.json` | Book recommendations and reviews |
| `problems` | `problems*.json` | Problems you're working on or solved |
| `hobbies` | `hobbies*.json` | Hobbies and personal interests |
| `looking_for` | `looking_for*.json` | Things you're currently seeking |

## 🔧 **CLI Commands Reference**

### Data Discovery and Status
```bash
# Discover all data files
python -m app.cli data discover [--dir path/to/data]

# Check import status of all files
python -m app.cli data status [--dir path/to/data]
```

### Single File Import
```bash
# Import specific endpoint from file
python -m app.cli data import <endpoint> --file <path> [--replace] [--user username]

# Examples:
python -m app.cli data import ideas --file data/ideas.json --replace
python -m app.cli data import skills --file data/skills_work.json --user admin
```

### Bulk Import
```bash
# Import all discovered files
python -m app.cli data import-all [--dir path/to/data] [--replace] [--user username]

# Examples:
python -m app.cli data import-all --replace
python -m app.cli data import-all --dir /path/to/data --user admin
```

### Resume-Specific Commands
```bash
# Resume has specialized commands (legacy support)
python -m app.cli resume check [--file path/to/resume.json]
python -m app.cli resume import-file [--file path] [--replace] [--user username]
python -m app.cli resume show
```

## 📋 **File Format Examples**

### Single Item Format
```json
{
  "name": "Example Skill",
  "category": "Programming",
  "level": "expert",
  "description": "Detailed description..."
}
```

### Multiple Items Format
```json
[
  {
    "name": "First Skill",
    "category": "Programming",
    "level": "expert"
  },
  {
    "name": "Second Skill",
    "category": "Leadership",
    "level": "advanced"
  }
]
```

### Wrapper Format (with metadata)
```json
{
  "metadata": {
    "updated_at": "2024-01-15",
    "version": "2.0",
    "source": "personal"
  },
  "data": [
    {
      "name": "Skill Name",
      "category": "Category",
      "level": "expert"
    }
  ]
}
```

## 🔄 **Update Workflow**

1. **Edit your data files** in the `data/` directory
2. **Run import command** with `--replace` flag:
   ```bash
   make import-all-data
   # or
   python -m app.cli data import ideas --file data/ideas.json --replace
   ```
3. **Verify import** via API or CLI:
   ```bash
   curl http://localhost:8000/api/v1/ideas
   # or
   make data-status
   ```

## 🤖 **Automatic Development Import**

When you run the development server, it automatically:
1. **Scans the `data/` directory** for files
2. **Imports missing data** (if no existing data in database)
3. **Skips import** if data already exists
4. **Shows helpful status messages**

This means your personal data loads seamlessly during development!

## 🔍 **Validation**

All imported data is validated against:
- **Pydantic models** for known endpoints (strong typing)
- **Generic JSON validation** for custom endpoints
- **File format validation** (JSON parsing)
- **Schema compliance** where defined

Validation errors are reported clearly with specific line/field information.

## 🔐 **Security Features**

- **Git protection**: Entire `data/` directory ignored by git
- **CLI-only import**: File import only available via command line, not web API
- **Authentication required**: API write operations require authentication
- **Audit logging**: All imports logged with user attribution
- **Backup inclusion**: All imported data included in automatic backups

## 🚨 **Privacy Patterns**

The `.gitignore` specifically protects files matching these patterns:
- `data/*_personal.json`
- `data/*_private.json`
- `data/resume_*.json`
- `data/contacts_*.json`
- `data/financial_*.json`
- `data/health_*.json`
- `data/diary_*.json`
- `data/journal_*.json`
- `data/confidential_*.json`

## 🎯 **Best Practices**

1. **Start with examples**: Always copy from `data/examples/` directory
2. **Use descriptive suffixes**: `ideas_work.json`, `skills_personal.json`
3. **Keep files small**: Split large datasets into logical groups
4. **Update regularly**: Edit files and re-import as your data changes
5. **Backup important data**: Use the backup commands before major changes
6. **Validate before committing**: Check `make data-status` before sharing code

This system gives you complete control over your personal data while keeping it private and secure! 🔒✨
