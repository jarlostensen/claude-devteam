# Dev Team - Claude Skills and Agents for Development Work

The purpose of this collection of plugins is to enhance Claude Code for software development tasks by providing a structured "virtual dev team" of specialized skills and agents. The plugins cover the entire development pipeline from initial design and planning through implementation, testing, deployment, and evolution.

---

## Key Development Principles

- **KISS**: Keep it Simple, Stupid
- **No dead code**: Never write code that is not being used. Defer writing code if it does not have an immediately understandable use
- **Technology-agnostic requirements**: Functional and non-functional requirements must, unless explicitly asked for, not contain any implementation details. "Use `redis` for the database" is not acceptable; "Use a key-value store" is more appropriate
- **Verified APIs and libraries**: All APIs or third-party libraries to be used must be fully understood and checked before finalising decisions on their suitability. Assumptions must be checked by searching for the most up-to-date documentation or by using tools such as the context7 MCP language API server
- **Live cross-references**: Keep task plans and requirements cross-referenced and updated at all times. When starting on a new solution these must be read and understood to ensure the new work fits with current state and previous decisions
- **Dual validation**: When creating proposals and implementation plans, the plans must always be verified with the user **and** verified by an independent expert developer agent tasked with validating and critiquing the design

---

## Plugin Architecture Overview

The Dev Team is structured as a set of Claude Code plugins, each representing a specialist role on the team. A top-level marketplace manifest (`marketplace.json`) registers all plugins, which can be installed individually or as a suite.

```
devteam/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace index for all plugins
│
├── devteam-workflow/             # Pipeline orchestration
├── devteam-architect/            # Design, requirements, and architecture
├── devteam-researcher/           # API, library, and codebase research
├── devteam-implementer/          # Implementation with standards enforcement
├── devteam-tester/               # Test generation and execution
└── devteam-reviewer/             # Code review, security, and design validation
```

Each plugin follows the standard Claude plugin layout:

```
devteam-<name>/
├── .claude-plugin/
│   └── plugin.json               # Plugin identity and metadata
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md              # Skill instructions and frontmatter
│       └── <supporting-files>    # Templates, examples, scripts
└── agents/
    └── <agent-name>.md           # Subagent definitions
```

Plugin skills are namespaced automatically (e.g., `/devteam-architect:design-session`). This prevents conflicts between plugins and with standalone `.claude/` configuration.

---

## Plugin Specifications

### 1. `devteam-workflow` - Pipeline Orchestration

Provides skills that manage the overall development workflow: tracking requirements, maintaining task plans, and ensuring process adherence.

**Skills:**

| Skill | Invocation | Purpose |
|---|---|---|
| `plan` | User-invoked | Create or update a structured task plan from requirements |
| `requirements` | User-invoked | Elicit, refine, and document requirements |
| `task-status` | User or model | Review current task plan state and flag drift |
| `session-start` | User-invoked | Load project context (requirements, ADRs, task plan) at session start |

**Key behaviours:**
- `plan` writes a `docs/task-plan.md` that stays cross-referenced with `docs/requirements.md`
- `session-start` reads both documents and summarises outstanding decisions before any work begins
- `task-status` uses `user-invocable: false` (model-invoked only) to silently check plan alignment during the session

**Agents:**

| Agent | Model | Purpose |
|---|---|---|
| `workflow-coordinator` | inherit | Monitors the session and proactively flags when work drifts from the task plan |

---

### 2. `devteam-architect` - Design and Architecture

Covers the design phase: facilitating design discussions, producing Architecture Decision Records (ADRs), and independently critiquing proposals.

**Skills:**

| Skill | Invocation | Context | Purpose |
|---|---|---|---|
| `design-session` | User-invoked | inline | Structured design discussion; explores tradeoffs and documents decisions |
| `adr` | User-invoked | inline | Generate an Architecture Decision Record from a design decision |
| `design-review` | User-invoked | `fork` / Explore | Spawn an independent Explore agent to critique a design against requirements |

**`design-review` detail:**

This skill satisfies the requirement for "independent expert developer agent validation". It:
1. Reads the current design document and requirements
2. Forks the `architect-reviewer` agent with no access to the main conversation
3. The subagent independently critiques the design for completeness, requirement coverage, technical risk, and KISS violations
4. Returns a structured critique report to the main conversation

```yaml
# skills/design-review/SKILL.md (frontmatter excerpt)
---
name: design-review
description: Independently review and critique a design against requirements. Use before finalising any architectural decision.
context: fork
agent: architect-reviewer
allowed-tools: Read, Grep, Glob, WebSearch, WebFetch
disable-model-invocation: true
---
```

**Agents:**

