# GitHub Copilot Instructions

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
