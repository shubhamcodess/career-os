# Skills Reference

## setup

**Trigger:** `setup`, `/setup`, "get me started", "what's left to set up",
"connect my job boards", or automatically when `config/user.json` is missing or
`target_companies` is empty.

Guided first-run onboarding. Six phases, each verified before the next: config files →
profile and targets → company registry → connectors → optional extras → budgets.

Two things it exists to make true: Career OS knows which companies you want (names only),
and it can reach them. Renders **one-click connector install cards** rather than sending
you into a settings menu — editing `mcp/.mcp.json` connects nothing in the desktop app.

Safe to re-run. Never overwrites config or the registry; re-checks and reports what's open.

**Scripts it drives:** `resolve-ats.py`, `careers-probe.py`, `mcp-budget.py`

---


Full documentation of every skill in Career OS — what it does, when it triggers, and
what commands drive it.

---

## Core Resume Pipeline

### job-search-command-center
The master orchestrator. Coordinates the full 9-phase job search process.
See `skills/job-search-command-center/references/phases.md` for complete details.

### resume-builder
Structure, bullet formulas, length rules, section ordering.
**Triggers:** resume generation (Phase 2 & 3)

### resume-tailoring
JD parsing, company research, experience-to-JD mapping.
**Triggers:** `make resume for [Company/Role]`

### resume-ats-optimizer
ATS compatibility scoring, keyword gap analysis.
**Triggers:** `ats check`, automatically after resume generation

### resume-humanizer
Detects and fixes AI-sounding phrasing.
**Triggers:** automatically after resume generation, or `humanize this`

### pdf-export
Puppeteer-based HTML→PDF rendering with full margin/padding/font control.
**Triggers:** `export pdf`, automatically after resume generation

---

### google-resume

**Trigger:** `make resume for Google [role]`, a Google Careers job URL, or any resume
request where the company is Google. `resume-tailoring` defers to it.

A dedicated pipeline for Google openings, built from Google's own published hiring
guidance. It runs on top of the standard resume skills rather than replacing them:

- **Application budget gate:** Google allows 3 applications per rolling 30 days and no
  edits after submitting. Checks the job store before any writing starts.
- **Minimum Qualifications map:** every MQ, verbatim, mapped to evidence and to where
  it's visible on the resume. An unmet MQ is a recommendation not to apply.
- **Blank-page build** with every bullet in Google's X-Y-Z form: *accomplished [X] as
  measured by [Y], by doing [Z]*.
- **Pre-submit checklist** (2 MB, parser check) and an **interview bridge** mapping each
  bullet to a STAR story.

