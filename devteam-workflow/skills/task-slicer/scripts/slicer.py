#!/usr/bin/env python3
"""
Slice executor: sends a single task slice to a configured executor model and
prints the response. The planner (Claude) produces the slice plan; this script
executes individual slices against a weaker model via an OpenAI-compatible API.

Usage:
    slicer.py <slice_json> [project_root]

Arguments:
    slice_json    JSON string of a single slice object (id, description,
                  target_files, acceptance_criteria, context, risk_level).
    project_root  Path to the project root (default: current directory).
                  Used to locate .claude/planner_config.toml and to read the
                  contents of target_files.

Exit codes:
    0  Success — executor model response printed to stdout.
    1  Configuration error, API failure, or invalid slice — error on stderr.
"""

import json
import os
import pathlib
import sys
import urllib.error
import urllib.request


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
""".format(filename=_CONFIG_FILENAME)

_IGNORED_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".tox", "htmlcov", "coverage",
}

_EXECUTOR_SYSTEM_PROMPT = """\
You are a code implementation assistant. You will be given a specific, \
scoped coding task to implement. Apply the changes described and return \
the complete updated contents of every file you modify or create.

Rules:
- Make ONLY the changes described in the task. Do not refactor unrelated code.
- For each file changed or created, output it using this exact format:

=== FILE: <relative/path/to/file> ===
<complete file contents>
=== END FILE ===

- If a file is not modified, do not include it in the output.
- Do not include any explanatory text outside the FILE blocks.
- Follow the existing code style and patterns shown in the current file contents.
- Satisfy all acceptance criteria listed in the task.
"""


def _load_config(project_root: pathlib.Path) -> dict:
    """
    Load and parse planner_config.toml from <project_root>/.claude/.

    Parameters:
        project_root (pathlib.Path): Root directory of the active project.

    Returns:
        dict: Parsed configuration with at minimum a 'model' sub-dict
              containing 'endpoint', 'api_key', 'name'.

    Raises:
        SystemExit(1): If the config file does not exist or cannot be parsed.
    """
    config_path = project_root / ".claude" / _CONFIG_FILENAME
    if not config_path.exists():
        _fatal(
            f"Config file not found: {config_path}\n\n{_CONFIG_HELP}"
        )

    text = config_path.read_text(encoding="utf-8")
    return _parse_toml(text)


def _parse_toml(text: str) -> dict:
    """
    Parse TOML text, using the stdlib tomllib (3.11+) when available,
    then tomli, then a minimal hand-rolled parser for simple configs.

    Parameters:
        text (str): Raw TOML content.

    Returns:
        dict: Parsed key/value structure.
    """
    try:
        import tomllib  # Python 3.11+
        return tomllib.loads(text)
    except ImportError:
        pass

    try:
        import tomli  # pip install tomli
        return tomli.loads(text)
    except ImportError:
        pass

    return _minimal_toml_parse(text)


def _minimal_toml_parse(text: str) -> dict:
    """
    Minimal TOML parser: handles [sections] and key = "value" / key = number.
    Sufficient for the flat planner_config.toml schema.

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
    """
    Extract model settings, supporting both [model] section and flat layout.

    Parameters:
        config (dict): Full parsed TOML config.

    Returns:
        dict: Flat dict with keys: endpoint, api_key, name, max_tokens.
    """
    base = config.get("model", config)
    return {
        "endpoint":   base.get("endpoint", "https://api.openai.com/v1/chat/completions"),
        "api_key":    str(base.get("api_key", "")),
        "name":       str(base.get("name", "gpt-4o-mini")),
        "max_tokens": int(base.get("max_tokens", 4096)),
    }


# ---------------------------------------------------------------------------
# File reading
# ---------------------------------------------------------------------------

