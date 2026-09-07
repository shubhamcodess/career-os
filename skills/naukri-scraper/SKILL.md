---
name: naukri-scraper
description: >
  Invoke to fetch live job listings from Naukri.com — the primary Indian job board.
  Triggers on: "search naukri for [role]", "naukri jobs for [role]",
  "find jobs on naukri", or when job-aggregator runs and Naukri is enabled in config.
  Uses Python + Playwright for JS-rendered page scraping.
  This skill is OPTIONAL and fragile — Naukri actively blocks scrapers.
  Set "naukri_enabled": true in config/user.json to activate.
  Saves results to data/market/job-feed.md alongside other sources.
---

# Naukri Scraper Skill

Scrapes live job listings from Naukri.com using a headless browser.

**Honest status:** Naukri has no public API. Scraping is the only option.
They actively detect and block bots. This skill uses Playwright with
human-like delays and user-agent rotation to minimize detection.
It works but may break if Naukri updates their anti-bot measures.
Check `config/user.json` → `naukri_enabled` to turn on/off.

**Why include it:** Naukri has exclusive listings not on Indeed/LinkedIn,
especially from Indian service companies and mid-market product companies.
For the Indian job market, ignoring Naukri means missing ~40% of listings.

## Prerequisites

```bash
pip install playwright
playwright install chromium
```

Add to `scripts/requirements.txt`:
```
playwright>=1.40.0
```

## Script: scripts/naukri-scraper.py

Claude Code will generate and run this script:

```python
#!/usr/bin/env python3
"""
Career OS — Naukri Scraper
Fetches job listings from Naukri.com using Playwright.
Usage: python3 scripts/naukri-scraper.py --role "Product Manager" --location "Bangalore" --pages 3
Output: JSON to stdout, errors to stderr
"""

import asyncio
import json
import sys
import argparse
import random
import time
from playwright.async_api import async_playwright

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

async def scrape_naukri(role: str, location: str, pages: int = 2) -> list[dict]:
    jobs = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1366, "height": 768},
            locale="en-IN",
        )
        
        # Mask automation signals
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)
        
        page = await context.new_page()
        
        for page_num in range(1, pages + 1):
            role_slug = role.lower().replace(" ", "-")
            location_slug = location.lower().replace(" ", "-")
            url = f"https://www.naukri.com/{role_slug}-jobs-in-{location_slug}-{page_num}"
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                # Human-like delay
                await asyncio.sleep(random.uniform(2.5, 4.5))
                
                # Extract job cards
                cards = await page.query_selector_all("article.jobTuple")
                
                for card in cards:
                    try:
                        title_el = await card.query_selector("a.title")
                        company_el = await card.query_selector("a.subTitle")
                        exp_el = await card.query_selector("span.experience")
                        location_el = await card.query_selector("span.location")
                        salary_el = await card.query_selector("span.salary")
                        date_el = await card.query_selector("span.date")
                        tags_els = await card.query_selector_all("li.tag")
                        
                        title = await title_el.inner_text() if title_el else ""
                        link = await title_el.get_attribute("href") if title_el else ""
                        company = await company_el.inner_text() if company_el else ""
                        exp = await exp_el.inner_text() if exp_el else ""
                        loc = await location_el.inner_text() if location_el else ""
                        salary = await salary_el.inner_text() if salary_el else "Not disclosed"
                        date = await date_el.inner_text() if date_el else ""
                        tags = [await t.inner_text() for t in tags_els]
                        
                        if title and company:
                            jobs.append({
                                "title": title.strip(),
                                "company": company.strip(),
                                "experience": exp.strip(),
                                "location": loc.strip(),
                                "salary": salary.strip(),
                                "posted": date.strip(),
                                "tags": tags,
                                "url": link,
                                "source": "naukri"
                            })
                    except Exception:
                        continue
                        
            except Exception as e:
                print(f"Page {page_num} failed: {e}", file=sys.stderr)
                continue
            
            # Polite delay between pages
            if page_num < pages:
                await asyncio.sleep(random.uniform(3, 6))
        
        await browser.close()
    
    return jobs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", required=True)
    parser.add_argument("--location", default="India")
    parser.add_argument("--pages", type=int, default=2)
    args = parser.parse_args()
    
    jobs = asyncio.run(scrape_naukri(args.role, args.location, args.pages))
    print(json.dumps(jobs, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
```

## How Claude Code Invokes This

```bash
python3 scripts/naukri-scraper.py \
  --role "Product Manager" \
  --location "Bangalore" \
  --pages 2
```

Parse the JSON output and merge results into the job feed using the same
scoring and deduplication logic as job-aggregator skill.

## Failure Handling

If the scraper returns 0 results or throws an error:
1. Log to `data/logs/naukri-scraper.log` with timestamp
2. Notify user: "Naukri scraper returned no results — site may have updated its structure.
   Check data/logs/naukri-scraper.log. Job feed built from other sources."
3. Continue with results from other MCPs — don't block the full job search

## Enabling / Disabling

In `config/user.json`:
```json
{
  "integrations": {
    "naukri_enabled": true,
    "naukri_pages_per_search": 2,
    "naukri_delay_seconds": [3, 6]
  }
}
```

Set `naukri_enabled: false` to skip Naukri entirely and use only MCP sources.
