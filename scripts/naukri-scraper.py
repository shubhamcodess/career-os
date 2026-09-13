#!/usr/bin/env python3
"""
Career OS — Naukri Scraper

Fetches job listings from Naukri.com using Playwright + system Chrome.

This is the primary fallback for companies with no reachable ATS board. Most
large enterprises hiring in India (Flipkart, PhonePe, Walmart India, Visa India,
Qualcomm India, SAP Labs, Adobe India, IBM) expose nothing by API but list
heavily on Naukri.

Usage:
  # Broad role search
  python3 scripts/naukri-scraper.py --role "Software Engineer" --location Bangalore --pages 2

  # One company
  python3 scripts/naukri-scraper.py --company IBM --role "Software Engineer" --location Bangalore

  # Several companies
  python3 scripts/naukri-scraper.py --companies IBM Flipkart PhonePe --role "Software Engineer"

  # Every company in config/companies.json with no reachable ATS board.
  # This is the one that closes the coverage gap.
  python3 scripts/naukri-scraper.py --from-unreachable --role "Software Engineer"

Output: JSON array on stdout (same shape as ats-fetcher), status on stderr.

Requires: playwright, playwright-stealth
System Chrome must be installed (used to bypass Akamai WAF).
"""

import asyncio
import json
import os
import re
import sys
import argparse
import random
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(ROOT, "config", "companies.json")
USER_CONFIG_PATH = os.path.join(ROOT, "config", "user.json")

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
]

def slugify(text: str) -> str:
    """Naukri URLs are hyphenated keyword slugs."""
    s = re.sub(r"[^\w\s-]", "", (text or "").lower()).strip()
    return re.sub(r"[\s_]+", "-", s)


def load_unreachable() -> list[tuple[str, str]]:
    """
    Companies with no fetchable ATS board, as (display_name, search_term).

    search_term comes from the registry's `search_as` when set. Some entries are
    internal names that mean nothing to a job board — "ISL" is IBM Software Labs,
    and searching Naukri for "ISL" returns noise. Set one with:
        resolve-ats.py --set-alias "ISL" "IBM ISL"
    """
    try:
        with open(REGISTRY_PATH) as f:
            reg = json.load(f)
    except Exception as e:
        print(f"Could not read config/companies.json: {e}", file=sys.stderr)
        return []
    out = []
    for c in reg.get("companies", {}).values():
        fetchable = (c.get("status") in ("verified", "manual")
                     and c.get("platform", "none") != "none")
        if fetchable:
            continue
        name = c.get("name", "")
        if name:
            out.append((name, c.get("search_as") or name))
    return out


def default_location() -> str:
    try:
        with open(USER_CONFIG_PATH) as f:
            cfg = json.load(f)
        locs = cfg.get("target", {}).get("target_locations", [])
        if locs:
            return locs[0].split(",")[0].strip()
    except Exception:
        pass
    return "Bangalore"


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
            role_slug = slugify(role)
            location_slug = slugify(location)
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


def dedupe(jobs: list[dict]) -> list[dict]:
    seen, out = set(), []
    for j in jobs:
        key = (j.get("url") or "").split("?")[0] or \
              f"{j.get('company','').lower()}|{j.get('title','').lower()}"
        if key in seen:
            continue
        seen.add(key)
        out.append(j)
    return out


def matches_company(job: dict, company: str) -> bool:
    """Naukri keyword search is fuzzy — verify the listing is really this company."""
    a = re.sub(r"[^a-z]", "", (job.get("company") or "").lower())
    b = re.sub(r"[^a-z]", "", company.lower())
    return bool(a and b) and (b in a or a in b)


async def run_searches(queries: list[tuple[str, str]], location: str,
                       pages: int) -> list[dict]:
    """queries: list of (search_text, company_filter_or_empty)."""
    all_jobs: list[dict] = []
    for i, (query, company) in enumerate(queries, 1):
        label = company or query
        print(f"[{i}/{len(queries)}] {label} …", file=sys.stderr)
        try:
            found = await scrape_naukri(query, location, pages)
        except Exception as e:
            print(f"    failed: {e}", file=sys.stderr)
            continue

        if company:
            kept = [j for j in found if matches_company(j, company)]
            print(f"    {len(kept)} matched / {len(found)} returned", file=sys.stderr)
            all_jobs.extend(kept)
        else:
            print(f"    {len(found)} jobs", file=sys.stderr)
            all_jobs.extend(found)

        if i < len(queries):
            await asyncio.sleep(random.uniform(4, 8))
    return all_jobs


def main():
    p = argparse.ArgumentParser(description="Fetch job listings from Naukri.com")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--company", help="Target a single company by name")
    g.add_argument("--companies", nargs="+", help="Target several companies")
    g.add_argument("--from-unreachable", action="store_true",
                   help="Every company in config/companies.json with no fetchable "
                        "ATS board — the coverage gap this scraper exists to close")

    p.add_argument("--role", default="", help="Role keywords, e.g. 'Software Engineer'")
    p.add_argument("--location", default="", help="City (defaults to target_locations[0])")
    p.add_argument("--pages", type=int, default=2, help="Pages per search (default 2)")
    args = p.parse_args()

    location = args.location or default_location()

    if args.from_unreachable:
        companies = load_unreachable()
        if not companies:
            print("No unreachable companies in the registry — nothing to do.", file=sys.stderr)
            print(json.dumps([]))
            return
        print(f"{len(companies)} companies have no ATS board: "
              f"{', '.join(n for n, _ in companies)}", file=sys.stderr)
    elif args.companies:
        companies = [(c, c) for c in args.companies]
    elif args.company:
        companies = [(args.company, args.company)]
    else:
        companies = []

    if companies:
        # Naukri has no company filter parameter, so the search term goes into
        # the keyword slug and results are verified against it afterwards.
        queries = [(f"{term} {args.role}".strip(), term) for _, term in companies]
    else:
        if not args.role:
            p.error("--role is required unless targeting companies")
        queries = [(args.role, "")]

    print(f"Naukri: {len(queries)} search(es) in {location}, {args.pages} page(s) each",
          file=sys.stderr)

    jobs = dedupe(asyncio.run(run_searches(queries, location, args.pages)))

    print(json.dumps(jobs, ensure_ascii=False, indent=2))
    found_companies = len({j.get("company") for j in jobs})
    print(f"\n# {len(jobs)} jobs across {found_companies} companies", file=sys.stderr)


if __name__ == "__main__":
    main()
