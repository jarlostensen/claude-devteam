---
name: check-assumptions
description: Audit every documented requirement by asking "why does this exist and is it still valid?" — spawns one independent analysis agent per requirement and flags each as ok, doubt, or invalid/contradicted.
allowed-tools: Read, Glob, Grep, Agent
argument-hint: "[optional: specific requirement IDs to check, e.g. FR-001 NFR-003, or leave blank for all]"
---

# Assumption Check

Audit the validity of documented requirements. For each requirement, an independent agent searches all available evidence — documentation, code, ADRs, task plan, git history — and answers: "Why does this exist? Is it still valid?"

## Step 1 — Load requirements

Read `docs/requirements.md`. If it does not exist, report:

> "No requirements.md found — run /devteam-workflow:requirements first."

and stop.

Parse every requirement row from the Functional Requirements and Non-Functional Requirements tables. For each row, capture:
- **ID** (e.g. FR-001, NFR-003)
- **Full requirement text**
- **Priority** (Must / Should / Could / Won't)

If `$ARGUMENTS` specifies requirement IDs (space or comma separated), filter to those IDs only. Otherwise, process all requirements.

## Step 2 — Build project inventory

Use Glob and Read to assemble a brief inventory to pass to each agent:

1. Check whether these files exist and note their paths: `docs/task-plan.md`, `README.md`
2. List all files under `docs/adr/` using Glob pattern `docs/adr/**/*.md`
3. List source file paths (patterns: `src/**/*`, `lib/**/*`, `app/**/*`) — paths only, do not read content
4. List test file paths (patterns: `tests/**/*`, `test/**/*`, `**/*.test.*`, `**/*.spec.*`) — paths only

Format the inventory as a compact file list. This is passed verbatim into each agent's prompt.

## Step 3 — Spawn one analysis agent per requirement

For each requirement, use the Agent tool with `subagent_type: "devteam-researcher:researcher"` to spawn an independent analysis agent.

**Run all agents in parallel** — pass them all in a single message using multiple Agent tool calls.

Each agent prompt must be fully self-contained (the agent has no other context). Use this template, filling in the values for that specific requirement:

---

```
You are auditing a single software requirement to determine whether it is still valid.

Requirement ID: {ID}
Requirement text: {full requirement text}
Priority: {priority}

Project files that exist (use these paths when reading):
{inventory from Step 2}

---

Your task: answer two questions.

1. WHY does this requirement exist? What user need, technical constraint, or business rule does it represent?
2. IS IT STILL VALID? Look for evidence that it is satisfied, contradicted, superseded, or no longer relevant.

How to investigate — read any of the following that exist and are relevant:

- docs/requirements.md — look for notes, dependencies between requirements, or context that clarifies this one
- docs/task-plan.md — check if this requirement is linked to a task and whether that task is complete, in progress, or removed
- docs/adr/*.md — read all ADR files; look for decisions that satisfy, constrain, or explicitly contradict this requirement
- README.md — check whether the project purpose and scope still include what this requirement describes
- Source code — use Grep to search for key terms from the requirement text; determine whether the described behaviour is implemented, absent, or was removed
- Git log — run `git log --oneline --no-merges -50` to check whether there are commits that added, changed, or explicitly removed the behaviour this requirement describes

Verdict definitions:
- ok: the requirement is clearly still valid, justified, and consistent with all evidence
- doubt: you found signals suggesting the requirement may be outdated, redundant, or poorly justified, but cannot confirm invalidity without more information
- invalid/contradicted: the requirement conflicts with a confirmed decision (ADR, committed code, explicit out-of-scope statement), exactly duplicates another requirement, or describes behaviour that was explicitly removed or never intended

Return EXACTLY this block and nothing else:

REQUIREMENT: {ID}
VERDICT: ok | doubt | invalid/contradicted
RATIONALE: {1-3 sentences explaining the verdict}
EVIDENCE: {specific files, ADR titles, code locations, or git commits that informed the verdict — be precise}
```

---

## Step 4 — Collect results and produce the report

Wait for all agents to complete. Parse each response for the REQUIREMENT / VERDICT / RATIONALE / EVIDENCE fields.

If any agent returns malformed output, record that requirement ID under a "parse error" section rather than silently dropping it.

Produce the final report in this format:

```
## Assumption Check Report

Scope: {N} requirements checked  ({date})
Arguments: {$ARGUMENTS or "all requirements"}

### Summary
{1-2 paragraphs. State how many are ok / doubt / invalid/contradicted.
Call out any patterns — e.g. "Three NFRs cite performance thresholds with no corresponding benchmark
or test, placing them all under doubt." Name requirements by ID when calling out patterns.}

---

### Invalid / Contradicted  ({count})

| ID | Priority | Requirement | Rationale | Evidence |
|---|---|---|---|---|
| FR-NNN | Must | {text} | {rationale} | {evidence} |

---

### Doubt  ({count})

| ID | Priority | Requirement | Rationale | Evidence |
|---|---|---|---|---|
| FR-NNN | Should | {text} | {rationale} | {evidence} |

---

### Confirmed valid  ({count})

| ID | Priority | Requirement |
|---|---|---|
| FR-NNN | Must | {text} |

---

### Recommended actions

For each invalid/contradicted requirement:
1. **{ID}**: {Specific action — remove it, rewrite it with correct scope, or confirm intent and update the text}

For each doubt requirement:
2. **{ID}**: {Specific action — gather missing evidence, clarify with stakeholders, or accept as-is with a note}

---

### Parse errors (if any)
- {IDs of requirements whose agent responses could not be parsed}
```
