---
name: cover-letter
description: >
  Generate a tailored, humanized cover letter for a specific company/role.
  Uses the targeted resume (not just master doc) so achievements match what was
  already selected for this application. Runs through humanizer pass. Exports
  cover-letter.md + cover-letter.html + cover-letter.pdf into the same resume folder.
  Trigger: "make cover letter for [Company/Role]", "write cover letter", "cover letter for [Company]"
---

# Cover Letter Skill

Produces a tailored, human-sounding cover letter that is consistent with the
targeted resume — same achievements, same framing, same emphasis — not a generic
draw from the master doc.

---

## When to Invoke

- `make cover letter for [Company/Role]`
- `write cover letter for [Company/Role]`
- `cover letter for [Company]`
- Automatically after a full resume pipeline run if the user asks for cover letter

---

## Inputs Required

1. **Target company and role** — from the command
2. **JD** — paste in, or fetch via Firecrawl if a URL is provided
3. **Targeted resume** — auto-located (see Step 1 below)
4. **Master experience doc** — `data/master-experience.md`
5. **Company intel** — `data/market/company-intel/[company-slug].md` if it exists

---

## Pipeline

### Step 1 — Locate the Targeted Resume

Search `resumes/` for folders matching `[Company]_[Role]_*`:

```
resumes/Razorpay_SeniorPM_*/
```

- If multiple versions exist, use the **highest version number** (latest)
- Read `resume.md` from that folder — this is the PRIMARY source of achievements
- If no targeted resume exists for this company/role, warn:
  > "No tailored resume found for [Company/Role]. Cover letter quality will be lower
  > without one — run `make resume for [Company/Role]` first, or continue with
  > master doc only?"
  Wait for user confirmation before continuing with master doc only.

### Step 2 — Load Context

Read in order:
1. `resumes/[folder]/resume.md` — the targeted resume (primary)
2. `data/master-experience.md` — full story, for depth not in the resume
3. `data/market/company-intel/[company-slug].md` — if exists, for specific company hooks
4. JD — from URL (use Firecrawl) or pasted text

From the targeted resume, extract:
- Top 3 achievement bullets (those with the strongest metrics)
- The summary/positioning statement (if present)
- Technical skills emphasized for this role
- The explicit framing used (growth-focused, technical, leadership, etc.)

From company intel (if available):
- A specific recent initiative, product, or value that is genuinely interesting
- Team size, stack, or culture detail worth referencing

### Step 3 — Write the Cover Letter

**Target length: 250–320 words.** Hiring managers do not read long cover letters.
Four paragraphs, strict structure:

#### Paragraph 1 — The Hook (2-3 sentences)
- Open with something specific about THIS company — a product decision, a public
  engineering post, a recent launch, a value they've stated publicly
- NOT: "I am excited to apply for the [Role] position at [Company]"
- YES: "Your recent [X] caught my attention — [one sentence on why it resonates
  with work you've done]. I'd like to bring that same thinking to [Role]."
- If no company intel is available, open with the most relevant intersection between
  your background and the role's core problem

#### Paragraph 2 — Why You (3-4 sentences)
- Pull 2-3 specific achievements directly from the targeted resume.md
- Use the same metrics and framing already selected for this company
- Connect each directly to a stated requirement from the JD
- Do NOT introduce achievements that aren't in the targeted resume — consistency matters

#### Paragraph 3 — Why This Company (2-3 sentences)
- One specific reason grounded in research (product direction, engineering culture,
  mission alignment, market position)
- One sentence connecting their direction to where you want to grow
- Must be specific enough that it couldn't apply to a different company

#### Paragraph 4 — Close (2-3 sentences)
- Clear, direct ask: "I'd welcome a conversation about how I can contribute to [X]"
- Available for next step: "Happy to connect at your convenience"
- No "I hope to hear from you soon" — too passive

**Salutation:** "Hi [Hiring Manager name]," if known from intel, otherwise "Hi [Company] Team,"
**Sign-off:** "Best," followed by full name

### Step 4 — Humanizer Pass

Apply humanizer rules specifically tuned for cover letters:

