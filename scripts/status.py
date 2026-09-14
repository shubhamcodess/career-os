#!/usr/bin/env python3
"""
Career OS — Status snapshot

One fast, read-only pass over every local state file, printed as JSON for the
`status` dashboard. No network calls; connector state comes from the session
(`session_connectors_status`), not from here. Never prints secret values — only
whether a key is set.

Usage:
  python3 scripts/status.py            # JSON on stdout
"""

import importlib.util
import json
import os
import re
import subprocess
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def p(*parts: str) -> str:
    return os.path.join(ROOT, *parts)


def read(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def load_json(path: str, default):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default


def git(*args: str, cwd: str = ROOT) -> str:
    try:
        return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except Exception:
        return ""


def env_flags() -> dict:
    values = {}
    for line in read(p(".env")).splitlines():
        m = re.match(r"\s*([A-Z_]+)\s*=\s*(.*)", line)
        if m:
            values[m.group(1)] = m.group(2).strip().strip("\"'")
    return {
        "exists": os.path.exists(p(".env")),
        "personalize": values.get("PERSONALIZE", "").lower() == "true",
        "private_repo_url_set": bool(values.get("PRIVATE_REPO_URL")),
        "github_token_set": bool(values.get("GITHUB_PERSONAL_ACCESS_TOKEN")),
    }


def interview() -> dict:
    text = read(p("checkpoints", "interview-state.md"))
    if not text:
        return {"status": "NOT STARTED", "checkpoints": 0, "last": ""}
    status = re.search(r"_Status:\s*([^_]+)_", text)
    cps = re.findall(r"^- (CP-\d+):\s*([^—\n]+)", text, re.M)
    return {"status": status.group(1).strip() if status else "IN PROGRESS",
            "checkpoints": len(cps),
            "last": f"{cps[-1][0]} {cps[-1][1].strip()}" if cps else ""}


def file_info(*parts: str) -> dict:
    path = p(*parts)
    if not os.path.exists(path):
        return {"exists": False, "lines": 0, "updated": ""}
    return {"exists": True, "lines": read(path).count("\n"),
            "updated": date.fromtimestamp(os.path.getmtime(path)).isoformat()}


def resumes() -> dict:
    base = p("resumes")
    dirs = sorted((d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))),
                  key=lambda d: os.path.getmtime(os.path.join(base, d))) if os.path.isdir(base) else []
    return {"count": len(dirs), "latest": dirs[-1] if dirs else ""}


def job_store() -> dict:
    index = load_json(p("data", "market", "job-index.json"), {})
    records = index.get("jobs", index) if isinstance(index, dict) else {}
    rows = records.values() if isinstance(records, dict) else records
    counts: dict[str, int] = {}
    google_applied_30d = 0
    cutoff = (date.today() - timedelta(days=30)).isoformat()
    total = 0
    for j in rows:
        if not isinstance(j, dict) or "status" not in j:
            continue
        total += 1
        counts[j["status"]] = counts.get(j["status"], 0) + 1
        if (j["status"] == "applied" and "google" in (j.get("company") or "").lower()
                and (j.get("status_set") or "") >= cutoff):
            google_applied_30d += 1
    runs_dir = p("data", "market", "runs")
    runs = sorted(os.listdir(runs_dir)) if os.path.isdir(runs_dir) else []
    feed = read(p("data", "market", "job-feed.md"))
    feed_updated = re.search(r"_Last updated:\s*([^_]+)_", feed)
    feed_counts = re.search(r"_(\d+) at your target companies · (\d+) from open discovery_", feed)
    return {
        "total": total, "by_status": counts,
        "last_run_day": runs[-1].removesuffix(".json") if runs else "",
        "run_days": len(runs),
        "feed_updated": feed_updated.group(1).strip() if feed_updated else "",
        "feed_targeted": int(feed_counts.group(1)) if feed_counts else 0,
        "feed_discovery": int(feed_counts.group(2)) if feed_counts else 0,
        "index_kb": round(os.path.getsize(p("data", "market", "job-index.json")) / 1024)
        if os.path.exists(p("data", "market", "job-index.json")) else 0,
        "google_applications_30d": google_applied_30d,
    }


