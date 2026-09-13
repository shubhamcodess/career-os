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

### Source A: ATS Direct

**Most reliable source** — pure JSON APIs, no scraping, no bot detection. Covers
Greenhouse, Lever, Ashby, Recruitee, Workable, SmartRecruiters and Workday.

**No company is hardcoded.** Every company → platform/slug mapping is read from
`config/companies.json`. If that file doesn't exist, the fetcher will tell you to
build it — do that first:

```bash
python3 scripts/resolve-ats.py --from-config
```

**For `find jobs` (every company in the registry):**
```bash
python3 scripts/ats-fetcher.py --all --role "[first target_role]"
```

**For `find jobs at [company]` (single company):**
```bash
python3 scripts/ats-fetcher.py --company "[company]" --role "[first target_role]"
```

If that company isn't in the registry the fetcher says so — resolve it, then retry:
```bash
python3 scripts/resolve-ats.py --company "[company]"
```

**Companies with no reachable board.** Entries with status `empty` or `unresolved`
have no public ATS *that we know of yet*. The fetcher prints their `careers_url`
instead of returning jobs. Never report these as "no openings" — they are almost
always hiring. Run them through the escalation ladder in **Source D** below.

**Registry hygiene.** ATS boards move. If a company that used to return jobs suddenly
returns none, re-verify before assuming the market went quiet:
```bash
python3 scripts/resolve-ats.py --refresh
```

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

**For `find jobs at [company]`** — target it directly; the scraper verifies every
result against the company field, so fuzzy keyword matches from other employers
are dropped:
```bash
python3 scripts/naukri-scraper.py --company "[company]" --role "[role]"
```

**Always also run the unreachable sweep.** This is what makes Naukri worth having —
it covers every company the ATS layer cannot reach:
```bash
python3 scripts/naukri-scraper.py --from-unreachable --role "[first target_role]"
```

If Naukri is disabled, continue without it. If it is enabled but returns 0 across
every company, that is a selector break, not an empty market — say so rather than
reporting no results. See `skills/naukri-scraper/SKILL.md` for troubleshooting.

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

**`mcp/.mcp.json` is not how these get connected.** All three are first-party connectors
in the Claude directory. Declaring a URL in `mcp/.mcp.json` does nothing in the desktop
app — the user must install them under **Settings → Connectors**:

| Connector | Tools | Auth |
|---|---|---|
| Dice | `search_jobs`, `get_job_details`, `get_company` | None — works immediately |
| Indeed | `search_jobs`, `get_job_details` | Required |
| ZipRecruiter | `search_jobs` | Required; aggressively rate-limited without it |

Before relying on any of them, check whether their tools exist in the session. If they
are absent, say so plainly and fall through to Source D. Never let a missing connector
read as "the market is quiet".

Dice is tech-focused and the best of the three for engineering roles. Its `search_jobs`
takes `keyword`, `location`, `radius`, `jobs_per_page`, `page_number`, `sort`,
`posted_date`, `workplace_types`, `employment_types`. Use `get_job_details` on the top
results to pull full JD text — the search response carries only a summary.

---

### Source D: Unreachable Companies — Escalation Ladder

For every company with status `empty` / `unresolved`, work down this ladder and stop at
the first rung that produces jobs. The order is by data quality: structured beats
scraped, scraped beats inferred.

**Rung 1 — Find the real ATS board and pin it. Do this first; it is permanent.**

Auto-discovery only tries variations of the company name, so it misses boards registered
under a legal entity. Razorpay's Greenhouse slug is `razorpaysoftwareprivatelimited` —
no name-based guess would ever produce that. Web search finds it in one query:

```
WebSearch: "[company]" site:boards.greenhouse.io OR site:jobs.lever.co OR site:jobs.ashbyhq.com
WebSearch: "[company]" careers "powered by" greenhouse OR lever OR workday OR eightfold
```

Then pin the URL you found — platform and slug are read straight off it:
```bash
python3 scripts/resolve-ats.py --from-url "Razorpay" "https://boards.greenhouse.io/razorpaysoftwareprivatelimited"
```

This is the highest-value action in the whole skill. One search converts a company from
permanently invisible to permanently fetchable. **Always try Rung 1 before scraping.**

Also worth fetching the careers page itself and looking at what it loads — the platform
is usually obvious from the HTML:

| Signal in page source | Platform | Pin with |
|---|---|---|
| `boards.greenhouse.io`, `grnhse` | greenhouse | `--from-url` |
| `jobs.lever.co`, `lever-client` | lever | `--from-url` |
| `myworkdayjobs.com` | workday | `--from-url` |
| `eightfold-font`, `/api/apply/v2/` | eightfold | `--from-url` |
| `ashbyhq`, `smartrecruiters`, `recruitee`, `workable` | as named | `--from-url` |
| `/api/pcsx/search` | pcsx (Microsoft-style Eightfold) | `--from-url` |
| `icims.com`, `phenompeople`, `successfactors` | not supported yet | careers_url + Rung 3 |

**Mega-cap careers portals.** Three of the biggest employers need bespoke adapters
because they run their own portals rather than a third-party ATS:

| Company | Platform | Pin with |
|---|---|---|
| Google | `google` — server-rendered HTML scrape, slug is `"query\|location"` | `--set "Google" google "software engineer\|India"` |
| Microsoft | `pcsx` — real JSON API | `--set "Microsoft" pcsx "apply.careers.microsoft.com\|microsoft.com"` |
| Amazon | `amazon` — public search JSON, slug is a query hint | `--set "Amazon" amazon "software engineer"` |

The `google` adapter is an HTML scraper, not a feed. It will break when Google reskins
the page — the symptom is a sudden drop to zero jobs, not an error. Re-check the
selectors rather than assuming Google stopped hiring. Because its slug embeds the
query and location, it returns a *pre-filtered* set: re-pin with a different slug to
search different roles or geographies.

**Meta is deliberately not supported.** `metacareers.com` serves jobs only through
POST GraphQL calls keyed by rotating internal `doc_id` values — a private API with no
stable contract. Route Meta through Rung 2/3 and say so honestly rather than shipping
an adapter that breaks weekly.

**Rung 2 — Naukri, for anything hiring in India.**

The strongest fallback for a Bangalore-based search. It covers exactly the companies
that are hardest to reach by API — Flipkart, PhonePe, Walmart India, Visa India,
Qualcomm India, SAP Labs, Adobe India, IBM. Requires `naukri_enabled: true` in
`config/user.json`.

**The one command that closes the coverage gap:**
```bash
python3 scripts/naukri-scraper.py --from-unreachable --role "[role]"
```

That reads `config/companies.json`, takes every company with no fetchable ATS board, and
runs a company-targeted search for each. Location defaults to `target_locations[0]`.
Run it after every `resolve-ats.py` pass.

Other modes:
```bash
python3 scripts/naukri-scraper.py --role "Software Engineer" --location Bangalore --pages 2
python3 scripts/naukri-scraper.py --company "IBM" --role "Software Engineer"
python3 scripts/naukri-scraper.py --companies IBM Flipkart PhonePe --role "Software Engineer"
```

**How company targeting works.** Naukri has no company filter parameter, so the company
name goes into the keyword slug and every result is then verified against the `company`
field. Fuzzy keyword matches belonging to a different employer are dropped — a search for
IBM returns desktop-support roles at unrelated vendors, and those must not reach your
feed. The scraper prints `matched / returned` per company so the filter is visible.

**Search aliases.** Some registry names mean nothing to a job board. `ISL` is IBM
Software Labs; searching Naukri for "ISL" returns noise. Give those entries an alias once:

```bash
python3 scripts/resolve-ats.py --set-alias "ISL" "IBM ISL"
```

`--from-unreachable` uses `search_as` when set, and the registry name otherwise.

Output is the same JSON shape as the ATS fetcher with `"source": "naukri"`, already
deduplicated, so it merges straight into Step 3 with no special handling.

Naukri is a scraper, not a feed: it needs system Chrome, it self-throttles 4–8s between
company searches, and Naukri changes its DOM periodically. If it returns zero across
every company, suspect a selector break before concluding nobody is hiring.

**Rung 3 — Web search the careers page directly.**

When there is no ATS and no Naukri coverage. Run several queries; one is not enough:

```
WebSearch: "[company]" careers "[role]" [location]
WebSearch: site:[careers domain] "[role]"
WebSearch: "[company]" "[role]" jobs 2026 -site:indeed.com
```

Then `WebFetch` the careers URL from `config/companies.json` and read the listings off
the page. If it returns thin content because the page renders client-side, use Firecrawl
if it is connected. If Firecrawl is not connected, say so rather than pretending the
company has no openings.

Mark anything from this rung `"source": "websearch"` and flag lower confidence — you are
reading a rendered page, not a structured feed, so titles and locations may be imprecise
and there is no reliable posted-date.

**Rung 4 — Report the gap honestly.**

If nothing works, say exactly that, per company, with the careers URL so the user can
look themselves:

```
No API coverage: Google, Apple, Meta — internal ATS, no public feed.
  Google → https://careers.google.com
  Apple  → https://jobs.apple.com
  Meta   → https://metacareers.com
Check these manually, or send me a board URL and I'll pin it permanently.
```

Never fabricate listings, and never let silence imply there are no jobs.

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
  "source": "greenhouse|lever|ashby|workable|smartrecruiters|recruitee|workday|naukri|indeed|ziprecruiter|dice|websearch"
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

## Step 6b — Notify via Slack (if enabled)

If `integrations.slack.enabled` is true in `config/user.json` and `job_feed` is in
`notify_on`, post the digest after `job-feed.md` is written and committed.
Read `skills/slack-bridge/SKILL.md` for format. Post the summary as a message and
the full ranked feed as a Canvas — never dump the whole feed into chat.

Slack failing must never fail the job search. Write the file, commit, then try Slack.

## Step 7 — Surface Insights

After ranking, tell the user:
- How many total listings found per source (ATS: N, Naukri: N, MCPs: N)
- Which target companies returned jobs vs. which have no reachable board
  (from `config/companies.json` — name them, and give their careers URL)
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
