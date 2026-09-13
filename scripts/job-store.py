#!/usr/bin/env python3
"""
Career OS — Job Store

Persistent memory for job listings, so a daily hunt shows what is actually new
rather than re-presenting the same few thousand rows every morning.

DIVISION OF LABOUR — this matters:

  This script owns FACTS, and nothing else. Which listings exist, when each was
  first and last seen, what the user did with it, whether it is still live. These
  are objective and must never be guessed at.

  Claude owns JUDGEMENT. Whether a role fits, whether it resembles something the
  user already passed on, whether it is worth surfacing. `context` hands Claude the
  user's decision history in plain form so it can reason over it. There is
  deliberately no keyword scoring here: counting title words produced nonsense like
  treating "engineering" as a dislike because the user dismissed one employer.

STORAGE LAYOUT

  data/market/
    job-index.json          slim index: id -> status + dates. Small, rewritten daily.
    runs/YYYY-MM-DD.json    what was fetched that day. Written once, never modified.
    jobs/YYYY-MM-DD.json    full JD text for listings shown that day, keyed by id.

  The daily run files exist for git's sake as much as yours. A single index
  rewritten every day makes git store a fresh copy of the whole thing daily —
  hundreds of megabytes of history for a few megabytes of content. Immutable
  per-day files are stored once.

STATUS VOCABULARY

  new         fetched, never shown
  shown       presented, awaiting a reaction
  interested  worth pursuing
  saved       keep for later
  pinned      keep at the top
  applied     applied to — kept forever, never pruned
  stale       user rejected it — never shown again, but the record is kept
  expired     gone from the market (distinct from stale: nobody rejected it)

Usage:
  python3 scripts/find-jobs.py --limit 0 | python3 scripts/job-store.py ingest --full-run --new-only --limit 25
  python3 scripts/job-store.py mark applied "Cisco" "Senior Software Engineer"
  python3 scripts/job-store.py mark stale "Walt Disney" --all
  python3 scripts/job-store.py context          # decision history, for Claude to reason over
  python3 scripts/job-store.py stats
  python3 scripts/job-store.py runs             # what was fetched on each day
  python3 scripts/job-store.py prune --days 90
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKET = os.path.join(ROOT, "data", "market")
INDEX_PATH = os.path.join(MARKET, "job-index.json")
RUNS_DIR = os.path.join(MARKET, "runs")
JD_DIR = os.path.join(MARKET, "jobs")

# Never shown again once set.
HIDDEN = {"applied", "stale", "expired"}
# Survives every prune — this is the user's application history.
PERMANENT = {"applied"}
# User-set states meaning "I want this".
WANTED = {"interested", "saved", "pinned"}

EXPIRE_AFTER_MISSES = 2
SIZE_WARN_KB = 3000


def job_id(job: dict) -> str:
    """Stable identity across runs. URL minus tracking params, else company+title."""
    url = (job.get("url") or "").split("?")[0].rstrip("/")
    basis = url or f"{job.get('company','')}|{job.get('title','')}".lower()
    return hashlib.sha1(basis.encode()).hexdigest()[:16]


def load() -> dict:
    try:
        with open(INDEX_PATH) as f:
            return json.load(f)
    except Exception:
        return {"version": 2, "runs": 0, "jobs": {}}


def save(store: dict) -> None:
    os.makedirs(MARKET, exist_ok=True)
    with open(INDEX_PATH, "w") as f:
        json.dump(store, f, indent=1, ensure_ascii=False)
        f.write("\n")


def write_run(day: str, payload: dict) -> str:
    """One immutable file per day. Re-running the same day merges into it."""
    os.makedirs(RUNS_DIR, exist_ok=True)
    path = os.path.join(RUNS_DIR, f"{day}.json")
    existing = {}
    if os.path.exists(path):
        try:
            with open(path) as f:
                existing = json.load(f)
        except Exception:
            existing = {}
    merged_ids = sorted(set(existing.get("fetched_ids", [])) | set(payload["fetched_ids"]))
    out = {
        "date": day,
        "runs_today": existing.get("runs_today", 0) + 1,
        "fetched": len(merged_ids),
        "new_this_day": sorted(set(existing.get("new_this_day", [])) | set(payload["new_this_day"])),
        "sources": sorted(set(existing.get("sources", [])) | set(payload["sources"])),
        "fetched_ids": merged_ids,
    }
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
        f.write("\n")
    return path


JD_FIELDS = ("title", "company", "location", "url", "source", "posted",
             "salary", "experience", "description", "tags")


def cache_jds(shown: list[dict], day: str) -> set[str]:
    """
    Keep full JD text for listings shown on a given day, in one file per day.

    One file per job named by hash was unbrowsable — twelve Cisco roles became
    twelve opaque filenames. A day file lines up with runs/YYYY-MM-DD.json, reads
    in one place, and git still stores each day once. Returns the ids cached.
    """
    rows = {j["id"]: {k: j.get(k) for k in JD_FIELDS}
            for j in shown if (j.get("description") or "").strip()}
    if not rows:
        return set()
    os.makedirs(JD_DIR, exist_ok=True)
    path = os.path.join(JD_DIR, f"{day}.json")
    existing = {}
    if os.path.exists(path):
        try:
            with open(path) as f:
                existing = json.load(f)
        except Exception:
            existing = {}
    existing.update(rows)
    with open(path, "w") as f:
        json.dump(dict(sorted(existing.items(), key=lambda kv: (kv[1].get("company") or "", kv[1].get("title") or ""))),
                  f, indent=1, ensure_ascii=False)
        f.write("\n")
    return set(rows)


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
    jobs = store["jobs"]
    seen_ids, new_ids, sources = set(), [], set()
    fresh, returning, suppressed = [], [], 0

    for job in incoming:
        jid = job_id(job)
        seen_ids.add(jid)
        if job.get("source"):
            sources.add(job["source"])
        rec = jobs.get(jid)

        if rec is None:
            rec = {"id": jid, "title": job.get("title", ""),
                   "company": job.get("company", ""), "url": job.get("url", ""),
                   "source": job.get("source", ""), "location": job.get("location", ""),
                   "first_seen": today, "last_seen": today,
                   "status": "new", "seen_count": 0, "misses": 0}
            jobs[jid] = rec
            new_ids.append(jid)
            is_new = True
        else:
            rec["last_seen"] = today
            rec["misses"] = 0
            if rec["status"] == "expired":      # reappeared, so it is live again
                rec["status"] = "shown"
            is_new = rec["status"] == "new"

        # Kept so `view` can rank and split the collected feed without re-fetching.
        rec["score"] = job.get("score", rec.get("score", 0))
        rec["track"] = job.get("track", rec.get("track", ""))

        if rec["status"] in HIDDEN:
            suppressed += 1
            continue

        job = dict(job)
        job["id"] = jid
        job["status"] = rec["status"]
        job["first_seen"] = rec["first_seen"]
        (fresh if is_new else returning).append(job)

    # Absence is only evidence when the run actually covered the market.
    expired_now = 0
    if args.full_run:
        for jid, rec in jobs.items():
            if jid in seen_ids or rec["status"] in HIDDEN or rec["status"] in WANTED:
                continue
            rec["misses"] = rec.get("misses", 0) + 1
            if rec["misses"] >= EXPIRE_AFTER_MISSES:
                rec["status"] = "expired"
                expired_now += 1

    out = fresh if args.new_only else fresh + returning
    out.sort(key=lambda j: -j.get("score", 0))
    if args.limit:
        out = out[:args.limit]

    for job in out:
        rec = jobs[job["id"]]
        rec["seen_count"] = rec.get("seen_count", 0) + 1
        if rec["status"] == "new":
            rec["status"] = "shown"
    for jid in cache_jds(out, today):
        jobs[jid]["jd_day"] = today

    save(store)
    run_path = write_run(today, {"fetched_ids": sorted(seen_ids),
                                 "new_this_day": new_ids,
                                 "sources": sorted(sources)})

    print(f"Run #{store['runs']} ({today}): {len(incoming)} in -> "
          f"{len(fresh)} new, {len(returning)} returning, {suppressed} hidden "
          f"(applied/stale/expired)", file=sys.stderr)
    if args.full_run and expired_now:
        print(f"Expired {expired_now} listings no longer in the market", file=sys.stderr)
    print(f"Returning {len(out)}" + (" (new only)" if args.new_only else "")
          + f" · day file: {os.path.relpath(run_path, ROOT)}", file=sys.stderr)
    warn_size()
    print(json.dumps(out, ensure_ascii=False, indent=2))


def warn_size() -> None:
    try:
        kb = os.path.getsize(INDEX_PATH) / 1024
    except OSError:
        return
    if kb > SIZE_WARN_KB:
        print(f"\nThe index is {kb/1024:.1f} MB. Consider: "
              f"job-store.py prune --days 90", file=sys.stderr)


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
        print(f"{len(matches)} matched — narrow it, or pass --all:", file=sys.stderr)
        for j in matches[:10]:
            print(f"  {j['company']} — {j['title'][:60]}", file=sys.stderr)
        sys.exit(1)
    for j in matches:
        j["status"] = args.status
        j["status_set"] = date.today().isoformat()
        if args.reason:
            j["reason"] = args.reason
        j["bulk"] = len(matches) > 1
    save(store)
    note = f" — {args.reason}" if args.reason else ""
    print(f"Marked {len(matches)} listing(s) as {args.status}{note}", file=sys.stderr)


def cmd_context(args) -> None:
    """
    Emit the user's decision history for Claude to reason over.

    Deliberately raw. No scoring, no keyword counts — Claude reads the actual
    titles the user accepted and rejected and forms its own view, which is the
    whole point of keeping judgement out of this script.
    """
    store = load()
    jobs = store["jobs"].values()
    buckets = {"applied": [], "stale": [], "interested": [], "saved": [], "pinned": []}
    for j in jobs:
        s = j.get("status")
        if s in buckets:
            buckets[s].append(j)

    if not any(buckets.values()):
        print("No decisions recorded yet — nothing to learn from.", file=sys.stderr)
        return

    print("# Decision history\n", file=sys.stderr)
    for name in ("applied", "interested", "saved", "pinned", "stale"):
        rows = buckets[name]
        if not rows:
            continue
        bulk = sum(1 for r in rows if r.get("bulk"))
        hdr = f"## {name} ({len(rows)})"
        if bulk:
            hdr += f" — {bulk} from bulk company rejections, weak signal about the role"
        print(hdr, file=sys.stderr)
        by_company: dict[str, list[str]] = {}
        for r in rows:
            by_company.setdefault(r.get("company", "?"), []).append(r.get("title", ""))
        for comp, titles in sorted(by_company.items(), key=lambda x: -len(x[1]))[:12]:
            sample = "; ".join(t[:54] for t in titles[:3])
            more = f" (+{len(titles)-3} more)" if len(titles) > 3 else ""
            print(f"  {comp} x{len(titles)}: {sample}{more}", file=sys.stderr)
        reasons = {r["reason"] for r in rows if r.get("reason")}
        if reasons:
            print(f"  reasons given: {'; '.join(sorted(reasons))}", file=sys.stderr)
        print("", file=sys.stderr)

    print("Use this to judge new listings. A bulk company rejection says "
          "'not this employer' — it says nothing about the role type.", file=sys.stderr)


def cmd_stats(args) -> None:
    store = load()
    jobs = store["jobs"]
    counts: dict[str, int] = {}
    for j in jobs.values():
        counts[j.get("status", "?")] = counts.get(j.get("status", "?"), 0) + 1
    print(f"Job store — {len(jobs)} listings across {store.get('runs',0)} runs",
          file=sys.stderr)
    for s in ("new", "shown", "interested", "saved", "pinned", "applied",
              "stale", "expired"):
        if counts.get(s):
            print(f"  {s:12} {counts[s]}", file=sys.stderr)
    cutoff = (date.today() - timedelta(days=7)).isoformat()
    print(f"\n  first seen in the last 7 days: "
          f"{sum(1 for j in jobs.values() if j.get('first_seen','') >= cutoff)}",
          file=sys.stderr)
    try:
        print(f"  index size: {os.path.getsize(INDEX_PATH)/1024:.0f} KB", file=sys.stderr)
    except OSError:
        pass
    warn_size()


VIEW_FILTERS = {
    "feed": "Current feed",
    "shortlist": "Shortlist",
    "stale": "Stale — passed on",
    "applied": "Applied",
    "expired": "Expired — gone from the market",
    "all": "All collected jobs",
}


def _cell(text, width: int) -> str:
    s = " ".join(str(text or "").split()).replace("|", "\\|")
    return s if len(s) <= width else s[:width - 1].rstrip() + "…"


def cmd_view(args) -> None:
    """
    Read-only view of what is already collected. Never fetches, never spends a
    connector call, never changes status — only `find jobs` gathers new listings.
    """
    store = load()
    jobs = list(store["jobs"].values())
    if not jobs:
        print("Nothing collected yet — run `find jobs` first.", file=sys.stderr)
        return

    latest = max(j.get("last_seen", "") for j in jobs)
    f = args.filter
    if f == "feed":
        # The most recent collection, minus anything already decided on.
        rows = [j for j in jobs if j.get("status") in ("new", "shown")
                and j.get("last_seen") == latest]
    elif f == "shortlist":
        rows = [j for j in jobs if j.get("status") in WANTED]
    elif f == "all":
        rows = jobs
    else:
        rows = [j for j in jobs if j.get("status") == f]

    if args.company:
        c = args.company.lower()
        rows = [j for j in rows if c in (j.get("company") or "").lower()]

    pin_first = {"pinned": 0, "interested": 1, "saved": 2}
    rows.sort(key=lambda j: (pin_first.get(j.get("status"), 3), -(j.get("score") or 0)))
    total = len(rows)
    rows = rows[:args.limit] if args.limit else rows

    if args.format == "json":
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    jd_days: dict[str, dict] = {}

    def requirements(j: dict) -> str:
        day = j.get("jd_day")
        if not day:
            return ""
        if day not in jd_days:
            try:
                with open(os.path.join(JD_DIR, f"{day}.json")) as fh:
                    jd_days[day] = json.load(fh)
            except Exception:
                jd_days[day] = {}
        text = (jd_days[day].get(j["id"]) or {}).get("description", "") or ""
        # Older cache entries hold a bare requisition ID instead of JD text.
        return text if re.search(r"[A-Za-z]{3,}\s+[A-Za-z]{2,}", text) else ""

    show_status = f in ("shortlist", "all")
    detail_hdr = "Reason" if f == "stale" else "Key requirements"

    def table(items: list[dict]) -> list[str]:
        hdr = ["#", "Score", "Role", "Company", "Location"]
        if show_status:
            hdr.append("Status")
        hdr += [detail_hdr, "Apply"]
        out = ["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
        for i, j in enumerate(items, 1):
            detail = j.get("reason", "") if f == "stale" else requirements(j)
            cells = [str(i), str(j.get("score") or "—"), _cell(j.get("title"), 40),
                     _cell(j.get("company"), 22), _cell(j.get("location"), 24)]
            if show_status:
                cells.append(j.get("status", ""))
            cells += [_cell(detail, 70) or "—",
                      f"[Apply]({j['url']})" if j.get("url") else "—"]
            out.append("| " + " | ".join(cells) + " |")
        return out

    label = VIEW_FILTERS[f]
    shown = f"{len(rows)} of {total}" if len(rows) < total else str(total)
    lines = [f"## {label} — {shown} jobs · collected as of {latest}", ""]

    if not rows:
        lines.append("_Nothing here._")
    elif f == "feed" and any(j.get("track") for j in rows):
        for track, title in (("targeted", "🎯 Your target companies"),
                             ("discovery", "🔎 Discovery")):
            part = [j for j in rows if j.get("track") == track]
            if part:
                lines += [f"### {title}", ""] + table(part) + [""]
        untracked = [j for j in rows if not j.get("track")]
        if untracked:
            lines += ["### Unclassified — collected before tracks were recorded", ""] \
                     + table(untracked) + [""]
    else:
        lines += table(rows)

    print("\n".join(lines).rstrip())


def cmd_runs(args) -> None:
    if not os.path.isdir(RUNS_DIR):
        print("No runs recorded yet.", file=sys.stderr)
        return
    files = sorted(os.listdir(RUNS_DIR), reverse=True)[:args.limit]
    print(f"Fetch history — {len(os.listdir(RUNS_DIR))} day(s) recorded", file=sys.stderr)
    for fn in files:
        try:
            with open(os.path.join(RUNS_DIR, fn)) as f:
                d = json.load(f)
        except Exception:
            continue
        print(f"  {d['date']}  fetched {d['fetched']:>5}  "
              f"new {len(d.get('new_this_day', [])):>4}  "
              f"runs {d.get('runs_today',1)}  "
              f"sources: {', '.join(d.get('sources', []))}", file=sys.stderr)


def cmd_prune(args) -> None:
    store = load()
    cutoff = (date.today() - timedelta(days=args.days)).isoformat()
    jobs = store["jobs"]
    removed: dict[str, int] = {}
    keep: dict[str, dict] = {}

    for jid, j in jobs.items():
        status = j.get("status", "")
        last = j.get("status_set") or j.get("last_seen", "")
        if status in PERMANENT or status in WANTED or last >= cutoff:
            keep[jid] = j
            continue
        if status in ("expired", "stale", "shown", "new"):
            removed[status] = removed.get(status, 0) + 1
        else:
            keep[jid] = j

    if not removed:
        print(f"Nothing older than {args.days} days to prune.", file=sys.stderr)
        return

    total = sum(removed.values())
    detail = ", ".join(f"{k} {v}" for k, v in sorted(removed.items()))
    if args.dry_run:
        print(f"Would prune {total} listing(s) older than {args.days} days: {detail}",
              file=sys.stderr)
        print("  applied and interested/saved/pinned are never pruned.", file=sys.stderr)
        return

    store["jobs"] = keep
    save(store)
    print(f"Pruned {total} listing(s) older than {args.days} days: {detail}",
          file=sys.stderr)
    print(f"  {len(keep)} kept (applied and wanted listings are never pruned)",
          file=sys.stderr)


def main() -> None:
    p = argparse.ArgumentParser(description="Persistent job listing memory")
    sub = p.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("ingest", help="Read jobs JSON on stdin, annotate and persist")
    i.add_argument("--new-only", action="store_true")
    i.add_argument("--full-run", action="store_true",
                   help="Run covered the whole market — absent listings count as missing")
    i.add_argument("--limit", type=int, default=0)
    i.set_defaults(fn=cmd_ingest)

    m = sub.add_parser("mark", help="Record a decision on a listing")
    m.add_argument("status", choices=["interested", "saved", "pinned", "applied",
                                      "stale", "shown"])
    m.add_argument("company", nargs="?", default="")
    m.add_argument("title", nargs="?", default="")
    m.add_argument("--url")
    m.add_argument("--all", action="store_true")
    m.add_argument("--reason", help="Why, in the user's own words — fed to Claude via `context`")
    m.set_defaults(fn=cmd_mark)

    c = sub.add_parser("context", help="Decision history for Claude to reason over")
    c.set_defaults(fn=cmd_context)

    s = sub.add_parser("stats", help="Counts by status")
    s.set_defaults(fn=cmd_stats)

    v = sub.add_parser("view", help="Show collected jobs — read-only, never fetches")
    v.add_argument("--filter", choices=list(VIEW_FILTERS), default="feed")
    v.add_argument("--company", default="")
    v.add_argument("--limit", type=int, default=25)
    v.add_argument("--format", choices=["md", "json"], default="md")
    v.set_defaults(fn=cmd_view)

    r = sub.add_parser("runs", help="What was fetched on each day")
    r.add_argument("--limit", type=int, default=14)
    r.set_defaults(fn=cmd_runs)

    pr = sub.add_parser("prune", help="Drop old listings (never applied or wanted)")
    pr.add_argument("--days", type=int, required=True)
    pr.add_argument("--dry-run", action="store_true")
    pr.set_defaults(fn=cmd_prune)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
