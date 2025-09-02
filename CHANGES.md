# Changes Log

## Version 0.3.1 (2025-09-02)

### 🔧 Performance & Development Experience
- **VS Code Performance Optimization**
  - Reduced CPU usage from 87% to ~82% through optimized settings
  - Enhanced Python analysis configuration with better indexing limits
  - Disabled unnecessary TypeScript auto-imports and features
  - Optimized file watchers and search exclusions
  - Added comprehensive development guidelines in local instructions

### 🧪 Test Suite Improvements
- **Fixed MCP Privacy Filtering Tests**
  - Corrected test expectations to preserve user intentional content
  - Phone numbers in user content now properly preserved (not filtered)
  - Privacy filtering focused on structured data fields, not user expression
  - All 21 MCP tests now passing with proper behavior validation

### 🔨 CI/CD Pipeline Fixes
- **Fixed Coverage Calculation**
  - Resolved "0% coverage" issue in CI workflows
  - Added missing step outputs for coverage percentage
  - Fixed invalid GitHub Actions syntax in coverage threshold checks
  - Coverage now properly calculated at 72.9% (above 40% threshold)

### 🗃️ Repository Management
- **Development File Optimization**
  - Removed COPILOT_INSTRUCTIONS.md from git tracking (local-only development file)
  - Enhanced .gitignore patterns for better development workflow
  - Cleaned up file tracking for development vs. team-shared files

### 🛡️ Privacy Philosophy Alignment
- **Content Preservation Principle**
  - Users can intentionally include sensitive information in their content
  - Privacy filtering applies to structured resume-style fields only
  - User agency and content control maintained in MCP responses
  - Clear distinction between automated filtering vs. user choice

### 📊 Testing & Coverage
- **Comprehensive Test Coverage**: 72.9% overall (538 passing tests)
- **All MCP Protocol Tests**: 21/21 passing with correct privacy behavior
- **E2E Test Coverage**: Full privacy filtering scenarios validated
- **CI Pipeline**: All checks passing with proper coverage reporting

## Version 0.3.0 (2025-08-31)

### 🔄 Database Migration System
- **Added comprehensive database migration system**
  - New `scripts/version_tracker.py` for database version tracking and schema validation
  - New `scripts/migrate_comprehensive.py` for automated migrations with safety checks
  - Pre-migration safety checks including disk space and schema integrity validation
  - Automatic backup creation before migrations with rollback capability
  - Support for all migration paths: v0.1.x → v0.2.x → v0.3.x
  - Command-line interface with status checking and forced migration options

### 📚 Enhanced Documentation
- **Comprehensive migration documentation** in `docs/DATABASE_MIGRATIONS.md`
  - Docker container-to-container upgrade procedures
  - Bare metal upgrade procedures with step-by-step instructions
  - Version-specific migration matrix with breaking changes documentation
  - Rollback procedures and troubleshooting guides
- **Migration tools documentation** in `scripts/README.md`
  - Detailed usage examples and feature descriptions
  - Safety features and backup procedures
  - Migration workflow for new installations and upgrades

### 🛡️ Safety Features
- **Automatic database backups** before all migrations
- **Schema integrity validation** before and after migrations
- **Disk space verification** (requires 3x database size for safety)
- **Rollback capability** on migration failure with clear restore instructions

## Version 0.3.0 (2025-08-31)

### 🧹 Repository Cleanup & Naming Convention
- **Unified naming convention** across the entire project
  - Renamed CLI command from `daemon-pmac` to `daemon`
  - Updated Docker container naming from `daemon-pmac-daemon-*` to clean `daemon-*` prefix
  - Removed "pmac" references from all documentation and configuration files
  - Updated service files and paths from `/opt/daemon-pmac` to `/opt/daemon`
  - Renamed workspace and service files to remove "pmac" suffix

### 🔒 Privacy & Security Improvements
- **Removed private development files** from public repository
  - Added Copilot instruction files to `.gitignore`
  - Removed implementation blueprint documentation from tracking
  - Cleaned up internal development guidance files
  - Enhanced repository privacy while maintaining functionality

### 🐛 CI/CD Pipeline Fixes
- **Fixed Docker Compose service naming** in CI workflows
  - Updated CI tests to use correct service names (`api` instead of `daemon-api`)
  - Resolved Docker profile testing failures
  - Ensured all CI steps pass after naming convention changes
  - Maintained comprehensive test coverage across all deployment scenarios

### 🏗️ Infrastructure Improvements
- **Enhanced Docker project structure**
  - Added project name configuration in `docker-compose.yml`
  - Improved container naming consistency
  - Streamlined service definitions and dependencies

## Version 0.2.2 (2025-08-30)

