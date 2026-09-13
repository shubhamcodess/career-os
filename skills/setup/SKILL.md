---
name: setup
description: >
  Guided first-run setup for Career OS. Walks a new user through config files,
  their target company list, the ATS registry, and connector installation —
  rendering one-click install cards for Indeed, ZipRecruiter, Dice and Gmail
  rather than making them hunt through settings. Verifies each step before
  moving on and reports exactly what is working.
  Triggers on: "setup", "/setup", "set up career os", "get me started",
  "finish setup", "what's left to set up", "add my companies", "connect my job boards",
  or automatically when config/user.json is missing or target_companies is empty.
---

# Setup

Career OS is useless until two things are true: it knows which companies you care
about, and it can reach them. This skill gets a new user to both, in order, verifying
as it goes.

**Never dump the whole checklist and walk away.** Run one phase, verify it, report the
result, then move on. A user who pastes a config and gets no confirmation does not know
whether it worked.

---

## Phase 0 — Config files

```bash
test -f config/user.json || cp config/user.example.json config/user.json
test -f .env || cp .env.example .env
```

Then in `.env`, set `PERSONALIZE=true` (personal job search) or `false` (contributing
to the framework). Everything below assumes `true`.

Report which files you created versus which already existed. Do not overwrite an
existing `config/user.json` — it holds the user's own data.

---

## Phase 1 — Who they are and what they want

Fill `config/user.json` → `profile` and `target`. Ask for anything missing; never invent
values.

```json
"profile": {
  "name": "", "email": "", "location": "",
  "linkedin_url": "", "github_username": ""
},
"target": {
  "target_roles": ["Software Engineer", "Full Stack Developer"],
  "target_companies": ["Nvidia", "Stripe", "Razorpay"],
  "target_locations": ["Bangalore, India"],
  "experience_years": 6,
  "domain_keywords": ["fintech", "AI"]
}
```

**`target_companies` takes names only — never slugs, never URLs.** The resolver works
out which ATS each one uses. "Nvidia", not "nvidia/wd5/NvidiaExternalCareerSite".

Tell the user they can add companies any time later with `add company [name]`.

---

## Phase 2 — Build the company registry

This is the step that makes job search work at all.

```bash
python3 scripts/resolve-ats.py --from-config
python3 scripts/resolve-ats.py --list
```

The resolver probes nine platforms — Greenhouse, Lever, Ashby, Recruitee, Workable,
SmartRecruiters, Workday, Eightfold/pcsx and company-specific adapters — and writes
`config/companies.json`.

Walk the user through the result by status:

| Status | Meaning | Next step |
|---|---|---|
| `verified` | Live board found | Nothing |
| `manual` | Pinned by hand | Nothing — never auto-overwritten |
| `empty` | Board exists, zero postings | Give it a careers URL |
| `unresolved` | No board found | Give it a careers URL |

Then close the gaps, in this order:

**a. Try the careers probe first — it is the permanent fix.**
```bash
python3 scripts/careers-probe.py --all-unreachable --apply
```
It reads each careers page for the ATS behind it and actively tests the host for
JS-mounted APIs. This is how Adobe and Qualcomm were recovered.

**b. Give anything still unresolved a careers URL**, so the job search routes it to
web search instead of skipping it:
```bash
python3 scripts/resolve-ats.py --set-careers "Google" https://careers.google.com
```

**c. Pin a board you already know:**
```bash
python3 scripts/resolve-ats.py --from-url "Razorpay" "https://boards.greenhouse.io/razorpaysoftwareprivatelimited"
```

**d. Flag anything marked LOW CONFIDENCE.** ATS slugs are first-come-first-served —
`google.recruitee.com` is a demo account owned by someone else. Tell the user to open
the board URL before trusting it.

Finish the phase by reporting the real number: *"N companies fetchable, M jobs reachable,
K need a careers URL."*

---

## Phase 3 — Connectors (render the install cards)

**Do not send the user hunting through settings menus.** Call
`mcp__mcp-registry__suggest_connectors` so they get one-click install cards inline.

First check what is already connected with `session_connectors_status`, then render cards
for only the missing ones:

```
mcp__mcp-registry__suggest_connectors(
  uuids: [
    "3035842b-464b-45f0-b8f0-1ddc01fb2eb2",   # Dice — no auth, works immediately
    "78cb9092-b837-4439-845d-fdccd5723e7f",   # Indeed — auth required, broadest coverage
    "8f48727e-897b-4012-8427-147b4ce5719a",   # ZipRecruiter — auth required
    "2701e52f-b826-4aaf-8b25-11f2a97c98b0"    # Gmail — outreach drafts + reply tracking
  ],
  keywords: ["jobs"],
  trigger: "user_asked"
)
```

