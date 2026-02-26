---
name: retrofit
description: Analyse an existing codebase and produce the project documentation the devteam suite expects — requirements, task plan, and ADR stubs. Use when adopting the devteam workflow on a project that already has code, designs, or prior implementation decisions.
disable-model-invocation: true
argument-hint: "[optional: focus area or specific feature to retrofit]"
---

# Retrofit Existing Project

Analyse this existing project and produce the devteam documentation structure so that development can continue using the full suite of skills and agents.

Work through each phase in order, presenting findings at each stage before writing anything. All output is reviewed with the user before being written to disk.

---

## Phase 1 — Project scan

Gather a complete picture of what already exists before drawing any conclusions.

### 1a — Structure and stack

Use Glob to map the project:
- Top-level directory layout
- Primary source directories
- Test directories and test file patterns
- Configuration files (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `pom.xml`, `Makefile`, etc.)

From the configuration files, extract:
- Project name and description
- Primary language and runtime version
- Direct dependencies (libraries already chosen)
- The test command (scripts.test, pytest config, etc.)
- The build command

### 1b — Existing documentation

Read any existing documentation in this order:
1. `README.md` or `README.rst` — often the richest source of intent
2. Any files in `docs/` not created by the devteam suite
3. Any `CHANGELOG.md`, `CONTRIBUTING.md`, or `ARCHITECTURE.md`
4. Inline documentation: read a representative sample of docstrings and module-level comments

### 1c — Git history

Run:
```
git log --oneline --no-merges -30
git log --format="%s" --no-merges -100 | sort | uniq -c | sort -rn | head -20
```

Extract themes from the commit history:
- What areas of the code have been most actively changed?
- Are there commit messages that describe features, fixes, or significant decisions?
- Are there any merge commits that indicate feature branches?

### 1d — Open work signals

Check for indicators of planned or incomplete work:

Search for TODO/FIXME comments:
```
grep -r "TODO\|FIXME\|HACK\|XXX" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" --include="*.rs" -l
```

Check for skipped or pending tests (search for `skip`, `xtest`, `pytest.mark.skip`, `xit(`, `test.skip`, etc.).

If `gh` is available, check for open issues and pull requests:
```
gh issue list --state open --limit 20
gh pr list --state open
```

### 1e — Present the project profile

Before proceeding, present a concise project profile for the user to confirm:

```
## Project Profile

**Name**: {name}
**Language / runtime**: {language and version}
**Primary purpose**: {1–2 sentence description inferred from README and code}
**Test command**: {command}
**Dependencies**: {key libraries — 5–10 most significant}

**Codebase size**: ~{N} source files, ~{N} test files
**Most active areas**: {top 3 directories by recent commit activity}
**Open signals**: {N} TODO/FIXME comments, {N} open GitHub issues, {N} skipped tests

**Existing documentation**: {list what was found}

Is this accurate? Anything to add or correct before proceeding?
```

Wait for the user to confirm before proceeding to Phase 2.

---

## Phase 2 — Derive requirements

Requirements describe what the system must do and the constraints it must satisfy — not how it is implemented.

### 2a — Infer functional requirements

From the README, tests, and code, identify what the system demonstrably does. For each distinct capability:
- State it as a requirement: "The system shall {verb} {object} {condition}"
- Assign a priority: Must (already implemented), Should (partially implemented), Could (planned but not started)

Primary sources for inference (in priority order):
1. Test names and test descriptions — these are specifications
2. README feature sections and usage examples
3. Exported/public API surface (function names, route handlers, CLI commands)
4. Docstrings describing purpose

### 2b — Infer non-functional requirements

From the codebase, infer constraints the system is designed to satisfy:
- **Performance**: Are there caches, connection pools, or pagination that imply scale requirements?
- **Security**: Are there authentication, authorisation, or input validation patterns?
- **Availability**: Is there retry logic, circuit breakers, or health checks?

Note these as NFRs with "Should" or "Could" priority since they are inferred, not confirmed.

### 2c — Present draft requirements

Present the inferred requirements for user review:

