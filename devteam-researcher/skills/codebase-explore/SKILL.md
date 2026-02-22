---
name: codebase-explore
description: Deeply explore the codebase to map patterns, entry points, key files, and conventions in a specific area. Use before designing a change or implementing in unfamiliar code.
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
argument-hint: "[area or topic to explore, e.g. 'authentication', 'database layer', 'API endpoints']"
---

# Codebase Exploration

Explore the codebase focused on: **$ARGUMENTS**

Produce a structured map that gives a developer everything they need to work in this area without getting lost. Be specific — file paths and line numbers are more useful than generalities.

## Step 1 — Locate the area

Use Glob patterns to find files related to $ARGUMENTS. Try multiple patterns:
- By directory name (e.g. `**/auth/**`, `**/db/**`)
- By filename convention (e.g. `**/*.repository.*`, `**/*.service.*`)
- By content (use Grep for key terms from the topic)

## Step 2 — Map the entry points

Identify:
- The primary entry points (the files a developer would open first)
- Public interfaces or contracts (exported functions, classes, API handlers)
- Configuration files that affect this area

## Step 3 — Understand the patterns

Read the key files. Identify:
- The dominant architectural pattern in this area (e.g. repository pattern, MVC, event-driven)
- Naming conventions used (file names, function names, variable names)
- Error handling approach (exceptions, result types, error codes?)
- How dependencies are injected or wired together
- Any notable abstractions or base classes

## Step 4 — Find the tests

Locate test files for this area. Note:
- Where tests live relative to source files
- The testing framework in use
- Approximate coverage (many tests / few tests / none visible)

## Step 5 — Identify integration points

What does this area depend on? What depends on this area?
- Upstream: what does it call or consume?
- Downstream: what calls into it?
- External: any third-party APIs, databases, queues?

## Step 6 — Flag anything unusual

Note anything that deviates from expected patterns, appears to be legacy code, has a TODO or FIXME comment, or looks like it needs attention.

## Output

```
## Codebase Map: {topic}

### Entry points
| File | Purpose |
|---|---|
| `path/to/file.ts:NN` | {one-line description} |

### Key files
| File | Role |
|---|---|
| `path/to/file.ts` | {one-line description} |

### Patterns in use
- **Architecture**: {pattern name and brief description}
- **Naming**: {conventions observed}
- **Error handling**: {approach}
- **Dependency wiring**: {approach}

### Tests
- Location: `{path pattern}`
- Framework: {framework name}
- Coverage impression: {Good / Sparse / None visible}

### Integration points
- Depends on: {list}
- Depended on by: {list}
- External: {list}

### Conventions to follow when making changes
1. {Specific convention — e.g. "Use the Repository interface; do not call the DB directly"}
2. {Specific convention}

### Things to be aware of
- {Any gotchas, legacy debt, or unusual patterns}
```
