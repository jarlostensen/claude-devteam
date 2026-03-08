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

### Phase 4: Executor and planner improvements (from ISS-001 – ISS-006)

Evidence source: `docs/slice-execution-report.md` (2026-03-08 test run, qwen3-coder-next).

Tasks are ordered by impact-to-effort ratio: highest-impact/lowest-effort first.

---

- [x] TASK-006: Configurable API timeout and stricter system prompt in `slicer.py` [ISS-004, ISS-002]

  **Why**: 3 of 6 slices timed out at the hardcoded 120-second limit. Local models on consumer
  hardware need 180–300 s for large prompts. Also tighten the system prompt to address the
  markdown fence and external text issues at the instruction level (defensive layer before
  the post-processor in TASK-007).

  **Changes to `slicer.py`**:
  - Add `timeout` key to `_resolve_model_config` (default: `240`)
  - Read from `[model]` section in `planner_config.toml`; update `_CONFIG_HELP` example
  - Pass `timeout` value to `urllib.request.urlopen(req, timeout=timeout)`
  - Extend `_EXECUTOR_SYSTEM_PROMPT` with:
    > "Do NOT wrap file contents in markdown code fences (` ``` `, ` ```rust `, etc.). Output raw
    > source code directly between the FILE markers. Do NOT output any text, reasoning, or
    > commentary before or after the `=== FILE: ... ===` blocks."

  **Acceptance**:
  - `python -m py_compile slicer.py` exits 0
  - Setting `timeout = 240` in `planner_config.toml` is read and passed to `urlopen`
  - `_EXECUTOR_SYSTEM_PROMPT` contains explicit prohibition of markdown fences and external text

---

- [x] TASK-007: FILE-block output post-processor in `slicer.py` [ISS-002]

  **Why**: Even with a stricter system prompt, local models frequently wrap code in markdown
  fences inside FILE blocks and leak explanation text outside them. A post-processor makes
  the output clean regardless of model compliance, avoiding manual cleanup.

  **Changes to `slicer.py`**:
  - Add `_clean_executor_response(text: str) -> str` function:
    1. Extract all `=== FILE: <path> ===\n...\n=== END FILE ===` blocks using regex
    2. For each block body, strip a leading ` ```[lang] ` line and trailing ` ``` ` line if present
    3. Strip leading/trailing blank lines from each block body
    4. Reassemble: return only the cleaned FILE blocks joined by `\n\n`, discarding all text outside
    5. If no FILE blocks are found at all, return the original text unchanged (preserves conversational/tool-only responses)
  - Call `_clean_executor_response(content)` on the final response inside `_run_executor` before returning

  **Acceptance**:
  - `python -m py_compile slicer.py` exits 0
  - Unit test (doctest or inline): input with explanatory prefix + markdown-fenced FILE block → output is clean FILE block with no fences and no prefix text
  - Input with no FILE blocks → output unchanged

---

- [x] TASK-008: `context_files` slice field — preload read-only dependency files [ISS-003, ISS-005]

  **Why**: Two failure modes share the same root cause — the model lacked context it needed and
  either explored via tool calls (burning turns → timeout) or hallucinated function names.
  A `context_files` field lets the planner declare files the executor needs to *read* but
  not *modify*, so they are preloaded without appearing in `target_files`.

  **Changes to `slicer.py`**:
  - In `main()`: read `slice_data.get("context_files", [])` alongside `target_files`
  - Add `_read_context_files(project_root, context_files) -> dict[str, str]` (same logic as
    `_read_target_files` but returns `[NOT FOUND]` instead of `[create it]` for missing files)
  - In `_build_executor_message`: add a distinct `## Reference files (do not modify)` section
    after the target files section, containing the context file contents
  - Update docstrings

  **Changes to `planner-prompt.md`**:
  - Add `context_files` to the slice JSON schema example (optional array, default `[]`)
  - Add rule: "For slices that call functions defined in other modules, list those modules in
    `context_files` and copy their complete public function signatures into the `context` field."

  **Acceptance**:
  - `python -m py_compile slicer.py` exits 0
  - A slice with `context_files: ["test/src/stats.rs"]` includes that file's content under
    "Reference files" in the executor message
  - `planner-prompt.md` schema and rule are updated

---

- [x] TASK-009: Three new planner rules in `planner-prompt.md` [ISS-001, ISS-005, ISS-006]

  **Why**: The three most impactful planner failures were caused by absent rules, not model
  capability. Adding explicit rules to `planner-prompt.md` fixes them at the source for all
  future slice plans, not just this one.

  **Rule 1 — No forward references (fixes ISS-001)**:
  > "If a file X will be *created* in a later slice, do not add `mod X`, `use X`, `import X`,
  > or any other reference to X in an earlier slice. The reference belongs in the same slice
  > that creates X, or in a dedicated wiring slice. Never write a slice whose acceptance
  > criteria require `cargo check` / `build` to pass if the slice itself introduces references
  > to files that will not exist until a later slice."

  **Rule 2 — Integration slices must include dependency signatures (fixes ISS-005)**:
  > "For any slice whose implementation calls functions defined in a *different* module, add
  > those modules to `context_files` and copy their complete public function signatures
  > (including parameter names, types, and return types) verbatim into the `context` field.
  > Never assume the executor will infer an interface it has not been shown."

  **Rule 3 — One source file per test slice (fixes ISS-006)**:
  > "Test slices must target exactly one source file. Do not combine tests for multiple modules
  > in a single slice — split into one slice per module under test. This keeps the preloaded
  > context small enough for the executor model to handle."

  **Acceptance**:
  - All three rules are present in `planner-prompt.md` under a `## Planner Rules` or
    `## Slice Design Rules` heading
  - The existing rules are preserved and numbered consistently

