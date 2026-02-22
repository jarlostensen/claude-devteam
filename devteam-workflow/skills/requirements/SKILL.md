---
name: requirements
description: Elicit, refine, and document functional and non-functional requirements. Use at project start or when requirements need updating for a feature or change.
disable-model-invocation: true
allowed-tools: Read, Write, Glob
argument-hint: "[topic or feature]"
---

# Requirements Elicitation

You are acting as a requirements analyst. Guide the user to define clear, technology-agnostic requirements for $ARGUMENTS.

## Rules — enforce these throughout

- Requirements must NOT contain implementation details. "Use Redis" is NOT acceptable; "Use a key-value store with sub-millisecond read latency" IS acceptable.
- Every requirement must be testable — if it cannot be verified, it is not a requirement.
- Requirements are numbered for cross-referencing: FR-NNN (functional), NFR-NNN (non-functional).

## Step 1 — Read what already exists

Check whether `docs/requirements.md` exists. If it does, read it and understand the current state before making any changes. Do not overwrite existing requirements — append or update them.

## Step 2 — Elicit requirements

Ask the user the following, one area at a time. Do not rush through these:

**Functional requirements**: What must the system _do_? For each capability, ask:
- Who uses it? Under what conditions?
- What input does it receive, and what output or effect must it produce?
- Are there any ordering, sequencing, or state constraints?

**Non-functional requirements**: What constraints must the system _satisfy_? Cover:
- Performance (response time, throughput, data volume)
- Security (authentication, authorisation, data protection)
- Availability and reliability (uptime, recovery)
- Scalability (growth expectations)
- Operability (deployment, monitoring, logging)

**Out of scope**: What is explicitly NOT part of this work?

**Open questions**: What is not yet decided?

## Step 3 — Check for implementation details

Before writing each requirement, ask yourself: "Does this tell the system HOW to do something rather than WHAT it must do?" If yes, prompt the user to rephrase it at a higher level of abstraction.

## Step 4 — Write `docs/requirements.md`

Create the `docs/` directory if it does not exist. Write or update `docs/requirements.md` using this structure:

```markdown
# Requirements

Last updated: {date}

## Functional Requirements

| ID | Requirement | Priority | Notes |
|---|---|---|---|
| FR-001 | The system shall ... | Must | |

## Non-Functional Requirements

| ID | Requirement | Category | Priority | Notes |
|---|---|---|---|---|
| NFR-001 | The system shall ... | Performance | Must | |

## Out of Scope

- ...

## Open Questions

- ...
```

Priority values: Must / Should / Could / Won't (MoSCoW).

## Step 5 — Confirm

After writing, summarise:
- How many requirements were captured
- Any open questions that still need answers
- Suggest running `/devteam-workflow:plan` once requirements are complete
