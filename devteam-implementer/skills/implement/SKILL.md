---
name: implement
description: Implement a feature or task from the plan. Reads requirements, existing patterns, and design decisions first, proposes an approach, then implements only after confirmation. Manages git branching and commits around the work.
disable-model-invocation: true
argument-hint: "[task ID or description, e.g. TASK-001 or 'add user authentication']"
---

# Implementation

Implement: **$ARGUMENTS**

Follow every step in order. Do not skip any step, and do not write code before step 6.

## Step 1 — Load project context

Read:
1. `docs/requirements.md` — identify which requirements the task addresses
2. `docs/task-plan.md` — confirm the task exists and find its acceptance criteria and VCS settings
3. Any ADR in `docs/adr/` relevant to the area being implemented
4. Any design document in `docs/design/` relevant to this task

If `docs/requirements.md` or `docs/task-plan.md` do not exist, stop and tell the user to run `/devteam-workflow:requirements` and `/devteam-workflow:plan` first.

## Step 2 — Git: branch setup

Check the current git state:

```
git branch --show-current
git status --short
```

If git is not available or the directory is not a repository, note this and skip to Step 3. Otherwise:

**If the working tree is not clean** (uncommitted changes exist), stop and tell the user:
> "There are uncommitted changes in the working tree. Please commit or stash them before starting new work."

**If the working tree is clean**, report the current branch and ask:

> "Currently on branch `{branch}`.
> Start this task on a new branch? (Recommended — keeps the task isolated and makes it easy to review or abandon.)
>
> Options:
> - **Yes** — create `feature/{task-slug}` (or suggest an alternative name)
> - **No** — continue on `{branch}`"

If the user chooses yes, confirm the branch name (suggest `feature/TASK-NNN-short-description` based on $ARGUMENTS, but let the user modify it), then:

```
git checkout -b {branch-name}
```

Confirm the new branch was created and note it — this is the branch that will be committed and optionally merged at the end.

## Step 3 — Read the existing code

Before proposing anything, read the relevant existing code in the area to be changed. Use Glob and Grep to locate:
- Files that will need to be modified
- Adjacent code that establishes the patterns to follow
- Existing tests for the area

Summarise what you found: what already exists, what is missing, and what patterns are in use.

## Step 4 — Pattern check

Search for any existing implementation that already does part or all of what is needed. State clearly whether you will reuse, extend, or create new code — and if creating new, why existing code cannot be reused.

## Step 5 — Propose the approach

Before writing any code, propose:

```
## Implementation approach for: {task}

**Branch**: {branch name}
**Requirements addressed**: FR-NNN, NFR-NNN
**Files to change**: {list}
**Files to create**: {list, or "None"}
**Approach**: {2–4 sentence description — what will be done and why this way}
**Test plan**: {which tests will be written and what they will verify}
**What will NOT be done**: {anything deferred or out of scope}
```

Wait for the user to confirm this approach before writing any code. Do not proceed without confirmation.

## Step 6 — Implement

After confirmation, implement the changes. Apply the standards from `session-context`:
- Write only what is needed for this task
- Follow the naming and structural patterns found in step 3
- Handle all error paths
- Document all public functions and methods
- Do not add speculative abstractions or future-proofing

## Step 7 — Write tests

Immediately after implementation, write unit tests for every new function or behaviour. Tests must:
- Cover the happy path
- Cover at least one error or edge case
- Follow the testing framework and conventions found in step 3

Do not proceed to step 8 until tests exist.

## Step 8 — Verify

Run the test command from `docs/task-plan.md`. All tests must pass before proceeding.

If tests fail, fix the implementation — do not adjust tests to pass around broken behaviour.

## Step 9 — Commit

With all tests passing, commit the work:

Identify the files changed during this task (implementation and tests). Stage them specifically — do not use `git add .` or `git add -A`:

```
git add {file1} {file2} ...
```

Generate a commit message in conventional commit format:
- `feat: ` for a new feature
- `fix: ` for a bug fix
- `test: ` for adding tests without changing behaviour
- `refactor: ` for restructuring without behaviour change

Format: `{type}({scope}): {short description}` followed by a blank line and the requirement IDs addressed.

Example:
```
feat(auth): add password reset flow

Implements FR-005, FR-006.
```

Show the proposed message and the files to be staged. Ask the user to confirm or edit, then commit:

```
git commit -m "{confirmed message}"
```

## Step 10 — Branch completion

If the work was done on a feature branch (not on main/master), offer the user three options:

> "All tests pass and the work is committed on `{branch-name}`.
>
> What would you like to do next?
>
> **1. Merge into {main/master}**
> Merges the branch locally and deletes it. Choose this for straightforward changes reviewed inline.
>
> **2. Push to GitHub for a pull request**
> Pushes the branch to the remote. Choose this for changes that need team review before merging.
>
> **3. Leave the branch as-is**
> The branch stays locally. You can merge or push it later."

**If option 1 — merge:**
```
git checkout {main/master}
git merge --no-ff {branch-name} -m "Merge {branch-name}"
git branch -d {branch-name}
```
Confirm the merge completed and report the final state.

**If option 2 — push:**
```
git push -u origin {branch-name}
```
Report the pushed branch URL if available (`git remote get-url origin`).

**If option 3 — leave:** note the branch name so the user can act on it later.

## Step 11 — Mark complete

Confirm:
- Which requirement IDs are now satisfied
- Whether the task acceptance criteria from the plan are met
- Remind the user to mark the task complete in `docs/task-plan.md`
