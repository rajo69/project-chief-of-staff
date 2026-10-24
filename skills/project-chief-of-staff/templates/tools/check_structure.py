"""Audit the project layout against the rules in CLAUDE.md and 00_hub/project.config.json.

    python tools/check_structure.py          # full report; exit 1 on errors
    python tools/check_structure.py --hook   # Claude Code Stop hook: exit 2 (blocks stopping) on errors

Errors: stray files at the root, missing top-level folders or hub files, a bad tracker CSV, tracker rows and item
folders out of step, a task board out of step with its folders, an activity log older than the latest change, and
(when the config sets max_path) paths too long for Windows with long paths disabled.
"""
import csv
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))
from tasks import COLUMNS as TASK_COLUMNS, STATUSES as TASK_STATUSES  # noqa: E402
from tracker import FOLDER_RE, Tracker  # noqa: E402

ROOT = Path(os.path.abspath(__file__)).parent.parent  # abspath, not resolve: measure the path Windows actually sees
HUB_FILES = ["HANDOFF.md", "activity-log.md", "decisions.md", "lessons.md", "team-charter.md", "project.config.json",
             "writing-style.md", "source-policy.md", "tasks/board.csv"]
ALWAYS_TOOLING = {".git", ".claude", ".mcp.json", "CLAUDE.local.md", "__pycache__"}
SLACK_SECONDS = 2


def load_structure(root):
    try:
        return json.loads((root / "00_hub" / "project.config.json").read_text(encoding="utf-8")).get("structure", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def check_tracker(root, errors, warnings):
    try:
        t = Tracker(root)
    except SystemExit as e:
        errors.append(f"tracker config: {e}")
        return
    rows = []
    try:
        with open(t.csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != t.columns:
                errors.append(f"{t.rel(t.csv_path)} header does not match the config; it must be: " + ",".join(t.columns))
            else:
                rows = list(reader)
    except FileNotFoundError:
        errors.append(f"{t.rel(t.csv_path)} is missing")
    seen = set()
    for r in rows:
        rid = r["id"]
        if not (len(rid) == 3 and rid.isdigit()):
            errors.append(f"tracker id '{rid}' is not 3 digits")
        if rid in seen:
            errors.append(f"tracker id {rid} is duplicated")
        seen.add(rid)
        for k, v in r.items():
            err = t.problem(k, v or "")
            if err:
                errors.append(f"tracker {rid}: {err}")
        if t.folder_dir:
            if not r["folder"] and r["status"] not in t.folderless:
                errors.append(f"tracker {rid} is '{r['status']}' but has no folder; run tools/tracker.py promote {rid}")
            if r["folder"] and not (t.folder_dir / r["folder"]).is_dir():
                errors.append(f"tracker {rid} points to missing folder {t.rel(t.folder_dir)}/{r['folder']}")
    if t.folder_dir and t.folder_dir.is_dir():
        tracked = {r["folder"] for r in rows if r["folder"]}
        for p in t.folder_dir.iterdir():
            if p.name in {"README.md", "_template", ".gitkeep"}:
                continue
            where = t.rel(t.folder_dir)
            if not p.is_dir():
                errors.append(f"loose file in {where}/: '{p.name}'. It belongs inside an item folder.")
            elif not FOLDER_RE.match(p.name):
                errors.append(f"badly named item folder '{where}/{p.name}' (expected NNN-TYPE_Name)")
            elif p.name not in tracked:
                errors.append(f"item folder '{where}/{p.name}' has no tracker row; folders are created by tracker.py promote")


def check_tasks(root, errors, warnings):
    tasks_dir = root / "00_hub" / "tasks"
    rows = []
    try:
        with open(tasks_dir / "board.csv", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != TASK_COLUMNS:
                errors.append("00_hub/tasks/board.csv header is wrong; it must be: " + ",".join(TASK_COLUMNS))
            else:
                rows = list(reader)
    except FileNotFoundError:
        return  # reported as a missing hub file
    folders = {r["folder"] for r in rows}
    for r in rows:
        if r["status"] not in TASK_STATUSES:
            errors.append(f"task {r['id']}: bad status '{r['status']}'")
        if not (tasks_dir / r["folder"]).is_dir():
            errors.append(f"task {r['id']} points to missing folder 00_hub/tasks/{r['folder']}")
        elif r["status"] == "done" and not (tasks_dir / r["folder"] / "report.md").exists():
            warnings.append(f"task {r['id']} is done but has no report.md")
    for p in tasks_dir.iterdir():
        if p.is_dir() and p.name not in folders:
            errors.append(f"task folder '{p.name}' has no board row; create tasks with tools/tasks.py new")


def check(root):
    errors, warnings = [], []
    s = load_structure(root)
    if not s:
        errors.append("00_hub/project.config.json is missing or has no 'structure' section")
    folders = s.get("folders", [])
    root_files = set(s.get("root_files", ["CLAUDE.md", "README.md", ".gitignore"]))
    tooling = ALWAYS_TOOLING | set(s.get("root_tooling", []))
    max_path = s.get("max_path")

    # 1. the root holds only the allowed files and folders
    for p in root.iterdir():
        if p.name not in root_files | tooling | set(folders):
            errors.append(f"stray at project root: '{p.name}'. File it in the right folder (CLAUDE.md, filing rule).")
    for name in folders:
        if not (root / name).is_dir():
            errors.append(f"missing top-level folder: {name}/")
    for name in HUB_FILES:
        if not (root / "00_hub" / name).exists():
            errors.append(f"missing hub file 00_hub/{name}")

    # 2. the tracker and the task board are consistent with their folders
    check_tracker(root, errors, warnings)
    check_tasks(root, errors, warnings)

    # 3. the activity log is not older than the latest change; paths stay short where they must
    log = root / "00_hub" / "activity-log.md"
    if log.exists():
        log_mtime = log.stat().st_mtime
        newer = []
        for p in root.rglob("*"):
            rel = p.relative_to(root)
            if rel.parts[0] in tooling or "__pycache__" in rel.parts:
                continue
            if max_path and len(str(p)) > max_path:
                errors.append(f"path is {len(str(p))} chars, over the {max_path} limit (Windows long paths are off): "
                              f"{rel.as_posix()}. Shorten it.")
            if p.is_file() and p != log and p.stat().st_mtime > log_mtime + SLACK_SECONDS:
                newer.append((p.stat().st_mtime, rel.as_posix()))
        if newer:
            newer.sort(reverse=True)
            listed = ", ".join(n for _, n in newer[:6]) + (" ..." if len(newer) > 6 else "")
            errors.append(f"00_hub/activity-log.md is older than {len(newer)} changed file(s) ({listed}). "
                          "Append an entry: what was done, files changed, next step.")

    # 4. every top-level folder explains itself
    for name in folders:
        if (root / name).is_dir() and not (root / name / "README.md").exists():
            warnings.append(f"{name}/ has no README.md")
    return errors, warnings


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    hook = "--hook" in sys.argv
    if hook:
        try:
            payload = json.load(sys.stdin)
        except (json.JSONDecodeError, ValueError):
            payload = {}
        if payload.get("stop_hook_active"):
            sys.exit(0)  # already blocked once this turn; don't loop
    errors, warnings = check(ROOT)
    if hook:
        if errors:
            print("Project structure check failed (tools/check_structure.py). Fix before finishing:\n- "
                  + "\n- ".join(errors[:20]), file=sys.stderr)
            sys.exit(2)
        sys.exit(0)
    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"WARN    {w}")
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
