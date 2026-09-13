---
name: google-resume
description: >
  Resume creation and tailoring dedicated to Google job openings (postings on Google
  Careers). Built on Google's own published hiring guidance: a job-specific resume
  started from a blank page, explicit alignment to the role's Minimum Qualifications,
  impact written as "accomplished [X] as measured by [Y], by doing [Z]", and Google's
  application rules (3 applications per rolling 30 days, 2 MB resume, no edits after
  submitting). Adds a minimum-qualification gate and an application-budget check on
  top of the standard resume pipeline.
  Triggers on: "make resume for Google", "google resume for [role]", "tailor my resume
  for this Google job", "apply to Google", any `make resume for` where the company is
  Google, or a google.com/about/careers job URL.
---

# Google Resume

A dedicated pipeline for Google openings. It **extends** the standard resume skills,
it doesn't replace them. `resume-builder`, `resume-ats-optimizer`, `resume-humanizer`
and `pdf-export` still run. This skill decides *what goes in* and *whether to apply
at all*, using Google's published guidance.

Two labels are used throughout so the user always knows what's authoritative:

- **[Google]**: stated on Google's official careers or help pages (sources at the end)
- **[Career OS]**: this project's own practice for applying that guidance

Never present a [Career OS] convention as a Google requirement.

---

## Why Google gets its own skill

Three things make a generic tailoring pass the wrong tool here:

1. **Applications are scarce.** [Google] Up to three applications in a rolling 30-day
   window, and a submitted application can't be edited or deleted. Each application is
   a limited resource, so choosing the role matters as much as writing the resume.
2. **Minimum Qualifications are a hard screen.** [Google] The resume must meet the
   role's MQs *and* clearly show that it does. A strong resume that leaves an MQ
   implicit can fail at the first read.
3. **Google names the bullet format it wants.** [Google] Projects should state the
   outcome and how success was measured, using the X-Y-Z formula.

---

## Step 0 — Guardrails

- Never fabricate experience, metrics, team sizes or scope. Every claim traces to
  `data/master-experience.md` or something the user states in this session.
- If a metric doesn't exist, ask for it. If there is none, use an honest proxy
  (scale, frequency, before/after, adoption) and label it as a proxy. Never invent a
  percentage.
- Read `data/master-experience.md` and `data/star-stories.md` before writing a word.

---

## Step 1 — Get the full job description

Google postings have four sections, and all four matter:

| Section | Use |
|---|---|
| **Minimum qualifications** | The hard screen. Each one must be visibly satisfied (Step 3) |
| **Preferred qualifications** | Decides what leads, which bullets go first and which projects appear |
| **About the job** | Team, product area, what the work is actually for. Source of framing |
| **Responsibilities** | The verbs and nouns to mirror in bullets |

How to fetch:

1. If the user pasted the JD, use it.
2. If there's a URL, fetch it with `WebFetch`. Google Careers job pages often come back
   as a shell because the content is embedded in the page's `AF_initDataCallback`
   script data. If the four sections are missing, fetch the raw HTML with browser
   headers and decode that embedded blob. The same technique recovered the
   how-we-hire page.
3. If both fail, **ask the user to paste the JD.** Never tailor against a guessed JD.

Save it to `resumes/Google_[Role]_[YYYY-MM-DD]_v[N]/jd.md` so the MQ map in Step 3
can cite line-by-line.

---

## Step 2 — Application budget gate (do this before writing)

[Google] You can apply to up to 3 jobs in a rolling 30-day window, a submitted
application can't be edited, and you must wait 90 days before reapplying to the same
job. [Google] For technical roles, reapplicants do best after adding 12–18 months of
experience, and the FAQ asks people to typically wait about a year before reapplying
for the same *type* of role.

Check the user's recent Google applications in the job store:

```bash
python3 scripts/job-store.py view --filter applied --company google --format json
```

Each record has `status_set` (the date it was marked applied). Count those within the
last 30 days, then report plainly:

```
Google applications, last 30 days: 2 of 3
  2026-09-02  Senior Software Engineer, Cloud
  2026-09-10  Staff SWE, Ads
One slot left until 2026-10-02.
```

Rules:
- **3 of 3 used:** stop. Say when the next slot opens. Offer to draft the resume now
  so it's ready, and make clear it can't be submitted yet.
- **Same job applied to within 90 days:** stop and explain the reapply rule.
- **[Career OS]** With one slot left, confirm this is the role worth spending it on.
  [Google] Their own FAQ recommends narrowing to a few jobs that truly match rather than
  applying to everything that looks close.

The job store only knows about applications the user marked. If they may have applied
outside Career OS, ask.

---

## Step 3 — Minimum Qualifications map (the hard gate)

