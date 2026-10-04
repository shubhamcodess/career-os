---
name: recruiter-connect
description: >
  Find the recruiters hiring for the companies and roles the user wants, and reach them
  first instead of waiting to be found. Finds in-house talent-acquisition people and
  relevant agency recruiters from public sources (the job posting, web search, search
  results that point to public LinkedIn profiles, company and agency pages), ranks them
  by evidence that they hire for this role now, and hands the best to cold-outreach with
  a recruiter variant that shares role, fit, availability and resume. Keeps a contact
  list with statuses, follow-ups, a configurable daily cap and a permanent do-not-contact.
  Output is markdown tables and copyable text blocks, never widgets.
  Triggers on: "find recruiters at [company]", "find recruiters for my shortlist",
  "who is hiring for [role] at [company]", "reach out to recruiter [n]", "recruiter
  pipeline", "recruiter follow-ups", "set my availability", "recruiter stats",
  "which agencies should I talk to".
---

# Recruiter Connect

Recruiters spend their day searching for people like the user. Most candidates wait to
be found. This skill turns that around: for each company and role the user wants, find
the person actually hiring for it, and send them something worth replying to, with the
role, the fit, the availability and the resume, so the recruiter has nothing to chase.

It works on top of the rest of Career OS:

| Needs | From |
|---|---|
| Which companies and roles | `job-store.py` shortlist and feed, `config/user.json` targets |
| What to say | `skills/cold-outreach` (recruiter variant below) |
| Sending and follow-up mail | `skills/gmail-tracker` (drafts only) |
| What the recruiter will click on | `skills/linkedin-profile`, `skills/naukri-profile` |
| The record | `scripts/recruiters.py` → `data/recruiters/contacts.json` |

---

## Guardrails — non-negotiable

Decided by the user; do not loosen without asking.

- **LinkedIn: search results only.** Recruiter names, titles and profile URLs may come
  from web search results that point to public LinkedIn pages. **Never fetch a
  linkedin.com URL** (no `WebFetch`, no browser), never log in, never send connection
  requests or messages, never automate anything there. The user opens the link.
- **Emails: public sources only.** Use an address only where it's published (the job
  posting, a company or agency page, the person's own public post). Record the URL with
  `--email-source`. **No guessing patterns, no enrichment tools, no verification pings.**
  `recruiters.py` rejects an email without a source.
- **Minimum data.** Professional details only: name, title, company, location, public
  profile URL, where they were found and why they're relevant. Never phone numbers,
  personal social accounts, or anything about their life outside work. Store only the
  people the user picks, not everyone the search turned up.
- **Do not contact is permanent.** Anyone who says no, or asks not to be contacted, is
  marked `do_not_contact` and is never suggested again. The script enforces this.
- **Daily cap.** `recruiter_connect.daily_new_contacts` in `config/user.json` (default 10)
  limits how many new people are contacted per day. It keeps every message personal and
  keeps the user inside LinkedIn's own connection limits. Never work around it.
- **Three touches, then stop** (`max_touches`). Silence is an answer.
- **Claude never sends.** Messages are drafted as copyable text or Gmail drafts.
- **Nothing invented** about the user. Every claim traces to `data/master-experience.md`;
  every availability fact comes from the snapshot.
- **Output:** markdown tables and fenced `text` blocks. Never `show_widget`.

---

## Step 0 — The candidate snapshot (once)

Command: `set my availability`

The facts every recruiter asks first, kept in one place so they never differ between
messages. Stored in `config/user.json` → `recruiter_connect.snapshot`.

| Field | How it's filled |
|---|---|
| `headline` | One line from the master doc, e.g. role + years + core strength |
| `years_experience` | From the master doc |
| `notice_period`, `available_from` | **Ask.** Never infer |
| `current_location`, `open_to_locations` | From `target_locations`, confirm relocation stance |
| `work_mode` | Ask: onsite / hybrid / remote / any |
| `expected_ctc` | Ask, optional. Shared in a first message only if `share_ctc_in_first_message` is true; otherwise only when a recruiter asks |
| `resume_link` | A shareable PDF link the user controls (Drive, personal site). Ask; never upload anything on their behalf |
| `portfolio_link` | GitHub or portfolio, optional |

