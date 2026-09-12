#!/usr/bin/env python3
"""
Career OS — ATS Fetcher

Fetches live job listings from company ATS boards (Greenhouse, Lever, Ashby,
Workable, SmartRecruiters, Recruitee) using their public JSON APIs.
No auth, no scraping, no bot detection.

No company is hardcoded here. Every company -> platform/slug mapping is read
from config/companies.json, which you build with:

    python3 scripts/resolve-ats.py --from-config

Usage:
  # Every company in the registry (default — mirrors your target_companies)
  python3 scripts/ats-fetcher.py --all --role "Software Engineer"

  # Only companies listed in config/user.json target_companies[]
  python3 scripts/ats-fetcher.py --from-config --role "Software Engineer"

  # One company
  python3 scripts/ats-fetcher.py --company Stripe --role Engineer

  # Several
  python3 scripts/ats-fetcher.py --companies Stripe Linear Ramp --role PM

Output: JSON array on stdout (same shape as naukri-scraper), status on stderr.
"""

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ats_platforms import fetch_jobs  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(ROOT, "config", "companies.json")
USER_CONFIG_PATH = os.path.join(ROOT, "config", "user.json")

DESC_CHARS = 400


def load_registry() -> dict:
    if not os.path.exists(REGISTRY_PATH):
        print("config/companies.json not found.", file=sys.stderr)
        print("Build it first:  python3 scripts/resolve-ats.py --from-config", file=sys.stderr)
        sys.exit(1)
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def load_target_companies() -> list[str]:
    try:
        with open(USER_CONFIG_PATH) as f:
            cfg = json.load(f)
        return cfg.get("target", {}).get("target_companies", []) or []
    except Exception:
        return []


def matches_role(title: str, role_filter: str) -> bool:
    """Loose OR match: any word of the filter appearing in the title counts."""
    if not role_filter:
        return True
    title_l = title.lower()
    return any(w.lower() in title_l for w in role_filter.split() if len(w) > 1)


def fetch_company(entry: dict, role_filter: str) -> list[dict]:
    name = entry.get("name", "?")
    platform = entry.get("platform", "none")
    slug = entry.get("slug", "")

    if platform == "none" or not slug:
        careers = entry.get("careers_url")
        if careers:
            print(f"  {name}: no public ATS — careers page: {careers}", file=sys.stderr)
        else:
            print(f"  {name}: unresolved, no careers_url set "
                  f"(fix: resolve-ats.py --set-careers \"{name}\" <url>)", file=sys.stderr)
        return []

    try:
        raw = fetch_jobs(platform, slug)
        if raw is None:
            print(f"  {name} ({platform}:{slug}): board did not respond — "
                  f"re-run resolve-ats.py --refresh", file=sys.stderr)
            return []

        jobs = []
        for j in raw:
            if not matches_role(j.get("title", ""), role_filter):
                continue
            jobs.append({
                "title": j.get("title", ""),
                "company": name,
                "experience": "",
                "location": j.get("location", ""),
                "salary": "Not disclosed",
                "description": (j.get("description") or "")[:DESC_CHARS],
                "posted": j.get("posted", ""),
                "tags": j.get("tags", []),
                "url": j.get("url", ""),
                "source": platform,
            })

        print(f"  {name} ({platform}:{slug}): {len(jobs)} matched / {len(raw)} total",
              file=sys.stderr)
        return jobs
    except Exception as e:
        print(f"  {name}: ERROR — {e}", file=sys.stderr)
        return []


def select_entries(reg: dict, args) -> list[dict]:
    companies = reg.get("companies", {})

    if args.all:
        wanted = list(companies.keys())
    elif args.from_config:
        targets = load_target_companies()
        if not targets:
            print("No target_companies in config/user.json", file=sys.stderr)
            sys.exit(1)
        wanted = [t.lower().strip() for t in targets]
    elif args.company:
        wanted = [args.company.lower().strip()]
    else:
        wanted = [c.lower().strip() for c in args.companies]

    entries, missing = [], []
    for key in wanted:
        entry = companies.get(key)
        if entry:
            entries.append(entry)
        else:
            missing.append(key)

    if missing:
        print(f"Not in registry: {', '.join(missing)}", file=sys.stderr)
        print(f"  Add them:  python3 scripts/resolve-ats.py --companies "
              f"{' '.join(repr(m) for m in missing)}", file=sys.stderr)

    return entries


def main() -> None:
    p = argparse.ArgumentParser(description="Fetch jobs from company ATS boards")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", action="store_true", help="Every company in config/companies.json")
    g.add_argument("--from-config", action="store_true",
                   help="Only config/user.json target_companies[]")
    g.add_argument("--company", help="Single company name")
    g.add_argument("--companies", nargs="+", help="Several company names")

    p.add_argument("--role", default="", help="Role keyword filter, e.g. 'Software Engineer'")
    p.add_argument("--workers", type=int, default=6, help="Parallel fetch threads (default 6)")
    args = p.parse_args()

    reg = load_registry()
    entries = select_entries(reg, args)
    if not entries:
        print("Nothing to fetch.", file=sys.stderr)
        print(json.dumps([]))
        return

    fetchable = [e for e in entries if e.get("platform", "none") != "none"]
    print(f"Fetching {len(fetchable)} ATS boards of {len(entries)} companies "
          f"(role filter: '{args.role or 'none'}')…", file=sys.stderr)

    all_jobs: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(fetch_company, e, args.role) for e in entries]
        for fut in as_completed(futures):
            all_jobs.extend(fut.result())

    skipped = len(entries) - len(fetchable)
    print(f"\nTotal: {len(all_jobs)} jobs from {len(fetchable)} boards"
          f"{f' ({skipped} companies have no public ATS)' if skipped else ''}", file=sys.stderr)
    print(json.dumps(all_jobs, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
