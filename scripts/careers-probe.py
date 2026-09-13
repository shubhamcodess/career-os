#!/usr/bin/env python3
"""
Career OS — Careers Page Probe

Last-resort discovery for companies that neither the ATS registry nor Naukri can
reach. Fetches a company's public careers page and looks for the ATS board it is
actually powered by, hiding in the page source.

This is a permanent fix, not a scrape. Careers pages are usually thin SPA shells
whose listings are loaded by JavaScript — scraping the rendered page gives you a
snapshot that breaks on the next redesign. But that same shell almost always
references its real backend, and that backend has a clean JSON API. Adobe's
careers page is a React app with no jobs in the HTML, yet the HTML names
"adobe.wd5.myworkdayjobs.com/external_experienced" — 500 jobs behind a stable API.

Usage:
  # One company (careers_url comes from config/companies.json)
  python3 scripts/careers-probe.py --company Adobe

  # Any URL directly
  python3 scripts/careers-probe.py --url https://careers.example.com

  # Every company with no fetchable board
  python3 scripts/careers-probe.py --all-unreachable

  # Pin whatever is found, instead of only printing the command
  python3 scripts/careers-probe.py --all-unreachable --apply

Nothing company-specific is hardcoded. Every candidate found is verified against
the live board before being reported.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ats_platforms import BROWSER_HEADERS, probe, board_url  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(ROOT, "config", "companies.json")
RESOLVER = os.path.join(ROOT, "scripts", "resolve-ats.py")

# Board references as they appear in careers-page source. Each pattern yields the
# pieces needed to build a registry slug for that platform.
BOARD_PATTERNS: list[tuple[str, str]] = [
    ("workday",
     r'https?://([a-z0-9-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([A-Za-z0-9_-]+)'),
    ("greenhouse", r'(?:boards|job-boards)\.greenhouse\.io/([a-zA-Z0-9_-]+)'),
    ("lever", r'jobs\.lever\.co/([a-zA-Z0-9_-]+)'),
    ("ashby", r'jobs\.ashbyhq\.com/([a-zA-Z0-9_-]+)'),
    ("smartrecruiters", r'jobs\.smartrecruiters\.com/([A-Za-z0-9_-]+)'),
    ("workable", r'apply\.workable\.com/([a-zA-Z0-9_-]+)'),
    ("recruitee", r'https?://([a-z0-9-]+)\.recruitee\.com'),
    ("pcsx", r'https?://([a-z0-9.-]+)/api/pcsx/search'),
    ("eightfold", r'https?://([a-z0-9.-]+)/api/apply/v2'),
]

# Platforms Career OS cannot fetch from yet. Worth reporting — knowing a company
# is on iCIMS tells you to stop probing and use Naukri or web search instead.
UNSUPPORTED_HINTS = {
    "icims": r'https?://([a-z0-9-]+)\.icims\.com',
    "phenom": r'phenompeople|/widgets\?',
    "successfactors": r'successfactors|jobs2web',
    "avature": r'avature\.net',
    "taleo": r'taleo\.net',
    "oracle-hcm": r'oraclecloud\.com/hcmUI',
}

# Slugs that appear on many sites but belong to the vendor, not the employer.
GENERIC_SLUGS = {"embed", "job-boards", "boards", "api", "v1", "v2", "www", "jobs"}


def load_registry() -> dict:
    try:
        with open(REGISTRY_PATH) as f:
            return json.load(f)
    except Exception as e:
        print(f"Could not read config/companies.json: {e}", file=sys.stderr)
        return {"companies": {}}


def fetch(url: str, timeout: int = 25) -> str | None:
    try:
        req = urllib.request.Request(url, headers=BROWSER_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return None


def candidates_from_html(html: str) -> list[tuple[str, str]]:
    """Extract (platform, slug) candidates referenced anywhere in the page."""
    found: list[tuple[str, str]] = []
    for platform, rx in BOARD_PATTERNS:
        for m in re.findall(rx, html):
            if platform == "workday":
                tenant, wd, site = m
                slug = f"{tenant}/{wd}/{site}"
            elif platform in ("eightfold", "pcsx"):
                host = m if isinstance(m, str) else m[0]
                domain = ".".join(host.split(".")[-2:])
                slug = f"{host}|{domain}"
            else:
                slug = m if isinstance(m, str) else m[0]
                if slug.lower() in GENERIC_SLUGS:
                    continue
            pair = (platform, slug)
            if pair not in found:
                found.append(pair)
    return found


def unsupported_from_html(html: str) -> list[str]:
    low = html.lower()
    return [name for name, rx in UNSUPPORTED_HINTS.items() if re.search(rx, low)]


def host_candidates(url: str) -> list[tuple[str, str]]:
    """
    Actively test the careers host for the API shapes that are mounted on the
    company's own domain rather than a vendor domain.

    Reading the HTML is not enough for these: Qualcomm's careers page builds
    "careers.qualcomm.com/api/pcsx/search" in JavaScript, so the string never
    appears in the page source — but the endpoint is live and serves 500 jobs.
    Probing the host directly costs two requests and catches that whole class.
    """
    try:
        host = urllib.parse.urlparse(url).netloc.lower()
    except Exception:
        return []
    if not host:
        return []
    parts = host.split(".")
    domain = ".".join(parts[-2:]) if len(parts) >= 2 else host
    return [("pcsx", f"{host}|{domain}"), ("eightfold", f"{host}|{domain}")]


def probe_company(name: str, url: str) -> dict:
    """Fetch a careers page and verify any board it references."""
    result = {"name": name, "url": url, "verified": [], "unsupported": [],
              "error": None, "candidates": 0}

    html = fetch(url)
    if html is None:
        result["error"] = "could not fetch (bot-blocked, redirect, or dead URL)"
        return result

    cands = candidates_from_html(html) + host_candidates(url)
    # Preserve order while dropping duplicates.
    cands = list(dict.fromkeys(cands))
    result["candidates"] = len(cands)
    result["unsupported"] = unsupported_from_html(html)

    # A reference is only useful if the board actually answers with jobs.
    for platform, slug in cands:
        count = probe(platform, slug)
        if count:
            result["verified"].append({"platform": platform, "slug": slug, "jobs": count})

    result["verified"].sort(key=lambda v: -v["jobs"])
    return result


def apply_pin(name: str, platform: str, slug: str) -> bool:
    try:
        out = subprocess.run(
            [sys.executable, RESOLVER, "--set", name, platform, slug],
            capture_output=True, text=True, timeout=180)
        print("   " + (out.stderr or out.stdout).strip(), file=sys.stderr)
        return out.returncode == 0
    except Exception as e:
        print(f"   pin failed: {e}", file=sys.stderr)
        return False


def report(r: dict, apply: bool) -> bool:
    name = r["name"]
    if r["error"]:
        print(f"  {name}: {r['error']}", file=sys.stderr)
        print(f"     -> ask Claude to open {r['url']} with WebFetch or the browser",
              file=sys.stderr)
        return False

    if r["verified"]:
        best = r["verified"][0]
        print(f"  {name}: FOUND {best['platform']}:{best['slug']} "
              f"({best['jobs']} jobs)", file=sys.stderr)
        if apply:
            return apply_pin(name, best["platform"], best["slug"])
        print(f'     -> resolve-ats.py --set "{name}" {best["platform"]} '
              f'"{best["slug"]}"', file=sys.stderr)
        return True

    if r["unsupported"]:
        print(f"  {name}: runs on {', '.join(r['unsupported'])} — not fetchable by "
              f"Career OS. Use Naukri or web search.", file=sys.stderr)
    elif r["candidates"]:
        print(f"  {name}: {r['candidates']} board reference(s) found but none "
              f"returned jobs", file=sys.stderr)
    else:
        print(f"  {name}: no ATS reference in page source "
              f"(likely fully client-rendered)", file=sys.stderr)
        print(f"     -> ask Claude to open {r['url']} with WebFetch or the browser",
              file=sys.stderr)
    return False


def main() -> None:
    p = argparse.ArgumentParser(description="Find the ATS board behind a careers page")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--company", help="Company name; careers_url read from the registry")
    g.add_argument("--url", help="Probe an arbitrary careers URL")
    g.add_argument("--all-unreachable", action="store_true",
                   help="Every registry company with no fetchable board")
    p.add_argument("--apply", action="store_true",
                   help="Pin what is found instead of only printing the command")
    p.add_argument("--workers", type=int, default=4)
    args = p.parse_args()

    reg = load_registry()
    companies = reg.get("companies", {})
    targets: list[tuple[str, str]] = []

    if args.url:
        targets = [(args.company or "(url)", args.url)]
    elif args.company:
        entry = companies.get(args.company.lower().strip())
        if not entry:
            print(f"{args.company} is not in the registry.", file=sys.stderr)
            sys.exit(1)
        if not entry.get("careers_url"):
            print(f"{args.company} has no careers_url. Set one:\n"
                  f'  resolve-ats.py --set-careers "{args.company}" https://…',
                  file=sys.stderr)
            sys.exit(1)
        targets = [(entry["name"], entry["careers_url"])]
    else:
        for c in companies.values():
            fetchable = (c.get("status") in ("verified", "manual")
                         and c.get("platform", "none") != "none")
            if not fetchable and c.get("careers_url"):
                targets.append((c["name"], c["careers_url"]))

    if not targets:
        print("Nothing to probe. Companies need a careers_url first.", file=sys.stderr)
        return

    print(f"Probing {len(targets)} careers page(s) for their real ATS board…",
          file=sys.stderr)

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(probe_company, n, u): n for n, u in targets}
        for fut in as_completed(futures):
            results.append(fut.result())

    wins = 0
    for r in sorted(results, key=lambda x: x["name"]):
        if report(r, args.apply):
            wins += 1

    print(f"\n{wins}/{len(targets)} companies resolved to a live board.", file=sys.stderr)
    if wins and not args.apply:
        print("Re-run with --apply to pin them automatically.", file=sys.stderr)


if __name__ == "__main__":
    main()
