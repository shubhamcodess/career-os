---
name: naukri-profile
description: >
  Build and polish a Naukri.com profile to reach a 100% profile score, rank higher in
  recruiter searches, and turn views into calls. Works from screenshots or pasted text,
  and produces exact paste-ready output for every Naukri section: resume headline, key
  skills, employment, IT skills, projects, profile summary, accomplishments, career
  profile, education, personal details. Keywords come from the user's real target JDs.
  Includes a weekly freshness routine and a views → actions → calls tracking loop.
  Triggers on: "polish my naukri", "naukri profile", "naukri score 100", "fix my naukri",
  "more naukri views", "not getting calls on naukri", "naukri refresh", pasted Naukri
  screenshots.
---

# Naukri Profile

On Naukri, recruiters search the database and filter by keywords, experience,
location, notice period and salary. A profile that isn't complete, keyword-matched and
fresh doesn't show up in those searches, however strong the candidate is.

Three outcomes to optimise, in order:
1. **Found.** Profile score at 100, exact keywords, correct filters.
2. **Noticed.** Headline and summary make a recruiter open the profile.
3. **Called.** Proof, clear availability and consistency make them pick up the phone.

`skills/profile-optimizer` defers to this skill for Naukri.

---

## Guardrails

- **Nothing invented.** Every skill, year count, project and number traces to
  `data/master-experience.md` or the user's own words. Naukri skill-years ("Python,
  6 yrs, last used 2026") are claims recruiters test in interviews.
- **One timeline everywhere.** Designations and dates match the latest resume and
  `data/profile-linkedin.md`. Flag mismatches first.
- **Honest about the numbers.** The 100% score is Naukri's own completeness meter, and
  that part is controllable. View counts and calls aren't guaranteed. Ranking and
  "freshness boost" advice comes from recruiter and third-party observation, not
  published Naukri rules. Say so, and measure what actually works for this user
  (Step 6).
- **No automation of Naukri.** Claude doesn't log in, edit or click on Naukri. The user
  pastes the output. The separate `naukri-scraper` only reads public job listings.
- **Don't push paid add-ons.** Mention Naukri's paid visibility products exist only if
  asked; organic fixes come first.

---

## Step 1: Gather

1. Read `data/master-experience.md`, `config/user.json` (target roles, locations,
   notice period and CTC if present), the latest `resumes/*/resume.md`,
   `data/profile-naukri.md` and `data/profile-linkedin.md` if they exist.
2. Ask for screenshots of every section of the Naukri profile page:
   - the top card (name, headline, experience, CTC, location, notice period, profile
     score meter)
   - resume attachment status
   - Resume headline
   - Key skills
   - Employment
   - Education
   - IT skills
   - Projects
   - Profile summary
   - Accomplishments
   - Career profile
   - Personal details
   - any "missing details" or "add X to boost your profile" prompts
3. Also ask for the **Naukri performance stats** screenshot (search appearances,
   recruiter actions, and whatever else Naukri currently shows). It's the baseline for
   Step 6.

## Step 2: Transcribe and confirm

Transcribe every field verbatim into a "Current profile" table. Note the score meter
value and every prompt Naukri shows for missing items, because those prompts are the
literal checklist for 100%. Ask the user to correct the transcription before
continuing.

## Step 3: Build the keyword list from real JDs

Recruiters search with the words in their own JDs, so take keywords from those:

1. Pull target JDs from the job store JD cache (`data/market/jobs/*.json`), plus the
   shortlist: `python3 scripts/job-store.py view --filter shortlist --format json`.
   If there are few, add fresh Naukri listings for the target roles from
   `naukri-scraper`.
2. Extract hard skills, tools, domains and role titles. Count how many JDs mention each,
   and merge synonyms under the spelling recruiters use most (e.g. "React.js" vs "React",
   "Gen AI" vs "Generative AI"; keep both forms if both are common).
3. Keep only terms the user can back with the master doc. Output a ranked list:
   **Core** (in >30% of JDs), **Strong**, **Differentiators** (rarer but high-value for
   the target roles).

## Step 4: Exact output, section by section

Paste-ready, in Naukri's section order. Show the character count where the editor has a
counter, and tell the user to check it against the live counter, since limits change.

