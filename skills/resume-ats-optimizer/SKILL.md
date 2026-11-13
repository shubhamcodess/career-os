---
name: resume-ats-optimizer
description: >
  Invoke for ATS scoring, keyword gap analysis, and ATS compatibility checks.
  Triggered by: "ats check", "ats score", "will this pass ATS", or automatically
  as part of Phase 4 after every resume generation. Runs scripts/ats-check.py and
  explains the result.
---

# Resume ATS Optimizer

An ATS does two things: it **parses** the file into fields, and it **matches** the text against
the job. This skill checks both with a script, so the result is the same every time and does
not depend on reading the PDF by eye.

## Run it

```bash
python3 scripts/render-resume.py resumes/[folder]     # build first
python3 scripts/ats-check.py resumes/[folder]         # add --pages 2 for a two-page target
```

The checker reads `resume.pdf` exactly as a parser would (text in reading order), plus
`resume.md` for structure and `jd-keywords.json` for the job's terms. It needs `pymupdf`
(`pip install -r scripts/requirements.txt`).

**The bar: 0 fails, 0 warnings, required keywords ≥ 85%, preferred ≥ 75%.** Run it after every
build and fix what it reports **before** showing the user. A resume is not "done" until it passes.

## What it checks, and the fix for each

### Layout

| Finding | Fix |
|---|---|
| More pages than the target | Cut words: orphan lines first, then the oldest role, then the least relevant bullet |
| **Page is scaled down** (shrink-to-fit) | One row is wider than the page, so Chrome shrank everything. Shorten the widest single-line row: the header contact line, or a project row with long URLs. Never accept the smaller text |
| Orphan words | Trim that bullet by a few words so it ends on the previous line; each orphan wastes a full line |
| Spare lines at the bottom | Use them: restore a cut detail, or let the renderer pick a roomier density |
| Characters some parsers garble | Replace arrows, fancy bullets and symbols with plain text |

### Parsing

| Finding | Fix |
|---|---|
| No email / phone in the first lines | Put them in the contact line under the headline |
| PDF text does not start with the name | The header's reading order is wrong; the identity block must come first |
| No LinkedIn URL as visible text | Show `linkedin.com/in/handle` as the link text, not the word "LinkedIn" |
| No postal code in the header | Add postal code and country; online checkers ask for both |
| Combined section heading | Split into two standard headings |
| Non-standard section heading | Rename to Summary, Experience, Projects, Skills, Certifications or Education |
| Mixed date formats | `Mon YYYY – Mon YYYY` everywhere |

### Content

| Finding | Fix |
|---|---|
| No number under a role | Add one real figure from the master doc, or a countable fact. Never invent one |
| Weak verbs | Replace with the action the user actually took |
| AI-sounding words, em dashes | Rewrite plainly (see `skills/resume-humanizer/SKILL.md`) |
| First person | Drop the subject |
| Mixed spelling variants | Pick one; checkers report the odd one as an "unknown word" |
| Stated more than once | Keep each fact in one place |
| Skills starting lowercase | Loose capability, not a named tool: name the technology or remove it |

Tool and product names (frameworks, class names, vendor products) will always show up as
"unknown words" in consumer checkers. That is expected; do not respell them.

### Keywords

`jd-keywords.json` is written once per job by `resume-tailoring` and reused for every version.

- **Missing term with evidence in the master doc** → work it into a bullet in the JD's exact
  wording. Check the summary too: it is the right home for terms that describe the whole body
  of work.
- **Term that appears only in a list** (reported as thin evidence) → add it to a bullet that
  genuinely used it. A keyword in Skills alone scores with the parser but not with a recruiter.
- **Term under `gaps`** → leave it out. Tell the user it is a real gap and what would close it.
- **Exact phrases matter.** "responsible-AI" does not match "responsible AI"; naming a
  monitoring tool does not match "monitoring". When a consumer checker reports a term as
  missing that looks present, compare the literal spelling first.

After rewording for keywords, re-read the changed bullets: each must still be true, still read
like a person wrote it, and still fit its lines. Then rebuild and re-run the checker.

## Reporting to the user

```
ATS check: [N] fails, [N] warnings
Required keywords: [N]%   Preferred: [N]%

Fixed in this version: [list]
Still open (real gaps): [list, with what would close each]
```

Lead with what changed and what remains. Do not paste the raw checker output.

## Online checkers

When the user pastes results from a web ATS checker:

1. Treat each flagged item as a claim to verify against the PDF text, not as an order.
2. Fix what is real (missing location parts, unknown-word spelling mixes, unquantified roles,
   combined headings, links not readable as text).
3. Explain what is noise (product names as unknown words, a location "missing" on a role line
   when it is on the employer line by the user's choice).
4. If the fix is a standing choice, record it in `data/resume-preferences.md`.

## Limits

The checker measures parsing and wording. It cannot judge whether a claim is true, whether the
strongest project was chosen, or whether a recruiter will be convinced. Those stay with
`resume-tailoring` and the user.
