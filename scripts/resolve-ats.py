#!/usr/bin/env python3
"""
Career OS — ATS Resolver

Builds and maintains config/companies.json: the one place where
company -> ATS platform + slug lives. Nothing is hardcoded in this repo's code.

You give it company NAMES. It probes every supported ATS platform and writes
the resolved registry. Companies it can't resolve are recorded as
status="unresolved" with a careers_url you can fill in by hand.

Usage:
  # Resolve every company in config/user.json -> target.target_companies[]
  python3 scripts/resolve-ats.py --from-config

  # Add one or more companies by name (also appends them to the registry)
  python3 scripts/resolve-ats.py --company "Zerodha"
  python3 scripts/resolve-ats.py --companies Stripe Linear Ramp

  # Re-verify everything already in the registry (run monthly — boards move)
  python3 scripts/resolve-ats.py --refresh

  # Manual override when auto-discovery can't find it
  python3 scripts/resolve-ats.py --set "Acme Corp" greenhouse acmecorp
  python3 scripts/resolve-ats.py --set-careers "Razorpay" https://razorpay.com/careers

  # See what's in the registry right now
  python3 scripts/resolve-ats.py --list
"""

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ats_platforms import (  # noqa: E402
    PLATFORMS, PROBE_ORDER, probe, slug_candidates, board_url,
    owner_name, names_match,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(ROOT, "config", "companies.json")
EXAMPLE_PATH = os.path.join(ROOT, "config", "companies.example.json")
USER_CONFIG_PATH = os.path.join(ROOT, "config", "user.json")

# Below this many postings, a resolved board is flagged low-confidence for review.
MIN_CONFIDENT_JOBS = 3


def key_of(name: str) -> str:
    return name.lower().strip()


def load_registry() -> dict:
    for path in (REGISTRY_PATH, EXAMPLE_PATH):
        if os.path.exists(path):
            try:
                with open(path) as f:
                    reg = json.load(f)
                if path == EXAMPLE_PATH:
                    print(f"No companies.json yet — seeding from {os.path.basename(path)}",
                          file=sys.stderr)
                    reg["companies"] = {}
                return reg
            except Exception as e:
                print(f"Could not read {path}: {e}", file=sys.stderr)
    return {"version": 1, "updated": "", "companies": {}}


def save_registry(reg: dict) -> None:
    reg["updated"] = date.today().isoformat()
    reg.setdefault("version", 1)
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    with open(REGISTRY_PATH, "w") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)
        f.write("\n")


def load_target_companies() -> list[str]:
    try:
        with open(USER_CONFIG_PATH) as f:
            cfg = json.load(f)
        return cfg.get("target", {}).get("target_companies", []) or []
    except Exception as e:
        print(f"Could not read config/user.json: {e}", file=sys.stderr)
        return []


def resolve_one(name: str) -> dict:
    """
    Probe every supported platform for this company and pick the best board.

    "Best" means most live jobs, not first hit. Large companies often keep a
    dormant Greenhouse or Workable account with zero postings while actually
    hiring through Workday — first-hit-wins would resolve them to the dead board
    and silently return no jobs forever.
    """
    today = date.today().isoformat()
    candidates = slug_candidates(name)
    hits: list[tuple[str, str, int]] = []  # (platform, slug, job_count)

    for platform in PROBE_ORDER:
        spec = PLATFORMS[platform]

        if spec.get("discover"):
            slug = spec["discover"](name)
            if slug:
                count = probe(platform, slug) or 0
                hits.append((platform, slug, count))
                if count > 0:
                    break  # a live Workday board is authoritative; stop here
            continue

        for slug in candidates:
            count = probe(platform, slug)
            if count is None:
                continue
            owner = owner_name(platform, slug)
            if owner and not names_match(name, owner):
                print(f"  {name}: skipping {platform}:{slug} — board belongs to "
                      f"'{owner}' (slug collision)", file=sys.stderr)
                continue
            hits.append((platform, slug, count))
            break  # one slug variant per platform is enough

    live = [h for h in hits if h[2] > 0]
    if live:
        platform, slug, count = max(live, key=lambda h: h[2])
        entry = {
            "name": name, "platform": platform, "slug": slug,
            "status": "verified", "jobs_seen": count,
            "board_url": board_url(platform, slug),
            "careers_url": "", "verified_at": today,
        }
        # A real corporate board essentially never carries one or two postings.
        # A tiny board usually means we hit a squatted slug or a demo account —
        # e.g. "google.recruitee.com" is a sample account that reports its own
        # company_name as "Google", so name matching alone can't catch it.
        if count < MIN_CONFIDENT_JOBS:
            entry["confidence"] = "low"
            entry["note"] = (f"Only {count} posting(s) on this board — likely a squatted "
                             f"slug or demo account, not the real company. Verify "
                             f"{entry['board_url']} and correct with --set / --set-careers.")
            print(f"  {name}: {platform}:{slug} ({count} jobs) — LOW CONFIDENCE, verify",
                  file=sys.stderr)
        else:
            print(f"  {name}: {platform}:{slug} ({count} jobs)", file=sys.stderr)
        return entry

    if hits:
        platform, slug, _ = hits[0]
        others = ", ".join(f"{p}:{s}" for p, s, _ in hits)
        print(f"  {name}: board exists but is empty ({others}) — "
              f"likely hiring elsewhere", file=sys.stderr)
        return {
            "name": name, "platform": platform, "slug": slug,
            "status": "empty", "jobs_seen": 0,
            "board_url": board_url(platform, slug),
            "careers_url": "",
            "note": f"Board found ({others}) but it lists zero jobs. The company is "
                    f"probably hiring through an ATS we can't reach. Set careers_url, "
                    f"or pin the real board with --set.",
            "verified_at": today,
        }

    print(f"  {name}: no public ATS board found — needs a careers_url", file=sys.stderr)
    return {
        "name": name, "platform": "none", "slug": "",
        "status": "unresolved", "jobs_seen": 0,
        "board_url": "", "careers_url": "",
        "note": f"Probed {', '.join(PROBE_ORDER)} — no board found. Likely an internal "
                f"ATS. Set careers_url with --set-careers, or pin with --set.",
        "verified_at": today,
    }


