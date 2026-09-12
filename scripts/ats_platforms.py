#!/usr/bin/env python3
"""
Career OS — ATS Platform Definitions

Single source of truth for every supported ATS platform: how to probe it,
how to fetch from it, and how to normalize its response.

Nothing company-specific lives here. Company -> platform/slug mappings live in
config/companies.json, built by scripts/resolve-ats.py.

Add a new platform by appending one entry to PLATFORMS. Both the resolver and
the fetcher pick it up automatically.
"""

import html
import json
import re
import urllib.parse
import urllib.request

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CareerOS/1.0)",
    "Accept": "application/json",
}

DEFAULT_TIMEOUT = 12


def http_json(url: str, timeout: int = DEFAULT_TIMEOUT):
    """GET a URL and parse JSON. Returns None on any failure."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception:
        return None


def post_json(url: str, body: dict, timeout: int = DEFAULT_TIMEOUT):
    """POST JSON and parse the JSON response. Returns None on any failure."""
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode(),
            headers={**HEADERS, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception:
        return None


def strip_html(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _first_nonempty(*vals) -> str:
    for v in vals:
        if v:
            return str(v)
    return ""


# ---------------------------------------------------------------------------
# Per-platform parsers. Each returns a list of normalized job dicts.
# ---------------------------------------------------------------------------

def _parse_greenhouse(data) -> list[dict]:
    if not isinstance(data, dict) or "jobs" not in data:
        return []
    out = []
    for j in data.get("jobs") or []:
        loc = ""
        location = j.get("location")
        if isinstance(location, dict):
            loc = location.get("name", "")
        if not loc:
            loc = ", ".join(o.get("name", "") for o in (j.get("offices") or []) if o.get("name"))
        out.append({
            "title": j.get("title", ""),
            "location": loc,
            "description": strip_html(j.get("content", "")),
            "posted": j.get("updated_at", "") or j.get("first_published", ""),
            "tags": [d.get("name", "") for d in (j.get("departments") or []) if d.get("name")],
            "url": j.get("absolute_url", ""),
        })
    return out


def _parse_lever(data) -> list[dict]:
    if not isinstance(data, list):
        return []
    out = []
    for j in data:
        cats = j.get("categories") or {}
        out.append({
            "title": j.get("text", ""),
            "location": _first_nonempty(cats.get("location"), j.get("country")),
            "description": strip_html(_first_nonempty(j.get("descriptionPlain"), j.get("description"))),
            "posted": "",
            "tags": [t for t in [cats.get("team"), cats.get("department"), cats.get("commitment")] if t],
            "url": j.get("hostedUrl", ""),
        })
    return out


def _parse_ashby(data) -> list[dict]:
    if not isinstance(data, dict):
        return []
    jobs = data.get("jobs") or (data.get("data") or {}).get("jobBoard", {}).get("jobPostings") or []
    out = []
    for j in jobs:
        out.append({
            "title": _first_nonempty(j.get("title"), j.get("jobTitle")),
            "location": _first_nonempty(j.get("location"), j.get("locationName")),
            "description": strip_html(_first_nonempty(j.get("descriptionPlain"), j.get("descriptionHtml"))),
            "posted": j.get("publishedAt", ""),
            "tags": [t for t in [j.get("department"), j.get("team"), j.get("employmentType")] if t],
            "url": _first_nonempty(j.get("jobUrl"), j.get("applyUrl"), j.get("externalLink")),
        })
    return out


def _parse_workable(data) -> list[dict]:
    if not isinstance(data, dict):
        return []
    out = []
    for j in data.get("jobs") or []:
        out.append({
            "title": j.get("title", ""),
            "location": _first_nonempty(
                j.get("location", {}).get("city") if isinstance(j.get("location"), dict) else None,
                j.get("city"), j.get("country"),
            ),
            "description": strip_html(_first_nonempty(j.get("description"), j.get("requirements"))),
            "posted": j.get("published_on", ""),
            "tags": [t for t in [j.get("department"), j.get("employment_type")] if t],
            "url": _first_nonempty(j.get("application_url"), j.get("url"), j.get("shortlink")),
        })
    return out


def _parse_smartrecruiters(data) -> list[dict]:
    if not isinstance(data, dict):
        return []
    out = []
    for j in data.get("content") or []:
        loc = j.get("location") or {}
        out.append({
            "title": j.get("name", ""),
            "location": ", ".join(x for x in [loc.get("city"), loc.get("country")] if x),
            "description": "",  # SmartRecruiters requires a second call per posting
            "posted": j.get("releasedDate", ""),
            "tags": [t for t in [(j.get("department") or {}).get("label"),
                                 (j.get("function") or {}).get("label")] if t],
            "url": (j.get("ref") or "").replace("api.smartrecruiters.com/v1/companies",
                                                "jobs.smartrecruiters.com") or "",
        })
    return out


def _parse_recruitee(data) -> list[dict]:
    if not isinstance(data, dict):
        return []
    out = []
    for j in data.get("offers") or []:
        out.append({
            "title": j.get("title", ""),
            "location": _first_nonempty(j.get("location"), j.get("city"), j.get("country")),
            "description": strip_html(_first_nonempty(j.get("description"), j.get("requirements"))),
            "posted": j.get("published_at", ""),
            "tags": [t for t in [j.get("department"), j.get("employment_type_code")] if t],
            "url": _first_nonempty(j.get("careers_url"), j.get("careers_apply_url")),
        })
    return out


# ---------------------------------------------------------------------------
# Workday — POST-based, and the slug is compound: "tenant/wdN/site"
# e.g. "nvidia/wd5/NvidiaExternalCareerSite". Covers most large enterprises.
# ---------------------------------------------------------------------------

WORKDAY_PAGE = 20   # Workday rejects limit > 20 with HTTP 400
WORKDAY_MAX = 500   # cap per company; these boards run to thousands

WD_NUMS = [5, 1, 3, 2, 101, 103, 10, 12]
WD_SITE_PATTERNS = [
    "{T}ExternalCareerSite", "{t}careers", "External", "Careers", "careers",
    "External_Career_Site", "{T}_External_Career_Site", "{T}Careers",
    "{t}_careers", "CareerSite", "Global", "Search",
]


def parse_workday_slug(slug: str) -> tuple[str, str, str] | None:
    """'nvidia/wd5/NvidiaExternalCareerSite' -> ('nvidia', 'wd5', 'Nvidia…')"""
    parts = [p for p in (slug or "").split("/") if p]
    if len(parts) != 3:
        return None
    return parts[0], parts[1], parts[2]


def workday_url(slug: str) -> str:
    parsed = parse_workday_slug(slug)
    if not parsed:
        return ""
    tenant, wd, site = parsed
    return f"https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"


def _fetch_workday(slug: str) -> list[dict] | None:
    url = workday_url(slug)
    if not url:
        return None
    parsed = parse_workday_slug(slug)
    tenant, wd, site = parsed
    base = f"https://{tenant}.{wd}.myworkdayjobs.com/en-US/{site}"

    out: list[dict] = []
    offset = 0
    while offset < WORKDAY_MAX:
        data = post_json(url, {"appliedFacets": {}, "limit": WORKDAY_PAGE,
                               "offset": offset, "searchText": ""})
        if not isinstance(data, dict) or "jobPostings" not in data:
            return out if out else None
        page = data.get("jobPostings") or []
        if not page:
            break
        for j in page:
            path = j.get("externalPath", "")
            out.append({
                "title": j.get("title", ""),
                "location": _first_nonempty(j.get("locationsText"), j.get("location")),
                "description": " ".join(j.get("bulletFields") or []),
                "posted": j.get("postedOn", ""),
                "tags": [t for t in (j.get("bulletFields") or []) if t][:3],
                "url": f"{base}{path}" if path else base,
            })
        if len(page) < WORKDAY_PAGE:
            break
        offset += WORKDAY_PAGE
    return out


# ---------------------------------------------------------------------------
# Eightfold AI — powers many large-enterprise careers portals (Netflix, and a
# long tail of others). Slug is compound: "host|domain".
#   e.g. "explore.jobs.netflix.net|netflix.com"
# ---------------------------------------------------------------------------

EIGHTFOLD_PAGE = 50
EIGHTFOLD_MAX = 500


def _fetch_eightfold(slug: str) -> list[dict] | None:
    if "|" not in (slug or ""):
        return None
    host, domain = slug.split("|", 1)
    out: list[dict] = []
    start = 0
    while start < EIGHTFOLD_MAX:
        url = (f"https://{host}/api/apply/v2/jobs?domain={domain}"
               f"&start={start}&num={EIGHTFOLD_PAGE}")
        data = http_json(url)
        if not isinstance(data, dict):
            return out if out else None
        page = data.get("positions") or []
        if not page:
            break
        total = data.get("count") or 0
        for j in page:
            loc = j.get("location") or ""
            if not loc and isinstance(j.get("locations"), list):
                loc = ", ".join(str(x) for x in j["locations"][:3])
            out.append({
                "title": j.get("name", ""),
                "location": loc,
                "description": strip_html(j.get("job_description", "")),
                "posted": str(j.get("t_create", "")),
                "tags": [t for t in [j.get("department"), j.get("work_location_option")] if t],
                "url": j.get("canonicalPositionUrl", ""),
            })
        # Eightfold silently caps page size below what we ask for, so advance by
        # what we actually got and stop on the reported total, not on a short page.
        start += len(page)
        if total and start >= total:
            break
    return out


# ---------------------------------------------------------------------------
# Amazon — its own public search JSON. Slug is unused but kept for uniformity.
# ---------------------------------------------------------------------------

AMAZON_URL = ("https://www.amazon.jobs/en/search.json"
              "?base_query={q}&result_limit=100&offset={offset}&sort=recent")
AMAZON_MAX = 300


def _fetch_amazon(slug: str) -> list[dict] | None:
    # slug optionally carries a query hint, e.g. "software engineer"
    query = urllib.parse.quote_plus(slug or "software engineer")
    out: list[dict] = []
    offset = 0
    while offset < AMAZON_MAX:
        data = http_json(AMAZON_URL.format(q=query, offset=offset))
        if not isinstance(data, dict):
            return out if out else None
        page = data.get("jobs") or []
        if not page:
            break
        for j in page:
            loc = j.get("location") or ", ".join(
                x for x in [j.get("city"), j.get("state"), j.get("country_code")] if x)
            path = j.get("job_path", "")
            out.append({
                "title": j.get("title", ""),
                "location": loc,
                "description": strip_html(_first_nonempty(
                    j.get("description_short"), j.get("description"),
                    j.get("basic_qualifications"))),
                "posted": j.get("posted_date", ""),
                "tags": [t for t in [j.get("job_category"), j.get("business_category")] if t],
                "url": f"https://www.amazon.jobs{path}" if path else "https://www.amazon.jobs",
            })
        if len(page) < 100:
            break
        offset += 100
    return out


def discover_workday(company: str) -> str | None:
    """Probe the Workday host/site matrix. Returns a compound slug or None."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    tenant = re.sub(r"[^\w]", "", company.lower())
    if not tenant:
        return None

    def attempt(wd_num: int, site: str) -> str | None:
        url = f"https://{tenant}.wd{wd_num}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
        data = post_json(url, {"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""},
                         timeout=7)
        if isinstance(data, dict) and "jobPostings" in data and data.get("total", 0) > 0:
            return f"{tenant}/wd{wd_num}/{site}"
        return None

    combos = [(n, s.format(t=tenant, T=tenant.capitalize()))
              for n in WD_NUMS for s in WD_SITE_PATTERNS]
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(attempt, n, s) for n, s in combos]
        for fut in as_completed(futures):
            try:
                hit = fut.result()
            except Exception:
                continue
            if hit:
                for f in futures:
                    f.cancel()
                return hit
    return None


