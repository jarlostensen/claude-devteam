---
name: lang-review
description: Deep language-specialist code review. Detects Go and Python in the changed files, spawns a specialist agent per language in parallel alongside the general code-reviewer, then synthesizes findings with cross-language conflict analysis.
allowed-tools: Read, Glob, Grep, Bash(git *), Agent
argument-hint: "[commit range or file paths, or leave blank for HEAD~1]"
---

# Language-Specialist Code Review

You are orchestrating a parallel code review. A general quality reviewer and up to two language specialists each review the same changes in isolation. You then synthesize their findings and flag any cross-language issues.

## Step 1 — Establish the diff scope

Determine the changed files:
- If `$ARGUMENTS` specifies a commit range or file paths, use that
- Otherwise run `git diff HEAD~1 --stat` to list changed files

Note the full list of changed file paths. You will use this to decide which specialist agents to spawn.

Also read `docs/requirements.md` and `docs/task-plan.md` if they exist — pass their paths to agents.

## Step 2 — Detect languages present in the diff

From the changed file list:
- **Go present**: any file ending in `.go` (excluding `_test.go`-only changes — still include, Go test patterns matter)
- **Python present**: any file ending in `.py`

Note which languages are present. If neither Go nor Python is in the diff, report:

> "No Go or Python files changed — use `/devteam-reviewer:code-review` for the general quality review."

and stop.

## Step 3 — Spawn reviewers in parallel

In a single response, launch all applicable agents simultaneously using the Agent tool. Do not wait for one before starting the next.

**Always spawn** the general code-reviewer:
- `subagent_type: "devteam-reviewer:code-reviewer"`
- Prompt: "Review the code changes in scope: `$ARGUMENTS` (or HEAD~1 if blank). Read docs/requirements.md and docs/task-plan.md if they exist. Follow your standard review checklist covering correctness, standards adherence, documentation, tests, and requirements coverage. Return your full structured report."

**If Go is present**, spawn the Go specialist:
- `subagent_type: "devteam-reviewer:go-specialist"`
- Prompt: "Review the Go files changed in: `$ARGUMENTS` (or HEAD~1 if blank). Run `git diff HEAD~1` and filter to `.go` files. Read each changed file in full. Apply your Go-specific checklist: concurrency, context handling, error handling, interfaces, memory/performance, module hygiene, and testing. Return your full structured report."

**If Python is present**, spawn the Python specialist:
- `subagent_type: "devteam-reviewer:python-specialist"`
- Prompt: "Review the Python files changed in: `$ARGUMENTS` (or HEAD~1 if blank). Run `git diff HEAD~1` and filter to `.py` files. Read each changed file in full. Apply your Python-specific checklist: type annotations, async correctness, exception handling, resource management, Pythonic idioms, import hygiene, packaging, and testing. Return your full structured report."

## Step 4 — Identify cross-language issues

Before writing the synthesis, examine findings from all agents together. Look specifically for issues that arise from Go and Python code interacting — these are invisible to single-language reviewers:

- **Serialisation contract mismatches**: Go struct tags (`json:"field_name"`) vs Python dict keys or Pydantic field names — any field that is snake_case on one side and camelCase on the other without explicit mapping
- **Null / None / zero-value divergence**: Go zero values (`""`, `0`, `false`) silently used where Python expects `None`; Go `omitempty` dropping fields Python code expects to always be present
- **Error representation**: Go returning `{"error": "..."}` vs Python expecting a typed exception structure or HTTP status code convention
- **Async boundary assumptions**: Go goroutine-based concurrency producing results that Python async code consumes — check that backpressure and cancellation signals are compatible
- **Integer width**: Go `int` is 64-bit on modern platforms; Python `int` is arbitrary precision — flag cases where the boundary passes numbers that could overflow on one side

## Step 5 — Write the synthesis report

```
## Language Review

**Scope**: {commit range or files reviewed}
**Languages**: {Go / Python / Go + Python}
**Task**: {TASK-NNN from task plan, or "Not identified"}

---

### Cross-language issues
{The most important section when both languages are present. Issues arising from Go/Python interaction.}

| Issue | Files affected | Resolution needed |
|---|---|---|
| {description} | {files} | {what must be fixed} |

If only one language is present or no cross-language issues found: "Not applicable." or "None identified."

---

### General quality findings
{Full output from the code-reviewer agent.}

---

### Go findings
{Full output from the go-specialist agent, or "Not applicable — no Go files in this diff."}

---

### Python findings
{Full output from the python-specialist agent, or "Not applicable — no Python files in this diff."}

---

### Combined verdict

| Reviewer | Verdict |
|---|---|
| General quality | Ready / Minor issues / Blocking issues |
| Go specialist | Clean / Minor issues / Blocking issues / N/A |
| Python specialist | Clean / Minor issues / Blocking issues / N/A |
| Cross-language | None identified / Issues present / N/A |
```

End with one of:
- "Ready to merge." (no Critical Issues from any reviewer, no cross-language issues)
- "Merge after addressing Critical Issues." (Critical Issues present in any reviewer's report)
