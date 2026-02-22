---
name: api-research
description: Research an API or library before it is used in code. Verifies current documentation, version status, and integration patterns. Use whenever an external dependency is being considered.
context: fork
agent: researcher
allowed-tools: Read, Grep, Glob, WebSearch, WebFetch
argument-hint: "[library or API name and intended use]"
---

# API Research

Research the API or library: **$ARGUMENTS**

Produce a structured suitability report. Do not assume anything — verify every claim against current documentation.

## Step 1 — Identify what to research

Parse $ARGUMENTS to extract:
- The library or API name
- The intended use case (if provided)

If the intended use is not clear, infer it from the name and proceed with a general assessment.

## Step 2 — Current version and status

Search for:
- Current stable version and release date
- Release cadence (actively maintained or stale?)
- Known deprecation or end-of-life announcements
- Number of open issues and recent commit activity (check GitHub or equivalent)

Use WebSearch with queries like:
- `"{library name}" latest version 2025`
- `"{library name}" deprecation OR "end of life" OR abandoned`
- `site:github.com {library name} releases`

## Step 3 — Official documentation

Fetch the official documentation homepage. Extract:
- Core concepts and terminology
- Primary usage patterns relevant to the intended use
- Any known limitations or caveats called out in the docs
- Authentication and authorisation model (for APIs)
- Rate limits, quotas, or pricing (for APIs)

## Step 4 — Integration assessment

Assess:
- **Ease of integration**: Is there a well-maintained client library for the likely implementation language?
- **Breaking changes**: Have there been recent breaking changes? Are migration guides available?
- **Dependency footprint**: Does it pull in many transitive dependencies?
- **Community health**: Stack Overflow presence, Discord/Slack activity, third-party tutorials

## Step 5 — Licensing

State the licence clearly. Flag any licence that restricts commercial use, requires source disclosure, or conflicts with common project licences (MIT, Apache-2.0).

## Step 6 — Alternatives

Name 1–2 alternatives that serve the same purpose, in one sentence each. This gives context for the decision.

## Output

```
## API Research Report: {library or API name}

**Assessed for**: {intended use}
**Date**: {today's date}

### Status
- Current version: {version} ({release date})
- Maintenance: {Active / Stale / Deprecated}
- Licence: {licence}

### Summary
{2–3 sentence plain-English verdict: is this suitable for the intended use?}

### Key findings

**Documentation quality**: {Good / Adequate / Poor} — {one sentence}
**Integration complexity**: {Low / Medium / High} — {one sentence}
**Breaking change risk**: {Low / Medium / High} — {one sentence}
**Dependency footprint**: {Light / Moderate / Heavy} — {one sentence}

### Relevant usage patterns
{Bullet list of patterns directly relevant to the intended use}

### Known limitations or caveats
{Bullet list — include anything the official docs flag as limitations}

### Licence summary
{Plain-English summary of what the licence permits and restricts}

### Alternatives considered
- {Alternative 1}: {one sentence}
- {Alternative 2}: {one sentence}

### Sources
- {URL}
- {URL}

### Verdict
{SUITABLE / SUITABLE WITH CAVEATS / NOT SUITABLE} — {one sentence justification}
```

If the verdict is "NOT SUITABLE" or "SUITABLE WITH CAVEATS", state clearly what would need to be true for it to become suitable.
