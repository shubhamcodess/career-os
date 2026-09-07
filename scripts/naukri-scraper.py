#!/usr/bin/env python3
"""
Career OS — Naukri Scraper
Fetches job listings from Naukri.com using Playwright + system Chrome.
Usage: python3 scripts/naukri-scraper.py --role "Software Engineer" --location "Bangalore" --pages 2
Output: JSON to stdout, errors to stderr

Requires: playwright, playwright-stealth
System Chrome must be installed (used to bypass Akamai WAF).
"""

import asyncio
import json
import sys
import argparse
import random
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
]

async def scrape_naukri(role: str, location: str, pages: int = 2) -> list[dict]:
    jobs = []

    async with async_playwright() as p:
        # System Chrome needed — bundled Chromium gets Akamai-blocked (TLS fingerprint mismatch)
        Stealth().hook_playwright_context(p)
        browser = await p.chromium.launch(
            headless=True,
            channel="chrome",
            args=["--no-sandbox"],
        )

        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1366, "height": 768},
            locale="en-IN",
        )

        page = await context.new_page()

        for page_num in range(1, pages + 1):
            role_slug = role.lower().replace(" ", "-")
            location_slug = location.lower().replace(" ", "-")
            url = f"https://www.naukri.com/{role_slug}-jobs-in-{location_slug}-{page_num}"

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(random.uniform(3, 5))

                # Selector updated Sep 2026 — Naukri moved from article.jobTuple to [data-job-id]
                cards = await page.query_selector_all("[data-job-id]")

                for card in cards:
                    try:
                        title_el  = await card.query_selector("a.title")
                        company_el = await card.query_selector("a.comp-name")
                        exp_el    = await card.query_selector(".expwdth")
                        salary_el = await card.query_selector(".sal span[title]")
                        loc_el    = await card.query_selector(".locWdth")
                        date_el   = await card.query_selector("span.job-post-day")
                        desc_el   = await card.query_selector("span.job-desc")
                        tags_els  = await card.query_selector_all("li.tag-li")

                        title   = (await title_el.get_attribute("title") or await title_el.inner_text()) if title_el else ""
                        link    = await title_el.get_attribute("href") if title_el else ""
                        company = (await company_el.get_attribute("title") or await company_el.inner_text()) if company_el else ""
                        exp     = (await exp_el.get_attribute("title") or await exp_el.inner_text()) if exp_el else ""
                        salary  = (await salary_el.get_attribute("title") or await salary_el.inner_text()) if salary_el else "Not disclosed"
                        loc     = (await loc_el.get_attribute("title") or await loc_el.inner_text()) if loc_el else ""
                        date    = await date_el.inner_text() if date_el else ""
                        desc    = await desc_el.inner_text() if desc_el else ""
                        tags    = [await t.inner_text() for t in tags_els]

                        if title and company:
                            jobs.append({
                                "title": title.strip(),
                                "company": company.strip(),
                                "experience": exp.strip(),
                                "location": loc.strip(),
                                "salary": salary.strip(),
                                "description": desc.strip(),
                                "posted": date.strip(),
                                "tags": [t.strip() for t in tags if t.strip()],
                                "url": link,
                                "source": "naukri",
                            })
                    except Exception:
                        continue

            except Exception as e:
                print(f"Page {page_num} failed: {e}", file=sys.stderr)
                continue

            if page_num < pages:
                await asyncio.sleep(random.uniform(3, 6))

        await browser.close()

    return jobs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", required=True)
    parser.add_argument("--location", default="Bangalore")
    parser.add_argument("--pages", type=int, default=2)
    args = parser.parse_args()

    jobs = asyncio.run(scrape_naukri(args.role, args.location, args.pages))
    print(json.dumps(jobs, ensure_ascii=False, indent=2))
    print(f"\n# {len(jobs)} jobs fetched", file=sys.stderr)


if __name__ == "__main__":
    main()