def _read_target_files(
    project_root: pathlib.Path,
    target_files: list[str],
) -> dict[str, str]:
    """
    Read the current contents of each target file relative to project_root.

    Parameters:
        project_root (pathlib.Path): Project root directory.
        target_files (list[str]):    Relative file paths from the slice.

    Returns:
        dict[str, str]: Map of relative path -> file contents (or an error
                        note if the file cannot be read).
    """
    contents: dict[str, str] = {}
    for rel_path in target_files:
        full_path = project_root / rel_path
        if full_path.exists() and full_path.is_file():
            try:
                contents[rel_path] = full_path.read_text(encoding="utf-8")
            except OSError as exc:
                contents[rel_path] = f"[Could not read file: {exc}]"
        else:
            contents[rel_path] = "[File does not exist yet — create it]"
    return contents


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------

def _build_executor_message(
    slice_data: dict,
    file_contents: dict[str, str],
) -> str:
    """
    Build the user message for the executor model from the slice data and the
    current contents of the target files.

    Parameters:
        slice_data (dict):            The single slice object from the plan.
        file_contents (dict[str,str]): Map of relative path -> current file text.

    Returns:
        str: Fully formatted message to send as the user turn.

    Example usage:
        msg = _build_executor_message(slice, {"src/foo.py": "..."})
    """
    parts: list[str] = []

    parts.append(f"## Task: {slice_data.get('id', 'unknown')}")
    parts.append(f"\n{slice_data.get('description', '')}")

    criteria = slice_data.get("acceptance_criteria", [])
    if criteria:
        parts.append("\n## Acceptance criteria")
        for criterion in criteria:
            parts.append(f"- {criterion}")

    context = slice_data.get("context", "").strip()
    if context:
        parts.append(f"\n## Context\n{context}")

    if file_contents:
        parts.append("\n## Current file contents")
        for rel_path, content in file_contents.items():
            parts.append(f"\n### {rel_path}\n```\n{content}\n```")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# API call
# ---------------------------------------------------------------------------

def _call_api(
    endpoint: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_message: str,
    max_tokens: int,
) -> str:
    """
    Send a single chat-completion request to the configured OpenAI-compatible
    endpoint and return the assistant message content.

    Parameters:
        endpoint (str):      Full URL of the chat completions endpoint.
        api_key (str):       Bearer token for the API.
        model (str):         Model identifier (e.g. "gpt-4o-mini").
        system_prompt (str): Executor system prompt.
        user_message (str):  Slice task description + current file contents.
        max_tokens (int):    Maximum tokens in the response.

    Returns:
        str: Raw content string from the first choice.

    Raises:
        SystemExit(1): On HTTP error or network failure.
    """
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        "max_tokens": max_tokens,
        "temperature": 0,
    }).encode("utf-8")

    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read())
        return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        _fatal(f"API error {exc.code}: {body}")
    except urllib.error.URLError as exc:
        _fatal(f"Network error reaching {endpoint}: {exc.reason}")
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        _fatal(f"Unexpected API response format: {exc}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fatal(message: str) -> None:
    """
    Print an error message to stderr and exit with code 1.

    Parameters:
        message (str): Human-readable error description.
    """
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Parse arguments, load configuration, read target file contents, call the
    executor model with the slice task, and print the response to stdout.
    """
    if len(sys.argv) < 2:
        print(
            "Usage: slicer.py <slice_json> [project_root]",
            file=sys.stderr,
        )
        sys.exit(1)

    # Parse slice JSON
    try:
        slice_data = json.loads(sys.argv[1])
    except json.JSONDecodeError as exc:
        _fatal(f"Invalid slice JSON: {exc}")

    project_root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else os.getcwd())
    config       = _load_config(project_root)
    model_cfg    = _resolve_model_config(config)

    if not model_cfg["api_key"]:
        _fatal("api_key is empty in planner_config.toml.\n\n" + _CONFIG_HELP)

    target_files  = slice_data.get("target_files", [])
    file_contents = _read_target_files(project_root, target_files)
    user_message  = _build_executor_message(slice_data, file_contents)

    response = _call_api(
        endpoint      = model_cfg["endpoint"],
        api_key       = model_cfg["api_key"],
        model         = model_cfg["name"],
        system_prompt = _EXECUTOR_SYSTEM_PROMPT,
        user_message  = user_message,
        max_tokens    = model_cfg["max_tokens"],
    )

    print(response)


if __name__ == "__main__":
    main()
