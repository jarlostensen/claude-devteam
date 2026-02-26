---
name: session-start
description: Load project context at the start of a working session. Reads requirements, task plan, recent ADRs, and git state, then provides a concise briefing. Use at the beginning of each session before doing any work.
disable-model-invocation: true
---

# Session Start

Load and summarise the current project state. Do this before any work begins.

## Step 1 — Requirements

Read `docs/requirements.md` if it exists. Note:
- Total number of functional and non-functional requirements
- Any open questions listed

## Step 2 — Task plan

Read `docs/task-plan.md` if it exists. Identify:
- The next incomplete task (first unchecked `- [ ]` item)
- How many tasks remain vs. how many are done
- Whether a test command is defined

## Step 3 — Recent ADRs

List files in `docs/adr/`. Read the most recent 3 (highest numbered). For each, extract:
- The decision made (one sentence)
- The status (proposed / accepted / deprecated / superseded)

## Step 4 — Git state

Run each of the following if git is available:

```
git branch --show-current
git status --short
git log --oneline -5
```

Extract:
- Current branch name
- Whether the working tree is clean or has uncommitted changes (list changed files if any)
- The last 5 commit messages

If git is not available or the directory is not a repository, note "No git repository found."

## Step 5 — Produce a session briefing

Output the following. Be concise — this is a briefing, not a report.

```
## Session Context

**Requirements**: {N} functional, {N} non-functional
{If open questions exist: "Open questions: {list them}"}

**Task Plan**:
- Next task: TASK-NNN — {description} [{requirement IDs}]
- {N} tasks remaining, {N} completed

**Recent decisions**:
- {ADR-NNNN}: {one-line summary} [{status}]

**Repository**:
- Branch: {branch name}
- Working tree: {Clean | {N} uncommitted changes: {file list}}
- Recent commits:
  - {commit hash} {commit message}
  - {commit hash} {commit message}

Ready to proceed. What would you like to work on?
```

If neither `docs/requirements.md` nor `docs/task-plan.md` exists, respond:

```
No project context found. To get started:
1. Run `/devteam-workflow:requirements` to define requirements
2. Run `/devteam-workflow:plan` to create a task plan
```
