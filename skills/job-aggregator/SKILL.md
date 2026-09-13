---
name: job-aggregator
description: >
  Invoke when searching for live job listings. Triggers on: "find jobs for me",
  "search jobs at [company]", "what roles are open at [company]", "job search",
  "find [role] openings", or as part of `status` dashboard refresh.
  Single entry point: scripts/find-jobs.py fans out across the ATS registry (9 platforms),
  Naukri, and the Indeed/Dice/ZipRecruiter connectors, then merges, deduplicates, scores
  and ranks in one place. Splits results into two tracks — 'targeted' for your configured
  companies and 'discovery' for open-market employers worth adding.
  Saves to data/market/job-feed.md and commits.
---

# Job Aggregator Skill

Searches all connected job sources in parallel, deduplicates, and ranks results
against your profile. Single source of live market intelligence.

## Trigger Commands

| Command | Action |
|---|---|
| `find jobs` | Full fan-out, then **only listings not seen before** (the daily default) |
| `find jobs at [company]` | Filter to one company across all sources |
| `find [role] jobs` | Search a specific role title |
| `find jobs at my companies` | `--targeted-only` — configured companies, no discovery |
| `show me everything` | Skip `--new-only` — include listings already seen |
| `applied to [company] [role]` | Mark applied — never shown again, never pruned |
| `not interested in [company]` | Mark stale — never shown again, record kept |
| `save [company] [role]` / `pin ...` | Keep on the shortlist |
| `job store stats` | Counts by status, index size |
| `fetch history` | What was fetched on each day |
| `what have I decided` | Decision history — what you pursued vs passed on |
| `prune job store [N] days` | Drop old listings; applied and shortlisted are kept |
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

## Step 2 — The Runbook

**`find jobs` means running every step below, in order.** This is not a menu. A source
you skip is coverage the user silently loses, and they cannot tell from the output that
it happened.

Only two things can call all the sources: a script can run scripts, and only you can call
MCP connectors. So you do the connector half first, hand the results to the entry point,
and it does the merging.

### 1. Check connector budgets

```bash
python3 scripts/mcp-budget.py check indeed
python3 scripts/mcp-budget.py check ziprecruiter
```

Non-zero exit means that connector is spent for today — skip it and say so. Never
work around the cap.

### 2. Call the MCP connectors yourself

A script cannot reach these. Call each one that is connected and under budget:

- **Indeed** — `search_jobs(search, location, country_code)`
- **Dice** — `search_jobs(keyword, location, jobs_per_page, sort)`
- **ZipRecruiter** — US and Canada only. For any other country it returns
  `UNSUPPORTED_COUNTRY`; skip it rather than spending a call to confirm that again.

Then `mcp-budget.py record <connector>` for each call you actually made.

### 3. Write connector results to JSON

Normalize to the standard shape — `title, company, location, url, source, posted,
salary, description` — and write one file per connector:

```
/tmp/cojobs/indeed.json
/tmp/cojobs/dice.json
```

### 4. Run the entry point with those files merged in

```bash
python3 scripts/find-jobs.py --limit 25 --write-feed \
  --merge /tmp/cojobs/indeed.json \
  --merge /tmp/cojobs/dice.json
```

This runs the ATS registry across all nine platforms, runs Naukri (on by default
whenever `naukri_enabled` is true), folds in the connector files, then dedupes, scores,
tags each job targeted/discovery, and ranks.

Role and location default to `target_roles[0]` and `target_locations[0]` — override with
`--role` / `--location`.

### 4b. Pipe through the job store — this is what makes a daily hunt useful

Without it every run re-presents the same ~2,000 listings, and the one thing that
matters daily — what appeared since yesterday — is invisible.

```bash
python3 scripts/find-jobs.py --limit 0 --merge /tmp/cojobs/indeed.json \
  | python3 scripts/job-store.py ingest --full-run --new-only --limit 25
```

Note `--limit 0` on the entry point: the store needs the **whole** result set to decide
what is new and what has vanished. Apply the limit at the store, after filtering.

| Flag | Effect |
|---|---|
| `--new-only` | Only listings never shown before — the default for a daily hunt |
| `--full-run` | This run covered the market, so absent listings count as missing |
| *(omit `--new-only`)* | New + returning, for "show me everything again" |

**Only pass `--full-run` when the run really was unfiltered.** A `--role` or `--limit`
run legitimately omits most of the market; telling the store otherwise expires live jobs.
Two consecutive misses expire a listing, so one bad run does not destroy the index.

