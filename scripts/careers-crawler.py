#!/usr/bin/env python3
"""
Career OS — Careers Crawler

For companies with no reachable ATS board, no job-board connector and no API.
Uses a real browser (Playwright) on the company's own careers page.

Two jobs, run at different cadences:

  discover   Slow, on demand. Loads the careers page and watches everything it
             touches: network calls, links, and apply URLs embedded in the page. If
             any of it points at a known job system (Workday, SmartRecruiters,
             Greenhouse, Lever, Ashby, Eightfold/pcsx...), that board is verified and
             can be pinned permanently, so no scraping is needed from then on. Lowe's,
             Visa and PhonePe all looked unreachable and all turned out to have one.
             Only when nothing is found does it fall back to saving a scrape recipe:
             the listing URL and the link prefix its job postings use.

  extract    Daily, called by find-jobs.py. Replays saved recipes: loads each listing
             page, collects job links, filters by role.

Policy: behaves like an ordinary browser. No stealth or fingerprint masking, a pause
between pages, a cap on pages per site, no logins. If a site shows a CAPTCHA or blocks
the request, the crawler stops for that company and says so, and the job search falls
back to Naukri or web search. It never tries to get around a block.

Usage:
  python3 scripts/careers-crawler.py discover --company "Apple"
  python3 scripts/careers-crawler.py discover --company "Apple" --url "https://jobs.apple.com/en-in/search?search=engineer"
  python3 scripts/careers-crawler.py discover --all-unreachable --apply
  python3 scripts/careers-crawler.py extract --all --role "Software Engineer"
  python3 scripts/careers-crawler.py extract --company "SAP"
"""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import date
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ats_platforms import platform_from_url, probe  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(ROOT, "config", "companies.json")
USER_CONFIG_PATH = os.path.join(ROOT, "config", "user.json")
RESOLVER = os.path.join(ROOT, "scripts", "resolve-ats.py")

SETTLE_MS = 6000          # let client-rendered listings appear
PAGE_DELAY_MS = 4000      # politeness pause between page loads on one site
DEFAULT_MAX_PAGES = 3
MIN_RECIPE_LINKS = 3      # fewer job links than this is not a listing page
MAX_ATS_CANDIDATES = 8

BLOCK_RE = re.compile(
    r"captcha|access denied|verify you are (a )?human|unusual traffic|are you a robot|"
    r"request blocked|attention required|pardon our interruption", re.I)
ATS_URL_RE = re.compile(
    r"https?://[^\s\"'<>\\]*(?:myworkdayjobs\.com|greenhouse\.io|lever\.co|ashbyhq\.com|"
    r"smartrecruiters\.com|workable\.com|recruitee\.com)[^\s\"'<>\\]*"
    r"|https?://[^\s\"'<>\\]+/api/(?:pcsx/search|apply/v2/jobs)[^\s\"'<>\\]*", re.I)
JOB_SEGMENT_RE = re.compile(
    r"^(job|jobs|details|position|positions|opening|openings|requisition|requisitions|"
    r"vacancy|vacancies)$", re.I)
NOISE_TEXT_RE = re.compile(
    r"^(see full role description|where we.re hiring|apply( now)?|learn more|"
    r"view (job|details)|read more|details|share|save( job)?)$", re.I)
NOISE_URL_RE = re.compile(r"locationpicker|/apply(/|$|\?)|/share|^mailto:|^javascript:", re.I)
HUB_TEXT_RE = re.compile(
    r"\b(search|view|see|browse|explore|find)\b.{0,12}\b(jobs|openings|roles|positions|opportunities)\b", re.I)


def load_json(path: str, default):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default


def save_registry(reg: dict) -> None:
    reg["updated"] = date.today().isoformat()
    with open(REGISTRY_PATH, "w") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)
        f.write("\n")


def default_role() -> str:
    roles = load_json(USER_CONFIG_PATH, {}).get("target", {}).get("target_roles", [])
    return roles[0] if roles else ""


def matches_role(title: str, role: str) -> bool:
    if not role:
        return True
    t = title.lower()
    return any(w.lower() in t for w in role.split() if len(w) > 1)


def site_domain(host: str) -> str:
    parts = host.lower().split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host.lower()


def link_prefix(path: str) -> str | None:
    """'/en-in/details/200314122/x' -> '/en-in/details/'. None without a job-ish segment."""
    parts = [p for p in path.split("/") if p]
    for i, seg in enumerate(parts):
        if JOB_SEGMENT_RE.match(seg):
            return "/" + "/".join(parts[:i + 1]) + "/"
    return None


