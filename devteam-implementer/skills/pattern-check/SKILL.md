---
name: pattern-check
description: Before writing new code, check for existing patterns and implementations in the codebase that should be reused or extended. Invoke automatically when about to implement something new.
user-invocable: false
allowed-tools: Read, Grep, Glob
---

# Pattern Check

Before writing new code, search for existing implementations that already do the same or a similar thing.

## What to search for

Based on what is about to be implemented, use Grep and Glob to search for:
- Functions with similar names or purposes
- Classes or types that might already model the same concept
- Utility functions that already perform the needed operation
- Configuration patterns already in use

## How to use the result

If an existing pattern is found:
- **Reuse it**: call the existing function or extend the existing class rather than duplicating logic
- **Extend it**: if the existing code does 80% of what is needed, extend it rather than writing a parallel implementation
- **Note the deviation**: if the existing pattern cannot be reused and a new approach is genuinely needed, note why the deviation from the existing pattern is justified

If no existing pattern is found:
- Proceed with implementation, but establish a clear pattern that future code can follow

## What to report

Before proceeding with implementation, briefly state:
- What was searched for and what was found
- Whether existing code will be reused, extended, or why a new approach is needed
- The file path of any existing implementation being reused (for the user's awareness)

This check is mandatory — do not skip it even for apparently simple additions.