Every rule is labelled **[Google]** (from Google's pages) or **[Career OS]** (this
project's practice), with source links at the end of the skill.

---

### careers-crawler

**Trigger:** `discover careers page for [company]`, `crawl unreachable companies`, or
any company in the registry with no fetchable board.

For companies with no ATS board, no connector and no API. Works on **any** careers
website, since nothing in it is company-specific. Uses Playwright in two stages:

- **Discover (on demand):** watches the page's network calls, JSON responses, links,
  iframes and embedded page data. In order of preference it will:
  1. pin a real job system permanently (Lowe's, Visa, PhonePe and IKEA all turned out to
     be Workday or SmartRecruiters underneath);
  2. save the JSON API the page itself calls;
  3. save JSON-LD / embedded job data;
  4. save a job-link pattern.
  Systems it recognises without an adapter (iCIMS, Taleo, Oracle HCM, Phenom, Jobvite…)
  are named in the report.
- **Extract (daily, inside `find jobs`):** replays saved recipes (`api`, `jsonld`,
  `embedded`, `links`), clicking "load more" and following pages, and reports as
  `Careers pages` in the coverage line.

Behaves like an ordinary browser: no stealth, polite delays, a page cap, no logins, never
LinkedIn, and it stops for any company that blocks it. Private or signed-API sites are
reported as unreachable rather than forced.

---

## Market Intelligence Layer

### job-aggregator
Fans out to Indeed, ZipRecruiter, Dice (and Naukri if enabled) simultaneously — all
free sources — deduplicates, and ranks against your profile.

**Triggers:**
- `find jobs`
- `find jobs at [company]`
- `find [role] jobs`
- `refresh job feed`

**Output:** `data/market/job-feed.md`

### profile-intelligence
Maps signals about a target company's engineering culture and GitHub-visible employees,
using GitHub public API + Claude's built-in WebSearch/WebFetch for web research. Free sources only —
no dedicated LinkedIn people-search yet (that would require a paid provider like Crustdata;
see the skill file for how to add one later).

**Triggers:**
- `profile intel for [company]`
- `who works at [company] as [role]`
- `research [company] hiring team`

**Output:** `data/market/company-intel/[company-slug].md`

**Requires:** `GITHUB_PERSONAL_ACCESS_TOKEN` (free) to avoid rate limits; built-in WebSearch/WebFetch (no key)
for web scraping — use sparingly on high-value company targets only.

### github-market-map
Builds a data-driven portrait of what people in your target role actually build,
using GitHub's public REST API.

**Triggers:**
- `github market map for [role]`
- `what projects should I have for [role]`
- `what stack do [role] people use`

**Output:** `data/market/role-portraits/[role-slug].md`

**Requires:** `GITHUB_PERSONAL_ACCESS_TOKEN` (works without it, but rate-limited to 60 req/hr)

### naukri-scraper
Optional Playwright-based scraper for Naukri.com listings — no official API exists.

**Triggers:** enabled via `config/user.json` → `naukri_enabled: true`, then part of
`find jobs` fan-out, or `search naukri for [role]` directly

**Status:** Fragile by nature — may break if Naukri updates their site structure.
Failures are logged to `data/logs/naukri-scraper.log` and don't block other sources.

---

## Profile & Outreach

### profile-optimizer
Platform-specific profile optimization for Naukri, LinkedIn, Instahyre, Wellfound, Cutshort.

**Triggers:** `optimize profile for [platform]`

**Note:** No LinkedIn MCP exists. Paste your profile URL or exported data for LinkedIn audits.

---

## Full Command Reference

| Command | Skill(s) Involved |
|---|---|
| `begin intake interview` | job-search-command-center |
| `pause interview` / `resume interview` | job-search-command-center |
| `show checkpoints` / `rewind to [CP-N]` | job-search-command-center |
| `make resume for [Company/Role]` | resume-tailoring → resume-builder → resume-ats-optimizer → resume-humanizer → pdf-export |
| `export pdf` | pdf-export |
| `use template [name]` | pdf-export |
| `ats check` | resume-ats-optimizer |
| `optimize profile for [platform]` | profile-optimizer |
| `find jobs` / `find jobs at [company]` | job-aggregator (+ naukri-scraper if enabled) |
| `profile intel for [company]` | profile-intelligence |
| `github market map for [role]` | github-market-map |
| `prep for [company] interview` | job-search-command-center (Phase 6) |
| `research comp for [role/company]` | job-search-command-center (Phase 7) |
| `draft outreach for [company]` | job-search-command-center (Phase 8), uses profile-intelligence's key-people map if available |
| `version log` / `diff [company] v1 v2` | job-search-command-center |
| `job tracker` | job-search-command-center |
| `update master` | job-search-command-center (Phase 1) |
| `export portfolio brief` | job-search-command-center (Phase 9) |
| `status` | job-search-command-center |

---

## Skill Dependency Graph

```
job-search-command-center (orchestrator)
├── resume-tailoring
│   ├── reads: data/master-experience.md
│   ├── reads: data/market/company-intel/*.md  (if fresh)
│   └── may trigger: profile-intelligence (if intel is stale)
├── resume-builder
├── resume-ats-optimizer
├── resume-humanizer
├── pdf-export
│   └── reads: templates/resume-templates/*.html
├── job-aggregator
│   ├── uses: Indeed, ZipRecruiter, Dice MCPs
│   └── may trigger: naukri-scraper (if enabled)
├── profile-intelligence
│   └── uses: GitHub REST API + built-in WebSearch/WebFetch
├── github-market-map
│   └── uses: GitHub REST API
└── profile-optimizer
    └── reads: data/master-experience.md
```
