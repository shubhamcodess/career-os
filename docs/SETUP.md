# Setup Guide

Full walkthrough for getting Career OS running, including API keys and fork strategy.

---

## 1. Choose Your Fork Strategy

**Option A — Public fork, private data (recommended)**
Fork the repo publicly (so you can contribute back / show it in your portfolio), but your
personal data never gets committed because it's gitignored. Your resumes, master experience
doc, etc. live only on your local machine unless you explicitly remove them from `.gitignore`.

**Option B — Fully private repo**
Clone (not fork) into a brand new private repo. Full privacy, but you lose the visible
connection to the open-source project and can't easily pull updates.

**Option C — Public fork, public data**
Remove the personal-data lines from `.gitignore`. Only do this if you're comfortable with
your resume content being public — some people do this intentionally as a "build in public"
job search.

This guide assumes **Option A**.

---

## 2. Clone and Configure

```bash
git clone https://github.com/yourusername/career-os.git
cd career-os

cp config/user.example.json config/user.json
cp .env.example .env
```

Edit `config/user.json`:
```json
{
  "profile": {
    "name": "Your Name",
    "email": "you@example.com",
    "location": "Bangalore, India",
    "linkedin_url": "https://linkedin.com/in/you",
    "github_username": "yourusername"
  },
  "target": {
    "target_roles": ["Senior Product Manager"],
    "target_companies": ["Razorpay", "Zepto", "Groww"],
    "target_locations": ["Bangalore", "Remote"],
    "experience_years": 6,
    "domain_keywords": ["fintech", "0-to-1"]
  }
}
```

---

## 3. Get API Keys

### GitHub Personal Access Token (required)
1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Scopes needed: `repo`, `read:user`
4. Copy into `.env` as `GITHUB_PERSONAL_ACCESS_TOKEN`

**Used for:** git operations, github-market-map skill, profile-intelligence GitHub lookups

### Firecrawl API Key (required for web scraping tasks)
1. Sign up at https://www.firecrawl.dev
2. Copy into `.env` as `FIRECRAWL_API_KEY`

**Used for:** fetching full JD pages from URLs, company profiling, candidate profile research
**Use sparingly** — reserve for high-value tasks (not routine lookups)

### A note on paid data sources

Everything in this setup runs on free tiers. One capability is intentionally left out:
direct people-search by company + role (e.g. "show me 20 Product Managers at Razorpay
with their skills"). That level of detail requires a licensed LinkedIn-layer data
provider like Crustdata, which is a paid product. Until a free or low-cost alternative
is added, `profile-intelligence` builds its picture from GitHub public data and web
search instead — still useful, just less granular on the people-search side. See
`skills/profile-intelligence/SKILL.md` for exactly how to plug a provider in later.

### Indeed, ZipRecruiter, Dice
No keys needed — these MCP connectors work immediately once connected in Claude's
connector directory (or configured in `mcp/.mcp.json` if using Claude Code directly).

---

## 4. Install Dependencies

```bash
npm install
```

**Only if using the Naukri scraper:**
```bash
pip install -r scripts/requirements.txt
playwright install chromium
```

Then in `config/user.json`, set:
```json
"integrations": {
  "naukri_enabled": true
}
```

---

## 5. Start Claude Code

```bash
claude
```

Paste `INIT_PROMPT.md` as your first message. It will:
- Verify the full folder structure
- Install npm dependencies
- Confirm which `.env` keys are present
- Test PDF export with a sample render
- Read all skills and confirm they're loaded
- Commit the initial setup

---

## 6. Begin

```
begin intake interview
```

From here, everything is driven by natural language commands — see `docs/SKILLS.md` for
the full reference, or just ask Claude what you can do.

---

## Troubleshooting

**"Puppeteer fails to launch"**
Usually a missing Chromium dependency on Linux. Run:
```bash
npx puppeteer browsers install chrome
```

**"Naukri scraper returns 0 results"**
Naukri may have changed their page structure, or you're being rate-limited/blocked.
Check `data/logs/naukri-scraper.log`. This is expected occasionally — the scraper is
explicitly documented as fragile. Job search continues fine with other sources.

**"GitHub API rate limited"**
You're likely making requests without the PAT, or it's not being read correctly from `.env`.
Confirm `GITHUB_PERSONAL_ACCESS_TOKEN` is set and valid.
