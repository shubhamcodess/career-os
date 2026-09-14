#!/usr/bin/env python3
"""
Career OS — Careers Crawler

For companies with no reachable ATS board, no job-board connector and no API.
Uses a real browser (Playwright) on the company's own careers page. Works on any
careers site: nothing here knows about a particular company.

Two jobs, run at different cadences:

  discover   Slow, on demand. Loads the careers page and watches everything it
             touches: network calls, JSON responses, links, embedded page data and
             apply URLs. In order of preference it looks for:
               1. a known job system with an adapter (Workday, SmartRecruiters,
                  Greenhouse, Lever, Ashby, Workable, Recruitee, Eightfold/pcsx) —
                  verified and pinned permanently, no browser needed afterwards
               2. the JSON API the page itself calls to list jobs — replayed daily
               3. job data embedded in the page (JSON-LD JobPosting, __NEXT_DATA__…)
               4. job links in the rendered page, grouped by their URL pattern
             Job systems with no adapter yet (iCIMS, Taleo, SuccessFactors, Oracle
             HCM, Phenom, Avature…) are reported by name, then handled by 2–4.

  extract    Daily, called by find-jobs.py. Replays saved recipes.

Policy: behaves like an ordinary browser. No stealth or fingerprint masking, a pause
between pages, a cap on pages per site, no logins. If a site shows a CAPTCHA or blocks
the request, the crawler stops for that company and says so, and the job search falls
back to Naukri or web search. It never tries to get around a block.

Usage:
  python3 scripts/careers-crawler.py discover --company "Acme" --url "https://careers.acme.com/search?q=engineer"
  python3 scripts/careers-crawler.py discover --all-unreachable --apply
  python3 scripts/careers-crawler.py extract --all --role "Software Engineer"
  python3 scripts/careers-crawler.py extract --company "Acme"
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
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ats_platforms import platform_from_url, probe  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(ROOT, "config", "companies.json")
USER_CONFIG_PATH = os.path.join(ROOT, "config", "user.json")
RESOLVER = os.path.join(ROOT, "scripts", "resolve-ats.py")

SETTLE_MS = 6000          # let client-rendered listings appear
PAGE_DELAY_MS = 4000      # politeness pause between page loads on one site
DEFAULT_MAX_PAGES = 3
MIN_RECIPE_LINKS = 3      # fewer jobs than this is not a listing
MAX_ATS_CANDIDATES = 8
MAX_JSON_BYTES = 3_000_000
LOAD_MORE_ROUNDS = 3

BLOCK_RE = re.compile(
    r"captcha|access denied|verify you are (a )?human|unusual traffic|are you a robot|"
    r"request blocked|attention required|pardon our interruption", re.I)
ATS_URL_RE = re.compile(
    r"https?://[^\s\"'<>\\]*(?:myworkdayjobs\.com|greenhouse\.io|lever\.co|ashbyhq\.com|"
    r"smartrecruiters\.com|workable\.com|recruitee\.com)[^\s\"'<>\\]*"
    r"|https?://[^\s\"'<>\\]+/api/(?:pcsx/search|apply/v2/jobs)[^\s\"'<>\\]*", re.I)
# Job systems we can recognise but have no adapter for. Reported, then scraped.
DETECT_ONLY = {
    "iCIMS": r"icims\.com", "Taleo": r"taleo\.net", "SuccessFactors": r"successfactors\.(?:com|eu)",
    "Oracle HCM": r"oraclecloud\.com/hcmUI|/CandidateExperience/", "Phenom": r"phenompeople\.com|cdn\.phenom",
    "Avature": r"avature\.net", "Jobvite": r"jobvite\.com", "BambooHR": r"bamboohr\.com",
    "Teamtailor": r"teamtailor\.com", "Personio": r"personio\.(?:de|com)", "Darwinbox": r"darwinbox\.in",
    "Zoho Recruit": r"zohorecruit\.", "Keka": r"keka\.com/careers", "Freshteam": r"freshteam\.com",
    "Breezy": r"breezy\.hr", "JazzHR": r"applytojob\.com", "Pinpoint": r"pinpointhq\.com",
    "Rippling ATS": r"ats\.rippling\.com", "Dover": r"app\.dover\.io",
}
JOB_SEGMENT_RE = re.compile(
    r"^(job|jobs|details|position|positions|opening|openings|requisition|requisitions|"
    r"vacancy|vacancies|role|roles|posting|postings|job-?details?|job-?description|"
    r"jobdetail|vacatures?|stellen(angebote)?|empleos?|emplois?|offres?)$", re.I)
JOB_QUERY_RE = re.compile(
    r"(?:^|&)((?:job|req|requisition|posting|position|vacancy|opening)[_-]?id|jid|gh_jid|jobid|pid)=([^&]+)", re.I)
JOB_TITLE_HINT = re.compile(
    r"engineer|developer|scientist|architect|analyst|designer|manager|lead|intern|"
    r"specialist|consultant|associate|director|administrator|researcher|programmer|sde|swe", re.I)
NOISE_TEXT_RE = re.compile(
    r"^(see full role description|where we.re hiring|apply( now)?|learn more|"
    r"view (job|details)|read more|details|share|save( job)?)$", re.I)
NOISE_URL_RE = re.compile(r"locationpicker|/apply(/|$|\?)|/share|^mailto:|^javascript:", re.I)
HUB_TEXT_RE = re.compile(
    r"\b(search|view|see|browse|explore|find)\b.{0,12}\b(jobs|openings|roles|positions|opportunities)\b", re.I)
LOAD_MORE_RE = re.compile(r"^\s*(load|show|see|view)\s+more\b.{0,20}$", re.I)

TITLE_KEYS = ("title", "jobTitle", "job_title", "postingTitle", "positionTitle", "externalTitle",
              "requisitionTitle", "jobName", "name")
URL_KEYS = ("url", "absolute_url", "applyUrl", "apply_url", "jobUrl", "job_url", "hostedUrl",
            "externalUrl", "canonicalUrl", "detailsUrl", "positionUrl", "externalPath", "link", "href")
ID_KEYS = ("id", "jobId", "job_id", "reqId", "req_id", "requisitionId", "jobReqId", "externalId",
           "displayJobId", "positionId", "jobCode", "slug")
LOC_KEYS = ("location", "locations", "locationName", "location_name", "locationsText", "primaryLocation",
            "jobLocation", "workLocation", "city", "cities")
PAGE_KEYS = ("page", "pageNumber", "pageNo", "page_number", "pg", "p")
OFFSET_KEYS = ("offset", "start", "from", "skip", "startIndex", "begin")


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


def location_re() -> re.Pattern:
    """Location words from config target_locations, plus 'remote'. Nothing hardcoded."""
    locs = load_json(USER_CONFIG_PATH, {}).get("target", {}).get("target_locations", []) or []
    words = {"remote", "hybrid"}
    for loc in locs:
        words.update(w.strip().lower() for w in loc.split(",") if w.strip())
    aliases = {"bengaluru": "bangalore", "bangalore": "bengaluru", "gurugram": "gurgaon",
               "gurgaon": "gurugram", "mumbai": "bombay", "chennai": "madras"}
    words.update(aliases[w] for w in list(words) if w in aliases)
    return re.compile("|".join(re.escape(w) for w in sorted(words)), re.I)


def matches_role(title: str, role: str) -> bool:
    if not role:
        return True
    t = title.lower()
    return any(w.lower() in t for w in role.split() if len(w) > 1)


def site_domain(host: str) -> str:
    parts = host.lower().split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host.lower()


def detect_systems(texts) -> list[str]:
    blob = "\n".join(texts)
    return [name for name, pat in DETECT_ONLY.items() if re.search(pat, blob, re.I)]


# ---------------------------------------------------------------------------
# job links
# ---------------------------------------------------------------------------

def link_key(href: str) -> tuple[str, str] | None:
    """(prefix, job key) for a URL that looks like a single posting, else None.

    Path style:  /en-in/details/200314122/x  -> ('/en-in/details/', '<url without query>')
    Query style: /job?jobId=123              -> ('/job?jobId=',     '<url>?jobId=123')
    """
    u = urlparse(href)
    parts = [p for p in u.path.split("/") if p]
    for i, seg in enumerate(parts):
        if JOB_SEGMENT_RE.match(seg) and i + 1 < len(parts):
            return "/" + "/".join(parts[:i + 1]) + "/", f"{u.scheme}://{u.netloc}{u.path.rstrip('/')}"
    m = JOB_QUERY_RE.search(u.query)
    if m:
        return (f"{u.path}?{m.group(1)}=",
                f"{u.scheme}://{u.netloc}{u.path}?{m.group(1)}={m.group(2)}")
    return None


def prefix_matches(href: str, prefix: str) -> bool:
    u = urlparse(href)
    if "?" in prefix:
        path, param = prefix.split("?", 1)
        return u.path == path and re.search(rf"(?:^|&){re.escape(param)}", u.query) is not None
    return u.path.startswith(prefix)


def group_job_links(links: list[dict], site: str | None = None, prefix: str | None = None) -> dict:
    """Collapse raw anchors into one entry per job URL, keeping the best title."""
    groups: dict[str, dict] = {}
    for link in links:
        href = link.get("h") or ""
        u = urlparse(href)
        if u.scheme not in ("http", "https") or NOISE_URL_RE.search(href):
            continue
        if site and not u.netloc.lower().endswith(site):
            continue
        lk = link_key(href)
        if not lk or (prefix and not prefix_matches(href, prefix)):
            continue
        p, key = lk
        g = groups.setdefault(key, {"url": key, "prefix": p, "site": site_domain(u.netloc),
                                    "title": "", "ctx": ""})
        text = (link.get("t") or "").strip()
        if text and not NOISE_TEXT_RE.match(text) and len(text) > len(g["title"]):
            g["title"] = text
        if len(link.get("ctx") or "") > len(g["ctx"]):
            g["ctx"] = link["ctx"]
    return {k: g for k, g in groups.items() if g["title"]}


def best_link_group(links: list[dict]) -> tuple[str, str, list[dict]] | None:
    groups = group_job_links(links)
    if len(groups) < MIN_RECIPE_LINKS:
        return None
    (site, prefix), n = Counter((g["site"], g["prefix"]) for g in groups.values()).most_common(1)[0]
    if n < MIN_RECIPE_LINKS:
        return None
    return site, prefix, [g for g in groups.values() if g["site"] == site and g["prefix"] == prefix]


# ---------------------------------------------------------------------------
# structured job data (JSON APIs, embedded page data, JSON-LD)
# ---------------------------------------------------------------------------

def _pick(d: dict, keys) -> str | None:
    lower = {k.lower(): k for k in d}
    for k in keys:
        real = k if k in d else lower.get(k.lower())
        if real is not None and d[real] not in (None, "", [], {}):
            return real
    return None


def flatten(v, depth=0) -> str:
    if v is None or depth > 3:
        return ""
    if isinstance(v, (str, int, float)):
        return str(v)
    if isinstance(v, list):
        return "; ".join(filter(None, (flatten(x, depth + 1) for x in v[:3])))
    if isinstance(v, dict):
        for k in ("name", "text", "label", "city", "locationName", "addressLocality", "address", "value"):
            if k in v:
                return flatten(v[k], depth + 1)
    return ""


def find_job_list(obj, path=(), depth=0) -> dict | None:
    """Largest list of job-shaped objects anywhere in a JSON document."""
    if depth > 7:
        return None
    best = None
    if isinstance(obj, list) and len(obj) >= MIN_RECIPE_LINKS and all(isinstance(x, dict) for x in obj[:10]):
        sample = obj[:20]
        tk = _pick(sample[0], TITLE_KEYS)
        if tk:
            titles = [x.get(tk) for x in sample if isinstance(x.get(tk), str) and 2 < len(x[tk]) < 160]
            jobby = sum(1 for t in titles if JOB_TITLE_HINT.search(t))
            linked = sum(1 for x in sample if _pick(x, URL_KEYS + ID_KEYS))
            if len(titles) >= MIN_RECIPE_LINKS and jobby >= len(titles) * 0.3 and linked >= len(titles) * 0.8:
                s0 = sample[0]
                best = {"path": list(path), "count": len(obj), "title_key": tk,
                        "url_key": _pick(s0, URL_KEYS), "id_key": _pick(s0, ID_KEYS),
                        "loc_key": _pick(s0, LOC_KEYS)}
    if isinstance(obj, dict):
        children = list(obj.items())
    elif isinstance(obj, list) and not best:
        # Wrappers like {"items": [{"requisitionList": [...]}]} (Oracle HCM and others)
        children = list(enumerate(obj[:3]))
    else:
        children = []
    for k, v in children:
        hit = find_job_list(v, path + (k,), depth + 1)
        if hit and (not best or hit["count"] > best["count"]):
            best = hit
    return best


def dig(obj, path: list):
    for k in path:
        if isinstance(k, int) and isinstance(obj, list):
            obj = obj[k] if k < len(obj) else None
        elif isinstance(obj, dict):
            obj = obj.get(k)
        else:
            return None
    return obj


def jsonld_postings(blobs: list[str]) -> list[dict]:
    """JobPosting objects from JSON-LD, wherever they sit (@graph, ItemList, arrays)."""
    out: list[dict] = []

    def walk(o, depth=0):
        if depth > 6:
            return
        if isinstance(o, list):
            for x in o:
                walk(x, depth + 1)
        elif isinstance(o, dict):
            t = o.get("@type")
            if t == "JobPosting" or (isinstance(t, list) and "JobPosting" in t):
                loc = o.get("jobLocation")
                out.append({"title": o.get("title") or "", "url": o.get("url") or "",
                            "location": flatten(dig(loc, ["address"]) if isinstance(loc, dict) else loc),
                            "posted": o.get("datePosted") or "",
                            "description": re.sub(r"<[^>]+>", " ", o.get("description") or "")[:400]})
            for k in ("@graph", "itemListElement", "item"):
                if k in o:
                    walk(o[k], depth + 1)
    for b in blobs:
        try:
            walk(json.loads(b))
        except Exception:
            continue
    return [p for p in out if p["title"]]


def items_to_jobs(items: list, spec: dict, base_url: str, listing_url: str) -> list[dict]:
    jobs = []
    for x in items:
        if not isinstance(x, dict):
            continue
        title = x.get(spec["title_key"])
        if not isinstance(title, str) or not title.strip():
            continue
        url = ""
        if spec.get("url_key") and isinstance(x.get(spec["url_key"]), str):
            url = urljoin(spec.get("url_base") or base_url, x[spec["url_key"]])
        elif spec.get("url_template") and spec.get("id_key") and x.get(spec["id_key"]) is not None:
            url = spec["url_template"].replace("{id}", str(x[spec["id_key"]]))
        jobs.append({"title": title.strip(), "url": url or listing_url,
                     "location": flatten(x.get(spec["loc_key"])) if spec.get("loc_key") else "",
                     "id": str(x.get(spec["id_key"])) if spec.get("id_key") else ""})
    return jobs


def url_template(items: list, spec: dict, links: list[dict]) -> str | None:
    """Work out the posting URL pattern by finding a page link that contains a job's id."""
    if not spec.get("id_key"):
        return None
    hrefs = [l.get("h") or "" for l in links]
    for x in items[:10]:
        ident = str(x.get(spec["id_key"]) or "")
        if len(ident) < 3:
            continue
        for h in hrefs:
            if ident in h:
                return h.replace(ident, "{id}", 1).split("#")[0]
    return None


