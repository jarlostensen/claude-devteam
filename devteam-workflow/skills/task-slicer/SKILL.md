---
name: task-slicer
description: Decompose an implementation request into small, focused task slices, then optionally execute each slice against a configured executor model. Use when breaking down implementation work into independently executable chunks.
disable-model-invocation: true
argument-hint: "[description of the implementation task to slice]"
---

# Task Slicer

Decompose this request into task slices: **$ARGUMENTS**

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

## Step 3 — Display the slice plan

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