### 🎨 Content Formatting & Documentation
- **Added comprehensive Markdown Style Guide** (`docs/MARKDOWN_STYLE_GUIDE.md`)
  - Standardized content block formatting with H4 headers
  - Multiple bullet point indentation techniques (4-space, HTML, non-breaking space)
  - Best practices for code blocks, tables, and links
  - Good vs poor formatting examples

### 🚀 Deployment Improvements
- **Fixed port inconsistencies** throughout documentation
  - Updated all examples from port 8000 to 8007 (actual default)
  - Clarified Docker vs bare metal deployment options
- **Enhanced Docker configuration**
  - Made ports configurable via environment variables
  - Improved docker-compose.yml with flexible port settings
  - Updated Dockerfile to use PORT environment variable
- **Improved deployment documentation**
  - Added comprehensive Docker setup instructions
  - Clarified environment configuration options
  - Better distinction between development and production modes

### 🧪 Testing Stability
- **Fixed all E2E test failures** (13/13 tests now passing)
  - Enhanced content validation to handle empty states gracefully
  - Updated CI database setup to create admin user
  - Improved test reliability across different environments

### 📋 CI/CD Pipeline
- **Green CI status** across all workflows
  - Frontend E2E tests: 100% pass rate
  - All quality gates: passing
  - Ready for production deployment

---

# Changes Made: Resume Endpoint and Attribution Updates

## 🆕 New Resume Endpoint

### Database Schema (app/database.py)
- Added comprehensive `resume` endpoint definition to `create_default_endpoints()`
- Schema includes:
  - **Basic Info**: name (required), title (required), summary
  - **Contact**: email, phone, location, website, linkedin, github
  - **Experience**: Array of work history with company, position, dates, achievements, technologies
  - **Education**: Array of educational background with institution, degree, field, dates, GPA, honors
  - **Skills**: Object with technical, languages, certifications, soft_skills arrays
  - **Projects**: Array of projects with name, description, technologies, URLs
  - **Additional**: awards, volunteer work, updated_at date

### Data Model (app/schemas.py)
- Added `ResumeData` Pydantic model for validation
- Includes proper typing with Optional fields and nested structures
- Added to `ENDPOINT_MODELS` mapping for automatic validation

### Testing (tests/)
- Added `sample_resume_data` fixture in `conftest.py` with comprehensive test data
- Added three new tests in `test_api.py`:
  - `test_resume_endpoint_specific_validation()` - Full resume data test
  - `test_resume_minimal_data()` - Test with only required fields
  - `test_resume_missing_required_fields()` - Validation error test

## 📝 Attribution Updates

### README.md Updates
- **Header section**: Clear identification as "example implementation" of Daniel Miessler's Daemon project
- **Attribution note**: Prominent note explaining relationship to original project
- **Core Endpoints**: Updated to reference "Based on Original Daemon Project"
- **Added resume endpoint** to the endpoints list
- **New Attribution section**: Comprehensive section covering:
  - Link to original Daemon project and Daniel Miessler's profile
  - Explanation of what this implementation provides beyond the original concept
  - Key differences from the original (database, auth, deployment, etc.)
  - Related projects in Daniel's ecosystem (Substrate, Fabric, TELOS)
  - Clear statement about independent development and respect for original vision

### PROJECT_STRUCTURE.md Updates
- **Header**: Added attribution banner
- **Endpoints section**: Added resume endpoint and attribution note
- **API Examples**: Added resume endpoint examples with comprehensive JSON structure

## 🎯 Key Features of Resume Endpoint

The resume endpoint supports:

1. **Professional Information**: Name, title, professional summary
2. **Contact Details**: Multiple contact methods and social profiles
3. **Work Experience**: Detailed work history with achievements and technologies
4. **Education**: Academic background with honors and GPA
5. **Skills Categorization**: Technical skills, languages, certifications, soft skills
6. **Projects**: Portfolio projects with descriptions and links
7. **Recognition**: Awards and volunteer work
8. **Versioning**: Updated_at field for tracking resume versions

## 🔗 API Usage Examples

```bash
# Get resume data
GET /api/v1/resume

# Add/update resume (authenticated)
POST /api/v1/resume
{
  "name": "John Doe",
  "title": "Software Engineer",
  "summary": "Experienced developer...",
  "contact": {
    "email": "john@example.com",
    "github": "https://github.com/johndoe"
  },
  "experience": [...],
  "education": [...],
  "skills": {...}
}
```

## ✅ Validation & Testing

- **Type Safety**: Full Pydantic validation for all nested structures
- **Required Fields**: Name and title are required, all other fields optional
- **Test Coverage**: Comprehensive tests covering valid data, minimal data, and validation errors
- **Schema Compliance**: Follows same patterns as other Daemon endpoints

This implementation now properly honors Daniel Miessler's original vision while providing a production-ready framework that developers can actually deploy and use immediately.
