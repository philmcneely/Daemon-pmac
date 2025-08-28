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

### 🔴 PROBLEM RESOLUTION (MANDATORY)

#### Root Cause Analysis
- **NEVER** suppress warnings or add workarounds - ALWAYS fix the root cause
- **ALWAYS** examine application code first to understand how to perform actions correctly

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
