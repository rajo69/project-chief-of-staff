# Team charter: how the agent team works

## Operating model

The **main session is the Chief of Staff (CoS)**. It talks to the user, makes and records decisions, plans the work, briefs
specialists, reviews what comes back and keeps the hub current. **It doesn't do bulk work itself.** Long research, reading
many pages, long drafts and repetitive edits go to specialists, so the main context stays small enough for good judgement
and lasts until the next handoff.

The specialists are defined in `.claude/agents/`. Each owns a lane and the folders that go with it.

| Agent | Role | Tier → model | Owns (writes to) | Typical jobs |
|---|---|---|---|---|
{{ROSTER_TABLE}}

Model cap for this project: **{{CAP_LABEL}}** (see `CLAUDE.md` §6). The CoS may move one task up or down a tier with the
Agent tool's `model` parameter, never above the cap.

The hub (`00_hub/HANDOFF.md`, `activity-log.md`, `decisions.md`, `lessons.md`, the task board's summary column) is
**CoS-only**, so parallel agents never collide on the same file.

## Delegation protocol

1. **Task:** `{{PY}} tools/tasks.py new --owner <agent> --title "..." [--item NNN] [--depends T001,T002]`
2. **Brief:** the CoS fills in `00_hub/tasks/T###_<slug>/brief.md`: goal, inputs, exact deliverable paths, constraints,
   done-when. The brief is the agent's only context, so write it for a capable colleague who has seen nothing.
3. **Spawn:** call the agent with `Execute task T### (brief at 00_hub/tasks/T###_<slug>/brief.md)`.
4. **Report:** the agent writes `report.md` next to the brief and returns **at most 8 lines**: outcome, paths written,
   decisions needed. Long content stays in files, never in the reply.
5. **Close:** the CoS reads the report (not the deliverables, unless a decision needs them), runs
   `{{PY}} tools/tasks.py update T### status=done summary="..."`, and moves lessons into `lessons.md` and decisions into `decisions.md`.

`report.md` sections: **Summary** · **Files written** · **Decisions needed** · **Handoff notes** (for named agents) · **Lessons**.

## Coordination between agents

- **Through files.** Downstream tasks list upstream ones in `depends_on` and start by reading their `report.md`. The
  upstream agent's "Handoff notes" speak directly to the next agent.
- **Typical chains:**
{{FLOWS}}
- **Parallel work** only when tasks write to different files. Two agents never edit the same file at the same time.
- **Direct messages:** every specialist has `SendMessage`, so a running agent can ask a running teammate a quick question
  by name. Anything that must last goes in files; messages vanish with the session.
- **No nesting:** specialists can't spawn subagents (`Agent` isn't in their tool lists). Only the CoS dispatches.
- **Each agent's own memory:** `memory: project` gives each specialist `.claude/agent-memory/<agent>/MEMORY.md` for craft
  knowledge in its lane. Cross-team lessons still go through `00_hub/lessons.md`.
- **Not used:** Claude Code's experimental agent-teams mode. Its state lives outside this folder and isn't restored on resume.

## Escalation: when an agent stops and reports instead of acting

- It needs a decision that belongs to the user (scope, priorities, framing, anything personal).
- It would need to read or write anything **outside the project folder**.
- The next step is outward-facing: sending, submitting, posting, publishing, paying, contacting anyone.
- A fact about the user is needed that isn't in the project. **Never invent it; report the gap.**
- A CAPTCHA, login, payment or credential is needed.

## Quality gate

Nothing outward-facing reaches the user as final until `red-team-reviewer` has reviewed it and its review is resolved.
The reviewer gets the artifact and the requirements, not the writer's reasoning, so its read stays independent.

- **Writing:** the reviewer runs `{{PY}} tools/style_lint.py`; PASS needs a clean lint or every flag justified in `review.md`
  (rules: `00_hub/writing-style.md`).
- **Sources:** research deliverables also go through `{{PY}} tools/source_check.py`; decision-critical facts need T1
  sources or an `UNVERIFIED` mark (rules: `00_hub/source-policy.md`).
