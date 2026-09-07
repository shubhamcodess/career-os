# Skills Reference

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
using GitHub public API + web search (Brave, if connected). Free sources only — no
dedicated LinkedIn people-search yet (that would require a paid provider like Crustdata;
see the skill file for how to add one later).

**Triggers:**
- `profile intel for [company]`
- `who works at [company] as [role]`
- `research [company] hiring team`

**Output:** `data/market/company-intel/[company-slug].md`

**Requires:** nothing paid. `GITHUB_PERSONAL_ACCESS_TOKEN` recommended (free) to avoid
rate limits; `BRAVE_API_KEY` optional (free tier) for the web-search layer.

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
│   └── uses: GitHub REST API + Brave Search MCP (optional)
├── github-market-map
│   └── uses: GitHub REST API
└── profile-optimizer
    └── reads: data/master-experience.md
```
