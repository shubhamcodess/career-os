#!/usr/bin/env python3
"""
Career OS — Find Jobs (single entry point)

One command that fans out across every source Career OS can reach, merges the
results, deduplicates, scores them against the user's profile, and writes the
ranked feed.

Two of the sources are not reachable from a script: Dice, Indeed and ZipRecruiter
are MCP connectors that only Claude can call. So this script covers everything
scriptable (the ATS registry and Naukri) and accepts connector results via
--merge, letting Claude hand them in. The merge, dedupe, scoring and ranking then
happen in exactly one place regardless of where a listing came from.

Usage:
  # Everything scriptable
  python3 scripts/find-jobs.py --limit 10

  # Narrow it
  python3 scripts/find-jobs.py --role "Software Engineer" --location Bangalore --limit 10

  # Include Naukri (slower — browser automation)
  python3 scripts/find-jobs.py --with-naukri --limit 10

  # Fold in connector results Claude fetched
  python3 scripts/find-jobs.py --merge /tmp/dice.json --merge /tmp/indeed.json --limit 10

  # Write the feed file as well as stdout
  python3 scripts/find-jobs.py --limit 10 --write-feed
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_CONFIG = os.path.join(ROOT, "config", "user.json")
FEED_PATH = os.path.join(ROOT, "data", "market", "job-feed.md")
PY = sys.executable


def load_config() -> dict:
    try:
        with open(USER_CONFIG) as f:
            return json.load(f)
    except Exception:
        return {}


def run_script(args: list[str], label: str) -> list[dict]:
    """Run a Career OS script and parse its JSON stdout."""
    try:
        proc = subprocess.run([PY] + args, capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        print(f"  {label}: timed out", file=sys.stderr)
        return []
    if proc.returncode != 0:
        tail = (proc.stderr or "").strip().splitlines()[-1:] or ["no detail"]
        print(f"  {label}: failed — {tail[0]}", file=sys.stderr)
        return []
    try:
        jobs = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        print(f"  {label}: unparseable output", file=sys.stderr)
        return []
    print(f"  {label}: {len(jobs)} jobs", file=sys.stderr)
    return jobs


def normalize(job: dict) -> dict:
    """Force every source into the same shape; tolerate partial connector rows."""
    return {
        "title": (job.get("title") or "").strip(),
        "company": (job.get("company") or "").strip(),
        "location": (job.get("location") or "").strip(),
        "experience": (job.get("experience") or "").strip(),
        "salary": (job.get("salary") or "Not disclosed").strip(),
        "description": (job.get("description") or "").strip(),
        "posted": (job.get("posted") or "").strip(),
        "tags": job.get("tags") or [],
        "url": (job.get("url") or "").strip(),
        "source": (job.get("source") or "unknown").strip(),
        "match_confidence": job.get("match_confidence"),
    }


def dedupe(jobs: list[dict]) -> list[dict]:
    """
    Same role posted to two boards is one job.

    URL is the strong key, but the same listing reaches us with different tracking
    URLs from different connectors, so company+title is the fallback.
    """
    seen_urls: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    out: list[dict] = []
    for j in jobs:
        url_key = j["url"].split("?")[0].rstrip("/")
        pair_key = (re.sub(r"[^a-z0-9]", "", j["company"].lower()),
                    re.sub(r"[^a-z0-9]", "", j["title"].lower()))
        if url_key and url_key in seen_urls:
            continue
        if pair_key[0] and pair_key[1] and pair_key in seen_pairs:
            continue
        if url_key:
            seen_urls.add(url_key)
        if pair_key[0] and pair_key[1]:
            seen_pairs.add(pair_key)
        out.append(j)
    return out


def score(job: dict, cfg: dict) -> tuple[int, list[str]]:
    """Score 0-100 against the user's profile. Returns (score, reasons)."""
    target = cfg.get("target", {})
    roles = [r.lower() for r in target.get("target_roles", [])]
    companies = [c.lower() for c in target.get("target_companies", [])]
    locations = [l.lower().split(",")[0].strip() for l in target.get("target_locations", [])]
    keywords = [k.lower() for k in target.get("domain_keywords", [])]

    title = job["title"].lower()
    loc = job["location"].lower()
    comp = job["company"].lower()
    blob = f"{title} {job['description'].lower()} {' '.join(str(t).lower() for t in job['tags'])}"

    pts, why = 0, []

    if any(r in title for r in roles):
        pts += 30
        why.append("role title match")
    elif any(w in title for w in ("engineer", "developer", "swe")):
        pts += 18
        why.append("adjacent role title")

    if any(c and c in comp for c in companies):
        pts += 25
        why.append("target company")

    if any(l and l in loc for l in locations):
        pts += 20
        why.append("target location")
    elif "remote" in loc:
        pts += 12
        why.append("remote")

    hits = [k for k in keywords if k in blob]
    if hits:
        pts += min(15, 5 * len(hits))
        why.append(f"domain: {', '.join(hits[:3])}")

    if any(w in title for w in ("senior", "sr.", "sr ", "staff", "lead")):
        pts += 10
        why.append("seniority fit")
    if any(w in title for w in ("intern", "graduate", "fresher", "trainee")):
        pts -= 25
        why.append("junior — likely mismatch")

    if job.get("match_confidence") == "partial":
        pts -= 15
        why.append("unverified company match")

    return max(0, min(100, pts)), why


