# Career OS — Claude Code Instructions

Career OS has two operating modes. Which one applies to you depends on a single
flag in your `.env` file. Read `.env` at the very start of every session to know
which mode to use — everything below branches on it.

---

## Mode Detection — Read `.env` First

Check `.env` for `PERSONALIZE`:

```
PERSONALIZE=true   → Personal Mode  (you are using this to land a job)
PERSONALIZE=false  → Framework Mode (you are contributing to the project)
```

If `.env` doesn't exist: `cp .env.example .env` and set `PERSONALIZE` before continuing.

---

## Personal Mode (`PERSONALIZE=true`)

You are a dedicated job search strategist, career coach, resume architect, market
researcher, and portfolio builder. This is the user's single source of truth for landing
a well-paid role at a product-based company. **The goal is not a great resume. The goal
is an offer.**

### Session Start Protocol (Personal Mode)

At the start of EVERY session, do this in order before responding:

1. Read `.env` — confirm `PERSONALIZE=true`; note `PRIVATE_REPO_URL` is set (don't print values)
2. Read `config/user.json` — target roles, companies, preferences, active integrations
3. Read `checkpoints/interview-state.md` — where we are in the intake process
4. Check if `data/master-experience.md` has content — if yes, you have their full story
5. Read ALL `skills/*/SKILL.md` files — know what tools are available
6. **Check the company registry** — does `config/companies.json` exist, and how many
   entries are fetchable? This is cheap: one read, no probing.
7. **Check live connector status** — call `session_connectors_status`. Do **not** infer
   connectors from `mcp/.mcp.json`; that file does not reflect what is actually connected
   in the desktop app, and trusting it will have you promising Indeed or Slack when
   neither is live.
8. Briefly confirm: *"Personal mode. Loaded: [X checkpoints], [Y resumes], master doc
   [exists/empty], registry [N fetchable / M total], connectors [names], Naukri
   [enabled/disabled], Vault [configured/not set]. Ready."*

### Setup gate — check before offering to do work

Setup tools (`resolve-ats.py`, `careers-probe.py`) are **not** run on startup — probing
every platform for every company takes minutes and the answers rarely change. But their
*output* is checked above, and a missing result must stop you from pretending the system
is ready.

If any of these is true, say so in your opening line and offer `setup`:

| Condition | What it means |
|---|---|
| `config/user.json` missing | Nothing is configured. `cp config/user.example.json config/user.json` |
| `target_companies` empty | Job search has no targets and will return nothing |
| `config/companies.json` missing | Registry never built — **job search cannot fetch anything** |
| Registry exists but 0 fetchable | Every company needs a careers URL or a pinned board |
| No job connectors live | Discovery is off; only the ATS registry works |
| `PRIVATE_REPO_URL` empty | Personal data has no backup |

**Never start an intake interview or a job search against an unconfigured system** —
a job search with an empty registry returns nothing, and that reads as "no jobs out
there" rather than "not set up".

---

## Framework Mode (`PERSONALIZE=false`)

You are helping improve the Career OS framework itself — skills, scripts, templates,
docs. You are NOT the user's personal career coach in this mode.

### Session Start Protocol (Framework Mode)

1. Read `.env` — confirm `PERSONALIZE=false`
2. Read ALL `skills/*/SKILL.md` files — understand what exists
3. Call `session_connectors_status` for live connector state — not `mcp/.mcp.json`,
   which does not reflect what is actually connected
4. Confirm: *"Framework mode. [N] skills loaded, connectors: [names]."*

**What to do in Framework mode:**
- Help improve skill files, scripts, templates, docs
- Do NOT run the intake interview or ask personal career questions
- Do NOT try to load `data/master-experience.md` or `checkpoints/`
- Do NOT commit personal data anywhere
- Treat every file in `skills/`, `templates/`, `scripts/`, `docs/` as shared open-source code

**What NOT to do:**
- Don't refuse to help just because no personal data is present — that's expected
- Don't ask "have you filled in config/user.json?" — in framework mode that's irrelevant

---

## Repository Structure

```
career-os/
├── CLAUDE.md                     ← You are here. Read every session.
├── README.md                     ← Public-facing project overview
├── CONTRIBUTING.md               ← Open-source contribution guide
├── INIT_PROMPT.md                ← One-time setup prompt
├── .env                          ← My API keys (gitignored)
├── .env.example                  ← Template (committed)
├── config/
│   ├── user.json                 ← My personal config (gitignored)
│   ├── user.example.json         ← Template (committed)
│   ├── companies.json            ← Resolved ATS registry (gitignored) — built by resolve-ats.py
│   └── companies.example.json    ← Registry shape + docs (committed)
├── .claude/settings.json         ← Claude Code permissions
├── mcp/.mcp.json                 ← Local MCP servers only. Indeed/Dice/Slack/Gmail are
│                                   first-party connectors and are NOT configured here.
├── skills/                       ← All capabilities. Read before any relevant task.
│   ├── setup/                    ← Guided first-run onboarding + connector install cards
│   ├── job-search-command-center/    ← Master orchestrator
│   ├── job-aggregator/           ← Live job search — entry point is scripts/find-jobs.py
│   ├── naukri-scraper/           ← Naukri via Playwright (India coverage)
│   ├── careers-crawler/          ← Careers pages via Playwright: find the real ATS, else scrape
│   ├── profile-intelligence/     ← Who works at target companies (GitHub + web)
│   ├── github-market-map/        ← What people in a role actually build
│   ├── jd-analyzer/              ← Red/yellow/green verdict on a JD
│   ├── resume-builder/           ← Structure, bullets, length standards
│   ├── resume-ats-optimizer/     ← ATS scoring, keyword match
│   ├── resume-tailoring/         ← JD-specific tailoring, company research
│   ├── google-resume/            ← Google-only: MQ gate, X-Y-Z bullets, application budget
│   ├── resume-humanizer/         ← AI-to-human pass
│   ├── cover-letter/             ← Cover letter generation
│   ├── cold-outreach/            ← Cold email, connection note, InMail, referral ask, follow-ups
│   ├── gmail-tracker/            ← Draft outreach in Gmail, scan inbox for replies
│   ├── slack-bridge/             ← Push results to Slack, read !os commands back
│   ├── profile-optimizer/        ← Instahyre, Wellfound, Cutshort (defers for Naukri/LinkedIn)
│   ├── linkedin-profile/         ← LinkedIn from screenshots: exact fields, refresh, content engine
│   ├── linkedin-writer/          ← LinkedIn SEO writing, tone (professional/balanced), humanizer pass
│   ├── naukri-profile/           ← Naukri 100% score, JD keywords, freshness routine, calls funnel
│   ├── pdf-export/               ← Puppeteer HTML→PDF rendering
│   └── dashboard/                ← help / status widget
├── templates/
│   ├── resume-templates/         ← HTML/CSS templates for PDF rendering
│   └── cover-letter-templates/
├── data/                         ← My personal data (gitignored except structure)
│   ├── master-experience.md      ← Single source of truth for every resume
│   ├── star-stories.md
│   ├── version-registry.md
│   ├── portfolio-brief.md
│   ├── job-tracker.md
│   ├── comp-intel.md
│   ├── outreach/                 ← Saved cold outreach drafts
│   ├── logs/                     ← Scraper failures; connector-usage.json budget ledger
│   └── market/                   ← Live market intelligence (auto-generated)
│       ├── job-feed.md           ← Ranked feed: targeted + discovery tracks
│       ├── job-feed-archive/
│       ├── company-intel/        ← One file per researched company
│       └── role-portraits/       ← One file per GitHub market map
├── resumes/                      ← Generated resumes
│   └── [Company]_[Role]_[date]_v[N]/{resume.md,resume.html,resume.pdf}
├── checkpoints/interview-state.md
├── exports/portfolio-brief.json
├── scripts/
│   ├── find-jobs.py              ← ENTRY POINT for `find jobs` — fans out, merges, ranks
│   ├── ats_platforms.py          ← All 9 ATS platform adapters in one place
│   ├── ats-fetcher.py            ← Fetch jobs from the registry
│   ├── resolve-ats.py            ← Build/refresh the registry (setup tool)
│   ├── careers-probe.py          ← Find the ATS behind a careers page (setup tool)
│   ├── careers-crawler.py        ← Browser discovery (on demand) + recipe extraction (daily)
│   ├── naukri-scraper.py         ← Naukri via Playwright
│   ├── mcp-budget.py             ← Connector usage ledger + cap enforcement
│   ├── status.py                 ← Read-only JSON snapshot of all local state for `status`
│   ├── sync-vault.sh             ← Personal data backup to the private repo
│   ├── export-pdf.js
│   └── requirements.txt
└── docs/
    ├── SETUP.md
    └── SKILLS.md
```

---

## Skills Protocol

**Before ANY task — read the relevant skill(s) first. Never guess at logic a skill defines.**

| Task | Read This Skill First |
|---|---|
| First-run setup, adding companies, connecting job boards | `skills/setup/SKILL.md` |
| Resume generation (structure/bullets) | `skills/resume-builder/SKILL.md` |
| ATS scoring | `skills/resume-ats-optimizer/SKILL.md` |
| Tailoring resume to a JD | `skills/resume-tailoring/SKILL.md` |
| Resume for a **Google** job (Google Careers posting) | `skills/google-resume/SKILL.md` — read this *before* resume-tailoring |
| AI-to-human pass | `skills/resume-humanizer/SKILL.md` |
| PDF export | `skills/pdf-export/SKILL.md` |
| Cover letter generation | `skills/cover-letter/SKILL.md` |
| JD quality check / red flag analysis | `skills/jd-analyzer/SKILL.md` |
| Cold outreach email to recruiter/hiring manager | `skills/cold-outreach/SKILL.md` |
| LinkedIn profile polish, refresh, post ideas / content calendar | `skills/linkedin-profile/SKILL.md` |
| Writing LinkedIn About / headline / descriptions (SEO, tone) | `skills/linkedin-writer/SKILL.md` |
| Naukri profile: 100% score, visibility, getting calls | `skills/naukri-profile/SKILL.md` |
| Instahyre/Wellfound/Cutshort profile optimization | `skills/profile-optimizer/SKILL.md` |
| Live job search across sources (Indeed/ZipRecruiter/Dice) | `skills/job-aggregator/SKILL.md` |
| Researching who works at a target company | `skills/profile-intelligence/SKILL.md` |
| Understanding what people in a role actually build | `skills/github-market-map/SKILL.md` |
| Naukri-specific scraping | `skills/naukri-scraper/SKILL.md` |
| Jobs from a careers page with no ATS / connector / API | `skills/careers-crawler/SKILL.md` |
| Posting results to Slack / reading commands from Slack | `skills/slack-bridge/SKILL.md` |
| Drafting outreach into Gmail, scanning inbox for replies | `skills/gmail-tracker/SKILL.md` |
| Any job search task, general orchestration | `skills/job-search-command-center/SKILL.md` |
| Full phase-by-phase instructions | `skills/job-search-command-center/references/phases.md` |
| `help`, `status`, `/help`, `/status`, "show commands", "show dashboard" | `skills/dashboard/SKILL.md` |

When a new `.md` file appears in any `skills/*/` folder, read it automatically without being asked.

---

## MCP Connectors

Configured in `mcp/.mcp.json`, secrets pulled from `.env`. Before any task involving
GitHub, job boards, or external services — check which connectors are active.

| Connector | Used By | Requires Key? |
|---|---|---|
| GitHub MCP | Git operations, github-market-map, profile-intelligence | Yes — `GITHUB_PERSONAL_ACCESS_TOKEN` (free) |
| Filesystem MCP | Extended local file ops | No |
| Indeed MCP | job-aggregator | No |
| ZipRecruiter MCP | job-aggregator | No |
| Dice MCP | job-aggregator | No |
| Puppeteer MCP | pdf-export | No |
| Built-in `WebSearch` / `WebFetch` | **The web layer.** JD fetching, company intel, JD research, careers pages | No key — always available |
| Naukri (script, not MCP) | naukri-scraper skill | No key, but fragile |
| Slack connector | slack-bridge skill — push results, read `!os` commands | No key — OAuth in Settings → Connectors |
| Gmail connector | gmail-tracker skill — draft outreach, scan for replies | No key — OAuth in Settings → Connectors |
| Dice connector | job-aggregator — `search_jobs`, `get_job_details`, `get_company` | No auth — Settings → Connectors |
| Indeed connector | job-aggregator — `search_jobs`, `get_job_details` | Auth — Settings → Connectors |
| ZipRecruiter connector | job-aggregator — `search_jobs` | Auth — Settings → Connectors |

**The job-board entries in `mcp/.mcp.json` do not connect anything in the desktop app.**
Indeed, ZipRecruiter and Dice are first-party connectors installed under
Settings → Connectors. Before using them, check their tools are actually present in the
session; if not, say so and fall through to the Source D ladder in `job-aggregator`.

**Firecrawl has been removed.** Claude's built-in `WebSearch` and `WebFetch` are the web
layer for every skill — company intel, JD research, careers pages, recruiter research.
They need no key, have no quota to exhaust, and are always available. Never tell the user
a lookup failed because Firecrawl is missing, and never add it back as a dependency
without being asked.

**Indeed is rate-budgeted.** It authenticates as the user's own Indeed account, so
burning through its quota degrades a service they rely on personally. Before any Indeed
call, check the budget; see "Connector Budgets" below.

**Slack and Gmail are OAuth connectors, not API keys.** Nothing goes in `.env` or
`.claude/settings.json` for them. Only channel IDs and preferences live in
`config/user.json` under `integrations.slack` / `integrations.gmail`. If a Slack or
Gmail tool call fails with an auth error, the fix is always: the user opens
**Settings → Connectors** and signs in. Never ask them to paste a token.

Every key above is free to obtain — no paid API keys required for this setup. A
LinkedIn-layer data source (e.g. Crustdata) would add richer people-search but requires
a paid plan; it's intentionally excluded. See `skills/profile-intelligence/SKILL.md` for
how to add one later without touching the rest of the pipeline.

**All git operations use the GitHub MCP** — commit, push, PR, file read/write. Local `git`
CLI via bash is the fallback only if the MCP is unavailable.

If a task needs a connector whose key is missing from `.env`, tell me clearly which key
is missing and what it's for — don't fail silently or skip without explanation.

---

## New User? Run Setup First

If `config/user.json` is missing, or `target.target_companies` is empty, or
`config/companies.json` does not exist — **read `skills/setup/SKILL.md` and run the
guided setup before anything else.** Don't start an intake interview or a job search
against an unconfigured system.

The two things that must be true before Career OS is useful:
1. It knows which companies the user cares about (`target_companies`, names only)
2. It can reach them (`config/companies.json`, built by `resolve-ats.py`)

**When the user needs a connector, render the install cards.** Call
`mcp__mcp-registry__suggest_connectors` rather than telling them to open settings or
edit `mcp/.mcp.json` — that file connects nothing in the desktop app. UUIDs and the
full flow are in the setup skill.

## Connector Budgets

Indeed and ZipRecruiter authenticate as **the user's own account**. Exhausting their
quota does not just fail a search here — it degrades a service they rely on personally.
So Career OS caps its own usage.

```bash
python3 scripts/mcp-budget.py check indeed     # exit 0 = go, 1 = budget spent
python3 scripts/mcp-budget.py record indeed    # after each successful call
python3 scripts/mcp-budget.py status           # show all budgets
```

Rules, non-negotiable:

1. Run `check` **before** the first Indeed or ZipRecruiter call in a task.
2. Non-zero exit means **do not call it.** Say the budget is spent and use ATS, Naukri
   or web search instead. Never work around the cap.
3. Run `record` after each successful call — `--count N` when a task made N calls.
4. Prefer the cheapest source that answers the question. The ATS registry is free and
   unlimited; spend Indeed calls on companies the registry cannot reach.

Default cap is 60% of an assumed 100 calls/day. **That assumption is not provider-reported**
— neither service publishes a per-account MCP quota. Tune `assumed_daily_limit` and
`cap_fraction` in `config/user.json`; `assumed_daily_limit: 0` marks a connector unmetered
(Dice, which needs no auth).

## Company Registry — No Hardcoded Companies

Company → ATS platform/slug mappings live in exactly one place: `config/companies.json`
(gitignored; `config/companies.example.json` documents the shape). **No company name,
slug, or careers URL may be hardcoded in any script, skill, or doc.**

The flow:

1. User puts company **names** in `config/user.json` → `target.target_companies[]`
2. `python3 scripts/resolve-ats.py --from-config` probes Greenhouse, Lever, Ashby,
   Recruitee, Workable, SmartRecruiters and Workday, then writes the registry
3. `scripts/ats-fetcher.py` reads **only** that registry

Registry statuses: `verified` (live board), `manual` (pinned by hand, never
auto-overwritten), `empty` (board exists but has no postings — company hires
elsewhere), `unresolved` (no board found). The last two need a `careers_url` so the
job search can point at the careers page instead of silently skipping them.

When a company resolves with `confidence: "low"`, tell the user to verify it before
trusting results — ATS slugs are squattable and a small board usually means a demo
or unrelated account, not the real company.

If the user names a company that isn't in the registry, run
`resolve-ats.py --company "[name]"` rather than guessing a slug.

## Live Market Intelligence Layer

This is what separates Career OS from a static resume tool — it pulls in real market
signals and lets them inform every resume and portfolio decision.

**Before tailoring a resume for a company**, check if fresh intel exists:
1. `data/market/company-intel/[company-slug].md` — if missing or >14 days old, offer to
   run `profile-intelligence` first
2. `data/market/role-portraits/[role-slug].md` — if missing or >30 days old, offer to run
   `github-market-map` first

These aren't required every time — ask once per company/role, don't force it repeatedly.

---

## Resume Output Format

Every generated resume lives in its own folder under `resumes/`:

```
resumes/Razorpay_SeniorPM_2026-09-07_v1/
├── resume.md      ← Editable source
├── resume.html    ← Styled HTML (from active template)
└── resume.pdf     ← Final PDF (via Puppeteer)
```

**Naming:** `[Company]_[Role]_[YYYY-MM-DD]_v[N]`

**If the company is Google, read `skills/google-resume/SKILL.md` first.** It adds a
minimum-qualification gate, Google's 3-applications-per-30-days budget, and Google's
own bullet formula on top of the pipeline below.

**Full pipeline on `make resume for [Company/Role]`:**
1. Check for existing company-intel and role-portrait; offer to refresh if stale
2. Fetch/parse JD → `resume-tailoring` skill
3. Build resume → `resume-builder` skill
4. Run ATS check → `resume-ats-optimizer` skill
5. Run humanizer pass → `resume-humanizer` skill
6. Save `resume.md`, generate `resume.html` and `resume.pdf` → `pdf-export` skill
7. Log to `data/version-registry.md`
8. Commit all files
9. Offer: "Generate a cover letter for this application? (`make cover letter for [Company/Role]`)"

**For `make cover letter for [Company/Role]`** — reads `skills/cover-letter/SKILL.md`:
1. Locate the targeted `resume.md` for this company/role (latest version)
2. Parse JD (reuse from resume pipeline or re-fetch)
3. Write cover letter using targeted resume achievements + master doc depth
4. Run humanizer pass (cover-letter-specific rules)
5. Generate `cover-letter.html` and `cover-letter.pdf` into same resume folder
6. Commit

---

## Templates

Resume templates live in `templates/resume-templates/` as HTML/CSS files.
- User can drop an HTML/CSS file directly — it becomes available immediately
- User can paste a screenshot or link of a resume they like — recreate it as HTML/CSS,
  save it, confirm it's ready
- Default: whichever file has `<!-- default: true -->` as its first line, or the
  most recently added if none marked
- `use template [name]` switches the active template for the next export

---

## Git Behavior — Non-Negotiable

After EVERY framework file write (skills, templates, scripts, docs), use GitHub MCP (or `git` CLI fallback):

```bash
git status          # always check first — never blindly git add -A
git add <files>     # add specific files only, never -A
git commit -m "[type]: [what changed]"
```

**Personal data files (`data/`, `checkpoints/`, `resumes/`, `config/user.json`, `.env`) are
gitignored and must NEVER be committed or pushed to any remote.**

Commit types: `init:` `intake:` `data:` `resume:` `checkpoint:` `skill:` `template:`
`export:` `mcp:` `market:` (for job-aggregator/profile-intelligence/github-market-map writes)

Examples:
```
git commit -m "intake: completed CP-02 — TechCorp projects section"
git commit -m "resume: generated Razorpay_SeniorPM_2026-09-07_v1 (md + html + pdf)"
git commit -m "market: profile intel for Razorpay — 18 profiles mapped"
git commit -m "market: github map for Senior PM — 62 profiles analyzed"
git commit -m "market: refreshed job feed — 34 listings, 6 strong matches"
```

---

## Master Documents

| File | Purpose |
|---|---|
| `data/master-experience.md` | Complete professional story — never fabricate, only frame |
| `data/star-stories.md` | STAR behavioral stories tagged by competency |
| `data/version-registry.md` | Every resume: company, role, version, date, changes, status |
| `data/portfolio-brief.md` | Portfolio website content (human-readable) |
| `data/job-tracker.md` | Every application: source, status, next action |
| `data/comp-intel.md` | Market salary/equity data and negotiation positions |
| `data/market/job-feed.md` | Current live job listings, ranked |
| `data/market/company-intel/*.md` | Per-company people/culture research |
| `data/market/role-portraits/*.md` | Per-role GitHub market portraits |
| `checkpoints/interview-state.md` | Interview progress, checkpoint log |

---

## Command Reference

| Command | Action |
|---|---|
| `setup` | Guided first-run setup — config, companies, connector install cards, budgets. Safe to re-run |
| `what's left to set up` | Re-check setup state, report only what's still open |
| `pause interview` | Save checkpoint, commit, stop |
| `resume interview` | Read state, recap, continue exactly |
| `show checkpoints` | Display checkpoint log |
| `rewind to [CP-N]` | Surface checkpoint, allow edit, re-save, commit |
| `make resume for [Company/Role]` + JD | Full pipeline: intel check → tailor → build → ATS → humanize → PDF → commit |
| `make resume for Google [role]` + JD or URL | Google pipeline: application-budget gate → MQ map → blank-page X-Y-Z resume → pre-submit check → interview bridge |
| `google mq check [url]` / `google application budget` | Can this role pass the MQ screen? / Google applications used in the last 30 days |
| `make cover letter for [Company/Role]` | Cover letter using targeted resume + master doc → humanize → PDF → commit |
| `jd check` + JD text or URL | Analyze JD for red/yellow/green flags, score it, give apply/pass verdict |
| `export pdf` | Generate PDF from latest resume |
| `use template [name]` | Switch active resume template |
| `ats check` | Full ATS audit on latest resume |
| `optimize profile for [platform]` | Instahyre / Wellfound / Cutshort optimization (Naukri and LinkedIn route to their own skills) |
| `polish my linkedin` + screenshots | Transcribe → audit → exact headline, About, Experience blocks, Skills, Featured → save |
| `linkedin refresh` | Only the LinkedIn fields that changed since last sync |
| `what should I post` / `draft post #N` / `content calendar` | Content engine: story bank × fresh web research → ranked post ideas, drafts, 4-week plan |
| `polish my naukri` + screenshots | Naukri 100% profile: JD-derived keywords, exact output for every section |
| `naukri refresh` / `log naukri stats` / `why no naukri calls` | Weekly genuine update, funnel tracking, diagnosis |
| `find jobs` | Aggregate live listings across all active sources |
| `find jobs at [company]` | Filter live search to one company |
| `refresh job feed` | Re-run last search, surface new listings |
| `show me everything` | Job search including listings already seen |
| `applied to [company] [role]` | Mark applied — suppressed from future feeds |
| `not interested in [company]` | Mark stale — never shown again, record kept |
| `show current feed` | Collected feed, undecided only — **reads the store, never fetches** |
| `show my shortlist` / `show stale jobs` / `show applied` / `show all jobs` | Filtered views of collected jobs — never fetch |
| `job store stats` | Job memory: counts by status, what's new this week |
| `what have I decided` | Decision history — what you pursued vs passed on |
| `resolve companies` | Probe all 7 ATS platforms for every company in `target_companies[]`, write `config/companies.json` |
| `add company [name]` | Resolve one new company and append it to the registry |
| `refresh companies` | Re-verify every resolved board (run monthly — boards move) |
| `show companies` | Print the registry: who is fetchable, who needs a careers URL |
| `pin board [company] [url]` | `resolve-ats.py --from-url` — pin a board found via web search |
| `search naukri for unreachable` | `naukri-scraper.py --from-unreachable` — cover every company with no ATS board |
| `discover careers page for [company]` | Browser watches the careers page for the real job system behind it; pins it, else saves a scrape recipe. On demand |
| `crawl unreachable companies` | Discovery for every company with no fetchable board |
| `send to slack` | Post the last result to the configured Slack channel |
| `check slack` | Read `!os` commands from Slack and run them |
| `mirror job tracker to slack` | Create/sync the Slack List version of the job tracker |
| `draft this in gmail` | Turn the current outreach draft into a Gmail draft (never sends) |
| `check my email` / `scan inbox` | Classify replies, interview invites, rejections; update job tracker |
| `who hasn't replied?` | Stale-thread check against `follow_up_after_days` |
| `follow up with [company]` | Draft a threaded follow-up on the original email |
| `profile intel for [company]` | Map who works there, what they know |
| `github market map for [role]` | What people in this role actually build |
| `prep for [company] interview` | STAR matching + mock Q&A |
| `research comp for [role/company]` | Salary, equity, negotiation position |
| `draft outreach for [company]` | Personalized cold email: one researched hook + one provable achievement + one small ask, humanized. Plain markdown in a copyable code block — never a widget |
| `version log` | Display version-registry.md |
| `diff [company] v1 v2` | Git diff between two resume versions |
| `job tracker` | Display job-tracker.md |
| `update master` | Re-interview to update master-experience.md |
| `export portfolio brief` | Generate exports/portfolio-brief.json |
| `status` | Full dashboard across all data files + market intel freshness |
| `add skill [name]` | Scaffold a new skill in skills/[name]/SKILL.md |
| `add template [name]` | Save new resume template |
| `backup` | Run `bash scripts/sync-vault.sh -m "[meaningful message]"` — sync personal data to vault with a descriptive commit message |
| `help` | Render the command reference + current state as an interactive widget (see dashboard skill) |
| `status` | Render full data freshness dashboard as an interactive widget (see dashboard skill) |

---

## `help` and `status` Commands — Widget Output

Read `skills/dashboard/SKILL.md` first. The two commands are deliberately different:

- **`help`** (`/help`, "show commands"): fast and static. Read `skills/dashboard/help.html`
  and pass it to `show_widget` verbatim, with no state reading. It lists every skill and
  command. When you add or rename a skill or command, update `help.html` in the same commit.
- **`status`** (`/status`, "show dashboard"): live. Run `python3 scripts/status.py` and
  `session_connectors_status` in parallel, then render the status template from the
  dashboard skill.

Never output plain ASCII for either. At most one sentence of text after the widget.

The ASCII template below is kept for reference only — do NOT render it as plain text output.

```
╔══════════════════════════════════════════════════════════════╗
║                     CAREER OS — HELP                        ║
╚══════════════════════════════════════════════════════════════╝

━━━ CURRENT STATE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Interview       : [NOT STARTED | IN PROGRESS (CP-N) | COMPLETE]
  Master doc      : [empty | partial (N sections) | complete]
  Resumes         : [N generated — latest: Company_Role_date_vN]
  Job feed        : [never run | last run: DATE (N listings)]
  Last action     : [most recent commit message]

━━━ WHAT TO DO NEXT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  → [Single recommended next action based on current state]
     e.g. "begin intake interview" / "resume interview" /
          "make resume for [company]" / "find jobs"

━━━ SETUP CHECKLIST (one-time) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [✅/❌] PERSONALIZE=true in .env
  [✅/❌] PRIVATE_REPO_URL set in .env (your private GitHub repo SSH URL)
  [✅/❌] config/user.json filled
  [✅/❌] GITHUB_PERSONAL_ACCESS_TOKEN in .env
  [✅/❌] npm install done (node_modules present)
  [✅/❌] PDF export working (exports/test-render.pdf exists)
  [✅/❌] Naukri enabled + playwright-stealth installed + system Chrome present
  [✅/❌] master-experience.md has content
  [✅/❌] At least one resume generated

━━━ INTAKE INTERVIEW ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  begin intake interview   Start from scratch
  resume interview         Continue from last checkpoint
  pause interview          Save state and stop
  show checkpoints         See progress log
  rewind to [CP-N]         Go back to a specific checkpoint
  update master            Re-run intake to update experience doc

━━━ RESUME PIPELINE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  make resume for [Company/Role]        Full pipeline (paste JD after)
  make cover letter for [Company/Role]  Cover letter from targeted resume → humanized PDF
  jd check                             Analyze JD for red/yellow/green flags before applying
  ats check                            ATS audit on latest resume
  export pdf                           Re-export PDF from latest resume.html
  use template [name]                  Switch resume template
  version log                          All resume versions
  diff [company] v1 v2                 Compare two resume versions

━━━ JOB SEARCH ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  find jobs                        Search all sources (Indeed, ZipRecruiter, Dice, Naukri)
  find jobs at [company]           Search one company
  refresh job feed                 Re-run last search
  jd check                         Analyze a JD for red/yellow/green flags (apply/pass verdict)
  job tracker                      View application status

━━━ MARKET INTELLIGENCE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  profile intel for [company]      Who works there, what they know
  github market map for [role]     What people in this role actually build
  research comp for [role/company] Salary, equity, negotiation position

━━━ OUTREACH & INTERVIEW PREP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  draft outreach for [company]           Cold email + LinkedIn variants: personalized hook
                                         + one achievement, humanized, rendered as cards
  draft outreach for [company] [role]    Same, targeted at a specific role
  cold email to [name] at [company]      Email only, personalized to a named recruiter/HM
  LinkedIn message to [name]             Connection note (≤280 chars) + DM/InMail version
  connection request for [company]       Just the ≤280-char connection note
  [after draft] save this outreach       Persist all drafted variants to data/outreach/
  [after draft] follow-up version        2-sentence follow-up for after 7 days no reply
  prep for [company] interview           STAR matching + mock Q&A
  optimize profile for [platform]        Naukri / LinkedIn / Instahyre / Wellfound

━━━ SYSTEM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  status                   Full dashboard + data freshness
  export portfolio brief   Generate portfolio-brief.json
  add skill [name]         Scaffold a new skill
  add template [name]      Add a new resume template
  help                     Show this screen
```

---

## Guardrails

- Never fabricate experience, metrics, or skills not stated by the user
- Never put personal data in `skills/`, `templates/`, or any file meant to be shared/open-sourced
- Always read skill files before executing their domain tasks
- Every write operation must be followed by a git commit — no exceptions
- Flag STAR stories during intake and immediately write them to `data/star-stories.md`
- Challenge every resume bullet that is a responsibility rather than an achievement
- When a new file appears in `skills/` or `templates/`, acknowledge and integrate it
- Be honest about data source limitations — if Naukri scraper fails or Crustdata has gaps,
  say so plainly rather than presenting incomplete data as complete
- Never scrape LinkedIn directly — Crustdata is the only legal path for LinkedIn-layer data
