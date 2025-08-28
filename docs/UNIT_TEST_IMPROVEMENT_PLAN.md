# Unit Test Consolidation Plan - EXECUTION READY

## Overview
Consolidate test files to have exa### Phase 1: Backup and Verify Current State

```bash
# Ensure working tests pass before starting
python -m pytest tests/unit/test_admin.py tests/unit/test_admin_working.py -v
python -m pytest tests/unit/test_data_loader.py -v
python -m pytest tests/unit/test_multi_user_import.py -v
python -m pytest tests/unit/test_resume_loader.py -v
python -m pytest tests/unit/test_security.py -v

# Create backup branch
git checkout -b test-consolidation-backup
git add -A && git commit -m "Backup before test consolidation"
git checkout main
```

### Phase 2: Consolidate Working Files

#### Step 1: Admin Tests (Priority 1)
```bash
# Verify both files work
python -m pytest tests/unit/test_admin.py tests/unit/test_admin_working.py -v

# Manual merge: Combine test_admin.py + test_admin_working.py content
# Keep all tests from both files, resolve any conflicts manually
# Result: Single test_admin.py with ~22 tests

# After manual merge, test the result
python -m pytest tests/unit/test_admin.py -v

# Delete duplicates
rm tests/unit/test_admin_proper.py          # identical to original
rm tests/unit/test_admin_comprehensive.py  # subset
rm tests/unit/test_admin_unit.py           # minimal
rm tests/unit/test_admin_working.py        # after merging
rm tests/unit/test_admin_consolidated.py   # broken version
```

#### Step 2: Data Loader Tests
```bash
# Test current file
python -m pytest tests/unit/test_data_loader.py -v

# Check what unique tests exist in comprehensive version
python -m pytest tests/unit/test_data_loader_comprehensive.py --collect-only

# Manual merge: Add any missing tests from comprehensive to main file
# Keep test_data_loader.py as base, add unique tests if they work

# After manual merge, test
python -m pytest tests/unit/test_data_loader.py -v

# Delete duplicates
rm tests/unit/test_data_loader_comprehensive.py
rm tests/unit/test_data_loader_simple.py
```

#### Step 3: Multi User Import Tests
```bash
# Test current working file
python -m pytest tests/unit/test_multi_user_import.py -v

# Check other versions for unique working tests
python -m pytest tests/unit/test_multi_user_import_unit.py --collect-only

# Manual merge: Add any unique working tests to main file
# Keep test_multi_user_import.py as base

# After manual merge, test
python -m pytest tests/unit/test_multi_user_import.py -v

# Delete duplicates
rm tests/unit/test_multi_user_import_comprehensive.py
rm tests/unit/test_multi_user_import_simple.py
rm tests/unit/test_multi_user_import_unit.py
rm tests/unit/test_multi_user_import_consolidated.py  # broken version
```

#### Step 4: Resume Loader Tests
```bash
# Keep main file, remove simple version
python -m pytest tests/unit/test_resume_loader.py -v
rm tests/unit/test_resume_loader_simple.py
```

#### Step 5: Security Tests
```bash
# Test main file
python -m pytest tests/unit/test_security.py -v

# Manual merge: Add content from additional file
# Merge test_security_additional.py into test_security.py

# After manual merge, test
python -m pytest tests/unit/test_security.py -v

# Delete additional file
rm tests/unit/test_security_additional.py
```

#### Step 6: Utils Tests (Create New)
```bash
# Create new consolidated utils test file
# Manual merge: Combine test_utils_comprehensive.py + test_utils_security.py
# Create: tests/unit/test_utils.py

# After manual merge, test
python -m pytest tests/unit/test_utils.py -v

# Delete original files
rm tests/unit/test_utils_comprehensive.py
rm tests/unit/test_utils_security.py
```

### Phase 3: Handle Misnamed and Orphaned Files

```bash
# Rename misnamed file
mv tests/unit/test_api_router_security.py tests/unit/test_api.py
python -m pytest tests/unit/test_api.py -v

# Remove orphaned file
rm tests/unit/test_projects_unit.py
```

### Phase 4: Create Missing Test Files