Before the first outreach, check `python3 scripts/status.py` → `profiles`. If LinkedIn or
Naukri was never polished, say once: recruiters will open the profile within a minute of
reading the message, so `polish my linkedin` first is worth it. Then continue if the user
wants to.

## Step 1 — Pick the targets

- `find recruiters for my shortlist` → each shortlisted job:
  `python3 scripts/job-store.py view --filter shortlist --format json`
- `find recruiters at [company]` → that company, using the user's target roles and locations
- `find recruiters for [job url]` → one specific posting

Each target is company + role + location, plus the requisition ID when the posting has
one. Recruiters search by req ID.

## Step 2 — Find in-house recruiters

Work through these with `WebSearch`, cheapest and strongest first. Record the source URL
and the date of every finding.

1. **The posting itself.** Fetch the job page (never LinkedIn). Some boards name the
   recruiter or the hiring team; Naukri, Hirist and iimjobs often show who posted it.
2. **Recent hiring posts.** Strongest evidence that someone is hiring *now*:
   ```
   site:linkedin.com/posts "[Company]" hiring "[role keyword]" (Bengaluru OR Bangalore)
   "[Company]" "we're hiring" "[role keyword]" [city] 2026
   ```
3. **Talent-acquisition profiles** at that company and city, from search snippets:
   ```
   site:linkedin.com/in ("technical recruiter" OR "talent acquisition") "[Company]" (Bengaluru OR Bangalore)
   site:linkedin.com/in "[Company]" "talent acquisition partner" "engineering"
   ```
4. **Company pages:** careers pages that introduce the recruiting team, hiring-event and
   drive pages, engineering-blog posts about hiring.

Titles that recruit engineers in India: Technical Recruiter, Senior Technical Recruiter,
Talent Acquisition Partner / Specialist / Lead / Manager, Tech Sourcer, Recruiting Lead,
Engineering Recruiter. **Skip** campus recruiters (unless the user is early career), HR
generalists, HR business partners, payroll and onboarding roles, and anyone whose
snippet says "ex-" or "former".

Read only what the search snippet shows. If the snippet doesn't establish the title,
company or city, the candidate is low confidence. Don't go and fetch the profile to
find out.

## Step 3 — Find agency recruiters (if `include_agencies`)

Agencies hold mandates from the same companies and are paid to place people, so a
well-matched agency recruiter is often the fastest reply. Use the reference list in
`config/agencies.json` (or `config/agencies.example.json`):

```bash
python3 scripts/recruiters.py agencies --type tech_specialist --seniority mid
```

- **Match the level.** Years of experience → `early` (0–2), `mid` (3–8), `senior` (9–15),
  `leadership` (15+). Executive-search firms only from senior upwards.
- **Look for a live mandate**, not just the agency name:
  ```
  "[Agency]" "[role keyword]" [city] hiring
  site:linkedin.com/posts "[Agency]" "[role keyword]" [city]
  site:linkedin.com/in "[Agency]" ("technology recruiter" OR "IT recruitment") [city]
  ```
- **Platform entries** (Instahyre, Cutshort, Hirist, Wellfound, Talent500, Uplers…) are
  channels, not people. Remind the user to keep those profiles active, because
  recruiters search them daily, rather than looking for someone to message.

## Step 4 — Rank and present

At most 2–4 people per role. Present a markdown table, no widget:

| # | Recruiter | Company | Kind | Why them (evidence, date) | Confidence | Link |
|---|---|---|---|---|---|---|

Confidence:
- **High:** named on this posting, or posted about this role or team in the last 30 days.
- **Medium:** a TA title at this company and city, with an engineering focus visible.
- **Low:** title or location unclear, or no date anywhere.

Then ask which numbers to keep. Only the picked ones are stored:

```bash
python3 scripts/recruiters.py add --name "…" --company "…" --title "…" --kind in_house \
  --location "…" --profile-url "…" --source-url "…" --evidence "…" \
  --role-title "…" --role-url "…"
```

`add` refuses anyone on the do-not-contact list and merges duplicates.

