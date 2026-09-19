# 🧭 career-os

**Your next unfair advantage in the career leap.**

A job hunt that runs like a system instead of a scramble: one source of truth for your
story, live openings pulled straight from company job boards every morning, resumes
tailored per application, profiles that recruiters actually find, and a memory that
knows what you have already seen and decided.

Built as a set of skills for [Claude Code](https://claude.com/claude-code). Every file
is markdown or JSON, every change is a git commit, and nothing about you leaves your
machine except what you choose to send.

![Skills](https://img.shields.io/badge/skills-22-6b5bd6)
![Job platforms](https://img.shields.io/badge/ATS%20platforms-11-1d9e75)
![Sources](https://img.shields.io/badge/sources-boards%20%C2%B7%20careers%20pages%20%C2%B7%20connectors%20%C2%B7%20Naukri-378add)
![Hardcoded companies](https://img.shields.io/badge/hardcoded%20companies-0-444441)
![Built for Claude Code](https://img.shields.io/badge/built%20for-Claude%20Code-d4a27f)
![License](https://img.shields.io/badge/license-MIT-639922)

---

## What this is

Most tools optimise the document. This optimises the outcome — the offer.

The bet: a job search fails on logistics far more often than on talent. You apply late
because you saw the posting late. You send the same resume everywhere because tailoring
by hand costs an hour. Your profile sits invisible because you never worked out which
keywords recruiters actually search. You lose track of what you already rejected.

career-os turns each of those into a step a machine can do well and you can check:

- **It knows your story.** A resumable interview captures your career once, in depth,
  into `data/master-experience.md`. Every resume, bullet and post is generated from it —
  never invented.
- **It finds the jobs.** Company boards, careers pages, job-board connectors and Naukri,
  merged and de-duplicated, with only what is new since last time shown to you.
- **It remembers your judgement.** Applied, shortlisted and rejected are recorded once
  and respected forever. Nothing is ever marked on your behalf.
- **It writes what you send.** Tailored resumes, ATS checks, cover letters, cold emails,
  LinkedIn and Naukri profile text — drafted, humanised, always yours to send.

---

## Quick start

### 1. Get Claude Code and clone

```bash
npm install -g @anthropic-ai/claude-code
git clone https://github.com/shubhamcodess/career-os.git
cd career-os
npm install
```

### 2. Create your config files

```bash
cp config/user.example.json config/user.json
cp .env.example .env
```

### 3. Flip the personalize switch

In `.env`:

```env
PERSONALIZE=true
PRIVATE_REPO_URL=git@github.com:you/career-os-private.git
```

`PERSONALIZE=true` runs career-os as *your* career system. Left `false`, Claude treats
the repo as an open-source project you are contributing to and never asks personal
questions. `PRIVATE_REPO_URL` is your own private GitHub repo — where your data is
backed up, and the only remote it is ever pushed to.

### 4. Name your targets

In `config/user.json`, fill in your target roles, locations and the companies you want
to work at. **Company names only.** career-os works out where each one posts its jobs;
no slug, URL or platform is ever hardcoded anywhere in this repo.

### 5. Let Claude finish the setup

```bash
claude
```

Then type:

```
setup
```

Setup builds the company registry, renders one-click install cards for the job-board
connectors, sets usage budgets, and ends by telling you how many companies are reachable
and what is still open. It is safe to re-run any time. `what's left to set up` re-checks
just the gaps.

### 6. Begin

```
begin intake interview      # capture your story — pausable, resumable, checkpointed
find jobs                   # first live pull across every source
```

Full walkthrough with troubleshooting: [docs/SETUP.md](docs/SETUP.md).

---

## How a day goes

```
  find jobs ──► only what's NEW since last run ──► you decide
                                                      │
        ┌─────────────────────────────────────────────┤
        │                                             │
    shortlist                                  not interested
        │                                             │
        ▼                                             ▼
  make resume for [Company/Role]              never shown again,
        │                                     record kept
        ├── tailored to the JD
        ├── ATS-checked
        ├── humanised
        └── PDF exported
        │
        ▼
  draft outreach for [Company] ──► Gmail draft ──► you send
        │
        ▼
  applied to [Company] [Role] ──► tracked, hidden from future feeds
```

Nothing in that loop fetches unless you ask it to. `find jobs` fetches; every `show`
command reads what has already been collected.

---

## Features, and how to try each one

| Feature | What it does | Try it | Skill |
|---|---|---|---|
| **Guided setup** | Config, registry, connectors, budgets — verified step by step | `setup` | [setup](skills/setup/SKILL.md) |
| **Intake interview** | Captures your full career into one master document, checkpoint by checkpoint | `begin intake interview` | [job-search-command-center](skills/job-search-command-center/SKILL.md) |
| **Job aggregation** | Every source in one command, merged, de-duplicated, ranked, new-only | `find jobs` | [job-aggregator](skills/job-aggregator/SKILL.md) |
| **Company registry** | Finds each target company's real job board; no hardcoding | `resolve companies` · `show companies` | [setup](skills/setup/SKILL.md) |
| **Careers-page crawler** | For companies with no reachable board: finds the job system, the page's own data feed, or its job links | `discover careers page for [company]` | [careers-crawler](skills/careers-crawler/SKILL.md) |
| **Naukri coverage** | India listings for companies international boards miss | `search naukri for unreachable` | [naukri-scraper](skills/naukri-scraper/SKILL.md) |
| **Job memory** | Day-grouped store of every listing, with your decisions kept permanently | `show current feed` · `job store stats` | [job-aggregator](skills/job-aggregator/SKILL.md) |
| **JD verdict** | Red/yellow/green read on a posting before you spend an evening on it | `jd check` + URL | [jd-analyzer](skills/jd-analyzer/SKILL.md) |
| **Tailored resumes** | JD-mapped resume → ATS score → humanised → PDF, versioned per application | `make resume for [Company/Role]` | [resume-tailoring](skills/resume-tailoring/SKILL.md) |
| **Google pipeline** | Google's own rules: minimum-qualification gate, X-Y-Z bullets, 3-per-30-days budget | `make resume for Google [role]` | [google-resume](skills/google-resume/SKILL.md) |
| **LinkedIn profile** | From screenshots: exact headline, About, every role block, skills order, Featured | `polish my linkedin` | [linkedin-profile](skills/linkedin-profile/SKILL.md) |
| **Content engine** | Post ideas pairing something new in your field with something you actually built | `what should I post` · `content calendar` | [linkedin-profile](skills/linkedin-profile/SKILL.md) |
| **Naukri profile** | 100% profile score, keywords taken from your real target JDs, weekly freshness routine | `polish my naukri` · `why no naukri calls` | [naukri-profile](skills/naukri-profile/SKILL.md) |
| **Cold outreach** | One hook, one achievement, humanised — as a Gmail draft, never auto-sent | `draft outreach for [company]` | [cold-outreach](skills/cold-outreach/SKILL.md) |
| **Inbox tracking** | Classifies replies, invites and rejections; updates the tracker | `check my email` · `who hasn't replied?` | [gmail-tracker](skills/gmail-tracker/SKILL.md) |
| **Slack bridge** | Results as clean tables in your channel; `!os` commands read back | `send to slack` · `check slack` | [slack-bridge](skills/slack-bridge/SKILL.md) |
| **Company intel** | Who works there, what that team values, before you tailor or reach out | `profile intel for [company]` | [profile-intelligence](skills/profile-intelligence/SKILL.md) |
| **Role portrait** | What people in your target role actually build, from public GitHub | `github market map for [role]` | [github-market-map](skills/github-market-map/SKILL.md) |
| **Interview prep** | STAR stories matched to the JD, then mock rounds | `prep for [company] interview` | [job-search-command-center](skills/job-search-command-center/SKILL.md) |
| **Help and status** | Static command reference; live dashboard of everything above | `help` · `status` | [dashboard](skills/dashboard/SKILL.md) |

Full reference: [docs/SKILLS.md](docs/SKILLS.md).

---

## Where the jobs come from

| Source | How | Notes |
|---|---|---|
| **Company job boards** (11 platforms) | Public JSON APIs | Greenhouse, Lever, Ashby, Workable, SmartRecruiters, Recruitee, Workday, Eightfold, pcsx, plus Amazon and Google adapters. No auth, no scraping, full depth |
| **Careers pages** | Real browser (Playwright) | For companies with no reachable board. Finds the job system behind the page, its data feed, or its job links |
| **Dice** | Connector | No auth |
| **Indeed / ZipRecruiter** | Connector | Run on *your* account, so career-os caps its own usage at 60% of an assumed daily limit and refuses to exceed it |
| **Naukri** | Playwright | No official API. Best India coverage; fragile by nature, and says so when it breaks |
| **Web search / fetch** | Built in | The research layer: JDs, careers pages, company intel, what's new in your field |
| **LinkedIn** | Never | Not scraped, not automated, not logged into. Profile work runs from screenshots you paste |

**Nothing is hardcoded.** You name companies; `resolve-ats.py` probes every platform and
writes `config/companies.json`. When a company has no public board, the ladder runs:
careers-page discovery → Naukri → web search → and if all of those fail, it tells you so
plainly with the careers URL, rather than returning a silent zero.

```bash
python3 scripts/resolve-ats.py --from-config     # build the registry
python3 scripts/resolve-ats.py --list            # who's reachable, who isn't
python3 scripts/careers-crawler.py discover --company "Acme" --url "https://careers.acme.com/search"
```

---

## What accumulates

```
data/
├── master-experience.md          your career, in full — the source of every document
├── star-stories.md               behavioural stories, tagged by competency
├── job-tracker.md                applications, status, next action
├── version-registry.md           every resume version and where it went
├── profile-linkedin.md           your current LinkedIn copy + audit
├── profile-naukri.md             your Naukri copy, keywords and views→calls funnel
├── content/                      story bank, post ideas, calendar, performance log
└── market/
    ├── job-index.json            every listing ever seen, with your decisions
    ├── runs/YYYY-MM-DD.json      what was fetched each day
    ├── jobs/YYYY-MM-DD.json      job descriptions, cached by day
    ├── company-intel/            per-company research
    └── role-portraits/           per-role GitHub portraits

resumes/[Company]_[Role]_[date]_v[N]/{resume.md, resume.html, resume.pdf}
checkpoints/interview-state.md    where the intake got to
```

The longer you use it, the better it gets: the store learns what you have seen, the
decision history informs what gets surfaced next, and your keyword lists follow the JDs
you are actually chasing.

---

## Your data stays yours

Three layers, by design:

1. **Gitignored.** `data/`, `resumes/`, `checkpoints/`, `config/user.json` and `.env`
   never enter the public repo.
2. **Your own vault.** `bash scripts/sync-vault.sh -m "what changed"` pushes your personal
   data to *your* private GitHub repo. That is the only remote it goes to.
3. **Nothing sent on your behalf.** Emails are drafted, never sent. Profiles are written
   for you to paste. Slack posts go only to the channel you configured.

---

## Honest limitations

- **Some companies cannot be reached.** A few serve jobs through private or signed APIs
  with no public links. career-os reports that instead of pretending there are no openings.
- **Scrapers break.** Naukri and careers-page recipes depend on page structure. When one
  returns nothing, you get a warning to re-discover, not a false "no jobs".
- **Sites that block a normal browser stay blocked.** No stealth, no fingerprint games,
  no logins. If a site says no, that's the end of it.
- **Connector quotas are real.** Indeed and ZipRecruiter authenticate as you, so usage is
  capped and the cap is never worked around.
- **Reach advice is a heuristic.** Profile and content guidance is grounded in published
  limits and current observation — not a promise of views, calls or virality.
- **Nothing is invented.** If your master document doesn't support a claim, it doesn't get
  written. That is a feature, and it means the intake interview is worth your time.

---

## Under the hood

| Script | Job |
|---|---|
| `find-jobs.py` | Entry point for `find jobs`: fans out to every source, merges, de-duplicates, ranks, reports coverage |
| `ats_platforms.py` | All 11 job-board adapters in one file — add a platform by appending one entry |
| `resolve-ats.py` | Builds and refreshes the company registry |
| `careers-crawler.py` | Browser discovery of any careers site + daily replay of saved recipes |
| `job-store.py` | Persistent job memory: day-grouped runs, statuses, decision history, pruning |
| `naukri-scraper.py` | Naukri listings via Playwright |
| `mcp-budget.py` | Connector usage ledger and cap enforcement |
| `status.py` | Read-only JSON snapshot of all local state, for the `status` dashboard |
| `sync-vault.sh` | Personal-data backup to your private repo |
| `export-pdf.js` | Puppeteer HTML → PDF rendering |

Claude reads `CLAUDE.md` every session, so it always knows the mode, the rules and where
you left off. Skills are plain markdown — open one, read it, change it.

---

## Commands

```
setup                            Guided setup; safe to re-run
help                             Every command and skill, instantly
status                           Live dashboard: progress, jobs, profiles, connectors, backup

find jobs                        Pull new listings from every source
show current feed                What you haven't decided on yet
applied to [company] [role]      Record an application
not interested in [company]      Never show it again; record kept

make resume for [Company/Role]   Tailor → ATS check → humanise → PDF
jd check [url]                   Verdict before you invest time
polish my linkedin               Exact profile copy from your screenshots
polish my naukri                 100% profile, JD-derived keywords
what should I post               Post ideas from your proof and fresh research
draft outreach for [company]     Cold email, drafted not sent
prep for [company] interview     STAR matching and mock rounds
backup                           Sync personal data to your private vault
```

---

## Contributing

Contributions are welcome — a job search system that works for one person usually works
for many. See [CONTRIBUTING.md](CONTRIBUTING.md) for the project's structure and PR flow.

The one rule that shapes everything: **no personal data and no hardcoded companies in
`skills/`, `scripts/`, `templates/` or `docs/`.** Company names, slugs and URLs belong in
`config/`, which is gitignored.

Good places to start:

- A new job-board adapter in `ats_platforms.py` (one entry, and both the resolver and
  fetcher pick it up)
- An adapter for a recognised-but-unsupported system (iCIMS, Taleo, SuccessFactors,
  Oracle HCM, Phenom, Jobvite)
- Region-specific profile skills beyond India and the US
- More resume templates in `templates/resume-templates/`
- Interview-prep frameworks for specific companies
- Honest documentation of anything you found fragile

---

## License

[MIT](LICENSE). Use it, fork it, improve it, help someone land their next role.

---

## Credits

Built with [Claude Code](https://claude.com/claude-code). PDF rendering via Puppeteer,
browser automation via Playwright, job data via public ATS APIs, first-party job-board
connectors, and company careers pages.
