---
name: task-status
description: Check whether the current conversation is aligned with the task plan and requirements. Invoke silently when work appears to drift from the documented plan, when a new topic is introduced without a corresponding task, or when an implementation detail is discussed that contradicts a requirement.
user-invocable: false
allowed-tools: Read
---

# Task Status Check

Read `docs/task-plan.md` and `docs/requirements.md` if they exist.

Compare what is currently being discussed or implemented against the plan and requirements.

## Situations that warrant a comment

Speak up only if ONE of these is true:

1. **Unplanned work**: The current work has no corresponding task in the task plan. Briefly note: "This doesn't appear in the task plan — should we add TASK-NNN for this before proceeding?"

2. **Requirement contradiction**: A proposed approach contradicts a documented requirement. Note: "NFR-NNN requires {constraint} — this approach may conflict with that."

3. **Implementation detail in requirements discussion**: A requirement is being framed in technology-specific terms. Note: "This is describing a solution rather than a requirement — should we keep it technology-agnostic?"

4. **Completed task still marked open**: If you can confirm a task is done (from the conversation), note: "TASK-NNN looks complete — should we mark it done in the task plan?"

## Situations that do NOT warrant a comment

- The work is clearly mapped to an existing task
- The task plan does not exist yet (the user may be in early-stage setup)
- The drift is minor and within scope of an existing task

Say nothing in these cases. This skill should be invisible when things are on track.
