---
name: cold-outreach
description: >
  Write cold outreach that sounds like a person wrote it: email to a recruiter or hiring
  manager, LinkedIn connection note, InMail/DM, referral ask, and follow-ups. Researches
  one real, checkable hook about the person or their team, matches it to one provable
  achievement from data/master-experience.md, makes one small ask, then runs a humanizer
  pass. Output is plain markdown in copyable code blocks — never a widget, never a card.
  Trigger: "draft outreach for [company]", "cold email to [name] at [company]",
  "linkedin message to [name]", "connection request for [company]", "ask for a referral",
  "follow up with [company]", "write outreach for [company] [role]".
---

# Cold Outreach

A recruiter decides in a few seconds. A hiring manager reads on the phone between
meetings. An engineer asked for a referral by a stranger is deciding whether you are
worth their name. All three are answering the same question: *is this person real, and
is this about me or a mail merge?*

Everything in this skill exists to make the answer obvious in the first line.

---

## Output rules — non-negotiable

- **No widgets. No `show_widget`. No HTML cards. Ever in this skill.** They burn tokens,
  can't be copied cleanly, and add nothing to a block of text the user is about to paste
  somewhere else.
- **Every draft goes in a fenced code block**, so it renders as one copyable unit:

  ````
  ```text
  Subject: …

  Hi …
  ```
  ````
- Use `text` as the fence language. Put the subject line inside the block, so subject and
  body copy together.
- Above each block, one line only: what it is, the word or character count, and the limit
  where one exists. Example: `Cold email · 104 words · aim 50–125`.
- Below each block: the **Why this is personal** list (see below), then options.
- No preamble, no "Here's a draft I came up with!", no emoji in drafts.

---

## What the research says (benchmarks, not promises)

Numbers below are third-party benchmarks from 2026 sources. Treat them as direction, not
guarantees, and never quote them to the user as certainties.

| Signal | What the data says |
|---|---|
| Reply rates | Cold email to recruiters averages ~5%; LinkedIn messages average much higher (~17%). Direct hiring-manager email is reported far above a blind application |
| Personalization | Generic messages are close to invisible; most people say they never reply to non-personalized outreach. Personalization is the single biggest lever |
| Length | Email: ~50–125 words. InMail: under ~400 characters does best. Connection note: 120–180 characters beats filling all 300 |
| Follow-ups | Roughly three touches capture nearly all replies a sequence will ever get |
| Timing | Tuesday–Thursday mornings in the recipient's timezone; Monday morning and Friday afternoon do worst |
| Referral asks | Keep under ~90 words, make the ask small and specific, don't attach a resume in the first message — offer it |

Sources are listed at the end of this file. Re-check with WebSearch if they're over a
year old.

---

## Step 1 — Load what we already know

Read, without asking:

- `data/master-experience.md` — the only source of achievements
- `data/star-stories.md` — for the detail behind a claim
- `config/user.json` — target roles, locations, what the user wants next
- the latest `resumes/[Company]_*/resume.md` if one exists for this company
- `data/market/company-intel/[company].md` if fresh (< 14 days)
- `data/outreach/` — what was already sent to this company, so we never repeat a line
- `data/job-tracker.md` — has this company already rejected or interviewed the user?

Ask the user only for what can't be derived:

- **Who** — name, role, and a LinkedIn or company page if they have it
- **Which role** — the JD link or the listing from the job store
- **Channel** — email, connection note, InMail/DM, or referral ask
- **Anything personal** they already know about this person (met at a meetup, same
  college, a talk they gave)

If the user has no name, say so plainly and offer two options: a role-generic email to a
team alias tends to do poorly, or spend two minutes finding a name first. Recommend the
second.

## Step 2 — Find one real hook

The hook is the reason this message could only have been sent to this person. Research
it with `WebSearch` / `WebFetch`, and **record the source URL and date for each fact**.

Hook tiers, best first:

| Tier | Source | Example shape |
|---|---|---|
| **A — their own words or work** | A talk, blog post, conference session, open-source PR, podcast, a thread they wrote | "Your talk on X made the case for Y…" |
| **B — their team's product or engineering detail** | Engineering blog, changelog, release notes, public architecture post, the team's repo | "The migration your team wrote up in …" |
| **C — the role itself** | A specific, unusual requirement in the JD; a problem the role exists to solve | "The JD asks for X alongside Y, which is an unusual pair…" |
| **D — company news** | Funding, launch, expansion | Weakest. Everyone uses it. Use only with something of your own attached |

Rules:

- **Never claim to have read something you haven't fetched.** If a search result is a
  title only, either fetch it or don't reference it.
- **No flattery.** "I'm a huge fan of your work" is a tell. React to a specific claim,
  decision or trade-off instead, and have an opinion about it.
- If nothing above tier D exists, say so and write an honest **no-hook opener**: name the
  role, name the specific problem you'd be walking into, and show you've solved that
  shape of problem before. Honest and direct beats manufactured intimacy.

## Step 3 — Pick one proof

Read the JD (or the role), find its hardest requirement, and pick the **single**
achievement from the master doc that most directly answers it.

- One achievement. Not a summary of the career.
- It must carry a number or a concrete outcome, and it must already exist in the master
  doc. Never round up, never invent, never imply team work was solo work.
- Prefer a proof that matches the *hook*: if the hook is their latency write-up, lead with
  latency work, not the unrelated bigger number.
- Confidential details stay out. Use relative numbers if the absolute one is internal.

## Step 4 — Make one small ask

The ask sets the reply cost. Pick the smallest that still moves things forward:

| Ask | Use when |
|---|---|
| A specific question they can answer in one line | Cold, no relationship, senior recipient |
| "Worth a short chat?" | Recruiter, or the role is clearly open |
| "Are you the right person, or can you point me to them?" | Wrong-person risk is high |
| "Would you be open to referring me? Happy to send anything that makes it easy" | Referral asks only |

Never: multiple asks, "let me know your availability this week", a calendar link, an
attached resume in a first touch, or "looking forward to hearing from you".

## Step 5 — Write it

**Email shape** (50–125 words, subject 4–8 words, specific and lowercase-ish, never
"Exploring opportunities"):

1. One line of hook — specific, with your reaction to it.
2. One line saying who you are and why you're writing, in plain words.
3. One or two lines of proof, tied to the hook or the role's hardest requirement.
4. The ask.
5. Optional PS: one link (repo, write-up, portfolio). PS lines get read.

**Connection note** (120–180 characters; 300 max on paid, 200 on free — ask which): the
hook plus who you are. No ask at all; the ask comes after they accept.

**InMail/DM** (under ~400 characters): hook, proof, ask. One paragraph each, line breaks
between them.

**Referral ask** (under 90 words): who you are, the exact role and req ID, two concrete
reasons you fit, the small ask, and an explicit "no problem at all if you'd rather not".
Offer the resume, don't attach it.

**Voice.** Before writing, look at how the user actually writes: their master doc, any
saved outreach, any LinkedIn post drafts in `data/content/`. Mirror their sentence length
and vocabulary. If nothing exists, ask for two or three sentences they've written to
someone at work and match that.

## Step 6 — Humanizer pass

Apply `skills/resume-humanizer/SKILL.md`, plus these outreach-specific tells. Every one of
these is an instant "this is a template":

**Delete on sight**
- "I hope this email finds you well", "I hope you're doing well"
- "I came across your profile", "I stumbled upon"
- "I'm reaching out because", "I wanted to reach out"
- "passionate about", "excited about the opportunity", "thrilled"
- "leverage", "spearheaded", "utilize", "synergy", "robust", "cutting-edge"
- "As you may know", "In today's fast-paced world"
- "I believe I would be a great fit" — show it, don't claim it
- "Please do not hesitate to", "Looking forward to hearing from you"

**Structural tells**
- Em dashes used as the default connector — split the sentence or use a comma
- Rule-of-three lists ("fast, reliable, and scalable")
- "not just X, but Y"
- Every sentence the same length; perfectly balanced clauses
- Three paragraphs of exactly equal size
- Any sentence that would survive a find-and-replace of the company name

**Keep**
- Contractions. Real people use them
- One slightly informal aside, if it's true
- A short sentence. Even a fragment, occasionally
- Plain verbs: built, shipped, cut, fixed, ran, broke, rewrote

