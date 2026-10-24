# Plan format (input to `scripts/scaffold.py`)

One JSON file describes the whole project. `scaffold.py preview` validates it and prints the one-screen preview;
`scaffold.py build` generates everything from it. A full worked example is `example-plan-phd.json`.

Write the plan to `.claude/setup-plan.json` inside the target folder (a tooling folder, so the root stays clean).
After a successful build the script moves it to `00_hub/setup-plan.json`.

Everything the plan says ends up in files other people may read, and the skill is user-agnostic: **no personal data,
no names, no machine-specific paths**. Describe roles and folders generically ("the user's documents, as imported by
the user"), never with details the user hasn't put into the project themselves.

## Top level

| Key | Required | What it is |
|---|---|---|
| `project` | yes | `title` (short name), `objective` (one sentence: the outcome), `purpose` (the user's words), `flow` (optional: the work's stages joined by →) |
| `models` | yes | `cap`: `fable`, `opus` or `sonnet`. `main_session`: optional model to pin in `.claude/settings.json` (never above the cap) |
| `folders` | yes | Numbered domain folders (see below). `00_hub/`, `tools/`, `_archive/`, `_bin/` are added automatically |
| `filing_rule` | no | One or two sentences: how to decide where a file goes. A generic rule is used if absent |
| `tracker` | yes | The main tracker (see below) |
| `agents` | yes | The specialists (see below). `red-team-reviewer` is always added; don't list it |
| `reviewer` | no | `tier` (default `deep`) and `checks`: extra purpose-specific review checks, one line each |
| `flows` | no | Typical agent chains, e.g. `"scout → analyst → writer → red-team-reviewer"` |
| `extras` | no | `playwright` (bool), `git` (bool: run `git init`) |
| `waiting_on_user` | no | What only the user can do next (goes in `HANDOFF.md`) |
| `first_steps` | no | The first 3–5 actions for the next session, each naming the agent to delegate to |
| `naming` | no | Extra naming conventions, one line each |
| `gitignore` | no | Extra `.gitignore` lines (e.g. private document folders) |
| `files` | no | Extra purpose-specific files: `{"path": "04_x/_templates/person.md", "content": "..."}`. Must sit inside a numbered folder |
| `writing` | yes | The writing norm for outgoing text (see below) |
| `sources` | no (strongly advised) | The source policy for research (see below) |
| `claude_md_sections` | no | Extra `CLAUDE.md` sections: `{"heading": "...", "body": "..."}` |
| `imports` | no | Items the user approved for copying in: `{"from": "<absolute path the user gave>", "to": "03_x/sub/"}`. Copied, never moved |

## folders

```json
{ "name": "02_research", "holds": "What we learned, with sources; evidence-log.md", "owner": "research-lead" }
```
- `name`: `NN_lowercase-kebab`, numbered from `01_`. Aim for 5–9 folders; each must be a real home for real files.
- `holds`: what lives there, concretely. It becomes the filing table in `CLAUDE.md` and the folder's README.
- `owner`: the agent that writes there (or `chief-of-staff`). Optional; leave it out for shared folders.

## tracker

The one CSV that answers "where does every X stand?". X is the unit of work the purpose revolves around:
opportunities, investors, features, chapters, leads, papers, grants.

| Key | Default | What it is |
|---|---|---|
| `name` | `tracker` | CSV name: `00_hub/<name>.csv` (e.g. `pipeline`, `roadmap`, `investors`) |
| `item` / `items` | `item` / auto plural | The unit, singular and plural |
| `types` | required | `{"CODE": "meaning"}`; codes are 2–6 capitals, used in folder names |
| `statuses` | required | The lifecycle in order, lowercase-kebab, open statuses first, then terminal ones |
| `terminal` | `[]` | Closed statuses (subset of `statuses`) |
| `start_status` | first status | Status of a newly added row |
| `promoted_status` | second status | Status set by `promote` |
| `folderless_statuses` | `[start_status]` | Statuses allowed without an item folder (terminal ones always are) |
| `folder_dir` | none | Numbered folder that holds one subfolder per promoted item. `null` = rows only, no item folders |
| `columns` | `[]` | Extra columns: `{"name": "deadline", "kind": "date"}`; kinds `text`, `date`, `enum` (+`values`), `upper`, `url` |
| `folder_fields` | `["title"]` | Columns that name an item folder: `NNN-TYPE_<field>_<field>` |
| `dedupe_fields` | `["title"]` | Columns that together identify a duplicate |
| `url_field` | none | A `url` column also used for duplicate detection |
| `list_fields` | `[]` | Columns shown by `tracker.py list` |
| `item_subdirs` | `[]` | Subfolders of the item template, e.g. `["sources", "drafts", "final"]` |
| `card_sections` | Summary, Notes | Sections of the item card `item.md`: `{"heading": "...", "hint": "..."}` |
| `notes` | none | A short paragraph of lifecycle rules for `CLAUDE.md` |

Built-in columns, always present: `id, type, status, priority, title, … , folder, next_action, next_action_due, added, updated, notes`.
`priority` is A/B/C or empty.

## writing and sources

Folder patterns are relative to the project root: `05_materials/` covers everything under that folder; `*` is one path
segment (`07_items/*/outreach/`); a pattern without a trailing slash names files (`07_items/*/item.md`). Each pattern must
start with one of the numbered folders. They go into `00_hub/project.config.json`, which the hooks read.

```json
"writing": {
  "outgoing": ["05_docs/", "06_community/", "07_releases/"],
  "kinds": "README and docs, issue and PR replies, release notes, announcements",
  "recipients": "users trying the tool for the first time, contributors, maintainers of related projects",
  "concrete": "commands, flags, version numbers, benchmarks with their setup, issue links"
},
"sources": {
  "research": ["02_research/", "03_design/"],
  "needs_sources": ["02_research/*.md"],
  "scope": "prior-art research, design decisions, dependency and licence checks",
  "capture": "`02_research/_raw-captures/`",
  "extra_low_domains": ["dev.to"],
  "tiers": {
    "T1": "Official documentation, specifications and RFCs, the maintainers' own repositories, release notes and changelogs, licence texts",
    "T2": "Conference talks by maintainers, established engineering blogs, well-maintained package registries' metadata",
    "T3": "Forums, Stack Overflow answers, personal blogs, social media, video tutorials, SEO listicles"
  }
}
```

| Key | Default | What it is |
|---|---|---|
| `writing.outgoing` | required | Folders whose files people outside the project read; linted on every write |
| `writing.kinds` / `recipients` / `concrete` | generic | Fill the style file: what goes out, who reads it, which concrete details good writing here uses |
| `sources.research` | `[]` | Folders of findings; checked on every write |
| `sources.needs_sources` | `[]` | Files that must contain at least one URL (dated `YYYY-MM-DD_*.md` reports in research folders always must) |
| `sources.tiers` | generic | Purpose-fitting examples for T1, T2 and T3 (the "Never" tier is fixed) |
| `sources.scope`, `capture`, `extra_low_domains` | generic | Which work the policy covers, where raw captures go, extra T3 domains |

## agents

```json
{
  "name": "research-lead",
  "role": "Head of Research",
  "tier": "deep",
  "description": "Head of Research. Use for ... (when the CoS should pick this agent)",
  "mission": "One or two sentences on what good work looks like in this lane.",
  "tools": ["WebSearch", "WebFetch", "Bash"],
  "owns": ["02_research/"],
  "jobs": "Short phrase for the roster table",
  "steps": ["Extra numbered steps for every task, if the lane has a ritual"],
  "standards": ["Lane-specific quality bars, one per line"],
  "never": ["Lane-specific hard limits beyond the shared ones"],
  "memory_focus": "what this agent should remember between tasks",
  "color": "blue"
}
```
- `name`: lowercase-kebab. Reserved: `red-team-reviewer`, `chief-of-staff`, `user`, `handoff`.
- `tier`: `deep` (judgement, taste, high-stakes writing, analysis), `standard` (skilled execution), `routine`
  (sweeps, logging, formatting, bulk mechanical work). The model comes from tier + cap (see `SKILL.md`).
  Deep-tier agents also get `effort: high`.
- `tools`: extras beyond the base set (`Read, Write, Edit, Glob, Grep, SendMessage`). Allowed: `WebSearch`, `WebFetch`,
  `Bash` (needed to run `tools/*.py` or the Playwright CLI), `NotebookEdit`. `Agent` is never given: only the CoS dispatches.
- `owns`: folders or files this agent writes to. Lanes shouldn't overlap; two agents writing the same file is a design bug.
- `color`: one of blue, green, purple, orange, yellow, cyan, pink (red is the reviewer's). Assigned automatically if absent.

The shared parts of every agent (task protocol, report format, staying inside the folder, never acting outward,
following `00_hub/writing-style.md`, coordination, memory) come from `templates/agents/specialist.md`, and every agent
with `WebSearch` or `WebFetch` also gets the source-policy line. Write only what is specific to the lane.
