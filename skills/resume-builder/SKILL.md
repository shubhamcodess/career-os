---
name: resume-builder
description: >
  Invoke when building or structuring any resume from scratch or from master-experience.md.
  Handles section order, bullet construction, length optimization, and formatting standards.
  Triggered by Phase 2 (master resume) and Phase 3 (tailored resume generation).
---

# Resume Builder

<!--
  SETUP REQUIRED: Copy the full content of your resume-builder skill
  from your Claude.ai Project here.

  Until then, the built-in fallback below applies.
-->

## Built-in Fallback

### Section Order (standard for product-based company applications)
1. Header (name, contact, LinkedIn, GitHub if relevant, location)
2. Professional Summary (3 lines max — optional but recommended for career changers)
3. Experience (reverse chronological)
4. Skills (grouped by category)
5. Projects (if adding value beyond experience section)
6. Education
7. Certifications (if recent and relevant)

### Bullet Formula
Every bullet: **Action Verb + What + Result/Scale**
- "Reduced API response time by 65% (800ms → 280ms) by implementing Redis caching,
  cutting cart abandonment by 4% and supporting 2x traffic growth"
- NOT: "Responsible for improving performance of the backend APIs"

### Length Rules
- Under 5 years experience: 1 page, no exceptions
- 5-10 years: 1-2 pages; cut anything older than 8 years that's not exceptional
- 10+ years: 2 pages; summarize early career in 1-2 lines per role

### Section-Level Rules
- Experience: 3-5 bullets per role; more for recent/relevant, fewer for older
- Skills: no "proficient in", "familiar with" — list the skill or don't
- Education: just degree, institution, year — no GPA unless <3 years out
- Projects: only include if they demonstrate something the experience section doesn't

### What to Always Cut
- Objective statements ("Seeking a challenging role...")
- References available on request
- Full home address (city + country only)
- Every soft skill listed as a skill ("team player", "good communicator")
- Any role older than 12 years unless directly relevant
