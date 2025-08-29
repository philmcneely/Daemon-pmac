# GitHub Copilot Instructions

## 🚨 WARNING: MANDATORY Development Workflow Rules 🚨

**These rules are CRITICAL and must NEVER be violated. They are embedded at multiple levels to prevent forgetting.**

### 🔴 DEVELOPMENT WORKFLOW (MANDATORY)

#### Test-First Development
- **ALWAYS** update tests when changing functionality
- **ALWAYS** run tests and ensure they pass before proceeding
- **NEVER** move to next task until all tests pass and docs are updated

#### Documentation Updates
- **ALWAYS** update `API_REQUIREMENTS.md` when changing API behavior
- **ALWAYS** update `E2E_TEST_CASES_GIVEN_WHEN_THEN.md` for new test scenarios
- **ALWAYS** update OpenAPI documentation for endpoint changes

#### Quality Gates (ALL MUST PASS)
- ✅ All existing tests must pass
- ✅ New tests must pass
- ✅ Documentation must be updated and accurate
- ✅ OpenAPI schema must be current
- ✅ No temporary files in project root

### 🔴 COMMAND OUTPUT HANDLING (MANDATORY)

#### GitHub CLI & Curl Commands
- **ALWAYS** pipe GitHub CLI (`gh`) commands to files in `gh_temp/` directory first, then read the file
- **ALWAYS** pipe `curl` commands to files in `gh_temp/` directory first, then read the file
- **NEVER** try to read CLI output directly from terminal

#### Backup Investigation Methods
- **ALWAYS** use multiple investigation approaches when debugging:
  1. **Search existing code**: Use `grep_search`, `semantic_search`, `file_search` to understand current patterns
  2. **Check route registration**: Verify endpoints are properly registered in routers and main.py
  3. **Test existing endpoints**: Use curl to test what already works before creating new
  4. **Examine logs**: Check server logs for errors, warnings, or routing issues
  5. **Validate assumptions**: Test your understanding of existing functionality
- **NEVER** assume functionality doesn't exist - always verify through multiple search methods

#### Examples:

##### ✅ CORRECT Pattern for GitHub CLI:
```bash
gh api repos/owner/repo/pulls > gh_temp/pulls.json 2>&1
cat gh_temp/pulls.json
```

##### ✅ CORRECT Pattern for Curl:
```bash
curl -s https://api.github.com/repos/owner/repo > gh_temp/repo.json 2>&1
cat gh_temp/repo.json
```

##### ❌ INCORRECT Pattern:
```bash
gh api repos/owner/repo/pulls  # Cannot read this output directly
curl -s https://api.github.com/repos/owner/repo  # Cannot read this output directly
```

### 🔴 FILE MANAGEMENT (MANDATORY)

