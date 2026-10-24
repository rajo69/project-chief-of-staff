# Purpose patterns

Starting shapes for common purposes. They are sketches, not templates: think about what *this* user's purpose needs,
then borrow. For a purpose that isn't here, work from first principles with the questions at the end.

## Startup (product company, early stage)
- **Folders:** 01_strategy · 02_research (market, competitors, customers) · 03_product (specs, roadmap notes) ·
  04_build (code or no-code assets) · 05_go-to-market · 06_fundraising · 07_customers (one folder per key account or
  interview series) · 08_finance-legal · 09_admin
- **Tracker:** `pipeline` of *leads/accounts* or `roadmap` of *features*; pick the one the user named as the bottleneck.
  Types e.g. `CUST` customer, `PART` partner, `INV` investor. Statuses: lead → contacted → meeting → trial → won; lost, parked.
- **Team:** research-lead, analyst (competitors), product designer, engineer, growth-marketer, sales-lead, finance-lead.

## Seed fundraising
- **Folders:** 01_company (facts, metrics as provided by the user) · 02_narrative (deck, memo, one-pager) ·
  03_research (investor landscape, comparable rounds) · 04_investors (one folder per active investor) · 05_outreach ·
  06_data-room · 07_finance (model, cap table, use of funds) · 08_legal (term sheets, notes) · 09_admin
- **Tracker:** `investors`; types `VC`, `ANG` angel, `ACC` accelerator, `CVC`; statuses: target → researched → intro-requested
  → first-meeting → partner-meeting → diligence → term-sheet → closed; passed, parked. Columns: firm, partner, stage_focus,
  cheque_size, warm_intro (enum yes/no), next_meeting (date).
- **Team:** analyst (investor intel), writer (narrative and deck copy), outreach-lead (intros, follow-ups; drafts only),
  finance-lead, operations-lead (data room, scheduling).

## Open source project
- **Folders:** 01_vision (scope, principles, governance) · 02_research (prior art, ecosystem) · 03_design (ADRs, specs) ·
  04_code (the repository working tree, or a pointer if it lives elsewhere) · 05_docs · 06_community (contributor guides,
  triage notes, announcements as drafts) · 07_releases (one folder per release) · 08_ops (CI, packaging, security policy)
- **Tracker:** `roadmap` of features and issues; types `FEAT`, `BUG`, `DOC`, `INFRA`; statuses: idea → accepted → in-progress
  → review → merged → released; rejected, duplicate. Columns: area, issue_url (url), target_release.
- **Team:** architect, engineer, docs writer, community-manager, project-manager (release manager).
- **Extras:** `git init` is usually wanted. Recommend the official GitHub MCP server later, with a yes.

## PhD application or research role search
See `example-plan-phd.json` for a full worked plan: profile, research, discovery, entities, materials, outreach,
one folder per opportunity, interviews, admin; a `pipeline` of opportunities; research-lead, scout, analyst,
outreach-lead, writer, operations-lead, interview coach.

## Doing a PhD or a research project
- **Folders:** 01_proposal · 02_literature · 03_methods · 04_data (raw as imported; processed) · 05_analysis · 06_writing
  (papers, thesis chapters) · 07_presentations · 08_supervision (meeting notes, decisions) · 09_admin
- **Tracker:** `papers` (own outputs) or `experiments`; types `PAPER`, `CHAP`, `EXP`, `TALK`; statuses: idea → planned →
  running → drafting → internal-review → submitted → revision → accepted; dropped, rejected.
- **Team:** literature-curator, research-lead, data-analyst, writer, editor, coach (talks, defence).

## Book (fiction or non-fiction)
- **Folders:** 01_concept (premise, audience, comparable titles) · 02_research · 03_outline · 04_manuscript (one folder per
  chapter) · 05_revision · 06_publishing (agents, publishers or self-publishing) · 07_marketing · 09_admin
- **Tracker:** `chapters`; types `CH`, `PART`, `FRONT`, `BACK`; statuses: outlined → drafting → drafted → revising →
  edited → final; cut. Columns: pov, word_count, target_words.
- **Team:** research-lead, writer, editor (developmental), editor (line), outreach-lead (queries; drafts only), growth-marketer.

## Job search (industry)
- **Folders:** 01_profile · 02_research (market, salaries) · 03_discovery · 04_companies · 05_materials · 06_outreach ·
  07_applications (one folder per application) · 08_interviews · 09_admin
- **Tracker:** `pipeline` of applications; types `FT`, `CON` contract, `INT`; statuses like the PhD example.
- **Team:** scout, analyst, writer, outreach-lead, operations-lead, coach.

## Grant or funding application (non-profit or research)
- **Folders:** 01_organisation · 02_research (funders, past awards) · 03_programme (the work to be funded) · 04_funders ·
  05_proposals (one folder per call) · 06_budget · 07_reporting · 09_admin
- **Tracker:** `calls`; statuses: spotted → eligible → drafting → internal-review → submitted → awarded; declined, missed.
- **Team:** scout, analyst, writer, finance-lead, operations-lead.

## Learning a subject or preparing for an exam
- **Folders:** 01_goals · 02_syllabus · 03_notes · 04_practice · 05_projects · 06_resources · 09_admin
- **Tracker:** `topics`; statuses: not-started → learning → practising → solid; dropped. Columns: exam_weight, confidence (enum 1-5).
- **Team:** research-lead (resources), coach (tutor), project-manager (study plan), writer (summaries).

## Event, campaign, client engagement, content channel …
Use the questions below.

## First principles: questions that shape any project
1. **What is the unit of work** that gets tracked one row at a time? That is the tracker's item. Its lifecycle is the
   status list; what you need to sort or filter by are the extra columns.
2. **Does each item deserve its own folder** (it accumulates documents) or only a row? That decides `folder_dir`.
3. **What is reusable across items** (dossiers, master documents, templates)? Each kind gets a numbered folder.
4. **Which judgements are hard, and which work is bulk?** Hard judgement → deep-tier agents; bulk → routine.
5. **What leaves the project** (messages, submissions, releases, posts)? Each kind needs a drafting lane, the reviewer,
   and the user's approval.
6. **What does the user bring** (documents, data, a codebase)? It gets a folder the user fills themselves.
7. **Which folders hold outgoing text, and which hold findings?** The first go in `writing.outgoing`, the second in
   `sources.research`. Then ask what counts as a primary source in this field: that is T1.
