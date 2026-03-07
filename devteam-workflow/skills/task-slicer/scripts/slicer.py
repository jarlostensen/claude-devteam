#!/usr/bin/env python3
"""
Slice executor: sends a single task slice to a configured executor model,
handles tool calls emitted by the model (read_file, list_directory), and
prints the final response. Runs an agentic text loop rather than relying on
the OpenAI structured tool-calls API — this works with local models that do
not honour the 'tools' request field but do embed tool calls in their text.

Usage:
    slicer.py <slice_json> [project_root]

Arguments:
    slice_json    JSON string of a single slice object (id, description,
                  target_files, acceptance_criteria, context, risk_level).
    project_root  Path to the project root (default: current directory).
                  Used to locate .claude/planner_config.toml and to resolve
                  file paths for tool calls.

Exit codes:
    0  Success — executor model response printed to stdout.
    1  Configuration error, API failure, or invalid slice — error on stderr.
"""

from __future__ import annotations

import dataclasses
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request
from uuid import uuid4


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_CONFIG_FILENAME = "planner_config.toml"
_CONFIG_HELP = """\
Create .claude/{filename} in your project root with the following content:

  [model]
  endpoint   = "https://api.openai.com/v1/chat/completions"
  api_key    = "sk-..."
  name       = "gpt-4o-mini"
  max_tokens = 4096
  max_turns  = 10
""".format(filename=_CONFIG_FILENAME)

_IGNORED_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".tox", "htmlcov", "coverage",
}

_EXECUTOR_SYSTEM_PROMPT = """\
You are a code implementation assistant. You will be given a specific, \
scoped coding task to implement.

## Your ONLY output: file contents

Write the complete contents of every file you create or modify using \
this exact format and nothing else outside it:

=== FILE: <relative/path/to/file> ===
<complete file contents>
=== END FILE ===

Do NOT include files that are unchanged.
Do NOT add explanation outside the FILE blocks — only file contents.

## IMPORTANT constraints

- You CANNOT run shell commands. Do not call cargo, git, npm, or any CLI tool.
- You CANNOT write or delete files directly. Output them in the FILE format above.
- You CANNOT execute code. Write it; the human will run it.
- If a file is new, write its full contents from scratch.

## Two read-only tools (use only when a file you need was not provided)

Request a file read:
<tool_call>
{"name": "read_file", "parameters": {"path": "relative/path/to/file"}}
</tool_call>

Request a directory listing:
<tool_call>
{"name": "list_directory", "parameters": {"path": "relative/directory/path"}}
</tool_call>

These are the ONLY two tools available. Any other tool name will return an \
error. Do not retry a failed tool with different parameters — if a tool \
returns an error, work around it using the information already provided.

## Rules

- Make ONLY the changes described in the task.
- Follow the existing code style in any provided file contents.
- Satisfy all acceptance criteria.
- Do not repeat a tool call that has already been answered.
- Paths in FILE blocks must be relative to the project root.
"""


# ---------------------------------------------------------------------------
# Tool call data
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class ToolCall:
    """A single tool call extracted from a model response.

    Attributes:
        name:       Tool name (e.g. 'read_file').
        parameters: Dict of arguments for the tool.
        id:         Unique identifier for this call.
    """
    name: str
    parameters: dict
    id: str


# ---------------------------------------------------------------------------
# Tool call parser (adapted from haraldus.tools.parser)
# ---------------------------------------------------------------------------

