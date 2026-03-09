# Dev Team

A suite of Claude Code plugins that provide a structured virtual development team. The plugins cover the full software development lifecycle — from requirements through design, implementation, testing, and review — enforcing consistent principles at every stage.

## Plugins at a glance

| Plugin | Role | Key skills |
|---|---|---|
| `devteam-workflow` | Pipeline orchestration | `requirements`, `plan`, `session-start`, `task-slicer` |
| `devteam-architect` | Design and architecture | `design-session`, `adr`, `design-review` |
| `devteam-researcher` | Research and validation | `api-research`, `library-check`, `codebase-explore` |
| `devteam-implementer` | Standards-enforcing coding | `implement`, `pattern-check` |
| `devteam-tester` | Testing | `write-tests`, `run-tests`, `coverage-check` |
| `devteam-reviewer` | Independent review | `code-review`, `security-review`, `requirements-check` |

## Core principles enforced by the suite

- **Requirements before code** — `implement` refuses to proceed without a requirements document and task plan
- **Technology-agnostic requirements** — `requirements` prevents implementation details from appearing in requirement statements
- **Verify before you use** — `api-research` and `library-check` produce a structured suitability report before any dependency is committed to
- **Independent critique** — `design-review` forks an isolated expert agent that critiques designs with no access to the conversation that produced them
- **Tests are not optional** — `implement` does not declare a task done without corresponding tests
- **Context-preserving reviews** — review and research skills run in forked agents; only summaries return to the main conversation

---

## Installation

### Prerequisites

