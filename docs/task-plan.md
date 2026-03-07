# Task Plan

Last updated: 2026-03-07

## Overview

Add a `task-slicer` skill to `devteam-workflow` that decomposes a user's implementation request into small, focused task slices (JSON), executes each slice against a configured executor model via an OpenAI-compatible API, and persists generated plans so they can be reused or referenced. Slice files are keyed by a content hash of the task arguments, so any change to the task description produces a new file (natural invalidation).

## Requirements covered

Inline (no formal requirements.md):
- The skill generates a JSON task-slice plan from a user request [FR-001]
- The planner prompt in `docs/planner_slice_prompt.md` is the canonical reference for the system prompt format [FR-002]
- Configuration is read from `.claude/planner_config.toml` in the active project — skill must fail with a clear message if the file does not exist [FR-003]
- The Python script uses only the standard library (no third-party packages) except for TOML parsing [FR-004]
- Generated slice plans are saved to `.claude/task-slices/` with a unique filename derived from a content hash of the task arguments [FR-005]
- Before generating, the skill checks whether a saved plan already exists for the given task and offers to reuse it [FR-006]
- Changing the task description invalidates the previous plan (different hash → different filename) [FR-007]

## Version control

- VCS: git
- Remote: GitHub
- Default branch: master
- Branching strategy: feature branch per task (e.g. `feature/TASK-004-slice-persistence`)

## Test command

```
python -m py_compile devteam-workflow/skills/task-slicer/scripts/slicer.py
```

## Tasks

### Phase 1: Skill scaffold (complete)

- [x] TASK-001: Create `devteam-workflow/skills/task-slicer/SKILL.md` [FR-001]
- [x] TASK-002: Bundle default planner prompt as `devteam-workflow/skills/task-slicer/planner-prompt.md` [FR-002]

### Phase 2: Python executor script (complete)

- [x] TASK-003: Create `devteam-workflow/skills/task-slicer/scripts/slicer.py` [FR-001, FR-002, FR-003, FR-004]
  - Executor receives a single slice JSON, reads target files, calls the configured model in an agentic loop
  - ToolCallParser handles `<tool_call>`, `[TOOL_CALLS]`, and `<|channel|>` formats from local LLMs
  - Call deduplication cache prevents runaway loops on repeated tool calls

### Phase 3: Slice persistence

- [x] TASK-004: Add Step 0 to `SKILL.md` — check for existing saved slices before generating [FR-005, FR-006]
  - List `.claude/task-slices/*.json` via `!python` command
  - Instruct Claude to derive a content hash and slug from `$ARGUMENTS`:
    - Normalise: strip, collapse whitespace, lowercase
    - Hash: `sha256(normalised)[:12]` (hex)
    - Slug: first 6 alphanumeric words joined with `-`
    - Expected filename: `<hash>-<slug>.json`
  - If the expected file appears in the listing: read it, display the saved plan, and ask:
    > "Slices for this task were saved on {created_at}. Use existing plan, or regenerate?"
    > - **Use existing** — skip to Step 4
    > - **Regenerate** — continue to Step 1 (file will be overwritten)
  - If no match: proceed directly to Step 1
  - Acceptance: `SKILL.md` contains Step 0 with the `!python` listing command and the hash/slug derivation instructions
  - Acceptance: Running the skill twice with identical args detects the file on the second run

- [x] TASK-005: Add save step to `SKILL.md` — persist the plan after Step 3 [FR-005, FR-007]
  - After displaying the plan, write `.claude/task-slices/<hash>-<slug>.json` using the Write tool
  - File content is a JSON object:
    ```json
    {
      "task": "<original $ARGUMENTS>",
      "hash": "<sha256[:12]>",
      "created_at": "<ISO 8601 timestamp>",
      "plan": { ...slice plan JSON... }
    }
    ```
  - Create `.claude/task-slices/` directory if it does not exist (note this in the skill instructions)
  - Confirm to user: `"Plan saved to .claude/task-slices/<filename>"`
  - Acceptance: `SKILL.md` contains the save instruction after Step 3
  - Acceptance: After running, the file exists at the expected path with valid JSON
  - Acceptance: Running with a different task description produces a different filename
