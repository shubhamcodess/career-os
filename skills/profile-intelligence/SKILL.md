---
name: profile-intelligence
description: >
  Invoke when researching who works at a target company, understanding what skills
  people in a target role actually have, or getting intel before applying.
  Triggers on: "who works at [company]", "research [company] team",
  "what skills do [role] at [company] have", "profile intel for [company]",
  "prep intel for [company]", or as part of `make resume for` pipeline.
  Currently runs on free sources only: GitHub public API + web search + company
  engineering blogs/pages. No paid API keys required. Saves to
  data/market/company-intel/[company].md
---

# Profile Intelligence Skill

Maps signals about the people and culture at your target company using only free,
public sources. Feeds directly into resume tailoring and outreach.

**Current data sources (all free):**
- **GitHub REST API** — public profile data, org member lists, repo activity
- **Built-in `WebSearch`** — always available; use for discovery queries: company blog,
  team pages, engineering culture writeups, Glassdoor/AmbitionBox, recent funding/news
- **Built-in `WebFetch`** — always available; use to read full content of URLs found via WebSearch
- **Firecrawl MCP** (if key set) — use alongside WebFetch for high-value targets;
  gives richer/cleaner extraction on JS-rendered pages (company career portals, LinkedIn
  public profiles, Medium/Substack engineering blogs) where WebFetch returns thin content

**What's intentionally NOT included yet:**
A dedicated LinkedIn-layer data source (e.g. Crustdata) would give direct people-search
by company + title with skills and career history. That requires a paid plan, so it's
excluded from this default setup. See "Future Upgrade" section below for how to add
one later without changing anything else in this pipeline.

**What you CANNOT do and why:**
- Direct LinkedIn scraping — violates ToS, accounts get banned. Never attempted.
- LinkedIn's official API doesn't expose other people's full profiles for this use case.

## Trigger Commands

| Command | Action |
|---|---|
| `profile intel for [company]` | Full company signal report |
| `who works at [company] as [role]` | GitHub org member search filtered by role signals |
| `research [company] hiring team` | Best-effort via web search + GitHub org |
| `what does a [role] at [company] look like` | Synthesized portrait from available data |

## Step 1 — GitHub Organization Search

Most product companies have a GitHub org, even if not all employees are visibly linked to it.

```
GET https://api.github.com/orgs/[company-slug]/members?per_page=50
GET https://api.github.com/orgs/[company-slug]/repos?sort=updated&per_page=20
```

If the org isn't found under the obvious slug, try variants (company name without spaces,
common abbreviations) or search:
```
GET https://api.github.com/search/users?q=[company]+in:company
```
This finds individuals who list the company in their GitHub bio/company field even if
there's no official org account.

For each member/matching user found:
```
GET https://api.github.com/users/[username]
GET https://api.github.com/users/[username]/repos?sort=stars&per_page=10
```

Capture: name, bio, listed title (if in bio), primary languages, top repos, activity level.

## Step 2 — Company Repo Analysis

From the org's public repos (if any):
- What languages/frameworks dominate their actual codebase
- How they structure READMEs and CONTRIBUTING docs (signals engineering culture)
- Recent commit activity (is the org active, what's being built lately)
- Open issues/PRs (occasionally reveals team structure via reviewers/assignees)

## Step 3 — Web Search Layer

Run targeted searches using built-in `WebSearch` for discovery, then read full content
using **`WebFetch`** (fast, clean HTML pages) and/or **Firecrawl MCP** (JS-rendered pages,
Medium/Substack/corporate blogs that render client-side). Use both where applicable:

- `"[company]" engineering blog`
- `"[company]" "[role]" hiring OR "we're looking for"`
- `"[company]" interview process [role]`
- `"[company]" tech stack`
- `site:glassdoor.com OR site:ambitionbox.com "[company]" reviews`

For each promising URL: try `WebFetch` for standard HTML pages; use Firecrawl for pages
that return thin or empty content via WebFetch (JS-heavy blogs, dynamic career portals).

Extract: culture signals, interview process notes, tech stack mentions, team structure
hints, recent news (funding, launches, layoffs — all relevant context).

## Step 4 — Company Careers Page

Fetch the careers URL (if known or found via Step 3 search). Use both where applicable:
- **`WebFetch`** — fast for standard HTML careers pages
- **Firecrawl MCP** — use for JS-rendered portals (Workday, Greenhouse-embedded, Lever-embedded)
  that return incomplete content via WebFetch

Extract: currently open roles (cross-reference with job-aggregator results), stated
values/culture language, team photos/bios if present, benefits signals.

## Step 5 — Synthesize Portrait

Combine everything into a portrait, being explicit about confidence level per section:

```markdown
## Company Signal Report: [Role] at [Company]
_Confidence: GitHub data is high-confidence (verified public data).
Web search / culture signals are lower-confidence (inferred from public writing)._

### Engineering Culture (from GitHub + blog signals)
- Primary tech stack: [languages/frameworks seen in org repos]
- Documentation style: [how they write READMEs — signals engineering maturity]
- Open source posture: [active contributor / minimal / none]

### What Their GitHub-Visible Employees Look Like
- Sample size: [N] profiles found
- Language distribution: [Python 60%, Go 20%, ...]
- Common project types: [what they build in public/personal repos]
- Caveat: this only reflects employees visible on GitHub — likely skews technical/senior

### Culture & Hiring Signals (from web search)
- [Bullet points from blog posts, review sites, careers page]
- Source confidence: [note if this is from official company content vs. third-party reviews]

### What This Means for Your Resume
- Lead with: [skills to emphasize based on observed stack]
- Framing: [how to position experience for this audience]
- Gaps to address honestly: [anything the data suggests you're missing]

### Data Gaps
- No direct people-search by role/title available (would require a LinkedIn-layer
  data source — see Future Upgrade below)
- Portrait is directional, not a verified roster of employees
```

## Step 6 — Save and Commit

Save to `data/market/company-intel/[company-slug].md`

```bash
git commit -m "data: profile intel for [company] (GitHub + web sources) — [N] profiles found"
```

## Integration with Resume Pipeline

When `make resume for [Company/Role]` is run:
1. Check if `data/market/company-intel/[company-slug].md` exists and is <14 days old
2. If yes — read it and use available signals to inform tailoring
3. If no — offer to run this skill first (it's optional, not blocking — resume can still
   be tailored from the JD alone if the user wants to skip this)

---

## Future Upgrade — Adding a LinkedIn-Layer Data Source

When budget allows, or a free/cheaper alternative to Crustdata is found, wire it in here
without touching any other skill:

1. Add the provider's MCP config to `mcp/.mcp.json`, or an API client script
2. Add a "Step 0 — [Provider] People Search" section above, returning: name, title,
   LinkedIn URL, skills, employment history, education
3. Update Step 5's synthesis to merge that data in and raise confidence level
4. Add a "Key People to Know" table (recruiters/hiring managers) — this was possible
   with Crustdata's people search and directly fed `draft outreach for [company]`;
   until a replacement is added, outreach drafting relies on whoever the user finds
   manually and pastes in

Candidates to evaluate when ready: Crustdata (paid), PeopleDataLabs (has free tier,
smaller data), or manual LinkedIn Sales Navigator exports pasted in by the user.
