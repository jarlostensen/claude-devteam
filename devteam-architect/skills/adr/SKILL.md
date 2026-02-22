---
name: adr
description: Generate a MADR-format Architecture Decision Record from a design decision. Use after a design session to formally document the decision before implementation begins.
disable-model-invocation: true
allowed-tools: Read, Write, Glob
argument-hint: "[short decision title]"
---

# Architecture Decision Record

Generate an ADR in MADR (Markdown Architectural Decision Records) format for the decision: $ARGUMENTS

## Step 1 — Find the next ADR number

List all files in `docs/adr/`. ADRs are named `NNNN-title.md`. Find the highest existing number and increment by 1. If the directory is empty or does not exist, start at `0001`.

Create `docs/adr/` if it does not exist.

## Step 2 — Gather the decision content

Read the most recent design note in `docs/design/` related to $ARGUMENTS. If no design note exists, ask the user to describe:
- What decision was made
- What options were considered and why they were rejected
- What requirements or constraints drove the decision

Also read `docs/requirements.md` to identify which requirement IDs this decision addresses.

## Step 3 — Fill in and write the ADR

Load the template from [madr-template.md](madr-template.md). Populate every section — do not leave placeholder text. Write the completed ADR to `docs/adr/NNNN-{kebab-case-title}.md`.

Use today's date in `YYYY-MM-DD` format. Set the initial status to `proposed` unless the user confirms it is already agreed, in which case use `accepted`.

## Step 4 — Confirm

Tell the user the filename and ADR number. Suggest that if any options or consequences remain uncertain, `/devteam-architect:design-review` can provide independent critique before the ADR status is moved to `accepted`.

## Additional resources

- For full MADR specification and examples, see [madr-template.md](madr-template.md)