class ToolCallParser:
    """Extract tool calls embedded in LLM text responses.

    Handles multiple formats used by different local and hosted models:
    - ``<tool_call>{...}</tool_call>`` (primary, instructed format)
    - `` ```tool_call ... ``` `` code blocks
    - ``<|channel|>commentary to=TOOL <|constrain|>json<|message|>{...}``
    - ``[TOOL_CALLS]name[ARGS]{...}``

    Includes JSON repair for truncated or malformed tool call payloads
    that local models occasionally emit.

    Example usage:
        parser = ToolCallParser()
        text, calls = parser.parse(response_text)
        for call in calls:
            print(call.name, call.parameters)
    """

    # Primary: <tool_call>...</tool_call>
    TOOL_CALL_PATTERN = re.compile(
        r"<tool_call>\s*(.*?)\s*</tool_call>",
        re.DOTALL | re.IGNORECASE,
    )

    ALT_PATTERNS = [
        # ```tool_call ... ```
        re.compile(r"```tool_call\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE),
        # ```json // tool_call ... ```
        re.compile(
            r"```json\s*//\s*tool_call\s*(.*?)\s*```",
            re.DOTALL | re.IGNORECASE,
        ),
        # <|channel|>commentary to=TOOL_NAME <|constrain|>json<|message|>{...}
        re.compile(
            r"<\|channel\|>commentary\s+to=([\w.]+)\s*"
            r"(?:<\|constrain\|>json|[\w]*)<\|message\|>(\\{.*)",
            re.DOTALL,
        ),
        # [TOOL_CALLS]name[ARGS]{...}
        re.compile(
            r'(?<!`)(?<!``)\[TOOL_CALLS\](\w+)\[ARGS\](\{[^`]*?\})',
            re.IGNORECASE,
        ),
        # Fallback: <tool_call> without closing tag
        re.compile(r"<tool_call>\s*(\{.*\})", re.DOTALL | re.IGNORECASE),
    ]

    CHANNEL_PATTERN = re.compile(
        r"<\|channel\|>commentary\s+to=([\w.]+)\s*"
        r"(?:<\|constrain\|>json|[\w]*)<\|message\|>(\\{.*)",
        re.DOTALL,
    )

    CHANNEL_PATTERN_ALT = re.compile(
        r"<\|channel\|>commentary\s+to=tool_name\s*"
        r"(?:<\|constrain\|>json|[\w]*)<\|message\|>(\\{.*)",
        re.DOTALL,
    )

    def has_tool_calls(self, response: str) -> bool:
        """Return True if the response appears to contain any tool calls.

        Parameters:
            response (str): Raw model response text.

        Returns:
            bool: True if at least one tool call pattern is found.
        """
        if self.TOOL_CALL_PATTERN.search(response):
            return True
        if self.CHANNEL_PATTERN.search(response):
            return True
        if self.CHANNEL_PATTERN_ALT.search(response):
            return True
        for pattern in self.ALT_PATTERNS:
            if pattern.search(response):
                return True
        return False

    def parse(self, response: str) -> tuple[str, list[ToolCall]]:
        """Extract all tool calls from a model response.

        Parameters:
            response (str): Raw model response text.

        Returns:
            tuple[str, list[ToolCall]]: The response with tool call blocks
                removed, and the list of parsed ToolCall objects.

        Example usage:
            text, calls = parser.parse(response)
        """
        tool_calls: list[ToolCall] = []
        cleaned = response

        matches = list(self.TOOL_CALL_PATTERN.finditer(response))
        is_channel = False
        is_channel_alt = False

        if not matches:
            matches = list(self.CHANNEL_PATTERN_ALT.finditer(response))
            if matches:
                is_channel_alt = True

        if not matches:
            matches = list(self.CHANNEL_PATTERN.finditer(response))
            if matches:
                is_channel = True

        if not matches:
            for pattern in self.ALT_PATTERNS:
                if pattern == self.CHANNEL_PATTERN:
                    continue
                matches = list(pattern.finditer(response))
                if matches:
                    if matches[0].lastindex and matches[0].lastindex >= 2:
                        is_channel = True
                    break

        for match in matches:
            try:
                if is_channel_alt:
                    call = self._parse_json_call(match.group(1).strip())
                elif is_channel and match.lastindex and match.lastindex >= 2:
                    call = self._parse_channel_call(
                        match.group(1).strip(),
                        match.group(2).strip(),
                    )
                else:
                    call = self._parse_json_call(match.group(1).strip())

                tool_calls.append(call)
                cleaned = cleaned.replace(match.group(0), "")
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                cleaned = cleaned.replace(
                    match.group(0), f"[Parse Error: {exc}]"
                )

        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        return cleaned, tool_calls

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_json_call(self, json_str: str) -> ToolCall:
        """Parse a tool call from a JSON string.

        Parameters:
            json_str (str): JSON text containing 'name' and 'parameters'.

        Returns:
            ToolCall: Parsed tool call.

        Raises:
            json.JSONDecodeError: If JSON cannot be repaired.
            KeyError: If 'name' field is missing.
            TypeError: If field types are wrong.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            data = json.loads(self._repair_json(json_str))

        if not isinstance(data, dict):
            raise TypeError(f"Tool call must be an object, got {type(data).__name__}")

        name = data.get("name")
        if not name:
            raise KeyError("Tool call missing 'name' field")
        if not isinstance(name, str):
            raise TypeError(f"Tool name must be a string, got {type(name).__name__}")

        parameters = data.get("parameters", {})
        if not isinstance(parameters, dict):
            raise TypeError(f"Parameters must be an object, got {type(parameters).__name__}")

        return ToolCall(name=name, parameters=parameters, id=data.get("id", str(uuid4())[:8]))

    _NAME_MAP = {
        "read_file": "read_file", "readfile": "read_file",
        "write_file": "write_file", "writefile": "write_file",
        "list_directory": "list_directory", "listdirectory": "list_directory",
        "shell": "shell", "bash": "shell",
        "glob": "glob", "grep": "grep",
        "repo_browser.read_file": "read_file",
        "repo_browser.write_file": "write_file",
        "repo_browser.glob": "glob",
        "repo_browser.grep": "grep",
    }

    def _parse_channel_call(self, tool_name: str, json_str: str) -> ToolCall:
        """Parse a channel-format tool call where the name is outside the JSON.

        Parameters:
            tool_name (str): Tool name extracted from the channel tag.
            json_str (str):  JSON string containing the parameters.

        Returns:
            ToolCall: Parsed tool call.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            data = json.loads(self._repair_json(json_str))

        if not isinstance(data, dict):
            raise TypeError(f"Tool parameters must be an object, got {type(data).__name__}")

        normalized = self._NAME_MAP.get(tool_name.lower(), tool_name.lower())
        if "." in tool_name and normalized == tool_name.lower():
            base = tool_name.rsplit(".", 1)[-1].lower()
            normalized = self._NAME_MAP.get(base, base)

        call_id = data.pop("id", str(uuid4())[:8])
        return ToolCall(name=normalized, parameters=data, id=str(call_id))

    def _escape_control_chars_in_strings(self, json_str: str) -> str:
        """Escape literal control characters inside JSON string values.

        Local LLMs frequently emit raw newlines inside string values instead
        of the required \\n sequences, making the JSON invalid.

        Parameters:
            json_str (str): JSON text that may contain literal control chars.

        Returns:
            str: JSON text with control characters inside strings escaped.
        """
        result: list[str] = []
        in_string = False
        escape_next = False

        for char in json_str:
            if escape_next:
                result.append(char)
                escape_next = False
            elif in_string and char == "\\":
                result.append(char)
                escape_next = True
            elif char == '"':
                in_string = not in_string
                result.append(char)
            elif in_string and char == "\n":
                result.append("\\n")
            elif in_string and char == "\r":
                result.append("\\r")
            elif in_string and char == "\t":
                result.append("\\t")
            else:
                result.append(char)

        return "".join(result)

    def _repair_json(self, json_str: str) -> str:
        """Attempt to repair truncated or malformed JSON from a model response.

        Applies three fixes in order:
        1. Escape literal control characters inside string values.
        2. Append missing closing braces/brackets.
        3. Delegate to the json-repair library if available.

        Parameters:
            json_str (str): Potentially malformed JSON string.

        Returns:
            str: Best-effort repaired JSON string.
        """
        repaired = self._escape_control_chars_in_strings(json_str)

        open_braces    = repaired.count("{")
        close_braces   = repaired.count("}")
        open_brackets  = repaired.count("[")
        close_brackets = repaired.count("]")

        repaired += "]" * (open_brackets - close_brackets)
        repaired += "}" * (open_braces - close_braces)

        try:
            json.loads(repaired)
            return repaired
        except json.JSONDecodeError:
            pass

        try:
            from json_repair import repair_json  # type: ignore[import-untyped]
            repaired = repair_json(repaired)
        except Exception:  # noqa: BLE001
            pass

        return repaired


# ---------------------------------------------------------------------------
# Configuration loading
# ---------------------------------------------------------------------------

def _load_config(project_root: pathlib.Path) -> dict:
    """Load and parse planner_config.toml from <project_root>/.claude/.

    Parameters:
        project_root (pathlib.Path): Root directory of the active project.

    Returns:
        dict: Parsed TOML configuration.

    Raises:
        SystemExit(1): If the config file is missing or unparseable.
    """
    config_path = project_root / ".claude" / _CONFIG_FILENAME
    if not config_path.exists():
        _fatal(f"Config file not found: {config_path}\n\n{_CONFIG_HELP}")

    return _parse_toml(config_path.read_text(encoding="utf-8"))


def _parse_toml(text: str) -> dict:
    """Parse TOML using stdlib tomllib (3.11+), tomli, or a hand-rolled fallback.

    Parameters:
        text (str): Raw TOML content.

    Returns:
        dict: Parsed configuration.
    """
    try:
        import tomllib
        return tomllib.loads(text)
    except ImportError:
        pass
    try:
        import tomli
        return tomli.loads(text)
    except ImportError:
        pass
    return _minimal_toml_parse(text)


def _minimal_toml_parse(text: str) -> dict:
    """Hand-rolled TOML parser for simple flat configs with [sections].

    Parameters:
        text (str): Raw TOML content.

    Returns:
        dict: Parsed key/value structure, with sections as nested dicts.
    """
    result: dict = {}
    section: dict = result
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            key = line[1:-1].strip()
            section = {}
            result[key] = section
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            k = k.strip()
            v = v.strip()
            if (v.startswith('"') and v.endswith('"')) or \
               (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            else:
                try:
                    v = int(v)
                except ValueError:
                    try:
                        v = float(v)
                    except ValueError:
                        pass
            section[k] = v
    return result


def _resolve_model_config(config: dict) -> dict:
    """Extract executor model settings from the parsed config.

    Parameters:
        config (dict): Full parsed TOML config.

    Returns:
        dict: Flat dict with keys: endpoint, api_key, name, max_tokens,
              max_turns.
    """
    base = config.get("model", config)
    endpoint = base.get("endpoint", "https://api.openai.com/v1/chat/completions")
    # Accept both base URLs (ending in /v1) and full endpoint paths
    if not endpoint.rstrip("/").endswith("/chat/completions"):
        endpoint = endpoint.rstrip("/") + "/chat/completions"
    return {
        "endpoint":   endpoint,
        "api_key":    str(base.get("api_key", "")),
        "name":       str(base.get("name", "gpt-4o-mini")),
        "max_tokens": int(base.get("max_tokens", 4096)),
        "max_turns":  int(base.get("max_turns", 10)),
    }


# ---------------------------------------------------------------------------
# File reading and prompt construction
# ---------------------------------------------------------------------------

def _read_target_files(
    project_root: pathlib.Path,
    target_files: list[str],
) -> dict[str, str]:
    """Read the current contents of each listed target file.

    Parameters:
        project_root (pathlib.Path): Project root directory.
        target_files (list[str]):    Relative paths from the slice.

    Returns:
        dict[str, str]: Map of relative path to file contents (or an error
                        note if the file cannot be read).
    """
    contents: dict[str, str] = {}
    for rel_path in target_files:
        full = project_root / rel_path
        if full.exists() and full.is_file():
            try:
                contents[rel_path] = full.read_text(encoding="utf-8")
            except OSError as exc:
                contents[rel_path] = f"[Could not read: {exc}]"
        else:
            contents[rel_path] = "[File does not exist yet — create it]"
    return contents


def _build_executor_message(
    slice_data: dict,
    file_contents: dict[str, str],
) -> str:
    """Build the initial user message for the executor model.

    Parameters:
        slice_data (dict):             The single slice object from the plan.
        file_contents (dict[str,str]): Map of relative path to current text.

    Returns:
        str: Formatted message to send as the first user turn.

    Example usage:
        msg = _build_executor_message(slice, {"src/foo.py": "..."})
    """
    parts: list[str] = []

    parts.append(f"## Task: {slice_data.get('id', 'unknown')}")
    parts.append(f"\n{slice_data.get('description', '')}")

    criteria = slice_data.get("acceptance_criteria", [])
    if criteria:
        parts.append("\n## Acceptance criteria")
        for c in criteria:
            parts.append(f"- {c}")

    ctx = slice_data.get("context", "").strip()
    if ctx:
        parts.append(f"\n## Context\n{ctx}")

    if file_contents:
        parts.append("\n## Current file contents")
        for rel_path, content in file_contents.items():
            parts.append(f"\n### {rel_path}\n```\n{content}\n```")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _safe_resolve(project_root: pathlib.Path, rel_path: str) -> pathlib.Path | None:
    """Resolve a relative path within the project root, blocking traversal.

    Parameters:
        project_root (pathlib.Path): Absolute project root.
        rel_path (str):              Requested relative path.

    Returns:
        pathlib.Path | None: Resolved absolute path if safe, None if the path
                             escapes the project root.
    """
    try:
        full = (project_root / rel_path).resolve()
        root = project_root.resolve()
        if str(full).startswith(str(root)):
            return full
    except (OSError, ValueError):
        pass
    return None


def _tool_read_file(path: str, project_root: pathlib.Path) -> str:
    """Read a file requested by the executor model.

    Parameters:
        path (str):                  Relative path to the file.
        project_root (pathlib.Path): Project root for path resolution.

    Returns:
        str: File contents, or an error string if the file cannot be read.
    """
    full = _safe_resolve(project_root, path)
    if full is None:
        return f"ERROR: path '{path}' is outside the project root"
    if not full.exists():
        return f"ERROR: file not found: {path}"
    if not full.is_file():
        return f"ERROR: '{path}' is not a file"
    try:
        return full.read_text(encoding="utf-8")
    except OSError as exc:
        return f"ERROR: could not read '{path}': {exc}"


def _tool_list_directory(path: str, project_root: pathlib.Path) -> str:
    """List the contents of a directory requested by the executor model.

    Parameters:
        path (str):                  Relative path to the directory.
        project_root (pathlib.Path): Project root for path resolution.

    Returns:
        str: Newline-separated list of entries, or an error string.
    """
    full = _safe_resolve(project_root, path)
    if full is None:
        return f"ERROR: path '{path}' is outside the project root"
    if not full.exists():
        return f"ERROR: directory not found: {path}"
    if not full.is_dir():
        return f"ERROR: '{path}' is not a directory"
    try:
        entries = sorted(full.iterdir())
        lines = []
        for entry in entries:
            suffix = "/" if entry.is_dir() else ""
            lines.append(f"{entry.name}{suffix}")
        return "\n".join(lines) if lines else "(empty directory)"
    except OSError as exc:
        return f"ERROR: could not list '{path}': {exc}"


def _dispatch_tool(call: ToolCall, project_root: pathlib.Path) -> str:
    """Dispatch a parsed tool call to its implementation.

    Parameters:
        call (ToolCall):             The tool call to execute.
        project_root (pathlib.Path): Project root for file operations.

    Returns:
        str: Tool result as a string (content or error message).
    """
    if call.name == "read_file":
        path = call.parameters.get("path", "")
        if not path:
            return "ERROR: read_file requires a 'path' parameter"
        return _tool_read_file(path, project_root)

    if call.name in ("list_directory", "ls"):
        path = call.parameters.get("path", ".")
        return _tool_list_directory(path, project_root)

    return (
        f"ERROR: unknown tool '{call.name}'. "
        "The ONLY available tools are 'read_file' and 'list_directory'. "
        "Do NOT call this tool again. Output file contents using the "
        "=== FILE: path === ... === END FILE === format instead."
    )


def _format_tool_results(calls: list[ToolCall], results: list[str]) -> str:
    """Format tool results as the next user message turn.

    Parameters:
        calls (list[ToolCall]): The tool calls that were executed.
        results (list[str]):    Corresponding result strings.

    Returns:
        str: Formatted message to append to the conversation as a user turn.
    """
    parts = ["Tool results:"]
    has_errors = False

    for call, result in zip(calls, results):
        parts.append(f"\n[{call.name}: {call.parameters}]")
        parts.append(result)
        if result.startswith("ERROR:"):
            has_errors = True

    parts.append("\n---")
    if has_errors:
        parts.append(
            "One or more tools returned errors. You may retry with corrected "
            "parameters or adjust your approach. Do NOT repeat a call that "
            "already succeeded."
        )
    else:
        parts.append(
            "All tools completed successfully. Continue your implementation "
            "based on the results above. Do NOT repeat tool calls that have "
            "already been answered."
        )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------

def _api_request(
    endpoint: str,
    api_key: str,
    model: str,
    messages: list[dict],
    max_tokens: int,
) -> dict:
    """Send one chat-completion request and return the parsed JSON response.

    Parameters:
        endpoint (str):       Full URL of the chat completions endpoint.
        api_key (str):        Bearer token (may be empty for local servers).
        model (str):          Model identifier.
        messages (list[dict]): Full conversation history.
        max_tokens (int):     Maximum tokens to generate.

    Returns:
        dict: Parsed API response body.

    Raises:
        SystemExit(1): On HTTP error, network failure, or malformed response.
    """
    payload = json.dumps({
        "model":      model,
        "messages":   messages,
        "max_tokens": max_tokens,
        "temperature": 0,
    }).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(
        endpoint, data=payload, headers=headers, method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        _fatal(f"API error {exc.code}: {body}")
    except urllib.error.URLError as exc:
        _fatal(f"Network error reaching {endpoint}: {exc.reason}")
    except json.JSONDecodeError as exc:
        _fatal(f"Malformed JSON in API response: {exc}")


# ---------------------------------------------------------------------------
# Agentic execution loop
# ---------------------------------------------------------------------------

def _run_executor(
    endpoint: str,
    api_key: str,
    model: str,
    system_prompt: str,
    initial_message: str,
    max_tokens: int,
    max_turns: int,
    project_root: pathlib.Path,
) -> str:
    """Run the executor model in an agentic loop, handling tool calls.

    Sends the initial message, then for each response:
    - If tool calls are present, executes them and feeds results back.
    - If no tool calls, returns the final response text.
    Stops after max_turns to prevent runaway loops.

    Parameters:
        endpoint (str):        API endpoint URL.
        api_key (str):         Bearer token.
        model (str):           Model identifier.
        system_prompt (str):   System instructions for the executor.
        initial_message (str): First user message (task + file contents).
        max_tokens (int):      Maximum tokens per API call.
        max_turns (int):       Maximum conversation turns before aborting.
        project_root (pathlib.Path): Project root for tool file access.

    Returns:
        str: Final text response from the executor model.

    Raises:
        SystemExit(1): If max_turns is exceeded or an API error occurs.
    """
    parser   = ToolCallParser()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": initial_message},
    ]
    # Cache of (tool_name, frozen_params) -> result to short-circuit repeats
    call_cache: dict[tuple, str] = {}

    for turn in range(1, max_turns + 1):
        response = _api_request(endpoint, api_key, model, messages, max_tokens)

        try:
            content = response["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError) as exc:
            _fatal(f"Unexpected API response structure: {exc}\n{response}")

        # Append assistant turn to history
        messages.append({"role": "assistant", "content": content})

        if not parser.has_tool_calls(content):
            # No tool calls — this is the final answer
            return content

        # Parse and execute tool calls
        _, calls = parser.parse(content)
        if not calls:
            # Parser found patterns but could not extract valid calls
            return content

        results: list[str] = []
        for call in calls:
            cache_key = (call.name, json.dumps(call.parameters, sort_keys=True))
            if cache_key in call_cache:
                cached = call_cache[cache_key]
                print(
                    f"[turn {turn}] duplicate call {call.name}({call.parameters}) "
                    "— returning cached result",
                    file=sys.stderr,
                )
                results.append(
                    f"[DUPLICATE — already answered] {cached}\n"
                    "This call was already made and answered. "
                    "Do NOT call it again. Use the result above to continue."
                )
            else:
                result = _dispatch_tool(call, project_root)
                call_cache[cache_key] = result
                results.append(result)

        print(
            f"[turn {turn}] {len(calls)} tool call(s): "
            + ", ".join(f"{c.name}({c.parameters})" for c in calls),
            file=sys.stderr,
        )

        tool_message = _format_tool_results(calls, results)
        messages.append({"role": "user", "content": tool_message})

    _fatal(
        f"Executor exceeded {max_turns} turns without producing a final response. "
        "Increase max_turns in planner_config.toml if the task is large."
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fatal(message: str) -> None:
    """Print an error to stderr and exit with code 1.

    Parameters:
        message (str): Human-readable error description.
    """
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Parse arguments, load config, run the executor loop, print the result."""
    if len(sys.argv) < 2:
        print("Usage: slicer.py <slice_json> [project_root]", file=sys.stderr)
        sys.exit(1)

    try:
        slice_data = json.loads(sys.argv[1])
    except json.JSONDecodeError as exc:
        _fatal(f"Invalid slice JSON: {exc}")

    project_root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else os.getcwd())
    config       = _load_config(project_root)
    model_cfg    = _resolve_model_config(config)

    if not model_cfg["api_key"] and "localhost" not in model_cfg["endpoint"]:
        _fatal("api_key is empty in planner_config.toml.\n\n" + _CONFIG_HELP)

    target_files   = slice_data.get("target_files", [])
    file_contents  = _read_target_files(project_root, target_files)
    initial_message = _build_executor_message(slice_data, file_contents)

    result = _run_executor(
        endpoint        = model_cfg["endpoint"],
        api_key         = model_cfg["api_key"],
        model           = model_cfg["name"],
        system_prompt   = _EXECUTOR_SYSTEM_PROMPT,
        initial_message = initial_message,
        max_tokens      = model_cfg["max_tokens"],
        max_turns       = model_cfg["max_turns"],
        project_root    = project_root,
    )

    print(result)


if __name__ == "__main__":
    main()
