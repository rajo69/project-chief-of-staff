"""Build the single-file edition of project-chief-of-staff from the skill folder.

    python build_single.py            # writes dist/project-chief-of-staff/SKILL.md, then tests it
    python build_single.py --no-test  # build only

The skill folder (plugins/project-chief-of-staff/skills/project-chief-of-staff/) is the source of truth and the main
distribution. This script turns it into one self-extracting SKILL.md: the same instructions, with scripts/scaffold.py,
templates/** and references/** embedded
verbatim at the end. At run time Claude unpacks them into the target's .claude/_project-chief-of-staff/ with one command and
then runs exactly the same scaffold. Rebuild after every change to the folder; never edit the output by hand.

Every text rewrite of SKILL.md is checked by count, so if the folder's SKILL.md changes in a way the rewrites no longer
fit, the build fails instead of producing a stale file. The test builds the PhD example plan twice (folder edition and
single-file edition, running the commands as written in the generated file) and requires identical output.
"""
import base64
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
SKILL = ROOT / "plugins" / "project-chief-of-staff" / "skills" / "project-chief-of-staff"
OUT = ROOT / "dist" / "project-chief-of-staff" / "SKILL.md"
UNPACK = ".claude/_project-chief-of-staff"
EMBED = ["scripts/scaffold.py", "templates", "references"]
# Text Claude Code would substitute or execute when it loads a skill. A file containing any of it is embedded as
# base64 instead of plain text, so loading the skill can't change it (the sha256 check would catch it anyway).
RISKY = re.compile(r"\$ARGUMENTS|\$\d|\$\{CLAUDE_[A-Z_]+\}|!`")
LANG = {".py": "python", ".md": "markdown", ".json": "json"}

BOOTSTRAP = ('PY -c "import sys;t=open(sys.argv[1],encoding=\'utf-8\').read().replace(chr(13),\'\');'
             'exec(t[t.index(\'#\'+\'<extractor>\'):t.index(\'#\'+\'</extractor>\')])" "${CLAUDE_SKILL_DIR}/SKILL.md"')
CLEANUP = (f'PY -c "import os,shutil;shutil.rmtree(\'{UNPACK}\',True);'
           f'os.path.isdir(\'.claude\') and not os.listdir(\'.claude\') and os.rmdir(\'.claude\')"')

STEP0 = f"""## 0. Unpack

This is the single-file edition: the skill's scripts, templates and references are embedded at the end of this file.
Unpack them into the target folder first (on agents other than Claude Code, use this file's own path):
```
{BOOTSTRAP}
```
It writes them to `{UNPACK}/` (a tooling folder, so the empty check below ignores it) and checks every file's
hash. The `references/…` files named below are also embedded at the end of this file, under the same paths: read them
there. Remove the unpacked copy whenever the skill ends, after the build or because you stopped early:
```
{CLEANUP}
```

"""

EXTRACTOR = '''#<extractor>
import base64, hashlib, os, re
dest, n = {unpack!r}, 0
for m in re.finditer(r"<!-- FILE (\\S+) sha256=([0-9a-f]{{64}}) nl=([01]) enc=(text|b64) -->\\n(~{{4,}})[a-z]*\\n(.*?)\\n\\5\\n", t, re.S):
    path, digest, nl, enc, body = m.group(1), m.group(2), m.group(3), m.group(4), m.group(6)
    if path.startswith("/") or ".." in path.split("/"):
        sys.exit("unsafe path: " + path)
    data = base64.b64decode(body) if enc == "b64" else (body + "\\n" * (nl == "1")).encode("utf-8")
    if hashlib.sha256(data).hexdigest() != digest:
        sys.exit("embedded file is damaged: " + path)
    out = os.path.join(dest, *path.split("/"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(data)
    n += 1
if n != {count}:
    sys.exit(f"expected {count} embedded files, found {{n}}: this SKILL.md is damaged")
print(f"unpacked {{n}} files to {{dest}}")
#</extractor>'''


def rewrite(text, old, new, count=1):
    found = text.count(old)
    if found != count:
        sys.exit(f"build_single: expected {count}x {old!r} in SKILL.md, found {found}. Update the rewrites.")
    return text.replace(old, new)


def files():
    out = []
    for e in EMBED:
        p = SKILL / e
        out += [p] if p.is_file() else sorted(q for q in p.rglob("*") if q.is_file() and "__pycache__" not in q.parts)
    return out


def block(p):
    rel = p.relative_to(SKILL).as_posix()
    data = p.read_bytes().replace(b"\r\n", b"\n")
    digest = hashlib.sha256(data).hexdigest()
    try:
        text = data.decode("utf-8")
        enc = "b64" if RISKY.search(text) else "text"
    except UnicodeDecodeError:
        enc = "b64"
    if enc == "b64":
        body, nl = "\n".join(re.findall(".{1,100}", base64.b64encode(data).decode())), "1"
    else:
        body, nl = text[:-1] if text.endswith("\n") else text, "1" if text.endswith("\n") else "0"
    fence = "~" * max(4, max((len(r) for r in re.findall(r"~+", body)), default=0) + 1)
    lang = "text" if enc == "b64" else LANG.get(p.suffix, "text")
    return f"<!-- FILE {rel} sha256={digest} nl={nl} enc={enc} -->\n{fence}{lang}\n{body}\n{fence}\n"