The store suppresses `applied` and `not_interested` outright, and reports counts:

```
Run #7: 2008 in -> 34 new, 1966 returning, 12 suppressed (applied/not interested)
```

Relay that line. "34 new since yesterday" is the useful number; 2008 is noise.

### 4c. Decisions — and where the judgement actually lives

**This script stores facts. You supply the judgement.** There is no keyword scoring in
the store, deliberately — counting title words produced nonsense, treating "engineering"
as a dislike because the user dismissed one employer.

Before presenting a feed, read the user's decision history:

```bash
python3 scripts/job-store.py context
```

That returns what they applied to, pinned, saved, and rejected — with their own stated
reasons, and flagged where a rejection was a bulk company dismissal. Read it and judge
the new listings yourself: does this resemble what they pursued, or what they passed on?
Say so in plain language when you present the feed.

A bulk company rejection means **"not this employer"**. It says nothing about the role
type, and the output labels it as weak signal for exactly that reason. Do not infer role
preferences from it.

Record every reaction, with the reason in their words when they give one:

```bash
python3 scripts/job-store.py mark applied "Cisco" "Senior Software Engineer"
python3 scripts/job-store.py mark pinned "Google" "Senior SWE, AI/ML"
python3 scripts/job-store.py mark saved --url "https://..."
python3 scripts/job-store.py mark stale "Walt Disney" --all --reason "not in my radar"
```

| Status | Meaning | Shown again? |
|---|---|---|
| `interested` / `saved` / `pinned` | Worth pursuing | Yes, on request |
| `applied` | Applied to | Never — kept forever, never pruned |
| `stale` | User rejected it | Never — record kept for `context` |
| `expired` | Gone from the market | Never — nobody rejected it, it just ended |

`stale` and `expired` are different things and must not be conflated. One is a decision,
the other is the market moving on.

### 4d. Day-grouped history

Every run writes `data/market/runs/YYYY-MM-DD.json` — which listings were fetched that
day, which were new, and from which sources. Written once per day and then only appended
to, so git stores each day once instead of a fresh copy of everything daily.

```bash
python3 scripts/job-store.py runs      # fetch history by day
python3 scripts/job-store.py stats     # counts by status, index size
```

Full JD text is cached to `data/market/jobs/YYYY-MM-DD.json` — one file per day, keyed
by job id and sorted by company, so a day's jobs read in one place. Each index entry
records `jd_day` so a listing's JD can be found again. Cached only for listings actually
shown — so you can judge fit from real requirements later without bloating the index.

### 4e. Pruning

Never automatic. When the index passes ~3 MB the store says so, and you offer:

```bash
python3 scripts/job-store.py prune --days 90 --dry-run
python3 scripts/job-store.py prune --days 90
```

Always dry-run first and show the user what would go. `applied` and
`interested`/`saved`/`pinned` are never pruned at any age — that is their application
history and their own shortlist.

### 5. Read the coverage report before reporting anything

The entry point prints which sources ran, were skipped, or failed:

```
Source coverage:
  ✓ ATS registry     ran      1854 jobs
  ✓ Naukri           ran      126 jobs
  ✓ indeed           ran      8 jobs (merged)
  ○ ziprecruiter     skipped  connector not merged — Claude did not call it
```

**Relay anything not marked `ran` to the user.** A skipped source is missing coverage,
not an empty market — and only the coverage line makes that visible.

### What this skill does NOT run

`resolve-ats.py` and `careers-probe.py` are setup tools, not search tools. They discover
boards and write `config/companies.json`, probing dozens of endpoints per company for
data that changes rarely. Running them on every search would turn a 30-second job search
into several minutes. They belong to `setup`, `add company` and `refresh companies`.

Run them from here only when the registry is the actual problem — a company returning
zero that used to return jobs, or a company the user names that isn't in the registry.

### The two tracks

Every job is tagged `track`, keyed on the **employer**, not the source:

| Track | Meaning |
|---|---|
| `targeted` | A company in `target_companies` — the ATS registry reaches these directly |
| `discovery` | Any other employer, surfaced by Indeed, Dice or a broad Naukri search |

Both matter, and they are kept visibly separate. Targeted results will outnumber
discovery by orders of magnitude — a run returning 2206 jobs had 2196 targeted and 10
discovery — so a plain top-N would bury discovery entirely. `--limit` therefore reserves
`--discovery-slots` (default 3) for open-market results.

