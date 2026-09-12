---
name: jd-analyzer
description: >
  Analyze a job description for red flags, green flags, and overall quality before
  investing time tailoring a resume. Outputs a scored verdict (GREEN / YELLOW / RED)
  with specific quoted evidence. Trigger: "jd check", "analyze this jd", "is this jd worth applying to",
  "check this job posting", or automatically when a JD is pasted without a specific command.
---

# JD Analyzer Skill

Reads a job description and gives you an honest, evidence-based verdict on whether
this role is worth your time — before you spend hours tailoring a resume for it.

The goal is not to be negative. Green flags matter as much as red ones. The output
should tell you: apply confidently / apply but clarify these things first / pass.

---

## When to Invoke

- `jd check` + paste JD (or provide URL)
- `analyze this jd`
- `is this worth applying to?`
- `check this job posting`
- Automatically when a URL to a job posting is shared without another command

If a URL is provided, fetch the full JD text before analyzing. Use both where applicable:
- **Built-in `WebFetch`** — always available, no key needed; fast for standard HTML job pages
- **Firecrawl MCP** — richer extraction, better on JS-heavy or dynamic job boards (Greenhouse, Lever, LinkedIn Jobs); use this when the JD is on a known ATS or the page renders poorly via WebFetch
- **Built-in `WebSearch`** — if the URL is broken or redirects, search `"[company]" "[role]" job posting site:[jobboard]` to find the canonical listing URL, then fetch it

---

## Analysis Framework

Score each section 0-100. Final score = weighted average:
- Scope clarity: 25%
- Compensation transparency: 25%
- Culture signals: 20%
- Requirement realism: 20%
- Specificity (vs. vague): 10%

### 1. Scope Clarity (25 pts)

**Red flags:**
- "Other duties as assigned" in a technical/senior role
- "Wear many hats" without specifying which hats, or without corresponding equity/comp signal
- Role title doesn't match the description (e.g., "Senior Engineer" with PM responsibilities)
- Reporting structure absent (who does this role report to?)
- Team size absent

**Yellow flags:**
- Responsibilities section is a list of 15+ items with no prioritization
- Mix of tactical and strategic responsibilities with no clarity on split

**Green flags:**
- Clear primary responsibility stated upfront
- Team size mentioned
- Reporting line clear
- Distinction between "day 1" vs. "growth" responsibilities

### 2. Compensation Transparency (25 pts)

**Red flags (major):**
- "Competitive salary" or "market rate" with no range
- Range absent entirely in a role posted in states where disclosure is legally required
  (CA, NY, CO, WA, IL — note which state if role location is specified)