def to_markdown(jobs: list[dict], sources: list[str]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = ["# Live Job Feed", f"_Last updated: {now}_",
             f"_Sources: {', '.join(sources) or 'none'}_", ""]
    bands = [("🔥 Strong matches (75+)", 75, 101),
             ("✅ Good matches (50–74)", 50, 75),
             ("📋 Worth watching (30–49)", 30, 50)]
    for label, lo, hi in bands:
        band = [j for j in jobs if lo <= j["score"] < hi]
        if not band:
            continue
        lines.append(f"## {label}")
        lines.append("")
        for j in band:
            lines.append(f"### {j['company']} — {j['title']}")
            lines.append(f"- Score: {j['score']}/100 · {', '.join(j['why']) or '—'}")
            lines.append(f"- Location: {j['location'] or '—'} | Source: {j['source']}"
                         + (f" | Posted: {j['posted']}" if j["posted"] else ""))
            if j["experience"]:
                lines.append(f"- Experience: {j['experience']}")
            if j["url"]:
                lines.append(f"- Apply: {j['url']}")
            if j["description"]:
                lines.append(f"- JD: {j['description'][:300]}")
            lines.append("")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(description="Fan out across every job source and rank")
    p.add_argument("--role", default="", help="Role filter (default: first target_role)")
    p.add_argument("--location", default="", help="Location filter for Naukri")
    p.add_argument("--limit", type=int, default=0, help="Max jobs to output (0 = all)")
    p.add_argument("--with-naukri", action="store_true",
                   help="Include Naukri — slower, uses browser automation")
    p.add_argument("--no-ats", action="store_true", help="Skip the ATS registry")
    p.add_argument("--merge", action="append", default=[], metavar="FILE",
                   help="JSON file of connector results to fold in (repeatable)")
    p.add_argument("--write-feed", action="store_true",
                   help="Also write data/market/job-feed.md")
    args = p.parse_args()

    cfg = load_config()
    target = cfg.get("target", {})
    role = args.role or (target.get("target_roles") or ["Software Engineer"])[0]
    location = args.location or (
        (target.get("target_locations") or ["Bangalore"])[0].split(",")[0].strip())

    print(f"Searching: role='{role}' location='{location}'", file=sys.stderr)

    raw: list[dict] = []
    sources: list[str] = []

    if not args.no_ats:
        jobs = run_script([os.path.join(ROOT, "scripts", "ats-fetcher.py"),
                           "--all", "--role", role], "ATS registry")
        if jobs:
            sources.append("ATS")
        raw += jobs

    if args.with_naukri:
        jobs = run_script([os.path.join(ROOT, "scripts", "naukri-scraper.py"),
                           "--role", role, "--location", location, "--pages", "1"],
                          "Naukri")
        if jobs:
            sources.append("Naukri")
        raw += jobs

    for path in args.merge:
        try:
            with open(path) as f:
                jobs = json.load(f)
            label = os.path.splitext(os.path.basename(path))[0]
            print(f"  {label} (merged): {len(jobs)} jobs", file=sys.stderr)
            if jobs:
                sources.append(label)
            raw += jobs
        except Exception as e:
            print(f"  {path}: could not merge — {e}", file=sys.stderr)

    if not raw:
        print("\nNo jobs from any source.", file=sys.stderr)
        print(json.dumps([]))
        return

    jobs = dedupe([normalize(j) for j in raw])
    for j in jobs:
        j["score"], j["why"] = score(j, cfg)
    jobs.sort(key=lambda j: -j["score"])

    print(f"\n{len(raw)} fetched -> {len(jobs)} after dedupe", file=sys.stderr)
    if args.limit:
        jobs = jobs[:args.limit]
        print(f"Returning top {len(jobs)}", file=sys.stderr)

    by_source: dict[str, int] = {}
    for j in jobs:
        by_source[j["source"]] = by_source.get(j["source"], 0) + 1
    print("By source: " + ", ".join(f"{k}={v}" for k, v in sorted(by_source.items())),
          file=sys.stderr)

    if args.write_feed:
        os.makedirs(os.path.dirname(FEED_PATH), exist_ok=True)
        with open(FEED_PATH, "w") as f:
            f.write(to_markdown(jobs, sources))
        print(f"Wrote {FEED_PATH}", file=sys.stderr)

    print(json.dumps(jobs, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