| Agent | Model | Tools | Memory | Purpose |
|---|---|---|---|---|
| `architect-reviewer` | opus | Read, Grep, Glob, WebSearch, WebFetch | `local` | Deep architectural review; can look up RFCs, patterns, and current best practices |

The `architect-reviewer` agent uses `model: opus` for the highest reasoning quality, has web access to verify referenced standards and look up current practices, and `memory: local` so accumulated architectural knowledge stays machine-local.

---

### 3. `devteam-researcher` - Research and Discovery

Handles all research tasks: verifying APIs and libraries, exploring the codebase, and producing factual research reports before decisions are made.

**Skills:**

| Skill | Invocation | Context | Purpose |
|---|---|---|---|
| `api-research` | User or model | `fork` / Explore | Research an API or library; verify documentation and suitability |
| `codebase-explore` | User or model | `fork` / Explore | Deep codebase analysis; map existing patterns and entry points |
| `library-check` | User or model | `fork` / Explore | Compare candidate libraries; produce a suitability matrix |

**`api-research` detail:**

Satisfies the principle "APIs or third-party libraries must be fully understood and checked". Uses dynamic context injection to fetch live documentation:

```yaml
---
name: api-research
description: Research an API or library before it is used. Use when evaluating any external dependency.
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, WebSearch, WebFetch
---

Research the API or library: $ARGUMENTS

Required output:
1. Current version and release status
2. Key concepts and usage patterns
3. Any known breaking changes or deprecations
4. Licensing and maintenance health
5. Recommended integration approach

Search for documentation at:
- Official docs site
- GitHub repository (issues, releases)
- Community resources (Stack Overflow, package registries)
```

**Agents:**

| Agent | Model | Tools | Purpose |
|---|---|---|---|
| `researcher` | haiku | Read, Grep, Glob, WebSearch, WebFetch | Fast, cost-efficient research agent with web access |

---

### 4. `devteam-implementer` - Implementation with Standards Enforcement

Guides implementation in accordance with the project's established standards, the task plan, and the design decisions already made.

**Skills:**

| Skill | Invocation | Purpose |
|---|---|---|
| `implement` | User-invoked | Guided implementation; reads task plan and requirements first |
| `pattern-check` | Model-invoked | Before writing new code, check for existing patterns to reuse |
| `session-context` | Model-invoked | Background skill: injects coding standards into context |

**`implement` detail:**

This skill enforces the "read before you write" principle:
1. Reads `docs/requirements.md` and `docs/task-plan.md`
2. Reads relevant existing code to understand patterns
3. Proposes the implementation approach and waits for user confirmation
4. Only then proceeds with code generation

```yaml
---
name: implement
description: Implement a feature or fix. Reads requirements and existing patterns first, proposes approach, then implements.
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Write, Edit, Bash
argument-hint: [feature-or-task-description]
---
```

**Agents:**

| Agent | Model | Tools | Purpose |
|---|---|---|---|
| `implementer` | inherit | Read, Grep, Glob, Write, Edit, Bash | Full implementation agent; enforces coding standards via preloaded skills |

The `implementer` agent preloads the `session-context` skill, which contains the devteam's own coding standards (defined within this plugin suite, not inherited from an external plugin).

---

### 5. `devteam-tester` - Test Generation and Execution

Ensures every piece of implemented code has corresponding tests. Enforces the principle "a task is not complete until tests exist and pass."

**Skills:**

| Skill | Invocation | Context | Purpose |
|---|---|---|---|
| `write-tests` | User-invoked | inline | Generate unit tests for a given module or function |
| `run-tests` | User-invoked | `fork` / Bash | Run the test suite and return only failures with context |
| `coverage-check` | User or model | `fork` / Explore | Analyse test coverage; identify untested code paths |

**`run-tests` detail:**

Uses `context: fork` to isolate verbose test output from the main conversation. Only the test failures and summary are returned.

```yaml
---
name: run-tests
description: Run the test suite and report only failing tests with error messages. Use after implementing to verify nothing is broken.
context: fork
agent: Bash
allowed-tools: Bash
disable-model-invocation: true
---

Run the project test suite:

!`cat docs/task-plan.md | grep -i "test command" || echo "No test command found in task plan"`

Identify the correct test runner from the project configuration, then run all tests.
Return ONLY:
1. A pass/fail summary (N passed, N failed)
2. For each failure: the test name, error message, and relevant stack trace lines
3. Any setup or configuration errors

Do not return passing test output.
```

**Agents:**

| Agent | Model | Tools | Purpose |
|---|---|---|---|
| `test-runner` | haiku | Bash, Read | Fast test execution and failure parsing |
| `test-writer` | inherit | Read, Grep, Glob, Write | Generates tests; reads source to understand what needs coverage |

