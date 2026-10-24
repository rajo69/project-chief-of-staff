---
name: handoff
description: Write the end-of-session handoff for this project so a fresh session can resume with no loss. Use when the user says /handoff, "handoff", "wrap up", "switching sessions", "new session", or the context is getting large.
---

# Session handoff

The next session starts with an empty context. Everything it needs must be in files, and the SessionStart hook
(`tools/session_brief.py`) loads `00_hub/HANDOFF.md` automatically. Write for a capable colleague who has seen nothing.

## Steps

1. **Collect state** (cheap commands only, no bulk reading):
   `{{PY}} tools/tasks.py list` · `{{PY}} tools/tracker.py list` · the last few entries of `00_hub/activity-log.md`.
2. **Close the loop on finished tasks:** for every task the team completed, make sure its board status and `summary` are
   set, its lessons are in `00_hub/lessons.md` and its decisions are in `00_hub/decisions.md`.
3. **Archive** the current handoff: copy `00_hub/HANDOFF.md` to `00_hub/handoffs/YYYY-MM-DD_session-NN.md`
   (NN = the `session` number in its header).
4. **Rewrite `00_hub/HANDOFF.md`** using the section layout already in that file. Increment `session`. **Keep it under
   ~120 lines.** Use pointers to files, not copied content. State facts, not narrative. Include:
   - **Phase and objective** right now
   - **Done this session:** outcomes, with paths
   - **In flight:** open tasks (id, owner, state, what's left)
   - **Waiting on the user:** questions and decisions only the user can make
   - **Next actions:** the first 3–5 things the next session should do, in order, each naming the agent to delegate to
   - **Watch-outs:** anything fragile, half-done or easy to get wrong
5. **Append** an entry to `00_hub/activity-log.md`.
6. **Verify:** `{{PY}} tools/check_structure.py` must report 0 errors.
7. **Tell the user** in two or three lines: the handoff is written; start a new session in this folder; the brief loads
   automatically. Name the first thing the next session will do.

## Rules

- Never put personal details in the handoff. Point to the files the user imported instead.
- Don't start new work during a handoff.
