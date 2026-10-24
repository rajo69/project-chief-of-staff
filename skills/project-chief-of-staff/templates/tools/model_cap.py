"""PreToolUse hook for the Agent tool: block a subagent launch whose `model` is above the project's cap.

The cap is `models.cap` in 00_hub/project.config.json (fable, opus or sonnet). A launch without a `model`
uses the agent file's own model, which the setup already kept at or below the cap, so it passes.
"""
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(os.path.abspath(__file__)).parent.parent
RANK = {"haiku": 0, "sonnet": 1, "opus": 2, "fable": 3}


def rank(model):
    m = (model or "").lower()
    found = [r for name, r in RANK.items() if name in m]
    return max(found) if found else None


def main():
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)
    model = str((payload.get("tool_input") or {}).get("model") or "")
    if not model or model == "inherit":
        sys.exit(0)
    try:
        cap = json.loads((ROOT / "00_hub" / "project.config.json").read_text(encoding="utf-8"))["models"]["cap"]
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        sys.exit(0)
    asked, limit = rank(model), RANK.get(cap)
    if asked is not None and limit is not None and asked > limit:
        print(f"Blocked by tools/model_cap.py: model '{model}' is above this project's cap ({cap}). "
              f"Use {cap} or lower, or omit model to use the agent's default (CLAUDE.md §6).", file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