def bump_page(url: str, body: str | None, step: int) -> tuple[str, str | None] | None:
    """Next page of an API request, by incrementing a page or offset parameter."""
    # Regex rather than query parsing: some APIs nest paging inside another parameter,
    # e.g. finder=findReqs;limit=25,offset=0
    for keys, inc in ((OFFSET_KEYS, step), (PAGE_KEYS, 1)):
        pat = re.compile(rf"([?&;,](?:{'|'.join(map(re.escape, keys))})=)(\d+)")
        if pat.search(url):
            return pat.sub(lambda m: m.group(1) + str(int(m.group(2)) + inc), url, count=1), body
    if body:
        try:
            data = json.loads(body)
        except Exception:
            return None
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, int) and (k in PAGE_KEYS or k in OFFSET_KEYS):
                    data[k] = v + (1 if k in PAGE_KEYS else step)
                    return url, json.dumps(data)
    return None


# ---------------------------------------------------------------------------
# browser helpers
# ---------------------------------------------------------------------------

async def expand_listing(page) -> None:
    """Click 'load more' / 'show more' a few times, as a reader would."""
    for _ in range(LOAD_MORE_ROUNDS):
        btn = page.get_by_role("button", name=LOAD_MORE_RE)
        try:
            if await btn.count() == 0:
                return
            await btn.first.click(timeout=3000)
            await page.wait_for_timeout(2500)
        except Exception:
            return


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
    blocked = status in (403, 429) or bool(BLOCK_RE.search(text))
    if not blocked:
        await expand_listing(page)
    return status, blocked


