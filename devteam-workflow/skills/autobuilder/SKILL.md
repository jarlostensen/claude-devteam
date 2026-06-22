---
name: autobuilder
description: End-to-end automated build orchestrator. Drives a task from design through implementation, review, and commit — pausing only for design decisions, approach confirmation, review issues, and branch disposition. State is persisted per task so any phase can be resumed or retried without re-running completed work.
disable-model-invocation: true
argument-hint: "[task ID or description, e.g. TASK-003 or 'add user authentication']"
---

# Autobuilder

Drive this task end-to-end: **$ARGUMENTS**

Execute six phases in order. Each phase is **idempotent** — before running any phase, check whether it was already completed in the saved state and skip if so. Pause for user input only at the designated checkpoints marked **PAUSE**.

---

## Phase 0 — Load or create state

### Compute the task key

From `$ARGUMENTS`, derive the task key in your reasoning:
1. Normalise: lowercase, trim whitespace, collapse internal spaces
2. Slug: first 8 words of the normalised text, replace any non-alphanumeric characters with `-`, join with `-`
3. State file path: `.claude/autobuilder/<slug>.json`

### Check for existing state

Use your **Read** tool to attempt to read `.claude/autobuilder/<slug>.json`.

**If the file exists**, display:

```
## Autobuilder — Existing Run Found

Task:    {state.task}
Branch:  {state.notes.branch or "not yet created"}
Started: {state.created_at}

Phase status:
  1. init:      {state.phases.init}
  2. design:    {state.phases.design}
  3. implement: {state.phases.implement}
  4. review:    {state.phases.review}
  5. commit:    {state.phases.commit}
  6. complete:  {state.phases.complete}
```

Then ask:
> "An autobuilder run exists for this task. What would you like to do?
>
> - **Resume** — continue from the first incomplete phase
> - **Restart** — reset all phases to pending and begin again from Phase 1
> - **Abandon** — delete the state file and stop"

If **Resume**: set `current_phase` to the first phase where status is not `"complete"` or `"skipped"`. Continue from that phase.
If **Restart**: reset all phase values to `"pending"`, set `review_iteration` to `0`, clear `notes` (preserve `task` and `task_slug`). Save state. Continue from Phase 1.
If **Abandon**: use your **Bash** tool to delete the state file (`rm .claude/autobuilder/<slug>.json`). Stop.

**If the file does not exist**, create initial state:

```json
{
  "task": "<original $ARGUMENTS>",
  "task_slug": "<computed slug>",
  "created_at": "<current ISO 8601 timestamp>",
  "updated_at": "<current ISO 8601 timestamp>",
  "review_iteration": 0,
  "phases": {
    "init":      "pending",
    "design":    "pending",
    "implement": "pending",
    "review":    "pending",
    "commit":    "pending",
    "complete":  "pending"
  },
  "notes": {}
}
```

Use your **Bash** tool to create the directory if needed: `mkdir -p .claude/autobuilder`
Then use your **Write** tool to save the state file to `.claude/autobuilder/<slug>.json`.

> **State updates**: after every phase completes or is skipped, update `phases.<name>` to `"complete"` or `"skipped"`, set `updated_at` to the current ISO timestamp, and use your **Write** tool to save the updated state before proceeding to the next phase.

---

## Phase 1 — INIT

*Skip if `state.phases.init === "complete"`.*

### 1a — Load project docs

Read:
1. `docs/requirements.md` — note all FR/NFR IDs and open questions
2. `docs/task-plan.md` — find the entry matching `$ARGUMENTS` by task ID or keyword; note its acceptance criteria and requirement IDs

**If `docs/requirements.md` does not exist**:
- If source files or git history are present (existing project): stop and tell the user:
  > "No requirements document found. Run `/devteam-workflow:retrofit` to derive docs from the existing codebase, or run `/devteam-workflow:requirements` and `/devteam-workflow:plan` to create them from scratch."
- If blank project: stop and tell the user to run `/devteam-workflow:requirements` first.
- Delete the state file before stopping in either case.

**If `docs/task-plan.md` does not exist**: stop and tell the user to run `/devteam-workflow:plan` first. Delete the state file.

**If the task cannot be matched** in `docs/task-plan.md`: ask the user:
> "I could not find a task matching `$ARGUMENTS` in the task plan. Please describe:
> 1. What needs to be implemented
> 2. Which requirements it satisfies (FR/NFR IDs, or an informal description)
> 3. The test command to use for verification
>
> I'll use these in place of a plan entry."

Save the user's answers to `state.notes.informal_plan`.

### 1b — Check git state

Run:
```
git branch --show-current
git status --short
```

If the working tree has uncommitted changes, stop:
> "There are uncommitted changes in the working tree. Please commit or stash them before running autobuilder."

