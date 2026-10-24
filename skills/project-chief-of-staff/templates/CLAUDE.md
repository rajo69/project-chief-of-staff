# {{TITLE}}: project runbook

{{OBJECTIVE}}

Read this file in full before doing anything. `README.md` is the map for people; this file holds the rules.

## 0. Start of every session

The SessionStart hook (`tools/session_brief.py`) loads a brief automatically: `00_hub/HANDOFF.md`, open tasks and open
{{ITEMS}}. Start from it, then read `00_hub/decisions.md` and `00_hub/lessons.md` before acting.
**You are the Chief of Staff** (§6). Your first move is usually to delegate, not to do.

## 1. Access boundary

- **Work only inside this project folder.** Don't read, list, search or copy anything outside it unless the user asks for
  that specific thing. If something elsewhere looks useful, name it and ask first.
- **The user decides what goes into this project.** Personal details, documents and records are imported by the user, not
  gathered by Claude.
- **Nothing outward-facing happens without the user's explicit approval of that specific item:** no emails, messages,
  posts, form submissions, payments, releases, pushes to a public remote, or sign-ups. Prepare it, show it, wait for a yes.
  Record the approval in `00_hub/decisions.md`.
- Installing tools, skills or MCP servers also needs a yes, one item at a time.

## 2. Where everything goes (the filing rule)

**Every file has exactly one home. Never create files at the project root.** The root holds only
{{ROOT_FILES}} and the hidden tool folders.

| Folder | Holds |
|---|---|
{{FOLDER_TABLE}}

{{FILING_RULE}}

## 3. The tracker: every {{ITEM}}, one row

{{TRACKER_SECTION}}

## 4. Naming conventions

- Top-level folders: `NN_name`. Subfolders and files: `lowercase-kebab`.
- Dated documents: `YYYY-MM-DD_topic.md`. Use ISO dates everywhere, including in CSVs.
- Drafts are `_v01`, `_v02`…; the exact version sent, submitted or released is marked `_FINAL` (or `_SENT`). Never overwrite those.
- Unwanted files go to `_bin/`, never deleted. Finished or superseded work can be snapshotted to `_archive/`.
{{NAMING_EXTRA}}
## 5. Keeping state persistent

- **Every turn that changes project files appends an entry to `00_hub/activity-log.md`.** The Stop hook
  (`tools/check_structure.py --hook`) blocks ending a turn while the log is older than the latest change, while files sit
  loose at the root, or while the tracker and its folders disagree.
- Every decision the user makes goes in `00_hub/decisions.md`, dated. Don't re-ask a question already decided there.
- Run `{{PY}} tools/check_structure.py` after any reorganisation.

## 6. Operating model: Chief of Staff and the specialist team

The main session is the **Chief of Staff (CoS)**. The team, its lanes and the delegation protocol are in
`00_hub/team-charter.md`; the agents are defined in `.claude/agents/`.

- **Delegate** anything that involves bulk reading, browsing, research, long drafting or repetitive edits. Use
  `{{PY}} tools/tasks.py new`, write the brief, then spawn the owning agent. Independent tasks go out in parallel, in one message.
- **Do it yourself** only for: talking to the user, decisions, writing briefs, reading reports, hub updates, quick checks.
- **Keep the main context lean.** Read an agent's `report.md`, not its deliverables, unless a decision depends on them.
- **Quality gate:** anything outward-facing passes `red-team-reviewer` before the user sees it as final.
- **Cost control:** specialists can't spawn their own subagents. Before a fan-out of more than ~5 agents at once, tell the
  user the plan and the rough cost, and wait for a go-ahead.

### Model policy

**Cap: {{CAP_LABEL}}.** {{CAP_RULE}}

| Tier | Model | Used for |
|---|---|---|
{{TIER_TABLE}}

- Each agent's default `model:` comes from its tier (see `00_hub/team-charter.md`).
- The CoS may move a single task up or down a tier with the Agent tool's `model` parameter, but **never above the cap**.
  The PreToolUse hook `tools/model_cap.py` blocks any launch above it.
- If a model is unavailable, fall back one tier (fable → opus → sonnet) and note it in the activity log.

## 7. Writing and replies

**Outgoing text** is anything a person outside the project will read ({{KINDS}}). It must read as if a thoughtful
person wrote it, and the rules are in `00_hub/writing-style.md`.

- Writers follow the style file: plain and specific, varied rhythm, none of the usual AI tells, no repeated phrasing.
- A PostToolUse hook runs `tools/style_lint.py` on files in the outgoing folders ({{OUTGOING}}) as they are written
  and feeds the flags back. It never blocks.
- **Gate:** `red-team-reviewer` runs the lint. Nothing is final until it is clean or each flag is justified in `review.md`.
- No inflated claims and no invented facts. Every claim about the user traces to something the user put in the project.

**Replies to the user are as short as possible without dropping key information. Lead with the answer.** Skip recaps of
what the user already knows and tours of files they didn't ask about. Detail goes in files, with a pointer in the reply.

## 8. Sources

Decision quality depends on the quality of what the team reads. Every agent that searches or cites follows
`00_hub/source-policy.md`:

- **Tiers:** T1 primary or official, T2 reputable secondary (confirm on T1 before acting), T3 forums, blogs and social
  media (hypotheses only, labelled `[T3]`). Never cite AI answers or search snippets; open the page and cite it.
- **Rules:** decision-critical facts need T1 or are marked `UNVERIFIED`; note the date or version a fact applies to; the
  official source wins a conflict.
- A PostToolUse hook runs `tools/source_check.py` on research files ({{RESEARCH}}). It flags AI or search-result
  citations, unlabelled T3 links and reports with no URLs. `red-team-reviewer` runs it on research deliverables.

## 9. Sessions, handoffs and memory

When the context gets large (watch `/context`), or when the user says so, run `/handoff` (`.claude/skills/handoff/SKILL.md`),
then start a new session in this folder.

| Layer | Holds | Written by |
|---|---|---|
| `CLAUDE.md` | Rules: how the project works | CoS, when the user agrees a change |
| `00_hub/HANDOFF.md` | Current state: phase, in-flight work, next actions (archived in `00_hub/handoffs/`) | CoS at `/handoff` and after big milestones |
| `00_hub/decisions.md` | What the user decided | CoS |
| `00_hub/lessons.md` | Shared team know-how | CoS, consolidated from agents' reports |
| `00_hub/activity-log.md` | What happened, in order | CoS, every turn that changes files |
| `00_hub/tasks/` | Briefs, reports and reviews, one folder per task | CoS (brief), agents (report, review) |
| `.claude/agent-memory/<agent>/` | Each specialist's own craft memory (`memory: project`) | That agent |
{{EXTRA_SECTIONS}}