def resolve_many(names: list[str], workers: int = 6) -> dict[str, dict]:
    results: dict[str, dict] = {}
    print(f"Probing {len(names)} companies across {len(PLATFORMS)} ATS platforms…", file=sys.stderr)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(resolve_one, n): n for n in names}
        for fut in as_completed(futures):
            name = futures[fut]
            try:
                results[key_of(name)] = fut.result()
            except Exception as e:
                print(f"  {name}: ERROR — {e}", file=sys.stderr)
    return results


def merge(reg: dict, resolved: dict[str, dict], preserve_manual: bool = True) -> dict:
    """Merge resolved entries into the registry, keeping manual edits intact."""
    companies = reg.setdefault("companies", {})
    for k, entry in resolved.items():
        existing = companies.get(k, {})
        # Never clobber a hand-set careers_url or a manual override.
        if preserve_manual:
            if existing.get("status") == "manual":
                print(f"  {entry['name']}: keeping manual override", file=sys.stderr)
                continue
            if existing.get("careers_url") and not entry.get("careers_url"):
                entry["careers_url"] = existing["careers_url"]
        companies[k] = entry
    return reg


def print_summary(reg: dict) -> None:
    companies = reg.get("companies", {})
    live = [c for c in companies.values() if c.get("status") in ("verified", "manual")]
    empty = [c for c in companies.values() if c.get("status") == "empty"]
    unresolved = [c for c in companies.values() if c.get("status") == "unresolved"]
    needs_attention = empty + unresolved
    with_careers = [c for c in needs_attention if c.get("careers_url")]
    total_jobs = sum(c.get("jobs_seen", 0) for c in live)

    print("", file=sys.stderr)
    print(f"Registry: {len(companies)} companies — {total_jobs} jobs reachable", file=sys.stderr)
    print(f"  fetchable (live board)   : {len(live)}", file=sys.stderr)
    print(f"  board exists but empty   : {len(empty)}", file=sys.stderr)
    print(f"  no board found           : {len(unresolved)}", file=sys.stderr)
    print(f"  of those, careers_url set: {len(with_careers)}/{len(needs_attention)}",
          file=sys.stderr)

    by_platform: dict[str, int] = {}
    for c in live:
        by_platform[c.get("platform", "?")] = by_platform.get(c.get("platform", "?"), 0) + 1
    if by_platform:
        breakdown = ", ".join(f"{p}: {n}" for p, n in sorted(by_platform.items()))
        print(f"  by platform              : {breakdown}", file=sys.stderr)

    low_conf = [c for c in live if c.get("confidence") == "low"]
    if low_conf:
        print("", file=sys.stderr)
        print("LOW CONFIDENCE — verify these boards are really the right company:",
              file=sys.stderr)
        for c in sorted(low_conf, key=lambda x: x["name"]):
            print(f"  {c['name']}: {c['platform']}:{c['slug']} "
                  f"({c.get('jobs_seen', 0)} jobs) {c.get('board_url', '')}", file=sys.stderr)

    if needs_attention:
        names = ", ".join(sorted(c["name"] for c in needs_attention))
        print("", file=sys.stderr)
        print(f"Needs attention: {names}", file=sys.stderr)
        print('  Point at the careers page:  resolve-ats.py --set-careers "Name" https://…',
              file=sys.stderr)
        print('  Or pin the real board:      resolve-ats.py --set "Name" workday '
              '"tenant/wd5/SiteName"', file=sys.stderr)
    print("\nWritten to config/companies.json", file=sys.stderr)


