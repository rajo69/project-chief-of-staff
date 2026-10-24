# Project Chief of Staff

A Claude Code plugin that turns an empty folder into a long-running project, set up for whatever you're working on:
an open source tool, a seed round, a PhD, a book, a job search. You state the purpose in a few words, answer one round
of questions, approve a one-screen preview, and the folder is ready.

From then on, every Claude Code session in that folder starts where the last one stopped. The main session acts as
your Chief of Staff: it keeps the state, decides what to delegate, and hands work to a team of specialist subagents
designed for your purpose.

**Works in:** Claude Code (terminal, IDE extensions, and the desktop app's Code tab). It doesn't work in claude.ai chat,
which has no project folder to set up. **Needs:** Python 3.9 or later.

## Install

In a Claude Code session (v2.1.275 or later):

```
/plugin install project-chief-of-staff --marketplace rajo69/project-chief-of-staff
```

Or in two steps, on any version:

```
/plugin marketplace add rajo69/project-chief-of-staff
/plugin install project-chief-of-staff@project-chief-of-staff
```

Without the plugin system, copy `skills/project-chief-of-staff/` from this folder into `~/.claude/skills/`. Each
[release](https://github.com/rajo69/project-chief-of-staff/releases) also has a single-file `SKILL.md` with the scripts
embedded, for places where one file is easier to handle. It puts about 40,000–55,000 tokens into context on every
run, while the folder version reads its reference files only when it needs them, so prefer the folder.

## Use

Open Claude Code in an empty folder and run:

```
/project-chief-of-staff an open source CLI tool
```

Claude asks which model tier you have (Fable-led, Opus cap or Sonnet cap), whether you want `git init` or the
Playwright CLI, and whether you have existing material to bring in. It then designs the project and shows a preview.
Nothing is written until you say yes. After the build, restart Claude Code in the folder so the hooks and agents load.

## What you get

```
CLAUDE.md             rules: filing table, tracker, model policy, writing norm, sources, access boundary
README.md             the map for people
00_hub/               HANDOFF, handoffs/, decisions, lessons, activity log, team charter, writing style,
                      source policy, the tracker CSV, project.config.json, tasks/board.csv
01_… to 09_…          domain folders named in your field's own vocabulary
tools/                tracker, task board, structure check, session brief, model-cap guard, style lint, source check
.claude/agents/       4–8 specialists plus a red-team reviewer, each with a model tier under your cap
.claude/skills/       /handoff, for ending a session cleanly
.claude/settings.json the hooks listed below
_archive/  _bin/      snapshots and discarded files (nothing is deleted)
```

## What it runs and writes

So you can judge it before installing:

- **During setup**, Claude runs the bundled script `skills/project-chief-of-staff/scripts/scaffold.py` with your local
  Python. It writes only inside the current folder and never overwrites a file. Apart from its working plan
  (`setup-plan.json`, moved into `00_hub/` by the build), it writes nothing until you approve the preview. If the folder isn't empty, it stops and asks.
- **Your files elsewhere** are read only if you type their paths, and copied in only item by item with your approval.
  Originals are never moved or changed.
- **The generated project** gets `.claude/settings.json` with four hooks. Each runs a Python script from the project's
  own `tools/` folder:
  - SessionStart: `session_brief.py` prints the handoff, open tasks and open tracker items into the session.
  - PreToolUse on subagent launches: `model_cap.py` blocks a launch above your model cap.
  - PostToolUse on Write and Edit: `style_lint.py` and `source_check.py` flag stock phrasing in outgoing text and weak
    sources in research files. They never block.
  - Stop: `check_structure.py` blocks ending a turn while the activity log is stale or files sit loose at the root.
- **Network:** the plugin and the generated tools make no network requests and send no data anywhere. Two setup
  steps are optional, and run only if you choose them: `git init`, which stays local, and the Playwright CLI. For the
  Playwright CLI, Claude uses npm to add the `@playwright/cli` package, pinned to an exact version, to the project's own
  `node_modules/`. That is the one step that downloads anything (from the npm registry), and the project then runs
  only that local copy.
- **Recommendations:** at the end, Claude may suggest up to five skills or MCP servers that fit your purpose. It
  installs none of them unless you say yes to each one.
- No telemetry, and no permission settings are changed.

## Source

[github.com/rajo69/project-chief-of-staff](https://github.com/rajo69/project-chief-of-staff) holds the source, the
single-file build, the tests and the issue tracker.

## License

[MIT](LICENSE)
