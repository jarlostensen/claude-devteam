---
name: plan
description: Create or update a structured task plan from the current requirements. Use after requirements are defined or when starting a new implementation task.
disable-model-invocation: true
argument-hint: "[feature or task to plan, or leave blank to plan from all requirements]"
---

# Task Planning

You are acting as a technical project planner. Produce a concrete, actionable task plan that maps to the documented requirements.

## Step 1 — Confirm version control

Check whether git is available and initialised:

```
git status
```

If git is present and the project is already a repository, read the current branch name:

```
git branch --show-current
```

If git is not initialised, ask the user:
> "This project does not appear to be a git repository. Would you like to initialise one before planning? (recommended)"

If the user confirms, note that `git init` should be run before implementation begins — but do not run it here. Record the choice below.

If a `docs/task-plan.md` already exists with a Version control section, read it and do not ask again.

Ask the user to confirm:
> "Version control: git (GitHub). Is this correct, or would you like to use a different VCS?"

Record the confirmed choice in the plan.

## Step 2 — Read the requirements

Read `docs/requirements.md`. This is mandatory — do not produce a plan without reading the requirements first. If the file does not exist, tell the user to run `/devteam-workflow:requirements` first.

## Step 3 — Read any existing plan

Check whether `docs/task-plan.md` exists. If it does, read it. Update it rather than replacing it — preserve completed tasks and add or revise pending ones.

## Step 4 — Read relevant existing code

Before planning implementation tasks, use Glob to check whether related code already exists. Tasks must not re-implement what is already there.

## Rules for task plans

- Every task must reference the requirement(s) it satisfies (e.g. [FR-001]).
- Tasks must be concrete enough to complete in a single focused session.
- The test command must be identified before any implementation tasks.
- Never plan tasks that write code with no requirement tracing.
- Defer any code that does not have immediately understandable use.
- Do not include implementation details that belong in design (e.g. "use a hash map") unless a design decision has already been recorded in an ADR.

## Step 5 — Write `docs/task-plan.md`

```markdown
# Task Plan

Last updated: {date}

## Overview

{One paragraph describing what this plan delivers}

## Requirements covered

{Comma-separated list of requirement IDs: FR-001, FR-002, NFR-001}

## Version control

- VCS: git
- Remote: GitHub
- Default branch: main (or master — confirm from `git branch`)
- Branching strategy: feature branches per task (e.g. `feature/TASK-NNN-short-description`)

## Test command

```
{command to run the full test suite}
```

## Tasks

### Phase 1: {Phase name}

- [ ] TASK-001: {Task description} [FR-001]
  - Acceptance: {How to verify this task is done}
- [ ] TASK-002: {Task description} [FR-001, NFR-001]
  - Acceptance: {How to verify this task is done}

### Phase 2: {Phase name}

- [ ] TASK-003: ...
```

## Step 6 — Confirm coverage

After writing, report:
- Which requirements are covered by at least one task
- Which requirements have NO task (these are gaps — flag them clearly)
- Suggest running `/devteam-architect:design-session` for any tasks that involve non-trivial design decisions before implementation begins