LINKS_JS = """els => els.map(a => {
    const box = a.closest('li, tr, article, [role=listitem]') || a.parentElement;
    return {h: a.href, t: (a.innerText || '').trim().split('\\n')[0].slice(0, 140),
            ctx: box ? (box.innerText || '').slice(0, 300) : ''};
})"""
SCRIPTS_JS = """() => [...document.querySelectorAll(
    'script[type="application/ld+json"], script[type="application/json"], script#__NEXT_DATA__')]
    .map(s => ({ld: s.type === 'application/ld+json', text: s.textContent}))"""


async def collect_links(page) -> list[dict]:
    links: list[dict] = []
    for frame in page.frames:  # listings are sometimes inside an iframe
        try:
            links += await frame.eval_on_selector_all("a[href]", LINKS_JS)
        except Exception:
            continue
    return links


async def collect_scripts(page) -> list[dict]:
    out: list[dict] = []
    for frame in page.frames:
        try:
            out += await frame.evaluate(SCRIPTS_JS)
        except Exception:
            continue
    return [s for s in out if s.get("text") and len(s["text"]) < MAX_JSON_BYTES]


def embedded_hit(scripts: list[dict]) -> dict | None:
    best = None
    for i, s in enumerate(scripts):
        if s["ld"]:
            continue
        try:
            hit = find_job_list(json.loads(s["text"]))
        except Exception:
            continue
        if hit and (not best or hit["count"] > best["count"]):
            best = dict(hit, script_index=i)
    return best


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


