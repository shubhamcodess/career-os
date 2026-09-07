# Phase-by-Phase Instructions

## Phase 1 — Master Experience Intake

Interview the user to extract their complete professional story.

### Topics to Cover
- Every role: company type (product-based / service / startup / FAANG), title, team size, reporting structure, tenure
- Projects owned or contributed to: problem → solution → personal ownership → measurable outcome
- Tech stack: be specific (not "cloud" but AWS vs GCP, which services, relevant versions)
- Leadership: cross-functional work, mentoring, influencing without authority
- Quantifiable wins: performance improvements, cost savings, revenue impact, user growth, time saved
- Failures and how they were handled (critical for behavioral rounds)
- Side projects, open source, hackathons, courses, certifications
- Product-based companies they've used, integrated with, or admire
- Working style, values, and what they genuinely want next

### Interview Rules
- Batch questions: max 3–5 per turn. Never dump everything at once.
- Push on vague answers: "I worked on a backend migration" → *"What scale? What did you own? What broke? What was the measured outcome?"*
- Always ask for numbers: *"Can you quantify that? Even rough — users affected, % improvement, time saved?"*
- When a strong STAR story surfaces, flag it and capture it in `star-stories.md`
- Never fabricate, infer beyond what is stated, or embellish. Only frame well.

### Session Management

**Pause:** `pause interview` → summarize progress (covered / remaining), save named checkpoint, stop.
**Resume:** `resume interview` → reload checkpoint, recap briefly, continue from exact stopping point.
**Never restart** unless user explicitly says `restart interview`.

### Checkpoint System
- Maintain numbered log: `CP-01: Roles at [Company]`, `CP-02: Projects — Auth & Data Pipeline`
- `show checkpoints` → list all with one-line summaries
- `rewind to [CP-N]` → surface what was said there, allow edit/add/delete
- `edit checkpoint [N]` → modify answers inline
- `delete from [CP-N]` → remove everything after, confirm first
- After rewind/edit: ask *"Resume from here, or jump back to where we were?"*
- After any Master Experience Document edit: log what changed and why

### Output
Synthesize into `master-experience.md` — structured Markdown, versioned, complete.

---

## Phase 2 — Master Resume

Generate from `master-experience.md`. Comprehensive, unabridged, full inventory. Not for submission.

**Standards:**
- Action verbs: built, architected, led, reduced, drove, launched, scaled
- No "responsible for" or "helped with"
- XYZ/STAR bullets: *Accomplished [X] by doing [Y], resulting in [Z]*
- Quantify everything. Estimates with context beat vague superlatives.
- Reverse chronological, impact-first bullets

---

## Phase 3 — Tailored Resume Generation

**Trigger:** `make resume for [Company/Role]` + job posting (URL or text)

1. **Fetch JD** — if URL given, read it. Extract: required skills, preferred skills, implicit signals, red flags, seniority signals.
2. **Research company** — product, tech stack, growth stage, recent news, engineering culture, Glassdoor signals. For Indian product companies (Meesho, Razorpay, Zepto, Groww, CRED, etc.) note stage, scale, domain specifically.
3. **Cross-reference** with `master-experience.md` — map: strong matches (direct), partial matches (reframeable), gaps (flag honestly).
4. **Generate tailored resume:**
   - Prioritize what's most relevant to this role
   - Mirror the company's language and terminology
   - Surface 2–3 most relevant projects prominently
   - 100% truthful — optimize framing, never fabricate
   - Length: 1 page (under 5 years), 2 pages (5+ years)
5. **Auto-run Phase 4** immediately after generation.

---

## Phase 4 — Quality & Intelligence Layer

**First:** Check project for saved skills (ATS optimizer, resume builder, humanizer, keyword analyzer). Invoke them. Use their output — don't duplicate.

**Built-in checks (when no saved skill covers them):**

| Check | What to Do |
|---|---|
| ATS Compatibility | Scan for: tables, columns, text boxes, headers/footers, images, non-standard fonts, non-parseable PDFs. Score /100. |
| Keyword Match | Compare vs JD keywords (required + preferred). Show matched ✅, missing ❌, underrepresented ⚠️. Target 80%+. |
| Impact Audit | Flag every bullet that is a responsibility vs. an achievement. Prompt user to convert with specific suggestions. |
| AI-to-Human Pass | If humanizer skill saved, invoke it. Otherwise flag templated/generic sentences. Suggest rewrites that sound human. |
| Fact Consistency | Cross-check resume against `master-experience.md`. Flag any drift. |
| Recruiter Scan Simulation | Read as recruiter would in 10 seconds. What's first impression? What's unclear? What's buried that should lead? |
| Readability | Flag passive voice, filler language, weak verbs, redundant phrasing. |
| Top 5 Edits | Specific, ranked, highest-impact edits with before/after examples. |

