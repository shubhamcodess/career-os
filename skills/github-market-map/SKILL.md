---
name: github-market-map
description: >
  Invoke to understand what people in a target role actually build, what their
  GitHub presence looks like, and what projects/skills help them get hired.
  Triggers on: "what do [role] people build", "github market map for [role]",
  "what projects should I have for [role]", "what's on a [role]'s GitHub",
  "market portrait for [role]".
  Uses GitHub public REST API only — zero ToS issues, fully public data.
  Saves to data/market/role-portraits/[role-slug].md
---

# GitHub Market Map Skill

Uses GitHub's public search API to build a data-driven portrait of what
people in your target role actually build, what skills they show, and
how they present themselves. Directly informs resume and portfolio decisions.

**Why this matters:** Job descriptions tell you what companies ask for.
GitHub tells you what people who actually get hired have done.
These are often different. This skill bridges the gap.

## Trigger Commands

| Command | Action |
|---|---|
| `github market map for [role]` | Full market portrait |
| `what projects should I have for [role]` | Project recommendations only |
| `what stack do [role] people use` | Tech stack analysis |
| `how should my GitHub look for [role]` | GitHub presence recommendations |
| `compare my GitHub for [role]` | Gap analysis vs. market portrait |

## Step 1 — Search GitHub Users

```
GET https://api.github.com/search/users
  ?q=[role-keyword]+location:[location]+followers:>10
  &sort=followers
  &per_page=30
Headers: Authorization: token [GITHUB_PAT from config]
```

Run 2–3 queries with different role keyword variations:
- "software engineer" → "backend engineer" → "SWE"
- "product manager" → "PM" → "product"
- "data scientist" → "ML engineer" → "machine learning"

Collect 50–80 unique profiles.

## Step 2 — Enrich Each Profile

For each user:
```
GET https://api.github.com/users/[username]
GET https://api.github.com/users/[username]/repos?sort=stars&per_page=10
```

Capture:
- Bio (self-description — what language do they use about themselves?)
- Company listed on GitHub
- Location
- Top repos: name, description, language, stars, topics[], fork status
- README existence on profile repo ([username]/[username])

**Read the profile README if it exists:**
```
GET https://api.github.com/repos/[username]/[username]/readme
```
Decode base64 content. Note: structure, what they highlight, how they describe themselves.

## Step 3 — Aggregate Market Data

After collecting all profiles, aggregate:

### Tech Stack Distribution
Count language occurrences across all repos, weighted by stars:
```
Python: 68% of profiles, avg 4.2 repos
JavaScript: 52%, avg 3.1 repos
Go: 23%, avg 1.8 repos
...
```

### Project Type Taxonomy
Cluster repo descriptions and topics into project types:
- "What do people in this role actually build for fun/portfolio?"
- e.g., for ML Engineers: "NLP tools (34%), CV projects (28%), data pipelines (22%), LLM wrappers (16%)"

### README Patterns
From profile READMEs that exist, identify:
- Do they list current role? Open to work?
- Do they list tech stack as badges or text?
- Do they link portfolio/blog?
- What do they lead with — projects, skills, or bio?
- Common sections: About / Tech Stack / Projects / Stats / Contact

### Repo Quality Signals
What separates top-starred repos from others:
- Do they have READMEs? (yes vs. no)
- Do they use topics/tags?
- Do they have demo links or live URLs?
- Do they have CI badges?

### Career Path Signals
From company fields and bio text:
- What companies appear most? (pedigree signals)
- What do they describe themselves as? (exact language used)
- What certifications/courses mentioned?

## Step 4 — Build Role Portrait

```markdown
# GitHub Market Portrait: [Role]
_Generated: [date] | Sample size: [N] profiles_

## Who Gets Hired
- Self-description patterns: "[X years of] [domain] [role] @ [company type]"
- Common pedigree companies: [list]
- Location distribution: [if relevant]

## Tech Stack Reality
(What they actually use, weighted by presence + stars)

| Skill | % of profiles | Avg repos | Notes |
|---|---|---|---|
| Python | 68% | 4.2 | Almost universal for [role] |
| React | 52% | 3.1 | Front-touch even for backend roles |
| ... | | | |

## What They Build
Top project types by frequency:
1. [type] — [N]% of portfolios — e.g., "LLM-powered tools"
2. [type] — [N]%
3. [type] — [N]%

## How They Present on GitHub

**Profile README structure (top pattern):**
- Header with name + role + current company
- 3–5 tech stack badges
- 2–3 pinned projects with descriptions
- GitHub stats widget (optional)
- Contact / social links

**Repo quality markers that correlate with strong profiles:**
- Detailed README with setup instructions ✅
- Live demo link or screenshot ✅
- Topics/tags applied ✅
- MIT or Apache license ✅
- Stars from others (not just forks) ✅

## Gap Analysis vs. Your Profile

_(Run after reading data/master-experience.md)_

| Market Has | You Have | Gap? |
|---|---|---|
| [skill] | ✅/❌ | Action needed |

## Recommendations

### Projects to Add to Your Portfolio
Based on what appears in the top 20% of profiles for this role:
1. **[Project type]** — "[Why: what it signals, what skills it shows]"
2. **[Project type]** — "[Why]"
3. **[Project type]** — "[Why]"

### Your GitHub README Should
- Lead with: [what to say first]
- Include: [specific sections]
- Avoid: [what looks dated or signals misfit]

### Skills to Surface More
- [Skill] — present in [N]% of market but underrepresented in your resume
```

## Step 4b — Supplement with Web Search (optional, high-value roles)

For any role where GitHub data alone feels thin (small sample, niche role, low follower
counts), supplement with built-in `WebSearch`:

- `[role] portfolio examples GitHub`
- `[role] interview what to build site:reddit.com OR site:dev.to`
- `"[role]" "projects" "hired" OR "got the job"`

Use `WebFetch` to read the full content of promising results. Synthesize findings
into the "What They Build" and "Recommendations" sections.

## Step 5 — Save and Commit

Save to `data/market/role-portraits/[role-slug].md`

```bash
git commit -m "data: github market map for [role] — [N] profiles analyzed"
```

## Integration Points

- **Resume tailoring** — reads role portrait to suggest project framing
- **Portfolio brief** — uses "Projects to Add" section to recommend what to build
- **Profile optimizer** — uses README patterns to optimize your GitHub profile
- **Comp intel** — company distribution gives salary benchmark signals

## GitHub API Notes

- Rate limit: 5,000 req/hr with PAT (set in `config/user.json` or `.env`)
- Search API: 30 results/page, max 1,000 results per query
- No auth needed for public data, but PAT avoids rate limiting
- README content is base64 encoded — always decode before reading
- `GET /repos/[user]/[user]` 404 = no profile README (don't error, just skip)