#### Clean Repository Practices
- **NEVER** create extraneous files for one-offs in the root directory
- **NEVER** create duplicate files and leave them around
- **ALWAYS** clean up temporary files after use
- **ALWAYS** use `gh_temp/` directory for temporary files (it's gitignored)

#### Code Investigation and Analysis
- **ALWAYS** investigate existing codebase before adding new functionality:
  1. Search for similar patterns: `grep_search`, `semantic_search`
  2. Check existing endpoints: Look at router files and test with curl
  3. Examine existing models and schemas
  4. Look for utility functions that might already solve the problem
- **ALWAYS** prefer extending/using existing functionality over creating new
- **ALWAYS** follow established patterns and conventions in the codebase

### 🔴 PROBLEM RESOLUTION (MANDATORY)

#### Root Cause Analysis
- **NEVER** suppress warnings or add workarounds - ALWAYS fix the root cause
- **ALWAYS** examine application code first to understand how to perform actions correctly

#### Check Existing Before Creating New
- **ALWAYS** check what endpoints, functions, or features already exist before creating new ones
- **NEVER** create duplicate functionality without understanding why existing solutions don't work
- **ALWAYS** examine existing patterns and follow them for consistency
- **ALWAYS** search codebase for similar functionality before implementing from scratch
- **ALWAYS** use `grep_search`, `semantic_search`, or `file_search` to find existing implementations

### 🔴 WORK COMPLETION (MANDATORY)

#### Summary Protocol
- **ALWAYS** commit changes before summarizing what you've done

#### File Naming Convention
**IMPORTANT**: Always use the `gh_temp/` directory for temporary files:
- `gh_temp/ci_status.txt` - CI pipeline status
- `gh_temp/pr_info.json` - Pull request information
- `gh_temp/repo_settings.json` - Repository settings
- `gh_temp/branch_protection.json` - Branch protection rules

## GitHub CLI Output Handling

**CRITICAL** Whenever you run a GitHub CLI (`gh`) command in the terminal, pipe the output to a file that you can read from. Always use the `gh_temp/` directory for temporary files (it's gitignored). Make sure to clean these files regularly so that it doesn't grow the directory too big. There is a bug in the current version of Copilot that causes it to not read the output of commands correctly. This workaround allows you to read the output from the temporary file instead. You MUST redirect output to a file first, then read the file.

### ✅ CORRECT Pattern:
```bash
gh api repos/owner/repo/pulls > gh_temp/pulls.json 2>&1
cat gh_temp/pulls.json
```

### ❌ INCORRECT Pattern:
```bash
gh api repos/owner/repo/pulls  # Cannot read this output directly
```

### Examples:

#### Repository Information:
```bash
gh repo view > gh_temp/repo_info.txt 2>&1
cat gh_temp/repo_info.txt
```

#### Pull Request Status:
```bash
gh pr list --state=all > gh_temp/pr_list.txt 2>&1
cat gh_temp/pr_list.txt
```

#### CI/CD Status:
```bash
gh run list > gh_temp/ci_runs.txt 2>&1
cat gh_temp/ci_runs.txt
```

#### API Calls:
```bash
gh api repos/philmcneely/Daemon-pmac/branches/main/protection > gh_temp/protection.json 2>&1
cat gh_temp/protection.json
```

## Why This is Required

The terminal integration cannot capture GitHub CLI output directly. Always use the redirect-and-read pattern to ensure you can access the command results.

## File Naming Convention

**IMPORTANT**: Always use the `gh_temp/` directory for temporary files (it's gitignored):

- `gh_temp/ci_status.txt` - CI pipeline status
- `gh_temp/pr_info.json` - Pull request information
- `gh_temp/repo_settings.json` - Repository settings
- `gh_temp/branch_protection.json` - Branch protection rules

The `gh_temp/` directory is automatically ignored by git and can be safely cleaned up periodically. Never put temporary GitHub CLI output files in the root directory.

---

## 🔴 GENERAL DEVELOPMENT DIRECTIVES (SECONDARY TO USER RULES)

### Code Quality Standards
- **Be consistent:** Follow the existing coding style and patterns found in the project
- **Provide detailed docstrings:** For all new functions and classes, include comprehensive docstrings following Google-style format
- **Use type hints:** Annotate function parameters and return values with Python type hints wherever possible
- **Use clear, actionable language:** Specific verbs, avoid ambiguity
- **Favor positive instructions:** Describe what to do, not what to avoid

### File Header Requirements
- **ALWAYS add detailed headers** to all Python files (.py) with:
  - Module description
  - Author information
  - Creation/modification dates
  - Dependencies
  - Usage examples (when applicable)
- **SKIP headers** for Markdown files (.md) - keep them clean

---

## 🔴 PYTHON STYLE AND CONVENTIONS

### Code Formatting
- **PEP 8:** Strict adherence to PEP 8 style guide
- **Line length:** Follow project's line length settings
- **Naming conventions:** `snake_case` for functions and variables, `PascalCase` for classes
- **Imports:** Order: standard library, third-party, local application imports
- **F-strings:** Prefer f-strings for string formatting
- **List comprehensions:** Use for concise list creation
- **Error handling:** Use `try...except` blocks, avoid bare `except:` statements

---

## 🔴 PROJECT-SPECIFIC TECHNOLOGY STACK

### Framework & Architecture
- **Backend Framework:** `FastAPI` (version 0.104.1+)
- **Database:** `SQLite` with `aiosqlite` (async support) via `SQLAlchemy 2.0+` ORM
- **Authentication:** JWT tokens using `python-jose[cryptography]`
- **Dependency Management:** `pip` with `requirements.txt` (NOT Poetry)
- **Testing Framework:** `pytest` with `pytest-asyncio`
- **Code Quality:** `black`, `isort`, `flake8`, `mypy`, `pre-commit`

### Database Patterns
- **All database interactions** must use SQLAlchemy models and sessions
- **NO raw SQL queries** - use SQLAlchemy ORM exclusively
- **Async sessions** with `aiosqlite` for database operations
- **Import pattern:** `from app.database import get_db, Base, engine`

### API Development Patterns
- **Route definitions:** Use FastAPI router patterns with `@router.get/post/put/delete`
- **Dependency injection:** Use `Depends(get_db)` for database sessions
- **Request/Response models:** Use Pydantic models for validation
- **Async functions:** All route handlers should be `async def`

---

## 🔴 TESTING REQUIREMENTS

### Test Structure
- **Framework:** `pytest` with `pytest-asyncio` for async testing
- **Directory structure:** Follow existing `tests/unit/` and `tests/e2e/` patterns
- **Naming convention:** `test_` prefix for test functions and files
- **Mock external dependencies** when appropriate
- **Database testing:** Use test database fixtures from `tests/conftest.py`

### Test Coverage
- **Unit tests:** All new functions and classes
- **E2E tests:** All new API endpoints for both single-user and multi-user scenarios
- **Integration tests:** Database operations and external API calls

---

## 🔴 SPECIFIC TASK EXAMPLES

### Task: Generate a new FastAPI route
```python
@router.get("/api/v1/items/{item_id}")
async def get_item(
    item_id: int,
    db: AsyncSession = Depends(get_db)
) -> ItemResponse:
    """Fetch a single item from the database."""
    # Implementation using SQLAlchemy async session
```

### Task: Write a pytest test
```python
async def test_create_item(db_session: AsyncSession):
    """Test the create_item function in crud.py."""
    # Test implementation with async database session
```

### Task: Database model creation
```python
class Item(Base):
    """Item model for storing item data."""
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
```

---

## 🔴 FILE HEADER TEMPLATE

### For Python Files (.py)
Use this header template for all Python files:

```python
"""
Module: [module_name]
Description: [Brief description of module purpose]

Author: [Your name]
Created: [YYYY-MM-DD]
Modified: [YYYY-MM-DD]

Dependencies:
- fastapi: [version] - Web framework
- sqlalchemy: [version] - Database ORM
- [other key dependencies]

Usage:
    [Brief usage example if applicable]

Notes:
    [Any important notes about the module]
"""
```

### For Markdown Files (.md)
- **NO headers** - keep Markdown files clean and focused on content
- Start directly with the main heading or content

---

## 🔴 TECHNOLOGY STACK CORRECTIONS

### What This Project Actually Uses:
- ✅ **Database:** SQLite with aiosqlite (NOT PostgreSQL)
- ✅ **Dependency Management:** pip with requirements.txt (NOT Poetry)
- ✅ **Async Database:** SQLAlchemy 2.0+ with aiosqlite async driver
- ✅ **Testing:** pytest with pytest-asyncio for async test support
- ✅ **Authentication:** JWT with python-jose[cryptography]

### Common Mistakes to Avoid:
- ❌ Don't reference PostgreSQL - this project uses SQLite
- ❌ Don't use Poetry commands - use pip and requirements.txt
- ❌ Don't forget async/await patterns for database operations
- ❌ Don't add headers to .md files - keep them clean

---

## 🔴 INVESTIGATION METHODOLOGIES (MANDATORY)

### Before Creating New Functionality

**CRITICAL**: Always investigate existing solutions before implementing new features.

#### 1. Search Existing Codebase
```bash
# Search for similar functionality
grep_search: "endpoint.*users" OR "get.*users" OR "list.*users"
semantic_search: "user listing functionality"
file_search: "**/routers/*.py" to examine all route definitions
```

#### 2. Test Existing Endpoints
```bash
# Always pipe to gh_temp/ directory
curl -X GET "http://localhost:8007/api/v1/system/info" > gh_temp/system_info.json 2>&1
cat gh_temp/system_info.json

# Check what endpoints already exist
python -c "from app.main import app; [print(f'{route.methods} {route.path}') for route in app.routes if hasattr(route, 'path')]"
```

#### 3. Examine Router Registration
- Check `app/main.py` for router inclusion
- Verify route ordering (specific routes before general ones)
- Look at existing router files: `app/routers/api.py`, `app/routers/auth.py`, `app/routers/admin.py`

#### 4. Validate Route Conflicts
- FastAPI matches routes in order of definition
- Specific paths (e.g., `/users`) must come before parameterized paths (e.g., `/{endpoint_name}`)
- Use router debugging to identify conflicts

#### 5. Check Authentication Requirements
- Understand difference between public and authenticated endpoints
- Verify existing endpoints' authentication requirements
- Don't create public versions of secure endpoints

### Real-World Example: User Listing Endpoint

**Scenario**: Frontend needs to list users for multi-user mode detection.

#### ❌ Wrong Approach (What I Did Initially):
1. Assumed no user listing endpoint existed
2. Created new `/api/v1/users` endpoint
3. Added new route without checking existing functionality
4. Created security concerns with public user data access

#### ✅ Correct Approach (What Should Have Been Done):
1. **Search existing**: `grep_search: "users.*endpoint" AND "@router.*users"`
2. **Found existing endpoints**: `/admin/users`, `/auth/users`, `/api/v1/system/info`
3. **Test existing**: `curl /api/v1/system/info` → Already returns user list + mode
4. **Use existing**: Update frontend to use `/api/v1/system/info`
5. **Result**: No new code needed, proper security maintained

#### Key Lessons:
- **System info endpoint already provided user list and mode detection**
- **Admin endpoints exist for authenticated user management**
- **Public endpoint patterns were already established**
- **Investigation time: 5 minutes vs. implementation time: 30 minutes**

#### Investigation Commands That Would Have Saved Time:
```bash
# This would have immediately shown existing endpoints
python -c "from app.main import app; [print(f'{route.methods} {route.path}') for route in app.routes if 'users' in route.path]"

# This would have shown system/info returns user data
curl -X GET "http://localhost:8007/api/v1/system/info" > gh_temp/system_info.json 2>&1
cat gh_temp/system_info.json
```

### Investigation Checklist

Before creating any new endpoint or functionality:

- [ ] **Search existing code** for similar patterns
- [ ] **Test existing endpoints** with curl (pipe to gh_temp/)
- [ ] **Check route registration** and ordering
- [ ] **Verify authentication requirements** match use case
- [ ] **Examine existing schemas and models**
- [ ] **Look for utility functions** that solve similar problems
- [ ] **Test the existing solution** to understand why it doesn't meet needs
