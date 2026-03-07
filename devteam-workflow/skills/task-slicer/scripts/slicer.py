#!/usr/bin/env python3
"""
Task slicer: decomposes a user request into task slices for delegation to an
executor model. Sends the planner prompt + request + file tree to an
OpenAI-compatible API endpoint configured in .claude/planner_config.toml.

Usage:
    slicer.py <user_request> [project_root]

Arguments:
    user_request   Description of the implementation task to slice.
    project_root   Path to the project root (default: current directory).
                   Used to locate .claude/planner_config.toml and build the
                   file tree.

Exit codes:
    0  Success — JSON slice plan printed to stdout.
    1  Configuration error or API failure — error printed to stderr.
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
  name       = "gpt-4o"
  max_slices = 8
  max_tokens = 4096
""".format(filename=_CONFIG_FILENAME)

_IGNORED_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    ".tox", "htmlcov", "coverage",
}


def _load_config(project_root: pathlib.Path) -> dict:
    """
    Load and parse planner_config.toml from <project_root>/.claude/.

    Parameters:
        project_root (pathlib.Path): Root directory of the active project.

    Returns:
        dict: Parsed configuration with at minimum a 'model' sub-dict
              containing 'endpoint', 'api_key', 'name', 'max_slices'.

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
            # Strip quotes
            if (v.startswith('"') and v.endswith('"')) or \
               (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            else:
                # Try int/float coercion
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
        dict: Flat dict with keys: endpoint, api_key, name, max_slices,
              max_tokens.
    """
    base = config.get("model", config)
    return {
        "endpoint": base.get(
            "endpoint", "https://api.openai.com/v1/chat/completions"
        ),
        "api_key":    str(base.get("api_key", "")),
        "name":       str(base.get("name", "gpt-4o")),
        "max_slices": int(base.get("max_slices", 8)),
        "max_tokens": int(base.get("max_tokens", 4096)),
    }


# ---------------------------------------------------------------------------
# File tree
# ---------------------------------------------------------------------------

def _build_file_tree(root: pathlib.Path, max_files: int = 300) -> str:
    """
    Build a compact indented file tree string, excluding common noise dirs.

    Parameters:
        root (pathlib.Path): Project root to walk.
        max_files (int): Maximum number of files to include before truncating.

    Returns:
        str: Multi-line indented tree, suitable for inclusion in a prompt.

    Example usage:
        tree = _build_file_tree(pathlib.Path("."))
    """
    lines: list[str] = []
    count = 0

    for path in sorted(root.rglob("*")):
        if count >= max_files:
            lines.append(f"  ... (truncated at {max_files} entries)")
            break
        try:
            parts = path.relative_to(root).parts
        except ValueError:
            continue
        if any(p in _IGNORED_DIRS or p.endswith(".egg-info") for p in parts):
            continue
        if path.is_file():
            indent = "  " * (len(parts) - 1)
            lines.append(f"{indent}{path.name}")
            count += 1

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Planner prompt
# ---------------------------------------------------------------------------

def _load_system_prompt(script_dir: pathlib.Path, max_slices: int) -> str:
    """
    Load the planner system prompt from planner-prompt.md in the skill root
    (one level above the scripts/ directory), then substitute {max_slices}.

    Parameters:
        script_dir (pathlib.Path): Directory containing this script.
        max_slices (int): Maximum slices to allow; substituted into the prompt.

    Returns:
        str: Fully rendered system prompt.

    Raises:
        SystemExit(1): If planner-prompt.md cannot be found.
    """
    candidates = [
        script_dir.parent / "planner-prompt.md",
        script_dir / "planner-prompt.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.read_text(encoding="utf-8").replace(
                "{max_slices}", str(max_slices)
            )

    _fatal(
        "planner-prompt.md not found. Expected at: "
        + str(candidates[0])
    )


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
        endpoint (str): Full URL of the chat completions endpoint.
        api_key (str): Bearer token for the API.
        model (str): Model identifier (e.g. "gpt-4o").
        system_prompt (str): Planner system prompt.
        user_message (str): User request + file tree.
        max_tokens (int): Maximum tokens in the response.

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
        with urllib.request.urlopen(request, timeout=90) as response:
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
# Output
# ---------------------------------------------------------------------------

def _extract_json(raw: str) -> str:
    """
    Strip markdown code fences that some models wrap around JSON output.

    Parameters:
        raw (str): Raw string from the model response.

    Returns:
        str: String with leading/trailing fences removed.
    """
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        start = 1
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[start:end])
    return text


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
    Parse arguments, load configuration, build the file tree, call the API,
    and print the JSON slice plan to stdout.
    """
    if len(sys.argv) < 2:
        print(
            "Usage: slicer.py <user_request> [project_root]",
            file=sys.stderr,
        )
        sys.exit(1)

    user_request = sys.argv[1]
    project_root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else os.getcwd())
    script_dir   = pathlib.Path(__file__).parent

    config     = _load_config(project_root)
    model_cfg  = _resolve_model_config(config)

    if not model_cfg["api_key"]:
        _fatal(
            "api_key is empty in planner_config.toml.\n\n" + _CONFIG_HELP
        )

    system_prompt = _load_system_prompt(script_dir, model_cfg["max_slices"])
    file_tree     = _build_file_tree(project_root)
    user_message  = (
        f"User request: {user_request}\n\n"
        f"Project file tree:\n{file_tree}"
    )

    raw    = _call_api(
        endpoint      = model_cfg["endpoint"],
        api_key       = model_cfg["api_key"],
        model         = model_cfg["name"],
        system_prompt = system_prompt,
        user_message  = user_message,
        max_tokens    = model_cfg["max_tokens"],
    )
    clean  = _extract_json(raw)

    try:
        parsed = json.loads(clean)
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        # Model returned non-JSON — print as-is so the user can see it
        print(clean)


if __name__ == "__main__":
    main()