# ---------------------------------------------------------------------------
# Platform registry — the only place a platform is defined.
#   url:    endpoint template, {slug} substituted
#   parse:  response -> list of normalized jobs
# ---------------------------------------------------------------------------

PLATFORMS: dict[str, dict] = {
    "greenhouse": {
        "url": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
        "parse": _parse_greenhouse,
        "board_url": "https://boards.greenhouse.io/{slug}",
        # 404s on an unknown slug, so any parseable response proves the board exists.
        "exists": lambda d: isinstance(d, dict) and "jobs" in d,
    },
    "lever": {
        "url": "https://api.lever.co/v0/postings/{slug}?mode=json&limit=200",
        "parse": _parse_lever,
        "board_url": "https://jobs.lever.co/{slug}",
        "exists": lambda d: isinstance(d, list),
    },
    "ashby": {
        "url": "https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true",
        "parse": _parse_ashby,
        "board_url": "https://jobs.ashbyhq.com/{slug}",
        "exists": lambda d: isinstance(d, dict) and ("jobs" in d or "data" in d),
    },
    "workable": {
        "url": "https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true",
        "parse": _parse_workable,
        "board_url": "https://apply.workable.com/{slug}",
        # Returns a named account object; bare "Not Found" for unknown slugs.
        "exists": lambda d: isinstance(d, dict) and bool(d.get("name")),
    },
    "smartrecruiters": {
        "url": "https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100",
        "parse": _parse_smartrecruiters,
        "board_url": "https://jobs.smartrecruiters.com/{slug}",
        # Returns 200 + empty content for ANY slug, real or not. The only proof
        # a board exists is at least one posting — otherwise it is indistinguishable
        # from a company that has no SmartRecruiters account at all.
        "exists": lambda d: isinstance(d, dict) and (d.get("totalFound") or 0) > 0,
    },
    "recruitee": {
        "url": "https://{slug}.recruitee.com/api/offers/",
        "parse": _parse_recruitee,
        "board_url": "https://{slug}.recruitee.com",
        "exists": lambda d: isinstance(d, dict) and "offers" in d,
    },
    "workday": {
        # Compound slug: "tenant/wdN/site". POST-based, so it has a custom fetcher.
        "url": None,
        "parse": None,
        "fetch": _fetch_workday,
        "discover": discover_workday,
        "board_url_fn": lambda slug: (
            lambda p: f"https://{p[0]}.{p[1]}.myworkdayjobs.com/en-US/{p[2]}" if p else ""
        )(parse_workday_slug(slug)),
    },
    "eightfold": {
        # Compound slug: "host|domain", e.g. "explore.jobs.netflix.net|netflix.com".
        # No auto-discovery: the host is company-specific and unguessable. Pin it
        # with --from-url after finding the careers portal.
        "url": None,
        "parse": None,
        "fetch": _fetch_eightfold,
        "board_url_fn": lambda slug: f"https://{slug.split('|')[0]}" if "|" in slug else "",
    },
    "amazon": {
        # Amazon's own public search JSON. Slug carries an optional query hint.
        "url": None,
        "parse": None,
        "fetch": _fetch_amazon,
        "board_url_fn": lambda slug: "https://www.amazon.jobs",
    },
}

