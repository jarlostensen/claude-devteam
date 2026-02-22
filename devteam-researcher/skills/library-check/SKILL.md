---
name: library-check
description: Compare candidate libraries for a given purpose and produce a suitability matrix to support a decision. Use when choosing between multiple options before committing to a dependency.
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

## Step 1 — Read project requirements

Check whether `docs/requirements.md` exists and read it. Identify any NFRs that are relevant to the library choice (e.g. performance thresholds, licence constraints, security requirements).

## Step 2 — Research each candidate

For each library, run the same research as `api-research` would:
- Current version, release date, maintenance status
- Licence
- Key capabilities relevant to the stated purpose
- Known limitations
- Community health indicators

Use WebSearch for each: `"{library}" vs alternatives {current year}` and the library's own documentation.

## Step 3 — Score against criteria

Define evaluation criteria based on the stated purpose and any relevant NFRs. Typical criteria:

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

Score each library per criterion: High / Medium / Low.

## Step 4 — Identify disqualifiers

Flag any library that:
- Is deprecated or unmaintained
- Has a licence incompatible with typical commercial projects
- Has a known critical vulnerability with no patch
- Fails to meet a Must-priority NFR

A disqualified library should be called out clearly — it may still appear in the table for completeness but should be marked as such.

## Output

```
## Library Comparison: {purpose}

**Date**: {today's date}

### Candidates assessed
{List each library with current version and licence}

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

### Disqualifiers
{List any library disqualified and why, or "None"}

### Recommendation
**Recommended**: {library name}

{2–3 sentence justification — tie it to the criteria and any relevant requirements}

**Runner-up**: {library name} — {one sentence on when this would be preferred instead}

### Sources
- {URL}
- {URL}
```

After producing the report, note: use `/devteam-architect:adr` to record the final library choice as an Architecture Decision Record.
