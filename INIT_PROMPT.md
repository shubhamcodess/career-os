# Career OS — Init Prompt

Paste this as your FIRST message after running `claude` inside your cloned repo.

---

I've cloned Career OS and I'm running you inside it with `claude`. Complete the setup
and confirm everything is ready before we begin.

## Step 1 — Verify config files exist

Check for `config/user.json` and `.env`. If either is missing, tell me to run:
```bash
cp config/user.example.json config/user.json
cp .env.example .env
```
Then stop and wait for me to fill them in before continuing.

## Step 2 — Verify structure

Run `find . -not -path './node_modules/*' -not -path './.git/*' | sort` and confirm
all expected files exist per the structure in `CLAUDE.md`. Flag anything missing.

## Step 3 — Install dependencies

```bash
npm install
```

If `config/user.json` has `naukri_enabled: true`:
```bash
pip install -r scripts/requirements.txt
playwright install chromium
```

## Step 4 — Check .env keys

Read `.env` (don't print values, just confirm presence) and tell me which of these
are set vs. missing:
- `GITHUB_PERSONAL_ACCESS_TOKEN` (required, free to create)
- `BRAVE_API_KEY` (optional, free tier)

Both are free — no paid API keys are needed for this setup.

For any missing required keys, point me to the relevant section in `docs/SETUP.md`.

## Step 5 — Configure MCP paths

Open `mcp/.mcp.json`. Confirm the `${CAREER_OS_ROOT}` variable resolves correctly —
if not using env var substitution, replace it with the absolute path from `pwd`.

## Step 6 — Test PDF export

```bash
node scripts/export-pdf.js templates/resume-templates/default.html exports/test-render.pdf
```

Confirm success and report file size.

## Step 7 — Read all skills

Read every `SKILL.md` file in `skills/`. Confirm which are ready to use and which need
missing API keys (note them, don't block on them — everything is designed to work on
free tiers, with graceful degradation if optional keys like `BRAVE_API_KEY` are absent).

## Step 8 — Initial commit

```bash
git add -A
git commit -m "init: Career OS fully initialized and ready"
git push origin main
```

## Step 9 — Confirm ready

Show me:
1. Full folder tree
2. Which `.env` keys are set
3. Which skills are fully ready vs. degraded (missing optional keys)
4. Puppeteer PDF status
5. Naukri scraper status (enabled/disabled)

Then say: **"Career OS is ready. Say 'begin intake interview' to start, or 'find jobs'
to see what's live in the market first."**

Do NOT begin the interview until I tell you to.
