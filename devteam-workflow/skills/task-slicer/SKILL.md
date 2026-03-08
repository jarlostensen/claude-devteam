---
name: task-slicer
description: Decompose an implementation request into small, focused task slices, then optionally execute each slice against a configured executor model. Use when breaking down implementation work into independently executable chunks.
disable-model-invocation: true
argument-hint: "[description of the implementation task to slice]"
---

# Task Slicer

Decompose this request into task slices: **$ARGUMENTS**

## Step 0 — Check for existing slices

Compute the **task key** from `$ARGUMENTS` in your reasoning:
1. Normalise: strip leading/trailing whitespace, collapse internal whitespace to single spaces, lowercase
2. Hash: `hashlib.sha256(normalised.encode()).hexdigest()[:12]`
3. Slug: take the first 6 words of the normalised text, replace any non-alphanumeric characters with `-`, join with `-`
4. Expected filename: `<hash>-<slug>.json`
5. Expected path: `.claude/task-slices/<hash>-<slug>.json`

Use your **Read** tool to attempt to read `.claude/task-slices/<hash>-<slug>.json`.

**If the file exists:** Extract the `created_at` and `plan` fields, display the plan using the table format from Step 3, then ask:

> "Slices for this task were saved on {created_at}. What would you like to do?
>
> - **Use existing** — proceed to Step 4 with the loaded plan
> - **Regenerate** — continue to Step 1 (existing file will be overwritten)"

**If the file does not exist:** Continue to Step 1.

## Step 1 — Check prerequisites

Use your **Read** tool to check whether `.claude/planner_config.toml` exists.
- If it exists: note **FOUND** and read its contents to confirm the model endpoint.
- If it does not exist: note **MISSING** — execution will not be available.

Use your **Glob** tool with the pattern `**/.claude/**/task-slicer/scripts/slicer.py` (from the home directory or a known plugins path) to locate `slicer.py`.
- If found: note the path. On Windows, also try `C:/Users/**/.claude/**/task-slicer/scripts/slicer.py`.
- If not found: note **NOT FOUND** — execution will not be available.

Use your **Glob** tool to build the project file tree. Run these patterns and combine the results, ignoring hits under `.git`, `node_modules`, `__pycache__`, `.venv`, `venv`, `dist`, `build`, `target` (Rust):
- `**/*.rs`, `**/*.py`, `**/*.ts`, `**/*.js`, `**/*.go`, `**/*.toml`, `**/*.json`, `**/*.yaml`, `**/*.md`

List the matching files (up to 300). Use this list in Step 2 to determine which files already exist.

## Step 2 — Produce the slice plan

Read [planner-prompt.md](planner-prompt.md) and follow its rules exactly to decompose **$ARGUMENTS** into task slices.

Use the project file tree from Step 1 to determine which files exist. Only reference files that appear in the tree.

Produce a valid JSON slice plan matching the format defined in planner-prompt.md.

## Step 3 — Display and save the slice plan

Present the JSON in a readable format:

```
## Task Slice Plan

**Summary**: {json.summary}
**Type**: {json.task_type}
**Complexity**: {json.estimated_complexity}

### Slices

| ID | Description | Risk | Depends on |
|---|---|---|---|
| {slice.id} | {slice.description} | {slice.risk_level} | {slice.depends_on or "—"} |

### Global acceptance criteria
- {criterion}

---
Full JSON plan:
{pretty-printed JSON}
```

Use your **Write** tool to save the plan to `.claude/task-slices/<hash>-<slug>.json` with this structure:

```json
{
  "task": "<original $ARGUMENTS>",
  "hash": "<sha256[:12] computed in Step 0>",
  "created_at": "<current ISO 8601 timestamp, e.g. 2026-03-07T14:23:00>",
  "plan": { ...the complete slice plan JSON... }
}
```

If the `.claude/task-slices/` directory does not yet exist, create it first using your **Bash** tool with `mkdir -p .claude/task-slices` — this single-purpose directory creation command does not require complex shell syntax and will not trigger permission issues.

Confirm to the user: `"Plan saved to .claude/task-slices/<filename>"`

## Step 4 — Offer execution (optional)

If the config file from Step 1 shows **FOUND** and the executor script shows a valid path (not **NOT FOUND**), ask:

> "Would you like to execute the slices using the configured executor model?
>
> - **Yes, all** — run every slice sequentially
> - **Yes, select** — choose which slices to run
> - **No** — stop here with the plan"

If the user wants to execute, for each selected slice (in dependency order), use your **Bash** tool to run:

```
python "<executor script path>" "<slice JSON as single-line string>" "<current working directory>"
```

Display the executor's output for each slice. If a slice exits non-zero, show the error and stop before running dependent slices.

If config is **MISSING** or the script is **NOT FOUND**, display the plan only and note that execution requires `.claude/planner_config.toml` to be configured.