async def fetch_api(page, recipe: dict, url: str, body: str | None):
    if recipe.get("method") == "POST":
        r = await page.request.post(url, data=body or "", headers={"content-type": "application/json"})
    else:
        r = await page.request.get(url)
    if r.status in (403, 429):
        return r.status, None
    try:
        return r.status, await r.json()
    except Exception:
        return r.status, None


# ---------------------------------------------------------------------------
# discover
# ---------------------------------------------------------------------------

async def discover_one(browser, name: str, url: str) -> dict:
    result: dict = {"name": name, "url": url}
    ctx = await browser.new_context(locale="en-IN", viewport={"width": 1366, "height": 900})
    page = await ctx.new_page()
    network: list[str] = []
    api_hits: list[dict] = []
    pending: list[asyncio.Task] = []

    async def on_response(resp):
        try:
            req = resp.request
            if req.resource_type not in ("xhr", "fetch") or req.method not in ("GET", "POST"):
                return
            if "json" not in (resp.headers.get("content-type") or ""):
                return
            text = await resp.text()
            if len(text) > MAX_JSON_BYTES:
                return
            hit = find_job_list(json.loads(text))
            if hit:
                api_hits.append(dict(hit, api_url=resp.url, method=req.method,
                                     body=req.post_data if req.method == "POST" else None,
                                     _items=dig(json.loads(text), hit["path"])))
        except Exception:
            return

    page.on("request", lambda r: network.append(r.url))
    page.on("response", lambda r: pending.append(asyncio.ensure_future(on_response(r))))
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
        if not api_hits and len(group_job_links(links, site)) < MIN_RECIPE_LINKS:
            hub = pick_hub(links, site, page.url)
            if hub:
                await page.wait_for_timeout(PAGE_DELAY_MS)
                status, blocked = await load(page, hub)
                if blocked:
                    result.update(blocked=True, status=status)
                    return result
                html += await page.content()
                links += await collect_links(page)
                result["followed"] = page.url

        await asyncio.gather(*pending, return_exceptions=True)
        scripts = await collect_scripts(page)
        result["final_url"] = page.url
        result["_links"] = links
        result["_scripts"] = scripts
        every = set(network) | {l["h"] for l in links} | set(ATS_URL_RE.findall(html))
        result["_candidates"] = sorted(u for u in every if ATS_URL_RE.match(u))
        result["detected"] = detect_systems(list(every) + [html[:200000]])

        # Replay the best API once, as the recipe would, before trusting it.
        for hit in sorted(api_hits, key=lambda h: -h["count"])[:3]:
            st, data = await fetch_api(page, hit, hit["api_url"], hit["body"])
            items = dig(data, hit["path"]) if data is not None else None
            if isinstance(items, list) and len(items) >= MIN_RECIPE_LINKS:
                hit["url_template"] = url_template(items, hit, links)
                result["_api"] = hit
                break
    except Exception as e:
        result["error"] = f"could not load: {str(e)[:90]}"
    finally:
        await ctx.close()
    return result


