#!/usr/bin/env python3
"""
Career OS — ATS Fetcher
Fetches live job listings directly from Greenhouse and Lever public JSON APIs.
No auth, no scraping, no bot detection — these are intentionally public endpoints.

Usage:
  # From config (uses target_companies in config/user.json):
  python3 scripts/ats-fetcher.py --from-config --role "Software Engineer"

  # For a specific company (used by `find jobs at [company]` command):
  python3 scripts/ats-fetcher.py --company Razorpay --role "Engineer"

  # Multiple companies:
  python3 scripts/ats-fetcher.py --companies Razorpay Stripe Notion --role "PM"

Output: JSON array to stdout (same shape as naukri-scraper output), status to stderr
"""

import argparse
import json
import sys
import re
import os
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------------------------------------------------------
# Known slug mappings: company name (lowercase) → {platform, slug}
# Verified against live APIs — mark unverified entries as "none" rather than guessing.
# Auto-discovery (try common slug patterns on both platforms) runs for unknown companies.
# ---------------------------------------------------------------------------
KNOWN_SLUGS: dict[str, dict] = {
    # ── Indian product companies (verified) ──────────────────────────────────
    "meesho":       {"platform": "lever",        "slug": "meesho"},        # ✅
    "cred":         {"platform": "lever",        "slug": "cred"},          # ✅
    "groww":        {"platform": "greenhouse",   "slug": "groww"},         # ✅
    "postman":      {"platform": "greenhouse",   "slug": "postman"},       # ✅
    "freshworks":   {"platform": "lever",        "slug": "freshworks"},    # ✅ (board valid, 0 now)
    # Indian companies on internal ATS (careers page only, not Greenhouse/Lever)
    "razorpay":     {"platform": "none",  "slug": "", "note": "uses razorpay.com/careers (internal ATS)"},
    "phonepe":      {"platform": "none",  "slug": "", "note": "uses phonepe.com/careers (internal ATS)"},
    "zepto":        {"platform": "none",  "slug": "", "note": "careers.zepto.com (internal ATS)"},
    "browserstack": {"platform": "none",  "slug": "", "note": "browserstack.com/careers (internal ATS)"},
    "flipkart":     {"platform": "none",  "slug": "", "note": "uses flipkartcareers.com"},
    "walmart":      {"platform": "none",  "slug": "", "note": "uses careers.walmart.com"},
    "ikea":         {"platform": "none",  "slug": "", "note": "uses about.ikea.com/en/careers"},
    # ── Global product companies (verified) ──────────────────────────────────
    "stripe":       {"platform": "greenhouse",   "slug": "stripe"},        # ✅ 621 jobs
    "databricks":   {"platform": "greenhouse",   "slug": "databricks"},    # ✅ 876 jobs
    "cloudflare":   {"platform": "greenhouse",   "slug": "cloudflare"},    # ✅
    "coinbase":     {"platform": "greenhouse",   "slug": "coinbase"},      # ✅
    "reddit":       {"platform": "greenhouse",   "slug": "reddit"},        # ✅
    "discord":      {"platform": "greenhouse",   "slug": "discord"},       # ✅
    "airbnb":       {"platform": "greenhouse",   "slug": "airbnb"},        # ✅
    "figma":        {"platform": "greenhouse",   "slug": "figma"},         # ✅
    "anthropic":    {"platform": "greenhouse",   "slug": "anthropic"},     # ✅
    "openai":       {"platform": "greenhouse",   "slug": "openai"},        # ✅
    "hashicorp":    {"platform": "greenhouse",   "slug": "hashicorp"},     # ✅
    "netflix":      {"platform": "lever",        "slug": "netflix"},       # ✅
    "lyft":         {"platform": "lever",        "slug": "lyft"},          # ✅
    "vercel":       {"platform": "lever",        "slug": "vercel"},        # ✅
    # Global companies on internal ATS
    "google":       {"platform": "none",  "slug": "", "note": "uses careers.google.com"},
    "microsoft":    {"platform": "none",  "slug": "", "note": "uses careers.microsoft.com"},
    "amazon":       {"platform": "none",  "slug": "", "note": "uses amazon.jobs"},
    "meta":         {"platform": "none",  "slug": "", "note": "uses metacareers.com"},
    "apple":        {"platform": "none",  "slug": "", "note": "uses jobs.apple.com"},
    "nvidia":       {"platform": "none",  "slug": "", "note": "uses nvidia.wd5.myworkdayjobs.com"},
    "visa":         {"platform": "none",  "slug": "", "note": "uses jobs.smartrecruiters.com/Visa"},
    "lowes":        {"platform": "none",  "slug": "", "note": "uses jobs.lowes.com"},
    "target":       {"platform": "none",  "slug": "", "note": "uses jobs.target.com"},
}

GH_API  = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
LV_API  = "https://api.lever.co/v0/postings/{slug}?mode=json&limit=200"
ASHBY_API = "https://jobs.ashby.com/api/job-board?identifier={slug}"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


def _get(url: str, timeout: int = 10) -> dict | list | None:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception:
        return None


