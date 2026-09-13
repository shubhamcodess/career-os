---
name: careers-crawler
description: >
  Get jobs from companies that have no reachable ATS board, no job-board connector
  and no API, by working through their own public careers page with a real browser
  (Playwright). First tries to discover the job system hiding behind the page and pin
  it permanently; only scrapes the rendered listing when nothing sits underneath.
  Discovery runs on demand; extraction of saved recipes runs daily inside find jobs.
  Triggers on: "crawl careers page for [company]", "discover careers page for [company]",
  "get jobs from [company]'s careers site", "why can't we reach [company]",
  "crawl unreachable companies", or when a company in the registry has no fetchable board.
---

# Careers Crawler

The last rung of job coverage, for companies that the ATS registry, Naukri and the
job-board connectors can't reach. It works the company's own careers page the way
a person would.

**Discovery beats scraping.** A careers page is usually a thin shell over a real job
system. Before any scraping, watch what the page loads and where its apply buttons
point. When this skill was built, four companies that looked unreachable turned out to
have a proper feed underneath:

| Company | Looked like | Actually was |
|---|---|---|
| Lowe's | Phenom careers site | Workday: apply links go to `lowes.wd5.myworkdayjobs.com/LWS_External_CS` |
| Visa | Custom careers page | Workday: the page calls `visa.wd5.myworkdayjobs.com/.../Visa` |
| PhonePe | Custom careers page | SmartRecruiters: job cards link to `jobs.smartrecruiters.com/PHONEPELIMITED` |
| IKEA | Branded jobs.ikea.com site | SmartRecruiters: apply links go to `jobs.smartrecruiters.com/InterIKEAGroup` |

Once pinned, those companies are fetched by the ATS registry every day at full depth,
with no browser. A scrape recipe is only for sites where nothing like that exists.

---

## Policy — non-negotiable

Chosen by the user; do not change without asking:

- **Behave like an ordinary browser.** Plain Playwright. No stealth plugins, no
  fingerprint masking, no rotating user agents or proxies.
- **Stop if blocked.** A CAPTCHA, an "access denied" page, or HTTP 403/429 means the
  crawler stops for that company and reports it. Never try to get around a block. Fall
  back to Naukri or web search for that company.
- **Be polite.** A pause between page loads on the same site, a cap on pages per site
  (default 3), sites crawled one at a time, no logins.
- **Public pages only.** Nothing behind a sign-in.

---

## When it runs

| Step | Cadence | Why |
|---|---|---|
| **Discover** | On demand, or when a company is added | Slow: a full browser load per company, plus verifying candidate boards |
| **Extract** | Daily, automatically inside `find jobs` | Replays saved recipes only; skipped entirely if none exist |

---

## Step 1 — Find the careers page

For each company, use `careers_url` from `config/companies.json`.

If there isn't one, **find it with web search**, then verify it before saving:

```
WebSearch: "[company]" careers jobs official site
WebSearch: "[company]" careers India [role]
```

Only accept a URL on the company's own domain or its known job system. Never a job
aggregator, never a lookalike domain. Then save it:

```bash
python3 scripts/resolve-ats.py --set-careers "[company]" "https://careers.example.com"
```

**Prefer a search-results URL** with the role and location already in it, e.g.
`jobs.apple.com/en-in/search?location=india-INDC&search=software%20engineer`. A bare
careers landing page often has no postings on it. The crawler follows one "search jobs"
/ "view openings" link automatically, but a direct results URL is more reliable. Pass it
with `--url`.

## Step 2 — Discover

```bash
python3 scripts/careers-crawler.py discover --company "Apple" --url "<search-results URL>"
python3 scripts/careers-crawler.py discover --all-unreachable
```

It loads the page, lets client-side listings render, scrolls, and records:
- every network request the page makes
- every link on the page
- apply URLs embedded in the page source

Anything pointing at a known job system (Workday, SmartRecruiters, Greenhouse, Lever,
Ashby, Workable, Recruitee, Eightfold/pcsx) is **verified against the live board**
before it's reported. Outcomes:

| Report | Meaning | Next |
|---|---|---|
| `FOUND workday:lowes/wd5/... (500 jobs)` | A real job system behind the page | Pin it. Permanent, no more crawling |
| `scrape recipe /en-in/details/ (21 jobs)` | No job system, but postings render as links | Save the recipe; extracted daily |
| `BLOCKED (HTTP 403)` | Site refused a normal browser | Stop. Naukri / web search for this company |
| `nothing usable` | No job system, no job links | Try a search-results `--url`, else Naukri / web search |

Nothing is written without `--apply`. Show the user the report first, then:

```bash
python3 scripts/careers-crawler.py discover --company "Apple" --url "<url>" --apply
```

`--apply` pins found boards through `resolve-ats.py --from-url` (which re-verifies
them) and saves recipes as a `scrape` block on the company's registry entry.
`resolve-ats.py --refresh` preserves that block.

## Step 3 — Extract (daily)

`find-jobs.py` runs this automatically when any recipe exists, and reports it in the
coverage line:

```
  ✓ Careers pages    ran      31 jobs from 3 site(s)
```

Directly:

```bash
python3 scripts/careers-crawler.py extract --all --role "Software Engineer"
python3 scripts/careers-crawler.py extract --company "SAP" --max-pages 5
```

For each recipe it loads the listing, collects links matching the saved prefix,
follows a "next page" link up to the page cap, and filters titles by role. Output is
the standard job shape with `"source": "careers"`, so dedupe, scoring and the job
store treat it like any other source.

A recipe that suddenly returns zero links means the site changed. Re-run discover for
that company rather than reporting "no openings".

---

## What it can't do (be honest about these)

- **Private APIs.** Walmart's search runs through an AI assistant GraphQL endpoint with
  hashed query IDs, and Meta serves jobs through private GraphQL. Neither has job links
  to follow. Say so; use Naukri / web search.
- **Location and experience are best-effort** for scraped listings. Location is read
  from the text around each job link and is often blank. Experience isn't available
  until the job's own page is fetched. The job store and Claude's review handle
  judgement.
- **No job description text** in scraped listings yet, only title, company, location and
  link. Fetch the detail page when a listing is worth a closer look.
- **Scraped sites break silently** when redesigned. That is why discovery always tries
  for a real job system first.

---

## Commands

| Command | Action |
|---|---|
| `discover careers page for [company]` | Step 2 for one company, report only |
| `crawl unreachable companies` | Step 2 for every company with no fetchable board |
| `save careers findings` | Re-run the last discovery with `--apply` |
| `crawl careers pages` | Step 3 now, outside `find jobs` |