- "Compensation commensurate with experience" (means they'll anchor low)

**Yellow flags:**
- Range given but very wide (>50% spread, e.g., ₹15L–₹40L or $80k–$180k) — signals
  they don't know what they want, or they're screening for someone cheap
- Equity mentioned but no details (cliff, vest schedule, strike price, class)

**Green flags:**
- Explicit salary range
- Equity structure described (options/RSUs, vesting, cliff)
- Benefits listed specifically (not just "great benefits")

### 3. Culture Signals (20 pts)

**Red flags:**
- "Rockstar", "ninja", "guru", "10x", "unicorn" — hero worship culture
- "We are a family" — often signals no professional boundaries
- "Unlimited PTO" used as a primary benefit without base comp transparency
  (unlimited PTO cultures often average fewer days taken than accrual policies)
- "Fast-paced", "high-pressure", "thrive under pressure", "wear many hats" as descriptors
  of the culture (not the role) — normalizes burnout
- "Self-starter who needs little direction" at a senior level — often means no support

**Yellow flags:**
- "Startup mentality" at a Series C or later company — usually means long hours, not agility
- No mention of engineering practices (code review? on-call? tech debt policy?)
- "Passionate" required multiple times — performance pressure framed as personal identity

**Green flags:**
- Mentions of team rituals, learning budget, mentorship
- Engineering culture details (on-call rotation, code review process, incident response)
- Explicit statement on remote/hybrid/in-office expectations
- Growth path or promotion criteria mentioned

### 4. Requirement Realism (20 pts)

Check for **requirement inflation** — asking for more experience than the technology has existed
in production use, or stacking requirements that no single candidate could have:

**Technology age reference (approximate mainstream adoption):**
| Technology | Mainstream adoption | Max realistic years (2026) |
|---|---|---|
| TypeScript | 2018 | 8 |
| React | 2015 | 11 |
| Kubernetes | 2017 | 9 |
| Next.js | 2019 | 7 |
| Rust | 2020 (systems prod) | 6 |
| Go | 2014 | 12 |
| GraphQL | 2018 | 8 |
| Terraform | 2017 | 9 |

If a JD asks for "X+ years of [technology]" and X approaches or exceeds the realistic max,
flag it with the math: "8+ years of TypeScript required; mainstream adoption began ~2018,
so this requires adoption in 2018 — an unrealistic filter, not a real requirement."

**Other requirement red flags:**
- 10+ required technologies for a single engineer role
- Senior-level experience requirements (8-10 years) for a role without senior-level comp signals
- Required degree in a domain where it doesn't affect job performance
- "Required: experience with [specific internal tool]" — signals they want a poach, not a hire

**Green flags:**
- Clear distinction between "required" and "nice to have"
- Requirements match the seniority level
- Technology requirements map to the actual job description

### 5. Specificity (10 pts)

**Red flags:**
- "Experience with modern web technologies" (tells you nothing)
- "Strong communication skills" as a standalone requirement
- Responsibilities described in outcomes only with no clarity on how ("drive growth")
- Company description is marketing copy ("leader in the [X] space")

**Green flags:**
- Specific tech stack named
- Specific team/product area named
- Concrete responsibilities ("own the checkout flow", "maintain our Kafka cluster")
- Company description mentions recent product changes or engineering milestones

---

## Output Format

```
━━━ JD ANALYSIS: [Role] at [Company] ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VERDICT: 🔴 RED  /  🟡 YELLOW  /  🟢 GREEN

Score: [N]/100
  Scope clarity       [N]/25
  Comp transparency   [N]/25
  Culture signals     [N]/20
  Req realism         [N]/20
  Specificity         [N]/10

━━━ RED FLAGS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 [Flag name]
   "[Quoted text from JD]"
   [1-2 sentences on why this is a problem and what it signals]

[Repeat for each red flag found]

━━━ YELLOW FLAGS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟡 [Flag name]
   "[Quoted text from JD]"
   [1 sentence on concern + what to clarify in the screening call]

[Repeat for each yellow flag]

━━━ GREEN FLAGS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ [What's good and why it signals a healthier role]

[Repeat for each green flag — don't skip these]

━━━ MATCH SIGNAL ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Only if master-experience.md or a targeted resume is available]
Strong match:  [Skills/experiences from their profile that directly hit JD requirements]
Gaps:          [JD requirements not covered — be honest]
Angle:         [Best positioning angle given their background]

━━━ RECOMMENDATION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[One of three verdicts:]

🟢 Apply — solid role, worth the full pipeline. Start with `make resume for [Company/Role]`.

🟡 Apply with caution — worth pursuing, but clarify these before investing time:
   • [Specific question to ask in the first screening call]
   • [Specific question to ask in the first screening call]
   Don't invest in full tailoring until the screening confirms [specific thing].

🔴 Pass — [Specific reason]. If you still want to apply: [what would need to be true].
```

---

## Verdict Thresholds

| Score | Verdict |
|---|---|
| 75–100 | 🟢 GREEN — Apply |
| 50–74 | 🟡 YELLOW — Apply with caution |
| 0–49 | 🔴 RED — Pass or gather more info first |

Override the score threshold when:
- Any single **critical** red flag (no comp range in a required-disclosure state, "10x
  engineer", or a score of 0/25 on comp transparency) → force at least YELLOW verdict
- Two or more critical red flags → force RED regardless of total score

---

## Context Integration

If `data/master-experience.md` is available, include the **Match Signal** section.
If it's not available (Framework mode, or intake not done), skip that section cleanly —
do not ask for personal data in Framework mode.

If company intel exists at `data/market/company-intel/[company-slug].md`, cross-reference
the JD against what's actually known about the company. Surface any contradictions
(e.g., JD says "work-life balance" but Glassdoor or employee interviews mention burnout).

---

## Notes

- Be direct. A 🔴 verdict saves the user hours. Don't soften it.
- Always include green flags — a JD with zero greens is rare; look harder.
- The Match Signal section is the most actionable part. If the user has their data loaded,
  always include it.
- Do NOT save the analysis to a file unless the user asks. This is a quick decision tool,
  not a tracked artifact. If they want it saved: `save jd analysis` → write to
  `data/market/jd-analyses/[Company]_[Role]_[date].md`.