def build():
    src = (SKILL / "SKILL.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    m = re.match(r"(---\n.*?\n---\n)(.*)", src, re.S)
    if not m:
        sys.exit("build_single: SKILL.md has no frontmatter")
    front, body = m.groups()
    body = rewrite(body, "Paths below are relative to this skill's folder, `${CLAUDE_SKILL_DIR}`.",
                   f"Step 0 unpacks the scripts to `{UNPACK}/`; the commands below run them from there.")
    body = rewrite(body, '"${CLAUDE_SKILL_DIR}/scripts/scaffold.py"', f"{UNPACK}/scripts/scaffold.py", 3)
    body = rewrite(body, "## 1. Check the folder\n", STEP0 + "## 1. Check the folder\n")
    body = rewrite(body, "## 7. Recommend, don't install\n",
                   f"Then remove the unpacked copy (step 0).\n\n## 7. Recommend, don't install\n")
    if body.count("${CLAUDE_SKILL_DIR}") != 1 or re.search(r"(?<!_project-chief-of-staff/)scripts/scaffold\.py", body):
        sys.exit("build_single: a path in SKILL.md still points into the skill folder. Update the rewrites.")

    fs = files()
    parts = [front,
             "\n<!-- Single-file edition, generated by build_single.py from the project-chief-of-staff folder. "
             "Edit the folder and rebuild; don't edit this file. -->\n",
             body.rstrip("\n") + "\n",
             "\n## Appendix: embedded files\n\n"
             "Step 0 unpacks these with the extractor below. They are the skill folder's files, verbatim.\n\n"
             "```python\n" + EXTRACTOR.format(unpack=UNPACK, count=len(fs)) + "\n```\n"]
    parts += ["\n" + block(p) for p in fs]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes("".join(parts).encode("utf-8"))
    size = OUT.stat().st_size
    print(f"built {OUT.relative_to(ROOT)}: {len(fs)} embedded files, {size:,} bytes "
          f"(roughly {size // 4:,}-{size // 3:,} tokens loaded per run)")


def commands(text):
    """The PY commands from the generated SKILL.md's code blocks, in order, ready to run."""
    body = text.split("\n## Appendix: embedded files\n")[0]
    return [line for line in re.findall(r"^PY .*$", body, re.M)]


def run(cmd, cwd, skill_dir):
    cmd = cmd.replace("${CLAUDE_SKILL_DIR}", skill_dir.as_posix())
    cmd = f'"{sys.executable}"' + cmd[2:]
    args = cmd if os.name == "nt" else shlex.split(cmd)
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", input="{}")
    if r.returncode:
        sys.exit(f"test: command failed ({r.returncode}): {cmd}\n{r.stdout}{r.stderr}")
    return r.stdout


def tree(d):
    out = {}
    for p in sorted(d.rglob("*")):
        if p.is_file() and ".git" not in p.relative_to(d).parts:
            out[p.relative_to(d).as_posix()] = p.read_bytes()
    return out


def test():
    text = OUT.read_text(encoding="utf-8")
    cmds = commands(text)
    pick = lambda key: next(c for c in cmds if key in c)  # noqa: E731
    unpack, probe, preview, build_, cleanup = (pick("<extractor>"), pick(" probe "), pick(" preview "),
                                               pick(" build "), pick("rmtree"))
    plan = (SKILL / "references" / "example-plan-phd.json").read_bytes()
    tmp = Path(tempfile.mkdtemp(prefix="project-chief-of-staff-test-"))
    try:
        skill_dir = tmp / "skills" / "project-chief-of-staff"
        skill_dir.mkdir(parents=True)
        shutil.copy(OUT, skill_dir / "SKILL.md")
        a, b = tmp / "folder-edition", tmp / "single-edition"
        for t in (a, b):
            t.mkdir(parents=True)

        def steps(target, cmds):
            # The order the skill follows: probe the empty folder, write the plan, preview, build.
            outs = [run(cmds[0], target, skill_dir)]
            (target / "setup-plan.json").write_bytes(plan)
            return outs + [run(c, target, skill_dir) for c in cmds[1:]]

        scaffold = f'PY "{(SKILL / "scripts" / "scaffold.py").as_posix()}"'
        outs_a = steps(a, [c.replace(f"PY {UNPACK}/scripts/scaffold.py", scaffold) for c in (probe, preview, build_)])

        print("test: " + run(unpack, b, skill_dir).strip())
        outs_b = steps(b, [probe, preview, build_])
        if (a / "setup-plan.json").exists() or (b / "setup-plan.json").exists():
            sys.exit("test: the build left setup-plan.json at the project root")
        if not json.loads(outs_b[0]).get("empty"):
            sys.exit(f"test: probe doesn't see the target as empty after unpacking:\n{outs_b[0]}")
        print("test: " + run("PY tools/check_structure.py", b, skill_dir).strip().splitlines()[-1])
        run(cleanup, b, skill_dir)
        if (b / UNPACK).exists():
            sys.exit("test: cleanup left the unpacked copy behind")

        if outs_a[1] != outs_b[1]:
            sys.exit("test: the two editions print different previews")
        ta, tb = tree(a), tree(b)
        diff = sorted(k for k in set(ta) | set(tb) if ta.get(k) != tb.get(k))
        if diff:
            sys.exit("test: the two editions built different files:\n  " + "\n  ".join(diff[:20]))
        print(f"test: passed. Both editions built the same {len(ta)} files from the PhD example plan.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    build()
    if "--no-test" not in sys.argv:
        test()