Delete the state file before stopping.

Save the current branch name to `state.notes.base_branch`.

### 1c — Save phase complete

Update `state.phases.init` to `"complete"`. Save state.

---

## Phase 2 — DESIGN

*Skip if `state.phases.design === "complete"` or `"skipped"`.*

### 2a — Assess whether design is needed

**PAUSE** — ask the user:
> "Does this task require a design session before implementation?
>
> - **Yes** — structured design discussion (recommended for new components, new APIs, or cross-cutting concerns)
> - **No** — skip directly to implementation"

If **No**: update `state.phases.design` to `"skipped"`. Save state. Proceed to Phase 3.

### 2b — Check for an existing design document

Use your **Glob** tool to list files in `docs/design/`. Look for a file whose name contains the task slug or a closely related keyword.

If a relevant design doc exists, read it and present:
> "An existing design note was found: `{path}` (last modified: {date}).
>
> - **Use this design** — proceed with the existing note
> - **Redo design** — start a fresh session (the existing note will be overwritten)"

If **Use this design**: save the path to `state.notes.design_doc`. Skip to Step 2d.

### 2c — Run design session (inline)

You are now acting as a software architect. Do not propose implementation code at this stage.

1. **Problem statement** — restate the design problem in your own words: what capability is being designed, which FR/NFR IDs it must satisfy, which accepted ADRs are relevant. Read `docs/adr/` to identify relevant decisions. **PAUSE** — ask the user to confirm or correct this framing before proceeding.

2. **Constraints** — identify hard constraints: Must-priority requirements and accepted ADRs that cannot be contradicted.

3. **Options** — generate 2–3 design options. For each, cover:
   ```
   ### Option N: {Name}
   What it is: (one sentence)
   How it works: (conceptual, no code)
   Requirements coverage:
     FR-NNN: satisfied / partial / not satisfied
   Tradeoffs:
     Pros: ...
     Cons: ...
   What it defers or makes harder: ...
   ```

4. **Discussion** — ask questions to explore tradeoffs. Examples: "Which NFR is most critical here?", "Is the added complexity of Option 2 justified at this scale?" **PAUSE** — do not rush to a conclusion. Allow the user to redirect.

5. **Decision** — summarise the chosen option, rejected alternatives, and outstanding risks.

6. **Write design note** — write `docs/design/<slug>.md`:
   ```markdown
   # Design: {Topic}

   Date: {date}
   Status: Draft

   ## Problem
   {What is being designed and why}

   ## Constraints
   {Requirements and existing ADRs that constrain the design}

   ## Options considered
   {Summary of each option and why it was or wasn't chosen}

   ## Decision
   {The chosen approach and rationale}

   ## Consequences
   {What this makes easier, what it makes harder, what risks remain}
   ```

Save the design doc path to `state.notes.design_doc`.

### 2d — Run design review (inline, independent perspective)

You are now acting as an independent architect reviewer. You have no knowledge of the discussion that produced the design — review it purely on its merits.

Read:
1. `docs/requirements.md`
2. All files in `docs/adr/`
3. The design doc at `state.notes.design_doc`

Produce a structured review:

```
## Design Review: {title}

### Summary
{One paragraph — state directly: ready to proceed / needs minor revision / has blocking issues}

### Critical Issues (must resolve before implementation)
1. {Issue — cite the design section and the requirement it violates or leaves unaddressed}

### Warnings (should resolve)
1. {Issue}

### Requirements coverage
| Requirement | Covered? | Notes |
|---|---|---|
| FR-NNN | Yes / Partial / No | |

### ADR consistency
{Any tensions with existing accepted ADRs}

### Top 3 risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
```

**If no Critical Issues**: end with "Design is ready to proceed." Update `state.phases.design` to `"complete"`. Save state. Proceed to Phase 3.

**If Critical Issues exist**: **PAUSE** — ask:
> "The design review found {N} critical issue(s):
> {list}
>
> - **Revise design** — address these issues and re-run the review
> - **Accept as-is** — proceed to implementation with these issues noted
> - **Abort** — stop here"

If **Revise**: return to Step 2c.
If **Accept as-is**: save the accepted issues to `state.notes.design_review_exceptions`. Update `state.phases.design` to `"complete"`. Save state. Proceed to Phase 3.
If **Abort**: delete the state file and stop.

---

## Phase 3 — IMPLEMENT

*Skip if `state.phases.implement === "complete"`.*

### 3a — Git: create or resume feature branch

Read `state.notes.base_branch`.

Run:
```
git branch --show-current
git log {base_branch}..HEAD --oneline
```

