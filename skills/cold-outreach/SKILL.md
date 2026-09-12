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

**Research depth rule:**
- LinkedIn URL provided → **quick fetch**: WebFetch the URL first; if thin/empty, use Firecrawl.
  One tool call per URL — don't over-research when you already have the target.
- Name only (no URL) → **targeted deep research**: run 3–4 WebSearch queries across sources,
  fetch the most promising results, synthesize what you find before writing. Don't stop at one
  failed search — try different query formulations.

If a LinkedIn URL is given — use both where they excel:
- **`WebFetch`** — fast for public LinkedIn profiles and personal sites
- **Firecrawl MCP** — use for JS-heavy or login-walled pages where WebFetch returns thin content

Extract: current role/title, how long at company, recent posts or articles they've shared,
any public interests (conferences they attend, topics they post about), prior companies.

If a name is given without a URL:
```
WebSearch: "[name]" "[company]" recruiter OR "talent acquisition" OR "hiring manager"
WebSearch: "[name]" "[company]" site:linkedin.com
WebSearch: "[name]" "[company]" blog OR talk OR conference OR podcast
```
Fetch the top results from each query via WebFetch or Firecrawl. Cross-reference to build
a picture before selecting the hook — the best hook often comes from a secondary source
(a conference talk, a tweet, a blog post) not just their job title.

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

### Email Template Skeleton

This skeleton is always followed — fill each slot, respect the word budgets.
Do not merge slots or skip the PS if a strong secondary hook is available.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUBJECT  │ [6-10 words — use a formula from the table above]
─────────┼──────────────────────────────────────────────────────────
FROM     │ [Full Name] <[email from config/user.json]>
TO       │ [Recruiter Name / [Company] Recruiting Team]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hi [First Name / [Company] Team],

▸ HOOK       [≤ 30 words]
             One specific thing about them or their company.
             Test: could this sentence appear in an email to a different company? If yes, rewrite.

▸ ACHIEVEMENT [≤ 40 words]
             One win with a metric. From targeted resume.md.
             Connect it explicitly to what this company is building or this role needs.

▸ ASK        [≤ 25 words]
             Single, specific, low-friction action.
             Name the format and timeframe: "15 minutes this week", "a quick intro call".

[Best / Thanks],
[Full Name]
[email] · [linkedin] · [github or portfolio — if relevant]

