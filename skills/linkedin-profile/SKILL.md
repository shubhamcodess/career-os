---
name: linkedin-profile
description: >
  Polish a LinkedIn profile field by field and keep it current, from screenshots or
  pasted text (LinkedIn is never scraped or logged into). Produces exact paste-ready
  output: headline, About, every Experience entry (title, company, dates, description,
  skills), Skills order, Featured, Open to Work, URL, banner. Also runs a content
  recommendation engine: mines data/master-experience.md for provable stories, uses
  WebSearch for fresh developments in the user's field, and ranks post ideas with hooks,
  format, outline and drafts.
  Triggers on: "polish my linkedin", "fix my linkedin profile", "linkedin headline",
  "rewrite my about section", "update linkedin", "linkedin refresh", pasted LinkedIn
  screenshots, "what should I post", "linkedin content ideas", "viral post ideas",
  "draft a linkedin post", "content calendar".
---

# LinkedIn Profile + Content Engine

Two jobs:

- **Profile.** Turn whatever is on LinkedIn today into a profile that recruiters find in
  search and that matches the resume exactly.
- **Content.** Suggest posts the user can credibly write, timed to what's happening in
  their field right now.

`skills/profile-optimizer` defers to this skill for LinkedIn.

---

## Guardrails — non-negotiable

- **Never scrape LinkedIn, never log in, never automate it.** Input is screenshots,
  pasted text, or the PDF from LinkedIn's "Resources → Save to PDF". If the user only
  gives a URL, ask for screenshots instead.
- **Nothing invented.** Every title, date, number and skill must trace to
  `data/master-experience.md` or something the user says in chat. If the profile claims
  something the master doc doesn't have, ask; don't silently copy it over.
- **One timeline everywhere.** Titles, companies and dates must match the latest resume
  in `resumes/` and the Naukri profile (`data/profile-naukri.md`). Flag any mismatch
  before writing. Recruiters cross-check.
- **Confidentiality.** No employer-internal numbers, client names or unreleased products
  unless the user confirms they're public. Default to relative metrics ("cut p95 latency
  by 40%").
- **Human voice.** Run every About, description and post through
  `skills/resume-humanizer` rules before handing it over.
- **Facts vs heuristics.** Character limits are LinkedIn's own. Algorithm and "what goes
  viral" advice comes from third-party observation and changes often: present it as
  guidance, never as guaranteed reach. Re-check with WebSearch if the last check in
  `data/profile-linkedin.md` is older than 90 days.

---

## Part 1 — Profile polish

### Step 1: Gather

1. Read `data/master-experience.md`, `config/user.json` (target roles, locations,
   companies), the latest `resumes/*/resume.md`, and `data/profile-linkedin.md` if it
   exists.
2. Ask for screenshots. The full-page set is: intro card (photo, banner, headline,
   location), About, Featured, every Experience entry expanded ("…see more" opened),
   Education, Licenses & certifications, Skills (the full list page), Recommendations,
   and the Open to Work settings. Partial sets are fine; work with what arrives.

### Step 2: Transcribe and confirm

Read each screenshot and transcribe **every field verbatim** into a "Current profile"
table: field, current value, char count. Mark unreadable bits `[unclear]`. Show it and
ask the user to correct anything before auditing. Wrong input gives confident wrong
output.

### Step 3: Audit

Score each area 0–5 with one line of why:

| Area | What good looks like |
|---|---|
| Headline | Target role in the words recruiters search, 2–3 hard skills, one proof point; the key part fits in the first ~70 chars |
| About | Hook in the first ~300 chars (visible before "see more"); story → proof with numbers → what's next; keywords woven in naturally |
| Experience | Exact titles, correct dates, employment type, location; 3–5 achievement bullets per recent role; skills attached per role |
| Skills | Top of the list = the most-searched skills for target roles; nothing stale |
| Featured | 1–3 items of proof: project, write-up, talk, strong post |
| Timeline consistency | Matches resume and Naukri exactly |
| Search basics | Custom URL, location set, Open to Work (recruiters-only) with exact target titles |
| Freshness | Current role and last 6 months of work reflected |

**Keyword source:** don't guess what recruiters search. Pull the skills and phrases
that recur in the user's target JDs: the job store's JD cache (`data/market/jobs/*.json`)
and `python3 scripts/job-store.py view --filter shortlist --format json`. Rank terms by
frequency across those JDs and use that list for the headline, About and Skills.

### Step 4: Exact output

Deliver paste-ready blocks, each with its character count and LinkedIn's limit. Use
the same order the user edits in:

```
HEADLINE  (n / 220 — first ~70 show in search)
<text>

ABOUT  (n / 2,600 — first ~300 show before "see more")
<text>

EXPERIENCE — <Company>  (one block per role, newest first)
  Title:            <exact title>
  Employment type:  Full-time | Contract | …
  Company:          <company page name>
  Location / type:  <city, country> · On-site | Hybrid | Remote
  Start – End:      <Mon YYYY> – <Mon YYYY | Present>
  Description:      (n / 2,000)
  <2-line context: team, product, scale>
  • <achievement bullet>
  • …
  Skills (pick up to 5 for this role): <skill>, <skill>, …

SKILLS — final order (top 3 are pinned highest)
1. … 2. … 3. …   Remove: …

FEATURED — what to pin, in order, with the title/description to use
OPEN TO WORK — titles, locations, workplace types, start date, visibility: recruiters only
CUSTOM URL — linkedin.com/in/<suggestion>
BANNER — one line of text for the banner image, if the user wants one
RECOMMENDATIONS — who to ask (by relationship, from the master doc) + a short ask message
```

