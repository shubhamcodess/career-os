#!/usr/bin/env python3
"""
Career OS — Recruiter contacts

The fact store for recruiter-connect. Claude does the finding (web search) and the
judgement (who is worth contacting, what to say); this script owns the record and
enforces the rules that must never depend on judgement:

  - a do-not-contact is permanent: add refuses that person forever
  - emails are public-source only: an email without --email-source is rejected
  - a daily cap on NEW people contacted (config: recruiter_connect.daily_new_contacts)
  - a maximum number of touches per person, then stop
  - follow-up dates set from the configured cadence
  - contacts found long ago are flagged for re-verification before first touch

Data: data/recruiters/contacts.json (gitignored, backed up by sync-vault.sh).

Usage:
  python3 scripts/recruiters.py add --name "A B" --company "Acme" --title "Technical Recruiter" \\
      --kind in_house --source-url https://… [--profile-url …] [--email … --email-source https://…] \\
      [--location Bengaluru] [--evidence "posted SWE II req on 2026-10-01"] [--role-title … --role-url …]
  python3 scripts/recruiters.py list [--status found] [--company Acme] [--format md|json]
  python3 scripts/recruiters.py touch <id> --channel linkedin_note|inmail|email|naukri|other [--note …]
  python3 scripts/recruiters.py mark <id> replied|call_scheduled|not_now|do_not_contact|closed|drafted [--note …]
  python3 scripts/recruiters.py verify <id>
  python3 scripts/recruiters.py due
  python3 scripts/recruiters.py cap
  python3 scripts/recruiters.py stats
  python3 scripts/recruiters.py agencies [--type tech_specialist] [--seniority mid]
"""

import argparse
import json
import os
import re
import sys
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE_DIR = os.path.join(ROOT, "data", "recruiters")
STORE = os.path.join(STORE_DIR, "contacts.json")
USER_CONFIG = os.path.join(ROOT, "config", "user.json")
AGENCIES = os.path.join(ROOT, "config", "agencies.json")
AGENCIES_EXAMPLE = os.path.join(ROOT, "config", "agencies.example.json")

DEFAULTS = {"daily_new_contacts": 10, "max_touches": 3, "follow_up_days": [5, 11],
            "stale_after_days": 30}
STATUSES = ["found", "drafted", "sent", "replied", "call_scheduled", "not_now",
            "do_not_contact", "closed"]
CHANNELS = ["linkedin_note", "inmail", "email", "naukri", "other"]
# A contact in one of these states never gets a follow-up nudge.
QUIET = {"replied", "call_scheduled", "not_now", "do_not_contact", "closed"}


def today() -> str:
    return date.today().isoformat()


def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default


def settings() -> dict:
    cfg = load_json(USER_CONFIG, {}).get("recruiter_connect", {}) or {}
    return {**DEFAULTS, **{k: v for k, v in cfg.items() if k in DEFAULTS}}


def load() -> dict:
    return load_json(STORE, {"contacts": {}})


def save(store: dict) -> None:
    os.makedirs(STORE_DIR, exist_ok=True)
    with open(STORE, "w") as f:
        json.dump(store, f, indent=2, ensure_ascii=False)
        f.write("\n")