For Slack, search the registry by name and render whatever it returns — do not guess
a UUID.

What each one buys them:

| Connector | Why | Auth |
|---|---|---|
| **Dice** | Tech-focused, best of the three for engineering | None — start here |
| **Indeed** | Broadest coverage, reaches companies with no ATS | Yes |
| **ZipRecruiter** | Extra coverage; rate-limits hard without auth | Yes |
| **Gmail** | Drafts outreach, scans inbox for replies and interview invites | Yes |
| **Slack** | Pushes results to a channel, reads `!os` commands back | Yes |

**Editing `mcp/.mcp.json` does not connect any of these in the desktop app.** They are
first-party connectors. Say so plainly — a user who edits that file and sees nothing
happen will assume the project is broken.

After they install, confirm with `session_connectors_status` and name what is live.
Connectors become available on the **next** turn, so end the turn after they click.

---

## Phase 4 — Optional extras

Offer these; do not force them. Each is independently skippable.

**Naukri** — the strongest source for an India-based search, covering companies with no
public API at all:
```bash
pip install -r scripts/requirements.txt
playwright install chromium
```
Set `naukri_enabled: true`. It needs **system Chrome** — bundled Chromium is blocked by
Naukri's WAF on TLS fingerprint.

**Slack** — set `integrations.slack.enabled`, plus `notify_channel_id` and
`command_channel_id`. Find the ID with `slack_search_channels`; a dedicated private
channel beats a team channel, since output includes recruiter names and resume drafts.

**Gmail** — set `integrations.gmail.enabled` and a signature. Claude only ever creates
drafts; the user sends.

**GitHub token** — `GITHUB_PERSONAL_ACCESS_TOKEN` in `.env`, scopes `repo` + `read:user`.
Free. Used by `github-market-map` and `profile-intelligence`.

**Private vault** — `PRIVATE_REPO_URL` in `.env` for personal-data backup via
`scripts/sync-vault.sh`.

---

## Phase 5 — Connector budgets

Indeed and ZipRecruiter authenticate as **the user's own account**. Explain that plainly,
because it is the reason the cap exists: exhausting the quota degrades a service they
use personally, outside this tool.

```bash
python3 scripts/mcp-budget.py status
```

Default is 60% of an assumed 100 calls/day. Be honest that the 100 is an assumption —
neither provider publishes a per-account MCP quota. Both numbers are tunable in
`config/user.json`:

```json
"indeed": { "enabled": true, "assumed_daily_limit": 100, "cap_fraction": 0.6 }
```

`assumed_daily_limit: 0` marks a connector unmetered — that is how Dice is configured,
since it needs no auth.

---

## Phase 6 — Verify and hand off

Run the checks and report actual numbers, not reassurance:

```bash
npm install
python3 scripts/resolve-ats.py --list
python3 scripts/mcp-budget.py status
git log -1 --format="%s"
```

Then a plain summary:

```
Setup complete.

Companies    11 of 25 fetchable · 2,586 jobs reachable · 590 in Bangalore
Connectors   Dice, Indeed, ZipRecruiter, Slack live · Gmail not connected
Web layer    built-in WebSearch/WebFetch — no key, no quota
Naukri       enabled (covers the 14 companies with no ATS board)
Budgets      Indeed 0/60 today · ZipRecruiter 0/60 · Dice unmetered

Still open
  • Gmail not connected — outreach drafting and reply tracking are off
  • 2 companies have no careers URL and will be skipped

Next: `begin intake interview` — nothing else works until your experience is captured.
```

Always end with the single next action. For a new user that is
`begin intake interview`; the resume pipeline has nothing to draw on without it.

---

## Re-running setup

`setup` is safe to run again at any point. It never overwrites `config/user.json` or the
company registry — it re-checks and reports what is still open. Use it when:

- Adding companies (or just `add company [name]`)
- A connector stopped working
- Boards moved: `resolve-ats.py --refresh`
- The user asks "what's left to set up"

---

## What NOT to do

- Don't paste the whole checklist at once — one phase, verified, then the next.
- Don't tell the user to edit `mcp/.mcp.json` for Indeed/ZipRecruiter/Dice/Slack/Gmail.
  Render the install cards instead.
- Don't invent profile values, company names or a careers URL. Ask.
- Don't claim a connector is working without checking `session_connectors_status`.
- Don't report "setup complete" while required pieces are missing — list what is open.
- Don't mention Firecrawl. It was removed; built-in WebSearch/WebFetch are the web layer.