def group_job_links(links: list[dict], site: str, prefix: str | None = None) -> dict:
    """Collapse raw anchors into one entry per job URL, keeping the best title."""
    groups: dict[str, dict] = {}
    for link in links:
        href = link.get("h") or ""
        u = urlparse(href)
        if not u.netloc.lower().endswith(site) or NOISE_URL_RE.search(href):
            continue
        p = link_prefix(u.path)
        if not p or (prefix and not u.path.startswith(prefix)):
            continue
        if len(u.path.rstrip("/")) <= len(p.rstrip("/")):
            continue  # the prefix itself, not a posting
        key = f"{u.scheme}://{u.netloc}{u.path.rstrip('/')}"
        g = groups.setdefault(key, {"url": key, "prefix": p, "title": "", "ctx": ""})
        text = (link.get("t") or "").strip()
        if text and not NOISE_TEXT_RE.match(text) and len(text) > len(g["title"]):
            g["title"] = text
        if len(link.get("ctx") or "") > len(g["ctx"]):
            g["ctx"] = link["ctx"]
    return {k: g for k, g in groups.items() if g["title"]}


async def load(page, url: str) -> tuple[int | None, bool]:
    resp = await page.goto(url, wait_until="domcontentloaded", timeout=45000)
    await page.wait_for_timeout(SETTLE_MS)
    for _ in range(2):
        await page.mouse.wheel(0, 4000)
        await page.wait_for_timeout(1200)
    status = resp.status if resp else None
    try:
        text = (await page.inner_text("body"))[:5000]
    except Exception:
        text = ""
    return status, status in (403, 429) or bool(BLOCK_RE.search(text))


async def collect_links(page) -> list[dict]:
    return await page.eval_on_selector_all("a[href]", """els => els.map(a => {
        const box = a.closest('li, tr, article, [role=listitem]') || a.parentElement;
        return {h: a.href, t: (a.innerText || '').trim().split('\\n')[0].slice(0, 140),
                ctx: box ? (box.innerText || '').slice(0, 300) : ''};
    })""")


def pick_hub(links: list[dict], site: str, current: str) -> str | None:
    """A 'search jobs' / 'view all openings' link on the same site, if the page has one."""
    for link in links:
        href = link.get("h") or ""
        if (HUB_TEXT_RE.search(link.get("t") or "") and urlparse(href).netloc.lower().endswith(site)
                and href.split("#")[0] != current.split("#")[0]):
            return href
    return None


def launch_playwright():
    try:
        from playwright.async_api import async_playwright  # deliberately no stealth
    except ImportError:
        print("Playwright is not installed: pip install playwright && python3 -m playwright "
              "install chromium", file=sys.stderr)
        sys.exit(2)
    return async_playwright


# ---------------------------------------------------------------------------
# discover
# ---------------------------------------------------------------------------

async def discover_one(browser, name: str, url: str) -> dict:
    result: dict = {"name": name, "url": url}
    ctx = await browser.new_context(locale="en-IN", viewport={"width": 1366, "height": 900})
    page = await ctx.new_page()
    network: list[str] = []
    page.on("request", lambda r: network.append(r.url))
    try:
        status, blocked = await load(page, url)
        result["status"] = status
        if blocked:
            result["blocked"] = True
            return result
        html = await page.content()
        links = await collect_links(page)
        site = site_domain(urlparse(page.url).netloc)

        # A landing page with no postings often links to the real listing. Follow it once.
        if len(group_job_links(links, site)) < MIN_RECIPE_LINKS:
            hub = pick_hub(links, site, page.url)
            if hub:
                await page.wait_for_timeout(PAGE_DELAY_MS)
                status, blocked = await load(page, hub)
                if blocked:
                    result["blocked"] = True
                    result["status"] = status
                    return result
                html += await page.content()
                links += await collect_links(page)
                result["followed"] = page.url

        result["final_url"] = page.url
        result["_links"] = links
        result["_candidates"] = sorted({u for u in set(network) | {l["h"] for l in links}
                                        | set(ATS_URL_RE.findall(html))
                                        if ATS_URL_RE.match(u)})
    except Exception as e:
        result["error"] = f"could not load: {str(e)[:90]}"
    finally:
        await ctx.close()
    return result


