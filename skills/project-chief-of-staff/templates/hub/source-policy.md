# Source policy: research only from reliable sources

Decisions are only as good as what they rest on. This applies to every agent that searches, reads or cites anything:
{{SCOPE}}.

- **As files are written:** a PostToolUse hook runs `tools/source_check.py` on research files ({{RESEARCH}}).
- **At review:** `red-team-reviewer` runs `{{PY}} tools/source_check.py <file>` on research deliverables and checks sourcing.

## Tiers (label each citation `[T1]`, `[T2]` or `[T3]` next to the URL)

| Tier | What | Use it for |
|---|---|---|
| **T1, primary** | {{T1}} | Anything that drives an action or decision: dates, rules, requirements, numbers, names and titles |
| **T2, reputable secondary** | {{T2}} | Finding leads and context. **Confirm on T1 before acting on any fact** |
| **T3, low reliability** | {{T3}} | Hypotheses and anecdote only, labelled as such. Never the sole basis for a decision, a recorded fact or anything sent out |
| **Never** | AI chatbot answers or AI search summaries, search-result snippets, unattributed screenshots, anything that can't be traced to who said it | Not citable. Open and cite the underlying page instead |

## Rules
1. **Open the page.** Cite what the page says, never a snippet or a summary of it. Record the URL and the date you checked it.
2. **Decision-critical facts need T1.** If only T2 or T3 exists, write `UNVERIFIED` and report the gap; don't fill it with a guess.
3. **Currency.** Note the date, version or cycle a fact applies to. Treat anything older than the current one as stale until it's re-checked.
4. **Conflicts.** The official source wins. Record the conflict and both URLs in the notes.
5. **Separate fact from inference** in writing. Numbers carry their source and their denominator.
6. **Capture key pages.** Save a raw copy of any page a decision rests on ({{CAPTURE}}).
7. **Track reliability.** When a source proves wrong or reliable, the agent notes it in its report's Lessons; the CoS keeps a
   running list below.

## Known sources
_CoS-maintained, from agents' reports. One line each: domain, tier, why._
