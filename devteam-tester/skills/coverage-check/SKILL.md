---
name: coverage-check
description: Analyse test coverage to identify untested code paths. Tries to run a coverage tool if configured; falls back to static analysis. Use to find gaps before a task is marked complete.
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, Bash
argument-hint: "[module or directory to check, or leave blank for full project]"
---

# Coverage Check

Analyse test coverage for: **$ARGUMENTS** (or the full project if blank)

## Step 1 — Try to run a coverage tool

Check whether a coverage tool is configured:
- Python: `coverage.py` (`.coveragerc`, `pyproject.toml [tool.coverage]`), or `pytest --cov`
- JavaScript/TypeScript: `jest --coverage`, `vitest --coverage`, `c8`, `nyc`
- Go: `go test -cover ./...`
- Rust: `cargo tarpaulin` or `cargo llvm-cov`

If a tool is found and can be run, execute it and extract:
- Overall coverage percentage
- Files or modules below a reasonable threshold (e.g. < 80%)
- Specific uncovered lines in those files

If a tool is available but fails to run (missing configuration, build error), report the failure and fall through to static analysis.

## Step 2 — Static analysis (fallback or supplement)

If no coverage tool is available or Step 1 produced incomplete results, perform static analysis:

**Find all source files** in the scope of $ARGUMENTS using Glob.

**Find all test files** using Glob patterns (`*.test.*`, `*.spec.*`, `test_*.py`, `*_test.go`, etc.).

**Map source files to test files**:

| Source file | Test file | Status |
|---|---|---|
| `src/auth/login.ts` | `src/auth/login.test.ts` | Covered |
| `src/auth/session.ts` | *(none found)* | No tests |

**For files with no corresponding test**, read the source and list the public functions or methods that have no test coverage.

## Step 3 — Output

```
## Coverage Check: {scope}

### Tool-based results
{Coverage percentage and per-file breakdown if a tool was run, or "No coverage tool found/run"}

### Files with no test coverage
| Source file | Untested public functions |
|---|---|
| `path/to/file` | `functionA`, `functionB` |

### Files with low coverage (< 80%)
| File | Coverage | Key untested paths |
|---|---|---|
| `path/to/file` | {N}% | {description} |

### Summary
{N} source files checked. {N} fully covered, {N} partially covered, {N} with no coverage.

### Recommended actions
1. {Most impactful gap to address first}
2. {Next gap}
```

If coverage is complete or close to complete, say so clearly.