def cmd_list(reg: dict) -> None:
    companies = reg.get("companies", {})
    if not companies:
        print("Registry is empty. Run: python3 scripts/resolve-ats.py --from-config", file=sys.stderr)
        return
    width = max(len(c.get("name", k)) for k, c in companies.items()) + 2
    for k in sorted(companies):
        c = companies[k]
        name = c.get("name", k)
        status = c.get("status", "?")
        if status in ("verified", "manual") and c.get("platform", "none") != "none":
            detail = f"{c['platform']}:{c['slug']}  ({c.get('jobs_seen', 0)} jobs)"
            if c.get("confidence") == "low":
                detail += "  [LOW CONFIDENCE — verify]"
        else:
            detail = c.get("careers_url") or "no careers_url set — job search will skip this"
        print(f"  {name:<{width}} {status:<11} {detail}", file=sys.stderr)


def main() -> None:
    p = argparse.ArgumentParser(description="Resolve companies to their ATS boards")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--from-config", action="store_true",
                   help="Resolve every company in config/user.json target_companies[]")
    g.add_argument("--company", help="Resolve and add a single company by name")
    g.add_argument("--companies", nargs="+", help="Resolve and add several companies by name")
    g.add_argument("--refresh", action="store_true",
                   help="Re-verify every company already in the registry")
    g.add_argument("--set", nargs=3, metavar=("NAME", "PLATFORM", "SLUG"),
                   help="Manually pin a company to a platform+slug")
    g.add_argument("--set-careers", nargs=2, metavar=("NAME", "URL"),
                   help="Set the careers page URL for a company with no public ATS")
    g.add_argument("--list", action="store_true", help="Print the current registry")

    p.add_argument("--workers", type=int, default=6, help="Parallel probe threads (default 6)")
    args = p.parse_args()

    reg = load_registry()
    today = date.today().isoformat()

    if args.list:
        cmd_list(reg)
        return

    if args.set:
        name, platform, slug = args.set
        if platform not in PLATFORMS and platform != "none":
            print(f"Unknown platform '{platform}'. Supported: {', '.join(PLATFORMS)}", file=sys.stderr)
            sys.exit(1)
        count = probe(platform, slug) if platform != "none" else None
        reg.setdefault("companies", {})[key_of(name)] = {
            "name": name,
            "platform": platform,
            "slug": slug,
            "status": "manual",
            "jobs_seen": count or 0,
            "board_url": board_url(platform, slug),
            "careers_url": reg.get("companies", {}).get(key_of(name), {}).get("careers_url", ""),
            "verified_at": today,
        }
        save_registry(reg)
        verdict = f"{count} jobs" if count is not None else "board did not respond — pinned anyway"
        print(f"Pinned {name} -> {platform}:{slug} ({verdict})", file=sys.stderr)
        return

    if args.set_careers:
        name, url = args.set_careers
        companies = reg.setdefault("companies", {})
        entry = companies.get(key_of(name), {
            "name": name, "platform": "none", "slug": "",
            "status": "unresolved", "jobs_seen": 0, "board_url": "",
        })
        entry["careers_url"] = url
        entry["verified_at"] = today
        companies[key_of(name)] = entry
        save_registry(reg)
        print(f"Set careers URL for {name} -> {url}", file=sys.stderr)
        return

    if args.from_config:
        names = load_target_companies()
        if not names:
            print("No target_companies in config/user.json. Add them there first.", file=sys.stderr)
            sys.exit(1)
    elif args.refresh:
        names = [c.get("name", k) for k, c in reg.get("companies", {}).items()
                 if c.get("status") != "manual"]
        if not names:
            print("Registry is empty — nothing to refresh.", file=sys.stderr)
            sys.exit(1)
    elif args.company:
        names = [args.company]
    else:
        names = args.companies

    resolved = resolve_many(names, workers=args.workers)
    reg = merge(reg, resolved)
    save_registry(reg)
    print_summary(reg)


if __name__ == "__main__":
    main()