```
## Draft Requirements

These are inferred from the existing code, tests, and documentation. Please:
- Confirm requirements that are accurate
- Correct any that misrepresent the intent
- Add any that are missing
- Remove any that are out of scope

### Functional Requirements (inferred)

| ID | Requirement | Basis | Priority |
|---|---|---|---|
| FR-001 | The system shall ... | {test name / README section / function name} | Must |

### Non-Functional Requirements (inferred)

| ID | Requirement | Category | Basis | Priority |
|---|---|---|---|---|
| NFR-001 | The system shall ... | Performance | {basis} | Should |

### Open questions
- {Anything that could not be confidently inferred}
```

Wait for user to confirm or revise before writing.

### 2d — Write `docs/requirements.md`

Create `docs/` if it does not exist. Write the confirmed requirements using the standard format.

---

## Phase 3 — Capture existing architectural decisions as ADRs

Identify decisions that are already baked into the codebase and should be recorded so the suite can reference them.

### 3a — Identify existing decisions

From the dependencies and code structure, identify the major choices already made:
- Framework choice (e.g. Express, FastAPI, Gin, Actix)
- Database or storage technology
- Authentication mechanism
- Testing framework
- Significant architectural patterns (REST vs GraphQL, event-driven, etc.)
- Any notable library choices with non-obvious rationale

For each, identify what the alternatives would have been (to fill in the ADR's "considered options").

### 3b — Present proposed ADRs

```
## Proposed ADR stubs

The following decisions are already in effect in the codebase. I'll create accepted ADRs for them so the suite can reference them. Confirm, remove, or add to this list:

1. ADR-0001: Use {framework} as the web framework
2. ADR-0002: Use {database} for persistence
3. ADR-0003: {other significant decision}

Anything to add or remove?
```

Wait for user confirmation.

### 3c — Write ADR stubs

Create `docs/adr/` if it does not exist. For each confirmed decision, write a minimal MADR-format ADR with:
- Status: `accepted` (decision is already in effect)
- Date: today's date (as "retrofitted" — note the actual decision predates this file)
- Decision outcome: the chosen option
- Pros and cons: brief, based on what can be inferred

Note in each ADR: `> This ADR was created retrospectively to document an existing decision.`

---

## Phase 4 — Draft the task plan

The task plan captures work that remains to be done, based on open signals found in Phase 1.

### 4a — Identify remaining work

Consolidate:
- Open GitHub issues (if available)
- TODO/FIXME comments with their file locations
- Skipped or pending tests
- README sections marked as TODO or "coming soon"
- Gaps between inferred requirements and current implementation (any FR with "Could" priority that isn't implemented)

### 4b — Present draft tasks

```
## Draft Task Plan

The following tasks are inferred from open signals in the codebase. Confirm, revise, reorder, or add:

### Identified from open issues
- [ ] TASK-001: {issue title} [{FR-NNN if mappable}]

### Identified from TODO comments
- [ ] TASK-002: {description of TODO} — `{file}:{line}` [{FR-NNN if mappable}]

### Identified from gaps in requirements coverage
- [ ] TASK-003: Implement {requirement not yet satisfied} [FR-NNN]

Anything to add, remove, or reprioritise?
```

Wait for user confirmation.

### 4c — Write `docs/task-plan.md`

Write the confirmed task plan using the standard format, including:
- The test command confirmed in Phase 1
- The VCS section (git/GitHub with default branch from `git branch --show-current`)
- All confirmed tasks with requirement cross-references

---

## Phase 5 — Summary

Report what was produced:

```
## Retrofit Complete

Created:
- `docs/requirements.md` — {N} functional, {N} non-functional requirements
- `docs/adr/` — {N} ADRs for existing decisions
- `docs/task-plan.md` — {N} tasks identified

You can now use the full devteam suite on this project:
- `/devteam-workflow:session-start` — start each session with a project briefing
- `/devteam-implementer:implement [TASK-NNN]` — implement tasks from the plan
- `/devteam-reviewer:code-review` — review changes before merging

To refine the requirements or plan further:
- `/devteam-workflow:requirements` — add or update requirements
- `/devteam-workflow:plan` — update the task plan
```