def classify(result: dict) -> dict:
    """Verify ATS candidates (network I/O), else pick the best recipe."""
    if result.get("blocked") or result.get("error"):
        return result
    links = result.pop("_links", [])
    scripts = result.pop("_scripts", [])
    api = result.pop("_api", None)
    final_url = result.get("final_url") or result["url"]
    today = date.today().isoformat()

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
        return result

    if api:
        items = api.pop("_items") or []
        spec = {k: api[k] for k in ("path", "title_key", "url_key", "id_key", "loc_key", "url_template")}
        jobs = items_to_jobs(items, spec, api["api_url"], final_url)
        result["recipe"] = dict(spec, mode="api", listing_url=final_url, api_url=api["api_url"],
                                method=api["method"], body=api["body"], jobs_seen=api["count"],
                                verified_at=today)
        result["sample"] = [j["title"] for j in jobs[:3]]
        if not spec["url_key"] and not spec["url_template"]:
            result["warning"] = "API has no posting URLs; listings will link to the careers page"
        return result

    postings = jsonld_postings([s["text"] for s in scripts if s["ld"]])
    if len(postings) >= MIN_RECIPE_LINKS:
        result["recipe"] = {"mode": "jsonld", "listing_url": final_url, "jobs_seen": len(postings),
                            "verified_at": today}
        result["sample"] = [p["title"] for p in postings[:3]]
        return result

    emb = embedded_hit(scripts)
    if emb:
        data = json.loads(scripts[emb["script_index"]]["text"])
        items = dig(data, emb["path"]) or []
        spec = {k: emb[k] for k in ("path", "title_key", "url_key", "id_key", "loc_key")}
        spec["url_template"] = url_template(items, emb, links)
        result["recipe"] = dict(spec, mode="embedded", listing_url=final_url,
                                jobs_seen=emb["count"], verified_at=today)
        result["sample"] = [j["title"] for j in items_to_jobs(items, spec, final_url, final_url)[:3]]
        return result

    best = best_link_group(links)
    if best:
        site, prefix, kept = best
        result["recipe"] = {"mode": "links", "listing_url": final_url, "link_prefix": prefix,
                            "site": site, "jobs_seen": len(kept), "verified_at": today}
        result["sample"] = [g["title"] for g in kept[:3]]
    return result


