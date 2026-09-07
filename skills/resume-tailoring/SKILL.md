---
name: resume-tailoring
description: >
  Invoke when tailoring a resume to a specific job description and company.
  Handles JD analysis, company research, experience reframing, and keyword matching.
  Triggered by: "make resume for [Company/Role]" + JD.
  Always reads master-experience.md and the job description before starting.
---

# Resume Tailoring

<!--
  SETUP REQUIRED: Copy the full content of your resume-tailoring skill
  from your Claude.ai Project here.

  Until then, the built-in fallback below applies.
-->

## Built-in Fallback

### Step 1 — Parse the JD

Extract and categorize:
- **Must-have skills** (required, listed first, repeated multiple times)
- **Nice-to-have skills** (preferred, bonus, "plus if you have")
- **Implicit signals** (what the role really needs, reading between the lines)
- **Seniority signals** (how much ownership/independence expected)
- **Culture signals** (words like "fast-paced", "ambiguous", "cross-functional", "data-driven")
- **Red flags** (unrealistic requirements, warning signs)

### Step 2 — Research the Company

Using available MCP connectors (brave-search or indeed):
- What does the company build? What's the core product?
- Stage: seed / Series A-C / growth / public
- Recent news: funding, product launches, leadership changes
- Tech stack: what they actually use (not what JD lists)
- Engineering culture: how they talk about their team publicly
- Indian product companies: note scale (DAU/MAU), domain (fintech/edtech/etc.), ESOP culture

### Step 3 — Map Experience to JD

Read `data/master-experience.md` and create a mapping:

| JD Requirement | My Experience | Match Level | Reframe Needed? |
|---|---|---|---|
| [requirement] | [my experience] | Strong/Partial/Gap | Yes/No |

### Step 4 — Tailoring Rules

- **Lead with what matters most to THIS company** — reorder bullets within roles
- **Mirror their language** — if they say "product sense", use "product sense" not "PM skills"
- **Surface the right projects** — pick 2-3 most relevant; move them up
- **Reframe partial matches** — if they want "growth PM" experience and you did growth
  adjacent work, frame it explicitly as growth
- **Be honest about gaps** — flag them to user; never fabricate to fill

### Step 5 — Output

Produce `resume.md` in the correct folder.
After completion, hand off to resume-builder skill for structure/formatting,
then pdf-export skill for HTML + PDF generation.
