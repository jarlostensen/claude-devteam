---
name: code-review
description: Review recent code changes for quality, correctness, and standards adherence. Runs in an isolated agent with no conversation context. Use before merging or declaring a task complete.
context: fork
agent: code-reviewer
allowed-tools: Read, Grep, Glob, Bash(git *)
disable-model-invocation: true
argument-hint: "[commit range or file paths, or leave blank for HEAD~1]"
---

# Code Review

Conduct a thorough code review. You have no context from the conversation that produced this code — review it purely on its merits.

## Step 1 — Establish what changed

Determine the scope:
- If $ARGUMENTS specifies a commit range or file paths, review those
- Otherwise, review changes since HEAD~1: run `git diff HEAD~1`
- Also run `git diff HEAD~1 --stat` to see the full list of changed files

If git is not available or no changes are found, read any recently modified source files using Glob sorted by modification time.

## Step 2 — Read the standards

Read `docs/requirements.md` if it exists — reviews check implementation against requirements.
Read `docs/task-plan.md` if it exists — identify which task this code is meant to complete.

## Step 3 — Review each changed file

For each changed file, read its full current content (not just the diff) to understand context. Apply the following checklist:

### Correctness
- [ ] Does the code do what it claims to do?
- [ ] Are all error and failure paths handled?
- [ ] Are there obvious off-by-one errors, null dereferences, or type mismatches?
- [ ] Is concurrency handled correctly (if applicable)?

### Standards adherence
- [ ] No unused code (functions, imports, variables defined but not called)
- [ ] Functions and variables are named accurately (the name matches the behaviour)
- [ ] Functions are appropriately sized (investigate if > ~100 lines)
- [ ] No silent swallowing of errors
- [ ] No hardcoded secrets, credentials, or magic strings
- [ ] No implementation details leaking through public interfaces

### Documentation
- [ ] All public functions and methods have documentation (docstring, JSDoc, etc.)
- [ ] Comments explain WHY, not WHAT, where they exist
- [ ] No misleading or out-of-date comments

### Tests
- [ ] New functionality has corresponding tests
- [ ] Tests cover at least one error/edge case per function
- [ ] Test names describe what is being tested and the expected outcome

### Requirements
- [ ] The change satisfies the requirement(s) it is meant to address
- [ ] The acceptance criteria from the task plan are met

## Step 4 — Output

```
## Code Review

**Scope**: {commit range or files reviewed}
**Task**: {TASK-NNN from task plan, or "Not identified"}

### Summary
{One paragraph overall assessment. State directly: ready to merge / needs minor fixes / has blocking issues.}

### Critical Issues (must fix)
1. `{file}:{line}` — {issue description. Explain why this is wrong and what the correct approach is.}

### Warnings (should fix)
1. `{file}:{line}` — {issue description}

### Suggestions (optional improvements)
1. `{file}:{line}` — {suggestion}

### Checklist
| Area | Status |
|---|---|
| Correctness | Pass / Fail / N/A |
| Standards adherence | Pass / Fail |
| Documentation | Pass / Fail |
| Tests | Pass / Fail / N/A |
| Requirements coverage | Pass / Fail / N/A |
```

End with one of:
- "Ready to merge." (no Critical Issues)
- "Merge after addressing Critical Issues." (Critical Issues present)