```
RESUME HEADLINE
<[years] yrs [target title] | [3–4 Core skills] | [domain/proof point] | [notice/availability if short]>
  → exact target title in recruiter spelling; lead with what they filter on

KEY SKILLS  (ordered: Core first, then Strong, then Differentiators)
<skill>, <skill>, …          Remove: <stale or unprovable skills>

EMPLOYMENT  (one block per role, newest first)
  Current employment:   Yes / No
  Employment type:      Full time | …
  Total experience:     <yrs> <months>
  Company name:         <as registered>
  Job title:            <exact designation>
  Joining date:         <Mon YYYY>     Worked till: <Mon YYYY | present>
  Current salary:       <user supplies — never guessed>
  Skills used:          <from keyword list, true for this role>
  Job profile:
  <2-line context: product, team, scale>
  • <achievement with number>
  • …
  Notice period:        <accurate — recruiters filter on it>

EDUCATION         — course, specialisation, institute, type, years, grading
IT SKILLS         — table: skill | version | last used | experience (yrs, months)
PROJECTS          — per project: title, tagged to employment, client (or "In-house"),
                    status, worked from/till, details (problem → what you built → result),
                    role, team size, skills used; add the project URL if public
PROFILE SUMMARY   — 3 short paragraphs: who + years + domain | 2–3 proof points with numbers |
                    what you want next + availability
ACCOMPLISHMENTS   — online profiles (GitHub, LinkedIn, portfolio), work samples,
                    certifications, publications, presentations, patents: only real ones
CAREER PROFILE    — current industry, department, role category, job role,
                    desired job type, employment type, preferred shift,
                    preferred work locations (all target cities), expected salary
PERSONAL DETAILS / LANGUAGES — complete them; they count toward the score
RESUME            — upload the latest ATS-checked PDF from resumes/ (resume-ats-optimizer)
PHOTO             — a clear professional photo counts toward completeness
```

After the blocks:
- **Score checklist:** every item Naukri flagged as missing, and which block fixes it.
- **Change list:** before → after for every field.

## Step 5: Save

Write the blocks, keyword list, baseline stats and `last_synced` to
`data/profile-naukri.md`, then back up with
`bash scripts/sync-vault.sh -m "data: naukri profile …"`.

---

## Staying visible: the freshness routine

Recruiter-side results favour recently active, recently updated profiles. These are
observed patterns, not published rules. Offer the user a weekly routine and, if they
want it, a reminder via a scheduled task:

| When | Action |
|---|---|
| 2–3× a week | Log in, answer every recruiter message (even "not interested"), apply to 2–5 genuinely relevant jobs |
| Weekly | One small **genuine** edit: a new skill from the JD list, a sharper bullet, an updated project status. Rotate sections |
| Every 2 weeks | Re-upload the latest resume PDF |
| When anything changes | Notice period, CTC, location, current role: immediately, since these are hard filters |
| Monthly | Re-run Step 3 keywords against new JDs; swap out skills that stopped appearing |

Never fake activity or add skills the user can't defend just to trigger a refresh.

Command `naukri refresh` generates this week's edit: one or two specific changes, as
paste-ready text, taken from the latest keyword and master-doc changes.

## Step 6: Measure views → actions → calls

Each week (`log naukri stats` + screenshot), log to `data/profile-naukri.md`:
- search appearances
- recruiter actions (views, downloads, messages)
- calls or interview invites (from the user, or from `gmail-tracker`)
- what changed that week

Diagnose from the funnel:

| Symptom | Likely cause | Fix |
|---|---|---|
| Low search appearances | Missing keywords or filters: title spelling, location, experience band, notice period | Step 3 keywords into headline + key skills + employment; fix filters |
| Appearances but few views | Headline and top card don't earn the click | Rewrite headline around exact target title + strongest proof |
| Views but no messages or calls | Summary and employment lack proof, CTC/notice mismatch, or inconsistent timeline | Numbers in bullets, projects, consistency with resume, realistic expected CTC |
| Calls for the wrong roles | Keywords too broad | Remove generic skills, tighten the headline title |

Compare before and after each change, and keep the changes that moved the numbers.

---

## Commands

| Command | Action |
|---|---|
| `polish my naukri` + screenshots | Steps 1–5: full profile with exact output |
| `naukri headline` / `naukri summary` / `naukri key skills` | One section, 2–3 options |
| `naukri keywords` | Step 3 only: ranked keyword list from target JDs |
| `naukri refresh` | This week's genuine update, paste-ready |
| `log naukri stats` + screenshot | Step 6 funnel log + diagnosis |
| `why no naukri calls` | Step 6 diagnosis from the latest stats and profile |
