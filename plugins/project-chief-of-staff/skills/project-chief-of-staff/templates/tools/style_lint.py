"""Flag AI stylistic patterns and repetition in outgoing text (rules: 00_hub/writing-style.md).

    python tools/style_lint.py <file> [<file> ...]
    python tools/style_lint.py --hook      # PostToolUse hook: lints outgoing files as they are written

Exit 0 = clean, 1 = findings. Findings are prompts for a human-quality rewrite, not automatic failures:
the reviewer either fixes each one or justifies it in review.md. Hook mode never blocks; it feeds findings back to the writer.
Which folders count as outgoing is set in 00_hub/project.config.json ("writing" -> "outgoing").
"""
import json
import os
import re
import sys
from collections import Counter

sys.dont_write_bytecode = True
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_NAMES = {"review.md", "report.md", "brief.md"}  # plus each top folder's own README.md (see skipped)

PHRASES = [
    r"\bdelv(e|es|ing)\b", r"\btapestry\b", r"\btestament to\b", r"\bever-evolving\b", r"\bfast-paced\b",
    r"\bnavigat(e|ing) the complexit", r"\bembark", r"\bjourney\b", r"\brealm\b", r"\bpivotal\b", r"\bfoster(s|ing)?\b",
    r"\bunderscore", r"\bshowcas", r"\bmeticulous", r"\bintricate\b", r"\bmultifaceted\b", r"\bseamless", r"\bcutting-edge\b",
    r"\bgame-changer\b", r"\bunlock", r"\bsynerg", r"\bleverag(e|es|ing)\b", r"\brobust\b", r"\bholistic\b",
    r"hope this (email|message) finds you", r"\bI(?: am|'m) (so )?(excited|thrilled)\b",
    r"\bpassionate about\b", r"\bdeeply passionate\b", r"it(?:'s| is) worth noting", r"\bin conclusion\b",
    r"^\s*(furthermore|moreover)\b", r"\bnot only\b.*\bbut also\b", r"\bhighly motivated\b", r"\bin today's\b",
]
EM_DASH_PER_100_WORDS = 1.0
LONG_SENTENCE_WORDS = 40


def patterns_to_regex(patterns):
    """Folder patterns from the config -> one regex on forward-slash paths relative to the project root.
    'a/' matches everything under a/; '*' is one path segment; '*.md' style wildcards work inside a segment."""
    parts = []
    for p in patterns or []:
        p = p.strip().replace("\\", "/")
        while p.startswith("./"):
            p = p[2:]
        if not p:
            continue
        segs = p.strip("/").split("/")
        rx = "/".join("[^/]+" if s == "*" else re.escape(s).replace(r"\*", "[^/]*") for s in segs)
        parts.append("^" + rx + ("/" if p.endswith("/") else "$"))
    return re.compile("|".join(parts)) if parts else None


def config():
    try:
        with open(os.path.join(ROOT, "00_hub", "project.config.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def rel(path):
    try:
        return os.path.relpath(os.path.abspath(path), ROOT).replace("\\", "/")
    except ValueError:  # another drive on Windows
        return "../" + os.path.basename(path)


def lint(path, label=None):
    text = open(path, encoding="utf-8").read()
    path = label or path
    lines = text.splitlines()
    out = []
    for i, line in enumerate(lines, 1):
        for pat in PHRASES:
            m = re.search(pat, line, re.I)
            if m:
                out.append(f"{path}:{i}: stock phrase '{m.group(0)}'")
        if "!" in re.sub(r"!\[|<!--|!=", "", line):
            out.append(f"{path}:{i}: exclamation mark")
    words = len(re.findall(r"\b\w+\b", text))
    dashes = text.count("—")
    if words and dashes * 100 / words > EM_DASH_PER_100_WORDS:
        out.append(f"{path}: {dashes} em dashes in {words} words (max {EM_DASH_PER_100_WORDS} per 100)")
    # Sentence checks read prose only: code blocks, headings and list items each end a sentence.
    prose = re.sub(r"(?ms)^(```|~~~).*?^\1[ \t]*$", ". ", text)
    prose = re.sub(r"(?m)^[ \t]*#+[ \t]+(.*)$", r". \1.", prose)
    prose = re.sub(r"(?m)^[ \t]*([-*+]|\d+[.)])[ \t]+", ". ", prose)
    sentences = [s.strip() for s in re.split(r"(?<=[.?!])\s+", re.sub(r"\s+", " ", prose)) if len(s.split()) > 2]
    openers = [s.split()[0].strip("\"'(*_#-`").lower() for s in sentences]
    openers = [o for o in openers if o]
    for word, n in Counter(openers).items():
        if n >= 3 and n / max(len(sentences), 1) > 0.25:
            out.append(f"{path}: {n} of {len(sentences)} sentences start with '{word}'")
    for a, b, c in zip(openers, openers[1:], openers[2:]):
        if a == b == c:
            out.append(f"{path}: three sentences in a row start with '{a}'")
            break
    for s in sentences:
        if len(s.split()) > LONG_SENTENCE_WORDS:
            out.append(f"{path}: long sentence ({len(s.split())} words): '{s[:60]}...'")
    lengths = [len(s.split()) for s in sentences]
    if len(lengths) >= 6 and max(lengths) - min(lengths) <= 6:
        out.append(f"{path}: sentence lengths are uniform ({min(lengths)}-{max(lengths)} words); vary the rhythm")
    return out


def skipped(r, names):
    """Task files, templates, and the README.md that explains each top-level folder. Deeper READMEs are real content."""
    name = r.rsplit("/", 1)[-1]
    return name in names or (name == "README.md" and r.count("/") == 1) or "/_template" in "/" + r


def is_outgoing(path, outgoing=None):
    outgoing = outgoing if outgoing is not None else patterns_to_regex(config().get("writing", {}).get("outgoing"))
    r = rel(path)
    name = os.path.basename(r)
    return (bool(outgoing and outgoing.search(r)) and not skipped(r, SKIP_NAMES)
            and not name.endswith(".trace.md") and name.endswith((".md", ".txt")))


def hook():
    try:
        path = json.load(sys.stdin).get("tool_input", {}).get("file_path", "")
    except (ValueError, AttributeError):
        return
    if not path or not os.path.isfile(path) or not is_outgoing(path):
        return
    findings = lint(path, rel(path))
    if findings:
        msg = ("Style lint (00_hub/writing-style.md) flagged outgoing text. Rewrite these naturally, "
               "or justify them in the report:\n" + "\n".join(findings[:25]))
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:] == ["--hook"]:
        return hook()
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    findings = [f for p in sys.argv[1:] for f in lint(p)]
    print("\n".join(findings) if findings else "clean")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