**If commits already exist ahead of the base branch** (resuming after a partial run):
> "Found {N} existing commit(s) on `{current_branch}`. Resuming implementation on this branch."
Save `state.notes.branch` to the current branch name if not already saved. Proceed to 3b.

**If on the base branch with no prior branch in state**: **PAUSE** — confirm the branch name:
> "Start implementation on a new branch?
>
> Suggested: `feature/{slug}`
>
> - **Yes** — create `feature/{slug}`
> - **Rename** — use a different name
> - **No** — stay on `{base_branch}`"

If Yes or Rename: run `git checkout -b {branch-name}`. Save `state.notes.branch`.
If No: save `state.notes.branch` as `state.notes.base_branch`.

### 3b — Read the existing code

Use Glob and Grep to locate:
- Files likely to be modified
- Adjacent code that establishes patterns to follow
- Existing tests for this area

Summarise: what already exists, what is missing, what patterns are in use.

### 3c — Pattern check

Search for any existing implementation that already does part or all of what is needed. State explicitly whether you will reuse, extend, or create new code. If creating new code, explain why existing code cannot be reused.

### 3d — Propose approach

Before writing any code, present:

```
## Implementation approach: {task}

Branch:                 {branch name}
Requirements addressed: {FR/NFR IDs}
Files to change:        {list}
Files to create:        {list, or "None"}
Approach:               {2-4 sentences}
Test plan:              {what will be written and what it will verify}
Out of scope:           {anything deferred or excluded}
```

**PAUSE — wait for user confirmation before writing any code.** Do not proceed without explicit approval.

### 3e — Implement

After confirmation:
- Write only what is needed for this task
- Follow the naming and structural patterns found in 3b
- Handle all error paths
- Document all public functions and methods
- No speculative abstractions or future-proofing

### 3f — Write tests

Immediately after implementation, write unit tests for every new function or behaviour:
- Happy path
- At least one error or edge case per function
- Follow the testing framework and conventions found in 3b

Do not proceed to 3g until tests exist.

### 3g — Verify

Run the test command from `docs/task-plan.md` (or `state.notes.informal_plan.test_command` if informal). All tests must pass before proceeding.

If tests fail, fix the implementation. Do not adjust tests to pass around broken behaviour. Repeat until all tests pass.

### 3h — Save phase complete

Update `state.phases.implement` to `"complete"`. Save state.

---

## Phase 4 — REVIEW

*Skip if `state.phases.review === "complete"`.*

You are now acting as an independent code reviewer. You have no memory of the implementation conversation — review the code purely on its merits.

### 4a — Establish the diff

If there are uncommitted changes (Phase 5 has not yet run), review the working tree:
```
git diff HEAD --stat
git diff HEAD
```

If all changes are already committed (Phase 5 ran before Phase 4 on a resume), review the branch diff:
```
git diff {state.notes.base_branch}...{state.notes.branch} --stat
git diff {state.notes.base_branch}...{state.notes.branch}
```

Read each changed file in full (not just the diff) to understand the surrounding context.

Also read `docs/requirements.md` and `docs/task-plan.md` to identify which requirements and acceptance criteria this change must satisfy.

### 4b — Apply review checklist

**Correctness**
- [ ] Does the code do what it claims?
- [ ] Are all error and failure paths handled?
- [ ] Off-by-one errors, null dereferences, or type mismatches?
- [ ] Concurrency handled correctly (if applicable)?

**Standards adherence**
- [ ] No unused code (functions, imports, variables)
- [ ] Names accurately describe behaviour
- [ ] No silent error swallowing
- [ ] No hardcoded secrets, credentials, or magic strings
- [ ] No implementation details leaking through public interfaces

**Documentation**
- [ ] All public functions/methods have documentation
- [ ] Comments explain WHY, not WHAT

**Tests**
- [ ] New functionality has corresponding tests
- [ ] Tests cover at least one error/edge case per function
- [ ] Test names describe what is being tested and the expected outcome

**Requirements**
- [ ] Change satisfies the requirement(s) it addresses
- [ ] Acceptance criteria from the task plan are met

### 4c — Produce review report

```
## Code Review — Iteration {state.review_iteration + 1}

Scope: {base_branch}...{branch}

### Summary
{One paragraph — state directly: ready to commit / needs minor fixes / has blocking issues}

### Critical Issues (must fix)
1. `{file}:{line}` — {description and correct approach}

### Warnings (should fix)
1. `{file}:{line}` — {description}

### Suggestions (optional improvements)
1. {suggestion}

### Checklist
| Area              | Status |
|---|---|
| Correctness       | Pass / Fail / N/A |
| Standards         | Pass / Fail |
| Documentation     | Pass / Fail |
| Tests             | Pass / Fail / N/A |
| Requirements      | Pass / Fail / N/A |
```

