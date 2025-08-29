# GitHub Copilot Instructions

## 🚨 CRITICAL DATA PROTECTION RULES 🚨

**NEVER DELETE FILES FROM `data/private/` DIRECTORY**
- **NEVER** run commands that could delete files in `data/private/`
- **NEVER** use `rm`, `mv`, or any destructive commands on `data/private/`
- **ALWAYS** treat `data/private/` as read-only unless explicitly instructed to add files
- This directory contains user data that is not tracked in git for privacy reasons

## 🔴 MANDATORY Development Workflow Rules

### Test-First Development
- **ALWAYS** update tests when changing functionality
- **ALWAYS** run tests and ensure they pass before proceeding
- **NEVER** move to next task until all tests pass and docs are updated

### Documentation Updates
- **ALWAYS** update `API_REQUIREMENTS.md` when changing API behavior
- **ALWAYS** update `E2E_TEST_CASES_GIVEN_WHEN_THEN.md` for new test scenarios
- **ALWAYS** update OpenAPI documentation for endpoint changes

### Command Output Handling
- **ALWAYS** pipe GitHub CLI (`gh`) commands to files in `gh_temp/` directory first, then read the file
- **ALWAYS** pipe `curl` commands to files in `gh_temp/` directory first, then read the file
- **NEVER** try to read CLI output directly from terminal

### File Management
- **NEVER** create extraneous files for one-offs in the root directory
- **NEVER** create duplicate files and leave them around
- **ALWAYS** clean up temporary files after use
- **ALWAYS** use `gh_temp/` directory for temporary files (it's gitignored)

### Problem Resolution
- **NEVER** suppress warnings or add workarounds - ALWAYS fix the root cause
- **ALWAYS** examine application code first to understand how to perform actions correctly

### Check Existing Before Creating New
- **ALWAYS** check what endpoints, functions, or features already exist before creating new ones
- **NEVER** create duplicate functionality without understanding why existing solutions don't work
- **ALWAYS** search codebase for similar functionality before implementing from scratch
- **ALWAYS** use `grep_search`, `semantic_search`, or `file_search` to find existing implementations

### Work Completion
- **ALWAYS** commit changes before summarizing what you've done

## Technology Stack

### Framework & Architecture
- **Backend Framework:** FastAPI (version 0.104.1+)
- **Database:** SQLite with aiosqlite (async support) via SQLAlchemy 2.0+ ORM
- **Authentication:** JWT tokens using python-jose[cryptography]
- **Dependency Management:** pip with requirements.txt (NOT Poetry)
- **Testing Framework:** pytest with pytest-asyncio
- **Code Quality:** black, isort, flake8, mypy, pre-commit

### Database Patterns
- **All database interactions** must use SQLAlchemy models and sessions
- **NO raw SQL queries** - use SQLAlchemy ORM exclusively
- **Async sessions** with aiosqlite for database operations
- **Import pattern:** `from app.database import get_db, Base, engine`

### API Development Patterns
- **Route definitions:** Use FastAPI router patterns with `@router.get/post/put/delete`
- **Dependency injection:** Use `Depends(get_db)` for database sessions
- **Request/Response models:** Use Pydantic models for validation
- **Async functions:** All route handlers should be `async def`

## Investigation Methodology

### Before Creating New Functionality
**CRITICAL**: Always investigate existing solutions before implementing new features.

1. **Search existing code**: Use `grep_search`, `semantic_search`, `file_search` to understand current patterns
2. **Check route registration**: Verify endpoints are properly registered in routers and main.py
3. **Test existing endpoints**: Use curl to test what already works before creating new
4. **Examine logs**: Check server logs for errors, warnings, or routing issues
5. **Validate assumptions**: Test your understanding of existing functionality

### Command Examples

#### ✅ CORRECT Pattern for Curl:
```bash
curl -X GET "http://localhost:8007/api/v1/system/info" > gh_temp/system_info.json 2>&1
cat gh_temp/system_info.json
```

#### ❌ INCORRECT Pattern:
```bash
curl -X GET "http://localhost:8007/api/v1/system/info"  # Cannot read this output directly
```

## Quality Gates (ALL MUST PASS)
- ✅ All existing tests must pass
- ✅ New tests must pass
- ✅ Documentation must be updated and accurate
- ✅ OpenAPI schema must be current
- ✅ No temporary files in project root
- ✅ No files deleted from `data/private/`