Read it aloud in your head. If it sounds like a press release or a cover letter, rewrite it.

## Step 7 — Deliver

For each channel the user asked for, output:

```
Cold email · 108 words · aim 50–125
```
then the fenced block, then:

**Why this is personal** — 2–4 bullets, each naming the specific fact and where it came
from, with the URL and date. This is how the user verifies you didn't make anything up,
and how they answer if the recipient asks "where did you see that?".

**Then offer, in one line:** a different hook, a shorter version, a warmer or more formal
tone, or the next channel. Don't produce every variant unprompted — that's what made this
skill expensive.

**Best time to send:** Tuesday–Thursday morning, recipient's timezone.

---

## Follow-ups

Three touches, total. Each one must add something new — never "just bumping this".

| Touch | When | Content |
|---|---|---|
| 1 | Day 0 | The original |
| 2 | Day 4–5 | New information: something you shipped, read, or noticed about their work. Two sentences, reply in-thread |
| 3 | Day 10–12 | The close: "I'll stop here — if timing is better later, I'm around." One or two sentences |

After three, stop. Silence is an answer, and respecting it is what makes a future message
welcome. `who hasn't replied?` in `gmail-tracker` finds threads that are due.

---

## Sending and saving

- **Claude never sends anything.** `draft this in gmail` creates a Gmail draft through
  `skills/gmail-tracker`. LinkedIn messages are copied by the user; LinkedIn is never
  automated.
- On `save this outreach`, append to `data/outreach/[company]-[YYYY-MM-DD].md`: every
  variant, the hook with its source URL, the proof used, the ask, and the send date. Then
  `bash scripts/sync-vault.sh -m "data: outreach — [company]"`.
- Log the touch in `data/job-tracker.md` so follow-up timing is traceable.

---

## Quality gates — check before showing anything

1. Could this message have been sent to anyone else at any other company? If yes, rewrite.
2. Is every fact about them traceable to a URL you actually fetched?
3. Is every claim about the user in `data/master-experience.md`?
4. Email 50–125 words? Connection note ≤ the user's limit and ideally 120–180 chars?
   InMail under ~400 chars? Referral ask under 90 words?
5. Exactly one ask, and is it the smallest one that works?
6. Zero phrases from the delete-on-sight list, zero decorative em dashes?
7. Would the user actually say these words out loud?
8. No attachment, no calendar link, no flattery, no fake urgency.

If a gate fails, fix it before output. Never show a draft with a caveat attached.

---

## Commands

| Command | Action |
|---|---|
| `draft outreach for [company]` | Research → hook → proof → email draft |
| `cold email to [name] at [company]` | Email to a named person |
| `linkedin message to [name]` | Connection note, then DM/InMail after they accept |
| `connection request for [company]` | Note only, 120–180 chars |
| `ask for a referral at [company]` | Referral ask, under 90 words |
| `follow up with [company]` | Next touch in the sequence, in-thread |
| `different hook` / `make it shorter` / `warmer tone` | Iterate without re-running research |
| `save this outreach` | Persist all variants with sources to `data/outreach/` |
| `draft this in gmail` | Hand off to `gmail-tracker` as a draft — never sent |

---

## Sources

Benchmarks above come from these; re-check annually.

- Pin, *Recruiting Outreach Benchmarks 2026* — https://www.pin.com/blog/recruiting-outreach-benchmark-report/
- HeroHunt, *Recruiting outreach reply rates 2026* — https://www.herohunt.ai/blog/recruiting-outreach-benchmarks-2026-reply-rates/
- Jobply, *Cold emailing hiring managers (2026)* — https://jobply.ai/guides/cold-email-hiring-managers
- LinkedIn Sales Solutions, *Improve InMail response rates* — https://business.linkedin.com/sales-solutions/b2b-sales-strategy-guides/improve-inmail-response-rates-on-linkedin
- ReactIn, *Connection request character limit 2026* — https://www.reactin.io/blog/linkedin-connection-request-character-limit-2026
- Rolewyn, *Asking for a referral on LinkedIn (2026)* — https://rolewyn.com/blog/ask-referral-linkedin