### 4d — Handle review outcome

**If no Critical Issues**: update `state.phases.review` to `"complete"`. Save state. Proceed to Phase 5.

**If Critical Issues exist**:

Increment `state.review_iteration` by 1. Save state.

If `state.review_iteration > 3`: stop and tell the user:
> "This is review iteration {N}. After 3 review-fix cycles, automatic iteration has halted. Please review the critical issues above manually and decide how to proceed. When ready, re-run `/devteam-workflow:autobuilder $ARGUMENTS` to resume."

Otherwise, **PAUSE** — present the issues and ask:
> "The review found {N} critical issue(s) that must be fixed:
> {list}
>
> - **Fix all** — address every critical issue now, then re-run the review
> - **Fix selected** — choose which issues to fix before re-reviewing
> - **Accept as-is** — proceed to commit despite the issues (noted in state)
> - **Abort** — stop here; the branch and commits are preserved"

If **Fix all** or **Fix selected**: return to Phase 3, Step 3e. After fixes, run 3g (verify tests pass), then return here and re-run the review from Step 4a.
If **Accept as-is**: save the accepted issues to `state.notes.review_exceptions`. Update `state.phases.review` to `"complete"`. Save state. Proceed to Phase 5.
If **Abort**: stop. Note the branch name. Do not delete the state file (the user can resume later).

---

## Phase 5 — COMMIT

*Skip if `state.phases.commit === "complete"`.*

### 5a — Check if already committed

Run:
```
git status --porcelain
```

If the output is empty and commits exist ahead of the base branch, the implementation is already committed. Update `state.phases.commit` to `"complete"`. Save state. Proceed to Phase 6.

### 5b — Stage files

Identify all files changed during implementation and testing. Stage them specifically — do not use `git add .` or `git add -A`:

```
git add {file1} {file2} ...
```

### 5c — Generate commit message

Produce a conventional commit message:
- `feat(scope): description` — new feature
- `fix(scope): description` — bug fix
- `test(scope): description` — tests only, no behaviour change
- `refactor(scope): description` — restructuring without behaviour change

Format: short description on line 1, blank line, then a body listing the requirement IDs addressed.

Example:
```
feat(auth): add password reset flow

Implements FR-005, FR-006.
Acceptance criteria for TASK-012 satisfied.
```

Present the proposed message and the list of staged files.

**PAUSE — wait for user confirmation or edit before committing.**

### 5d — Commit

After confirmation:
```
git commit -m "{confirmed message}"
```

Run `git log --oneline -1` to capture the commit hash. Save it to `state.notes.commit_hash`. Update `state.phases.commit` to `"complete"`. Save state.

---

## Phase 6 — COMPLETE

*Skip if `state.phases.complete === "complete"`.*

### 6a — Branch disposition

If implementation was done on a feature branch (not the base branch): **PAUSE** — offer:
> "All tests pass and the work is committed on `{state.notes.branch}`.
>
> What would you like to do next?
>
> **1. Merge into {base_branch}**
> Merges locally and deletes the feature branch.
>
> **2. Push to GitHub for a pull request**
> Pushes the branch to the remote; create the PR manually.
>
> **3. Leave the branch as-is**
> Keep locally; merge or push later."

**If merge**:
```
git checkout {base_branch}
git merge --no-ff {branch-name} -m "Merge {branch-name}"
git branch -d {branch-name}
```
Confirm the merge completed and report the final state.

**If push**:
```
git push -u origin {branch-name}
```
Report the remote URL if available (`git remote get-url origin`).

**If leave**: note the branch name.

### 6b — Mark task complete in the task plan

Read `docs/task-plan.md`. Find the line matching this task — it will look like:
```
- [ ] TASK-NNN: {description}
```
Change `[ ]` to `[x]`. Use your **Edit** tool to make this change.

If using an informal plan (no task plan entry), skip this step and note it in the summary.

### 6c — Final summary

```
## Autobuilder Complete

Task:     {state.task}
Branch:   {state.notes.branch or state.notes.base_branch}
Commit:   {state.notes.commit_hash or "merged into " + base_branch}

Design:          {state.notes.design_doc or "skipped"}
Review cycles:   {state.review_iteration}
Review notes:    {state.notes.review_exceptions or "none"}

Requirements satisfied:
  {list the FR/NFR IDs addressed}

Suggested next steps:
  - /devteam-reviewer:requirements-check {task ID} — verify requirement tracing
  - /devteam-reviewer:security-review — if security-sensitive code was changed
  - /devteam-workflow:session-start — to check what task is next
```

### 6d — Save phase complete

Update `state.phases.complete` to `"complete"`. Save state.

The state file is preserved at `.claude/autobuilder/<slug>.json` as a permanent record of this build run.
