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

### Slack and Gmail — no keys, OAuth only

These two are **connectors, not API keys**. There is nothing to paste into `.env`
and nothing to add to `.claude/settings.json`. Connect them in the Claude app under
**Settings → Connectors**, then put only your *preferences* in `config/user.json`.

Both are optional. Career OS works fully without either.

---

## 3b. Build the Company Registry

Career OS hardcodes no companies. You supply **names**; a resolver figures out which
ATS each one uses and writes `config/companies.json`.

First put your targets in `config/user.json`:
```json
"target": {
  "target_companies": ["Nvidia", "Stripe", "Razorpay", "Target"]
}
```

Then resolve them:
```bash
python3 scripts/resolve-ats.py --from-config
```

This probes Greenhouse, Lever, Ashby, Recruitee, Workable, SmartRecruiters and Workday
for each name. Check the result:

```bash
python3 scripts/resolve-ats.py --list
```

You will see four statuses:

| Status | Meaning | What to do |
|---|---|---|
| `verified` | Live board found | Nothing — job search will fetch it |
| `manual` | You pinned it by hand | Nothing — never auto-overwritten |
| `empty` | Board exists but has zero postings | Give it a careers URL (below) |
| `unresolved` | No public board found | Give it a careers URL (below) |

Large enterprises (Google, Amazon, Apple, Meta, Microsoft) run internal ATS systems
with no public API. That is expected — point them at their careers page so the job
search routes them through web search instead of skipping them:

```bash
python3 scripts/resolve-ats.py --set-careers "Google" https://careers.google.com
```

If you know a company's real board and auto-discovery missed it, pin it directly.
Workday slugs are compound — `tenant/wdNumber/site`:

```bash
python3 scripts/resolve-ats.py --set "Walt Disney" workday "disney/wd5/disneycareer"
python3 scripts/resolve-ats.py --set "Stripe" greenhouse stripe
```

Anything flagged **LOW CONFIDENCE** is worth opening in a browser before trusting.
ATS slugs are first-come-first-served: `google.recruitee.com` is a demo account owned
by someone else entirely. A board with one or two postings is usually not the company
you meant.

Boards move, so re-verify occasionally:
```bash
python3 scripts/resolve-ats.py --refresh
```

Adding a company later:
```bash
python3 scripts/resolve-ats.py --company "Anthropic"
```

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

## 5b. Optional — Slack and Gmail

Both are optional and independent. Skip either without consequence.

### Slack — results pushed to you, commands read back

A job feed refresh takes minutes and you will not be watching the terminal. With Slack
connected, results land in a channel and you can reply with the next instruction.

1. **Settings → Connectors → Slack → Connect**
2. Create a dedicated private channel (`#career-os`). Career OS output is noisy and personal.
3. Ask Claude: `find my career-os slack channel id` — or call
   `slack_search_channels(query="career-os")`.
4. Put it in `config/user.json`:

```json
"integrations": {
  "slack": {
    "enabled": true,
    "notify_channel_id": "C0XXXXXXXX",
    "command_channel_id": "C0XXXXXXXX",
    "command_prefix": "!os",
    "notify_on": ["job_feed", "jd_analysis", "resume_generated", "outreach_drafted", "inbox_scan"],
    "long_output_as_canvas": true,
    "job_tracker_list_id": ""
  }
}
```

**How the two directions differ.** Outbound is instant — Claude posts when work finishes.
Inbound is **pull-based**: Claude has no live listener and sees your message only when
something makes it look. Say `check slack` in a session, or set up a poll:

```
Ask Claude: "set up a slack poll every 17 minutes on weekday working hours"
```

That creates a scheduled task. **Scheduled tasks only run while the Claude app is open** —
if it's closed when a poll is due, it runs at next launch. This is a desktop assistant,
not a server.

Only messages starting with `!os` are treated as commands. Everything else in the channel
is ignored, so you can paste JDs and notes freely.

Try it: `!os find jobs`

### Gmail — draft outreach, track replies

1. **Settings → Connectors → Gmail → Connect**
2. Add to `config/user.json`:

```json
"integrations": {
  "gmail": {
    "enabled": true,
    "signature": "Your Name\nyour@email.com\nlinkedin.com/in/your-handle",
    "label": "CareerOS",
    "scan_days": 14,
    "follow_up_after_days": 7,
    "auto_label": true
  }
}
```

**Claude drafts. You send.** Claude will never send email on your behalf — not even if
you ask it to, not even from a Slack command. Outreach becomes a Gmail draft with the
label applied; you review and hit send yourself. Cold email to a recruiter is
irreversible and goes out under your name, so the review step stays.

The half that compounds is the scanning. `scan inbox` classifies job-related mail into
interview invites, live replies, awaiting, stale and closed — then writes status back
to `data/job-tracker.md`. Applications go quiet silently; this is what catches it.

```
scan inbox
who hasn't replied?
follow up with Meta
```

Scanning is scoped to companies in your tracker, known recruiter addresses, and
job-related subject patterns. It does not read your whole inbox.

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