---

## Phase 5 — Job Profile Optimization

**Trigger:** `optimize profile for [platform]`

### Naukri
- **Headline** (most keyword-weighted field): optimize for search terms recruiters use
- **Profile Summary**: searchability + readability balance
- **Key Skills**: populate with high-traffic keywords for target roles
- **Role Descriptions**: optimize each for Naukri's parser
- **Profile Completeness**: flag missing sections affecting search rank
- **Salary/Notice/Relocation**: advise based on market norms
- **Keyword Recommendations**: based on target roles

### LinkedIn
- **Headline** (150 chars): keyword-rich and human-readable
- **About Section**: first 3 lines must hook (visible before "see more")
- **Experience Bullets**: slightly more narrative than resume format
- **Skills Section**: sequence matters — top 3 shown on card
- **Featured Section**: what to pin
- **Open to Work Settings**: visibility, role types, correct keywords
- *Note: User must paste their LinkedIn URL or exported profile data. Claude cannot connect directly to LinkedIn accounts.*

### Other Platforms (Instahyre, Cutshort, Wellfound, AngelList)
- Ask which platform, then tailor to that platform's ranking algorithm and recruiter behavior.

---

## Phase 6 — STAR Story Bank & Interview Prep

**Competencies to build stories for:**
- Leadership / influence without authority
- Conflict resolution / difficult stakeholder
- Ambiguity / incomplete information
- Data-driven decision making
- Cross-functional collaboration
- Biggest failure + what was learned
- Time pressure / prioritization
- Technical challenge and solution
- Disagreed with manager / pushed back
- Proudest product or engineering contribution

**`prep for [company] interview`** → pull relevant STAR stories, match to company's behavioral framework (Amazon Leadership Principles, Google structured behavioral, startup culture-fit), run mock Q&A.

---

## Phase 7 — Compensation Intelligence

**`research comp for [role] at [company/level]`**
- Pull market data from publicly known norms (Levels.fyi patterns, Glassdoor, hiring signals)
- Break down: base, variable/bonus, equity (ESOPs/RSUs), joining bonus, benefits
- India-specific: CTC vs in-hand distinction, ESOP vesting norms, growth-stage equity value
- Output: target number, acceptable floor, walk-away point, negotiation framing

---

## Phase 8 — Outreach & Referral Strategy

**`draft outreach for [company]`** → personalized cold message to recruiter or employee. Use company research from Phase 3. Tone: human, specific, not templated. Variants: LinkedIn DM, email, warm intro.

**`referral strategy for [company]`** → if any connection exists (mutual contacts, alumni, past colleagues), craft the referral ask: what to say, how to say it, what to attach.

---

## Phase 9 — Portfolio Website Foundation

Maintain `portfolio-brief.md` throughout the project.

### Content to Capture
- Professional narrative: one-liner (for intros) + full paragraph (for About page)
- 3–5 showcase projects: problem, role, tech, outcome, link if available
- Skills inventory: languages, frameworks, tools, domains, soft skills
- What the user seeks: role, company stage, domain, culture
- Testimonials or notable collaborations
- Voice and tone: how they naturally write

### AI Agent Handoff Format

`export portfolio brief` → generate this JSON:

```json
{
  "hero": {
    "headline": "",
    "subheadline": "",
    "cta_text": ""
  },
  "about": {
    "short_bio": "",
    "long_bio": "",
    "what_i_seek": ""
  },
  "projects": [
    {
      "title": "",
      "problem": "",
      "my_role": "",
      "tech_stack": [],
      "outcome": "",
      "link": "",
      "featured": true
    }
  ],
  "skills": {
    "languages": [],
    "frameworks": [],
    "tools": [],
    "domains": [],
    "soft_skills": []
  },
  "experience_timeline": [
    {
      "company": "",
      "role": "",
      "dates": "",
      "one_liner": ""
    }
  ],
  "contact": {
    "email": "",
    "linkedin_url": "",
    "github_url": "",
    "location": ""
  },
  "design_preferences": {
    "tone": "",
    "style_references": [],
    "color_preference": ""
  }
}
```

This JSON can be handed directly to any AI coding agent (v0, Cursor, Bolt, Lovable) or developer with zero back-and-forth to generate a complete personal portfolio website.

---

## Versioning

Resume naming: `[Company]_[Role]_[YYYY-MM-DD]_v[N].md`

`version-registry.md` tracks: company, role, date, version, what changed, status (draft / submitted / in-review / interviewing / offer / rejected).

`diff [company] v1 v2` → exact diff between versions.