# Order matters for auto-discovery: cheapest and most common first.
# Workday is last because discovery costs a probe matrix, not a single request.
PROBE_ORDER = ["greenhouse", "lever", "ashby", "recruitee", "workable",
               "smartrecruiters", "workday"]


def fetch_jobs(platform: str, slug: str) -> list[dict] | None:
    """Fetch and normalize all jobs for a platform+slug. None = endpoint failed."""
    spec = PLATFORMS.get(platform)
    if not spec:
        return None
    if spec.get("fetch"):
        return spec["fetch"](slug)
    data = http_json(spec["url"].format(slug=slug))
    if data is None or not spec["exists"](data):
        return None
    return spec["parse"](data)


def probe(platform: str, slug: str) -> int | None:
    """
    Return the job count if this platform+slug is a real, live board, else None.

    A board that exists but currently lists zero jobs returns 0, not None —
    the caller decides whether a dormant board is good enough. Distinguishing
    the two matters: many large companies keep a vestigial Workable or
    Greenhouse account while actually hiring through Workday.
    """
    jobs = fetch_jobs(platform, slug)
    if jobs is None:
        return None
    return len(jobs)


# ---------------------------------------------------------------------------
# Owner verification — guards against slug collisions.
#
# ATS slugs are first-come-first-served. "google.recruitee.com" belongs to an
# unrelated Dutch marketing agency, not Google. Without this check the resolver
# happily points your job search at the wrong company's board.
# ---------------------------------------------------------------------------