def apply_result(result: dict) -> str:
    """Write one finding. Reloads the registry each time: resolve-ats may have just written it."""
    name = result["name"]
    if result.get("ats"):
        a = result["ats"]
        out = subprocess.run([sys.executable, RESOLVER, "--from-url", name, a["url"]],
                             capture_output=True, text=True, timeout=240)
        msg = (out.stderr or out.stdout).strip()
        return msg.splitlines()[-1] if msg else "pinned"
    if result.get("recipe"):
        reg = load_json(REGISTRY_PATH, {"companies": {}})
        companies = reg.setdefault("companies", {})
        key = name.lower().strip()
        entry = companies.get(key) or {"name": name, "platform": "none", "slug": "",
                                       "status": "unresolved", "jobs_seen": 0,
                                       "board_url": "", "careers_url": ""}
        entry["scrape"] = result["recipe"]
        if not entry.get("careers_url"):
            entry["careers_url"] = result["url"]
        companies[key] = entry
        save_registry(reg)
        return f"saved {result['recipe']['mode']} recipe ({result['recipe']['jobs_seen']} jobs)"
    return ""


def report_discovery(result: dict, applied: str) -> None:
    name = result["name"]
    systems = f" · job system: {', '.join(result['detected'])} (no adapter)" if result.get("detected") else ""
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
        where = {"api": f"page API {urlparse(r.get('api_url', '')).path}",
                 "jsonld": "JSON-LD JobPosting data", "embedded": "job data embedded in the page",
                 "links": f"job links {r.get('link_prefix')} on {r.get('site')}"}[r["mode"]]
        print(f"  {name}: {r['mode']} recipe — {where} ({r['jobs_seen']} jobs){systems} "
              f"e.g. {result.get('sample')}", file=sys.stderr)
        if result.get("warning"):
            print(f"     note: {result['warning']}", file=sys.stderr)
        print(f"     {applied or 'save with --apply'}", file=sys.stderr)
    else:
        print(f"  {name}: nothing usable{systems} — no API, page data or job links on "
              f"{result.get('final_url') or result['url']}. Try a search-results URL with --url, "
              f"or use Naukri / web search", file=sys.stderr)


