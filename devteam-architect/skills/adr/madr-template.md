# MADR Template

Markdown Architectural Decision Records (MADR) — version 3.x

Copy the template below. Replace all `{placeholder}` text. Do not leave placeholder text in the final ADR.

---

```markdown
---
status: {proposed | accepted | deprecated | superseded by [ADR-NNNN](NNNN-title.md)}
date: {YYYY-MM-DD}
deciders: {list everyone involved in the decision}
consulted: {list everyone whose opinions were sought}
informed: {list everyone kept up-to-date on progress}
---

# {Short noun phrase — what was decided, not why}

## Context and Problem Statement

{Describe the context and problem that required a decision. 2–4 sentences.
Why does this decision need to be made? What happens without it?}

## Decision Drivers

* {requirement ID or constraint — e.g. FR-001, NFR-002}
* {another driver — e.g. KISS principle, existing ADR-NNNN}

## Considered Options

* {Option 1 — short name}
* {Option 2 — short name}
* {Option 3 — short name, use "Do nothing" if applicable}

## Decision Outcome

Chosen option: "{option name}", because {justification in one or two sentences. Reference decision drivers.}

### Positive Consequences

* {positive consequence — e.g. "Satisfies NFR-001 with margin"}
* {positive consequence}

### Negative Consequences

* {negative consequence — e.g. "Increases operational complexity"}
* {negative consequence}

## Pros and Cons of the Options

### {Option 1}

{One-sentence description}

* Good, because {argument — tie to a decision driver where possible}
* Good, because {argument}
* Bad, because {argument}
* Bad, because {argument}

### {Option 2}

{One-sentence description}

* Good, because {argument}
* Bad, because {argument}
* Bad, because {argument}

### {Option 3}

{One-sentence description}

* Good, because {argument}
* Bad, because {argument}

## More Information

{Optional. Links to related ADRs, design documents, external references, or RFCs that informed the decision.}
```

---

## Status values

| Status | Meaning |
|---|---|
| `proposed` | Under consideration; not yet agreed |
| `accepted` | Agreed and in effect |
| `deprecated` | No longer recommended; superseded or obsolete |
| `superseded by ADR-NNNN` | Replaced by a later decision |

## Naming convention

Files are named `NNNN-short-title.md` where:
- `NNNN` is a zero-padded four-digit sequence number
- `short-title` is a kebab-case summary of the decision (not the problem)

Examples:
- `0001-use-event-driven-architecture.md`
- `0002-store-sessions-in-database.md`
- `0003-adopt-openapi-for-api-contracts.md`
