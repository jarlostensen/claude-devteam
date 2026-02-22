---
name: write-tests
description: Write unit tests for a module, function, or class. Reads the source and existing tests first to match conventions. Use immediately after implementing new code.
disable-model-invocation: true
allowed-tools: Read, Write, Grep, Glob
argument-hint: "[file path or module name to test]"
---

# Write Tests

Write unit tests for: **$ARGUMENTS**

## Step 1 — Read the source

Read the file(s) identified in $ARGUMENTS. For each public function, method, or class, note:
- Its name and signature
- What it does (from the implementation and any documentation)
- Its inputs, outputs, and side effects
- Error conditions it can raise or return

## Step 2 — Find existing tests

Locate any existing tests for this code using Glob:
- Look for files matching `**/*.test.*`, `**/*.spec.*`, `**/test_*.py`, etc.
- Look for a `tests/`, `__tests__/`, or `spec/` directory adjacent to or above the source

Read the existing tests to understand:
- The testing framework in use (Jest, pytest, Vitest, Go testing, etc.)
- The file naming convention
- The test structure (`describe`/`it`, `def test_`, etc.)
- Any shared fixtures or setup helpers

If no existing tests are found, establish the testing framework from project configuration files (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, etc.).

## Step 3 — Plan coverage

For each testable unit, plan the test cases:

| Function/method | Happy path | Error/edge cases |
|---|---|---|
| `{name}` | {describe the happy path} | {list edge cases} |

A minimum acceptable test suite covers:
- The happy path for every public function
- At least one error case for every function that can fail
- Boundary conditions (empty input, zero, maximum values, null/None)
- Any behaviour documented in requirements that the function implements

## Step 4 — Write the tests

Write tests following the conventions found in step 2. Place test files in the location that matches the existing convention.

Each test must:
- Have a descriptive name that states WHAT is being tested and WHAT the expected outcome is (not "test_function_1")
- Be independent — no test should depend on the side effects of another
- Have a clear arrange / act / assert (or given / when / then) structure

Do not mock implementation details — test behaviour, not structure. Mock only external dependencies (databases, network calls, file I/O).

## Step 5 — Confirm

After writing, report:
- How many tests were written
- Which functions/methods are now covered
- Any functions that could not be tested without additional setup or fixtures (flag these as coverage gaps)

Tell the user to run `/devteam-tester:run-tests` to verify all new tests pass.