```bash
# Create skeleton test files for missing modules
touch tests/unit/test_auth.py
touch tests/unit/test_config.py
touch tests/unit/test_database.py
touch tests/unit/test_main.py
touch tests/unit/test_privacy.py
touch tests/unit/test_schemas.py
touch tests/unit/test_auth_router.py
touch tests/unit/test_mcp.py

# Add basic test structure to each new file
# (Will be implemented in separate phase)
```

### Phase 5: Final Validation

```bash
# Verify exactly 16 test files exist (1 per app module)
ls tests/unit/test_*.py | wc -l  # Should output: 16

# Verify all tests pass
python -m pytest tests/unit/ -v

# Check for coverage gaps
python -m pytest tests/unit/ --cov=app --cov-report=html

# Final file list should be:
# test_admin.py, test_api.py, test_auth.py, test_auth_router.py
# test_cli.py, test_config.py, test_data_loader.py, test_database.py
# test_main.py, test_mcp.py, test_multi_user_import.py, test_privacy.py
# test_resume_loader.py, test_schemas.py, test_security.py, test_utils.py
```

## Manual Merge Guidelines

### For Each Consolidation:
1. **Start with the working base file**
2. **Identify unique tests** in duplicate files
3. **Copy unique test classes/methods** (don't duplicate)
4. **Preserve all imports** needed for merged tests
5. **Test after each merge** to ensure nothing breaks
6. **Keep test names descriptive** and avoid conflicts

### Test Naming Convention:
- Use descriptive class names: `TestAdminAuthentication`, `TestAdminAuthorization`
- Use descriptive method names: `test_list_users_unauthorized`, `test_create_api_key_success`
- Group related tests in classes for organization

## Success Criteria

✅ **Exactly 16 test files** (1:1 mapping with app modules)
✅ **All existing tests continue to pass**
✅ **No duplicate test files**
✅ **Proper naming convention** (`test_<module>.py`)
✅ **No orphaned test files**
✅ **Test coverage maintained or improved**le per app module**. Use working original files as the base and manually merge content from duplicates.

## Target Structure (1:1 Mapping)
```
App Module                    → Target Test File
app/auth.py                  → tests/unit/test_auth.py (NEW)
app/cli.py                   → tests/unit/test_cli.py (EXISTS ✅)
app/config.py                → tests/unit/test_config.py (NEW)
app/data_loader.py           → tests/unit/test_data_loader.py (CONSOLIDATE)
app/database.py              → tests/unit/test_database.py (NEW)
app/main.py                  → tests/unit/test_main.py (NEW)
app/multi_user_import.py     → tests/unit/test_multi_user_import.py (CONSOLIDATE)
app/privacy.py               → tests/unit/test_privacy.py (NEW)
app/resume_loader.py         → tests/unit/test_resume_loader.py (CONSOLIDATE)
app/schemas.py               → tests/unit/test_schemas.py (NEW)
app/security.py              → tests/unit/test_security.py (CONSOLIDATE)
app/utils.py                 → tests/unit/test_utils.py (NEW)
app/routers/admin.py         → tests/unit/test_admin.py (CONSOLIDATE)
app/routers/api.py           → tests/unit/test_api.py (RENAME)
app/routers/auth.py          → tests/unit/test_auth_router.py (NEW)
app/routers/mcp.py           → tests/unit/test_mcp.py (NEW)
```

## Current State Analysis

## Current State Analysis

### Files to Consolidate

#### 🔴 Admin Tests (6 duplicate files)
**Target:** `tests/unit/test_admin.py`
- ✅ `test_admin.py` (211 lines, 14 tests) - WORKING, unauthorized + validation + errors
- ✅ `test_admin_working.py` (345 lines, 8 tests) - WORKING, success scenarios with mocking
- ❌ `test_admin_proper.py` (211 lines) - IDENTICAL to test_admin.py
- ❌ `test_admin_comprehensive.py` (72 lines, 6 tests) - subset of test_admin.py
- ❌ `test_admin_unit.py` (69 lines) - minimal tests
- ❌ `test_admin_consolidated.py` (35KB) - BROKEN, has errors

**Action:** Merge `test_admin.py` + `test_admin_working.py`, delete the rest

#### 🔴 Data Loader Tests (3 duplicate files)
**Target:** `tests/unit/test_data_loader.py`
- ✅ `test_data_loader.py` (368 lines, ~20 tests) - WORKING base file
- ❌ `test_data_loader_comprehensive.py` (445 lines, ~30 tests) - more comprehensive but untested
- ❌ `test_data_loader_simple.py` (106 lines, ~10 tests) - basic subset

**Action:** Keep `test_data_loader.py`, merge unique tests from comprehensive, delete others

#### 🔴 Multi User Import Tests (5 duplicate files)
**Target:** `tests/unit/test_multi_user_import.py`
- ✅ `test_multi_user_import.py` (93 lines) - WORKING basic version
- ❌ `test_multi_user_import_comprehensive.py` (504 lines) - extensive but untested
- ❌ `test_multi_user_import_simple.py` (93 lines) - likely identical to basic
- ❌ `test_multi_user_import_unit.py` (197 lines) - unit-focused
- ❌ `test_multi_user_import_consolidated.py` (23KB) - BROKEN, has errors

**Action:** Keep `test_multi_user_import.py`, merge unique working tests, delete others

#### 🔴 Resume Loader Tests (2 duplicate files)
**Target:** `tests/unit/test_resume_loader.py`
- ✅ `test_resume_loader.py` (360 lines) - WORKING main file
- ❌ `test_resume_loader_simple.py` (116 lines) - basic subset

**Action:** Keep `test_resume_loader.py`, delete simple version

#### 🔴 Security Tests (2 duplicate files)
**Target:** `tests/unit/test_security.py`
- ✅ `test_security.py` - WORKING main file
- ❌ `test_security_additional.py` - additional tests

**Action:** Merge additional into main, delete additional

#### 🔴 Utils Tests (2 duplicate files)
**Target:** `tests/unit/test_utils.py` (NEW)
- ❌ `test_utils_comprehensive.py` - comprehensive version
- ❌ `test_utils_security.py` - security-focused version

**Action:** Create new `test_utils.py` merging both, delete originals

### Files to Handle

#### 🔴 Misnamed Files
- `test_api_router_security.py` → rename to `test_api.py`

#### 🔴 Orphaned Files
- `test_projects_unit.py` → DELETE (no corresponding app/projects.py)

#### 🔴 Missing Files (8 new files needed)
- `test_auth.py`, `test_config.py`, `test_database.py`, `test_main.py`
- `test_privacy.py`, `test_schemas.py`, `test_auth_router.py`, `test_mcp.py`

## EXECUTION PLAN

### Phase 1: Backup and Verify Current State#### 🔴 Priority 1: Admin Router Tests
**Analysis of test coverage:**
- `test_admin.py` (211 lines): unauthorized + validation + error scenarios
- `test_admin_working.py` (344 lines): success scenarios with proper mocking
- `test_admin_proper.py`: IDENTICAL to `test_admin.py` - safe to delete
- `test_admin_comprehensive.py`: subset of `test_admin.py` - safe to delete
- `test_admin_unit.py`: minimal tests - safe to delete

**Action Items:**
1. **Merge `test_admin_working.py` into `test_admin.py`:**
   - Add the 8 success scenario tests from `test_admin_working.py`
   - Preserve all existing 14 tests from `test_admin.py`
   - Result: Single file with ~22 comprehensive tests
2. **Delete identical/subset files:**
   - [ ] Delete `test_admin_proper.py` (identical)
   - [ ] Delete `test_admin_comprehensive.py` (subset)
   - [ ] Delete `test_admin_unit.py` (minimal)
   - [ ] Delete `test_admin_working.py` (after merging)

#### 🔴 Priority 2: Data Loader Tests
**Analysis of test coverage:**
- `test_data_loader_comprehensive.py` (445 lines, ~30 tests): Most complete
- `test_data_loader.py` (368 lines, ~20 tests): Main file but less comprehensive
- `test_data_loader_simple.py` (106 lines, ~10 tests): Basic subset

**Action Items:**
1. **Use `test_data_loader_comprehensive.py` as the base**
2. **Rename it to `test_data_loader.py`**
3. **Delete the other versions:**
   - [ ] Delete original `test_data_loader.py`
   - [ ] Delete `test_data_loader_simple.py`

#### 🔴 Priority 3: Multi User Import Tests
**Analysis of test coverage:**
- `test_multi_user_import_comprehensive.py` (504 lines): Most complete
- `test_multi_user_import_unit.py` (197 lines): Unit-focused
- `test_multi_user_import.py` (93 lines): Basic
- `test_multi_user_import_simple.py` (93 lines): Appears identical to basic

**Action Items:**
1. **Use `test_multi_user_import_comprehensive.py` as the base**
2. **Merge any unique tests from `test_multi_user_import_unit.py`**
3. **Rename result to `test_multi_user_import.py`**
4. **Delete the other versions:**
   - [ ] Delete original `test_multi_user_import.py`
   - [ ] Delete `test_multi_user_import_simple.py`
   - [ ] Delete `test_multi_user_import_unit.py`

#### 🔴 Priority 4: Resume Loader Tests
**Action Items:**
1. **Keep `test_resume_loader.py` (360 lines) as the main file**
2. **Delete `test_resume_loader_simple.py` (subset)**

#### 🔴 Priority 5: Security Tests
**Action Items:**
1. **Merge `test_security_additional.py` into `test_security.py`**
2. **Delete `test_security_additional.py`**

#### 🔴 Priority 6: Utils Tests
**Action Items:**
1. **Merge `test_utils_comprehensive.py` and `test_utils_security.py`**
2. **Create final `test_utils.py`**
3. **Delete both original files**

### Phase 2: Handle Misnamed/Orphaned Files

#### 🔴 Rename Misnamed Files
1. **`test_api_router_security.py` → `test_api.py`**
   - This file tests `app/routers/api.py` functionality
   - Rename to follow proper naming convention

#### 🔴 Remove Orphaned Files
1. **Delete `test_projects_unit.py`**
   - No corresponding `app/projects.py` file exists
   - This appears to be leftover from refactoring

### Phase 3: Create Missing Test Files

#### 🔴 Required New Test Files (1:1 mapping with app modules)

**Core App Modules:**
- [ ] `tests/unit/test_auth.py` (for `app/auth.py`)
- [ ] `tests/unit/test_config.py` (for `app/config.py`)
- [ ] `tests/unit/test_database.py` (for `app/database.py`)
- [ ] `tests/unit/test_main.py` (for `app/main.py`)
- [ ] `tests/unit/test_privacy.py` (for `app/privacy.py`)
- [ ] `tests/unit/test_schemas.py` (for `app/schemas.py`)

**Router Modules:**
- [ ] `tests/unit/test_auth_router.py` (for `app/routers/auth.py`)
- [ ] `tests/unit/test_mcp.py` (for `app/routers/mcp.py`)

**Already Exist (Keep):**
- ✅ `tests/unit/test_cli.py` (for `app/cli.py`)

## Final Target Structure

After consolidation, we should have exactly these test files:

```
tests/unit/
├── test_admin.py          # app/routers/admin.py (consolidated)
├── test_api.py            # app/routers/api.py (renamed)
├── test_auth.py           # app/auth.py (new)
├── test_auth_router.py    # app/routers/auth.py (new)
├── test_cli.py            # app/cli.py (existing)
├── test_config.py         # app/config.py (new)
├── test_data_loader.py    # app/data_loader.py (consolidated)
├── test_database.py       # app/database.py (new)
├── test_main.py           # app/main.py (new)
├── test_mcp.py            # app/routers/mcp.py (new)
├── test_multi_user_import.py  # app/multi_user_import.py (consolidated)
├── test_privacy.py        # app/privacy.py (new)
├── test_resume_loader.py  # app/resume_loader.py (existing/consolidated)
├── test_schemas.py        # app/schemas.py (new)
├── test_security.py       # app/security.py (consolidated)
└── test_utils.py          # app/utils.py (consolidated)
```

## Implementation Steps

### Step 1: Backup and Validate Current State
```bash
# Ensure all tests pass before starting
python -m pytest tests/unit/ -v

# Create backup branch
git checkout -b test-consolidation-backup
git add -A && git commit -m "Backup before test consolidation"
git checkout main
```

### Step 2: Phase 1 - Remove Duplicates (Preserve Behavior)

**Admin Tests:**
```bash
# Test current state
python -m pytest tests/unit/test_admin*.py -v

# Manually merge test_admin_working.py success tests into test_admin.py
# Then delete duplicates
rm tests/unit/test_admin_proper.py      # identical
rm tests/unit/test_admin_comprehensive.py  # subset
rm tests/unit/test_admin_unit.py        # minimal
rm tests/unit/test_admin_working.py     # after merging

# Verify merged tests still pass
python -m pytest tests/unit/test_admin.py -v
```

**Data Loader Tests:**
```bash
# Test current state
python -m pytest tests/unit/test_data_loader*.py -v

# Use comprehensive version as base
mv tests/unit/test_data_loader_comprehensive.py tests/unit/test_data_loader_new.py
rm tests/unit/test_data_loader.py
rm tests/unit/test_data_loader_simple.py
mv tests/unit/test_data_loader_new.py tests/unit/test_data_loader.py

# Verify consolidated tests pass
python -m pytest tests/unit/test_data_loader.py -v
```

**Multi User Import Tests:**
```bash
# Test current state
python -m pytest tests/unit/test_multi_user_import*.py -v

# Use comprehensive as base, merge unit tests if needed
mv tests/unit/test_multi_user_import_comprehensive.py tests/unit/test_multi_user_import_new.py
# TODO: Check for unique tests in test_multi_user_import_unit.py and merge if needed
rm tests/unit/test_multi_user_import.py
rm tests/unit/test_multi_user_import_simple.py
rm tests/unit/test_multi_user_import_unit.py
mv tests/unit/test_multi_user_import_new.py tests/unit/test_multi_user_import.py

# Verify consolidated tests pass
python -m pytest tests/unit/test_multi_user_import.py -v
```

**Resume Loader Tests:**
```bash
# Keep main file, remove simple version
rm tests/unit/test_resume_loader_simple.py

# Verify remaining tests pass
python -m pytest tests/unit/test_resume_loader.py -v
```

**Security Tests:**
```bash
# Merge additional into main, then remove additional
# TODO: Manually merge content from test_security_additional.py into test_security.py
rm tests/unit/test_security_additional.py

# Verify merged tests pass
python -m pytest tests/unit/test_security.py -v
```

**Utils Tests:**
```bash
# Merge comprehensive and security versions
# TODO: Manually merge content into single test_utils.py
rm tests/unit/test_utils_comprehensive.py
rm tests/unit/test_utils_security.py

# Verify merged tests pass
python -m pytest tests/unit/test_utils.py -v
```

### Step 3: Phase 2 - Handle Misnamed/Orphaned

```bash
# Rename misnamed file
mv tests/unit/test_api_router_security.py tests/unit/test_api.py

# Remove orphaned file
rm tests/unit/test_projects_unit.py

# Verify renamed tests pass
python -m pytest tests/unit/test_api.py -v
```

### Step 4: Phase 3 - Create Missing Test Files

```bash
# Create new test files for modules without tests
# TODO: Create each of these files with appropriate test structure
touch tests/unit/test_auth.py
touch tests/unit/test_config.py
touch tests/unit/test_database.py
touch tests/unit/test_main.py
touch tests/unit/test_privacy.py
touch tests/unit/test_schemas.py
touch tests/unit/test_auth_router.py
touch tests/unit/test_mcp.py
```

### Step 5: Final Validation

```bash
# Run all tests to ensure nothing broke
python -m pytest tests/unit/ -v

# Check test count - should have 16 test files (one per app module)
ls tests/unit/test_*.py | wc -l

# Run coverage to identify gaps
python -m pytest tests/unit/ --cov=app --cov-report=html
```

## Success Criteria

- ✅ All tests continue to pass after consolidation
- ✅ Exactly 16 test files (1:1 mapping with app modules)
- ✅ No duplicate test files
- ✅ Proper naming convention followed
- ✅ No orphaned test files
- ✅ Test coverage maintained or improved
GET /admin/users                    # ✅ Partially covered
PUT /admin/users/{user_id}/toggle   # ❌ Missing
PUT /admin/users/{user_id}/admin    # ❌ Missing
GET /admin/api-keys                 # ✅ Covered in working file
POST /admin/api-keys               # ❌ Missing
DELETE /admin/api-keys/{key_id}    # ❌ Missing
GET /admin/endpoints               # ❌ Missing
PUT /admin/endpoints/{endpoint_id}/toggle  # ❌ Missing
DELETE /admin/endpoints/{endpoint_id}      # ❌ Missing
GET /admin/data/stats              # ❌ Missing
DELETE /admin/data/cleanup         # ❌ Missing
POST /admin/backup                 # ✅ Partially covered
GET /admin/backups                 # ❌ Missing
DELETE /admin/backup/cleanup       # ❌ Missing
POST /admin/restore/{backup_filename}  # ✅ Partially covered
GET /admin/audit                   # ✅ Partially covered
GET /admin/system                  # ❌ Missing
GET /admin/stats                   # ❌ Missing
```

#### 🔴 Priority 2: Data Loader Tests
**Action Items:**
- [ ] **Consolidate into `test_data_loader.py`:**
  - Merge comprehensive tests from `test_data_loader_comprehensive.py`
  - Include simple test patterns from `test_data_loader_simple.py`
- [ ] **Delete duplicate files:**
  - [ ] `test_data_loader_comprehensive.py`
  - [ ] `test_data_loader_simple.py`

**Required Test Coverage for Data Loader:**
```python
# Functions from app/data_loader.py:
discover_data_files()              # ❌ Unknown coverage
load_endpoint_data_from_file()     # ❌ Unknown coverage
import_endpoint_data_to_database() # ❌ Unknown coverage
import_all_discovered_data()       # ❌ Unknown coverage
get_data_import_status()           # ❌ Unknown coverage
```

#### 🔴 Priority 3: Multi User Import Tests
**Action Items:**
- [ ] **Consolidate into `test_multi_user_import.py`:**
  - Merge all functionality from 4 different files
  - Ensure proper mocking patterns
- [ ] **Delete duplicate files:**
  - [ ] `test_multi_user_import_comprehensive.py`
  - [ ] `test_multi_user_import_simple.py`
  - [ ] `test_multi_user_import_unit.py`

#### 🔴 Priority 4: Other Duplicates
**Action Items:**
- [ ] **Resume Loader:** Consolidate into `test_resume_loader.py`, delete `test_resume_loader_simple.py`
- [ ] **Security:** Consolidate into `test_security.py`, merge from `test_security_additional.py`
- [ ] **Utils:** Create `test_utils.py`, consolidate from `test_utils_comprehensive.py` and `test_utils_security.py`

### Phase 2: Create Missing Test Files

#### 🟡 Priority 5: Create Missing Core Module Tests

**test_auth.py** (for `app/auth.py`)
```python
# Required test coverage:
- get_password_hash()
- verify_password()
- create_access_token()
- get_current_user()
- get_current_admin_user()
- generate_api_key()
- Security tests for token validation
- Boundary tests for token expiration
- Negative tests for invalid credentials
```

**test_config.py** (for `app/config.py`)
```python
# Required test coverage:
- Settings class validation
- Environment variable loading
- Default value handling
- Invalid configuration scenarios
- Security-sensitive config validation
```

**test_database.py** (for `app/database.py`)
```python
# Required test coverage:
- Database model relationships
- Model validation
- Database session management
- get_db() dependency
- Constraint violations
- Database connection error handling
```

**test_main.py** (for `app/main.py`)
```python
# Required test coverage:
- FastAPI app initialization
- Middleware setup
- get_available_endpoints()
- custom_openapi()
- Router inclusion
- CORS configuration
- Error handlers
```

**test_privacy.py** (for `app/privacy.py`)
```python
# Required test coverage:
- PrivacyFilter class methods
- get_privacy_filter()
- Data filtering logic
- Privacy rule enforcement
- Boundary conditions for filtering
- Security tests for data leakage
```

**test_schemas.py** (for `app/schemas.py`)
```python
# Required test coverage:
- Pydantic model validation
- Field constraints
- Data serialization/deserialization
- Invalid data handling
- Boundary value testing
- Security input validation
```

#### 🟡 Priority 6: Create Missing Router Tests

**test_api.py** (for `app/routers/api.py`)
```python
# Required test coverage:
- All API endpoints
- Authentication requirements
- Input validation
- Error responses
- Security boundary tests
```

**test_auth_router.py** (for `app/routers/auth.py`)
```python
# Required test coverage:
- Login endpoint
- Token refresh
- User registration (if exists)
- Authentication flows
- Security tests for auth bypass
- Rate limiting tests
```

**test_mcp.py** (for `app/routers/mcp.py`)
```python
# Required test coverage:
- MCP protocol endpoints
- Message handling
- Error responses
- Security validation
```

### Phase 3: Enhance Test Quality

#### 🟢 Priority 7: Add Comprehensive Test Patterns

**For each test file, ensure coverage of:**

1. **Positive Flow Tests**
   - [ ] Happy path scenarios
   - [ ] Valid input combinations
   - [ ] Expected return values
   - [ ] Successful state changes

2. **Negative Flow Tests**
   - [ ] Invalid inputs
   - [ ] Missing required parameters
   - [ ] Malformed data
   - [ ] Authentication failures
   - [ ] Authorization failures

3. **Boundary Condition Tests**
   - [ ] Empty inputs
   - [ ] Maximum length inputs
   - [ ] Null/None values
   - [ ] Edge case values (0, -1, etc.)
   - [ ] Large datasets

4. **Security Tests**
   - [ ] SQL injection attempts
   - [ ] XSS payload testing
   - [ ] Path traversal attempts
   - [ ] Authentication bypass attempts
   - [ ] Authorization escalation tests
   - [ ] Input sanitization validation

5. **Error Handling Tests**
   - [ ] Database connection failures
   - [ ] External service failures
   - [ ] File system errors
   - [ ] Network timeouts
   - [ ] Memory/resource constraints

6. **Performance/Load Tests (where applicable)**
   - [ ] Large input handling
   - [ ] Multiple concurrent requests
   - [ ] Resource cleanup verification

## Implementation Checklist

### Phase 1 Tasks
- [ ] **Analyze content of all duplicate admin test files**
- [ ] **Create consolidated `test_admin.py` with complete endpoint coverage**
- [ ] **Delete 4 duplicate admin test files**
- [ ] **Consolidate data loader tests**
- [ ] **Consolidate multi user import tests**
- [ ] **Consolidate security, utils, and resume loader tests**
- [ ] **Remove incorrectly named test files**

### Phase 2 Tasks
- [ ] **Create `test_auth.py`**
- [ ] **Create `test_config.py`**
- [ ] **Create `test_database.py`**
- [ ] **Create `test_main.py`**
- [ ] **Create `test_privacy.py`**
- [ ] **Create `test_schemas.py`**
- [ ] **Create `test_api.py`**
- [ ] **Create `test_auth_router.py`**
- [ ] **Create `test_mcp.py`**

### Phase 3 Tasks
- [ ] **Add comprehensive security tests to all files**
- [ ] **Add boundary condition tests to all files**
- [ ] **Add negative flow tests to all files**
- [ ] **Add error handling tests to all files**
- [ ] **Verify proper mocking patterns in all files**
- [ ] **Add performance tests where applicable**

## Success Metrics

### Coverage Goals
- [ ] **100% of app modules have corresponding unit test files**
- [ ] **95%+ code coverage for all critical functions**
- [ ] **Zero duplicate test files**
- [ ] **All security-sensitive functions have security tests**
- [ ] **All public functions have positive and negative test cases**

### Quality Goals
- [ ] **All tests use proper mocking (no real database/file system access)**
- [ ] **All tests are fast (<1s each)**
- [ ] **All tests are deterministic and reliable**
- [ ] **All tests follow consistent naming patterns**
- [ ] **All tests have clear docstrings explaining purpose**

## Execution Notes

### Mocking Best Practices
- Use `unittest.mock.patch` for external dependencies
- Mock database sessions with MagicMock
- Mock file system operations
- Mock network calls
- Mock datetime for time-sensitive tests

### Test Organization Patterns
```python
class TestModuleFunctionName:
    """Test the specific function with various scenarios"""

    def test_function_name_success(self):
        """Test successful execution with valid inputs"""

    def test_function_name_invalid_input(self):
        """Test handling of invalid inputs"""

    def test_function_name_boundary_conditions(self):
        """Test edge cases and boundary values"""

    def test_function_name_security_validation(self):
        """Test security input validation"""

    def test_function_name_error_handling(self):
        """Test error scenarios and exception handling"""
```

### Security Test Patterns
- Test SQL injection payloads
- Test XSS payloads
- Test path traversal attempts
- Test authentication bypass
- Test authorization escalation
- Test input sanitization
- Test rate limiting
- Test CSRF protection

---

**Next Steps:** Start with Phase 1 by analyzing and consolidating the admin router tests, as this has the most duplication (5 files) and represents a critical security component.
