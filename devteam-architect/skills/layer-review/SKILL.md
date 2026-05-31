---
name: layer-review
description: Run parallel domain-specialist reviews of a design across C++/client, cloud infrastructure, and AI/ML layers, then synthesize into a unified cross-layer report. Use when a design spans multiple technical domains.
argument-hint: "[path to design doc or ADR, or leave blank for most recent]"
---

# Layer Review

You are orchestrating a parallel domain-specialist design review. Three specialist agents each review the design from a single domain perspective in isolation. You then synthesize their findings, with particular focus on cross-layer conflicts that no single-domain reviewer can catch.

## Step 1 — Locate the design document

If $ARGUMENTS specifies a path, use that. Otherwise, list `docs/design/` and `docs/adr/` and select the most recently modified file across both directories. Read it now and note its absolute path.

Also check whether `docs/requirements.md` exists — note its path for use in agent prompts.

## Step 2 — Determine which layers are relevant

Skim the design. Identify which of the three layers it touches:

- **C++ / Client**: any native binary, client library, SDK, embedded component, or performance-critical path
- **Cloud / Infra**: any service, API endpoint, deployment, database, queue, or network boundary
- **AI / ML**: any model inference, training pipeline, LLM integration, or evaluation workflow

Skip any layer the design has no content for — note it as "not applicable" in the final report.

## Step 3 — Spawn specialist reviews in parallel

In a single response, use the Agent tool to launch all applicable specialist agents simultaneously. Do not wait for one to finish before starting the next.

For each specialist, pass a self-contained prompt with:
- The full absolute path to the design document
- The path to `docs/requirements.md` if it exists
- The path to `docs/adr/` if it exists
- Their specific mandate (copy the mandate text below verbatim)

### C++ / Client agent
- subagent_type: `devteam-architect:cpp-specialist`
- Mandate: "Review the design document at {path}. Read docs/requirements.md and all files in docs/adr/ for context. Produce a structured review covering: API contracts and ABI stability, memory management and ownership at boundaries, threading model and concurrency safety, performance on hot paths, build system implications, and cross-platform assumptions. Follow your output format exactly."

### Cloud / Infrastructure agent
- subagent_type: `devteam-architect:cloud-specialist`
- Mandate: "Review the design document at {path}. Read docs/requirements.md and all files in docs/adr/ for context. Produce a structured review covering: service topology and boundaries, failure modes and recovery paths for every component, scalability and cost model, state management and data durability, observability strategy, security and trust boundaries, and deployment and rollback approach. Follow your output format exactly."

### AI / ML agent
- subagent_type: `devteam-architect:ai-specialist`
- Mandate: "Review the design document at {path}. Read docs/requirements.md and all files in docs/adr/ for context. Produce a structured review covering: inference serving architecture and latency/throughput budgets, model versioning and rollout strategy, evaluation pipeline and acceptance criteria, data pipeline and production feedback loops, compute requirements, context/token management for LLM components, output failure modes and fallbacks, and production monitoring for drift. Follow your output format exactly."

## Step 4 — Identify cross-layer conflicts

Before writing the synthesis, examine the findings from all specialists together and look for conflicts between layers. These are the highest-value findings — no single specialist can see them. Examples:

- C++ layer assumes synchronous blocking calls; cloud layer requires async messaging
- Cloud layer expects stateless services; C++ layer implies in-process state shared across requests
- AI layer requires GPU co-location; cloud layer assumes commodity nodes
- C++ API contract is version-locked; cloud layer needs independent deployment cadence

## Step 5 — Write the synthesis report

```
## Layer Review: {design title}
Date: {today's date}

### Cross-layer summary
{2-3 sentences. Is the design coherent across layers, or do specialist findings expose mismatches?}

### Cross-layer conflicts
{The most important section. Issues where one layer's design contradicts or creates hidden assumptions for another.}

| Conflict | Layers affected | Resolution needed |
|---|---|---|
| {description} | C++ / Cloud / AI | {what must be decided} |

If none found: "No cross-layer conflicts identified."

### C++ / Client findings
{Paste the full output from the cpp-specialist agent, or "Not applicable — no C++ layer in this design."}

### Cloud / Infrastructure findings
{Paste the full output from the cloud-specialist agent, or "Not applicable — no cloud layer in this design."}

### AI / ML findings
{Paste the full output from the ai-specialist agent, or "Not applicable — no AI/ML layer in this design."}

### Layer coverage
| Layer | Applicable | Verdict |
|---|---|---|
| C++ / Client | Yes / No | {one-sentence specialist verdict, or N/A} |
| Cloud / Infra | Yes / No | {one-sentence specialist verdict, or N/A} |
| AI / ML | Yes / No | {one-sentence specialist verdict, or N/A} |
```

End with one of:
- "Design is consistent across layers. Run `/devteam-architect:design-review` for full architectural critique."
- "Cross-layer conflicts require resolution before proceeding to `/devteam-architect:design-review`."
