---
name: project-chief-of-staff
description: Turn an empty folder into a persistent, organised Claude Code project run by a Chief-of-Staff main session and a specialist agent team fitted to any purpose (startup, open source, PhD, book, fundraising, job search, research, a campaign, anything). Creates numbered folders, a config-driven tracker, a task board, handoffs, decision and lesson logs, SessionStart and Stop hooks, a /handoff skill and per-agent model tiers. Use whenever the user runs /project-chief-of-staff or asks to set up, initialise, scaffold or bootstrap a new project folder or workspace, or wants "a team of agents" or "a proper structure" for a new long-running effort, even if they don't name this skill. Not for adding features to an existing codebase.
argument-hint: "[purpose, e.g. an open source CLI tool]"
effort: max
---

# project-chief-of-staff

ultrathink. This setup shapes every session the user will have in this folder, so reason carefully about what this
particular purpose needs before creating anything. The scaffold script does the mechanical work; your job is the design
and the conversation.

Paths below are relative to this skill's folder, `${CLAUDE_SKILL_DIR}`. Run the script with whichever of `python3`,
`python` or `py -3` runs Python 3 (call it `PY` below). The target is the current working directory.

## Ground rules

- **Stay inside the target folder.** Read nothing outside it except paths the user names in step 3, and never scan
  neighbouring folders. Everything about the user comes from the user.
- **Ask little.** A few short questions, one preview, one yes. Don't interview.
- **Nothing is created before the yes**, and nothing is installed without its own yes.
- **No personal data in generated files** beyond what the user explicitly approves importing.

## 1. Check the folder