Discovery is how the user finds employers worth *adding* to their target list. When a
discovery company keeps appearing, say so and offer `add company [name]`.

`--targeted-only` drops discovery when the user wants just their own list.

### Connectors: Claude's half of the fan-out

Indeed, Dice and ZipRecruiter are MCP connectors — a script cannot call them. So:

1. **Check the budget first** (see below) — `mcp-budget.py check indeed`
2. Call the connectors yourself
3. Write their results to JSON in the standard shape
4. Hand them to the entry point: `--merge /tmp/indeed.json --merge /tmp/dice.json`

That keeps dedupe and scoring in one place instead of reimplementing them per source.

**Known geographic limits, verified live:**
- **ZipRecruiter** returns `UNSUPPORTED_COUNTRY` outside the US and Canada. For an
  India-based search it contributes nothing — don't spend a budget call on it.
- **Dice** is US-centric. It accepts an India location but returns US and remote roles,
  which then score low on location. Treat its output as discovery, never as local supply.

---

## Step 2b — Source Detail

Reference for each source the entry point calls, and what to do when one comes up empty.
The entry point already runs these — don't invoke them separately unless you are
debugging a single source.

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
Tool: search_jobs
Params: job_role=[role], location=[location], country_admin_code=US|CA
```
US and Canada only — any other country returns `UNSUPPORTED_COUNTRY`. Skip it entirely
for an India-based search rather than spending a budget call to confirm that again.

**Dice MCP:**
```
Tool: search_jobs
Params: keyword=[role], location=[location], jobs_per_page=N, sort=datePosted
Then: get_job_details on the ones worth keeping — search returns only a summary
```
US-centric. It accepts a non-US location but still returns US and remote roles, so
treat its output as discovery rather than local supply.

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

### Budget — check before every Indeed or ZipRecruiter call

**Indeed authenticates as the user's own Indeed account.** Burning its quota does not
just fail a search here — it degrades a service they use personally, outside this tool.
A feed refresh fanning out across 25 companies can spend a daily allowance in one
command, so the budget is enforced, not just intended.

```bash
python3 scripts/mcp-budget.py check indeed     # exit 0 = go, 1 = stop
python3 scripts/mcp-budget.py record indeed    # after each successful call
python3 scripts/mcp-budget.py status           # show all budgets
```

The rule:

1. Run `check` **before** the first Indeed/ZipRecruiter call of a task.
2. If it exits non-zero, **do not call that connector.** Say the budget is spent for
   today, and get the results from ATS, Naukri or web search instead.
3. Run `record` after each successful call so the ledger stays accurate.
4. When a search would need many calls, record the real count: `record indeed --count 12`.

Default cap is 60% of an assumed 100 calls/day, so 60. **That assumption is not a
provider-reported limit** — neither Indeed nor ZipRecruiter publishes a per-account MCP
quota. It is a deliberately conservative self-imposed budget. If the user learns the real
number, change `assumed_daily_limit` in `config/user.json` and the cap follows.
Dice is configured as unmetered (`assumed_daily_limit: 0`) — it needs no auth.

Prefer the cheapest source that answers the question. The ATS registry is free and
unlimited; spend Indeed calls on companies the registry cannot reach, not on ones it
already covers.

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

**Automate that with the careers probe.** It fetches the careers page, pulls out any ATS
board it references, *and* actively tests the careers host for API shapes that JavaScript
builds at runtime. Every candidate is verified against the live board before being
reported:

```bash
python3 scripts/careers-probe.py --company "Adobe"
python3 scripts/careers-probe.py --all-unreachable          # print findings
python3 scripts/careers-probe.py --all-unreachable --apply  # pin them
```

Two real wins from this, both permanent:
- **Adobe** — careers page is a React shell with no jobs in the HTML, but the HTML names
  `adobe.wd5.myworkdayjobs.com/external_experienced`. 500 jobs behind a stable API.
- **Qualcomm** — the endpoint never appears in the page source at all; the page builds
  `careers.qualcomm.com/api/pcsx/search` in JS. The active host probe found it anyway:
  1 Naukri match became 396 jobs, 161 in India.

That second case is why the probe tests the host directly instead of only reading HTML.

The same signals read by eye, if you are inspecting a page manually:

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
name goes into the keyword slug and every result is verified against the `company` field
afterwards. The scraper prints `matched / returned` per company so the filter stays
visible.

Matching is word-anchored in three tiers:

| Tier | Meaning | Example |
|---|---|---|
| exact | Name matches, or the query is the leading word | `Visa Consolidated Support Services India`, `Inter Ikea Group` |
| partial | Query appears mid-name behind a non-filler word — tagged `"match_confidence": "partial"` | `Skys Adobe Plus` when searching Adobe |
| dropped | No word-boundary match | `Metamorphosis Consulting` when searching Meta |

Never match on a bare substring or `startswith`. `Meta` prefixes `Metamorphosis
Consulting` and `SAP` prefixes `Sapient` — both are different employers, and a
character-level check silently files their jobs under a company you are targeting.

Treat anything carrying `match_confidence: "partial"` as unverified. Show it separately
in the feed rather than mixing it into the ranked results — a search for Adobe returns
an interior-design firm whose openings are for civil engineers and corporate lawyers.

**Search aliases.** Some registry names mean nothing to a job board. `ISL` is IBM
Software Labs; searching Naukri for "ISL" returns noise. Give those entries an alias once:

```bash
python3 scripts/resolve-ats.py --set-alias "ISL" "IBM ISL"
```

`--from-unreachable` uses `search_as` when set, and the registry name otherwise.
Aliases live in `config/companies.json` — **never hardcode a company name or alias in
a script or in this skill.**

**Aliases are discovered, not hardcoded.** When a targeted search returns fewer than
three matches, the scraper automatically retries under variants derived from the name
itself — `"<name> India"`, `"<name> Labs India"`, `"<name> Technologies"`. Many
multinationals list on Indian boards only under a local entity, so a bare name returns
almost nothing while the local one returns plenty (Qualcomm went 1 → 5 this way).

Anything that works is **suggested, not saved** — the scraper prints the exact
`--set-alias` command and leaves the decision to the user. Disable the retry with
`--no-retry-variants`.

**When the company name is also a skill keyword.** Some names cannot be rescued by any
alias. Searching Naukri for `SAP` returns TCS, Infosys, Capgemini and PwC hiring SAP
*consultants* — in the Indian market "SAP" is a skill, not an employer. The matcher
correctly rejects all of them and the scraper says so explicitly rather than reporting a
silent zero. Route those companies to their careers page instead; do not invent an alias
to force a match. The same trap applies to names like Oracle, Salesforce and Workday.

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
the page.

**When the page is client-rendered and WebFetch returns a shell**, open it in the browser
tool and read the network requests — that is how Microsoft's and Qualcomm's real
endpoints were found. The sequence:

1. `navigate` to the careers URL with a role and location in the query string
2. `read_network_requests` filtered on `api` or `search`
3. If a JSON endpoint appears, **stop scraping** — pin it with `resolve-ats.py --set` or
   `--from-url` so the company becomes permanently fetchable
4. Only if there is genuinely no API, read the rendered listings with `get_page_text`

Always prefer step 3. A pinned board keeps working; a scrape of rendered HTML is a
snapshot that dies on the next redesign.

**On Firecrawl.** The key in `.env` is set but the account is banned — the API returns
`403: This account has been banned`. Do not route work to Firecrawl expecting it to
work, and do not present its absence as the reason a company has no listings. If the
user wants it back they need a new key from firecrawl.dev. Everything in this ladder
works without it.

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

**`find-jobs.py` already did this.** Steps 3–5 describe what it does internally; they are
reference, not a second implementation. Don't merge, dedupe, score or rank by hand.



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

**Post it as two markdown tables — targeted first, then discovery — with a heading each
and nothing else.** No preamble, no commentary between rows. Columns:
`# | Score | Role | Company | Location | Key requirements | Apply`, with the link as
`[Apply](url)` inside the cell. Trim roles to ~40 chars and requirements to ~70 so cells
don't wrap. Full format rules in `skills/slack-bridge/SKILL.md`.

If the feed is long, cap each table at ~10 rows and put the full ranked list in a Canvas,
linked from a single line under the tables.

Slack failing must never fail the job search. Write the file, commit, then try Slack.

## Step 7 — Surface Insights

After ranking, tell the user:
- Totals per source, and the targeted/discovery split
- Which target companies returned jobs vs. which have no reachable board
  (from `config/companies.json` — name them, and give their careers URL)
- **Discovery companies worth adding.** If an employer the user has never targeted keeps
  surfacing with strong scores, name it and offer `add company [name]`. That is the
  feedback loop discovery exists for — otherwise it is just noise in the feed.
- Any source that returned nothing, and why. A geographic limit
  (ZipRecruiter outside US/CA) is not the same as a quiet market, and must never be
  reported as one.
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
