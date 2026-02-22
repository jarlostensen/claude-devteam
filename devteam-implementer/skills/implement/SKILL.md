---
name: implement
description: Implement a feature or task from the plan. Reads requirements, existing patterns, and design decisions first, proposes an approach, then implements only after confirmation.
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
argument-hint: "[task ID or description, e.g. TASK-001 or 'add user authentication']"
---

# Implementation

Implement: **$ARGUMENTS**

Follow every step in order. Do not skip any step, and do not write code before step 5.

## Step 1 — Load project context

Read:
1. `docs/requirements.md` — identify which requirements the task addresses
2. `docs/task-plan.md` — confirm the task exists and find its acceptance criteria
3. Any ADR in `docs/adr/` relevant to the area being implemented
4. Any design document in `docs/design/` relevant to this task

If `docs/requirements.md` or `docs/task-plan.md` do not exist, stop and tell the user to run `/devteam-workflow:requirements` and `/devteam-workflow:plan` first.

## Step 2 — Read the existing code

Before proposing anything, read the relevant existing code in the area to be changed. Use Glob and Grep to locate:
- Files that will need to be modified
- Adjacent code that establishes the patterns to follow
- Existing tests for the area

Summarise what you found: what already exists, what is missing, and what patterns are in use.

## Step 3 — Pattern check

Search for any existing implementation that already does part or all of what is needed. State clearly whether you will reuse, extend, or create new code — and if creating new, why existing code cannot be reused.

## Step 4 — Propose the approach

Before writing any code, propose:

```
## Implementation approach for: {task}

**Requirements addressed**: FR-NNN, NFR-NNN
**Files to change**: {list}
**Files to create**: {list, or "None"}
**Approach**: {2–4 sentence description — what will be done and why this way}
**Test plan**: {which tests will be written and what they will verify}
**What will NOT be done**: {anything deferred or out of scope}
```

Wait for the user to confirm this approach before writing any code. Do not proceed without confirmation.

## Step 5 — Implement

After confirmation, implement the changes. Apply the standards from `session-context`:
- Write only what is needed for this task
- Follow the naming and structural patterns found in step 2
- Handle all error paths
- Document all public functions and methods
- Do not add speculative abstractions or future-proofing

## Step 6 — Write tests

Immediately after implementation, write unit tests for every new function or behaviour. Tests must:
- Cover the happy path
- Cover at least one error or edge case
- Follow the testing framework and conventions found in step 2

Do not mark the task complete until tests exist.

## Step 7 — Verify

Run the test command from `docs/task-plan.md`. All tests must pass before declaring the task done.

If tests fail, fix the implementation — do not adjust tests to pass around broken behaviour.

## Step 8 — Complete

Confirm:
- Which requirement IDs are now satisfied
- Whether the task acceptance criteria from the plan are met
- Suggest updating `docs/task-plan.md` to mark the task complete: `/devteam-workflow:plan`
