---
name: requirements-check
description: Verify that the implementation satisfies the documented requirements and task acceptance criteria. Use before marking any task complete.
context: fork
agent: code-reviewer
allowed-tools: Read, Grep, Glob, Bash(git *)
disable-model-invocation: true
argument-hint: "[task ID or feature to check, or leave blank to check all incomplete tasks]"
---

# Requirements Conformance Check

Verify that the implementation satisfies the documented requirements for: **$ARGUMENTS**

## Step 1 — Load requirements and plan

Read:
1. `docs/requirements.md` — the full requirements list
2. `docs/task-plan.md` — the tasks and their acceptance criteria

If $ARGUMENTS specifies a task ID (e.g. TASK-003), focus on that task and its linked requirements.
If $ARGUMENTS is blank, check all tasks that are not yet marked complete (`- [ ]`).

## Step 2 — Read the implementation

For each task under review, identify the files that implement it. Use Glob and Grep to find:
- Source files relevant to the requirement
- Test files that exercise the relevant behaviour
- Any configuration changes

Read the implementation and tests in full.

## Step 3 — Check each requirement

For each requirement linked to the task(s) under review:

**Functional requirements**: Is there code that demonstrably implements this behaviour? Does a test exercise it?

**Non-functional requirements**: Is there evidence the constraint is met?
- Performance NFRs: Is there a benchmark or load test? Does the implementation avoid obvious bottlenecks?
- Security NFRs: Is the security control in place and tested?
- Availability NFRs: Is error handling and recovery implemented?

**Acceptance criteria**: Read each acceptance criterion from the task plan. Is it satisfied?

## Step 4 — Output

```
## Requirements Conformance Check

**Scope**: {task IDs or feature reviewed}

### Summary
{One paragraph. State clearly: all requirements satisfied / gaps found.}

### Requirements coverage

| ID | Requirement | Implemented | Tested | Notes |
|---|---|---|---|---|
| FR-NNN | {requirement text} | Yes/Partial/No | Yes/No | {notes} |
| NFR-NNN | {requirement text} | Yes/Partial/No | Yes/No | {notes} |

### Acceptance criteria

| Task | Criterion | Met? | Notes |
|---|---|---|---|
| TASK-NNN | {criterion} | Yes/No | |

### Gaps (requirements not yet satisfied)
1. **{FR/NFR-NNN}**: {What is missing. Be specific — what code or test would need to exist.}

### Verdict
{All requirements satisfied — task may be marked complete.}
{OR}
{The following requirements are not yet satisfied: FR-NNN, NFR-NNN. Do not mark complete until they are addressed.}
```
