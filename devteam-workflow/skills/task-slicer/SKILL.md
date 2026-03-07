---
name: task-slicer
description: Decompose an implementation request into small, focused task slices, then optionally execute each slice against a configured executor model. Use when breaking down implementation work into independently executable chunks.
disable-model-invocation: true
argument-hint: "[description of the implementation task to slice]"
---

# Task Slicer

Decompose this request into task slices: **$ARGUMENTS**

## Step 0 — Check for existing slices

Existing slice files:
!`python -c "import pathlib; p=pathlib.Path('.claude/task-slices'); files=sorted(p.glob('*.json')) if p.exists() else []; print('\n'.join(f.name for f in files) if files else 'NONE')"`

Compute the **task key** from `$ARGUMENTS`:
1. Normalise: strip leading/trailing whitespace, collapse internal whitespace to single spaces, lowercase
2. Hash: `hashlib.sha256(normalised.encode()).hexdigest()[:12]`
3. Slug: take the first 6 words of the normalised text, replace any non-alphanumeric characters with `-`, join with `-`
4. Expected filename: `<hash>-<slug>.json`

Check whether the expected filename appears in the listing above.

**If found:** Read `.claude/task-slices/<hash>-<slug>.json`, extract the `created_at` and `plan` fields, display the plan using the table format from Step 3, then ask:

> "Slices for this task were saved on {created_at}. What would you like to do?
>
> - **Use existing** — proceed to Step 4 with the loaded plan
> - **Regenerate** — continue to Step 1 (existing file will be overwritten)"

**If not found:** Continue to Step 1.

## Step 1 — Check prerequisites

Config file: !`python -c "import pathlib; p=pathlib.Path('.claude/planner_config.toml'); print('FOUND: ' + str(p) if p.exists() else 'MISSING')"`

Executor script: !`python -c "import pathlib; hits=sorted(pathlib.Path.home().joinpath('.claude').rglob('task-slicer/scripts/slicer.py')); print(str(hits[-1]) if hits else 'NOT FOUND')"`

Project file tree:
!`python -c "
import pathlib
ignored = {'.git','__pycache__','node_modules','.venv','venv','dist','build','.mypy_cache','.pytest_cache','.ruff_cache'}
files = sorted(p for p in pathlib.Path('.').rglob('*') if p.is_file() and not any(d in p.parts for d in ignored))
print('\n'.join(str(f) for f in files[:300]))
"`

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

Then save the plan to `.claude/task-slices/<hash>-<slug>.json` (creating the directory if it does not exist) with this structure:

```json
{
  "task": "<original $ARGUMENTS>",
  "hash": "<sha256[:12] computed in Step 0>",
  "created_at": "<current ISO 8601 timestamp, e.g. 2026-03-07T14:23:00>",
  "plan": { ...the complete slice plan JSON... }
}
```

Confirm to the user: `"Plan saved to .claude/task-slices/<filename>"`

## Step 4 — Offer execution (optional)

If the config file from Step 1 shows **FOUND** and the executor script shows a valid path (not **NOT FOUND**), ask:

> "Would you like to execute the slices using the configured executor model?
>
> - **Yes, all** — run every slice sequentially
> - **Yes, select** — choose which slices to run
> - **No** — stop here with the plan"

If the user wants to execute, for each selected slice (in dependency order), run:

```bash
python "{executor script path}" '{slice JSON as single-line string}' "{current working directory}"
```

Display the executor's output for each slice. If a slice exits non-zero, show the error and stop before running dependent slices.

If config is **MISSING** or the script is **NOT FOUND**, display the plan only and note that execution requires `.claude/planner_config.toml` to be configured.
