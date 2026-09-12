---
name: job-aggregator
description: >
  Invoke when searching for live job listings. Triggers on: "find jobs for me",
  "search jobs at [company]", "what roles are open at [company]", "job search",
  "find [role] openings", or as part of `status` dashboard refresh.
  Fans out to ATS Direct (Greenhouse/Lever), Naukri, and job board MCPs simultaneously,
  deduplicates results, and ranks by match against master-experience.md.
  Saves results to data/market/job-feed.md and commits.
---

# Job Aggregator Skill

Searches all connected job sources in parallel, deduplicates, and ranks results
against your profile. Single source of live market intelligence.

## Trigger Commands

| Command | Action |
|---|---|
| `find jobs` | Broad search based on target role in config/user.json |
| `find jobs at [company]` | Filter to specific company across all sources |
| `find [role] jobs` | Search for specific role title |
| `refresh job feed` | Re-run last search, surface new listings only |
| `rank my job feed` | Re-score existing feed against latest resume |

## Step 1 — Load Search Parameters

Read `config/user.json`:
- `target_roles[]` — list of role titles to search
- `target_companies[]` — priority companies (rank these higher)
- `target_locations[]` — locations or "remote"
- `experience_years` — for seniority filtering
- `domain_keywords[]` — domain terms to include in searches
- `integrations.naukri_enabled` — whether to include Naukri
- `integrations.naukri_pages_per_search` — how many pages to scrape

## Step 2 — Fan Out to All Sources

Run ALL of these simultaneously. Don't wait for one before starting the next.

---

### Source A: ATS Direct (Greenhouse + Lever)

**Most reliable source** — pure JSON APIs, no scraping, no bot detection.
Companies with internal ATS (Google, Amazon, etc.) are automatically skipped with
a note pointing to their careers page.

**For `find jobs` (broad search across config companies):**
```bash
python3 scripts/ats-fetcher.py --from-config --role "[first target_role]"
```

**For `find jobs at [company]` (single company):**
```bash
python3 scripts/ats-fetcher.py --company "[company]" --role "[first target_role]"
```

**For multiple specific companies:**
```bash
python3 scripts/ats-fetcher.py --companies Stripe Anthropic Groww --role "[role]"
```

Known Greenhouse companies (from `KNOWN_SLUGS` in the script): Groww, Postman, Stripe,
Databricks, Cloudflare, Coinbase, Reddit, Discord, Airbnb, Figma, Anthropic, OpenAI,
HashiCorp.

Known Lever companies: Meesho, Cred, Freshworks, Netflix, Lyft, Vercel.

Companies NOT on Greenhouse/Lever (internal ATS): Razorpay, PhonePe, Zepto,
BrowserStack, Flipkart, Walmart, IKEA, Google, Microsoft, Amazon, Meta, Apple, Nvidia,
Visa, Lowes, Target. The script will skip these and print the correct careers URL.

To add a new company: look up its Greenhouse board at
`boards-api.greenhouse.io/v1/boards/{slug}/jobs` or Lever at
`api.lever.co/v0/postings/{slug}`, then add to `KNOWN_SLUGS` in `scripts/ats-fetcher.py`.

---

### Source B: Naukri (if `naukri_enabled: true` in config)

Best for: Indian market listings, companies not on international job boards,
mid-market product companies.

```bash
python3 scripts/naukri-scraper.py \
  --role "[first target_role]" \
  --location "[city from target_locations]" \
  --pages [naukri_pages_per_search]
```

For `find jobs at [company]`: Naukri does not support single-company filtering
via URL. Run normally and post-filter results by `company` field in the JSON.

If Naukri is disabled or returns 0 results, continue without it — ATS + MCPs
are sufficient. See `skills/naukri-scraper/SKILL.md` for troubleshooting.

---

### Source C: Job Board MCPs

Run in parallel with Sources A and B.

**Indeed MCP:**
```
Tool: search_jobs
Params: query=[role], location=[location], limit=20
Then: get_job_details for top 10 results
```