async def run_discover(targets: list[tuple[str, str]], apply: bool) -> None:
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
        applied = apply_result(result) if apply else ""
        report_discovery(result, applied)


# ---------------------------------------------------------------------------
# extract
# ---------------------------------------------------------------------------

async def next_page_url(page) -> str | None:
    return await page.evaluate("""() => {
        const a = document.querySelector('a[rel=next], a[aria-label*="next" i], a[title*="next" i]');
        return a && a.href ? a.href : null;
    }""")


async def extract_links(page, recipe: dict, max_pages: int) -> tuple[list[dict], int, str]:
    found: dict[str, dict] = {}
    url, pages = recipe["listing_url"], 0
    while url and pages < max_pages:
        status, blocked = await load(page, url)
        if blocked:
            return list(found.values()), pages, f"blocked (HTTP {status}) — stopped"
        for key, g in group_job_links(await collect_links(page), recipe.get("site"),
                                      recipe["link_prefix"]).items():
            found.setdefault(key, g)
        pages += 1
        nxt = await next_page_url(page)
        if not nxt or nxt == url:
            break
        url = nxt
        await page.wait_for_timeout(PAGE_DELAY_MS)
    loc = location_re()
    out = []
    for g in found.values():
        lines = [l.strip() for l in re.split(r"[\n\t]", g["ctx"] or "") if l.strip()]
        location = next((l for l in lines if l != g["title"] and len(l) < 60 and loc.search(l)), "")
        out.append({"title": g["title"], "url": g["url"], "location": location})
    return out, pages, ""


