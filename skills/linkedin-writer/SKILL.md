---
name: linkedin-writer
description: >
  Write or rewrite LinkedIn text (About, headline, experience descriptions, posts) so it
  is both searchable and human. Applies LinkedIn SEO rules, offers a tone choice
  (professional or balanced), and runs the humanizer pass. Used by linkedin-profile.
  Triggers on: "write my about", "rewrite my about", "linkedin seo", "linkedin writer",
  "make my linkedin more searchable", "tone: professional / balanced".
---

# LinkedIn Writer

Text only. Facts come from `data/master-experience.md`; never invent. Stage progress
in `data/profile-linkedin.md`. Do not commit or sync until the user says a section is
locked. Keep replies short: give the draft, its character counts, one line on changes.

## Tone (ask once, remember in `data/profile-linkedin.md`)

| Tone | Voice | Use when |
|---|---|---|
| **Professional** | First person, formal, precise, no contractions, no humour or asides | Senior/enterprise roles, conservative employers |
| **Balanced** (default) | First person, plain and conversational, contractions fine, one human touch | Product companies, startups, most tech roles |

Both: no buzzwords, no em dashes, no "not X but Y", no title the user doesn't hold.

## SEO rules (from 2026 recruiter and profile-writing research)

- **Hook first.** Only ~200-300 characters show before "see more". Open with clearest
  identity plus the strongest differentiator. A verifiable number is the strongest
  hook; if the user has ruled numbers out, use a concrete claim instead.
- **Keywords in sentences, not lists.** Show tools being used ("I build X with Y"),
  then give one grouped stack line for scanning. Never stuff; LinkedIn penalises it.
- **Which keywords:** exact title, core languages, frameworks, cloud and AI tools the
  user uses daily. Take them from target JDs (`job-store.py view --filter shortlist
  --format json`, `data/market/jobs/`), not guesses. Add city and region once.
- **Structure:** 3-4 short paragraphs, 200-300 words is the sweet spot (limit 2,600
  chars). Identity → technical depth → how they work → stack → optional CTA.
- **Short sentences** for mobile. Read aloud; if it sounds like a press release, redo it.
- Skills with 5+ endorsements rank higher: remind the user to get endorsements on the top 5.

## Process

1. Read the profile draft and target roles. Confirm tone.
2. Write the draft. Return: text, total chars, chars in the first 300, keywords used.
3. Humanizer pass (`skills/resume-humanizer`): strip em dashes, rule-of-three padding,
   "not just X but Y", vague superlatives, repeated words.
4. Check: title matches Experience, every claim traces to the master doc.
5. Iterate one section at a time. Never move on until the user says "locked".

## Commands

| Command | Action |
|---|---|
| `write my about` | Draft in chosen tone |
| `about tone: professional` / `balanced` | Rewrite in that tone |
| `linkedin seo check` | Keywords present vs missing, first-300 hook score, fixes |
