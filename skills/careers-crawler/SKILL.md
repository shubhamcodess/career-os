---
name: careers-crawler
description: >
  Get jobs from any company's own careers website when it has no reachable ATS board,
  no job-board connector and no public API. Works on any site, since nothing in it is
  specific to a company. Uses a real browser (Playwright) to find how the page gets its
  jobs: a known job system (pinned permanently), the JSON API the page calls, job data
  embedded in the page (JSON-LD, __NEXT_DATA__), or plain job links. Saves the best one as a
  recipe. Discovery runs on demand; extraction of saved recipes runs daily inside find jobs.
  Triggers on: "crawl careers page for [company]", "discover careers page for [company]",
  "get jobs from [company]'s careers site", "why can't we reach [company]",
  "crawl unreachable companies", "add [company] from its careers page", or when a
  company in the registry has no fetchable board.
---

# Careers Crawler

The last rung of job coverage, for companies that the ATS registry, Naukri and the
job-board connectors can't reach. It works any company's own careers page the way a
person would. Nothing in the script or this skill is specific to a company; every
company, URL and recipe lives in `config/companies.json`.

**Discovery beats scraping.** A careers page is usually a thin shell over a real job
system. Before any scraping, watch what the page loads and where its apply buttons
point. When this skill was built, four companies that looked unreachable turned out to
have a proper feed underneath (examples only, nothing is hardcoded):

| Company | Looked like | Actually was |
|---|---|---|
| Lowe's | Phenom careers site | Workday: apply links go to `lowes.wd5.myworkdayjobs.com/LWS_External_CS` |
| Visa | Custom careers page | Workday: the page calls `visa.wd5.myworkdayjobs.com/.../Visa` |
| PhonePe | Custom careers page | SmartRecruiters: job cards link to `jobs.smartrecruiters.com/PHONEPELIMITED` |
| IKEA | Branded jobs.ikea.com site | SmartRecruiters: apply links go to `jobs.smartrecruiters.com/InterIKEAGroup` |

Once pinned, those companies are fetched by the ATS registry every day at full depth,
with no browser. A recipe is only for sites where nothing like that exists.

---

## Policy — non-negotiable

Chosen by the user; do not change without asking:

- **Behave like an ordinary browser.** Plain Playwright. No stealth plugins, no
  fingerprint masking, no rotating user agents or proxies.
- **Stop if blocked.** A CAPTCHA, an "access denied" page, or HTTP 403/429 means the
  crawler stops for that company and reports it. Never try to get around a block. Fall
  back to Naukri or web search for that company.
- **Be polite.** A pause between page loads and API calls on the same site, a cap on
  pages per site (default 3), sites crawled one at a time, no logins.
- **Public pages only.** Nothing behind a sign-in. API replays only call the same
  endpoints the public page itself calls, in the same browser session.
- **Never LinkedIn.** LinkedIn is not crawled (see Guardrails in `CLAUDE.md`).

---

## What it looks for, in order

| # | Finding | Recipe mode | How it's used daily |
|---|---|---|---|
| 1 | A job system with an adapter (Workday, SmartRecruiters, Greenhouse, Lever, Ashby, Workable, Recruitee, Eightfold/pcsx) | *none, it's pinned* | Fetched by `ats-fetcher.py`, no browser |
| 2 | The JSON API the page calls to list jobs (GET or POST) | `api` | Page loads once for its session, then the API is replayed, paging by `page`/`offset` |
| 3 | JSON-LD `JobPosting` data in the page | `jsonld` | Page loads, structured postings are read |
| 4 | Job lists embedded in page data (`__NEXT_DATA__`, `application/json` scripts) | `embedded` | Page loads, the saved JSON path is read |
| 5 | Job links in the rendered page, grouped by URL pattern (`/job/123`, `?jobId=123`, links into iframes or other domains) | `links` | Page loads, "load more" is clicked, "next" pages followed |

Job systems it recognises but has **no adapter** for (iCIMS, Taleo, SuccessFactors,
Oracle HCM, Phenom, Avature, Jobvite, BambooHR, Teamtailor, Personio, Darwinbox, Zoho
Recruit, Keka, Freshteam, Breezy, JazzHR, Pinpoint, Rippling ATS, Dover) are reported by
name, then handled by rungs 2–5. That name is useful when Oracle HCM or a similar system
is shared by many companies. If the same system keeps coming up, writing an adapter in
`ats_platforms.py` is the durable fix.

For API and embedded recipes, a posting URL is taken from the data where there is one.
Otherwise it's derived by finding a page link containing the job's id
(`https://site/job/{id}`). If neither exists, listings link to the careers page, and
discovery says so.

---

## When it runs

