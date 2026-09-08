---
name: cold-outreach
description: >
  Draft a highly personalized cold email to a specific recruiter or hiring manager at
  a target company. Pulls from all available intel (company-intel, role-portrait, targeted
  resume, master experience, recruiter profile) to produce a 100-150 word email that
  leads with ONE specific hook, cites ONE achievement, and asks for ONE thing.
  Runs a cold-email-specific humanizer pass. Renders visually in chat as an email card.
  Option to persist to data/outreach/ for later reference.
  Trigger: "draft outreach for [company]", "cold email to [recruiter]",
  "write outreach for [company/role]", "draft email to [name] at [company]"
---

# Cold Outreach Skill

Produces a cold email that a recruiter actually reads and replies to. Not a cover letter,
not a LinkedIn message, not a "I am interested in opportunities at your company" template.

**The only email that gets a reply is the one that doesn't look like every other email
in a recruiter's inbox.** That means: short, specific, peer-to-peer in tone, and
immediately answers "why should I spend 15 minutes on this person?"

---

## The Physics of Cold Email

A recruiter spends 3-5 seconds on a cold email before deciding to reply or delete.
That means:

- **Subject line**: must be specific enough to stop the scroll
- **Sentence 1**: must show you know something specific about THEM or their company
- **Sentence 2-4**: your single most relevant win, with a number
- **Sentence 5-6**: direct, low-friction ask
- **PS** (optional but powerful): PS lines get read even when the body gets skimmed —
  use it for a portfolio link, a relevant GitHub repo, or a specific project reference

Total body: **100-150 words hard limit.** Longer = deleted.

---

## When to Invoke

- `draft outreach for [company]`
- `cold email to [recruiter name] at [company]`
- `write outreach for [company] [role]`
- `draft email to [name]` (when company is already known from context)

---

## Input Gathering

Collect before writing. Ask for what's missing — don't fabricate.

### Required
- **Target company** — always required
- **Target role** (the JD or role title being pursued) — strongly preferred; if not provided,
  use the user's primary target role from `config/user.json`

### Optional but high-impact (ask if not provided)
- **Recruiter / hiring manager info** — any of:
  - Full name
  - LinkedIn URL → fetch full profile via Firecrawl
  - Job title at the company
  - GitHub username (if found in company intel)
  - Something they've written/posted publicly (talk, blog post, tweet, conference talk)
- **Selected resume** — which version to reference
  (`resumes/[Company]_[Role]_*/resume.md` — auto-detect if not specified)

### Auto-loaded (no need to ask)
- `data/master-experience.md` — full story, for selecting the single best achievement
- `data/market/company-intel/[company-slug].md` — if it exists
- `data/market/role-portraits/[role-slug].md` — if it exists
- `resumes/[Company]_[Role]_*/resume.md` — latest tailored resume for this company/role
- `config/user.json` — name, email, LinkedIn, GitHub for email signature

---

## Research Protocol

### Step 1 — Load All Available Intel

Read in this order:
1. `resumes/[Company]_[Role]_*/resume.md` (latest version) — extract top 3 achievement bullets
2. `data/master-experience.md` — for achievements that may not be in the tailored resume
3. `data/market/company-intel/[company-slug].md` — company signals, recent news, culture
4. `data/market/role-portraits/[role-slug].md` — what people in this role build

If company intel is missing or >14 days old, note it but don't block — proceed with
what's available. Offer to run `profile intel for [company]` afterward.

### Step 2 — Recruiter Research (if any info provided)

If a LinkedIn URL is given:
```
Firecrawl: fetch [linkedin_url]
```
Extract: current role/title, how long at company, recent posts or articles they've shared,
any public interests (conferences they attend, topics they post about), prior companies.

If a name is given without a URL:
```
Web search: "[name]" "[company]" recruiter OR "talent acquisition" OR "hiring manager"
```
Try to find: their LinkedIn, any public profiles, talks or posts.

If a GitHub username is in the company intel:
```
GET https://api.github.com/users/[username]
```
Check their public repos, bio, interests — useful for technical hiring managers.

**What to extract from recruiter research:**
- A specific recent activity (post shared, conference attended, tool they mentioned)
- Career background (what have they hired for before — signals what they value)
- Any shared professional interest with the user's background
- Their first name for salutation

If no recruiter info is available: address email to "the [Company] recruiting team"
in the salutation and omit the personalized recruiter hook (rely on company hook instead).

### Step 3 — Identify the ONE Hook

From all research, select the single strongest personalization anchor:

**Priority order:**
1. Something the recruiter specifically did, wrote, or said publicly
   ("Your talk on [X] at [Conference] — the point about [specific detail] stuck with me")
2. A recent company initiative, product launch, or engineering decision
   ("Your migration to [tech] last quarter, described in your eng blog — that's exactly
   the problem I solved at [Company]")
3. A company value or culture signal that genuinely maps to the user's background
4. A shared connection between what the company is building and the user's specific expertise

**Disqualified as hooks (too generic):**
- "I've always admired [Company]'s mission"
- "I saw you're hiring for [Role]"
- "Your company is a leader in [space]"
- Any hook that could apply to 10 other companies

### Step 4 — Identify the ONE Achievement

From the targeted `resume.md` (preferred) or `master-experience.md`:

Select the achievement that:
- Has the strongest metric (%, $, time saved, scale)
- Most directly maps to what this company's role needs
- Is specific enough to be verifiable (not "improved performance")
- Is short enough to fit in 2 sentences

One achievement only. A list of achievements in a cold email reads as desperation.

---

## Email Construction

### Subject Line (6-10 words)

**Formulas — pick the best fit for available intel:**

| Formula | Example |
|---|---|
| `[Their thing] + [Your skill]` | "Your Kafka migration → I've done this twice" |
| `[Metric] → [Company implication]` | "Cut API latency 40% — could do the same at [Company]" |
| `Re: [Specific thing they built/said]` | "Re: your post on distributed tracing" |
| `[Role] at [Company] — [Your name]` | "Senior PM at Razorpay — [Name]" (only if you have a strong email body) |
| `[Shared interest] + opportunity` | "Rust in production + your infra role" |

Never: "Excited about [Role] opportunity", "Quick question about [Company]",
"Reaching out regarding...", "I wanted to introduce myself"

### Email Body (100-150 words)

```
Hi [First Name / [Company] Team],

[HOOK — 1-2 sentences]
[Something specific about them/their company that shows real research. NOT "I admire your mission."
The recruiter must think: "they actually know what we're doing."]

[ACHIEVEMENT — 2-3 sentences]
[One specific win from the targeted resume, stated with the metric, in the context of
why it's relevant here. "At [Company], I [did X] which [resulted in Y metric]. That maps
directly to [what this role needs / what you're building]."]

[ASK — 1-2 sentences]
[Specific, low-friction. Not "I would love to be considered for any opportunities."
Yes: "Would you have 15 minutes this week to talk about the [Role]?"]

[Sign-off],
[Full Name]
[Email] · [LinkedIn short URL] · [GitHub if relevant]

P.S. [Optional: one secondary hook — link to portfolio, relevant project, GitHub repo,
or something that reinforces the achievement. PS lines get read even when body gets
skimmed.]
```

### Sign-off Options (in order of preference)
- "Best," — professional, not stiff
- "Thanks," — warm, peer-to-peer
- Never: "Sincerely," "Regards," "Respectfully," (too formal for cold email)

---

## Humanizer Pass — Cold Email Rules

Apply after drafting. Cold emails have a different failure mode than resumes — they
sound like AI-generated templates, not like a human who actually took 20 minutes to
research the company.

**Strip these entirely:**
- "I hope this email finds you well" / "I hope you're doing well"
- "I am reaching out to express my interest in"
- "I came across your profile / the job posting"
- "I am excited about the opportunity to"
- "I believe I would be a great fit"
- "Please find attached / Please consider my application"
- "I am passionate about / I have always been passionate about"
- "Looking forward to hearing from you" (replace with specific ask)
- "leverage", "synergize", "spearhead", "utilize", "orchestrate"
- "results-driven", "team player", "self-starter", "proven track record"
- Any sentence that starts with "As a [job title]..."
- Rhetorical questions that sound like sales copy ("Have you ever wondered...?")

**Rewrite rules:**
- Short sentences. 10-15 words each. Vary the rhythm.
- Active voice throughout. "I cut API latency 40%" not "API latency was reduced by 40% through my efforts"
- First-person is fine here (unlike resume bullets) — this is a personal email
- Specific nouns, not adjectives. "Kafka cluster handling 80k events/sec" not "high-performance messaging system"
- The hook sentence should feel like you're continuing a conversation, not opening a pitch

**Read-aloud test:** read the email aloud. If any sentence sounds like you're presenting
at a conference or giving a performance review, rewrite it in the voice you'd use
talking to a colleague at a meetup.

---

## Visual Rendering in Chat

After humanizer pass, render the final email as a styled email card using `show_widget`.

Build the widget HTML as:

```html
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 640px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; background: #fff;">
  <!-- Email header chrome -->
  <div style="background: #f6f8fa; border-bottom: 1px solid #e0e0e0; padding: 14px 20px;">
    <div style="font-size: 18px; font-weight: 600; color: #1a1a1a; margin-bottom: 12px;">
      Subject: [SUBJECT LINE]
    </div>
    <div style="font-size: 12px; color: #666; line-height: 1.8;">
      <div><span style="color:#999; min-width:32px; display:inline-block;">From</span> [User Name] &lt;[User Email]&gt;</div>
      <div><span style="color:#999; min-width:32px; display:inline-block;">To</span> [Recruiter Name / Company Recruiting Team]</div>
    </div>
  </div>
  <!-- Email body -->
  <div style="padding: 24px 20px; font-size: 14px; line-height: 1.7; color: #1a1a1a;">
    [EMAIL BODY — each paragraph in <p> tags, PS in its own <p> with slight gray color]
  </div>
  <!-- Footer meta -->
  <div style="background: #f6f8fa; border-top: 1px solid #e0e0e0; padding: 10px 20px; font-size: 11px; color: #888;">
    [N] words · Generated [date] · [company]-[role]
  </div>
</div>
```

Use `var(--color-text-primary)` and `var(--color-bg-surface)` CSS variables for
theme-aware rendering. The card should look like a realistic email preview.

After rendering, add in regular text:
```
Word count: [N] (target: 100-150)
To persist: say "save this outreach"
To revise: say "make it more [casual/direct/brief]" or "add more about [X]"
```

---

## Persistence

By default: **show only in chat, don't save.**

If the user says "save this", "keep this", or "persist this outreach":

1. Save to `data/outreach/[Company]_[RecruiterFirstName or "recruiter"]_[YYYY-MM-DD].md`:

```markdown
# Cold Outreach — [Company] / [Role] / [Recruiter Name]
_Drafted: [date] | Resume version: [folder name] | Status: drafted_

## Subject
[subject line]

## Email
[full email text]

## Intel Used
- Company intel: [yes/no, date]
- Role portrait: [yes/no, date]
- Recruiter research: [what was found / "none"]
- Targeted resume: [folder name]

## Notes
[Any notes on follow-up, when to send, variations tried]
```

2. Commit:
```bash
git add data/outreach/[file]
git commit -m "market: cold outreach drafted for [Company] — [RecruiterName or role]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

3. Run `bash scripts/sync-vault.sh -m "market: cold outreach for [Company]"` to back it up.

---

## Variations

After the initial draft, support quick iterations without re-running the full pipeline:

| Command | Action |
|---|---|
| `make it shorter` | Trim to 80-100 words; cut the PS if needed |
| `make it more direct` | Remove any softening language; lead harder with the achievement |
| `make it more casual` | More conversational; shorter sentences; first name only |
| `different hook` | Try a different personalization angle from available intel |
| `stronger subject` | Generate 3 alternative subject lines, user picks |
| `add portfolio` | Weave in portfolio link or specific project URL in the PS |
| `follow-up version` | Draft a 2-sentence follow-up for if there's no reply after 7 days |

---

## Follow-Up Email (when requested)

If no reply after 7 days, draft a follow-up:

- **Length:** 2-3 sentences only
- **Tone:** assumes they're busy, not that they ignored it
- **Structure:** one sentence referencing the first email + one new hook or updated context +
  same low-friction ask
- **Subject:** `Re: [original subject line]` — never change the subject; keeps the thread

Example:
```
Hi [Name],

Following up on my email from [date]. Thought I'd add — [one new piece of context:
a project just shipped, a metric update, or something you read about their company].

Still happy to find 15 minutes if the timing works.

[Name]
```

---

## Quality Gates

Before rendering, verify:
- [ ] Body is 100-150 words (hard limit)
- [ ] Hook is specific enough that it couldn't apply to another company or recruiter
- [ ] Achievement has a concrete metric — no vague claims
- [ ] Ask is explicit: one specific action (call, reply, intro)
- [ ] No banned phrases survived the humanizer pass
- [ ] Subject line is ≤10 words
- [ ] PS (if included) adds a distinct secondary hook, not a repeat of the body
- [ ] Sign-off is "Best," or "Thanks," — not "Sincerely"
- [ ] Email reads at a 7th-grade level — clear, simple, direct
