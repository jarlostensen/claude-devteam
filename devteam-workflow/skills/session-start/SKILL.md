---
name: session-start
description: Load project context at the start of a working session. Reads requirements, task plan, and recent ADRs, then provides a concise briefing. Use at the beginning of each session before doing any work.
disable-model-invocation: true
allowed-tools: Read, Glob, Bash(git log *)
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

## Step 4 — Recent git activity

Run `git log --oneline -10` if git is available. Capture the last few commit messages.

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

**Recent commits**:
- {commit message}
- {commit message}

Ready to proceed. What would you like to work on?
```

If neither `docs/requirements.md` nor `docs/task-plan.md` exists, respond:

```
No project context found. To get started:
1. Run `/devteam-workflow:requirements` to define requirements
2. Run `/devteam-workflow:plan` to create a task plan
```