### Phase 5: Trailing comma precision and thinking-model timeout (ISS-007, ISS-008)

Evidence source: `docs/slice-execution-report-v2.md` (2026-03-08 second test run).

---

- [x] TASK-010: Add Rule 14 to `planner-prompt.md` — exact code in context for format-sensitive output [ISS-007]

  **Root cause**: When the `context` field describes a CSV format using a mix of rows with
  and without trailing commas (e.g. `centroid,{cx},{cy}` vs `cov_xx,{v},`), the executor
  generalises the comma pattern to all rows. This is a plausible inference that happens to
  be wrong. Showing exact code eliminates the ambiguity entirely.

  **Changes to `planner-prompt.md`**:
  - Add Rule 14 under the existing numbered rules:
    > "When the `context` field specifies an output format where specific characters
    > (trailing commas, quotes, delimiters) differ between row or field types, show the
    > **exact code** that writes each row — not an abstract placeholder pattern.
    > For Rust: use literal `writeln!` calls. For Python: use literal f-strings or
    > `csv.writer` calls. Never use placeholder notation like `{cx},{cy}` when the
    > executor must infer surrounding punctuation — spell out the complete format string
    > verbatim. Example:
    >
    > **Wrong** (ambiguous): `centroid,{cx},{cy}` / `cov_xx,{v},`
    >
    > **Right** (unambiguous):
    > ```
    > writeln!(file, "centroid,{},{}", centroid.0, centroid.1)?;
    > writeln!(file, "cov_xx,{},", cov[0][0])?;
    > ```"

  **Acceptance**:
  - Rule 14 present in `planner-prompt.md`
  - The rule includes a concrete right/wrong example pair

---

- [x] TASK-011: Streaming API mode in `slicer.py` to survive thinking-model latency [ISS-008]

  **Root cause**: `urllib.request.urlopen(req, timeout=N)` applies `N` as the socket *idle*
  timeout — how long to wait between successive bytes. Thinking models (e.g. qwen3-coder-next)
  generate a long internal chain-of-thought before emitting the first visible token. During
  this phase the server connection is open but silent, triggering a socket timeout even though
  the model will eventually respond correctly.

  With streaming (`stream: true`), the server sends Server-Sent Events (SSE) as it generates
  each token — including thinking tokens. Each SSE chunk resets the idle timer, so the
  connection survives arbitrarily long thinking phases.

  **Changes to `slicer.py`**:

  1. Add `"stream": bool(base.get("stream", False))` to `_resolve_model_config`.
     Update `_CONFIG_HELP` to show `stream = true` (recommended for local thinking models).

  2. Add `_api_request_stream(endpoint, api_key, model, messages, max_tokens, timeout) -> str`:
     - Sets `"stream": true` in the JSON request body
     - Opens the HTTP response with `urllib.request.urlopen(req, timeout=timeout)`
       (timeout now applies per-chunk, not to total response time)
     - Reads response line-by-line; lines starting with `data: ` are parsed as JSON
     - Accumulates `choices[0]["delta"]["content"]` from each non-`[DONE]` chunk
     - Returns the fully assembled content string

  3. Add `stream: bool` parameter to `_api_request`; dispatch to `_api_request_stream`
     when `stream=True`, otherwise use the existing single-request path.

  4. Thread `stream=model_cfg["stream"]` through `_run_executor` → `_api_request`.

  **Acceptance**:
  - `python -m py_compile slicer.py` exits 0
  - Setting `stream = true` in config causes `"stream": true` in the request body
  - Non-streaming path (`stream = false`, the default) is unchanged in behaviour
  - A mock SSE response with multiple `data:` chunks is correctly assembled into one string

### Phase 6: Import style disambiguation (ISS-009)

Evidence source: `docs/slice-execution-report-v3.md` (2026-03-08, Python run).

- [x] TASK-012: Add Rule 15 to `planner-prompt.md` � import style for wiring slices [ISS-009]

  **Root cause**: The executor defaulted to `from . import parser, stats, writer`
  (relative package imports) because the context did not specify the import style.
  Relative imports fail for flat directory layouts run as `python script.py`.

  **Fix**: Rule 15 requires the context of any wiring slice to explicitly state
  whether to use flat imports (`import x`) for same-directory modules or relative
  imports (`from . import x`) for package-structured code.

  **Acceptance**: Rule 15 present in `planner-prompt.md` with both flat/package examples.
