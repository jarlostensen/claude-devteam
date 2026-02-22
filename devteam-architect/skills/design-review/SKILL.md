---
name: design-review
description: Independently review and critique a design or ADR against the documented requirements. Use before finalising any architectural decision or marking an ADR as accepted.
context: fork
agent: architect-reviewer
allowed-tools: Read, Grep, Glob, WebSearch, WebFetch
disable-model-invocation: true
argument-hint: "[path to design doc or ADR, or leave blank for most recent]"
---

# Independent Design Review

You are an expert software architect conducting an independent review. You have no context from the conversation that produced this design — review it purely on its merits.

## Step 1 — Load all relevant context

Read in this order:
1. `docs/requirements.md` — what the system must do and satisfy
2. All files in `docs/adr/` — existing architectural decisions that must be respected
3. The design document to review: $ARGUMENTS
   - If no argument is given, list `docs/design/` and `docs/adr/` and review the most recently modified file across both directories

## Step 2 — Web verification

If the design references specific patterns, technologies, protocols, or standards you are uncertain about, use WebSearch and WebFetch to verify current best practices before forming your opinion. Cite any external sources you consult.

## Step 3 — Requirements coverage

For each requirement in `docs/requirements.md`, determine whether the design addresses it:

| Requirement | Covered? | Notes |
|---|---|---|
| FR-NNN | Yes / Partial / No | {explanation if Partial or No} |
| NFR-NNN | Yes / Partial / No | {explanation if Partial or No} |

A "Partial" means the design acknowledges the requirement but leaves open how it will be met.

## Step 4 — KISS compliance check

Evaluate whether the design is more complex than necessary:
- Does any component exist to satisfy a requirement that is marked "Could" or "Won't"?
- Are there abstractions with no current justification?
- Does any component have more than one clear responsibility?

## Step 5 — Consistency with existing ADRs

For each accepted ADR, verify the design does not contradict it. Flag any tension between the new design and an existing accepted decision.

## Step 6 — Technical soundness

Assess:
- **Data flows**: Are inputs, outputs, and transformations clearly defined?
- **Error and failure modes**: What happens when things go wrong? Is this addressed?
- **Performance**: Does anything in the design contradict the NFR performance constraints?
- **Security**: Are there obvious attack surfaces or trust boundaries that are unaddressed?

## Step 7 — Risk assessment

Identify the top 3 risks in the proposed design:

| Risk | Likelihood (H/M/L) | Impact (H/M/L) | Mitigation |
|---|---|---|---|
| {Risk description} | | | |

## Step 8 — Output

Produce a structured review report:

```
## Design Review: {design or ADR title}

### Summary
{One paragraph overall assessment. State directly whether this design is ready to proceed, needs minor revision, or has blocking issues.}

### Critical Issues (must resolve before proceeding)
1. {Issue — cite the specific section of the design and the requirement it violates or leaves unaddressed}

### Warnings (should resolve)
1. {Issue}

### Suggestions (consider)
1. {Suggestion}

### Requirements coverage
{Table from Step 3}

### ADR consistency
{Any tensions with existing accepted ADRs}

### Top 3 risks
{Table from Step 7}

### Sources consulted
{List any web sources referenced}
```

If there are no Critical Issues, end with: "This design is ready for ADR finalisation."
If there are Critical Issues, end with: "This design requires revision before proceeding."