---

### 6. `devteam-reviewer` - Code Review and Validation

Provides independent review of code quality, security, and conformance to requirements. Each review agent runs in isolation from the main conversation.

**Skills:**

| Skill | Invocation | Context | Purpose |
|---|---|---|---|
| `code-review` | User-invoked | `fork` / Explore | Full code review of recent changes |
| `security-review` | User-invoked | `fork` / Explore | Security-focused review: OWASP top 10, injection, secrets, auth |
| `requirements-check` | User-invoked | `fork` / Explore | Verify the implementation satisfies stated requirements |

**`code-review` detail:**

Uses dynamic context injection to get fresh git diff data before the subagent runs:

```yaml
---
name: code-review
description: Review recent code changes for quality, correctness, and standards adherence.
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, Bash(git *)
disable-model-invocation: true
---

## Code to review

Recent changes:
!`git diff HEAD~1 --stat`

Full diff:
!`git diff HEAD~1`

## Review checklist

Evaluate against:
1. Code clarity and self-documentation
2. Function and variable naming accuracy
3. Error handling completeness
4. No code that is not being used
5. Consistent style with the surrounding codebase
6. Test coverage for changed code
7. No exposed secrets or hardcoded credentials
8. Performance considerations

Organise output as:
- Critical (must fix before merge)
- Warning (should fix)
- Suggestion (consider improving)
```

**Agents:**

| Agent | Model | Tools | Memory | Purpose |
|---|---|---|---|---|
| `code-reviewer` | opus | Read, Grep, Glob, Bash | `local` | Deep quality review; accumulates codebase knowledge on this machine |
| `security-reviewer` | opus | Read, Grep, Glob | `local` | Security-focused review; tracks known vulnerability patterns on this machine |

Both review agents use `model: opus` for highest-quality analysis and `memory: local` so accumulated knowledge stays machine-local and is never committed to version control.

---

## Marketplace Manifest

The top-level `marketplace.json` registers all plugins for installation via `/plugin`:

```json
{
  "name": "devteam-plugins",
  "owner": {
    "name": "Dev Team"
  },
  "plugins": [
    {
      "name": "devteam-workflow",
      "source": "./devteam-workflow",
      "description": "Pipeline orchestration: requirements, task plans, and session context management"
    },
    {
      "name": "devteam-architect",
      "source": "./devteam-architect",
      "description": "Design sessions, ADRs, and independent design critique via forked expert agent"
    },
    {
      "name": "devteam-researcher",
      "source": "./devteam-researcher",
      "description": "API research, library validation, and codebase exploration using isolated Explore agents"
    },
    {
      "name": "devteam-implementer",
      "source": "./devteam-implementer",
      "description": "Standards-enforcing implementation with mandatory requirements and pattern checks"
    },
    {
      "name": "devteam-tester",
      "source": "./devteam-tester",
      "description": "Test generation, test execution, and coverage analysis"
    },
    {
      "name": "devteam-reviewer",
      "source": "./devteam-reviewer",
      "description": "Code review, security review, and requirements conformance check via independent agents"
    }
  ]
}
```

---

## Cross-Plugin Interactions and Workflow

A typical session using the full Dev Team suite:

```
1. /devteam-workflow:session-start
   - Loads requirements and task plan into context
   - Summarises outstanding decisions

2. /devteam-architect:design-session [topic]
   - Facilitates a design discussion
   - Produces a design document

3. /devteam-architect:design-review
   - Forks an independent Explore agent
   - Returns structured critique of the design

4. /devteam-architect:adr [decision title]
   - Documents the decision in docs/adr/

5. /devteam-researcher:api-research [library name]
   - Forks an Explore+Web agent to verify the library
   - Returns suitability report before any code is written

6. /devteam-workflow:plan
   - Produces a cross-referenced task plan

7. /devteam-implementer:implement [task]
   - Reads requirements and plan first
   - Proposes approach and awaits confirmation
   - Implements to standards

8. /devteam-tester:write-tests [module]
   - Generates tests for the new code

9. /devteam-tester:run-tests
   - Runs the suite in an isolated fork
   - Returns failures only

10. /devteam-reviewer:code-review
    - Independent quality review

11. /devteam-reviewer:security-review
    - Independent security review

12. /devteam-reviewer:requirements-check
    - Verifies implementation against requirements
```

---

## Implementation Plan

### Phase 0: Infrastructure (Prerequisites)