Build a table covering **every** MQ, in the posting's own words:

| # | Minimum qualification (verbatim) | Evidence (master-experience) | Where it shows on the resume | Met? |
|---|---|---|---|---|
| 1 | Bachelor's degree or equivalent practical experience | B.Tech CSE, 2019 | Education | ✅ |
| 2 | 5 years of experience with software development in one or more languages | 6 yrs Java/Python, two roles | Experience dates + Skills | ✅ |
| 3 | 3 years of experience with distributed systems | 18 months at X, stated in one bullet | Experience, role 1 bullet 2 | ⚠️ implicit |

Rules:
- **Every MQ must map to something a reviewer can see within seconds.** An MQ that's
  only implied (⚠️) must become explicit: name the technology, state the years, put it
  in a bullet.
- **Year-count MQs:** make sure the dates on the resume actually add up to the number.
  If experience is split across roles, say so in the relevant bullets.
- **Unmet MQ (❌):** say so plainly and recommend against spending an application on
  this role. Suggest closer-fitting Google roles if the job store has them. Never
  stretch a claim to cover a gap.
- Save the table as `mq-map.md` in the resume folder. It doubles as interview prep.

Then do the same for **Preferred qualifications**, ranked by how strongly the user's
evidence supports each. PQs don't gate the application. They decide ordering.

---

## Step 4 — Build from a blank page

[Google] Start with a blank document and create a resume designed for this specific job.
Keep an old resume nearby for reference only, and don't edit it into shape.

In practice: generate from `master-experience.md` against the MQ/PQ maps. Never start
from a previous tailored resume, including an earlier Google one.

### Section order [Career OS]

1. **Header:** name, email, city, LinkedIn, GitHub (for technical roles)
2. **Experience:** reverse chronological
3. **Projects:** only where they cover an MQ/PQ the experience section doesn't
4. **Skills:** grouped, using the exact technology names from the MQs/PQs
5. **Education:** degree, institution, year. [Google] Add GPA only if the posting asks
   for it (typical for students and new grads)

Skip a summary/objective by default. Google's guidance doesn't ask for one, and the
space goes further as another impact bullet. Add one only for a career change that
the experience section can't make obvious.

---

## Step 5 — Write every bullet as impact

[Google] Be specific about projects you worked on or managed: what was the outcome, and
how did you measure success? Use the formula:

> **Accomplished [X] as measured by [Y], by doing [Z]**

- **X:** the result for the business, product, users or engineering
- **Y:** the measurement: a number, scale, frequency, or before → after
- **Z:** what you actually did: the technical work or decision

Google's own example is lighthearted ("increased tail wags of Dooglers by 75% over two
days by placing dog treats outside of conference rooms"). The structure is what
matters: outcome, number, method.

[Google] The guidance says to use *variations* of the formula. Don't make every bullet
the identical template, because a column of mechanical bullets reads as generated.
Vary the order (Z-first or Y-first) while keeping all three parts. `resume-humanizer`
checks for this.

Worked transformation:

| Before | After |
|---|---|
| Responsible for improving API performance | Cut p95 latency on the checkout API from 800 ms to 140 ms by moving session lookups to a Redis read-through cache, holding it under 2× traffic growth |
| Worked on the data pipeline team | Reduced nightly batch runtime 6 h → 90 min for 40 downstream teams by partitioning Spark jobs on event date and removing a full-table shuffle |

Additional rules:

- **[Google] Leadership:** if the user led anything, state **team size** and **scope**.
  This includes leading without the title and leadership outside work (volunteer,
  part-time). "Led 4 engineers across 2 time zones to…" beats "led a team".
- **[Google] Data everywhere possible.** Tie work directly to the role's qualifications
  and include data.
- **[Career OS] Mirror MQ and PQ wording exactly.** If the MQ says "distributed
  systems", write "distributed systems", not "scalable backend architecture". This
  helps the parser and the human reviewer alike.
- **[Google] Early career:** with limited work experience, use school projects and
  coursework that demonstrate the qualifications.
- 3–5 bullets for recent relevant roles, fewer for older ones.

---

## Step 6 — Length and skim test

- **[Google]** There's no length requirement for experienced candidates. Clear and
  succinct is what they ask for.
- **[Google]** For students and early career: aim for one page.
- **[Google] Skim test:** if someone had only a few minutes, could they find the
  relevant information quickly? Apply it literally: each MQ from Step 3 should be
  findable in under 10 seconds.
- **[Career OS]** Under ~8 years of experience: one page. Beyond that: two pages at
  most, with early roles compressed to one line each.

---

## Step 7 — Cover letter: skip by default

