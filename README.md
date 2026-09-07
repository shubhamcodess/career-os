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
- **Aggregates live job listings** from Indeed, ZipRecruiter, Dice, Crustdata (and optionally Naukri)
- **Maps what people in your target role actually built** using public GitHub data — informs what
  projects to add to your portfolio
- **Researches who works at your target company** using legal LinkedIn-layer data (Crustdata) —
  informs resume framing and outreach
- **Tracks every application, resume version, and interview** with full git history
- **Prepares STAR stories** for behavioral rounds
- **Researches compensation** and helps you build a negotiation position
- **Builds your portfolio website content** in an AI-agent-ready format for one-shot generation

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

Fill in `config/user.json` with your target roles, companies, and preferences.
Fill in `.env` with your API keys (see [Setup Guide](docs/SETUP.md) for how to get each one).

### 2. Install dependencies

```bash
npm install
pip install -r scripts/requirements.txt   # only needed if using Naukri scraper
playwright install chromium                # only needed if using Naukri scraper
```

### 3. Start Claude Code

```bash
claude
```

Paste the contents of `INIT_PROMPT.md` as your first message. Claude Code will verify
the setup, test PDF export, and confirm which integrations are active.

### 4. Begin

```
begin intake interview
```

That's it. Claude Code reads `CLAUDE.md` automatically every session — it always knows
where you are and what to do next.

---

## Project Structure

```
career-os/
├── CLAUDE.md                    ← Claude Code's persistent instructions (read every session)
├── INIT_PROMPT.md               ← One-time setup prompt
├── config/
│   ├── user.json                ← Your personal config (gitignored)
│   └── user.example.json        ← Template for others
├── .env                         ← Your API keys (gitignored)
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
│   ├── job-aggregator/              ← Live job search across sources
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
│   └── naukri-scraper.py          ← Optional Naukri integration
└── docs/
    ├── SETUP.md                   ← Full setup walkthrough
    └── SKILLS.md                  ← Detailed skill documentation
```

---

## Data Sources & What's Really Possible

Being upfront about what's live data vs. workaround, so you know what you're getting.
**This setup uses free sources only — no paid API keys required.**

| Source | Status | Notes |
|---|---|---|
| Indeed | ✅ Live MCP | Free, works out of the box |
| ZipRecruiter | ✅ Live MCP | Free, authless, works immediately |
| Dice | ✅ Live MCP | Free, authless, tech-focused |
| GitHub | ✅ Live REST API | Free, public data, 5,000 req/hr with a free personal access token |
| Brave Search | ✅ Live MCP | Free tier (2,000 queries/month), used for company research |
| Naukri | ⚠️ Scraper | No official API. Playwright-based, free but fragile — may break if Naukri changes their site |
| LinkedIn direct | ❌ Not possible | Scraping violates ToS — never attempted |
| LinkedIn-layer data (e.g. Crustdata) | 🔜 Not included | Would give direct people-search by company/role; requires a paid plan, so it's left out of the default setup. `profile-intelligence` currently runs on GitHub + web search instead. See that skill's file for how to add a provider later. |

---

## Commands

See [docs/SKILLS.md](docs/SKILLS.md) for the full command reference across all skills.
Quick highlights:

```
begin intake interview          Start capturing your professional story
make resume for [Company/Role]  Generate a tailored, ATS-checked, PDF-exported resume
find jobs                       Aggregate live listings across all sources
profile intel for [Company]     Map who works there and what they know
github market map for [Role]    See what people in this role actually build
prep for [Company] interview    STAR story matching + mock behavioral Q&A
status                          Full dashboard
```

---

## Contributing

This project is open source because a good job search system helps everyone.
See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add skills, improve prompts, or fix bugs.

Ideas for contributions:
- Additional job board integrations (LinkedIn Jobs official API when available, Wellfound, etc.)
- More resume templates
- Region-specific profile optimizers (beyond India/US)
- Better company research synthesis
- Interview prep frameworks for specific companies (Amazon LPs, Google, etc.)

---

## Privacy & Data

Your personal data (`config/user.json`, `data/*.md`, `.env`) is gitignored by default in this
template. If you fork this repo to build your own private career OS, your data stays local
unless you explicitly push it. If you want to keep your personal repo private while still
using the public skills/templates, see [docs/SETUP.md](docs/SETUP.md) for the recommended
fork structure.

---

## License

MIT. Use it, fork it, improve it, help someone land their next role.

---

## Credits

Built with [Claude Code](https://claude.com/claude-code) by Anthropic.
Job data via Indeed, ZipRecruiter, Dice, and Crustdata MCP connectors.
PDF rendering via Puppeteer.
