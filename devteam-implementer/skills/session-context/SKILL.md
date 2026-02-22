---
name: session-context
description: Coding standards and implementation principles for this project. Load automatically when implementing code to ensure consistent quality.
user-invocable: false
---

# Implementation Standards

These standards apply to all code written in this project. They are not suggestions.

## 1. Never write unused code

Write only code that is immediately needed. If a function, class, variable, or import has no current caller or user, do not create it. "We might need this later" is not a reason to write code today.

## 2. Read before you write

Before creating any new function, class, or module, search the codebase for an existing implementation that does the same or similar thing. Reuse over reinvention.

Before implementing, read:
- `docs/requirements.md` — to understand what is required
- `docs/task-plan.md` — to confirm the task being worked on
- Any relevant ADR in `docs/adr/` — to honour previous design decisions
- The existing code in the area being changed — to understand the patterns in use

## 3. Function and module size

- Functions: investigate if over ~100 lines. If the logic cannot be understood at a glance, it is too large.
- Files/modules: investigate if over ~800 lines.

If a limit is exceeded and there is a good reason, add a comment explaining why.

## 4. Naming

Names must accurately describe behaviour. If you cannot find a name that describes what a function does, that is a signal the function is doing too much. Rename or split.

## 5. Comments

Write comments when:
- The code does something that looks wrong but is correct (explain why it must be this way)
- The logic is non-obvious (explain the reasoning, not the mechanics)
- Business logic is not evident from the code alone

Do not write comments that restate what the code already says.

## 6. Error handling

Handle errors at the appropriate level. Do not silently swallow errors. Every error path must either:
- Return a meaningful error to the caller
- Log the error with enough context to diagnose it
- Fail fast and explicitly

## 7. Documentation

Document all public functions, classes, and methods using the idiomatic documentation style for the language in use (docstrings, JSDoc, rustdoc, etc.). Include:
- What the function does (one sentence)
- Parameters: type, name, description
- Return value: type and meaning
- Example usage for non-trivial functions

## 8. Tests

Tests are not optional. Every new function or behaviour must have a corresponding unit test before the task is considered complete. Do not defer testing.

## 9. No implementation details in interfaces

Public interfaces describe WHAT something does, not HOW. Avoid leaking implementation details through interface names, parameter names, or documentation.

## 10. Security

- Never hardcode secrets, credentials, or tokens in source code
- Validate all inputs at system boundaries (user input, external API responses)
- Do not trust data from external sources without validation
- Do not log sensitive data (passwords, tokens, PII)
