"""Single entry point for changing the main tracker (its CSV path, item types, statuses and columns are set in
00_hub/project.config.json under "tracker").

    python tools/tracker.py add TYPE "Title" [column=value ...] [--force]
    python tools/tracker.py promote 004
    python tools/tracker.py update 004 status=active next_action="..." next_action_due=2026-11-02
    python tools/tracker.py list [--all] [--status STATUS] [--type TYPE]
    python tools/tracker.py schema

Keeps ids unique, dates ISO, types and statuses valid, and every promoted row paired with its item folder.
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import shutil
import sys
import unicodedata
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(os.path.abspath(__file__)).parent.parent
CONFIG_PATH = ROOT / "00_hub" / "project.config.json"

HEAD = ["id", "type", "status", "priority", "title"]
TAIL = ["folder", "next_action", "next_action_due", "added", "updated", "notes"]
MANAGED = {"id", "folder", "added", "updated"}
FOLDER_RE = re.compile(r"^\d{3}-[A-Z0-9]{2,6}_[A-Za-z0-9_-]+$")


def die(msg):
    sys.exit(f"ERROR: {msg}")


def today():
    return dt.date.today().isoformat()


class Tracker:
    """The tracker's rules, read from the config so every project can shape its own."""

    def __init__(self, root=ROOT):
        self.root = Path(root)
        cfg_path = self.root / "00_hub" / "project.config.json"
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))["tracker"]
        except FileNotFoundError:
            die(f"missing {cfg_path}")
        except (KeyError, json.JSONDecodeError) as e:
            die(f"{cfg_path} has no valid 'tracker' section ({e})")
        self.item = cfg.get("item", "item")
        self.items = cfg.get("items", self.item + "s")
        self.csv_path = self.root / cfg.get("csv", "00_hub/tracker.csv")
        self.types = cfg["types"]  # {"CODE": "meaning"}
        self.statuses = cfg["statuses"]
        self.terminal = set(cfg.get("terminal", []))
        self.start = cfg.get("start_status", self.statuses[0])
        self.promoted = cfg.get("promoted_status", self.statuses[1] if len(self.statuses) > 1 else self.start)
        self.folderless = set(cfg.get("folderless_statuses", [self.start])) | self.terminal
        self.folder_dir = self.root / cfg["folder_dir"] if cfg.get("folder_dir") else None
        self.folder_fields = cfg.get("folder_fields", ["title"])
        self.dedupe_fields = cfg.get("dedupe_fields", ["title"])
        self.url_field = cfg.get("url_field")
        self.custom = cfg.get("columns", [])  # [{"name", "kind": text|date|enum|upper|url, "values": [...]}]
        self.columns = HEAD + [c["name"] for c in self.custom] + TAIL
        self.kinds = {c["name"]: c for c in self.custom}
        self.kinds["priority"] = {"name": "priority", "kind": "enum", "values": ["", "A", "B", "C"]}
        self.kinds["next_action_due"] = {"name": "next_action_due", "kind": "date"}
        self.kinds["added"] = self.kinds["updated"] = {"kind": "date"}
        self.list_fields = cfg.get("list_fields", [])

    # -- storage ---------------------------------------------------------------
    def load(self):
        try:
            with open(self.csv_path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames != self.columns:
                    die(f"{self.rel(self.csv_path)} header does not match the config. Expected:\n  {','.join(self.columns)}")
                return list(reader)
        except FileNotFoundError:
            die(f"missing {self.rel(self.csv_path)}")

    def save(self, rows):
        tmp = self.csv_path.with_suffix(".csv.tmp")
        with open(tmp, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=self.columns)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp, self.csv_path)

    def rel(self, p):
        return Path(p).relative_to(self.root).as_posix()

    # -- validation ------------------------------------------------------------
    def problem(self, key, value):
        """Return an error message for a bad value, or None."""
        if key not in self.columns:
            return f"unknown column '{key}'. Columns: {', '.join(self.columns)}"
        if key == "type" and value not in self.types:
            return f"type must be one of {sorted(self.types)}"
        if key == "status" and value not in self.statuses:
            return f"status must be one of {self.statuses}"
        spec = self.kinds.get(key, {})
        kind = spec.get("kind", "text")
        if value and kind == "date":
            try:
                dt.date.fromisoformat(value)
            except ValueError:
                return f"{key} must be YYYY-MM-DD, got '{value}'"
        if kind == "enum" and value not in spec.get("values", []) and not (value == "" and "" in spec.get("values", [""])):
            return f"{key} must be one of {spec.get('values')}"
        return None

    def normalise(self, key, value):
        value = value.strip()
        if key in {"type", "priority"} or self.kinds.get(key, {}).get("kind") == "upper":
            value = value.upper()
        return value

    def find(self, rows, rid):
        rid = rid.zfill(3)
        for r in rows:
            if r["id"] == rid:
                return r
        die(f"no {self.item} with id {rid}")

    def folder_name(self, row):
        # short enough that files nested inside stay well under Windows' 260-character limit
        parts = [slug(row.get(f, ""), 30 if f == "title" else 22) for f in self.folder_fields]
        name = f"{row['id']}-{row['type']}_" + "_".join(p for p in parts if p)
        return name.rstrip("_-") if parts else name


def slug(text, max_len):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    words = [w for w in re.split(r"[^A-Za-z0-9]+", text) if w]
    out = ""
    for w in words:
        candidate = f"{out}-{w}" if out else w
        if len(candidate) > max_len:
            break
        out = candidate
    return out or ("Untitled" if max_len >= 8 else "")