def _slug_candidates(name: str) -> list[str]:
    """Generate slug guesses from a company name."""
    clean = name.lower().strip()
    no_space = clean.replace(" ", "")
    hyphen = clean.replace(" ", "-")
    return list(dict.fromkeys([no_space, hyphen, clean]))


def resolve_ats(company: str) -> dict | None:
    """Return {platform, slug} for a company, or None if no public ATS found."""
    key = company.lower().strip()

    known = KNOWN_SLUGS.get(key)
    if known:
        if known["platform"] == "none":
            print(f"  {company}: internal ATS — {known.get('note', 'not on Greenhouse/Lever')}", file=sys.stderr)
            return None
        return known

    # Auto-discover: try slug guesses on both platforms
    print(f"  {company}: unknown — probing Greenhouse and Lever…", file=sys.stderr)
    for slug in _slug_candidates(company):
        if _get(GH_API.format(slug=slug)):
            return {"platform": "greenhouse", "slug": slug}
        if _get(LV_API.format(slug=slug)):
            return {"platform": "lever", "slug": slug}

    print(f"  {company}: not found on Greenhouse or Lever", file=sys.stderr)
    return None


def fetch_greenhouse(slug: str, role_filter: str) -> list[dict]:
    data = _get(GH_API.format(slug=slug))
    if not data or "jobs" not in data:
        return []
    jobs = []
    for j in data["jobs"]:
        title = j.get("title", "")
        if role_filter and not any(w.lower() in title.lower() for w in role_filter.split()):
            continue
        loc = ", ".join(o.get("name", "") for o in j.get("offices", [])) or \
              ", ".join(l.get("name", "") for l in j.get("location", {}) if isinstance(j.get("location"), list)) or \
              (j.get("location", {}).get("name", "") if isinstance(j.get("location"), dict) else "")
        jobs.append({
            "title": title,
            "company": slug.capitalize(),
            "experience": "",
            "location": loc,
            "salary": "Not disclosed",
            "description": _strip_html(j.get("content", ""))[:300],
            "posted": j.get("updated_at", ""),
            "tags": [d.get("name", "") for d in j.get("departments", []) if d.get("name")],
            "url": j.get("absolute_url", ""),
            "source": "greenhouse",
        })
    return jobs


def fetch_lever(slug: str, role_filter: str) -> list[dict]:
    data = _get(LV_API.format(slug=slug))
    if not isinstance(data, list):
        return []
    jobs = []
    for j in data:
        title = j.get("text", "")
        if role_filter and not any(w.lower() in title.lower() for w in role_filter.split()):
            continue
        loc = j.get("categories", {}).get("location", "") or j.get("country", "")
        jobs.append({
            "title": title,
            "company": slug.capitalize(),
            "experience": "",
            "location": loc,
            "salary": "Not disclosed",
            "description": _strip_html(j.get("descriptionPlain", "") or j.get("description", ""))[:300],
            "posted": "",
            "tags": [t for t in [j.get("categories", {}).get("team", ""),
                                  j.get("categories", {}).get("department", "")] if t],
            "url": j.get("hostedUrl", ""),
            "source": "lever",
        })
    return jobs


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "").strip()


def fetch_company(company: str, role_filter: str) -> list[dict]:
    try:
        ats = resolve_ats(company)
        if not ats:
            return []
        platform, slug = ats["platform"], ats["slug"]
        if platform == "greenhouse":
            jobs = fetch_greenhouse(slug, role_filter)
        elif platform == "lever":
            jobs = fetch_lever(slug, role_filter)
        else:
            jobs = []

        for j in jobs:
            j["company"] = company

        print(f"  {company} ({platform}:{slug}): {len(jobs)} jobs", file=sys.stderr)
        return jobs
    except Exception as e:
        print(f"  {company}: ERROR — {e}", file=sys.stderr)
        return []


def load_config_companies() -> list[str]:
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "user.json")
    try:
        with open(config_path) as f:
            cfg = json.load(f)
        return cfg.get("target", {}).get("target_companies", [])
    except Exception:
        return []


def main():
    parser = argparse.ArgumentParser(description="Fetch jobs from company ATS boards")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--from-config", action="store_true",
                       help="Use target_companies from config/user.json")
    group.add_argument("--company",  help="Single company name")
    group.add_argument("--companies", nargs="+", help="Multiple company names")

    parser.add_argument("--role", default="",
                        help="Role keyword filter (e.g. 'Engineer', 'Product Manager')")
    parser.add_argument("--workers", type=int, default=6,
                        help="Parallel fetch threads (default: 6)")
    args = parser.parse_args()

    if args.from_config:
        companies = load_config_companies()
        if not companies:
            print("No target_companies in config/user.json", file=sys.stderr)
            sys.exit(1)
    elif args.company:
        companies = [args.company]
    else:
        companies = args.companies

    print(f"Fetching ATS listings for {len(companies)} companies (role filter: '{args.role or 'none'}')…",
          file=sys.stderr)

    all_jobs: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch_company, c, args.role): c for c in companies}
        for fut in as_completed(futures):
            all_jobs.extend(fut.result())

    print(f"\nTotal: {len(all_jobs)} jobs across {len(companies)} companies", file=sys.stderr)
    print(json.dumps(all_jobs, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
