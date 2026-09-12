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

**Check these are actually connected before relying on them.** Indeed, ZipRecruiter and
Dice are declared in `mcp/.mcp.json`, but a declaration is not a connection. If their
tools are absent from the session, say so plainly and fall through to Source D — do not
silently return fewer results and let the user think the market is quiet.

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
| `icims.com`, `phenompeople`, `successfactors` | not supported yet | careers_url + Rung 3 |

**Rung 2 — Naukri, for anything hiring in India.**

This is the strongest fallback for a Bangalore-based search, and it covers exactly the
companies that are hardest to reach by API: Flipkart, PhonePe, Walmart India, Visa India,
Qualcomm India, SAP Labs, Adobe India, IKEA India. Requires `naukri_enabled: true`.

```bash
python3 scripts/naukri-scraper.py --role "[role]" --location "[city]" --pages [N]
```

Naukri cannot filter by a single company via URL. Run it broadly and post-filter the
JSON on the `company` field against your unreachable list.

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
