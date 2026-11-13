---
name: resume-tailoring
description: >
  Invoke when tailoring a resume to a specific job description and company.
  Handles the pre-draft intake, JD keyword map, evidence mapping, experience reframing and
  keyword matching. Triggered by: "make resume for [Company/Role]" + JD.
  Always reads master-experience.md, data/resume-preferences.md and the job description first.
---

# Resume Tailoring

The goal is a resume the user accepts on the **first or second version**. Almost every extra
iteration comes from something that could have been settled before writing: a missing contact
detail, a preference the user already stated once, a keyword that was never mapped, a number
nobody had. This skill front-loads all of that.

## Company-specific skills — check first

If the target company has its own skill, read it before this one. It overrides the
generic rules below where they conflict.

| Company | Skill |
|---|---|
| Google | `skills/google-resume/SKILL.md`: MQ gate, 3-applications-per-30-days budget, X-Y-Z bullets |

## Step 0 — Load what is already decided

Read these before anything else. Never re-ask what they answer.

1. `data/resume-preferences.md` — the user's standing resume decisions (layout, wording they
   reject, how they want titles, links, locations and numbers shown). **These are rules, not
   suggestions.** If the file is missing, create it from the template at the end of this skill
   the first time the user corrects a draft.
2. `config/user.json` → `profile` — name, email, phone, location, links.
3. The latest resume folder in `resumes/`, if any — its `resume.md` is the best starting
   structure, and `data/version-registry.md` says what changed in each version and why.
4. `data/master-experience.md` — the only source of facts. Read the Project Selection Index
   and its rules before choosing projects.

## Step 1 — Parse the JD into `jd-keywords.json`

Fetch the posting (see `skills/jd-analyzer/SKILL.md` for the fetch ladder), then write
`resumes/[folder]/jd-keywords.json` **before drafting**. It is the fixed yardstick for every
version of this resume, so the score cannot drift between iterations.

```json
{
  "required":  {"Term as the JD says it": ["spelling that counts", "another"]},
  "preferred": {"Term": ["spelling"]},
  "gaps":      ["Things the JD wants that the user has genuinely not done"]
}
```

- One entry per distinct requirement: tools, methods, and the JD's own nouns
  ("observability", "responsible AI", "prototype", "cross-functional"). Typically 25–50 terms.
- Use the JD's **exact wording** as a match spelling. Checkers and recruiters search for the
  literal phrase: "responsible AI" does not match "responsible-AI", and a tool name does not
  match the category it belongs to ("monitoring" is not matched by naming a monitoring tool).
- Spellings are case-insensitive regular expressions; plain words work as they are.
- Put a term under `gaps` only after checking the master doc. Gaps are reported to the user
  and never worded around.

Also note: seniority signals, the two or three things the role is really about, and red flags.

## Step 2 — Research the company

**This step is always deep research** — run multiple queries, fetch from multiple sources,
synthesize. Use built-in `WebSearch` and `WebFetch`; the browser only for client-rendered pages.
Check `data/market/company-intel/[company-slug].md` first and offer a refresh if it is missing
or older than 14 days (ask once, do not block on it).

Find: what they build, stage, recent news, the real tech stack, how they talk about engineering.

## Step 3 — Evidence map (before any bullet is written)

For **every** term in `jd-keywords.json`, find the evidence in the master doc:

| JD term | Evidence in master doc | Strength | Where it will appear |
|---|---|---|---|
| [term] | [project / phase + the fact] | Strong / Partial / None | Bullet in role X / project Y / skills only |

Rules:

- **Search the whole master doc, including the oldest roles.** Early-career and "maintenance"
  phases often hold the exact evidence a JD asks for (a platform migration, on-call ownership,
  a compliance process). A term is a gap only after every phase and project has been checked.
- A term with evidence must appear **in a bullet**, in the JD's wording, not only in the skills
  list. `ats-check.py` reports list-only terms as thin evidence.
- A term with no evidence goes to `gaps`. Tell the user plainly and, where realistic, say what
  small real piece of work would close it before the deadline.
- Never fabricate: not experience, not tools, not numbers. If the user asks for an invented
  number, decline, and offer the nearest real countable fact from the master doc instead
  ("one class per new integration", "6 flows", "10+ repositories").

## Step 4 — Ask everything in one round

Collect the open questions and ask them **together, once**, before drafting. Skip anything the
preferences file, config or master doc already answers. Typical gaps:

- Contact details missing from config (phone, postal code, country).
- Verification links for certifications that will be listed.
- Real numbers behind bullets that have none (team size, volumes, before/after timings).
  Offer "skip the number" as an option; then name the design instead of inventing a figure.
- Page target if the preferences file does not set one.
- Which of two equally strong projects to feature, when space allows only one.

Use `AskUserQuestion` when the session supports it. Save every answer that will matter next
time into `data/resume-preferences.md` or `config/user.json` right away.

## Step 5 — Tailoring rules

- **Lead with what matters most to this role** — order bullets by the JD's priorities.
- **Mirror their language** — the JD's phrase, not a synonym.
- **Pick 2–3 projects** by JD signal using the Project Selection Index, and prefer the ones
  that add terms the experience section cannot cover.
- **Reframe partial matches explicitly**, and keep every claim defensible in an interview.
  When a bullet describes team work, say so in conversation so the user can prepare their part.
- **Be honest about gaps** — flag them; never write around them.

## Step 6 — Hand off

Write `resume.md` following `skills/resume-builder/SKILL.md` (structure and writing rules), then:

```bash
python3 scripts/render-resume.py resumes/[folder]     # html + pdf, fitted to the page target
python3 scripts/ats-check.py resumes/[folder]         # must end with 0 fails, 0 warnings
```

Fix what the checker reports, **then** show the user. See `skills/resume-ats-optimizer/SKILL.md`
and `skills/pdf-export/SKILL.md`.

## When the user corrects a draft

Every correction is one of two things. Decide which, every time:

1. **About this resume only** (a specific bullet, this JD's wording) → fix it in a new version.
2. **A standing preference** (how they want titles, numbers, links, locations, tone, layout) →
   fix it **and append it to `data/resume-preferences.md`** in the same turn, so it is never
   raised again. When unsure, treat it as standing.

Batch the fixes: apply everything from the user's message in one new version, rebuild, run the
checker, and only then report. One version per message, not one per fix.

## `data/resume-preferences.md` — template

Personal, gitignored, backed up by `sync-vault.sh`. Create it with these headings and fill
only what the user has actually decided:

```markdown
# Resume Preferences
_Standing decisions. Read before every resume. Updated: YYYY-MM-DD_

## Layout
## Header and contact
## Titles and role lines
## Bullets and numbers
## Projects
## Skills
## Certifications and education
## Summary
## Wording to avoid
## Process
```