def classify(result: dict) -> dict:
    """Verify ATS candidates (network I/O), else derive a scrape recipe."""
    if result.get("blocked") or result.get("error"):
        return result

    boards: dict[tuple[str, str], str] = {}
    for u in result.pop("_candidates", []):
        pf = platform_from_url(u)
        if pf and pf not in boards:
            boards[pf] = u
    verified = []
    for (platform, slug), u in list(boards.items())[:MAX_ATS_CANDIDATES]:
        count = probe(platform, slug)
        if count:
            verified.append({"platform": platform, "slug": slug, "jobs": count, "url": u})
    if verified:
        result["ats"] = max(verified, key=lambda v: v["jobs"])
        result.pop("_links", None)
        return result

    final_url = result.get("final_url") or result["url"]
    site = site_domain(urlparse(final_url).netloc)
    groups = group_job_links(result.pop("_links", []), site)
    if len(groups) >= MIN_RECIPE_LINKS:
        prefix = Counter(g["prefix"] for g in groups.values()).most_common(1)[0][0]
        kept = [g for g in groups.values() if g["prefix"] == prefix]
        result["recipe"] = {"listing_url": final_url, "link_prefix": prefix, "site": site,
                            "jobs_seen": len(kept), "verified_at": date.today().isoformat()}
        result["sample"] = [g["title"] for g in kept[:3]]
    return result


def apply_result(result: dict, reg: dict) -> str:
    name = result["name"]
    if result.get("ats"):
        a = result["ats"]
        out = subprocess.run([sys.executable, RESOLVER, "--from-url", name, a["url"]],
                             capture_output=True, text=True, timeout=240)
        return (out.stderr or out.stdout).strip().splitlines()[-1] if (out.stderr or out.stdout) else "pinned"
    if result.get("recipe"):
        companies = reg.setdefault("companies", {})
        key = name.lower().strip()
        entry = companies.get(key) or {"name": name, "platform": "none", "slug": "",
                                       "status": "unresolved", "jobs_seen": 0,
                                       "board_url": "", "careers_url": ""}
        entry["scrape"] = result["recipe"]
        if not entry.get("careers_url"):
            entry["careers_url"] = result["url"]
        companies[key] = entry
        return f"saved scrape recipe ({result['recipe']['jobs_seen']} jobs)"
    return ""


def report_discovery(result: dict, applied: str) -> None:
    name = result["name"]
    if result.get("error"):
        print(f"  {name}: {result['error']}", file=sys.stderr)
    elif result.get("blocked"):
        print(f"  {name}: BLOCKED (HTTP {result.get('status')}) — stopped; "
              f"use Naukri or web search for this company", file=sys.stderr)
    elif result.get("ats"):
        a = result["ats"]
        print(f"  {name}: FOUND {a['platform']}:{a['slug']} ({a['jobs']} jobs) — permanent, "
              f"no scraping needed", file=sys.stderr)
        print(f"     {applied or 'pin with: resolve-ats.py --from-url ' + repr(name) + ' ' + repr(a['url'])}",
              file=sys.stderr)
    elif result.get("recipe"):
        r = result["recipe"]
        print(f"  {name}: no job system found · scrape recipe {r['link_prefix']} on {r['site']} "
              f"({r['jobs_seen']} jobs) e.g. {result.get('sample')}", file=sys.stderr)
        print(f"     {applied or 'save with --apply'}", file=sys.stderr)
    else:
        print(f"  {name}: nothing usable — no job system and no job links on "
              f"{result.get('final_url') or result['url']}. Try a search-results URL with --url, "
              f"or use Naukri / web search", file=sys.stderr)


async def run_discover(targets: list[tuple[str, str]], apply: bool) -> None:
    reg = load_json(REGISTRY_PATH, {"companies": {}})
    async_playwright = launch_playwright()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        raw = []
        for i, (name, url) in enumerate(targets):
            print(f"[{i + 1}/{len(targets)}] {name} …", file=sys.stderr)
            raw.append(await discover_one(browser, name, url))
        await browser.close()

    for result in raw:
        result = classify(result)
        applied = apply_result(result, reg) if apply else ""
        report_discovery(result, applied)
    if apply:
        save_registry(reg)


# ---------------------------------------------------------------------------
# extract
# ---------------------------------------------------------------------------

async def next_page_url(page) -> str | None:
    return await page.evaluate("""() => {
        const a = document.querySelector('a[rel=next], a[aria-label*="next" i], a[title*="next" i]');
        return a && a.href ? a.href : null;
    }""")


