# Career OS

**A complete, AI-driven job search system built on Claude Code.**

Career OS turns your job search into a structured, versioned, data-driven pipeline —
from capturing your professional story once, to generating tailored resumes for every
application, to understanding what people who actually get hired look like, to building
your portfolio website. All powered by Claude Code, git, and a set of composable skills.

---

## What It Does

- **Captures your complete professional story once** through a structured, resumable interview
- **Generates tailored resumes** for any company/role in seconds — ATS-optimized, fact-checked, humanized
- **Exports pixel-perfect PDFs** via Puppeteer — not generic markdown-to-PDF garbage
- **Fetches live jobs directly from company ATS boards** (Greenhouse + Lever) — no scraping,
  pure JSON APIs covering hundreds of companies (Stripe, Anthropic, Groww, Meesho, Postman, and more)
- **Aggregates job listings** from Indeed, ZipRecruiter, and Dice simultaneously
- **Scrapes Naukri.com** (optional) for Indian market listings not on international boards
- **Maps what people in your target role actually built** using public GitHub data — informs what
  projects to add to your portfolio
- **Researches who works at your target company** using GitHub + web search — informs resume framing and outreach
- **Tracks every application, resume version, and interview** with full git history
- **Prepares STAR stories** for behavioral rounds
- **Researches compensation** and helps you build a negotiation position
- **Backs up your personal data** to your own private GitHub repo — you own your data, always

Every file is markdown or JSON. Every change is git-committed. Nothing lives in a black box.

---

## Why This Exists

Most resume tools optimize the document. This optimizes the **outcome** — the offer.
That means treating your job search as a system: one source of truth, informed by real
market data, producing artifacts (resumes, outreach, prep material) that are honest,
targeted, and continuously improved as you learn more about what works.

---

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/yourusername/career-os.git
cd career-os
cp config/user.example.json config/user.json
cp .env.example .env
```

### 2. Flip the personalize switch

Open `.env` and set:

```env
PERSONALIZE=true
PRIVATE_REPO_URL=git@github.com:yourusername/career-os-private.git
```

- **`PERSONALIZE=true`** — activates personal career OS mode. When false (the default),
  Claude treats this as a framework contribution session and won't ask personal questions.
- **`PRIVATE_REPO_URL`** — your private GitHub repo for personal data backup (resumes,
  interview notes, job tracker). Create a new private repo on GitHub first, then paste
  the SSH clone URL here. Run `bash scripts/sync-vault.sh` after any personal data session.

Then fill in `config/user.json` with your target roles, companies, and preferences.
Add your API keys to `.env` (see [Setup Guide](docs/SETUP.md)).

### 3. Install dependencies

```bash
npm install
```

For ATS Direct job fetching (no extra setup — pure HTTP, works immediately):
```bash
# Already works — scripts/ats-fetcher.py uses only Python stdlib
python3 scripts/ats-fetcher.py --company Stripe --role "Engineer"
```

For Naukri scraper (optional, Indian market listings):
```bash
pip3 install playwright playwright-stealth --break-system-packages
python3 -m playwright install chromium
# System Chrome (/Applications/Google Chrome.app) must also be installed —
# bundled Chromium is blocked by Naukri's WAF; real Chrome is not.
```

### 4. Start Claude Code

```bash
claude
```

Paste the contents of `INIT_PROMPT.md` as your first message. Claude Code will verify
the setup, test PDF export, and confirm which integrations are active.

### 5. Begin

```
begin intake interview
```

That's it. Claude Code reads `CLAUDE.md` automatically every session — it always knows
which mode you're in and where you left off.

---

## Project Structure

```
career-os/
├── CLAUDE.md                    ← Claude Code's persistent instructions (read every session)
├── INIT_PROMPT.md               ← One-time setup prompt
├── config/
│   ├── user.json                ← Your personal config (gitignored)
│   └── user.example.json        ← Template for others
├── .env                         ← API keys + PERSONALIZE flag (gitignored)
├── .env.example                 ← Template for others
├── mcp/.mcp.json                ← MCP connector configuration
├── skills/                      ← All capabilities, as Claude Code skills
│   ├── job-search-command-center/   ← Master orchestrator
│   ├── pdf-export/                  ← Puppeteer-based PDF generation
│   ├── profile-optimizer/           ← Naukri/LinkedIn/Instahyre profile optimization
│   ├── resume-ats-optimizer/        ← ATS scoring
│   ├── resume-builder/              ← Structure and bullet standards
│   ├── resume-humanizer/            ← AI-to-human pass
│   ├── resume-tailoring/            ← JD-specific tailoring
│   ├── job-aggregator/              ← Live job search across all sources
│   ├── profile-intelligence/        ← Who works at target companies
│   ├── github-market-map/           ← What people in your role actually build
│   └── naukri-scraper/              ← Optional Naukri.com integration
├── templates/
│   ├── resume-templates/            ← HTML/CSS templates for PDF rendering
│   └── cover-letter-templates/
├── data/                         ← Your personal data (gitignored except structure)
│   ├── master-experience.md
│   ├── star-stories.md
│   ├── version-registry.md
│   ├── portfolio-brief.md
│   ├── job-tracker.md
│   ├── comp-intel.md
│   └── market/                   ← Live market intelligence (auto-generated)
│       ├── job-feed.md
│       ├── company-intel/
│       └── role-portraits/
├── resumes/                      ← Generated resumes (md + html + pdf per version)
├── checkpoints/                  ← Interview state, resumable at any point
├── exports/                      ← Portfolio JSON, misc exports
├── scripts/
│   ├── export-pdf.js              ← Puppeteer PDF renderer
│   ├── ats-fetcher.py             ← Fetches jobs from Greenhouse + Lever APIs (no auth)
│   ├── naukri-scraper.py          ← Optional Naukri.com integration (Playwright)
│   ├── sync-vault.sh              ← Backs up personal data to your private repo
│   └── requirements.txt
└── docs/
    ├── SETUP.md                   ← Full setup walkthrough
    └── SKILLS.md                  ← Detailed skill documentation
