"""Build a persistent, multi-agent project folder from a plan file.

    python scaffold.py probe   --target DIR                 # is DIR empty? which python? long-path guard? (JSON)
    python scaffold.py preview --plan PLAN.json [--target DIR]   # validate the plan and print the one-screen preview
    python scaffold.py build   --plan PLAN.json --target DIR [--allow-existing]

The plan format is documented in ../references/plan-format.md. Python 3.8+, standard library only.
Nothing is ever overwritten: existing files are reported as collisions and, with --allow-existing, skipped.
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
SKILL_DIR = Path(os.path.abspath(__file__)).parent.parent
TEMPLATES = SKILL_DIR / "templates"

# Entries a folder can hold and still count as empty: VCS, Claude/agent tooling, OS litter.
TOOLING = {".git", ".claude", ".mcp.json", "CLAUDE.local.md", ".agents", ".vscode", ".idea", "skills-lock.json", ".DS_Store", "Thumbs.db", "desktop.ini"}
CORE_FOLDERS = ["00_hub", "tools", "_archive", "_bin"]
TIERS = {
    "fable": {"deep": "fable", "standard": "opus", "routine": "sonnet"},
    "opus": {"deep": "opus", "standard": "sonnet", "routine": "sonnet"},
    "sonnet": {"deep": "sonnet", "standard": "sonnet", "routine": "sonnet"},
}
CAP_LABELS = {"fable": "Fable-led (Max)", "opus": "Opus cap", "sonnet": "Sonnet cap (Pro)"}
MODEL_RANK = {"sonnet": 1, "opus": 2, "fable": 3}
TIER_USE = {"deep": "deep reasoning, judgement and taste", "standard": "standard skilled work",
            "routine": "routine, high-volume or mechanical work"}
BASE_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep"]
EXTRA_TOOLS = {"WebSearch", "WebFetch", "Bash", "NotebookEdit"}
COLORS = ["blue", "green", "purple", "orange", "yellow", "cyan", "pink", "red"]
RESERVED_AGENTS = {"red-team-reviewer", "chief-of-staff", "user", "handoff"}
HEAD = ["id", "type", "status", "priority", "title"]
TAIL = ["folder", "next_action", "next_action_due", "added", "updated", "notes"]
COLUMN_KINDS = {"text", "date", "enum", "upper", "url"}
FOLDER_RE = re.compile(r"^(0[1-9]|1[0-9])_[a-z0-9][a-z0-9-]*$")
AGENT_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
TODAY = dt.date.today().isoformat()


class PlanError(Exception):
    pass


# -- environment ----------------------------------------------------------------------------------------------
def detect_python():
    """The command hooks should call: whatever on PATH actually runs Python 3 (not the Windows Store stub)."""
    candidates = [["python"], ["py", "-3"], ["python3"]] if os.name == "nt" else [["python3"], ["python"]]
    for cmd in candidates:
        if not shutil.which(cmd[0]):
            continue
        try:
            out = subprocess.run(cmd + ["-c", "import sys; print(sys.version_info[0])"], capture_output=True,
                                 text=True, timeout=15)
        except (OSError, subprocess.SubprocessError):
            continue
        if out.returncode == 0 and out.stdout.strip() == "3":
            return " ".join(cmd)
    return "python" if os.name == "nt" else "python3"


def long_paths_disabled():
    """True only on Windows with long paths off; then paths are kept under 240 characters."""
    if os.name != "nt":
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem") as key:
            return winreg.QueryValueEx(key, "LongPathsEnabled")[0] != 1
    except OSError:
        return True


def probe(target):
    target = Path(os.path.abspath(target))
    entries = sorted(p.name for p in target.iterdir()) if target.is_dir() else []
    content = [e for e in entries if e not in TOOLING]
    guard = long_paths_disabled()
    return {
        "target": str(target),
        "exists": target.is_dir(),
        "empty": target.is_dir() and not content,
        "non_tooling_entries": content[:50],
        "tooling_entries": [e for e in entries if e in TOOLING],
        "python": detect_python(),
        "os": "windows" if os.name == "nt" else sys.platform,
        "max_path": 240 if guard else None,
        "target_path_length": len(str(target)),
        "git_available": bool(shutil.which("git")),
        "npm_available": bool(shutil.which("npm")),
    }


# -- plan validation ------------------------------------------------------------------------------------------
def need(cond, msg):
    if not cond:
        raise PlanError(msg)


def validate(plan):
    """Check the plan and fill in defaults. Returns (plan, warnings)."""
    warnings = []
    p = plan.setdefault("project", {})
    need(p.get("title"), "project.title is required")
    need(p.get("objective"), "project.objective is required (one sentence)")
    p.setdefault("purpose", p["title"])
    p.setdefault("flow", "")

    m = plan.setdefault("models", {})
    need(m.get("cap") in TIERS, "models.cap must be fable, opus or sonnet")
    ms = m.get("main_session")
    need(ms in (None, "", "fable", "opus", "sonnet"), "models.main_session must be fable, opus, sonnet or null")
    need(not ms or MODEL_RANK[ms] <= MODEL_RANK[m["cap"]], "models.main_session is above the cap")

    folders = plan.get("folders") or []
    need(folders, "folders: at least one numbered domain folder is required")
    names = [f.get("name", "") for f in folders]
    for n in names:
        need(FOLDER_RE.match(n), f"folder '{n}' must look like 01_name (01-19, lowercase-kebab)")
    need(len(set(names)) == len(names), "folder names repeat")
    need(len({n[:2] for n in names}) == len(names), "two folders share a number")
    if len(folders) > 10:
        warnings.append(f"{len(folders)} domain folders is a lot; most projects work best with 5-9")
    for f in folders:
        need(f.get("holds"), f"folder {f['name']}: 'holds' is required")
    plan["folders"] = sorted(folders, key=lambda f: f["name"])

    t = plan.setdefault("tracker", {})
    t.setdefault("item", "item")
    t.setdefault("items", plural(t["item"]))
    t.setdefault("name", "tracker")
    need(re.match(r"^[a-z][a-z0-9-]*$", t["name"]), "tracker.name must be lowercase-kebab (it names the CSV)")
    t["csv"] = f"00_hub/{t['name']}.csv"
    types = t.get("types") or {}
    need(types, "tracker.types is required, e.g. {\"FEAT\": \"feature\"}")
    for code in types:
        need(re.match(r"^[A-Z0-9]{2,6}$", code), f"tracker type '{code}' must be 2-6 capitals or digits")
    statuses = t.get("statuses") or []
    need(len(statuses) >= 2, "tracker.statuses needs at least two statuses")
    for s in statuses:
        need(re.match(r"^[a-z][a-z0-9-]*$", s), f"status '{s}' must be lowercase-kebab")
    need(len(set(statuses)) == len(statuses), "tracker.statuses repeat")
    t.setdefault("terminal", [])
    for s in t["terminal"]:
        need(s in statuses, f"terminal status '{s}' is not in tracker.statuses")
    t.setdefault("start_status", statuses[0])
    t.setdefault("promoted_status", statuses[1])
    for k in ("start_status", "promoted_status"):
        need(t[k] in statuses, f"tracker.{k} '{t[k]}' is not in tracker.statuses")
    t.setdefault("folderless_statuses", [t["start_status"]])
    fd = t.get("folder_dir")
    need(fd in (None, "") or fd in names, f"tracker.folder_dir '{fd}' must be one of the folders, or null")
    cols = t.setdefault("columns", [])
    col_names = []
    for c in cols:
        n = c.get("name", "")
        need(re.match(r"^[a-z][a-z0-9_]*$", n), f"tracker column '{n}' must be lowercase_snake")
        need(n not in HEAD + TAIL, f"tracker column '{n}' is built in; drop it from columns")
        c.setdefault("kind", "text")
        need(c["kind"] in COLUMN_KINDS, f"column {n}: kind must be one of {sorted(COLUMN_KINDS)}")
        if c["kind"] == "enum":
            need(c.get("values"), f"column {n}: enum needs 'values'")
        col_names.append(n)
    need(len(set(col_names)) == len(col_names), "tracker columns repeat")
    known = set(col_names) | {"title"}
    for k in ("folder_fields", "dedupe_fields", "list_fields"):
        t.setdefault(k, ["title"] if k != "list_fields" else [])
        for f in t[k]:
            need(f in known | ({"priority"} if k == "list_fields" else set()), f"tracker.{k}: unknown column '{f}'")
    if t.get("url_field"):
        need(t["url_field"] in col_names, "tracker.url_field must be one of the columns")
    t.setdefault("item_subdirs", [])
    t.setdefault("card_sections", [])

    agents = plan.get("agents") or []
    need(agents, "agents: at least one specialist is required (the reviewer is added automatically)")
    seen = set()
    for i, a in enumerate(agents):
        n = a.get("name", "")
        need(AGENT_RE.match(n), f"agent '{n}' must be lowercase-kebab")
        need(n not in RESERVED_AGENTS, f"agent name '{n}' is reserved")
        need(n not in seen, f"agent '{n}' repeats")
        seen.add(n)
        for k in ("role", "description", "mission"):
            need(a.get(k), f"agent {n}: '{k}' is required")
        a.setdefault("tier", "standard")
        need(a["tier"] in TIER_USE, f"agent {n}: tier must be deep, standard or routine")
        a.setdefault("tools", [])
        bad = set(a["tools"]) - EXTRA_TOOLS
        need(not bad, f"agent {n}: tools {sorted(bad)} not allowed (extras: {sorted(EXTRA_TOOLS)}; Agent is never given)")
        a.setdefault("owns", [])
        for o in a["owns"]:
            top = o.strip("/").split("/")[0]
            if "/" in o and top not in names and top != "00_hub":
                warnings.append(f"agent {n} owns '{o}', which is not under a planned folder")
        a.setdefault("steps", [])
        a.setdefault("standards", [])
        a.setdefault("never", [])
        a.setdefault("memory_focus", "what worked, what failed, sources and tools worth reusing")
        if a.get("color") not in COLORS[:-1]:
            a["color"] = COLORS[i % (len(COLORS) - 1)]
        if a.get("jobs") is None:
            a["jobs"] = ""
    if len(agents) > 9:
        warnings.append(f"{len(agents)} specialists plus the reviewer is a big team; consider merging lanes")
    for f in folders:
        if f.get("owner") and f["owner"] not in seen | {"chief-of-staff"}:
            warnings.append(f"folder {f['name']} names owner '{f['owner']}', who is not on the team")
    r = plan.setdefault("reviewer", {})
    r.setdefault("tier", "deep")
    need(r["tier"] in TIER_USE, "reviewer.tier must be deep, standard or routine")
    r.setdefault("checks", [])

    ex = plan.setdefault("extras", {})
    ex.setdefault("playwright", False)
    ex.setdefault("git", False)
    plan.setdefault("flows", [])
    plan.setdefault("first_steps", [])
    plan.setdefault("waiting_on_user", [])
    plan.setdefault("gitignore", [])
    plan.setdefault("naming", [])
    plan.setdefault("files", [])
    for f in plan["files"]:
        path = f.get("path", "")
        parts = Path(path).parts
        need(path and not Path(path).is_absolute() and ".." not in parts, f"files: bad path '{path}'")
        need(parts[0] in names, f"files: '{path}' must sit inside one of the numbered folders")
        need("content" in f, f"files: '{path}' needs content")
    plan.setdefault("imports", [])
    for im in plan["imports"]:
        need(im.get("from") and im.get("to"), "imports: each item needs 'from' and 'to'")
        need(Path(im["to"]).parts[0] in names and ".." not in Path(im["to"]).parts,
             f"imports: destination '{im['to']}' must sit inside one of the numbered folders")
        need(os.path.exists(im["from"]), f"imports: source not found: {im['from']}")

    def check_patterns(key, pats):
        for p in pats:
            need(isinstance(p, str) and p.strip("/") and ".." not in p, f"{key}: bad pattern '{p}'")
            need(p.strip("./").split("/")[0] in names, f"{key}: '{p}' must start with one of the numbered folders")

    wr = plan.setdefault("writing", {})
    need(wr.get("outgoing"), "writing.outgoing is required: folder patterns whose files people outside the project "
                             "read, e.g. [\"05_materials/\", \"07_items/*/outreach/\"]")
    check_patterns("writing.outgoing", wr["outgoing"])
    wr.setdefault("kinds", "emails, messages, documents, posts and anything else that leaves the project")
    wr.setdefault("recipients", "the people this project writes to")
    wr.setdefault("concrete", "names, numbers with their baselines, dates, places, specific examples")
    so = plan.setdefault("sources", {})
    so.setdefault("research", [])
    so.setdefault("needs_sources", [])
    if not so["research"]:
        warnings.append("sources.research is empty, so the source check hook will never run")
    check_patterns("sources.research", so["research"])
    check_patterns("sources.needs_sources", so["needs_sources"])
    tiers = so.setdefault("tiers", {})
    tiers.setdefault("T1", "The organisation, authority or person in their own words: official sites, documentation, "
                           "regulations, filings, peer-reviewed papers, official statistics")
    tiers.setdefault("T2", "Established news outlets, recognised professional bodies, reputable industry reports and "
                           "directories that link back to the original")
    tiers.setdefault("T3", "Forums, personal blogs, Medium or Substack posts, social media, video, wikis, SEO listicles, "
                           "content farms")
    so.setdefault("scope", "research, discovery, dossiers, analysis, admin facts, and facts about a recipient in "
                           "anything sent out")
    so.setdefault("capture", (so["research"][0].rstrip("/") + "/_raw-captures/") if so["research"] else
                  "the folder of the item the decision is about")
    so.setdefault("extra_low_domains", [])
    return plan, warnings


# -- rendering helpers ----------------------------------------------------------------------------------------
def cell(text):
    return str(text).replace("|", "/").replace("\n", " ")


def fill(text, values):
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def tpl(rel):
    return (TEMPLATES / rel).read_text(encoding="utf-8")


def model_for(plan, tier):
    return TIERS[plan["models"]["cap"]][tier]


def slugify(text, n=24):
    words = re.findall(r"[a-z0-9]+", text.lower())
    out = ""
    for w in words:
        cand = f"{out}-{w}" if out else w
        if len(cand) > n:
            break
        out = cand
    return out or "project"


def plural(word):
    if re.search(r"[^aeiou]y$", word):
        return word[:-1] + "ies"
    if re.search(r"(s|x|z|ch|sh)$", word):
        return word + "es"
    return word + "s"


def shorten(text, n):
    text = " ".join(str(text).split())
    if len(text) <= n:
        return text
    return text[:n].rsplit(" ", 1)[0].rstrip(",;:(") + "…"


def pattern_list(pats):
    return ", ".join(f"`{p}`" for p in pats)


def bullets(items, indent=""):
    return "".join(f"{indent}- {x}\n" for x in items)


def all_folders(plan):
    return ["00_hub"] + [f["name"] for f in plan["folders"]] + ["tools", "_archive", "_bin"]


def root_files(plan):
    files = ["CLAUDE.md", "README.md", ".gitignore"]
    if plan["extras"]["playwright"]:
        files += ["package.json", "package-lock.json"]
    return files


def tracker_config(plan):
    t = plan["tracker"]
    keys = ["item", "items", "csv", "types", "statuses", "terminal", "start_status", "promoted_status", "folderless_statuses",
            "folder_dir", "folder_fields", "dedupe_fields", "url_field", "columns", "list_fields"]
    return {k: t.get(k) for k in keys if t.get(k) not in (None, "")}


def tracker_columns(plan):
    return HEAD + [c["name"] for c in plan["tracker"]["columns"]] + TAIL


# -- documents ------------------------------------------------------------------------------------------------
def render_claude_md(plan, env):
    t, py = plan["tracker"], env["python"]
    cap = plan["models"]["cap"]
    owners = {f["name"]: f.get("owner") for f in plan["folders"]}
    rows = ["| `00_hub/` | State: the tracker, task board, handoffs, decisions, lessons, activity log, team charter |"]
    for f in plan["folders"]:
        own = f" (owner: `{owners[f['name']]}`)" if owners.get(f["name"]) else ""
        rows.append(f"| `{f['name']}/` | {cell(f['holds'])}{own} |")
    rows += ["| `tools/` | Project scripts (Python, standard library only) |",
             "| `_archive/` | Read-only snapshots of finished or superseded work |",
             "| `_bin/` | Unwanted files go here instead of being deleted |"]
    filing = plan.get("filing_rule") or ("Decision rule: *is it about one tracked " + t["item"] + "?* → its folder. "
                                         "*Is it reusable?* → the domain folder it belongs to. *Is it state?* → `00_hub/`.")
    types = ", ".join(f"`{k}` ({v})" for k, v in t["types"].items())
    open_flow = " → ".join(s for s in t["statuses"] if s not in t["terminal"])
    term = ", ".join(f"`{s}`" for s in t["terminal"]) or "none"
    lines = [f"- A new {t['item']} becomes a **row** in `{t['csv']}` with `status={t['start_status']}`:",
             f"  `{py} tools/tracker.py add <TYPE> \"<title>\" [column=value ...]`"]
    if t.get("folder_dir"):
        lines += [f"- When it is worth real work: `{py} tools/tracker.py promote <id>`. This creates "
                  f"`{t['folder_dir']}/<id>-<TYPE>_<Name>/` from `{t['folder_dir']}/_template/` and sets "
                  f"`status={t['promoted_status']}`. Everything specific to that {t['item']} lives in its folder."]
    lines += [f"- Changes: `{py} tools/tracker.py update <id> status=... next_action=\"...\" next_action_due=YYYY-MM-DD`",
              f"- **Always change the tracker through `tools/tracker.py`**, never by hand. `tools/tracker.py schema` shows the rules.",
              f"- Closed {t['items']} keep their row with a terminal status.", "",
              f"**Types:** {types}.", f"**Statuses:** `{open_flow}`; terminal: {term}."]
    if t.get("columns"):
        lines.append("**Extra columns:** " + ", ".join(f"`{c['name']}`" + (f" ({c['kind']})" if c["kind"] != "text" else "")
                                                       for c in t["columns"]) + ".")
    if t.get("notes"):
        lines += ["", t["notes"]]
    lines.append("The tracker's types, statuses and columns live in `00_hub/project.config.json`. Change them only "
                 "when the user agrees, and update the CSV header in the same step.")
    naming = list(plan["naming"])
    if env.get("max_path"):
        naming.append(f"- Windows long paths are disabled on this machine: keep paths under {env['max_path']} characters "
                      "(the structure check enforces it).")
    tier_rows = [f"| {tier} | `{model_for(plan, tier)}` | {TIER_USE[tier]} |" for tier in ("deep", "standard", "routine")]
    cap_rule = {"fable": "Fable is the ceiling; everything may run up to Fable.",
                "opus": "Opus is the ceiling: never use Fable in this project.",
                "sonnet": "Sonnet is the ceiling: every agent and task runs on Sonnet."}[cap]
    if plan["models"].get("main_session"):
        cap_rule += f" The main session is pinned to `{plan['models']['main_session']}` in `.claude/settings.json`."
    extra = ""
    if plan["extras"]["playwright"]:
        s = env["slug"]
        extra += ("\n## 10. Browser tooling\n\n**Playwright CLI** (installed locally in `node_modules/`). Use one named, "
                  "headed, persistent session:\n```\n"
                  f"npx playwright-cli -s={s} open <url> --headed --profile=.playwright/profile-{s}\n"
                  f"npx playwright-cli -s={s} goto <url>      # then snapshot / click / fill\n"
                  f"npx playwright-cli -s={s} close\n```\n"
                  "Run `npx playwright-cli --help` if a flag has changed. The profile keeps logins between sessions "
                  "and is gitignored. CAPTCHAs, logins and payments: hand over to the user.\n")
    for sec in plan.get("claude_md_sections", []):
        extra += f"\n## {sec['heading']}\n\n{sec['body'].strip()}\n"
    return fill(tpl("CLAUDE.md"), {
        "TITLE": plan["project"]["title"], "OBJECTIVE": plan["project"]["objective"]
        + (f" Flow: **{plan['project']['flow']}**." if plan["project"]["flow"] else ""),
        "ITEM": t["item"], "ITEMS": t["items"], "ROOT_FILES": ", ".join(f"`{f}`" for f in root_files(plan)),
        "FOLDER_TABLE": "\n".join(rows), "FILING_RULE": filing, "TRACKER_SECTION": "\n".join(lines),
        "NAMING_EXTRA": "".join(n if n.startswith("- ") else f"- {n}" for n in (x + "\n" for x in naming)),
        "PY": py, "CAP_LABEL": CAP_LABELS[cap], "CAP_RULE": cap_rule, "TIER_TABLE": "\n".join(tier_rows),
        "EXTRA_SECTIONS": extra, "KINDS": plan["writing"]["kinds"],
        "OUTGOING": pattern_list(plan["writing"]["outgoing"]),
        "RESEARCH": pattern_list(plan["sources"]["research"]) or "none configured"})


def render_agent(plan, a, teammates):
    steps = ["Read your brief (its path is in the request), the `report.md` of every task in its `depends_on`, and "
             "`00_hub/lessons.md`.",
             "Work only on what the brief asks. Useful findings outside it go in your report's Handoff notes, not into "
             "the deliverable."] + a["steps"] + [
             "Write deliverables where the brief says, then `report.md` next to the brief: **Summary** · **Files written** "
             "· **Decisions needed** · **Handoff notes** · **Lessons**.",
             "Reply to the Chief of Staff in **at most 8 lines**: the outcome, the paths, any decision needed. Never paste "
             "the work into the reply."]
    desc = a["description"].strip()
    if "00_hub/tasks" not in desc:
        desc += " Works from a task brief in 00_hub/tasks/."
    tools = BASE_TOOLS + [x for x in ["WebSearch", "WebFetch", "Bash", "NotebookEdit"] if x in a["tools"]] + ["SendMessage"]
    owns = ", ".join(f"`{o}`" for o in a["owns"]) or "the paths named in each brief"
    standards = list(a["standards"])
    if {"WebSearch", "WebFetch"} & set(a["tools"]):
        standards.append("Research follows `00_hub/source-policy.md`: open the page, T1 for anything decision-critical "
                         "(otherwise mark it `UNVERIFIED`), label `[T3]` sources, never cite AI answers or search snippets.")
    return fill(tpl("agents/specialist.md"), {
        "NAME": a["name"], "DESCRIPTION": desc.replace("\n", " "), "TOOLS": ", ".join(tools),
        "MODEL": model_for(plan, a["tier"]), "EFFORT_LINE": "effort: high\n" if a["tier"] == "deep" else "",
        "COLOR": a["color"], "ROLE": a["role"], "MISSION": a["mission"].strip(),
        "EVERY_TASK": "".join(f"{i}. {s}\n" for i, s in enumerate(steps, 1)).rstrip("\n"),
        "OWNS": owns, "STANDARDS": bullets(standards).rstrip("\n"),
        "NEVER": bullets(a["never"]), "TEAMMATES": ", ".join(f"`{n}`" for n in teammates),
        "MEMORY_FOCUS": a["memory_focus"]}).replace("\n\n\n", "\n\n")


def render_reviewer(plan, env):
    r = plan["reviewer"]
    checks = "".join(f"   - {c}\n" for c in r["checks"])
    return fill(tpl("agents/red-team-reviewer.md"), {
        "MODEL": model_for(plan, r["tier"]), "EFFORT_LINE": "effort: high\n" if r["tier"] == "deep" else "",
        "CHECKS": checks, "PY": env["python"]})


def render_charter(plan, env):
    rows = []
    for a in plan["agents"]:
        owns = ", ".join(f"`{o}`" for o in a["owns"]) or "-"
        rows.append(f"| `{a['name']}` | {cell(a['role'])} | {a['tier']} → `{model_for(plan, a['tier'])}` | {owns} | "
                    f"{cell(a['jobs'] or a['mission'])} |")
    r = plan["reviewer"]
    rows.append(f"| `red-team-reviewer` | Quality & Risk | {r['tier']} → `{model_for(plan, r['tier'])}` | "
                "`00_hub/tasks/<task>/review.md` only | Independent review of outgoing text and research; gates on the style lint and source check |")
    flows = plan["flows"] or [" → ".join([a["name"] for a in plan["agents"][:3]] + ["red-team-reviewer"])]
    return fill(tpl("hub/team-charter.md"), {
        "ROSTER_TABLE": "\n".join(rows), "CAP_LABEL": CAP_LABELS[plan["models"]["cap"]], "PY": env["python"],
        "FLOWS": "".join(f"  - {f}\n" for f in flows).rstrip("\n")})


def render_readme(plan, env):
    t, py = plan["tracker"], env["python"]
    width = max(len(n) for n in all_folders(plan)) + 3
    lines = [f"{'00_hub/':<{width}}STATE: {t['name']}.csv (every {t['item']}), task board, handoffs, decisions, lessons, activity log"]
    lines += [f"{f['name'] + '/':<{width}}{f['holds']}" for f in plan["folders"]]
    lines += [f"{'tools/':<{width}}tracker.py, tasks.py, check_structure.py (Stop hook), session_brief.py (startup brief)",
              f"{'.claude/agents/':<{width}}The specialist team (see 00_hub/team-charter.md)",
              f"{'_archive/':<{width}}Read-only snapshots of finished work",
              f"{'_bin/':<{width}}Nothing is deleted; unwanted files go here"]
    flow = plan["project"]["flow"] or " → ".join(s for s in t["statuses"] if s not in t["terminal"])
    team = ", ".join(a["role"] for a in plan["agents"]) + ", and Quality & Risk"
    return (f"# {plan['project']['title']}\n\n{plan['project']['objective']}\n"
            f"**Rules for Claude are in `CLAUDE.md`.** This page is the map.\n\n```\n" + "\n".join(lines) + "\n```\n\n"
            f"**How work flows:** {flow}.\n\n"
            f"**Quick status:** `{py} tools/tracker.py list` · `{py} tools/tasks.py list`\n\n"
            f"**How work gets done:** the main Claude session acts as Chief of Staff. It plans, decides with you, and "
            f"delegates to {len(plan['agents']) + 1} specialists ({team}), which coordinate through `00_hub/tasks/`. "
            f"See `00_hub/team-charter.md`.\n\n"
            f"**Switching sessions:** when the context gets large, type `/handoff`, then start a new session here. "
            f"The brief loads automatically.\n")


def render_handoff(plan, env):
    p, t = plan["project"], plan["tracker"]
    waiting = plan["waiting_on_user"] or ["Confirm the first priority for the team."]
    nxt = plan["first_steps"] or ["CoS: agree the first piece of work with the user, then brief the owning agent."]
    watch = ["Don't read or import anything outside this folder without the user asking for it.",
             "Run `/handoff` before the context gets large, then start a new session."]
    if env.get("max_path"):
        watch.append(f"Windows long paths are off: keep paths under {env['max_path']} characters.")
    return (f"# HANDOFF: current state of the project\n\nsession: 1\nupdated: {TODAY}\n"
            f"phase: Setup complete. No {t['items']} or tasks yet.\n\n"
            "> Loaded automatically at session start. Rewritten at every `/handoff`; earlier versions are in "
            "`00_hub/handoffs/`.\n> Keep it under ~120 lines and point to files instead of copying them.\n\n"
            f"## Objective\n{p['objective']}\n\n"
            "## Done so far\n"
            f"- Structure: `00_hub/`, {', '.join(f'`{f}/`' for f in [x['name'] for x in plan['folders']])}, `tools/`, "
            "`_archive/`, `_bin/`.\n"
            f"- Tracker: `{t['csv']}` via `tools/tracker.py` (rules in `00_hub/project.config.json`); task board via `tools/tasks.py`.\n"
            f"- Team: {len(plan['agents']) + 1} specialists in `.claude/agents/`, model cap {CAP_LABELS[plan['models']['cap']]}; "
            "rules in `00_hub/team-charter.md`; `/handoff` skill.\n"
            "- Hooks: SessionStart brief (`tools/session_brief.py`), model-cap guard on agent launches (`tools/model_cap.py`), "
            "style lint and source check after each write (`tools/style_lint.py`, `tools/source_check.py`), "
            "Stop structure check (`tools/check_structure.py --hook`).\n"
            "- Norms: `00_hub/writing-style.md` (outgoing text) and `00_hub/source-policy.md` (research), both gated by "
            "the reviewer.\n"
            + (f"- Imported by the user's approval: {len(plan['imports'])} item(s) (see `00_hub/decisions.md`).\n"
               if plan["imports"] else "")
            + "\n## In flight\n- Nothing. The tracker and the task board are empty.\n\n"
            "## Waiting on the user\n" + "".join(f"{i}. {w}\n" for i, w in enumerate(waiting, 1))
            + "\n## Next actions\n" + "".join(f"{i}. {n}\n" for i, n in enumerate(nxt, 1))
            + "\n## Watch-outs\n" + bullets(watch))


def render_hub_readme(plan):
    t = plan["tracker"]
    return ("# 00_hub: project state and team coordination\n\n"
            "The single source of truth for **where things stand**. Content lives elsewhere; this folder tracks it.\n\n"
            "| File | Holds | Edited by |\n|---|---|---|\n"
            "| `HANDOFF.md` | Current state for the next session (loaded automatically) | CoS, at `/handoff` |\n"
            "| `handoffs/` | Earlier handoffs, `YYYY-MM-DD_session-NN.md` | CoS |\n"
            f"| `{t['name']}.csv` | One row per {t['item']} | `tools/tracker.py` only |\n"
            "| `project.config.json` | Folder list, tracker types, statuses and columns, path limit | CoS, when the user agrees |\n"
            "| `tasks/board.csv` + `tasks/T###_*/` | One row and one folder per delegated task (`brief.md`, `report.md`, "
            "`review.md`) | `tools/tasks.py`; agents write reports |\n"
            "| `team-charter.md` | Team roles, delegation protocol, coordination rules | CoS, when the user agrees |\n"
            "| `decisions.md` | The user's decisions, dated | CoS |\n"
            "| `lessons.md` | Shared team know-how | CoS |\n"
            "| `activity-log.md` | What happened, in order | CoS, every turn that changes files |\n"
            "| `writing-style.md` | How outgoing text must read; enforced by `tools/style_lint.py` and the reviewer "
            "| CoS, when the user agrees |\n"
            "| `source-policy.md` | Source tiers and rules; enforced by `tools/source_check.py` and the reviewer "
            "| CoS (keeps the known-sources list) |\n"
            "| `setup-plan.json` | The plan this project was built from (reference only) | nobody |\n\n"
            f"## {t['name']}.csv columns\n" + " · ".join(f"`{c}`" for c in tracker_columns(plan)) + "\n\n"
            "## tasks/board.csv columns\n`id` (T###) · `title` · `owner` (an agent, `chief-of-staff` or `user`) · "
            "`status` (open, in-progress, blocked, review, done, cancelled) · `item_id` · `depends_on` · `folder` · "
            "`created` · `updated` · `summary`\n")


def render_item_card(plan):
    t = plan["tracker"]
    fm = "".join(f"{c}: \"{{{{{c}}}}}\"\n" for c in ["id", "type", "title"] + [c["name"] for c in t["columns"]])
    secs = t["card_sections"] or [{"heading": "Summary", "hint": f"One paragraph: what this {t['item']} is and why it matters."},
                                  {"heading": "Notes", "hint": "Facts with sources, open questions, links to files in this folder."}]
    body = "".join(f"## {s['heading']}\n_{s.get('hint', '')}_\n\n" for s in secs)
    return (f"---\n{fm}---\n\n# {{{{id}}}} · {{{{title}}}}\n\n"
            f"> Status, priority and next action live in `{t['csv']}`, not here.\n\n{body}"
            "## Timeline\n- {{added}}: added to the tracker\n")


def folder_readme(plan, f):
    t = plan["tracker"]
    text = f"# {f['name']}\n\n{f['holds']}\n"
    if f.get("owner"):
        text += f"\nOwner: `{f['owner']}`. Others read freely; they write here only when a brief says so.\n"
    if t.get("folder_dir") == f["name"]:
        text += (f"\nOne folder per promoted {t['item']}, named `NNN-TYPE_Name` and created only by "
                 f"`tools/tracker.py promote`. `_template/` is copied for each new one.\n")
    return text


def gitignore(plan):
    lines = ["__pycache__/", "*.csv.tmp", ".claude/settings.local.json", ".claude/agent-memory-local/"]
    if plan["extras"]["playwright"]:
        lines += ["node_modules/", "# Persistent browser profile: holds cookies and logins. Never commit.",
                  ".playwright/profile-*/", ".playwright-cli/"]
    return "\n".join(lines + list(plan["gitignore"])) + "\n"


def settings(plan, env, existing):
    py = env["python"]
    data = dict(existing)
    hooks = data.setdefault("hooks", {})
    hooks.setdefault("SessionStart", []).append({"hooks": [{
        "type": "command", "command": f"{py} \"$CLAUDE_PROJECT_DIR/tools/session_brief.py\"", "timeout": 30,
        "statusMessage": "Loading project brief..."}]})
    hooks.setdefault("PreToolUse", []).append({"matcher": "Agent|Task", "hooks": [{
        "type": "command", "command": f"{py} \"$CLAUDE_PROJECT_DIR/tools/model_cap.py\"", "timeout": 15}]})
    hooks.setdefault("PostToolUse", []).append({"matcher": "Write|Edit", "hooks": [
        {"type": "command", "command": f"{py} \"$CLAUDE_PROJECT_DIR/tools/style_lint.py\" --hook", "timeout": 30},
        {"type": "command", "command": f"{py} \"$CLAUDE_PROJECT_DIR/tools/source_check.py\" --hook", "timeout": 30}]})
    hooks.setdefault("Stop", []).append({"hooks": [{
        "type": "command", "command": f"{py} \"$CLAUDE_PROJECT_DIR/tools/check_structure.py\" --hook", "timeout": 30,
        "statusMessage": "Checking project structure..."}]})
    if plan["models"].get("main_session"):
        data["model"] = plan["models"]["main_session"]
    return json.dumps(data, indent=2) + "\n"


# -- preview ------------------------------------------------------------------------------------------------------
def preview(plan, env, warnings):
    t, cap = plan["tracker"], plan["models"]["cap"]
    w = max(len(f["name"]) for f in plan["folders"]) + 3
    w = max(w, len("tools/ _archive/ _bin/") + 2)
    out = [f"PLAN · {plan['project']['title']}", plan["project"]["objective"], "", "Folders"]
    out.append(f"  {'00_hub/':<{w}}state: {t['name']}.csv, task board, handoffs, decisions, lessons, log")
    for f in plan["folders"]:
        own = f"  [{f['owner']}]" if f.get("owner") else ""
        out.append(f"  {f['name'] + '/':<{w}}{shorten(f['holds'], 64)}{own}")
    out.append(f"  {'tools/ _archive/ _bin/':<{w}}scripts, snapshots, nothing-is-deleted bin")
    out += ["", f"Tracker · one row per {t['item']}"
            + (f", promoted ones get a folder in {t['folder_dir']}/" if t.get("folder_dir") else ""),
            "  types: " + ", ".join(f"{k} ({v})" for k, v in t["types"].items()),
            "  flow: " + " → ".join(s for s in t["statuses"] if s not in t["terminal"])
            + (f"  | closed: {', '.join(t['terminal'])}" if t["terminal"] else "")]
    if t["columns"]:
        out.append("  extra columns: " + ", ".join(c["name"] for c in t["columns"]))
    ms = plan["models"].get("main_session")
    nw = max([len(a["name"]) for a in plan["agents"]] + [len("red-team-reviewer")]) + 2
    rw = max([len(a["role"]) for a in plan["agents"]] + [len("main session: plans, decides, delegates")]) + 2
    out += ["", f"Team · model cap: {CAP_LABELS[cap]}",
            f"  {'chief-of-staff':<{nw}}{'main session: plans, decides, delegates':<{rw}}{ms or 'your current model'}"]
    for a in plan["agents"]:
        out.append(f"  {a['name']:<{nw}}{a['role']:<{rw}}{model_for(plan, a['tier'])} ({a['tier']})")
    r = plan["reviewer"]
    out.append(f"  {'red-team-reviewer':<{nw}}{'Quality & Risk, writing norm':<{rw}}{model_for(plan, r['tier'])} ({r['tier']})")
    out += ["", f"Hooks · session brief at start, model-cap guard on agent launches, style lint + source check after writes, structure check at stop (runs `{env['python']}`)"
            + (f"; paths kept under {env['max_path']} chars" if env.get("max_path") else "")]
    out.append("Writing · style file + lint on " + shorten(", ".join(plan["writing"]["outgoing"]), 90))
    out.append("Sources · tiered policy + check on " + (shorten(", ".join(plan["sources"]["research"]), 90) or "(none)"))
    ex = plan["extras"]
    out.append("Extras · " + " · ".join([f"Playwright CLI: {'yes' if ex['playwright'] else 'no'}",
                                          f"git init: {'yes' if ex['git'] else 'no'}",
                                          f"pin main-session model: {ms or 'no'}"]))
    if plan["imports"]:
        out.append(f"Imports · {len(plan['imports'])} approved item(s) copied in (originals untouched)")
    for wmsg in warnings:
        out.append(f"(note: {wmsg})")
    return "\n".join(out)


# -- build --------------------------------------------------------------------------------------------------------
class Writer:
    def __init__(self, root, allow_existing):
        self.root, self.allow, self.written, self.skipped = root, allow_existing, [], []

    def collisions(self, rels):
        return [r for r in rels if (self.root / r).exists()]

    def write(self, rel, text):
        dest = self.root / rel
        if dest.exists():
            self.skipped.append(rel)
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(text.encode("utf-8"))  # LF on every OS (write_text's newline= needs Python 3.10)
        self.written.append(rel)

    def copy(self, rel, src):
        dest = self.root / rel
        if dest.exists():
            self.skipped.append(rel)
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        self.written.append(rel)


def plan_files(plan, env):
    """Every generated file as (relative path, text). Directories come from these paths plus .gitkeep files."""
    py = env["python"]
    t = plan["tracker"]
    files = {}
    files["CLAUDE.md"] = render_claude_md(plan, env)
    files["README.md"] = render_readme(plan, env)
    files[".gitignore"] = gitignore(plan)
    names = [a["name"] for a in plan["agents"]] + ["red-team-reviewer"]
    for a in plan["agents"]:
        files[f".claude/agents/{a['name']}.md"] = render_agent(plan, a, [n for n in names if n != a["name"]])
    files[".claude/agents/red-team-reviewer.md"] = render_reviewer(plan, env)
    files[".claude/skills/handoff/SKILL.md"] = fill(tpl("skills/handoff/SKILL.md"), {"PY": py})
    for name in ("tracker.py", "tasks.py", "check_structure.py", "session_brief.py", "model_cap.py", "style_lint.py",
                 "source_check.py"):
        files[f"tools/{name}"] = tpl(f"tools/{name}")
    files["tools/README.md"] = fill(tpl("tools/README.md"), {"PY": py, "CSV": t["csv"]})
    tooling = sorted((TOOLING - {".DS_Store", "Thumbs.db", "desktop.ini"}) | set(env.get("tooling_entries", [])))
    if plan["extras"]["playwright"]:
        tooling += ["node_modules", ".playwright", ".playwright-cli"]
    config = {"project": plan["project"]["title"], "created": TODAY,
              "models": {"cap": plan["models"]["cap"], "tiers": TIERS[plan["models"]["cap"]]},
              "structure": {"folders": all_folders(plan), "root_files": root_files(plan), "root_tooling": tooling,
                            "max_path": env.get("max_path")},
              "tracker": tracker_config(plan),
              "writing": {"outgoing": plan["writing"]["outgoing"]},
              "sources": {k: plan["sources"][k] for k in ("research", "needs_sources", "extra_low_domains")}}
    files["00_hub/project.config.json"] = json.dumps(config, indent=2, ensure_ascii=False) + "\n"
    files[f"00_hub/{t['name']}.csv"] = ",".join(tracker_columns(plan)) + "\n"
    files["00_hub/tasks/board.csv"] = "id,title,owner,status,item_id,depends_on,folder,created,updated,summary\n"
    files["00_hub/README.md"] = render_hub_readme(plan)
    files["00_hub/HANDOFF.md"] = render_handoff(plan, env)
    files["00_hub/handoffs/.gitkeep"] = ""
    files["00_hub/team-charter.md"] = render_charter(plan, env)
    wr, so = plan["writing"], plan["sources"]
    files["00_hub/writing-style.md"] = fill(tpl("hub/writing-style.md"), {
        "KINDS": wr["kinds"], "OUTGOING": pattern_list(wr["outgoing"]), "PY": py, "CONCRETE": wr["concrete"],
        "RECIPIENTS": wr["recipients"]})
    files["00_hub/source-policy.md"] = fill(tpl("hub/source-policy.md"), {
        "SCOPE": so["scope"], "RESEARCH": pattern_list(so["research"]) or "none configured", "PY": py,
        "T1": cell(so["tiers"]["T1"]), "T2": cell(so["tiers"]["T2"]), "T3": cell(so["tiers"]["T3"]),
        "CAPTURE": so["capture"]})
    lessons = ["Work only inside this folder. The user imports their own details; never gather personal "
               "information from elsewhere.",
               "Replies to the user are as short as possible without dropping key information; lead with the answer."]
    tool_lessons = []
    process_lessons = ["Outgoing text: write plainly and specifically (`00_hub/writing-style.md`). Lint flags are prompts "
                       "for a natural rewrite, not boxes to tick.",
                       "Decision quality follows source quality: T1 for anything decision-critical, `UNVERIFIED` when "
                       "there is none (`00_hub/source-policy.md`)."]
    if env.get("max_path"):
        tool_lessons.append(f"Windows long paths are off: keep paths under {env['max_path']} characters "
                            "(`tools/check_structure.py` enforces this).")
    files["00_hub/lessons.md"] = (
        "# Lessons (shared team memory)\n\nDurable know-how learned while working, for the chief of staff and every "
        "agent: what worked, what failed, quirks of tools and sites, the user's working preferences. "
        "**Read before starting work.**\n\nOnly the chief of staff edits this file. Agents propose lessons in the "
        "\"Lessons\" section of their task `report.md`; the chief of staff consolidates them here. One line each, dated, "
        "with a pointer to the evidence. Replace a lesson when it changes; don't stack contradictions.\n\n"
        "## Working with the user\n" + "".join(f"- {TODAY} · {x}\n" for x in lessons)
        + "\n## Tools and sites\n" + "".join(f"- {TODAY} · {x}\n" for x in tool_lessons) + "\n## Process\n" + "".join(f"- {TODAY} · {x}\n" for x in process_lessons))
    ex = plan["extras"]
    decisions = [f"Project set up for: {plan['project']['purpose']}.",
                 f"Model cap: {CAP_LABELS[plan['models']['cap']]}. Agents take their default model from their tier; "
                 "single tasks may move a tier, never above the cap.",
                 f"Extras: Playwright CLI {'yes' if ex['playwright'] else 'no'}; git {'yes' if ex['git'] else 'no'}; "
                 f"main-session model {plan['models'].get('main_session') or 'not pinned'}.",
                 "Outgoing text follows `00_hub/writing-style.md`; `red-team-reviewer` gates on `tools/style_lint.py` "
                 "(clean, or each flag justified in review.md).",
                 "Research uses reliable sources only (`00_hub/source-policy.md`); the reviewer runs "
                 "`tools/source_check.py` on research deliverables.",
                 "Replies to the user are as short as possible without dropping key information, leading with the answer."]
    for im in plan["imports"]:
        decisions.append(f"User approved importing `{Path(im['from']).name}` into `{im['to']}` (copied; original untouched).")
    files["00_hub/decisions.md"] = ("# Decisions\n\nEvery decision the user makes, dated, newest last. Don't re-ask a "
                                    "question that is settled here.\n\n" + "".join(f"- {TODAY} · {d}\n" for d in decisions))
    for f in plan["folders"]:
        files[f"{f['name']}/README.md"] = folder_readme(plan, f)
    if t.get("folder_dir"):
        files[f"{t['folder_dir']}/_template/item.md"] = render_item_card(plan)
        for sub in t["item_subdirs"]:
            files[f"{t['folder_dir']}/_template/{sub.strip('/')}/.gitkeep"] = ""
    files["_archive/README.md"] = "# _archive\n\nRead-only snapshots of finished or superseded work, `YYYY-MM-DD_<what>/`.\n"
    files["_bin/README.md"] = ("# _bin\n\nNothing in this project is deleted. Unwanted files are moved here, with a "
                               "one-line note in the activity log. The user empties it.\n")
    for f in plan["files"]:
        files[f["path"]] = f["content"] if f["content"].endswith("\n") else f["content"] + "\n"
    return files


def build(plan, target, allow_existing, plan_path=None):
    env = probe(target)
    if not env["exists"]:
        Path(target).mkdir(parents=True)
        env = probe(target)
    env["slug"] = slugify(plan["project"]["title"])
    # The plan itself may sit in the target root (it moves to 00_hub/ after the build); it doesn't make the folder non-empty.
    content = [e for e in env["non_tooling_entries"]
               if not (plan_path and plan_path.parent == Path(env["target"]) and e == plan_path.name)]
    if content and not allow_existing:
        raise PlanError("target is not empty: " + ", ".join(content[:10])
                        + ". Ask the user; rerun with --allow-existing only if they agree.")
    root = Path(env["target"])
    files = plan_files(plan, env)
    w = Writer(root, allow_existing)
    clash = w.collisions(files)
    if clash and not allow_existing:
        raise PlanError("these files already exist: " + ", ".join(clash))
    for rel, text in files.items():
        if rel == "00_hub/activity-log.md":
            continue
        w.write(rel, text)
    settings_path = root / ".claude" / "settings.json"
    existing = {}
    if settings_path.exists():
        existing = json.loads(settings_path.read_text(encoding="utf-8") or "{}")
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_bytes(settings(plan, env, existing).encode("utf-8"))
    w.written.append(".claude/settings.json" + (" (merged)" if existing else ""))
    for im in plan["imports"]:
        src = Path(im["from"])
        dest = Path(im["to"])
        if src.is_dir():
            for p in src.rglob("*"):
                if p.is_file():
                    w.copy((dest / p.relative_to(src)).as_posix(), p)
        else:
            w.copy(dest.as_posix() if dest.suffix else (dest / src.name).as_posix(), src)
    git_note = ""
    if plan["extras"]["git"]:
        if not (root / ".git").exists() and shutil.which("git"):
            res = subprocess.run(["git", "init"], cwd=root, capture_output=True, text=True)
            git_note = "git init: ok" if res.returncode == 0 else f"git init failed: {res.stderr.strip()}"
        else:
            git_note = "git init: skipped (already a repository or git not found)"
    log = (f"# Activity log\n\nWhat happened, newest last. One entry per turn that changes files: what was done, files "
           f"changed, next step.\n\n## {TODAY} · Project set up\n- Built from the setup plan "
           f"(`00_hub/setup-plan.json`): {len(plan['folders'])} domain folders, tracker `{plan['tracker']['csv']}`, "
           f"{len(plan['agents']) + 1} agents, hooks, `/handoff` skill.\n"
           + (f"- Imported {len(plan['imports'])} approved item(s).\n" if plan["imports"] else "")
           + "- Next: restart the session so the hooks and agents load; then follow `00_hub/HANDOFF.md`.\n")
    w.write("00_hub/setup-plan.json", json.dumps(plan, indent=2, ensure_ascii=False) + "\n")
    w.write("00_hub/activity-log.md", log)  # last, so it is newer than everything it describes
    return env, w, git_note


def load_plan(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise PlanError(f"plan is not valid JSON: {e}")


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("probe")
    pr.add_argument("--target", default=".")
    pv = sub.add_parser("preview")
    pv.add_argument("--plan", required=True)
    pv.add_argument("--target", default=".")
    b = sub.add_parser("build")
    b.add_argument("--plan", required=True)
    b.add_argument("--target", default=".")
    b.add_argument("--allow-existing", action="store_true")
    args = ap.parse_args()
    try:
        if args.cmd == "probe":
            print(json.dumps(probe(args.target), indent=2))
            return
        plan, warnings = validate(load_plan(args.plan))
        if args.cmd == "preview":
            env = probe(args.target)
            print(preview(plan, env, warnings))
            return
        plan_path = Path(os.path.abspath(args.plan))
        env, w, git_note = build(plan, args.target, args.allow_existing, plan_path)
        if plan_path.parent in (Path(env["target"]), Path(env["target"]) / ".claude"):
            plan_path.unlink()  # its copy now lives in 00_hub/setup-plan.json
        print(f"built {len(w.written)} files in {env['target']} (hooks run: {env['python']})")
        if w.skipped:
            print("skipped (already existed): " + ", ".join(w.skipped))
        if git_note:
            print(git_note)
        for msg in warnings:
            print(f"note: {msg}")
    except PlanError as e:
        sys.exit(f"PLAN ERROR: {e}")


if __name__ == "__main__":
    main()