- [Claude Code](https://code.claude.com) installed and authenticated
- Claude Code version 1.0.33 or later (`claude --version`)

### Add the marketplace

```
/plugin marketplace add <github-org>/<repo-name>
```

### Install plugins

Install the full suite:

```
/plugin install devteam-workflow@devteam
/plugin install devteam-architect@devteam
/plugin install devteam-researcher@devteam
/plugin install devteam-implementer@devteam
/plugin install devteam-tester@devteam
/plugin install devteam-reviewer@devteam
```

Or install only the plugins you need — each is fully independent.

### Enable for a project

To have teammates automatically prompted to install the marketplace when they open the project, add to `.claude/settings.json` in your project repository:

```json
{
  "extraKnownMarketplaces": {
    "devteam": {
      "source": {
        "source": "github",
        "repo": "<github-org>/<repo-name>"
      }
    }
  }
}
```

---

## Adopting the suite on an existing project

If you have an existing codebase with prior design decisions, implementations, and history, use the `retrofit` skill to bring it under the devteam workflow rather than starting from scratch.

```
/devteam-workflow:retrofit
```

The skill analyses the project in five phases:

1. **Project scan** — maps the codebase structure, stack, dependencies, git history, TODO comments, open GitHub issues, and skipped tests
2. **Derive requirements** — infers functional and non-functional requirements from tests, the README, and the public API surface; presents them for your review and confirmation before writing
3. **Capture existing decisions as ADRs** — identifies the major architectural choices already in effect (framework, database, auth mechanism, etc.) and creates retrospective MADR-format ADRs marked `accepted`
4. **Draft the task plan** — consolidates remaining work from open issues, TODO comments, pending tests, and requirement gaps into a `docs/task-plan.md`
5. **Summary** — reports what was produced and which devteam skills to use next

After `retrofit` completes, the full suite is available:  `session-start`, `implement`, `code-review`, `design-session`, and all others work against the derived project docs.

You can run `retrofit` on a partially-documented project too — it skips phases where docs already exist and only fills in what is missing.

---

## Typical session workflow

### 1. Start every session

```
/devteam-workflow:session-start
```

Loads and summarises the current requirements, task plan, and recent architectural decisions. Run this before any work begins.

### 2. Define or update requirements

```
/devteam-workflow:requirements [topic]
```

Guides a structured requirements discussion and writes `docs/requirements.md`. Enforces technology-agnostic requirement statements and assigns FR/NFR IDs for cross-referencing.

### 3. Create a task plan

```
/devteam-workflow:plan
```

Reads `docs/requirements.md` and produces `docs/task-plan.md` with tasks mapped to requirement IDs. Flags any requirements with no corresponding task.

### 4. Design non-trivial components

```
/devteam-architect:design-session [component or system]
```

Facilitates a structured options-and-tradeoffs discussion. Produces a design note in `docs/design/`.

```
/devteam-architect:adr [decision title]
```

Formalises the decision as a MADR-format Architecture Decision Record in `docs/adr/`.

```
/devteam-architect:design-review
```

Forks an independent `architect-reviewer` agent (Claude Opus with web access) to critique the design against requirements. Returns a structured report with requirements coverage, KISS compliance, ADR consistency, and risk assessment. Run this before marking any ADR as `accepted`.

### 5. Research dependencies

```
/devteam-researcher:library-check [purpose] [lib1] [lib2] [lib3]
```

Compares candidate libraries across a standard set of criteria including project consistency, licence, maintenance health, and feature fit. Produces a suitability matrix and summary — **you make the final selection**, taking team familiarity and preferences into account.

```
/devteam-researcher:api-research [chosen library] for [purpose]
```

Once a library is chosen, research its version lines. Presents current stable, LTS, and other available versions with their support windows, breaking change notes, and selection considerations — **you select the version**. The latest version is not always the right choice. Record both decisions with `/devteam-architect:adr`.

```
/devteam-researcher:codebase-explore [area or topic]
```

Maps entry points, patterns, conventions, and integration points in an unfamiliar area of the codebase. Run before implementing in an area you haven't worked in before.

### 6. Decompose a task into executor slices (optional)

```
/devteam-workflow:task-slicer [description of the implementation task]
```

Breaks a scoped implementation request into small, independently executable slices and optionally sends each slice to a weaker executor model via an OpenAI-compatible API. Useful when you want to delegate implementation to a local model (e.g. a quantised coding model running in LM Studio) while Claude acts as the planner and reviewer.

The skill:
- Computes a content hash of the request so identical tasks reuse an existing plan
- Saves each plan to `.claude/task-slices/` as a JSON file
- Applies the executor's file output itself (the executor model does not write to disk)
- Verifies acceptance criteria after each slice before proceeding to dependent slices

Requires `.claude/planner_config.toml` in the active project — see [Executor configuration](#executor-configuration).

### 7. Implement

```
/devteam-implementer:implement [task ID or description]
```

Reads requirements, task plan, and existing patterns first. Proposes an approach and waits for confirmation before writing any code. Writes tests as part of implementation.

### 8. Test

```
/devteam-tester:write-tests [file or module]
```

Generates unit tests matching the project's existing testing conventions. Covers happy paths, error cases, and boundary conditions.

```
/devteam-tester:run-tests
```

Runs the test suite in an isolated fork and returns only failures with context. Passing test output is suppressed.

```
/devteam-tester:coverage-check [module or directory]
```

Identifies untested source files and functions. Tries to run the project's coverage tool; falls back to static analysis.

### 9. Review before merging

```
/devteam-reviewer:code-review
```

Forks an independent `code-reviewer` agent to review recent changes for correctness, standards adherence, documentation, and test coverage.

```
/devteam-reviewer:security-review
```

Forks an independent `security-reviewer` agent to check against the OWASP Top 10 (2021), scan for hardcoded secrets, and assess the attack surface.

```
/devteam-reviewer:requirements-check [task ID]
```

Verifies the implementation satisfies the documented requirements and acceptance criteria before the task is marked complete.

---

## Plugin reference

### devteam-workflow

| Skill | Invocation | Description |
|---|---|---|
| `session-start` | `/devteam-workflow:session-start` | Load requirements, task plan, and recent ADRs at session start |
| `requirements` | `/devteam-workflow:requirements [topic]` | Elicit and document technology-agnostic requirements |
| `plan` | `/devteam-workflow:plan` | Create or update the task plan from requirements |
| `retrofit` | `/devteam-workflow:retrofit` | Analyse an existing codebase and produce requirements, ADRs, and a task plan |
| `task-slicer` | `/devteam-workflow:task-slicer [task]` | Decompose a task into executor slices; optionally delegate implementation to a local model |
| `task-status` | *(model-invoked)* | Silent background check; flags when work drifts from the plan |

**Project files managed**: `docs/requirements.md`, `docs/task-plan.md`

---

### Executor configuration

`task-slicer` requires a configuration file at `.claude/planner_config.toml` in the active project:

```toml
[model]
endpoint   = "http://localhost:1234/v1"   # OpenAI-compatible endpoint
api_key    = ""                            # leave empty for local servers
name       = "your-model-name"
max_tokens = 4096
max_slices = 8
max_turns  = 10
timeout    = 1200   # seconds per API call; 1200 recommended for local thinking models
stream     = false  # set true for thinking models (qwen3, deepseek-r1, etc.)
```

`endpoint` accepts either a full chat completions URL (`/v1/chat/completions`) or a base URL (`/v1`) — the skill appends the path automatically.

`stream = true` uses Server-Sent Events rather than a single blocking request. This keeps the TCP connection alive during any internal chain-of-thought phase, preventing socket timeouts on thinking models.

The executor model receives one slice at a time. It outputs file contents in `=== FILE: path === ... === END FILE ===` blocks; Claude writes each file and verifies the acceptance criteria before proceeding to the next slice.

---

### devteam-architect

| Skill | Invocation | Description |
|---|---|---|
| `design-session` | `/devteam-architect:design-session [topic]` | Structured design discussion with options and tradeoffs |
| `adr` | `/devteam-architect:adr [title]` | Generate a MADR-format Architecture Decision Record |
| `design-review` | `/devteam-architect:design-review [doc path]` | Independent design critique via forked architect-reviewer agent |

**Project files managed**: `docs/design/`, `docs/adr/`

**Agent**: `architect-reviewer` — Claude Opus with web access and local memory. Critiques designs independently with no access to the main conversation. Accumulates codebase knowledge across sessions.

---

### devteam-researcher

| Skill | Invocation | Description |
|---|---|---|
| `api-research` | `/devteam-researcher:api-research [name and use]` | Research a library and present version options for user selection |
| `library-check` | `/devteam-researcher:library-check [purpose] [lib1] [lib2]` | Compare candidate libraries; presents options — user makes the selection |
| `codebase-explore` | `/devteam-researcher:codebase-explore [area]` | Map patterns and entry points in a codebase area |

**Agent**: `researcher` — Claude Haiku with web access. Fast, cost-efficient; verifies claims against primary sources.

---

### devteam-implementer

| Skill | Invocation | Description |
|---|---|---|
| `implement` | `/devteam-implementer:implement [task]` | Implement a task: reads requirements first, proposes approach, waits for confirmation |
| `pattern-check` | *(model-invoked)* | Check for existing patterns before writing new code |
| `session-context` | *(model-invoked)* | Background coding standards; loaded automatically during implementation |

**Agent**: `implementer` — preloads `session-context` standards; reads requirements and design decisions before writing any code.

---

### devteam-tester

| Skill | Invocation | Description |
|---|---|---|
| `write-tests` | `/devteam-tester:write-tests [file]` | Write unit tests matching project conventions |
| `run-tests` | `/devteam-tester:run-tests` | Run test suite; return failures only |
| `coverage-check` | `/devteam-tester:coverage-check [scope]` | Identify untested code paths |

**Agents**:
- `test-runner` — Claude Haiku; fast test execution and failure parsing
- `test-writer` — generates tests; reads source to understand coverage needed

---

### devteam-reviewer

| Skill | Invocation | Description |
|---|---|---|
| `code-review` | `/devteam-reviewer:code-review` | Quality, correctness, and standards review of recent changes |
| `security-review` | `/devteam-reviewer:security-review` | OWASP Top 10 check, secrets scan, attack surface assessment |
| `requirements-check` | `/devteam-reviewer:requirements-check [task]` | Verify implementation satisfies requirements and acceptance criteria |

**Agents**:
- `code-reviewer` — Claude Opus with local memory; accumulates codebase knowledge across sessions
- `security-reviewer` — Claude Opus with local memory; tracks vulnerability patterns in this codebase

Both reviewer agents run in isolation from the main conversation. Only their structured reports are returned.

---

## Project documentation layout

The suite expects and maintains the following structure in any project it is used on:

```
docs/
├── requirements.md        # FR/NFR requirements (managed by devteam-workflow:requirements)
├── task-plan.md           # Task plan with requirement cross-references (managed by devteam-workflow:plan)
├── adr/
│   ├── 0001-title.md      # Architecture Decision Records in MADR format
│   └── 0002-title.md
└── design/
    └── topic.md           # Design notes produced by devteam-architect:design-session

.claude/
├── planner_config.toml    # Executor model config for task-slicer (not committed — see below)
└── task-slices/
    └── <hash>-<slug>.json # Saved slice plans, keyed by content hash of the task description
```

None of these files need to exist before you start — each skill creates them on first use.

---

## Local-only files

The following are gitignored and never committed:

- `.claude/settings.local.json` — machine-specific Claude Code settings
- `.claude/agent-memory-local/` — per-developer agent memory for `architect-reviewer`, `code-reviewer`, and `security-reviewer`
- `.claude/planner_config.toml` — executor model endpoint and API key for `task-slicer`; contains credentials and is machine-specific

Each developer's review agents build up their own independent knowledge of the codebase over time.

The `.claude/task-slices/` directory can optionally be committed — the saved slice plans are content-addressed by a hash of the task description and contain no credentials. Committing them lets the team reuse slice plans across machines.