```
PY "${CLAUDE_SKILL_DIR}/scripts/scaffold.py" probe --target .
```
It reports whether the folder is empty (tool folders like `.git`, `.claude` and an installed skill don't count), which
Python command the hooks should use, and whether the Windows long-path guard applies. If `empty` is false, **stop**:
list what is there and ask whether to continue anyway. Continue only on a clear yes, and then pass `--allow-existing`
to `build` (it never overwrites; existing files are skipped and reported).

## 2. Purpose

Take the purpose from the invocation: `$ARGUMENTS`. If it is empty, ask "Purpose in 2–3 words?". If the purpose is
genuinely ambiguous in a way that changes the structure (writing a PhD vs applying to one), add one clarifying question
to the round below. Otherwise don't.

## 3. One round of questions

Ask these together in a single AskUserQuestion call (keep the wording short):

1. **Model tier** (you can't detect the subscription):
   - *Fable-led (Max):* deep = `fable`, standard = `opus`, routine = `sonnet`
   - *Opus cap:* deep = `opus`, standard = `sonnet`, routine = `sonnet`
   - *Sonnet cap (Pro):* everything `sonnet`
2. **Extras** (multi-select): Playwright CLI for real-browser work · `git init` · pin a model for the main session
   (only at or below the cap; if chosen, ask which).
3. **Existing material elsewhere?** No / Yes, I'll give the paths.

If they have existing material, there are **two consent gates**:
- Read **only** the paths the user types. List what you found (name, type, size, one-line gist), no more.
- Ask which items to bring in, item by item (multi-select is fine). Only approved items go in the plan's `imports`,
  each mapped to its destination folder. They are copied at build time; originals are never moved or changed.

## 4. Design the project (think hard here)

Read `references/purpose-patterns.md` and `references/archetypes.md`, then `references/plan-format.md` for the exact
format. `references/example-plan-phd.json` is a complete worked example. Design:

- **Domain folders** `01_…09_`: real homes for real files, 5–9 of them, named in the purpose's own vocabulary.
- **The tracker:** the unit of work (its item), the types, the lifecycle (statuses), the few columns worth sorting by,
  and whether each item earns its own folder.
- **The team:** 4–8 specialists from the archetypes, renamed and rewritten for this purpose, each with a clear lane that
  doesn't overlap another's, and a tier that matches how much judgement the lane needs. The reviewer is added for you.
- **Writing norm:** which folders hold outgoing text (anything a person outside the project reads); the style lint
  hook watches them. Name the readers and the concrete details good writing in this field uses.
- **Source policy:** which folders hold research, which files must cite sources, and tier examples that fit the purpose
  (for open source, T1 is official docs, maintainers' repos and release notes; for fundraising, filings and the
  investors' own sites). The source check hook watches those folders.
- **HANDOFF content:** what only the user can do next, and the first 3–5 actions for the next session.

Write the plan to `.claude/setup-plan.json`.

### Second pass: review the whole design before showing it

Read the plan again as a sceptical expert in this purpose would, and fix what you find:
- Would someone doing this work recognise the folders and the lifecycle as theirs? Is anything generic filler?
- Does every recurring kind of file have exactly one obvious home? Does any folder have no clear contents?
- Do any two agents write to the same place? Is any lane so thin it should merge, or so broad it should split?
- Are tiers honest (deep only where judgement or taste decides the outcome; routine for sweeps and logging)? Deep
  runs cost the most, so usually no more than about half the team (plus the reviewer) is deep.
- Does everything that leaves the project pass through a drafting lane, the reviewer and the user's approval? Is every
  folder that produces outgoing text in `writing.outgoing`, and every folder of findings in `sources.research`?
- Is the plan free of personal data and machine-specific paths?

## 5. Preview and one yes

```
PY "${CLAUDE_SKILL_DIR}/scripts/scaffold.py" preview --plan .claude/setup-plan.json --target .
```
Fix any `PLAN ERROR`. Show the preview to the user verbatim in a code block, then ask once: **Create it** /
**Change something**. On changes, edit the plan, re-run the preview and ask again. Don't create anything until the yes.

## 6. Build

```
PY "${CLAUDE_SKILL_DIR}/scripts/scaffold.py" build --plan .claude/setup-plan.json --target .
```
This writes everything: `CLAUDE.md` (rules, filing table, tracker, model policy, writing and replies, sources, access
boundary), `README.md`, `00_hub/` (HANDOFF, handoffs/, decisions, lessons, activity log, team charter, writing-style,
source-policy, tracker CSV, `project.config.json`, `tasks/board.csv`), `tools/` (tracker, tasks, check_structure,
session_brief, model_cap, style_lint, source_check), the agents (the reviewer gates on the style lint and source check),
the `/handoff` skill, `.claude/settings.json` with the hooks (session brief, model-cap guard, style lint and source check
after each write, structure check at stop), `_archive/`, `_bin/`, and runs `git init` if chosen.

If Playwright CLI was chosen: `npm init -y`, then `npm install --save-dev --save-exact @playwright/cli@0.1.22` (a newer
exact version is fine), then install its Claude Code skill into the project with the local copy (check
`npx --no playwright-cli --help`; currently `npx --no playwright-cli install --skills`). If a step
fails, say so plainly and leave the rest of the setup in place.

Finish with: append a line to `00_hub/activity-log.md` for anything done after the build (the Playwright install, for
example), then `PY tools/check_structure.py` must report 0 errors. Fix anything it reports, except files the user had
in the folder before setup: ask where those belong (a domain folder, or `_archive/pre-setup/`) rather than moving them yourself.

## 7. Recommend, don't install

Pick up to five skills or MCP servers from `references/recommendations.md` that clearly fit this purpose: safe,
preferably official or first-party, each with a one-line reason and the access it needs. Fewer is better than padding;
none is fine. Follow the rules in that file. Install nothing
unless the user says yes to that item.

## 8. Final reply: brief

Key facts only, roughly this shape and no longer:

```
Set up <title>: <N> folders, tracker `00_hub/<name>.csv` (<items>), <M> agents (cap: <cap>), hooks, /handoff.
Next: restart Claude Code in this folder (exit, then run `claude`) so the hooks and agents load. The brief appears automatically.
Then: <the first thing the user should do, from HANDOFF "Waiting on the user">.
Optional, say yes to any: <name: reason (access)> · <name: reason (access)>
```

No tour of the files, no recap of the plan they already approved.