- [ ] Initialise the devteam GitHub repository
- [ ] Create the root `marketplace.json` registering all six plugins
- [ ] Define the standard `plugin.json` template used by each plugin
- [ ] Establish the expected project docs layout (`docs/requirements.md`, `docs/task-plan.md`, `docs/adr/`) and document it in the repo README

### Phase 1: Core Workflow and Architecture Plugins

Priority: These two plugins provide the foundation that all others build on.

1. **`devteam-workflow`**
   - `requirements` skill (inline, user-invoked)
   - `plan` skill (inline, user-invoked)
   - `session-start` skill (inline, user-invoked)
   - `task-status` skill (inline, model-invoked, `user-invocable: false`)

2. **`devteam-architect`**
   - `design-session` skill (inline, user-invoked)
   - `adr` skill (inline, user-invoked) with MADR template as supporting file
   - `design-review` skill (`context: fork`, user-invoked, web access enabled)
   - `architect-reviewer` agent (`model: opus`, `memory: local`, web access)

### Phase 2: Research Plugin

3. **`devteam-researcher`**
   - `api-research` skill (`context: fork`, model or user-invoked)
   - `codebase-explore` skill (`context: fork`, model or user-invoked)
   - `library-check` skill (`context: fork`, user-invoked)
   - `researcher` agent (`model: haiku`)

### Phase 3: Implementation Plugin

4. **`devteam-implementer`**
   - `session-context` skill (inline, `user-invocable: false`) - background standards injection
   - `pattern-check` skill (inline, model-invoked)
   - `implement` skill (inline, user-invoked, `disable-model-invocation: true`)
   - `implementer` agent (inherit model, preloads `session-context` skill)

### Phase 4: Testing Plugin

5. **`devteam-tester`**
   - `write-tests` skill (inline, user-invoked)
   - `run-tests` skill (`context: fork`, user-invoked)
   - `coverage-check` skill (`context: fork`, model or user-invoked)
   - `test-runner` agent (`model: haiku`)
   - `test-writer` agent (inherit model)

### Phase 5: Review Plugin

6. **`devteam-reviewer`**
   - `code-review` skill (`context: fork`, user-invoked, with dynamic git diff injection)
   - `security-review` skill (`context: fork`, user-invoked)
   - `requirements-check` skill (`context: fork`, user-invoked)
   - `code-reviewer` agent (`model: opus`, `memory: project`)
   - `security-reviewer` agent (`model: opus`, `memory: project`)

### Phase 6: Integration and Validation

- [ ] Install all plugins via the marketplace and test end-to-end workflows
- [ ] Verify cross-plugin skill references work correctly
- [ ] Document usage examples in each plugin's `README.md`
- [ ] Validate that the `design-review` and `architect-reviewer` provide genuinely independent critique (test with a deliberately flawed design)
- [ ] Performance-test agent startup times, especially for forked Explore agents

---

## Key Technical Decisions

### Why `context: fork` for review and research skills?

Review and research operations produce large amounts of output (diffs, search results, documentation). Running them in the main conversation would pollute the context window. A forked subagent keeps the output isolated; only the summary returns to the main conversation. This directly implements the "preserve context by keeping exploration out of the main conversation" pattern.

### Why `model: opus` for reviewer agents?

Code review and architectural critique require the highest reasoning quality. The cost premium is justified for these infrequent, high-stakes operations. All other agents use `inherit` or `haiku` for cost efficiency.

### Why `memory: local` for reviewer and architect agents?

These agents benefit from accumulated knowledge about the codebase: its patterns, its historical decisions, its common mistakes. `memory: local` keeps this knowledge in `.claude/agent-memory-local/` — it is never committed to version control, so personal review notes and codebase observations stay on the developer's machine. Each developer builds their own agent memory independently.

### Why `disable-model-invocation: true` for `implement` and `run-tests`?

Both have side effects (writing files, running commands). These should only happen when the user explicitly requests them, never because Claude decided the code "looks ready to implement" or "probably needs tests now".

### Why separate plugins rather than one monolithic plugin?

Each plugin can be installed independently. A team that only wants pair-programming navigator mode and code review does not need the full suite. Namespacing also prevents skill name conflicts and makes it clear which plugin provides which capability.

---

## Decisions Log

| # | Question | Decision |
|---|---|---|
| 1 | Marketplace location | Separate GitHub repo with its own `marketplace.json`; independent from `code_rules` |
| 2 | Implementation standards | `devteam-implementer` defines its own standards within the plugin suite |
| 3 | Architect reviewer web access | Yes — `architect-reviewer` and `design-review` skill both include `WebSearch` and `WebFetch` |
| 4 | ADR format | MADR (Markdown Architectural Decision Records) |
| 5 | Agent memory scope | `memory: local` — machine-local, never committed to version control |
