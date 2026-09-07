---
name: resume-ats-optimizer
description: >
  Invoke for ATS scoring, keyword gap analysis, and ATS compatibility checks.
  Triggered by: "ats check", "ats score", "will this pass ATS", or automatically
  as part of Phase 4 after every resume generation.
---

# Resume ATS Optimizer

<!-- 
  SETUP REQUIRED: Copy the full content of your resume-ats-optimizer skill
  from your Claude.ai Project into this file.
  
  To get it: go to your Claude.ai Resume project → Skills → resume-ats-optimizer
  → view skill content → copy here.
  
  Until this is filled in, Claude Code will use its built-in ATS checking logic
  from skills/job-search-command-center/references/phases.md (Phase 4).
-->

## Built-in Fallback (used until skill content is added above)

When invoked, run these checks against the resume and the job description:

### ATS Compatibility Check
- Flag: tables, multi-column layouts, text boxes, headers/footers with key info
- Flag: images, icons, graphics of any kind
- Flag: non-standard fonts (anything other than Arial, Calibri, Times New Roman, Georgia)
- Flag: special characters that may not parse (◆ ● ★ — use • or plain text instead)
- Score /100

### Keyword Match
Compare resume text against JD:
- Required skills: list matched ✅ and missing ❌
- Preferred skills: list matched ✅ and missing ❌
- Role title match: does resume title match JD title?
- Overall keyword match: X/Y keywords = N%
- Target: 75%+ for strong ATS pass

### Keyword Gap Recommendations
For each missing required keyword, recommend:
- Whether user's experience covers it (just not worded right) → suggest rewording
- Whether it's a genuine gap → flag honestly

### Output Format
```
ATS Score: [N]/100
Keyword Match: [N]%

✅ Matched: [list]
❌ Missing (required): [list]
⚠️  Underrepresented: [list]

Formatting Issues: [list or "None found"]

Top 3 fixes for maximum ATS score:
1. [specific fix]
2. [specific fix]
3. [specific fix]
```