Where a role has promotions at one company, give each title its own position under the
company group so the progression shows.

End with a **change list**: every field that changes, before → after, so the user can
tick them off.

### Step 5: Save

Write the final blocks, audit scores, keyword list and today's date as `last_synced` to
`data/profile-linkedin.md`. Back up with `bash scripts/sync-vault.sh -m "data: linkedin profile …"`.
Personal data, so never committed to `main`.

---

## Keeping it up to date

Command: `linkedin refresh`

1. Read `last_synced` from `data/profile-linkedin.md`.
2. Diff against what's newer: master-doc changes (`git -C .personal-worktree log`
   since that date, or ask), new resume versions, new STAR stories, applied/shortlisted
   roles that shift the target keywords.
3. Output **only the fields that should change**, in the Step 4 block format.
4. Nudge the user when any of these happen: new role or promotion, a shipped project
   with a number attached, a new certification, target roles changing, or 90 days
   since `last_synced`.

---

## Part 2 — Content recommendation engine

Goal: posts that make recruiters and hiring managers in the user's target space
remember them. That means credible, specific and timely, not generic advice.

### Stage A: Mine the user's proof (once, then refresh with the master doc)

From `data/master-experience.md` and `data/star-stories.md`, build a **story bank** in
`data/content/story-bank.md`. Each entry has:

- **Story:** what happened, one paragraph
- **Proof:** numbers, artifacts, stack
- **Lesson:** the non-obvious takeaway
- **Contrarian angle:** what most people get wrong here
- **Pillar:** which of 3–4 content pillars it serves
- **Sensitivity:** public / needs anonymising / don't use

**Pillars** come from the intersection of what the user has deep proof in and what their
target roles value. Example shapes: "building agentic systems in production", "lessons
from scaling X", "career moves in Y". Derive them from the data; don't invent a persona.

### Stage B: Research what's happening now (every run)

Use `WebSearch` (and `WebFetch` to read the best results) per pillar:

```
"[pillar topic] 2026" news        e.g. latest model/tool/framework releases in the user's stack
"[technology] released" OR "announces" past month
"[technology] vs [technology]" debate
"[target company] engineering blog" recent posts
"[role] hiring trends India 2026"
```

Keep items from roughly the last 30 days, with a source URL and date. Discard anything
the user has no first-hand angle on.

### Stage C: Generate and rank ideas

An idea is **a fresh trigger × a story from the bank**. "X just launched; here's what I
learned running something similar in production" beats both a news summary and an
undated war story.

Score each idea 1–5 on:

| Signal | Question |
|---|---|
| Credibility | Can the user prove it from their own work? (A 1 or 2 here drops the idea) |
| Timeliness | Is the trigger less than ~2 weeks old, or an evergreen question people keep asking? |
| Hook | Does line 1 create a gap the reader wants closed? |
| Recruiter signal | Does it demonstrate a skill the target JDs ask for? |
| Discussion | Will practitioners want to add or argue in comments? |
| Risk | Confidentiality, punching down, hot-button topics (subtract) |

### Stage D: Output idea cards

For the top 5–10, each card has:

```
#  Title of idea                                  Score  Pillar
Trigger:   <news/debate + source link + date>
Your proof: <story-bank entry>
Hooks (3 options, ≤ 2 lines each, no clickbait)
Format:    text story | carousel/document (5–8 slides) | short video | poll + comment
Outline:   3–6 beats
Close:     a specific question that invites practitioners to comment
When:      suggested day/time window for the user's audience
```

On request (`draft post #N`), write the full post in the user's voice, humanized, with
line breaks for mobile. For carousels, give slide-by-slide copy.

**Current format heuristics** (third-party observations, check they're still current):
- Dwell time and substantive comments matter more than likes.
- Document/carousel posts and strong text stories hold attention longest.
- Early engagement in the first hour or so matters.
- Don't post again within a few hours of your last post.
- Put links in the first comment rather than the post body.
- Reply to every early comment.

Say these are heuristics, and never promise virality.

### Stage E: Calendar and learning loop

- `content calendar`: 2–3 posts a week for 4 weeks, balanced across pillars and formats,
  saved to `data/content/calendar.md`.
- After posting, the user pastes the post's analytics screenshot. Log impressions,
  reactions, comments, profile views and follower change against the idea in
  `data/content/performance.md`.
- Once there are 5+ logged posts, weight future ranking toward the pillars, formats and
  hook styles that actually performed for this user, not the generic heuristics.

**Never:**
- write fake stories or "I was rejected 100 times" style bait
- engagement pods or comment-for-access schemes
- tag people without the user's say-so
- auto-post (Claude never posts to LinkedIn)

---

## Commands

| Command | Action |
|---|---|
| `polish my linkedin` + screenshots | Steps 1–5: transcribe → confirm → audit → exact output → save |
| `linkedin headline` / `rewrite my about` | Just that field, 3 options with char counts |
| `linkedin experience for [company]` | Exact Experience block(s) for one employer |
| `linkedin refresh` | Only what's changed since `last_synced` |
| `linkedin audit` | Scores + top 5 fixes, no rewrites |
| `what should I post` / `linkedin content ideas` | Stages A–D: ranked idea cards with fresh sources |
| `draft post #N` | Full post (or carousel slides) for an idea card |
| `content calendar` | 4-week plan |
| `log post performance` + screenshot | Stage E learning loop |