async def extract_one(browser, entry: dict, role: str, max_pages: int) -> list[dict]:
    recipe, name = entry["scrape"], entry["name"]
    ctx = await browser.new_context(locale="en-IN", viewport={"width": 1366, "height": 900})
    page = await ctx.new_page()
    found: dict[str, dict] = {}
    url, pages, note = recipe["listing_url"], 0, ""
    try:
        while url and pages < max_pages:
            status, blocked = await load(page, url)
            if blocked:
                note = f"blocked (HTTP {status}) — stopped"
                break
            for key, g in group_job_links(await collect_links(page), recipe["site"],
                                          recipe["link_prefix"]).items():
                found.setdefault(key, g)
            pages += 1
            nxt = await next_page_url(page)
            if not nxt or nxt == url:
                break
            url = nxt
            await page.wait_for_timeout(PAGE_DELAY_MS)
    except Exception as e:
        note = f"error: {str(e)[:80]}"
    finally:
        await ctx.close()

    jobs = []
    for g in found.values():
        if not matches_role(g["title"], role):
            continue
        ctx_lines = [l.strip() for l in (g["ctx"] or "").splitlines() if l.strip()]
        location = next((l for l in ctx_lines if l != g["title"] and len(l) < 60 and re.search(
            r"india|bengaluru|bangalore|hyderabad|pune|remote|chennai|mumbai|delhi|gurugram|noida",
            l, re.I)), "")
        jobs.append({"title": g["title"], "company": name, "location": location,
                     "experience": "", "salary": "Not disclosed", "description": "",
                     "posted": "", "tags": [], "url": g["url"], "source": "careers"})

    if not found and not note:
        note = "recipe returned no job links — the site may have changed; re-run discover"
    print(f"  {name}: {len(jobs)} matched / {len(found)} links over {pages} page(s)"
          + (f" · {note}" if note else ""), file=sys.stderr)
    return jobs


async def run_extract(entries: list[dict], role: str, max_pages: int) -> None:
    async_playwright = launch_playwright()
    jobs: list[dict] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for i, entry in enumerate(entries):
            if i:
                await asyncio.sleep(PAGE_DELAY_MS / 1000)
            jobs += await extract_one(browser, entry, role, max_pages)
        await browser.close()
    print(json.dumps(jobs, ensure_ascii=False, indent=2))
    print(f"\n# {len(jobs)} jobs from {len(entries)} careers page(s)", file=sys.stderr)


# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Careers pages for companies with no ATS/API")
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("discover", help="Find the job system behind a careers page (slow)")
    d.add_argument("--company", help="Registry company; uses its careers_url unless --url given")
    d.add_argument("--url", help="Careers or search-results URL to inspect")
    d.add_argument("--all-unreachable", action="store_true",
                   help="Every registry company with no fetchable board and a careers_url")
    d.add_argument("--apply", action="store_true",
                   help="Pin found boards and save scrape recipes to the registry")

    e = sub.add_parser("extract", help="Replay saved scrape recipes (daily)")
    e.add_argument("--all", action="store_true", help="Every company with a scrape recipe")
    e.add_argument("--company")
    e.add_argument("--role", default="", help="Role filter (default: target_roles[0])")
    e.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)

    args = ap.parse_args()
    reg = load_json(REGISTRY_PATH, {"companies": {}})
    companies = reg.get("companies", {})

    if args.cmd == "discover":
        targets: list[tuple[str, str]] = []
        if args.all_unreachable:
            for c in companies.values():
                fetchable = c.get("status") in ("verified", "manual") and c.get("platform", "none") != "none"
                if fetchable:
                    continue
                if c.get("careers_url"):
                    targets.append((c["name"], c["careers_url"]))
                else:
                    print(f"  {c['name']}: no careers_url — find it with web search, then "
                          f"resolve-ats.py --set-careers", file=sys.stderr)
        elif args.company:
            entry = companies.get(args.company.lower().strip())
            url = args.url or (entry or {}).get("careers_url")
            if not url:
                print(f"No URL for {args.company}. Pass --url, or set a careers_url first.",
                      file=sys.stderr)
                sys.exit(1)
            targets = [((entry or {}).get("name") or args.company, url)]
        elif args.url:
            targets = [(urlparse(args.url).netloc, args.url)]
        else:
            ap.error("discover needs --company, --url or --all-unreachable")
        if not targets:
            print("Nothing to discover.", file=sys.stderr)
            return
        asyncio.run(run_discover(targets, args.apply))
        return

    entries = [c for c in companies.values() if c.get("scrape")]
    if args.company:
        entries = [c for c in entries if c["name"].lower() == args.company.lower().strip()]
    elif not args.all:
        ap.error("extract needs --all or --company")
    if not entries:
        print("No scrape recipes saved. Run: careers-crawler.py discover ... --apply", file=sys.stderr)
        print(json.dumps([]))
        return
    asyncio.run(run_extract(entries, args.role or default_role(), args.max_pages))


if __name__ == "__main__":
    main()
