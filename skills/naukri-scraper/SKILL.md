---
name: naukri-scraper
description: >
  Invoke to fetch live job listings from Naukri.com — the primary Indian job board.
  Triggers on: "search naukri for [role]", "naukri jobs for [role]",
  "find jobs on naukri", or when job-aggregator runs and Naukri is enabled in config.
  Uses Python + Playwright with system Chrome to bypass Akamai WAF detection.
  This skill is OPTIONAL and somewhat fragile — Naukri updates its DOM periodically.
  Set "naukri_enabled": true in config/user.json to activate.
  Saves results to data/market/job-feed.md alongside other sources.
---

# Naukri Scraper Skill

Scrapes live job listings from Naukri.com using a headless browser.

**Honest status:** Naukri has no public API. Scraping is the only option.
They use Akamai WAF which detects the TLS fingerprint of bundled Playwright
Chromium. This skill bypasses that by using `channel="chrome"` (system Chrome)
plus `playwright-stealth` for JS-level automation signal masking.
It works but may break if Naukri updates their DOM or anti-bot measures.

**Why include it:** Naukri has exclusive listings not on Indeed/LinkedIn,
especially from Indian product companies and mid-market companies.
For the Indian job market, ignoring Naukri means missing ~40% of listings.

## Prerequisites

```bash
pip3 install playwright playwright-stealth --break-system-packages
python3 -m playwright install chromium   # if not already installed
# System Chrome must also be installed at /Applications/Google Chrome.app
```

`scripts/requirements.txt` entries:
```
playwright>=1.40.0
playwright-stealth>=2.0.0
```

**Important:** Bundled Playwright Chromium gets blocked by Akamai (TLS fingerprint
mismatch). The script uses `channel="chrome"` which launches the real system Chrome
installation. Both must be present.

## Script: `scripts/naukri-scraper.py`

The live script is at `scripts/naukri-scraper.py`. Do NOT regenerate or replace it —
the current version has been fixed to work against the live Naukri DOM as of Sep 2026.

**Key implementation details (for debugging if selectors break):**
- Uses `channel="chrome"` (system Chrome) to bypass Akamai TLS fingerprint blocking
- Uses `Stealth().hook_playwright_context(p)` where `p` is the `async_playwright()` context
- Selector set updated Sep 2026:
  - Job cards: `[data-job-id]` (was: `article.jobTuple`)
  - Title: `a.title` with `.get_attribute("title")` fallback to `.inner_text()`
  - Company: `a.comp-name` with `.get_attribute("title")`
  - Experience: `.expwdth` with `.get_attribute("title")`
  - Salary: `.sal span[title]` with `.get_attribute("title")`
  - Location: `.locWdth` with `.get_attribute("title")`
  - Date posted: `span.job-post-day`
  - Description snippet: `span.job-desc`
  - Skill tags: `li.tag-li` (was: `li.tag`)

## How Claude Code Invokes This

```bash
# From job-aggregator (config-driven):
python3 scripts/naukri-scraper.py \
  --role "Software Engineer" \
  --location "Bangalore" \
  --pages 2

# Single page smoke test:
python3 scripts/naukri-scraper.py --role "Software Engineer" --location "Bangalore" --pages 1
```

Read `config/user.json` for:
- `target_roles[0]` → `--role`
- `target_locations[0]` → `--location` (strip country, use city only)
- `naukri_pages_per_search` → `--pages`

## Output Format

JSON array printed to stdout. Each job:
```json
{
  "title": "Senior Software Engineer",
  "company": "Walmart Global Tech",
  "experience": "5-8 Yrs",
  "location": "Bengaluru",
  "salary": "Not disclosed",
  "description": "We are looking for...",
  "posted": "3 Days Ago",
  "tags": ["Python", "Microservices", "AWS"],
  "url": "https://www.naukri.com/job-listings-...",
  "source": "naukri"
}
```

Same shape as `ats-fetcher.py` output — both can be merged directly.

## Failure Handling

If the scraper returns 0 results or throws an error:
1. Log the error to stderr (already done by the script)
2. Notify user: "Naukri scraper returned no results — DOM may have changed.
   Run a smoke test: `python3 scripts/naukri-scraper.py --role 'Software Engineer' --location 'Bangalore' --pages 1`
   Check selector constants in the script if 0 results come back."
3. Continue with results from ATS fetcher and MCPs — don't block the full job search

**Common failure modes:**
- `Error: Executable doesn't exist` → System Chrome not installed or path changed
- 0 results with no error → DOM selector change, inspect a live Naukri page
- Timeout → Naukri slow or blocking; try increasing timeout or reducing `--pages`

## Enabling / Disabling

In `config/user.json`:
```json
{
  "integrations": {
    "naukri_enabled": true,
    "naukri_pages_per_search": 2
  }
}
```

Set `naukri_enabled: false` to skip Naukri entirely and use only ATS + MCP sources.
