# Project Chief of Staff

<img src="assets/icon.svg" alt="" width="96" align="right">

A Claude Code plugin that turns an empty folder into a long-running project, set up for whatever you're working on:
an open source tool, a seed round, a PhD, a book, a job search. You state the purpose in a few words, answer one round
of questions, approve a one-screen preview, and the folder is ready. From then on, every session in that folder starts
where the last one stopped, with the main session acting as your Chief of Staff over a team of specialist subagents.

**The plugin's own README, with what it builds and everything it runs and writes, is
[plugins/project-chief-of-staff/README.md](plugins/project-chief-of-staff/README.md).**

## Install

In a Claude Code session:

```
/plugin marketplace add rajo69/project-chief-of-staff
/plugin install project-chief-of-staff@project-chief-of-staff
```

Then open Claude Code in an empty folder and run `/project-chief-of-staff <purpose>`, for example
`/project-chief-of-staff an open source CLI tool`. It works in Claude Code only and needs Python 3.9 or later.

## This repository

| Path | What it is |
|---|---|
| `.claude-plugin/marketplace.json` | The marketplace, with one plugin |
| `plugins/project-chief-of-staff/` | The plugin: its manifest and listing icon in `.claude-plugin/`, the skill, its README and licence. This folder is all that gets installed |
| `evals/` | Three test cases for `claude plugin eval`: an open source project, a seed round, and a folder that isn't empty |
| `build_single.py` | Builds `dist/project-chief-of-staff/SKILL.md`, the single-file edition attached to each release, and tests it |
| `assets/icon.svg` | Source of the icon |

## Develop

- Edit the skill in `plugins/project-chief-of-staff/skills/project-chief-of-staff/`.
- `python build_single.py` builds the single-file edition and tests it: it builds the example plan with both editions
  and requires identical output. CI runs this on Linux, macOS and Windows with Python 3.9 and 3.13.
- `claude plugin validate --strict .` checks the marketplace.
- The evals sit outside the plugin folder so installs stay small, and `claude plugin eval <path>` only reads evals inside
  the plugin. Run them against the installed plugin from the repository root instead:
  `claude plugin eval project-chief-of-staff@project-chief-of-staff`.

## License

[MIT](LICENSE)
