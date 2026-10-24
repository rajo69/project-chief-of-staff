"""Print a compact project brief for a new session (run by the SessionStart hook).

    python tools/session_brief.py

Prints 00_hub/HANDOFF.md, the open tasks, and a summary of open tracker items. The output is capped because
SessionStart context is limited to 10,000 characters.
"""
import csv
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(os.path.abspath(__file__)).parent.parent
MAX_HANDOFF_LINES = 130
MAX_CHARS = 9000
CLOSED_TASKS = {"done", "cancelled"}


def rows(path):
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    out = ["=== PROJECT BRIEF (auto-loaded at session start by tools/session_brief.py) ===",
           "You are the Chief of Staff. Follow CLAUDE.md and 00_hub/team-charter.md. Delegate bulk work to the agents.",
           "Replies to the user: as short as possible without dropping key information. Lead with the answer.",
           "Research: reliable sources only (00_hub/source-policy.md). Outgoing text: 00_hub/writing-style.md.", ""]

    handoff = ROOT / "00_hub" / "HANDOFF.md"
    if handoff.exists():
        lines = handoff.read_text(encoding="utf-8").splitlines()
        out += lines[:MAX_HANDOFF_LINES]
        if len(lines) > MAX_HANDOFF_LINES:
            out.append(f"... (HANDOFF.md truncated at {MAX_HANDOFF_LINES} lines; read the file for the rest)")
    else:
        out.append("(no 00_hub/HANDOFF.md yet)")

    tasks = [r for r in rows(ROOT / "00_hub" / "tasks" / "board.csv") if r.get("status") not in CLOSED_TASKS]
    out += ["", f"--- Open tasks ({len(tasks)}) ---"]
    out += [f"{r['id']} {r['status']:<11} {r['owner']:<20} {r['title']}" for r in tasks[:15]] or ["(none)"]

    try:
        cfg = json.loads((ROOT / "00_hub" / "project.config.json").read_text(encoding="utf-8"))["tracker"]
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        cfg = None
    if cfg:
        terminal = set(cfg.get("terminal", []))
        items = [r for r in rows(ROOT / cfg.get("csv", "00_hub/tracker.csv")) if r.get("status") not in terminal]
        counts = Counter(r["status"] for r in items)
        out += ["", f"--- Open {cfg.get('items', 'items')} ({len(items)}) ---",
                ", ".join(f"{k}: {v}" for k, v in counts.items()) or "(none)"]
        due = sorted((r for r in items if r.get("next_action_due")), key=lambda r: r["next_action_due"])[:5]
        out += [f"{r['id']} due {r['next_action_due']}: {r['next_action'] or '-'} ({r['title']})" for r in due]

    text = "\n".join(out)
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n... (brief truncated; read 00_hub/HANDOFF.md in full)"
    print(text)


if __name__ == "__main__":
    main()
