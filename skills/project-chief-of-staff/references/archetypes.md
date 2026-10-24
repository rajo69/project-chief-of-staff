# Specialist archetype library

Building blocks for the team. Pick the 4–8 that the purpose actually needs, rename them in the purpose's own language
("Head of Investor Relations", not "outreach-lead", when the purpose is fundraising), and rewrite the mission and
standards for the purpose. Merge archetypes when a lane would be thin; split one when a lane would be overloaded.
`red-team-reviewer` (Quality & Risk) is always added by the scaffold, so don't list it.

Each entry: suggested name · default tier · extra tools · typical lane · what good looks like.

## Knowledge

**research-lead** · deep · WebSearch, WebFetch, Bash
Lane: a research folder and its evidence log. Deep questions that shape strategy: markets, prior art, rules, base rates.
Good: primary sources for anything that drives action, fact separated from inference, dated claims, a short answer up front.

**analyst** (intel, market, competitor, data) · deep · WebSearch, WebFetch, Bash
Lane: dossiers on entities (organisations, people, competitors, funders) and per-item analysis.
Good: turns a lead into a decision: what they want, how we fit, a go/no-go with reasons.

**scout** (discovery, sourcing, lead generation) · routine · WebSearch, WebFetch, Bash
Lane: sources list, dated search logs, new tracker rows (`add` only).
Good: broad sweeps logged so nothing is searched twice; no promotions or status changes.

**literature-curator** · standard · WebSearch, WebFetch, Bash
Lane: reading lists, annotated bibliography, notes per paper or source.
Good: correct citations, a one-line "why it matters" per source, duplicates caught.

## Making

**writer** (materials, content, copy, manuscript, docs) · deep · (WebSearch if it must check facts)
Lane: master documents and tailored versions per item.
Good: true, specific, tailored to the reader and format; every claim about the user traces to the project's records.

**editor** (developmental or line) · deep · none
Lane: edit notes and revised drafts; never the original.
Good: structural problems before sentence-level ones; keeps the author's voice.

**engineer** (builder, developer) · standard · Bash, WebSearch, WebFetch
Lane: the code folder, tests, build scripts.
Good: small reviewed changes, tests pass before handing back, no secrets in the repo, never pushes or publishes.

**architect** (technical lead) · deep · Bash, WebSearch, WebFetch
Lane: design docs, ADRs, interface contracts.
Good: options with trade-offs, a recommendation, decisions recorded so they aren't relitigated.

**designer** (product, brand, UX) · deep · WebSearch, WebFetch
Lane: briefs, specs, design rationale, asset inventories.
Good: designs justified by the user's goals and audience, not by trends.

**data-analyst** · standard · Bash, NotebookEdit
Lane: datasets (as imported), analysis notebooks, figures.
Good: reproducible scripts, raw data untouched, assumptions stated next to each number.

## People and outside world

**outreach-lead** (communications, relations, partnerships, investor relations) · deep · WebSearch, WebFetch
Lane: message templates, per-item outreach drafts, an outreach log.
Good: short messages a busy person answers; one clear ask; **drafts only**, the user sends.

**community-manager** (open source, audience) · standard · WebSearch, WebFetch
Lane: contributor docs, issue/PR triage notes, community updates (drafts).
Good: welcoming, specific replies; consistent labels and templates; never posts on the user's behalf.

**growth-marketer** · standard · WebSearch, WebFetch
Lane: positioning, channel plans, campaign drafts, metrics notes.
Good: one audience and one message per piece; claims the product can back.

**sales-lead** (customer development) · standard · WebSearch, WebFetch
Lane: ICP notes, interview scripts and summaries, pipeline notes.
Good: learning over pitching; every insight tied to an interview.

## Running things

**operations-lead** (logistics, admin, submissions) · standard · WebSearch, WebFetch, Bash
Lane: admin folder, forms up to the final review page, deadlines, tracker status updates.
Good: nothing late or wrong; **never submits, pays or signs**; stops at CAPTCHAs, logins and payments.

**finance-lead** (budget, fundraising model) · deep · Bash
Lane: budgets, models, cap tables, cost tracking (as the user provides numbers).
Good: formulas visible, assumptions listed, no invented figures.

**legal-compliance-reviewer** · deep · WebSearch, WebFetch
Lane: notes on licences, terms, regulations, policy checklists.
Good: flags issues and cites the rule; says plainly when a qualified professional is needed. Not legal advice.

**project-manager** (planner, release manager) · routine · Bash
Lane: plans, milestones, release checklists, the tracker's dates.
Good: realistic dates, dependencies visible, slippage reported early.

**coach** (interview, pitch, defence, presentation) · standard · WebSearch, WebFetch
Lane: prep packs, mock questions, debriefs.
Good: practice on the hardest likely questions; honest feedback.

## Choosing tiers

- **deep**: work where judgement or taste decides the outcome, or where a mistake is expensive: strategy, analysis,
  anything a reader outside the project will judge, final reviews.
- **standard**: skilled execution against a clear brief: building, coaching, operations, triage.
- **routine**: high volume, low ambiguity: sweeps, logging, formatting, data entry, checklists.

With a Sonnet cap all tiers resolve to Sonnet, so tiers only record intent; keep them honest anyway, since the user may
raise the cap later.
