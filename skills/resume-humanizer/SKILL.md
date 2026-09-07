---
name: resume-humanizer
description: >
  Invoke to make resume content sound like a real human wrote it — not an AI.
  Triggered by: "humanize", "make it sound human", "ai-to-human pass", or automatically
  as part of Phase 4 after every resume generation.
---

# Resume Humanizer

<!--
  SETUP REQUIRED: If you have a humanizer skill saved in your Claude.ai project,
  copy its content here.

  Until then, the built-in fallback below is used.
-->

## Built-in Fallback

When invoked, scan the resume for:

### Patterns That Signal AI-Written Content
- Phrases: "spearheaded", "leveraged", "synergized", "orchestrated", "facilitated"
- Openers: "Successfully...", "Effectively...", "Demonstrated ability to..."
- Vague superlatives: "significant impact", "substantial improvement", "key contributor"
- Passive construction: "was responsible for", "was involved in", "helped to"
- Generic claims with no specifics: "improved performance", "enhanced user experience"

### Rewrite Rules
- Replace with: specific verbs that match what actually happened
- Add: concrete context (who, what, how many, which team)
- Sound like: someone who lived the experience and is describing it plainly
- Rhythm: vary sentence length; not all bullets the same structure
- Voice: confident, direct, first-person implied (no "I" — omit the subject)

### Before/After Format
For each flagged sentence, output:
```
Before: [original]
After:  [rewritten]
Why:    [one line on what was wrong]
```

Apply all approved rewrites to the resume file and save.