def registry() -> dict:
    reg = load_json(p("config", "companies.json"), None)
    if reg is None:
        return {"built": False}
    companies = reg.get("companies", {}).values()
    fetchable = [c for c in companies if c.get("platform", "none") != "none"
                 and c.get("status") in ("verified", "manual")]
    recipes = [c for c in companies if c.get("scrape")]
    reached = {c["name"] for c in fetchable} | {c["name"] for c in recipes}
    unreachable = sorted(c["name"] for c in companies if c["name"] not in reached)
    return {"built": True, "total": len(reg.get("companies", {})), "fetchable": len(fetchable),
            "careers_recipes": len(recipes), "unreachable": unreachable,
            "low_confidence": sorted(c["name"] for c in fetchable if c.get("confidence") == "low"),
            "updated": reg.get("updated", "")}


def find_key(obj, key: str):
    """First value for key anywhere in a nested config — sections move between versions."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            found = find_key(v, key)
            if found is not None:
                return found
    return None


def user_config() -> dict:
    cfg = load_json(p("config", "user.json"), None)
    if cfg is None:
        return {"exists": False}
    target = cfg.get("target", {})
    integrations = cfg.get("integrations", {})
    return {"exists": True,
            "target_companies": len(target.get("target_companies", []) or []),
            "target_roles": target.get("target_roles", []) or [],
            "target_locations": target.get("target_locations", []) or [],
            "naukri_enabled": bool(find_key(cfg, "naukri_enabled")),
            "slack_enabled": bool(integrations.get("slack", {}).get("enabled")),
            "gmail_enabled": bool(integrations.get("gmail", {}).get("enabled"))}


def budgets() -> list[dict]:
    try:
        out = subprocess.run(["python3", p("scripts", "mcp-budget.py"), "status"],
                             capture_output=True, text=True, timeout=10)
        text = out.stdout + out.stderr
    except Exception:
        return []
    rows = []
    for line in text.splitlines():
        m = re.match(r"\s+(\w+)\s+(\d+)(?:/(\d+))?\s", line)
        if m:
            rows.append({"connector": m.group(1), "used": int(m.group(2)),
                         "cap": int(m.group(3)) if m.group(3) else None})
    return rows


def synced(*parts: str) -> str:
    m = re.search(r"last_synced:\s*([0-9-]+)", read(p(*parts)))
    return m.group(1) if m else ""


def main() -> None:
    worktree = p(".personal-worktree")
    unpushed = git("rev-list", "--count", "origin/main..main")
    snapshot = {
        "generated": datetime.now().isoformat(timespec="minutes"),
        "env": env_flags(),
        "config": user_config(),
        "interview": interview(),
        "master_doc": file_info("data", "master-experience.md"),
        "star_stories": file_info("data", "star-stories.md"),
        "job_tracker": file_info("data", "job-tracker.md"),
        "resumes": resumes(),
        "job_store": job_store(),
        "registry": registry(),
        "budgets": budgets(),
        "profiles": {"linkedin_synced": synced("data", "profile-linkedin.md"),
                     "naukri_synced": synced("data", "profile-naukri.md"),
                     "content_ideas": os.path.exists(p("data", "content", "story-bank.md")),
                     "content_calendar": os.path.exists(p("data", "content", "calendar.md"))},
        "outreach_files": len([f for f in os.listdir(p("data", "outreach"))
                               if f.endswith(".md")]) if os.path.isdir(p("data", "outreach")) else 0,
        "setup": {"node_modules": os.path.isdir(p("node_modules")),
                  "pdf_export_tested": os.path.exists(p("exports", "test-render.pdf")),
                  "playwright": importlib.util.find_spec("playwright") is not None},
        "git": {"last_commit": git("log", "-1", "--format=%s"),
                "unpushed_public": int(unpushed) if unpushed.isdigit() else None,
                "vault_synced": git("log", "-1", "--format=%ar", cwd=worktree)
                if os.path.isdir(worktree) else "never"},
    }
    print(json.dumps(snapshot, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
