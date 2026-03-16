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

If config is **MISSING** or the script is **NOT FOUND**, display the plan only and note that execution requires `.claude/planner_config.toml` to be configured.

---

## Step 4a — Execute each slice

For each selected slice (in dependency order):

1. **Write the slice JSON to a temp file** — use your **Write** tool to save the slice's JSON object to `.claude/task-slices/current-slice.json` in the project root. This avoids shell quoting issues (dollar signs, backslashes, and braces in the JSON context would be corrupted if passed as a bash argument).

2. **Run the executor** — use your **Bash** tool:

```
python "<executor script path>" "@<project root>/.claude/task-slices/current-slice.json" "<current working directory>"
```

Capture the full stdout. If the process exits non-zero, show the error output and stop — do not proceed to dependent slices.

---

## Step 4b — Apply the executor's output

The executor outputs file contents as text. **It does not write files to disk.** You must apply each file yourself.

For every `=== FILE: <path> === ... === END FILE ===` block in the stdout:

1. **Create any missing parent directories** — use your **Bash** tool: `mkdir -p "<parent directory>"` if the directory does not yet exist.
2. **Write the file** — use your **Write** tool with the exact path from the FILE header and the exact content between the markers. Do not add, remove, or alter any characters.
3. **Confirm** — after writing, note: `"Written: <path>"`.

If the executor output contains no FILE blocks (e.g. a timeout or error message), do not write anything. Show the raw output to the user and ask how to proceed.

---

## Step 4c — Verify the acceptance criteria

After applying the files for a slice, check each of its `acceptance_criteria` entries in order.

Run any shell command the criterion refers to (e.g. `cargo check`, `python -m py_compile`, `pytest`) using your **Bash** tool from the appropriate working directory.

For each criterion report one of:

- **PASS** — the command exited 0 or the condition is met.
- **FAIL** — the command failed. Show the relevant output (last 20 lines). Do not proceed to dependent slices until this is resolved.

After all criteria for a slice pass, print a summary line:

```
[slice_NNN] PASS — <N> file(s) written, all acceptance criteria met.
```

Then continue to the next slice.