def slug(*parts: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", " ".join(parts).lower()).strip("-")


def norm_url(u: str) -> str:
    return (u or "").split("?")[0].rstrip("/").lower()


def find_existing(store: dict, name: str, company: str, profile_url: str):
    pu = norm_url(profile_url)
    for cid, c in store["contacts"].items():
        if pu and norm_url(c.get("profile_url")) == pu:
            return cid
        if slug(c["name"]) == slug(name) and slug(c["company"]) == slug(company):
            return cid
    return None


def first_touched_today(store: dict) -> int:
    return sum(1 for c in store["contacts"].values()
               if c.get("touches") and c["touches"][0]["date"] == today())


def get(store: dict, cid: str) -> dict:
    c = store["contacts"].get(cid)
    if not c:
        print(f"No contact '{cid}'. See: recruiters.py list", file=sys.stderr)
        sys.exit(1)
    return c


# ---------------------------------------------------------------------------

def cmd_add(a) -> None:
    if a.email and not a.email_source:
        print("Refused: emails must come from a public source. Pass --email-source <url> "
              "where the address is published, or leave the email out.", file=sys.stderr)
        sys.exit(1)
    store = load()
    cid = find_existing(store, a.name, a.company, a.profile_url)
    if cid:
        c = store["contacts"][cid]
        if c["status"] == "do_not_contact":
            print(f"Refused: {c['name']} ({c['company']}) asked not to be contacted.",
                  file=sys.stderr)
            sys.exit(1)
        if a.role_url and a.role_url not in [r.get("url") for r in c["roles"]]:
            c["roles"].append({"title": a.role_title or "", "url": a.role_url})
        c["verified_at"] = today()
        save(store)
        print(f"Already known: {cid} ({c['status']}) — refreshed", file=sys.stderr)
        print(cid)
        return
    cid = slug(a.name, a.company)
    store["contacts"][cid] = {
        "name": a.name, "company": a.company, "title": a.title or "",
        "kind": a.kind, "agency": a.agency or "", "location": a.location or "",
        "profile_url": a.profile_url or "", "email": a.email or "",
        "email_source": a.email_source or "", "source_url": a.source_url,
        "evidence": a.evidence or "",
        "roles": [{"title": a.role_title or "", "url": a.role_url}] if a.role_url else [],
        "status": "found", "found_at": today(), "verified_at": today(),
        "touches": [], "next_follow_up": "", "notes": [],
    }
    save(store)
    print(f"Added {cid}", file=sys.stderr)
    print(cid)


def cmd_touch(a) -> None:
    store, s = load(), settings()
    c = get(store, a.id)
    if c["status"] == "do_not_contact":
        print("Refused: this person asked not to be contacted.", file=sys.stderr)
        sys.exit(1)
    if len(c["touches"]) >= s["max_touches"]:
        print(f"Refused: {s['max_touches']} touches already. Silence is an answer; "
              f"mark it closed or not_now.", file=sys.stderr)
        sys.exit(1)
    if not c["touches"]:
        used = first_touched_today(store)
        if used >= s["daily_new_contacts"]:
            print(f"Refused: daily cap reached ({used}/{s['daily_new_contacts']} new people "
                  f"today). Change recruiter_connect.daily_new_contacts in config/user.json "
                  f"if you mean to.", file=sys.stderr)
            sys.exit(1)
        stale = (date.today() - date.fromisoformat(c["verified_at"])).days
        if stale > s["stale_after_days"] and not a.force:
            print(f"Refused: found {stale} days ago; people move. Re-check they still hold "
                  f"this role, then: recruiters.py verify {a.id}", file=sys.stderr)
            sys.exit(1)
    c["touches"].append({"date": today(), "channel": a.channel, "note": a.note or ""})
    c["status"] = "sent"
    n = len(c["touches"])
    first = date.fromisoformat(c["touches"][0]["date"])
    cadence = s["follow_up_days"]
    c["next_follow_up"] = ((first + timedelta(days=cadence[n - 1])).isoformat()
                           if n <= len(cadence) and n < s["max_touches"] else "")
    save(store)
    print(f"Logged touch {n}/{s['max_touches']} for {c['name']}"
          + (f" · next follow-up {c['next_follow_up']}" if c["next_follow_up"] else " · last touch"),
          file=sys.stderr)


def cmd_mark(a) -> None:
    store = load()
    c = get(store, a.id)
    c["status"] = a.status
    if a.status in QUIET:
        c["next_follow_up"] = ""
    if a.note:
        c["notes"].append({"date": today(), "note": a.note})
    save(store)
    print(f"{c['name']} → {a.status}", file=sys.stderr)


def cmd_verify(a) -> None:
    store = load()
    get(store, a.id)["verified_at"] = today()
    save(store)
    print(f"Verified {a.id} today", file=sys.stderr)


def row(cid: str, c: dict) -> str:
    who = f"{c['name']} — {c['title']}" if c["title"] else c["name"]
    kind = f"agency: {c['agency']}" if c["kind"] == "agency" and c["agency"] else c["kind"]
    link = c["profile_url"] or c["source_url"]
    return (f"| `{cid}` | {who} | {c['company']} | {kind} | {c['status']} | "
            f"{len(c['touches'])} | {c['next_follow_up'] or '—'} | [link]({link}) |")


HEADER = ("| id | Recruiter | Company | Kind | Status | Touches | Next | Link |\n"
          "|---|---|---|---|---|---|---|---|")


def cmd_list(a) -> None:
    store = load()
    items = [(cid, c) for cid, c in store["contacts"].items()
             if (not a.status or c["status"] == a.status)
             and (not a.company or a.company.lower() in c["company"].lower())]
    if a.format == "json":
        print(json.dumps(dict(items), indent=2, ensure_ascii=False))
        return
    if not items:
        print("No recruiters yet. Find some: `find recruiters at [company]`.")
        return
    print(HEADER)
    for cid, c in sorted(items, key=lambda x: (x[1]["company"], x[1]["status"])):
        print(row(cid, c))


def cmd_due(a) -> None:
    store, s = load(), settings()
    t = today()
    due = [(cid, c) for cid, c in store["contacts"].items()
           if c["next_follow_up"] and c["next_follow_up"] <= t and c["status"] not in QUIET]
    stale = [(cid, c) for cid, c in store["contacts"].items()
             if c["status"] in ("found", "drafted") and not c["touches"]
             and (date.today() - date.fromisoformat(c["verified_at"])).days > s["stale_after_days"]]
    if not due and not stale:
        print("Nothing due today.")
        return
    if due:
        print(f"### Follow-ups due ({len(due)})\n\n{HEADER}")
        for cid, c in due:
            print(row(cid, c))
    if stale:
        print(f"\n### Re-check before contacting ({len(stale)}) — found over "
              f"{s['stale_after_days']} days ago\n\n{HEADER}")
        for cid, c in stale:
            print(row(cid, c))


def cmd_cap(a) -> None:
    s = settings()
    used = first_touched_today(load())
    print(json.dumps({"new_today": used, "cap": s["daily_new_contacts"],
                      "remaining": max(0, s["daily_new_contacts"] - used)}))


def cmd_stats(a) -> None:
    contacts = load()["contacts"].values()
    by_status: dict = {}
    for c in contacts:
        by_status[c["status"]] = by_status.get(c["status"], 0) + 1
    out = {"total": len(contacts), "by_status": by_status, "reply_rate": {}}
    for key in ("kind", "channel"):
        groups: dict = {}
        for c in contacts:
            if not c["touches"]:
                continue
            g = c["kind"] if key == "kind" else c["touches"][0]["channel"]
            sent, replied = groups.get(g, (0, 0))
            groups[g] = (sent + 1, replied + (c["status"] in ("replied", "call_scheduled")))
        out["reply_rate"][key] = {g: f"{r}/{n}" for g, (n, r) in groups.items()}
    print(json.dumps(out, indent=2))


def cmd_agencies(a) -> None:
    data = load_json(AGENCIES, None) or load_json(AGENCIES_EXAMPLE, {"agencies": []})
    rows = [g for g in data["agencies"]
            if (not a.type or g["type"] == a.type)
            and (not a.seniority or a.seniority in g.get("seniority", []))]
    print("| Agency | Type | Focus | Levels | Website |\n|---|---|---|---|---|")
    for g in rows:
        print(f"| {g['name']} | {g['type']} | {', '.join(g['focus'])} | "
              f"{', '.join(g.get('seniority', []))} | {g['website']} |")


def main() -> None:
    p = argparse.ArgumentParser(description="Recruiter contacts for recruiter-connect")
    sub = p.add_subparsers(dest="cmd", required=True)

    ad = sub.add_parser("add")
    ad.add_argument("--name", required=True)
    ad.add_argument("--company", required=True, help="Company they hire for (or the agency's client)")
    ad.add_argument("--title")
    ad.add_argument("--kind", choices=["in_house", "agency"], required=True)
    ad.add_argument("--agency", help="Agency name, when kind=agency")
    ad.add_argument("--location")
    ad.add_argument("--profile-url")
    ad.add_argument("--email")
    ad.add_argument("--email-source", help="URL where the email is publicly published")
    ad.add_argument("--source-url", required=True, help="Where this person was found")
    ad.add_argument("--evidence", help="Why they're relevant now")
    ad.add_argument("--role-title")
    ad.add_argument("--role-url")
    ad.set_defaults(fn=cmd_add)

    t = sub.add_parser("touch")
    t.add_argument("id")
    t.add_argument("--channel", choices=CHANNELS, required=True)
    t.add_argument("--note")
    t.add_argument("--force", action="store_true", help="Skip the stale check (you re-checked by hand)")
    t.set_defaults(fn=cmd_touch)

    m = sub.add_parser("mark")
    m.add_argument("id")
    m.add_argument("status", choices=[s for s in STATUSES if s not in ("found", "sent")])
    m.add_argument("--note")
    m.set_defaults(fn=cmd_mark)

    v = sub.add_parser("verify")
    v.add_argument("id")
    v.set_defaults(fn=cmd_verify)

    ls = sub.add_parser("list")
    ls.add_argument("--status", choices=STATUSES)
    ls.add_argument("--company")
    ls.add_argument("--format", choices=["md", "json"], default="md")
    ls.set_defaults(fn=cmd_list)

    sub.add_parser("due").set_defaults(fn=cmd_due)
    sub.add_parser("cap").set_defaults(fn=cmd_cap)
    sub.add_parser("stats").set_defaults(fn=cmd_stats)

    ag = sub.add_parser("agencies")
    ag.add_argument("--type", choices=["staffing", "tech_specialist", "executive_search",
                                       "rpo", "platform"])
    ag.add_argument("--seniority", choices=["early", "mid", "senior", "leadership"])
    ag.set_defaults(fn=cmd_agencies)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
