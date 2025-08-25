# Data Directory Structure

This directory contains all data files for the Daemon Personal API system, organized by endpoint type.

## 🔒 **Privacy & Security**

⚠️ **The `data/private/` directory is ignored by git** to protect your personal information. Only the `examples/` subdirectory is tracked.

## 📂 **New Organized Structure**

```
data/
├── examples/           # Example data files (tracked in git)
│   ├── resume/         # Resume endpoint examples and docs
│   │   ├── resume_example.json
│   │   ├── README.md
│   │   ├── RESUME_MANAGEMENT.md
│   │   └── RESUME_IMPORT_SUMMARY.md
│   ├── skills/         # Skills endpoint examples and docs
│   │   ├── skills_example.json
│   │   └── README.md
│   ├── books/          # Favorite books endpoint examples and docs
│   │   ├── favorite_books_example.json
│   │   └── README.md
│   ├── hobbies/        # Hobbies endpoint examples and docs
│   ├── ideas/          # Ideas endpoint examples and docs
│   ├── problems/       # Problems endpoint examples and docs
│   └── looking_for/    # Looking for endpoint examples and docs
└── private/            # User-specific data (ignored by git)
    └── {username}/     # Each user has their own directory
        ├── resume/     # User's resume data
        ├── skills/     # User's skills data
        ├── books/      # User's favorite books
        ├── hobbies/    # User's hobbies
        ├── ideas/      # User's ideas
        ├── problems/   # User's problems
        └── looking_for/ # What the user is looking for
```

## 🚀 **Quick Commands**

```bash
# Check what data files are available
python -m app.cli data discover

# Import all discovered data files
python -m app.cli data import-all --replace

# Import specific endpoint
python -m app.cli data import ideas --file data/ideas.json --replace

# Check import status
python -m app.cli data status
```

## 📝 **Creating Data Files**

1. **Copy examples**: Start with files from `data/examples/`
2. **Rename**: Remove `_example` suffix (e.g., `ideas_example.json` → `ideas.json`)
3. **Edit**: Add your personal data
4. **Import**: Use CLI commands to import
5. **Update**: Edit files and re-import as needed

## 🔄 **Update Workflow**

1. Edit your data files in this directory
2. Run import command with `--replace` flag
3. Your API endpoints are immediately updated

## 📋 **Available Endpoints**

Based on the original Daemon project:

- **resume** - Professional resume and work history
- **about** - Basic personal information
- **ideas** - Ideas, thoughts, and concepts
- **skills** - Skills and areas of expertise
- **favorite_books** - Book recommendations and reviews
- **problems** - Problems you're working on or have solved
- **hobbies** - Hobbies and personal interests
- **looking_for** - Things you're currently seeking

## 🎯 **File Formats**

All data files should be valid JSON. See `examples/` directory for templates and proper formatting.

### Single Item Format:
```json
{
  "field1": "value1",
  "field2": "value2"
}
```

### Multiple Items Format:
```json
[
  {"field1": "value1", "field2": "value2"},
  {"field1": "value3", "field2": "value4"}
]
```

### Wrapper Format:
```json
{
  "metadata": {
    "updated_at": "2024-01-15",
    "version": "1.0"
  },
  "data": [
    {"field1": "value1", "field2": "value2"}
  ]
}
```

The system automatically handles all these formats!