[Google] Cover letters aren't required, and Google suggests putting that time into the
resume instead. Don't offer one unprompted. If the user wants one, the same rules apply:
tailor it to this job, show the difference you made with data, and connect the user's
motivation to this specific position. Hand off to `skills/cover-letter/SKILL.md`.

---

## Step 8 — Run the standard quality layer

In order, as the normal pipeline does:

1. `resume-ats-optimizer`: score keyword match against **MQs first, then PQs**. An
   MQ keyword missing from the resume is a blocker, not a score deduction.
2. `resume-humanizer`: check especially for identical X-Y-Z templating and invented
   metrics.
3. `pdf-export`: produce `resume.pdf`.

---

## Step 9 — Pre-submit checklist

Present this before the user submits, since it can't be edited afterwards:

- [ ] [Google] PDF is under **2 MB**
- [ ] Every MQ in `mq-map.md` is ✅, with none left implicit
- [ ] Single-column layout, no tables or text boxes, so the application form's parser
      can read it [Career OS]
- [ ] [Google] After uploading, re-check the auto-filled fields. The parser can miss
      things, and missing fields have to be filled in by hand
- [ ] [Google] Education, work history and cover letter fields are optional
- [ ] Contact email is one the user checks regularly (Google's primary channel)
- [ ] Budget gate from Step 2 still passes
- [ ] [Google] **Nothing can be edited after submission.** Confirm the final file

After they confirm they've submitted:

```bash
python3 scripts/job-store.py mark applied "Google" "[exact role title]"
```

This keeps the 30-day budget in Step 2 accurate next time. Log the version to
`data/version-registry.md` and back up with `bash scripts/sync-vault.sh -m "resume:
Google [role] vN"`.

---

## Step 10 — Bridge to interview prep

[Google] Google's interview guidance tells candidates to cross-reference their resume
with the job description and build a library of examples for the overlap. It says
interviews rely heavily on "tell me about a time when…" questions, recommends STAR
structure, and emphasises data, handling ambiguity, collaboration and leadership.

So every resume this skill produces also gets `interview-bridge.md` in the same folder:

| Resume bullet | MQ/PQ it proves | STAR story (star-stories.md) | Likely question |
|---|---|---|---|
| Cut checkout p95 800→140 ms… | PQ: performance at scale | "Checkout latency crisis" | Tell me about a time you improved a system under load |

If a bullet has no matching STAR story, flag it. That claim will be probed in an
interview, and the user needs the full story ready.

[Google] Also tell the user: AI tools aren't permitted during Google interviews, and
there are no brainteasers. Questions are open-ended, role-related and scored against
consistent rubrics.

---

## Output

```
resumes/Google_[Role]_[YYYY-MM-DD]_v[N]/
├── jd.md                ← the posting, as fetched or pasted
├── mq-map.md            ← MQ + PQ evidence tables (Step 3)
├── resume.md
├── resume.html
├── resume.pdf
└── interview-bridge.md  ← bullet → MQ → STAR → likely question (Step 10)
```

---

## Commands

| Command | Action |
|---|---|
| `make resume for Google [role]` + JD/URL | Full pipeline, Steps 0–10 |
| `google mq check [url]` | Steps 1 + 3 only: can this role pass the MQ screen? |
| `google application budget` | Step 2 only: slots used in the last 30 days |
| `google pre-submit check` | Step 9 checklist against the latest Google resume |

---

## Process context (for setting expectations)

[Google] After an application is selected, expect roughly 6–8 weeks. That usually
covers a Google Hiring Assessment (workstyle) and sometimes a role-related assessment
such as a coding exercise, one or two recruiter conversations, possibly project work
(a case study, writing or code samples), then a panel of structured interviews. The
decision draws on several perspectives across the application and interviews.
Recruiters can't follow up with every applicant, so the Google Careers profile is
where application status shows up. Most Googlers applied to other Google roles before
reaching interviews, so a rejection often comes down to timing.

---

## Sources

Retrieved 2026-09-14. Google's careers pages render their content from an embedded
script blob, so they were read by decoding that data rather than through plain fetch.

- [Our hiring process — Google Careers](https://www.google.com/about/careers/applications/how-we-hire/)
- [How to prepare for the hiring process — Google Careers](https://www.google.com/about/careers/applications/stories/applying-to-google)
- [Interviewing at Google: best practices, advice, and tips — Google Careers](https://www.google.com/about/careers/applications/interview-tips)
- [Apply for a job — Google Careers Help](https://support.google.com/googlecareers/answer/6095391?hl=en)

Re-check these if the skill hasn't been reviewed in ~6 months, since application limits
and waiting periods can change. When Google's pages and this file disagree, Google wins.
Update the file.
