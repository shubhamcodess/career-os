---
name: resume-builder
description: >
  Invoke when building or structuring any resume from scratch or from master-experience.md.
  Defines the resume.md format, section order, bullet construction, length and the writing
  rules that keep a resume ATS-safe and recruiter-readable. Triggered by Phase 2 (master resume)
  and Phase 3 (tailored resume generation).
---

# Resume Builder

Write `resumes/[Company]_[Role]_[YYYY-MM-DD]_v[N]/resume.md` in the format below. The format is
a contract with `scripts/render-resume.py`: follow it and the HTML and PDF build with one
command. Read `data/resume-preferences.md` first; where it disagrees with this file, it wins.

## The resume.md format

```markdown
# Full Name

**Headline · the target role in the JD's words**

City, ST 000000, CC · +00-0000000000 · name@example.com

[linkedin.com/in/handle](https://www.linkedin.com/in/handle/) · [github.com/handle](https://github.com/handle)

## Summary

One paragraph, 2–3 lines.

## Experience

### Company (client: X) | City, CC | Mon YYYY – Present

**Role · product or team in plain words | Mon YYYY – Present**

- Bullet.

## Projects

**Project name** | Tech, Tech | [github.com/handle/repo](https://github.com/handle/repo) · [handle.github.io/repo](https://handle.github.io/repo/)

- Bullet.

## Skills

- **Label:** Item, Item, Item

## Certifications

**Issuer:** [Certificate name](https://verification-url), [Another](https://verification-url)

## Education

**Degree, Field** | Institution | City, ST · YYYY – YYYY
```

Fields on a row are separated by ` | `, items inside a field by ` · `.

## Section order

Header → Summary → Experience → Projects → Skills → Certifications → Education.
Put Certifications above Education once the user has 3+ years of experience; reverse it for
new graduates. **Never merge two sections under one heading** ("Education & Certifications"):
parsers file everything under the first word.

## Header

- Name, then a **headline** that is the target role in the JD's wording, without claiming a
  tool the user has not used.
- **Contact line:** city, state, postal code, country · phone with country code · email.
  Online checkers flag a missing postal code or country, so include both when known.
- **Links line:** the visible text is the URL itself (`linkedin.com/in/handle`). An ATS reads
  visible text only; a link labelled "LinkedIn" gives it nothing. The renderer adds a small
  icon in front of each URL, so no label word is needed.
- Keep the contact line and the longest link short enough to sit side by side. If the build
  reports a width overflow, abbreviate the state or shorten the contact line; do not let the
  page be scaled down.

## Summary

The summary is the pitch, not a recap. In 2–3 lines:

1. **Position**: who they are for *this* role, using the JD's central phrase.
2. **Scale**: years and the size of what they have run (users, markets, volumes).
3. **Proof that appears nowhere else on the page**: a strong project or result that did not get
   its own entry. Do not repeat certifications, tools or bullets that are listed below.

It is also the best place for JD terms that are true of the whole body of work but belong to
no single bullet (evaluation, monitoring, observability, responsible AI, cross-functional).
Use the JD's exact spelling.

## Experience

**Role lines**

- Use real, plain titles. Drop qualifiers that read as "almost" ("Shadow", "Acting",
  "Informal"). Show the higher responsibility through the verb in a bullet instead
  ("Architected…", "Led…").
- **No internal codenames.** A recruiter cannot decode a project acronym. Write the product in
  plain words ("B2B order-routing platform"); if a name must appear, give the full name once
  with a plain description.
- One location per employer, on the company line, in the same form everywhere
  (`City, CC` or `City, ST`). Dates as `Mon YYYY – Mon YYYY`.

**Depth by recency**

- **Current / most relevant role:** 4–6 bullets, up to two lines each.
- **Earlier roles:** 1–2 bullets, **one line each**, impact with a number.
- Oldest role: a single line, or the role line alone.

**Bullets — X-Y-Z**

Every bullet states what was accomplished (X), measured by what (Y), by doing what (Z):

- "Cut batch runtimes 40–55% on 400K-record runs by replacing an unbounded thread pool with
  semaphore-based admission control."
- Not: "Responsible for improving batch performance."

Rules:

- Start with a strong past-tense verb that claims ownership: Architected, Designed, Built,
  Launched, Cut, Migrated. Never "helped", "assisted", "worked on", "supported", "involved in".
  If the work was a team's, still state the user's action plainly, and tell the user to be
  ready to describe their own part.
- **Name the technique, not just the outcome**: the pattern, the class of tool, the mechanism.
  "with bounded concurrency" is weak; "with semaphore-based admission control and a bounded
  thread-pool executor" is credible.
- **At least one real number per role.** Only numbers from the master doc or the user. If none
  exists, use a countable fact (flows, repositories, classes, markets) — never an invented
  percentage or a guessed team size.
- A single number, not a range, for things like team size. State each fact **once** on the
  page: no team size in two roles, no metric repeated in the summary.
- No first person. No em dashes. One spelling variant throughout (do not mix "programme" with
  "modernization").
- Write so a line does not end with one or two orphan words; the checker lists them. Trim the
  bullet rather than accept a wasted line.
- A bullet must read like a resume line, not a slogan: concrete nouns, the mechanism, the
  result. If it could be a social-media caption, rewrite it.

## Projects

- 2–3 projects that add JD terms the experience section cannot cover.
- Lead each with a **product statement** (what it is, for whom, in the user's market's words),
  then the mechanism, then the metrics.
- Adoption numbers (downloads, stars, users) only when they are real and looked up on the day;
  say where they came from in conversation.
- Links as visible URLs. Mark closed-source work `Private`. If a project name, its tech list
  and its URLs do not fit on one row, move the tech into the bullet.

## Skills

- **Named technologies only**, in their official spelling and capitalisation. No loose
  capabilities ("automated testing", "grounding", "problem solving").
- 4–5 labelled lines, each fitting on **one line** of the page.
- The first line is the one closest to the JD. Every skill listed should be defensible.
- Methods the JD names (RAG, Embeddings, Vector Search) are acceptable as skills when the
  master doc backs them; capitalise them like the rest.

## Certifications and Education

- Group certifications by issuer, one line per issuer, each name linked to its verification
  page. Leave out anything expired.
- Education: institution, degree, then `City, ST · years` on the right, the same way the
  company line shows its location.

## Length

- Follow `config/user.json` → `resume.default_page_length` and the preferences file.
- Under 5 years: one page. 5–10 years: one page unless the user asks for two.
- The renderer picks the spacing. When it cannot fit the target, cut words (orphans first,
  then the oldest role, then the least JD-relevant bullet). Never shrink below the tightest
  density.

## What to always cut

- Objective statements, "references available", full street address.
- Soft skills as skills. Roles older than 12 years unless directly relevant.
- Anything that repeats another line on the page.
