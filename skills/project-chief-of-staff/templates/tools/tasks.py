"""Single entry point for the team task board, 00_hub/tasks/board.csv.

    python tools/tasks.py new --owner <agent> --title "..." [--item 004] [--depends T001,T002]
    python tools/tasks.py update T003 status=done summary="Wrote 02_research/2026-11-02_overview.md"
    python tools/tasks.py list [--all] [--owner <agent>]

`new` creates 00_hub/tasks/T###_<slug>/brief.md from the template; the chief of staff fills in the brief, and the owning
agent writes report.md next to it. Owners must be an agent defined in .claude/agents/, chief-of-staff or user.
"""
import argparse
import csv
import datetime as dt
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))
from tracker import slug  # noqa: E402

ROOT = Path(os.path.abspath(__file__)).parent.parent
COLUMNS = ["id", "title", "owner", "status", "item_id", "depends_on", "folder", "created", "updated", "summary"]
STATUSES = ["open", "in-progress", "blocked", "review", "done", "cancelled"]
CLOSED = {"done", "cancelled"}
READ_ONLY = {"id", "folder", "created", "updated"}
TASK_RE = re.compile(r"^T\d{3}$")

BRIEF = """# {id} · {title}

- **Owner:** {owner}
- **Tracker item:** {item_id}
- **Depends on:** {depends_on} (read their `report.md` first)
- **Created:** {created}
- **Sources:** follow `00_hub/source-policy.md` (T1 for decision-critical facts, `[T3]` labelled, gaps marked UNVERIFIED)
- **Writing:** outgoing text follows `00_hub/writing-style.md`

## Goal
_One or two sentences: the outcome, not the method._

## Inputs
_Files and folders to read. Nothing outside the project folder._

## Deliverables
_Exact paths to write. Follow the filing rule in CLAUDE.md._

## Constraints
_Scope limits, sources to use or avoid, anything the user has decided._

## Done when
_Checkable criteria._
"""


def today():
    return dt.date.today().isoformat()


def die(msg):
    sys.exit(f"ERROR: {msg}")


def paths(root):
    root = Path(os.path.abspath(root))
    return root, root / "00_hub" / "tasks" / "board.csv", root / "00_hub" / "tasks"


def agent_names(root):
    agents = Path(root) / ".claude" / "agents"
    names = {p.stem for p in agents.glob("*.md")} if agents.is_dir() else set()
    return names | {"chief-of-staff", "user"}


def load(csv_path):
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != COLUMNS:
            die(f"{csv_path} header does not match the expected columns:\n  {','.join(COLUMNS)}")
        return list(reader)


def save(csv_path, rows):
    tmp = csv_path.with_suffix(".csv.tmp")
    with open(tmp, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, csv_path)


def norm_id(tid):
    tid = tid.upper()
    if not tid.startswith("T"):
        tid = "T" + tid
    tid = "T" + tid[1:].zfill(3)
    if not TASK_RE.match(tid):
        die(f"bad task id '{tid}'")
    return tid


def find(rows, tid):
    tid = norm_id(tid)
    for r in rows:
        if r["id"] == tid:
            return r
    die(f"no task {tid}")


def parse_depends(value, rows):
    ids = [norm_id(x.strip()) for x in value.replace(";", ",").split(",") if x.strip()]
    known = {r["id"] for r in rows}
    for i in ids:
        if i not in known:
            die(f"depends_on refers to unknown task {i}")
    return ";".join(ids)


def cmd_new(args, root):
    root, csv_path, tasks_dir = paths(root)
    rows = load(csv_path)
    if args.owner not in agent_names(root):
        die(f"unknown owner '{args.owner}'. Known: {', '.join(sorted(agent_names(root)))}")
    next_id = f"T{max([int(r['id'][1:]) for r in rows] + [0]) + 1:03d}"
    folder = f"{next_id}_{slug(args.title, 40)}"
    row = {c: "" for c in COLUMNS}
    row.update(id=next_id, title=args.title, owner=args.owner, status="open",
               item_id=args.item.zfill(3) if args.item else "",
               depends_on=parse_depends(args.depends or "", rows), folder=folder, created=today(), updated=today())
    (tasks_dir / folder).mkdir(parents=True)
    (tasks_dir / folder / "brief.md").write_text(
        BRIEF.format(**{k: (row[k] or "-") for k in COLUMNS}), encoding="utf-8")
    rows.append(row)
    save(csv_path, rows)
    print(f"created {next_id} -> 00_hub/tasks/{folder}/brief.md (owner={args.owner})")


def cmd_update(args, root):
    root, csv_path, _ = paths(root)
    rows = load(csv_path)
    row = find(rows, args.id)
    for pair in args.pairs:
        if "=" not in pair:
            die(f"expected key=value, got '{pair}'")
        key, value = (s.strip() for s in pair.split("=", 1))
        if key not in COLUMNS:
            die(f"unknown column '{key}'")
        if key in READ_ONLY:
            die(f"'{key}' is managed by the script")
        if key == "status" and value not in STATUSES:
            die(f"status must be one of {STATUSES}")
        if key == "owner" and value not in agent_names(root):
            die(f"unknown owner '{value}'")
        if key == "depends_on":
            value = parse_depends(value, rows)
        row[key] = value
    row["updated"] = today()
    save(csv_path, rows)
    print(f"updated {row['id']}: " + ", ".join(args.pairs))


def cmd_list(args, root):
    _, csv_path, _ = paths(root)
    rows = load(csv_path)
    if args.owner:
        rows = [r for r in rows if r["owner"] == args.owner]
    if not args.all:
        rows = [r for r in rows if r["status"] not in CLOSED]
    if not rows:
        print("(no matching tasks)")
        return
    for r in rows:
        dep = f" after {r['depends_on']}" if r["depends_on"] else ""
        print(f"{r['id']} {r['status']:<11} {r['owner']:<20} {r['title']}{dep}"
              + (f"  | {r['summary']}" if r["summary"] else ""))


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=ROOT)
    sub = p.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new", help="create a task and its brief")
    n.add_argument("--owner", required=True)
    n.add_argument("--title", required=True)
    n.add_argument("--item", help="tracker item id this task belongs to")
    n.add_argument("--depends", help="comma-separated task ids")
    u = sub.add_parser("update", help="set fields: key=value ...")
    u.add_argument("id")
    u.add_argument("pairs", nargs="+")
    ls = sub.add_parser("list", help="list open tasks")
    ls.add_argument("--all", action="store_true")
    ls.add_argument("--owner")
    args = p.parse_args()
    {"new": cmd_new, "update": cmd_update, "list": cmd_list}[args.cmd](args, args.root)


if __name__ == "__main__":
    main()
