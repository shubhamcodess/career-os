---
name: job-aggregator
description: >
  Invoke when searching for live job listings. Triggers on: "find jobs for me",
  "search jobs at [company]", "what roles are open at [company]", "job search",
  "find [role] openings", or as part of `status` dashboard refresh.
  Fans out to Indeed, ZipRecruiter, and Dice simultaneously (all free MCPs, no paid
  keys required), deduplicates results, and ranks by match against master-experience.md.
  Saves results to data/market/job-feed.md and commits.
---

# Job Aggregator Skill

Searches all connected job MCPs in parallel, deduplicates, and ranks results
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

## Step 2 — Fan Out to All Active MCPs

Run ALL of these in the same turn. Don't wait for one before starting the next.

### Indeed MCP
```
Tool: search_jobs
Params: query=[role], location=[location], limit=20
Then: get_job_details for top 10 results
```

### ZipRecruiter MCP
```
Tool: search_jobs (authless)
Params: search=[role], location=[location], days_ago=7
```

### Dice MCP
```
Tool: search_jobs (authless, tech-focused)
Params: q=[role], location=[location]
Best for: engineering, data, product roles at tech companies
```

<!--
FUTURE: A fourth source (e.g. Crustdata, or another job/company data provider) can be
added here once a free or budget-friendly option is chosen. Crustdata was evaluated but
requires a paid plan, so it's excluded from the default setup. To add a new source:
1. Add its MCP config to mcp/.mcp.json
2. Add a fan-out block here following the pattern above
3. Update the dedupe and scoring steps below if it returns a different data shape
-->

## Step 3 — Deduplicate

After all sources return results, deduplicate by:
1. Exact match: same job title + same company = one listing
2. Fuzzy match: title similarity >80% + same company = likely duplicate, keep the one
   with more detail

## Step 4 — Score and Rank

For each unique listing, score it against `data/master-experience.md`:

| Signal | Weight |
|---|---|
| Role title match to target_roles | 30% |
| Required skills present in my stack | 30% |
| Company in target_companies list | 20% |
| Location match | 10% |
| Recency (posted <7 days = full score) | 10% |

Produce a score 0–100 for each listing.

## Step 5 — Output Format

Save to `data/market/job-feed.md`:

```markdown
# Live Job Feed
_Last updated: [datetime]_
_Sources: Indeed, ZipRecruiter, Dice (+ Naukri if enabled)_

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

## Step 6 — Surface Insights

After ranking, tell the user:
- How many total listings found across all sources
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