def pairs_to_dict(t, pairs):
    out = {}
    for pair in pairs:
        if "=" not in pair:
            die(f"expected column=value, got '{pair}'")
        key, value = pair.split("=", 1)
        key = key.strip().replace("-", "_")
        out[key] = t.normalise(key, value)
    return out


# -- commands ------------------------------------------------------------------
def cmd_add(t, args):
    rows = t.load()
    fields = pairs_to_dict(t, args.pairs)
    row = {c: "" for c in t.columns}
    row.update(fields)
    row.update(type=args.type.upper(), title=args.title.strip(), status=t.start, added=today(), updated=today())
    for k in MANAGED - {"added", "updated"}:
        if k in fields:
            die(f"'{k}' is managed by the script")
    for k, v in row.items():
        err = t.problem(k, v)
        if err:
            die(err)
    if not args.force:
        for r in rows:
            same_url = t.url_field and row[t.url_field] and r[t.url_field].strip() == row[t.url_field]
            same_key = all(r[f].strip().lower() == row[f].lower() for f in t.dedupe_fields)
            if same_url or same_key:
                die(f"looks like a duplicate of {r['id']} ({r['title']}). Use --force if it is not.")
    row["id"] = f"{max([int(r['id']) for r in rows] + [0]) + 1:03d}"
    rows.append(row)
    t.save(rows)
    print(f"added {row['id']} [{row['type']}] {row['title']} (status={row['status']})")


def cmd_promote(t, args):
    if not t.folder_dir:
        die("this tracker has no item folders (tracker.folder_dir is empty in the config)")
    rows = t.load()
    row = t.find(rows, args.id)
    if row["folder"]:
        die(f"{row['id']} already has folder {row['folder']}")
    if row["status"] in t.terminal:
        die(f"{row['id']} is {row['status']}; reopen it with update status={t.start} first")
    name = t.folder_name(row)
    if not FOLDER_RE.match(name):
        die(f"generated folder name '{name}' is invalid; check the title and type")
    dest = t.folder_dir / name
    if dest.exists():
        die(f"{t.rel(dest)} already exists")
    template = t.folder_dir / "_template"
    if template.is_dir():
        shutil.copytree(template, dest)
    else:
        dest.mkdir(parents=True)
    for card in dest.glob("*.md"):
        text = card.read_text(encoding="utf-8")
        for k in t.columns:
            text = text.replace("{{" + k + "}}", row.get(k, "") or "")
        card.write_text(text, encoding="utf-8")
    row["folder"] = name
    if row["status"] == t.start:
        row["status"] = t.promoted
    row["updated"] = today()
    t.save(rows)
    print(f"promoted {row['id']} -> {t.rel(dest)} (status={row['status']})")


def cmd_update(t, args):
    rows = t.load()
    row = t.find(rows, args.id)
    for key, value in pairs_to_dict(t, args.pairs).items():
        if key in MANAGED:
            die(f"'{key}' is managed by the script")
        err = t.problem(key, value)
        if err:
            die(err)
        if key == "status" and t.folder_dir and value not in t.folderless and not row["folder"]:
            die(f"status '{value}' needs a folder: run 'promote {row['id']}' first")
        row[key] = value
    row["updated"] = today()
    t.save(rows)
    print(f"updated {row['id']}: " + ", ".join(args.pairs))


def cmd_list(t, args):
    rows = t.load()
    if args.status:
        rows = [r for r in rows if r["status"] == args.status]
    elif not args.all:
        rows = [r for r in rows if r["status"] not in t.terminal]
    if args.type:
        rows = [r for r in rows if r["type"] == args.type.upper()]
    date_cols = [c["name"] for c in t.custom if c.get("kind") == "date"]
    rows.sort(key=lambda r: (r["next_action_due"] or next((r[c] for c in date_cols if r[c]), "") or "9999", r["id"]))
    if not rows:
        print(f"(no matching {t.items})")
        return
    for r in rows:
        extra = " ".join(f"{f}={r[f]}" for f in t.list_fields if r.get(f))
        print(f"{r['id']} {r['type']:<4} {r['status']:<12} {r['priority'] or '-'} {r['title']}"
              + (f"  [{extra}]" if extra else "")
              + f"  | next: {r['next_action'] or '-'} ({r['next_action_due'] or '-'})")


def cmd_schema(t, args):
    print(f"item: {t.item}   csv: {t.rel(t.csv_path)}   folders: {t.rel(t.folder_dir) if t.folder_dir else '(none)'}")
    print("types: " + ", ".join(f"{k} ({v})" for k, v in t.types.items()))
    print("statuses: " + " -> ".join(s for s in t.statuses if s not in t.terminal)
          + "; terminal: " + ", ".join(s for s in t.statuses if s in t.terminal))
    print("columns: " + ", ".join(t.columns))


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", default=ROOT, help="project root (default: this project)")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add", help="add an item at the start status")
    a.add_argument("type")
    a.add_argument("title")
    a.add_argument("pairs", nargs="*", help="column=value")
    a.add_argument("--force", action="store_true", help="add even if it looks like a duplicate")
    pr = sub.add_parser("promote", help="give an item its own folder")
    pr.add_argument("id")
    u = sub.add_parser("update", help="set fields: column=value ...")
    u.add_argument("id")
    u.add_argument("pairs", nargs="+")
    ls = sub.add_parser("list", help="list open items by next due date")
    ls.add_argument("--all", action="store_true", help="include closed ones")
    ls.add_argument("--status")
    ls.add_argument("--type")
    sub.add_parser("schema", help="show types, statuses and columns")
    args = p.parse_args()
    t = Tracker(args.root)
    {"add": cmd_add, "promote": cmd_promote, "update": cmd_update, "list": cmd_list, "schema": cmd_schema}[args.cmd](t, args)


if __name__ == "__main__":
    main()
