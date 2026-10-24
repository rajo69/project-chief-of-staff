# tools: project scripts (Python 3, standard library only)

| Script | Does |
|---|---|
| `tracker.py` | The **only** way to change `{{CSV}}`: `add` an item, `promote` it (creates its folder), `update` fields, `list` open items, `schema` (types, statuses, columns). Rules come from `00_hub/project.config.json` |
| `tasks.py` | The task board: `new` (creates `00_hub/tasks/T###_<slug>/brief.md`), `update`, `list` |
| `check_structure.py` | Audits the layout. With `--hook` it is the **Stop hook**: blocks ending a turn on stray root files, tracker/folder or board/folder mismatches, missing hub files, an out-of-date activity log, or over-long paths |
| `model_cap.py` | **PreToolUse hook** on agent launches: blocks a `model` above the cap in `00_hub/project.config.json` |
| `style_lint.py` | Flags AI stylistic patterns in outgoing text (`00_hub/writing-style.md`). With `--hook` it is a **PostToolUse hook** on Write/Edit for the outgoing folders: it feeds flags back and never blocks. The reviewer runs it on every outgoing artifact |
| `source_check.py` | Flags AI or search-result citations, unlabelled T3 links and reports without URLs (`00_hub/source-policy.md`). With `--hook` it is a **PostToolUse hook** for the research folders; never blocks |
| `session_brief.py` | The **SessionStart hook**: prints `HANDOFF.md`, open tasks and open items into the new session (kept under 10,000 characters) |

```
{{PY}} tools/tracker.py schema
{{PY}} tools/tracker.py list
{{PY}} tools/tasks.py new --owner <agent> --title "..." [--depends T001]
{{PY}} tools/tasks.py update T001 status=done summary="..."
{{PY}} tools/check_structure.py
{{PY}} tools/style_lint.py <file>
{{PY}} tools/source_check.py <file>
```