| Step | Cadence | Why |
|---|---|---|
| **Discover** | On demand, or when a company is added | Slow: a full browser load per company, plus verification |
| **Extract** | Daily, automatically inside `find jobs` | Replays saved recipes only; skipped entirely if none exist |

---

## Step 1 — Find the careers page

For each company, use `careers_url` from `config/companies.json`.

If there isn't one, **find it with web search**, then verify it before using it:

```
WebSearch: "[company]" careers jobs official site
WebSearch: "[company]" careers India [role]
```

Only accept a URL on the company's own domain or a job system clearly registered to
it. Never a job aggregator (Naukri, Instahyre, Cutshort, VC job boards), never a
lookalike domain. Search results often surface the underlying board directly (e.g. a
`smartrecruiters.com/<Company>` link); pin those straight away with
`resolve-ats.py --from-url` and skip crawling.

**Prefer a search-results URL** with the role and location already in it. A bare
careers landing page often has no postings on it. The crawler follows one "search jobs"
/ "view openings" link automatically, but a direct results URL is more reliable and
makes API recipes return the right slice.

## Step 2 — Discover

Works on any URL, and for companies not yet in the registry:

```bash
python3 scripts/careers-crawler.py discover --company "Acme" --url "<careers or search-results URL>"
python3 scripts/careers-crawler.py discover --all-unreachable
```

It loads the page, lets client-side listings render, scrolls, clicks "load more",
follows a hub link if needed, and records every network request, JSON response, link
(including inside iframes), embedded script data and apply URL. Reports:

| Report | Meaning | Next |
|---|---|---|
| `FOUND workday:tenant/wd5/Site (500 jobs)` | A real job system behind the page | Pin it. Permanent, no more crawling |
| `api recipe — page API /api/jobs (40 jobs)` | The page's own job API, replayed successfully | Save; extracted daily |
| `jsonld recipe` / `embedded recipe` | Structured job data inside the page | Save; extracted daily |
| `links recipe — job links /job/ on site.com (21 jobs)` | Postings render as links | Save; extracted daily |
| `· job system: iCIMS (no adapter)` | Recognised system with no adapter; handled by a recipe | Consider an adapter if it recurs |
| `BLOCKED (HTTP 403)` | Site refused a normal browser | Stop. Naukri / web search for this company |
| `nothing usable` | No system, API, data or links | Try a search-results `--url`, else Naukri / web search |

**Sanity-check the sample titles** before saving. If they look like navigation
("HOME", "Teams", "Life at X") rather than job titles, don't save the recipe.

Nothing is written without `--apply`:

```bash
python3 scripts/careers-crawler.py discover --company "Acme" --url "<url>" --apply
```

`--apply` pins found boards through `resolve-ats.py --from-url` (which re-verifies
them) and saves recipes as a `scrape` block on the company's registry entry, creating
the entry if the company is new. `resolve-ats.py --refresh` preserves that block. A
company added this way should also go in `target.target_companies` so its jobs land in
the targeted track.

## Step 3 — Extract (daily)

`find-jobs.py` runs this automatically when any recipe exists, and reports it in the
coverage line:

```
  ✓ Careers pages    ran      31 jobs from 3 site(s)
```

Directly:

```bash
python3 scripts/careers-crawler.py extract --all --role "Software Engineer"
python3 scripts/careers-crawler.py extract --company "Acme" --max-pages 5
```

Output is the standard job shape with `"source": "careers"`, so dedupe, scoring and the
job store treat it like any other source. Location comes from the data where it exists
(API, JSON-LD). For link recipes it's read from text near the link and matched against
`target_locations`.

A recipe that suddenly returns nothing means the site changed. Re-run discover for
that company rather than reporting "no openings".

---

## What it can't do (be honest about these)

- **Private or signed APIs.** Some sites call GraphQL with hashed query IDs or
  short-lived signed tokens and render no job links. Replaying those would mean working
  around the site, so the crawler reports "nothing usable". Use Naukri / web search.
- **Blocks.** Sites behind bot protection return 403 to a plain browser. That's final.
- **Job descriptions** are only present when the API or JSON-LD carries them. Fetch the
  detail page when a listing is worth a closer look.
- **Scraped sites break silently** when redesigned. That's why discovery always tries
  for a real job system or API first, and why a zero-result extract is flagged.

---

## Commands

| Command | Action |
|---|---|
| `discover careers page for [company]` | Step 1 (web search if needed) + Step 2, report only |
| `add [company] from its careers page` | Steps 1–2 with `--apply`, then add to `target_companies` |
| `crawl unreachable companies` | Step 2 for every company with no fetchable board or recipe |
| `save careers findings` | Re-run the last discovery with `--apply` |
| `crawl careers pages` | Step 3 now, outside `find jobs` |
