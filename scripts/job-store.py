#!/usr/bin/env python3
"""
Career OS — Job Store

Persistent memory for job listings, so a daily job hunt shows what is actually new
rather than the same 2,000 rows every morning.

Without this, `find jobs` is stateless: it re-fetches the whole market each run and
re-presents everything, including roles already rejected or applied to. The signal
that matters daily — what appeared since yesterday — is buried.

What it tracks per listing:
  first_seen / last_seen   when it entered and was last confirmed live
  status                   new -> seen -> saved | applied | not_interested | expired
  seen_count               how many runs it has survived

Three behaviours fall out of that:
  Freshness   --new-only returns listings never shown before
  Lifecycle   applied / not_interested are never shown again
  Staleness   listings absent from a full run are expired — the feed tracks the
              live market instead of accumulating dead links

It also builds a taste profile from what the user rejects, and downranks similar
listings. That is a frequency count over rejected companies and title words, not a
model — it is meant to be inspectable and easy to reset.

Usage:
  # Ingest a run's results; prints them back annotated with status
  python3 scripts/find-jobs.py --limit 0 | python3 scripts/job-store.py ingest --full-run

  # Only what the user has never seen
  cat results.json | python3 scripts/job-store.py ingest --new-only

  # Lifecycle
  python3 scripts/job-store.py mark applied "Cisco" "Senior Software Engineer"
  python3 scripts/job-store.py mark not_interested --url "https://..."

  python3 scripts/job-store.py stats
  python3 scripts/job-store.py taste
  python3 scripts/job-store.py forget not_interested     # reset the taste profile
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE_PATH = os.path.join(ROOT, "data", "market", "job-index.json")

ACTIVE = {"new", "seen", "saved"}
CLOSED = {"applied", "not_interested", "expired"}

# A listing absent from this many consecutive full runs is treated as gone.
EXPIRE_AFTER_MISSES = 2
# Stop words that carry no signal when learning from rejected titles.
STOP = {"senior", "sr", "staff", "lead", "principal", "engineer", "software", "i",
        "ii", "iii", "the", "and", "of", "for", "a", "an", "to", "in", "at", "with"}


def job_id(job: dict) -> str:
    """
    Stable identity for a listing across runs.

    URL is the natural key but arrives with per-connector tracking parameters, so it
    is stripped to path before hashing. Listings with no URL fall back to
    company+title, which is weaker but keeps them addressable.
    """
    url = (job.get("url") or "").split("?")[0].rstrip("/")
    basis = url or f"{job.get('company','')}|{job.get('title','')}".lower()
    return hashlib.sha1(basis.encode()).hexdigest()[:16]


def load() -> dict:
    try:
        with open(STORE_PATH) as f:
            return json.load(f)
    except Exception:
        return {"version": 1, "runs": 0, "jobs": {}}


def save(store: dict) -> None:
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
    with open(STORE_PATH, "w") as f:
        json.dump(store, f, indent=1, ensure_ascii=False)
        f.write("\n")


def title_tokens(title: str) -> list[str]:
    words = re.split(r"[^a-z0-9+#]+", (title or "").lower())
    return [w for w in words if len(w) > 2 and w not in STOP]


def taste_profile(store: dict) -> dict:
    """
    Frequency counts over what the user rejected. Deliberately simple.

    Bulk rejections contribute a company signal but NOT title tokens. Rejecting a
    whole company in one go says "not this employer" — it says nothing about the
    roles. Counting those titles teaches the opposite: dismissing all 88 Disney
    listings would learn that "engineering", "product" and "platform" are dislikes,
    which then penalises every good job elsewhere.
    """
    companies: dict[str, int] = {}
    tokens: dict[str, int] = {}
    for j in store["jobs"].values():
        if j.get("status") != "not_interested":
            continue
        c = re.sub(r"[^a-z0-9]", "", (j.get("company") or "").lower())
        if c:
            companies[c] = companies.get(c, 0) + 1
        if j.get("bulk_reject"):
            continue
        for t in title_tokens(j.get("title", "")):
            tokens[t] = tokens.get(t, 0) + 1
    return {"companies": companies, "tokens": tokens}


def taste_penalty(job: dict, profile: dict) -> tuple[int, list[str]]:
    """Score adjustment from learned dislikes. Never hides a job, only downranks it."""
    pen, why = 0, []
    comp = re.sub(r"[^a-z0-9]", "", (job.get("company") or "").lower())
    n = profile["companies"].get(comp, 0)
    if n:
        pen += min(30, 10 * n)
        why.append(f"passed on {job.get('company')} {n}x")
    hits = [t for t in title_tokens(job.get("title", "")) if profile["tokens"].get(t, 0) >= 2]
    if hits:
        pen += min(20, 5 * len(hits))
        why.append(f"rejected before: {', '.join(hits[:3])}")
    return pen, why


def cmd_ingest(args) -> None:
    store = load()
    today = date.today().isoformat()
    try:
        incoming = json.load(sys.stdin)
    except Exception as e:
        print(f"Could not read JSON on stdin: {e}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(incoming, list):
        print("Expected a JSON array of jobs on stdin", file=sys.stderr)
        sys.exit(1)

    store["runs"] = store.get("runs", 0) + 1
    profile = taste_profile(store)
    jobs = store["jobs"]
    seen_ids: set[str] = set()
    fresh, returning, suppressed = [], [], 0

    for job in incoming:
        jid = job_id(job)
        seen_ids.add(jid)
        rec = jobs.get(jid)

        if rec is None:
            rec = {"id": jid, "title": job.get("title", ""),
                   "company": job.get("company", ""), "url": job.get("url", ""),
                   "source": job.get("source", ""), "location": job.get("location", ""),
                   "first_seen": today, "last_seen": today,
                   "status": "new", "seen_count": 0, "misses": 0}
            jobs[jid] = rec
            is_new = True
        else:
            rec["last_seen"] = today
            rec["misses"] = 0
            # A listing that reappears after being expired is live again.
            if rec["status"] == "expired":
                rec["status"] = "seen"
            is_new = rec["status"] == "new"

        job = dict(job)
        job["id"] = jid
        job["status"] = rec["status"]
        job["first_seen"] = rec["first_seen"]

        if rec["status"] in ("applied", "not_interested"):
            suppressed += 1
            continue

        pen, why = taste_penalty(job, profile)
        if pen:
            job["score"] = max(0, job.get("score", 0) - pen)
            job["why"] = (job.get("why") or []) + why

        (fresh if is_new else returning).append(job)

    # Anything not in this run is a miss. Only a full run is evidence of absence —
    # a --limit or --role filtered run legitimately omits most of the market.
    expired_now = 0
    if args.full_run:
        for jid, rec in jobs.items():
            if jid in seen_ids or rec["status"] in CLOSED:
                continue
            rec["misses"] = rec.get("misses", 0) + 1
            if rec["misses"] >= EXPIRE_AFTER_MISSES:
                rec["status"] = "expired"
                expired_now += 1

    out = fresh if args.new_only else fresh + returning
    out.sort(key=lambda j: -j.get("score", 0))
    if args.limit:
        out = out[:args.limit]

    # Showing a listing is what makes it no longer new.
    for job in out:
        rec = jobs[job["id"]]
        rec["seen_count"] = rec.get("seen_count", 0) + 1
        if rec["status"] == "new":
            rec["status"] = "seen"

    save(store)

    print(f"Run #{store['runs']}: {len(incoming)} in -> "
          f"{len(fresh)} new, {len(returning)} returning, "
          f"{suppressed} suppressed (applied/not interested)", file=sys.stderr)
    if args.full_run and expired_now:
        print(f"Expired {expired_now} listings no longer in the market", file=sys.stderr)
    print(f"Returning {len(out)}"
          + (" (new only)" if args.new_only else ""), file=sys.stderr)
    print(json.dumps(out, ensure_ascii=False, indent=2))


def find_records(store: dict, args) -> list[dict]:
    jobs = list(store["jobs"].values())
    if args.url:
        key = args.url.split("?")[0].rstrip("/")
        return [j for j in jobs if (j.get("url") or "").split("?")[0].rstrip("/") == key]
    out = jobs
    if args.company:
        c = args.company.lower()
        out = [j for j in out if c in (j.get("company") or "").lower()]
    if args.title:
        t = args.title.lower()
        out = [j for j in out if t in (j.get("title") or "").lower()]
    return out


def cmd_mark(args) -> None:
    store = load()
    matches = find_records(store, args)
    if not matches:
        print("No stored listing matched.", file=sys.stderr)
        sys.exit(1)
    if len(matches) > 1 and not args.all:
        print(f"{len(matches)} listings matched — narrow it, or pass --all:", file=sys.stderr)
        for j in matches[:10]:
            print(f"  {j['company']} — {j['title'][:60]}", file=sys.stderr)
        sys.exit(1)
    bulk = len(matches) > 1
    for j in matches:
        j["status"] = args.status
        j["status_set"] = date.today().isoformat()
        if args.status == "not_interested":
            j["bulk_reject"] = bulk
    save(store)
    note = "" if not bulk else "  (bulk — company signal only, titles not learned)"
    print(f"Marked {len(matches)} listing(s) as {args.status}{note}", file=sys.stderr)


def cmd_stats(args) -> None:
    store = load()
    jobs = store["jobs"]
    counts: dict[str, int] = {}
    for j in jobs.values():
        counts[j.get("status", "?")] = counts.get(j.get("status", "?"), 0) + 1
    print(f"Job store — {len(jobs)} listings tracked across {store.get('runs',0)} runs",
          file=sys.stderr)
    for s in ("new", "seen", "saved", "applied", "not_interested", "expired"):
        if counts.get(s):
            print(f"  {s:16} {counts[s]}", file=sys.stderr)

    cutoff = (date.today() - timedelta(days=7)).isoformat()
    recent = [j for j in jobs.values() if j.get("first_seen", "") >= cutoff]
    print(f"\n  appeared in the last 7 days: {len(recent)}", file=sys.stderr)


def cmd_taste(args) -> None:
    store = load()
    p = taste_profile(store)
    rejected = sum(1 for j in store["jobs"].values() if j.get("status") == "not_interested")
    if not rejected:
        print("No taste profile yet — nothing marked not_interested.", file=sys.stderr)
        return
    print(f"Taste profile — learned from {rejected} rejected listings", file=sys.stderr)
    if p["companies"]:
        top = sorted(p["companies"].items(), key=lambda x: -x[1])[:8]
        print("  companies: " + ", ".join(f"{c} x{n}" for c, n in top), file=sys.stderr)
    strong = sorted(((t, n) for t, n in p["tokens"].items() if n >= 2),
                    key=lambda x: -x[1])[:10]
    if strong:
        print("  title words: " + ", ".join(f"{t} x{n}" for t, n in strong), file=sys.stderr)
    print("\n  Applied as a score penalty only — never hides a listing outright.",
          file=sys.stderr)


def cmd_forget(args) -> None:
    store = load()
    n = 0
    for j in store["jobs"].values():
        if j.get("status") == args.status:
            j["status"] = "seen"
            n += 1
    save(store)
    print(f"Reset {n} listing(s) from {args.status} back to seen", file=sys.stderr)


def main() -> None:
    p = argparse.ArgumentParser(description="Persistent job listing memory")
    sub = p.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("ingest", help="Read jobs JSON on stdin, annotate and persist")
    i.add_argument("--new-only", action="store_true",
                   help="Return only listings never shown before")
    i.add_argument("--full-run", action="store_true",
                   help="This run covered the whole market — absent listings count as "
                        "missing and eventually expire")
    i.add_argument("--limit", type=int, default=0)
    i.set_defaults(fn=cmd_ingest)

    m = sub.add_parser("mark", help="Set lifecycle status on a listing")
    m.add_argument("status", choices=["saved", "applied", "not_interested", "seen"])
    m.add_argument("company", nargs="?", default="")
    m.add_argument("title", nargs="?", default="")
    m.add_argument("--url")
    m.add_argument("--all", action="store_true", help="Apply to every match")
    m.set_defaults(fn=cmd_mark)

    s = sub.add_parser("stats", help="Counts by status")
    s.set_defaults(fn=cmd_stats)

    t = sub.add_parser("taste", help="Show what has been learned from rejections")
    t.set_defaults(fn=cmd_taste)

    f = sub.add_parser("forget", help="Reset a status back to seen")
    f.add_argument("status", choices=["not_interested", "applied", "saved", "expired"])
    f.set_defaults(fn=cmd_forget)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
