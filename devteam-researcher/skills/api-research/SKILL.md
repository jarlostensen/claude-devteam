---
name: api-research
description: Research an API or library before it is used in code. Verifies documentation, presents version options for user selection, and assesses suitability. Use whenever an external dependency is being considered.
context: fork
agent: researcher
allowed-tools: Read, Grep, Glob, WebSearch, WebFetch
argument-hint: "[library or API name and intended use]"
---

# API Research

Research the API or library: **$ARGUMENTS**

Produce a structured research report. Do not assume anything — verify every claim against current documentation. Do not select a version — present the options clearly so the user can decide.

## Step 1 — Check existing project usage

Before researching externally, search the codebase:
- Use Grep to find any existing imports or references to this library
- Check `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, or equivalent for any current version pin
- Check `docs/adr/` for any prior decision involving this library

Report what is already in use. If the project already pins a version, note it — a version change may require a migration.

## Step 2 — Identify what to research

Parse $ARGUMENTS to extract:
- The library or API name
- The intended use case (if provided)

If the intended use is not clear, infer it from the name and proceed with a general assessment.

## Step 3 — Map the available versions

This is the most important step. Do not default to "the latest version". Identify all version lines currently available:

Search for:
- All major version lines currently receiving updates or support (e.g. v2.x LTS, v3.x stable, v4.x beta)
- Each version's release date, latest patch, and stated support/EOL window
- What changed between major versions — breaking changes, removed APIs, new required migrations
- Whether each version has known CVEs or security advisories outstanding

Use WebSearch:
- `"{library}" versions support schedule`
- `"{library}" v{N} vs v{N+1} breaking changes migration`
- `"{library}" LTS OR "long-term support"`

## Step 4 — Official documentation

Fetch the official documentation homepage. Extract:
- Core concepts and terminology
- Primary usage patterns relevant to the intended use
- Any known limitations or caveats called out in the docs
- Authentication and authorisation model (for APIs)
- Rate limits, quotas, or pricing (for APIs)

## Step 5 — Integration assessment

Assess:
- **Ease of integration**: Is there a well-maintained client library for the likely implementation language?
- **Dependency footprint**: Does it pull in many transitive dependencies?
- **Community health**: Stack Overflow presence, Discord/Slack activity, third-party tutorials

## Step 6 — Licensing

State the licence clearly. Flag any licence that restricts commercial use, requires source disclosure, or conflicts with common project licences (MIT, Apache-2.0). Note whether the licence differs between version lines.

## Step 7 — Alternatives

Name 1–2 alternatives that serve the same purpose, in one sentence each.

## Output

```
## API Research Report: {library or API name}

**Assessed for**: {intended use}
**Date**: {today's date}
**Currently in project**: {version string, or "Not currently used"}

### Overall status
- Maintenance: {Active / Stale / Deprecated}
- Licence: {licence}

### Summary
{2–3 sentence plain-English overview of the library and its fitness for the intended use}

### Version options

| Version line | Latest patch | Status | Support until | Notes |
|---|---|---|---|---|
| v{N}.x | {version} | Current stable | {date or TBD} | {e.g. "Recommended for new projects"} |
| v{N-1}.x | {version} | LTS | {date} | {e.g. "No new features; security fixes only"} |
| v{N+1}.x | {version} | Beta / RC | {date} | {e.g. "Not production-ready"} |

**Breaking changes between versions**:
- v{N-1} → v{N}: {summary of breaking changes, or "None significant"}

**Version selection considerations**:
- Choose v{N-1}.x (LTS) if: {e.g. stability is critical, existing integrations depend on v{N-1} APIs, support window aligns with your project lifecycle}
- Choose v{N}.x (stable) if: {e.g. starting a new project, you need {specific feature}, team is comfortable with the migration}
- Avoid v{N+1}.x unless: {e.g. you specifically need {feature} and can accept pre-release risk}

### Key findings

**Documentation quality**: {Good / Adequate / Poor} — {one sentence}
**Integration complexity**: {Low / Medium / High} — {one sentence}
**Breaking change risk (upgrading later)**: {Low / Medium / High} — {one sentence}
**Dependency footprint**: {Light / Moderate / Heavy} — {one sentence}

### Relevant usage patterns
{Bullet list of patterns directly relevant to the intended use}

### Known limitations or caveats
{Bullet list — include anything the official docs flag as limitations}

### Licence summary
{Plain-English summary. Note any version-line differences.}

### Alternatives
- {Alternative 1}: {one sentence}
- {Alternative 2}: {one sentence}

### Sources
- {URL}
- {URL}

---

**Please select a version to proceed with.**
Consider team familiarity, existing project usage, support window, and the breaking change notes above.
Once decided, record the choice with `/devteam-architect:adr`.
```