**ZipRecruiter MCP:**
```
Tool: search_jobs (authless)
Params: search=[role], location=[location], days_ago=7
```

**Dice MCP:**
```
Tool: search_jobs (authless, tech-focused)
Params: q=[role], location=[location]
Best for: engineering, data, product roles at tech companies
```

If an MCP connector is unavailable or returns an error, skip it and note in the output.
MCP sources are best for roles not at the specific companies in `target_companies[]`.

**Web search fallback (when all MCPs are down):** This is curated job hunting — run deep
research, not a single query. Use multiple `WebSearch` queries to cover the search space,
then `WebFetch`/Firecrawl each promising result URL to extract the full JD:

Queries to run (adapt role/location from config):
- `site:greenhouse.io "[role]" [location]`
- `site:lever.co "[role]" [location]`
- `"[company]" "[role]" hiring 2026 site:linkedin.com/jobs`
- `[role] jobs [location] -site:indeed.com` (surface direct company pages)
- `"[target company]" careers "[role]"` (for each company in target_companies[])

Fetch the top 3–5 results per query, extract JD text, deduplicate by company+title, then
rank as usual. Note in output that results came from web search and coverage may be incomplete.

---

## Step 3 — Merge All Results

Collect JSON arrays from ATS fetcher (stdout), Naukri scraper (stdout), and MCP results.
All three sources use the same field shape:
```json
{
  "title": "...",
  "company": "...",
  "experience": "...",
  "location": "...",
  "salary": "...",
  "description": "...",
  "posted": "...",
  "tags": [],
  "url": "...",
  "source": "greenhouse|lever|naukri|indeed|ziprecruiter|dice"
}
```

## Step 4 — Deduplicate

After all sources return results, deduplicate by:
1. Exact match: same job title + same company = one listing
2. Fuzzy match: title similarity >80% + same company = likely duplicate, keep the one
   with more detail (prefer ATS source over board MCPs — more accurate description)

## Step 5 — Score and Rank

For each unique listing, score it against `data/master-experience.md`:

| Signal | Weight |
|---|---|
| Role title match to target_roles | 30% |
| Required skills present in my stack | 30% |
| Company in target_companies list | 20% |
| Location match | 10% |
| Recency (posted <7 days = full score) | 10% |

Produce a score 0–100 for each listing.

## Step 6 — Output Format

Save to `data/market/job-feed.md`:

```markdown
# Live Job Feed
_Last updated: [datetime]_
_Sources: ATS Direct ([N] companies), Naukri ([N] pages), Indeed, ZipRecruiter, Dice_

## 🔥 Strong Matches (Score 75+)
### [Company] — [Role Title]
- Score: [N]/100
- Location: [location] | Posted: [date] | Source: [source]
- Match reasons: [why this scored high]
- Skills gap: [anything in JD not in my profile]
- Apply link: [url]
- JD snippet: [key requirements, 2-3 lines]

---

## ✅ Good Matches (Score 50–74)
[same format]

## 📋 Worth Watching (Score 30–49)
[condensed format]
```

Git commit after save:
```bash
git commit -m "data: refreshed job feed — [N] listings, [N] strong matches"
```

## Step 7 — Surface Insights

After ranking, tell the user:
- How many total listings found per source (ATS: N, Naukri: N, MCPs: N)
- Which target companies had Greenhouse/Lever boards vs. internal ATS
- How many strong matches
- Any new companies appearing that aren't in their target list
- Salary ranges seen (if available) → suggest adding to comp-intel.md
- Any role titles appearing frequently that differ from their target titles
  (market may use different terminology)

## Data Storage

```
data/market/
├── job-feed.md          ← Current ranked feed (overwritten on refresh)
├── job-feed-archive/    ← Previous feeds (for tracking market changes)
│   └── job-feed-[date].md
└── company-intel/       ← Company research snapshots
    └── [company-slug].md
```
