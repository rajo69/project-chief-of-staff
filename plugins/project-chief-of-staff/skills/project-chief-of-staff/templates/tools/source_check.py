"""Flag unreliable or uncitable sources in research files (rules: 00_hub/source-policy.md).

    python tools/source_check.py <file> [<file> ...]
    python tools/source_check.py --hook      # PostToolUse hook: checks research files as they are written

Flags: AI chatbot or search-result links (never citable), low-reliability (T3) links not labelled [T3], and reports
of findings with no source links at all. Exit 0 = clean, 1 = findings. Hook mode never blocks; it feeds findings back
to the writer. Which folders hold research, and which files must cite sources, is set in 00_hub/project.config.json
("sources" -> "research", "needs_sources", "extra_low_domains").
"""
import json
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from style_lint import config, patterns_to_regex, rel, skipped  # noqa: E402

SKIP_NAMES = {"brief.md", "report.md", "review.md"}
URL = re.compile(r"https?://[^\s)>\]|\"']+", re.I)
NEVER = re.compile(r"(chatgpt\.com|chat\.openai\.com|gemini\.google\.com|bard\.google|perplexity\.ai|claude\.ai"
                   r"|copilot\.microsoft|poe\.com|you\.com/search|google\.[a-z.]+/search|bing\.com/search"
                   r"|duckduckgo\.com/\?|vertexaisearch)", re.I)
LOW_DOMAINS = ["reddit.com", "quora.com", "medium.com", "substack.com", "blogspot.", "wordpress.com", "tumblr.com",
               "twitter.com", "//x.com", "facebook.com", "instagram.com", "tiktok.com", "youtube.com", "youtu.be",
               "linkedin.com/pulse", "wikipedia.org", "fandom.com", "stackexchange.com", "stackoverflow.com"]
DATED_REPORT = re.compile(r"(^|/)\d{4}-\d{2}-\d{2}_[^/]+\.md$")  # dated reports of findings must cite something


def rules():
    s = config().get("sources", {})
    low = LOW_DOMAINS + list(s.get("extra_low_domains", []))
    return (patterns_to_regex(s.get("research")), patterns_to_regex(s.get("needs_sources")),
            re.compile("|".join(re.escape(d) for d in low), re.I))


def check(path, low=None, needs=None, label=None):
    if low is None:
        _, needs, low = rules()
    text = open(path, encoding="utf-8").read()
    r = rel(path)
    path = label or path
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        for url in URL.findall(line):
            if NEVER.search(url):
                out.append(f"{path}:{i}: not citable (AI answer or search result), cite the underlying page: {url}")
            elif low.search(url) and "[T3]" not in line:
                out.append(f"{path}:{i}: low-reliability source not labelled [T3]; confirm on a primary source: {url}")
    must_cite = DATED_REPORT.search(r) or (needs and needs.search(r))
    if must_cite and "/_template" not in "/" + r and not URL.search(text) and "{{" not in text:
        out.append(f"{path}: no source links; every fact needs a URL (00_hub/source-policy.md)")
    return out


def applies(path, research):
    r = rel(path)
    name = os.path.basename(r)
    return (bool(research and research.search(r)) and not skipped(r, SKIP_NAMES)
            and name.endswith((".md", ".txt", ".csv")))


def hook():
    try:
        path = json.load(sys.stdin).get("tool_input", {}).get("file_path", "")
    except (ValueError, AttributeError):
        return
    research, needs, low = rules()
    if not path or not os.path.isfile(path) or not applies(path, research):
        return
    findings = check(path, low, needs, rel(path))
    if findings:
        msg = ("Source check (00_hub/source-policy.md) flagged this research file. Replace or label these sources, "
               "or report the gap:\n" + "\n".join(findings[:25]))
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:] == ["--hook"]:
        return hook()
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    findings = [f for p in sys.argv[1:] for f in check(p)]
    print("\n".join(findings) if findings else "clean")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
