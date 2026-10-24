# Recommending skills and MCP servers after setup

Offer a short list (up to five items) of what clearly fits the purpose; none is fine. **Never install anything without the user's yes to that item.**

## Rules
- **Prefer first-party:** made by Anthropic, or by the vendor whose service it connects to. Mark anything else as
  "third-party" and suggest it only when there is no first-party option and the benefit is clear.
- **One line each:** what it does for *this* project, and the access it needs (read-only or read-write, which account).
- **Least access:** suggest read-only scopes where they exist. Never suggest anything that needs the user's passwords.
- **Check before you name an install command.** Install commands and URLs change; confirm the current one on the
  official page (WebFetch) before giving it. If you can't confirm it, name the item and the official page instead.
- **Already connected?** If the session already has a connector for that service, say so instead of recommending an install.
- **On a yes:** install at project scope where possible (`claude mcp add --scope project ...` writes `.mcp.json`, which
  the structure check allows at the root), record it in `00_hub/decisions.md`, add a line to the activity log, and note
  that MCP tools are not in the specialists' tool lists: add `mcp__<server>__*` to an agent's `tools` only if that agent needs it.

## Candidates (verify before recommending)

| Need | Candidate | Maker | Access it needs |
|---|---|---|---|
| Word, Excel, PowerPoint, PDF files | Anthropic document skills (`anthropics/skills` repository) | Anthropic | Local files only |
| Building or improving skills | skill-creator (same repository) | Anthropic | Local files only |
| Repositories, issues, pull requests | GitHub MCP server (`github/github-mcp-server`) | GitHub | A GitHub token; read-only scope to start |
| Browsing sites that need a real browser | Playwright CLI (`@playwright/cli`, offered at setup) or Playwright MCP (`microsoft/playwright-mcp`) | Microsoft | Local browser; logins stay in the project's profile |
| Notes and wikis | Notion MCP (hosted) | Notion | OAuth to the chosen workspace pages |
| Issue tracking | Linear MCP (hosted) or Atlassian MCP (Jira, Confluence) | Linear / Atlassian | OAuth to the workspace |
| Design files | Figma MCP server | Figma | Figma account; read access to files |
| Payments, billing data | Stripe MCP | Stripe | Restricted API key; read-only first |
| Error monitoring | Sentry MCP | Sentry | OAuth to the organisation |
| Deploying web apps | Vercel MCP, Cloudflare MCP, Supabase MCP | Vercel / Cloudflare / Supabase | OAuth to the account or project |
| Models, datasets, papers | Hugging Face MCP | Hugging Face | Hugging Face account; read access |
| Email, calendar, drive | The Gmail, Google Calendar and Google Drive connectors in Claude | Anthropic | OAuth to the Google account; read-only where offered |

Sensible defaults by purpose:
- **Writing-heavy** (book, grants, applications, fundraising): document skills; Google Drive connector if the user keeps drafts there.
- **Software** (startup, open source): GitHub MCP; the host or monitoring MCP the user already uses.
- **Research**: Hugging Face MCP for ML work; document skills for PDFs; Playwright for sites WebFetch can't read.
- **Outreach-heavy**: Gmail and Calendar connectors for *reading* context; messages are still drafted in the project
  and sent by the user.
