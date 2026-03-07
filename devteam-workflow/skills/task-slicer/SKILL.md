---
name: task-slicer
description: Decompose an implementation request into small, focused task slices for delegation to an executor model. Reads planner_config.toml from .claude/ in the active project. Use when breaking down implementation work into independently executable chunks.
disable-model-invocation: true
argument-hint: "[description of the implementation task to slice]"
---

# Task Slicer

Decompose this request into task slices: **$ARGUMENTS**

Locate and run the slicer script, then display the resulting slice plan.

## Step 1 — Check prerequisites

Config file location: !`[ -f ".claude/planner_config.toml" ] && echo "FOUND: .claude/planner_config.toml" || echo "MISSING"`

Slicer script: !`find "$HOME/.claude" -path "*/task-slicer/scripts/slicer.py" 2>/dev/null | sort | tail -1`

If the config line above shows **MISSING**, stop immediately and tell the user:

```
ERROR: .claude/planner_config.toml not found.

Create it with the following content:

[model]
endpoint  = "https://api.openai.com/v1/chat/completions"
api_key   = "sk-..."
name      = "gpt-4o"
max_slices = 8
```

If the slicer script line is empty, stop and tell the user:
```
ERROR: slicer.py not found in the Claude plugin cache.
Re-install the devteam-workflow plugin, or reinstall from the marketplace.
```

## Step 2 — Run the slicer

Using the resolved slicer script path from Step 1, run:

```bash
python3 "{resolved script path}" "{$ARGUMENTS}" "{current working directory}"
```

Pass the current working directory as the third argument so the script can locate `.claude/planner_config.toml` relative to the project root.

If the script exits with a non-zero code, display the error output and stop.

## Step 3 — Display the slice plan

Parse and present the JSON output in a readable format:

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

## Additional resources

- Planner system prompt: [planner-prompt.md](planner-prompt.md)
- Config schema: see Step 1 error message above