## Step 5 — Draft the message (recruiter variant)

Write it with `skills/cold-outreach` (research, voice, humanizer and quality gates
apply), using the recruiter shapes below. Recruiters want facts fast: make every one
they need visible without a reply.

**In-house, open role** — the strongest case.
- Email: 60–120 words.
  1. The role and req ID.
  2. A two-line fit, with one proof from the master doc that answers the role's hardest
     requirement.
  3. Snapshot facts: location, notice period or availability.
  4. "Resume attached", or the link.
  5. One ask: "Worth a quick call?"
- Connection note: under 180 characters, e.g. role, years, core strength, availability,
  "could I share my resume?". No attachment.

**In-house, company target with no specific role.**
- Short: what you do, the kind of team you'd fit, availability.
- Ask which teams are hiring for that profile.

**Agency recruiter.**
- Structured, because agencies match on fields. Start with what you're looking for:
  role, level, location and work mode, availability, and CTC band only if the user
  allows it.
- Name the client companies that interest you.
- Ask whether they hold matching mandates.

**Resume** follows `attach_resume_for`: `in_house_with_open_role` → attach the latest
targeted PDF from `resumes/` to the Gmail draft (or the general resume); everything else
gets `resume_link`. Never attach anything in a LinkedIn note.

**No mass messages.** Every message names the role or the evidence that made this person
relevant. Check `data/outreach/` so no line repeats between recruiters at the same company.

Deliver each draft as one-line metadata, a fenced `text` block, and the "why this is
personal" list, per cold-outreach.

## Step 6 — Log, follow up, learn

- When the user says it's sent, log the touch. This enforces the daily cap, the touch
  limit and stale checks, and sets the follow-up date:
  ```bash
  python3 scripts/recruiters.py cap                     # before drafting a batch
  python3 scripts/recruiters.py touch <id> --channel linkedin_note|inmail|email|naukri
  ```
  A contact found more than `stale_after_days` ago is refused until re-checked. Re-run
  the Step 2 search for that person, then `recruiters.py verify <id>`.
- `recruiter follow-ups` → `recruiters.py due`, then draft each follow-up per
  cold-outreach's cadence (new information each time, three touches maximum).
- Replies: the user pastes them, or `check my email` (gmail-tracker) finds them.
  - Interested → `mark <id> call_scheduled`, then offer `prep for [company] interview`.
  - "Not now" → `not_now`, kept warm for later.
  - "Please don't contact me" → `do_not_contact`, permanently.
- Mirror sends in `data/job-tracker.md` against the role.
- `recruiter stats` → reply rate by kind (in-house vs agency) and by first channel. Once
  there are about 20 touches, recommend leaning toward whatever is actually working for
  this user.
- Back up after a session: `bash scripts/sync-vault.sh -m "data: recruiters — …"`.

---

## Honest limits

- **Search coverage varies.** Some companies' recruiters are barely visible in public
  search. Say how many were found and how confident each is; never pad the list.
- **People move.** That's why there's a stale check before first contact.
- **No email for many recruiters.** Public-only means LinkedIn (opened by the user) is
  often the only channel. That's by design.
- **Agencies vary in quality** and may pitch unrelated roles. They're labelled; the user
  can set `include_agencies: false`.
- **More replies, not guaranteed replies.** Stats show what works; nothing promises a call.

---

## Commands

| Command | Action |
|---|---|
| `set my availability` | Step 0: fill the candidate snapshot |
| `find recruiters for my shortlist` | Steps 1–4 for every shortlisted role |
| `find recruiters at [company]` | Steps 1–4 for one company |
| `find recruiters for [job url]` | Steps 1–4 for one posting |
| `which agencies should I talk to` | Agencies filtered to the user's level and roles |
| `reach out to recruiter [n]` | Step 5 draft for a picked recruiter |
| `sent to [n]` | Log the touch (`recruiters.py touch`) |
| `recruiter pipeline` | `recruiters.py list` |
| `recruiter follow-ups` | `recruiters.py due` + follow-up drafts |
| `mark [n] replied / call scheduled / not now / do not contact` | `recruiters.py mark` |
| `recruiter stats` | Reply rates by kind and channel |
