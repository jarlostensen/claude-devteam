---
name: library-check
description: Compare candidate libraries for a given purpose and produce a suitability matrix. Presents options for the user to choose from — does not make the selection. Use when choosing between multiple libraries before committing to a dependency.
context: fork
agent: researcher
allowed-tools: Read, Grep, Glob, WebSearch, WebFetch
disable-model-invocation: true
argument-hint: "[purpose] [lib1] [lib2] [lib3...]"
---

# Library Comparison

Compare candidate libraries for: **$ARGUMENTS**

Parse $ARGUMENTS as: the first phrase describes the purpose; subsequent words or comma-separated names are the candidate libraries.

If fewer than 2 candidates are named, search for the most commonly used libraries for the stated purpose and select the top 3 to compare.

Produce a comparison that informs the user's decision. Do not make the selection — that is the user's call.

## Step 1 — Check existing project conventions

Before researching externally:
- Search the codebase for any libraries already used for similar purposes (Grep for related import patterns)
- Check `docs/adr/` for any prior library decision in this area
- Note any established patterns — consistency with what is already in the project is a valid reason to prefer one option over another

Report any existing conventions found. They should carry weight in the comparison.

## Step 2 — Read project requirements

Check whether `docs/requirements.md` exists and read it. Identify any NFRs relevant to the library choice (e.g. performance thresholds, licence constraints, security requirements).

## Step 3 — Research each candidate

For each library:
- Current stable version, release date, maintenance status
- Licence
- Key capabilities relevant to the stated purpose
- Known limitations
- Community health indicators

Use WebSearch for each: `"{library}" site:github.com` and `"{library}" documentation`.

## Step 4 — Score against criteria

Score each library per criterion: High / Medium / Low.

| Criterion | Why it matters |
|---|---|
| Feature fit | Does it cover the required capability? |
| API ergonomics | How much boilerplate does it require? |
| Performance | Relevant if NFRs specify throughput or latency |
| Bundle size / footprint | Relevant for client-side or resource-constrained environments |
| Maintenance health | Is it actively maintained? |
| Licence compatibility | Does the licence permit commercial use? |
| Documentation quality | Can a developer be productive quickly? |
| Community size | Is help available when needed? |
| Project consistency | Does it match patterns already in use in this codebase? |

## Step 5 — Identify disqualifiers

Flag any library that:
- Is deprecated or unmaintained
- Has a licence incompatible with typical commercial projects
- Has a known critical vulnerability with no patch
- Fails to meet a Must-priority NFR

A disqualified library should be called out clearly — it may still appear in the table for completeness but should be marked as disqualified.

## Output

```
## Library Comparison: {purpose}

**Date**: {today's date}
**Existing project conventions**: {what is already in use, or "None found"}

### Candidates assessed
{List each library with current stable version and licence}

### Suitability matrix

| Criterion | {Lib 1} | {Lib 2} | {Lib 3} |
|---|---|---|---|
| Feature fit | H/M/L | H/M/L | H/M/L |
| API ergonomics | H/M/L | H/M/L | H/M/L |
| Performance | H/M/L | H/M/L | H/M/L |
| Footprint | H/M/L | H/M/L | H/M/L |
| Maintenance health | H/M/L | H/M/L | H/M/L |
| Licence compatibility | H/M/L | H/M/L | H/M/L |
| Documentation quality | H/M/L | H/M/L | H/M/L |
| Community size | H/M/L | H/M/L | H/M/L |
| Project consistency | H/M/L | H/M/L | H/M/L |

### Disqualifiers
{List any library disqualified and why, or "None"}

### Summary for selection

{Lib 1} — {one sentence: what it is strongest at and its main weakness}
{Lib 2} — {one sentence: what it is strongest at and its main weakness}
{Lib 3} — {one sentence: what it is strongest at and its main weakness}

**Factors not captured in the matrix to consider**:
- Team familiarity with any of these libraries
- Organisational standards or prior experience
- Any preference for minimising new dependencies
- Whether an existing library in the project could be extended instead

### Sources
- {URL}
- {URL}

---

**Please select a library.**
This comparison informs your decision — it does not make it. Consider the matrix, the existing project conventions, and your own preferences.

Once you have selected a library, run `/devteam-researcher:api-research [chosen library] for [purpose]` to research version options before committing to a specific version, then `/devteam-architect:adr` to record the decision.
```