async def extract_api(page, recipe: dict, max_pages: int) -> tuple[list[dict], int, str]:
    status, blocked = await load(page, recipe["listing_url"])  # same session the site gives a visitor
    if blocked:
        return [], 0, f"blocked (HTTP {status}) — stopped"
    jobs: list[dict] = []
    seen: set[str] = set()
    url, body, pages = recipe["api_url"], recipe.get("body"), 0
    while pages < max_pages:
        st, data = await fetch_api(page, recipe, url, body)
        if data is None:
            note = f"blocked (HTTP {st}) — stopped" if st in (403, 429) else f"API returned HTTP {st}"
            return jobs, pages, "" if jobs else note
        items = dig(data, recipe["path"])
        if not isinstance(items, list):
            break
        pages += 1
        fresh = [j for j in items_to_jobs(items, recipe, recipe["api_url"], recipe["listing_url"])
                 if (j["id"] or j["url"] + j["title"]) not in seen]
        if not fresh:
            break
        seen.update(j["id"] or j["url"] + j["title"] for j in fresh)
        jobs += fresh
        nxt = bump_page(url, body, len(items))
        if not nxt:
            break
        url, body = nxt
        await page.wait_for_timeout(PAGE_DELAY_MS)
    return jobs, pages, ""


async def extract_page_data(page, recipe: dict) -> tuple[list[dict], int, str]:
    status, blocked = await load(page, recipe["listing_url"])
    if blocked:
        return [], 0, f"blocked (HTTP {status}) — stopped"
    scripts = await collect_scripts(page)
    if recipe["mode"] == "jsonld":
        return jsonld_postings([s["text"] for s in scripts if s["ld"]]), 1, ""
    for s in scripts:
        if s["ld"]:
            continue
        try:
            items = dig(json.loads(s["text"]), recipe["path"])
        except Exception:
            continue
        if isinstance(items, list) and items:
            return items_to_jobs(items, recipe, recipe["listing_url"], recipe["listing_url"]), 1, ""
    return [], 1, ""


async def extract_one(browser, entry: dict, role: str, max_pages: int) -> list[dict]:
    recipe, name = entry["scrape"], entry["name"]
    mode = recipe.get("mode", "links")
    ctx = await browser.new_context(locale="en-IN", viewport={"width": 1366, "height": 900})
    page = await ctx.new_page()
    raw, pages, note = [], 0, ""
    try:
        if mode == "api":
            raw, pages, note = await extract_api(page, recipe, max_pages)
        elif mode in ("jsonld", "embedded"):
            raw, pages, note = await extract_page_data(page, recipe)
        else:
            raw, pages, note = await extract_links(page, recipe, max_pages)
    except Exception as e:
        note = f"error: {str(e)[:80]}"
    finally:
        await ctx.close()

    jobs = [{"title": j["title"], "company": name, "location": j.get("location", ""),
             "experience": "", "salary": "Not disclosed", "description": j.get("description", ""),
             "posted": j.get("posted", ""), "tags": [], "url": j["url"], "source": "careers"}
            for j in raw if matches_role(j["title"], role)]
    if not raw and not note:
        note = f"{mode} recipe returned nothing — the site may have changed; re-run discover"
    print(f"  {name} [{mode}]: {len(jobs)} matched / {len(raw)} found over {pages} page(s)"
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

    d = sub.add_parser("discover", help="Find the job system or data behind a careers page (slow)")
    d.add_argument("--company", help="Company name; uses its registry careers_url unless --url given. "
                                     "Need not be in the registry yet")
    d.add_argument("--url", help="Careers or search-results URL to inspect (any site)")
    d.add_argument("--all-unreachable", action="store_true",
                   help="Every registry company with no fetchable board and a careers_url")
    d.add_argument("--apply", action="store_true",
                   help="Pin found boards and save recipes to the registry")

    e = sub.add_parser("extract", help="Replay saved recipes (daily)")
    e.add_argument("--all", action="store_true", help="Every company with a recipe")
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
                if fetchable or c.get("scrape"):
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
            if args.apply:
                ap.error("--apply needs --company, so the recipe is saved under a name")
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
        print("No recipes saved. Run: careers-crawler.py discover ... --apply", file=sys.stderr)
        print(json.dumps([]))
        return
    asyncio.run(run_extract(entries, args.role or default_role(), args.max_pages))


if __name__ == "__main__":
    main()