P.S. [≤ 20 words — optional but use it if there's a strong secondary hook:
     a live project, a relevant repo, a portfolio piece, or a specific metric
     that didn't fit the body. PS lines are read even when body gets skimmed.]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORD BUDGET │ Hook ≤30 · Achievement ≤40 · Ask ≤25 · PS ≤20
TOTAL BODY  │ 100-150 words (hard cap — count before rendering)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Sign-off
- "Best," — professional, not stiff (default)
- "Thanks," — warmer, peer-to-peer (use when tone is more casual)
- Never: "Sincerely," "Regards," "Respectfully," — too formal for cold outreach

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

## LinkedIn Message Variants

When the user says "LinkedIn message", "LinkedIn outreach", "connection request",
"InMail", or "DM on LinkedIn", produce the appropriate LinkedIn variant instead of
(or alongside) the email. Same research pipeline applies — same hook and achievement
selection logic. Different constraints on format, length, and tone.

### Variant A — Connection Request Note (≤ 300 characters hard limit)

LinkedIn enforces a 300-character cap on connection request notes. Every character counts.
No subject line. No sign-off. No links. Pure text.

**Template skeleton:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TYPE     │ LinkedIn Connection Request Note
CHAR CAP │ 300 (hard limit enforced by LinkedIn — draft to ≤ 280 for safety)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hi [First Name],

▸ HOOK [1 sentence, ≤ 100 chars]
  Something specific — their recent post, talk, company initiative, or shared context.

▸ BRIDGE [1 sentence, ≤ 100 chars]
  One line on your most relevant signal for them — role, metric, or shared background.

▸ SOFT ASK [1 sentence, ≤ 80 chars]
  "Would love to connect." or "Happy to share more if useful."
  Never ask for a call in a connection note — too much friction before they've accepted.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CHAR BUDGET │ Hook ≤100 · Bridge ≤100 · Ask ≤80 · TOTAL ≤ 280
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

After drafting, always show the character count: `[N]/300 characters`.

**Example (filled):**
```
Hi Priya,

Saw your post on Razorpay's checkout latency work — that's exactly the problem I
spent 18 months on at [Company], cutting p95 from 800ms to 140ms.

Would love to connect.

[Name]
```
→ 196 characters. Clean, specific, leaves room.

**Banned from connection notes:**
- "I came across your profile on LinkedIn" (every note starts this way — instant generic signal)
- "I am looking for new opportunities" (makes it about you, not them)
- Links of any kind (LinkedIn strips them from notes)
- Multiple asks
- "Please accept my request" (desperate)

---

### Variant B — LinkedIn DM / InMail (after connected, or with InMail credit)

More room than a connection note, but still tighter than email. Casual, peer-to-peer.
No formal subject line shown to recipient (InMail has a subject field — treat it like
the email subject but can be slightly longer: up to 15 words).

**Template skeleton:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TYPE      │ LinkedIn DM or InMail
SUBJECT   │ [InMail only — ≤ 15 words, same formula as email subject]
WORD CAP  │ 150-200 words (DM) / 200-300 words (InMail — still keep it tight)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hi [First Name],

▸ HOOK        [≤ 30 words]
              Same rule as email: must be specific, not swappable with another company.

▸ ACHIEVEMENT [≤ 40 words]
              One metric-backed win. Tighter than email — no "that maps directly to"
              filler. Let the metric speak: "At [Co], I [did X] → [metric result]."

▸ ASK         [≤ 20 words]
              Same as email. "Would you have 15 minutes?" works here too.
              Can add: "Happy to send my resume/portfolio if useful."

[First name only — no formal sign-off on LinkedIn DMs]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WORD BUDGET │ Hook ≤30 · Achievement ≤40 · Ask ≤20 · TOTAL ≤ 200
NO PS LINE  │ PS lines don't render well in LinkedIn DMs — skip it
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Sign-off:** First name only. "Priya" not "Best, Priya Sharma".
LinkedIn is casual — a formal sign-off reads wrong.

**Banned from LinkedIn DMs (additional to the shared list below):**
- "I noticed you viewed my profile" (even if true — sounds surveillance-y)
- "I came across your profile on LinkedIn" (everyone says this)
- "I thought I'd reach out" (filler — just reach out)
- "I would love to be considered for any opportunities" (too passive, makes them do the work)
- Emoji in the first sentence (one at the end of the message is fine if tone is casual)

---

### Shared Humanizer Rules (apply to all LinkedIn variants)

In addition to the email humanizer rules:
- LinkedIn tone is 10% more casual than email. Contractions are fine ("I've", "you're").
- No formal salutation ("Dear [Name]" — never on LinkedIn)
- No closing pleasantries ("Looking forward to connecting!", "Have a great day!")
- Keep sentences under 12 words — LinkedIn is read on mobile; long sentences get skipped

---

### LinkedIn Rendering in Chat

For **connection request notes**, render as a LinkedIn-style card:

```html
<div style="font-family: -apple-system, 'Segoe UI', sans-serif; max-width: 500px;
  border: 1px solid #d0d7de; border-radius: 8px; overflow: hidden;">
  <div style="background: #0a66c2; padding: 10px 16px; display: flex;
    align-items: center; gap: 10px;">
    <span style="color: white; font-weight: 700; font-size: 15px;">in</span>
    <span style="color: white; font-size: 13px; opacity: 0.9;">Connection Request</span>
  </div>
  <div style="padding: 16px; background: white;">
    <div style="font-size: 12px; color: #666; margin-bottom: 10px;">
      To: [Recruiter Name] · [Title] at [Company]
    </div>
    <div style="font-size: 14px; line-height: 1.6; color: #1a1a1a; white-space: pre-wrap;">
      [NOTE TEXT]
    </div>
  </div>
  <div style="background: #f3f2ef; border-top: 1px solid #d0d7de; padding: 8px 16px;
    font-size: 11px; color: #888;">
    [N]/300 characters
  </div>
</div>
```

For **DMs/InMail**, render as a LinkedIn message thread bubble:

```html
<div style="font-family: -apple-system, 'Segoe UI', sans-serif; max-width: 540px;
  border: 1px solid #d0d7de; border-radius: 8px; overflow: hidden;">
  <div style="background: #0a66c2; padding: 10px 16px; display: flex;
    align-items: center; gap: 10px;">
    <span style="color: white; font-weight: 700; font-size: 15px;">in</span>
    <span style="color: white; font-size: 13px; opacity: 0.9;">
      [DM / InMail] · [Recruiter Name]
    </span>
  </div>
  [InMail only — show subject line bar]
  <div style="background: #f3f2ef; padding: 8px 16px; font-size: 12px;
    color: #555; border-bottom: 1px solid #d0d7de;">
    Subject: [SUBJECT]
  </div>
  <div style="padding: 16px; background: white;">
    <div style="background: #dce6f1; border-radius: 12px 12px 2px 12px;
      padding: 12px 14px; font-size: 14px; line-height: 1.65;
      color: #1a1a1a; white-space: pre-wrap; display: inline-block; max-width: 90%;">
      [MESSAGE TEXT]
    </div>
  </div>
  <div style="background: #f3f2ef; border-top: 1px solid #d0d7de; padding: 8px 16px;
    font-size: 11px; color: #888;">
    [N] words · Generated [date]
  </div>
</div>
```

After rendering any LinkedIn variant, add in regular text:
```
[Connection note: N/300 chars | DM: N words]
To persist: say "save this outreach"
To revise: say "make it more casual" / "tighten the hook" / "different achievement"
Want the email version too? Say "also draft the email"
```

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
Want a LinkedIn version? Say "also draft LinkedIn message" or "connection request version"
```

**Note:** LinkedIn rendering is handled in the LinkedIn Message Variants section above.
When both email and LinkedIn are requested in the same session, render them sequentially —
email card first, LinkedIn card second — so the user can compare tone.

---

## Sending — Handoff to Gmail

This skill drafts; it never sends. When the user says `send this`, `draft this in
gmail`, or `put this in my drafts`, hand off to `skills/gmail-tracker/SKILL.md`.

That skill will confirm the recipient and the full body before creating a **draft**
in Gmail. Nothing is ever sent by Claude — the user reviews and sends from Gmail.
If Gmail isn't connected, gmail-tracker says so once; don't invent a fallback.

If `integrations.slack.enabled` is true and `outreach_drafted` is in `notify_on`,
also post the draft to Slack for approval-at-a-distance — subject and hook in the
message, full body in a thread reply.

---

## Persistence

By default: **show only in chat, don't save.**

If the user says "save this", "keep this", or "persist this outreach":

1. Save to `data/outreach/[Company]_[RecruiterFirstName or "recruiter"]_[YYYY-MM-DD].md`:

```markdown
# Cold Outreach — [Company] / [Role] / [Recruiter Name]
_Drafted: [date] | Resume version: [folder name] | Status: drafted_

## Cold Email

**Subject:** [subject line]

[full email text including PS]

---

## LinkedIn Connection Request Note
_[N]/300 characters_

[note text]

---

## LinkedIn DM / InMail
_[InMail subject if applicable]_

[message text]

---

## Intel Used
- Company intel: [yes/no — data/market/company-intel/[slug].md, date if exists]
- Role portrait: [yes/no — data/market/role-portraits/[slug].md, date if exists]
- Recruiter research: [what was found: name, title, profile source / "none"]
- Targeted resume: [resumes/[folder]/resume.md]

## Notes
[Anything relevant: when to send, which variant performed, follow-up sent date]
```

Omit any section (Email / Connection Note / DM) that wasn't drafted in this session —
don't save empty placeholders.

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
| `also draft LinkedIn message` | Draft both connection note (≤280 chars) AND DM version |
| `connection request version` | Draft just the ≤280-character connection note |
| `LinkedIn DM version` | Draft the longer DM/InMail variant (~150-200 words) |
| `tighten the hook` | Rewrite hook only — keep rest of email/message intact |
| `different achievement` | Swap to the next strongest achievement from targeted resume |

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

### Cold Email
Before rendering, verify:
- [ ] Body is 100-150 words (hard limit — count before rendering)
- [ ] Hook is specific: could NOT appear in an email to a different company or recruiter
- [ ] Achievement has a concrete metric — no vague claims ("improved performance")
- [ ] Ask is explicit: one specific action, named format and timeframe
- [ ] No banned phrases survived the humanizer pass
- [ ] Subject line is ≤10 words, uses one of the formulas
- [ ] PS (if included) adds a distinct secondary hook — not a repeat of the body
- [ ] Sign-off is "Best," or "Thanks," — not "Sincerely" or "Regards"
- [ ] Reads at a 7th-grade level — clear, direct, no corporate vocabulary

### LinkedIn Connection Request Note
- [ ] ≤ 280 characters (show count — LinkedIn cap is 300, draft to 280 for safety)
- [ ] Hook is specific: could not be copy-pasted to someone else at the same company
- [ ] No links (LinkedIn strips them from connection notes)
- [ ] Soft ask only — do NOT ask for a call in a connection note
- [ ] Does NOT open with "I came across your profile on LinkedIn"

### LinkedIn DM / InMail
- [ ] ≤ 200 words (DM) / ≤ 300 words (InMail)
- [ ] Same hook specificity rule as email
- [ ] No formal sign-off — first name only
- [ ] InMail subject line present if drafting InMail (≤15 words)
- [ ] No PS line (doesn't render well in LinkedIn UI)
- [ ] Does NOT open with "I noticed you viewed my profile" or "I came across your profile"
