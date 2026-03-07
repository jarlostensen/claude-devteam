# Task Plan

Last updated: 2026-03-07

## Overview

Add a `task-slicer` skill to `devteam-workflow` that decomposes a user's implementation request into small, focused task slices (JSON) suitable for delegation to a weaker executor model. The skill drives a Python script that calls an OpenAI-compatible API endpoint; configuration (endpoint URL, API key, model name) is read from `.claude/planner_config.toml` in the active project. The skill fails fast and clearly if the config file is missing.

## Requirements covered

Inline (no formal requirements.md):
- The skill generates a JSON task-slice plan from a user request
- The planner prompt in `docs/planner_slice_prompt.md` is the canonical reference for the system prompt format
- Configuration is read from `.claude/planner_config.toml` in the active project — skill must fail with a clear message if the file does not exist
- The Python script uses only the standard library (no third-party packages) except for TOML parsing

## Version control

- VCS: git
- Remote: GitHub
- Default branch: master
- Branching strategy: feature branch per task

## Test command

```
python -m py_compile devteam-workflow/skills/task-slicer/scripts/slicer.py
```

## Tasks

### Phase 1: Skill scaffold

- [ ] TASK-001: Create `devteam-workflow/skills/task-slicer/SKILL.md` [inline-FR-001]
  - Acceptance: File exists and is valid SKILL.md frontmatter (name, description, disable-model-invocation, argument-hint)
  - Acceptance: Skill instructions reference the Python script and the config file path clearly

- [ ] TASK-002: Bundle default planner prompt as `devteam-workflow/skills/task-slicer/planner-prompt.md` [inline-FR-002]
  - Acceptance: File contains the full system prompt from `docs/planner_slice_prompt.md`
  - Acceptance: The `{max_slices}` placeholder is preserved exactly as-is for runtime substitution

### Phase 2: Python script

- [ ] TASK-003: Create `devteam-workflow/skills/task-slicer/scripts/slicer.py` [inline-FR-001, inline-FR-002, inline-FR-003]
  - Acceptance: `python -m py_compile devteam-workflow/skills/task-slicer/scripts/slicer.py` exits 0
  - Acceptance: Script exits with code 1 and a clear human-readable error if `.claude/planner_config.toml` is not found
  - Acceptance: Script reads `endpoint`, `api_key`, `model`, `max_slices` from the TOML config
  - Acceptance: Script substitutes `{max_slices}` in the system prompt before sending
  - Acceptance: Script collects the project file tree and includes it in the user message
  - Acceptance: Script prints valid JSON to stdout on success
  - Acceptance: Uses only Python standard library (no pip installs required beyond `tomllib`/`tomli` for TOML)
