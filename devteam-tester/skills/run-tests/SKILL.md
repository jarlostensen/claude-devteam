---
name: run-tests
description: Run the project test suite and return only failures with context. Keeps verbose test output out of the main conversation. Use after implementing or changing code.
context: fork
agent: test-runner
allowed-tools: Bash, Read, Glob
disable-model-invocation: true
---

# Run Tests

Run the full test suite and report results.

## Step 1 — Find the test command

Look for the test command in this order:
1. `docs/task-plan.md` — the plan should have a "Test command" section
2. `package.json` `scripts.test` field
3. `pyproject.toml` `[tool.pytest.ini_options]` or `Makefile` test target
4. `Cargo.toml` (use `cargo test`)
5. `go.mod` (use `go test ./...`)
6. `Makefile` — look for a `test` target

If no test command can be found, report the failure and list what was checked.

## Step 2 — Run tests

Execute the test command. Capture all output.

## Step 3 — Parse results

From the raw output, extract:

**Summary**: `{N} passed, {N} failed, {N} skipped` (use the framework's own summary line where possible)

**For each failure**:
- Test name / test identifier
- The assertion that failed (expected vs actual, if shown)
- The relevant lines of the stack trace (not the full trace — just the lines pointing to the test and the source under test)
- Any error message

**Setup or infrastructure errors** (e.g. missing dependency, database connection refused): report these separately before test results.

## Step 4 — Output

Return ONLY:

```
## Test Results

**Summary**: {N} passed | {N} failed | {N} skipped
**Command**: `{command run}`

### Failures

#### {Test name}
```
{assertion failure or error message}
{relevant stack trace lines}
```

### Infrastructure errors
{Any setup errors that prevented tests from running, or "None"}
```

Do not return passing test output. If all tests pass, return only:

```
## Test Results

All {N} tests passed.
**Command**: `{command run}`
```