```

---

## Data Sources

What's live vs. workaround, so you know what you're getting.
**This setup uses free sources only — no paid API keys required for core functionality.**

| Source | Status | Notes |
|---|---|---|
| **ATS Direct** (Greenhouse + Lever) | ✅ Live JSON API | Free, no auth, no scraping. Covers hundreds of companies. Add any company's slug to `scripts/ats-fetcher.py` to include it. |
| Indeed | ✅ Live MCP | Free, works out of the box |
| ZipRecruiter | ✅ Live MCP | Free, authless |
| Dice | ✅ Live MCP | Free, authless, tech-focused |
| GitHub | ✅ Live REST API | Free, public data, 5,000 req/hr with a free personal access token |
| Firecrawl | ✅ Live MCP | Free tier available — used for JD fetching, company profiling, candidate research |
| Naukri | ⚠️ Scraper | No official API. Uses Playwright + system Chrome (bypasses Akamai WAF). Free but fragile — may break if Naukri updates their DOM or anti-bot rules. Best for Indian market. |
| LinkedIn direct | ❌ Not possible | Scraping violates ToS — never attempted |
| LinkedIn-layer data (Crustdata) | 🔜 Not included | Richer people-search by company/role, but requires a paid plan. `profile-intelligence` runs on GitHub + web search instead. See that skill's file for how to add a provider later. |

**ATS Direct known companies (sample):**
Greenhouse — Stripe, Databricks, Cloudflare, Coinbase, Reddit, Discord, Airbnb, Figma,
Anthropic, OpenAI, HashiCorp, Groww, Postman.
Lever — Meesho, Cred, Freshworks, Netflix, Lyft, Vercel.
Internal ATS (auto-skipped with careers page URL) — Google, Amazon, Microsoft, Meta,
Apple, Nvidia, Razorpay, PhonePe, Flipkart, Walmart, and others.

---

## Commands

Quick highlights — see [docs/SKILLS.md](docs/SKILLS.md) for the full reference.

```
begin intake interview            Start capturing your professional story
resume interview                  Continue from your last checkpoint
make resume for [Company/Role]    Generate a tailored, ATS-checked, PDF-exported resume
find jobs                         Aggregate live listings (ATS Direct + Naukri + MCPs)
find jobs at [company]            Fetch openings at one specific company
profile intel for [Company]       Map who works there and what they know
github market map for [Role]      See what people in this role actually build
prep for [Company] interview      STAR story matching + mock behavioral Q&A
status                            Full dashboard
backup                            Sync personal data to your private vault repo
```

---

## Contributing

This project is open source because a good job search system helps everyone.
See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add skills, improve prompts, or fix bugs.

Ideas for contributions:
- More ATS slug mappings in `scripts/ats-fetcher.py` (add companies you've verified)
- Additional job board integrations (Wellfound, LinkedIn Jobs when available, Ashby)
- More resume templates
- Region-specific profile optimizers (beyond India/US)
- Better company research synthesis
- Interview prep frameworks for specific companies (Amazon LPs, Google, etc.)

---

## Privacy & Data

Your personal data (`config/user.json`, `data/*.md`, `resumes/`, `.env`) is gitignored
by default. It never touches the public repo.

Set `PERSONALIZE=true` and `PRIVATE_REPO_URL` in `.env`, then run `bash scripts/sync-vault.sh`
to back up your personal data to your own private GitHub repo. You own it completely —
Career OS is just the framework that generates it.

---

## License

MIT. Use it, fork it, improve it, help someone land their next role.

---

## Credits

Built with [Claude Code](https://claude.com/claude-code) by Anthropic.
Job data via ATS Direct (Greenhouse/Lever APIs), Indeed, ZipRecruiter, Dice, and Naukri.
PDF rendering via Puppeteer.
