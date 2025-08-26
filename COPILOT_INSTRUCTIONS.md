# GitHub Copilot Instructions

## GitHub CLI Commands
**CRITICAL**: When using GitHub CLI (`gh`) commands, ALWAYS redirect output to a text file first, then read the file content.

### Correct Pattern:
```bash
gh run list --repo philmcneely/Daemon-pmac --limit 5 > ci_status.txt 2>&1
```
Then read the file:
```bash
cat ci_status.txt
```

### Why This is Required:
- GitHub CLI output cannot be read directly from terminal output in VS Code
- The user has repeatedly emphasized this requirement
- This pattern ensures reliable access to CI/CD status and logs

### Examples:
- CI status: `gh run list > ci_status.txt 2>&1`
- Run details: `gh run view <run_id> > ci_details.txt 2>&1`
- Failure logs: `gh run view <run_id> --log-failed > ci_logs.txt 2>&1`

Always follow this pattern for ALL `gh` commands.