**Strip these phrases entirely:**
- "I am excited / thrilled / passionate about"
- "I believe I would be a great fit"
- "I am writing to express my interest in"
- "Please find attached" / "Please consider my application"
- "leverage", "synergize", "orchestrate", "spearhead", "utilize"
- "results-driven", "team player", "self-starter", "detail-oriented"
- "proven track record of"
- Anything that starts with "As a [Job Title]..."

**Rewrite rules:**
- Replace adjective-heavy phrases with specific examples
- Replace passive voice with active: "I led" not "I was responsible for leading"
- Vary sentence length — two short sentences followed by one longer one reads human
- The goal: sounds like a smart person who wrote this in 30 minutes, not a bot

**Do NOT show before/after for each line** (unlike the resume humanizer).
Apply changes directly and present the final version.

### Step 5 — Save Files

**Folder:** Same folder as the targeted resume — `resumes/[Company]_[Role]_[date]_v[N]/`
If no targeted resume exists, save to `resumes/[Company]_[Role]_[today]_v1/` (create it).

Save:
- `cover-letter.md` — clean markdown, the editable source
- `cover-letter.html` — cover letter injected into the active cover letter template
- `cover-letter.pdf` — via Puppeteer (same pipeline as pdf-export skill)

**Template:** Read `templates/cover-letter-templates/` and use:
- The file marked `<!-- default: true -->` on its first line
- If only one `.html` file exists, use it
- If none exists, use the built-in template below and save it first

### Step 6 — Commit

```bash
git status   # always check first
git add resumes/[folder]/cover-letter.md resumes/[folder]/cover-letter.html resumes/[folder]/cover-letter.pdf
git commit -m "resume: cover letter for [Company]_[Role]_[date]_v[N]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Built-in Cover Letter Template

If no template exists in `templates/cover-letter-templates/`, create
`templates/cover-letter-templates/default.html`:

```html
<!-- default: true -->
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Calibri', 'Segoe UI', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.65;
    color: #1a1a1a;
    background: white;
  }

  .page {
    max-width: 680px;
    margin: 0 auto;
  }

  .header {
    margin-bottom: 36px;
    padding-bottom: 12px;
    border-bottom: 1.5px solid #2c5282;
  }

  .name {
    font-size: 20pt;
    font-weight: 700;
    color: #1a1a2e;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
  }

  .contact-line {
    font-size: 9.5pt;
    color: #555;
  }

  .contact-line a { color: #2c5282; text-decoration: none; }

  .date-line {
    margin-bottom: 24px;
    font-size: 10.5pt;
    color: #444;
  }

  .salutation {
    font-size: 11pt;
    margin-bottom: 20px;
    font-weight: 600;
  }

  .body p {
    margin-bottom: 16px;
    font-size: 11pt;
  }

  .closing {
    margin-top: 28px;
    font-size: 11pt;
  }

  .closing .sign-off {
    display: block;
    margin-bottom: 40px;
  }

  .closing .sig-name {
    font-weight: 700;
    font-size: 11pt;
  }
</style>
</head>
<body>
<div class="page">
  {{COVER_LETTER_CONTENT}}
</div>
</body>
</html>
```

When populating this template, build the HTML body as:

```html
<div class="header">
  <div class="name">[Full Name]</div>
  <div class="contact-line">[Email] · [Phone] · [LinkedIn] · [GitHub/Portfolio]</div>
</div>

<div class="date-line">[Date, e.g. September 8, 2026]</div>

<div class="salutation">Hi [Name / Company] Team,</div>

<div class="body">
  <p>[Paragraph 1 — Hook]</p>
  <p>[Paragraph 2 — Why You]</p>
  <p>[Paragraph 3 — Why This Company]</p>
  <p>[Paragraph 4 — Close]</p>
</div>

<div class="closing">
  <span class="sign-off">Best,</span>
  <span class="sig-name">[Full Name]</span>
</div>
```

---

## Quality Checklist

Before saving, verify:
- [ ] Under 330 words
- [ ] Hook is company-specific — could NOT apply to another company unchanged
- [ ] Every achievement in Para 2 appears in the targeted resume.md
- [ ] No banned phrases from the humanizer list
- [ ] Metrics are preserved exactly (no rounding or paraphrasing)
- [ ] Salutation is specific (name or team), not "To Whom It May Concern"
- [ ] Sign-off is "Best," not "Sincerely" or "Regards" (too formal)
- [ ] PDF renders cleanly on one page