_CORP_SUFFIXES = r"\b(inc|llc|ltd|limited|corp|corporation|company|co|plc|gmbh|bv|nv|" \
                 r"pvt|private|technologies|technology|labs|group|holdings|international)\b"


def _normalize_name(name: str) -> str:
    n = re.sub(r"[^\w\s]", " ", (name or "").lower())
    n = re.sub(_CORP_SUFFIXES, " ", n)
    return re.sub(r"\s+", "", n).strip()


def names_match(query: str, owner: str) -> bool:
    """Loose match between the company we asked for and the board's own name."""
    q, o = _normalize_name(query), _normalize_name(owner)
    if not q or not o:
        return True  # nothing to compare — don't block on missing data
    return q in o or o in q


def owner_name(platform: str, slug: str, data=None) -> str | None:
    """
    The company name the board itself declares, or None if the platform
    doesn't expose one. Used to verify we resolved the right company.
    """
    if platform == "workable":
        d = data if data is not None else http_json(
            PLATFORMS["workable"]["url"].format(slug=slug))
        return d.get("name") if isinstance(d, dict) else None

    if platform == "greenhouse":
        d = http_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}")
        return d.get("name") if isinstance(d, dict) else None

    if platform == "recruitee":
        d = data if data is not None else http_json(
            PLATFORMS["recruitee"]["url"].format(slug=slug))
        offers = (d or {}).get("offers") or []
        return offers[0].get("company_name") if offers else None

    if platform == "smartrecruiters":
        d = http_json(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=1")
        content = (d or {}).get("content") or []
        return (content[0].get("company") or {}).get("name") if content else None

    # lever, ashby and workday don't expose a reliable board-owner name.
    return None


def slug_candidates(name: str) -> list[str]:
    """Generate plausible ATS slugs from a company name."""
    clean = re.sub(r"[^\w\s-]", "", name.lower().strip())
    variants = [
        clean.replace(" ", ""),
        clean.replace(" ", "-"),
        clean,
        re.sub(r"\b(technologies|technology|labs|inc|ltd|limited|pvt|private|corp|corporation|company|co)\b",
               "", clean).strip().replace(" ", ""),
    ]
    return [v for v in dict.fromkeys(variants) if v]


def platform_from_url(url: str) -> tuple[str, str] | None:
    """
    Work out (platform, slug) from a pasted ATS or careers URL.

    This is the escape hatch from slug guessing. Auto-discovery only tries
    variations of the company name, so it misses boards registered under a legal
    entity — Razorpay's Greenhouse slug is "razorpaysoftwareprivatelimited", which
    no name-based guess would ever produce. Search the web for the real board,
    paste the URL here, and the mapping is exact.

    Returns None if the URL isn't a recognizable ATS board.
    """
    u = (url or "").strip()
    if not u:
        return None
    if not u.startswith("http"):
        u = "https://" + u

    parsed = urllib.parse.urlparse(u)
    host = (parsed.netloc or "").lower()
    path = [p for p in (parsed.path or "").split("/") if p]

    def seg_after(marker: str) -> str | None:
        for i, p in enumerate(path):
            if p == marker and i + 1 < len(path):
                return path[i + 1]
        return None

    # Greenhouse: boards.greenhouse.io/<slug>, job-boards.greenhouse.io/<slug>,
    # boards-api.greenhouse.io/v1/boards/<slug>/jobs
    if "greenhouse.io" in host:
        slug = seg_after("boards") or (path[0] if path and path[0] != "v1" else None)
        return ("greenhouse", slug) if slug else None

    # Lever: jobs.lever.co/<slug>, api.lever.co/v0/postings/<slug>
    if "lever.co" in host:
        slug = seg_after("postings") or (path[0] if path else None)
        return ("lever", slug) if slug else None

    # Ashby: jobs.ashbyhq.com/<slug>
    if "ashbyhq.com" in host:
        slug = seg_after("job-board") or (path[0] if path else None)
        return ("ashby", slug) if slug else None

    # Workable: apply.workable.com/<slug>
    if "workable.com" in host:
        slug = seg_after("accounts") or (path[0] if path else None)
        return ("workable", slug) if slug else None

    # SmartRecruiters: jobs.smartrecruiters.com/<Slug>
    if "smartrecruiters.com" in host:
        slug = seg_after("companies") or (path[0] if path else None)
        return ("smartrecruiters", slug) if slug else None

    # Recruitee: <slug>.recruitee.com
    if host.endswith("recruitee.com"):
        slug = host.split(".")[0]
        return ("recruitee", slug) if slug else None

    # Workday: <tenant>.wdN.myworkdayjobs.com/[en-US/]<site>
    if "myworkdayjobs.com" in host:
        parts = host.split(".")
        if len(parts) >= 3:
            tenant, wd = parts[0], parts[1]
            site = None
            for p in path:
                if p.lower() in ("en-us", "wday", "cxs") or p == tenant:
                    continue
                site = p
                break
            if site:
                return ("workday", f"{tenant}/{wd}/{site}")
        return None

    # Eightfold: the host is company-specific, so infer the domain from the host.
    # Recognized by the /careers or /api/apply path shape.
    if "/api/apply" in (parsed.path or "") or any(
            s in host for s in ("eightfold.ai", "jobs.", "explore.", "careers.")):
        domain = ".".join(host.split(".")[-2:])
        for marker in ("netflix", "microsoft"):
            if marker in host:
                domain = f"{marker}.com"
        return ("eightfold", f"{host}|{domain}")

    return None


def board_url(platform: str, slug: str) -> str:
    spec = PLATFORMS.get(platform)
    if not spec:
        return ""
    if spec.get("board_url_fn"):
        return spec["board_url_fn"](slug)
    return spec["board_url"].format(slug=slug)
