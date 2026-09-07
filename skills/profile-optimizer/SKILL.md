---
name: profile-optimizer
description: >
  Invoke when user says "optimize profile for [platform]", "fix my Naukri", "update LinkedIn",
  "optimize my Instahyre profile", or any request to improve their presence on a job platform.
  Covers Naukri, LinkedIn, Instahyre, Cutshort, Wellfound/AngelList, and Dice.
  Always reads master-experience.md first to ground all optimizations in real data.
---

# Profile Optimizer Skill

Optimizes job platform profiles for maximum recruiter visibility and inbound interest.
Each platform has a different ranking algorithm — this skill handles each specifically.

## Before Any Platform Optimization

1. Read `data/master-experience.md` — all optimization must reflect real experience
2. Ask the user to paste their current profile content (headline, summary, skills, etc.)
   OR paste the profile URL so it can be fetched
3. Ask what roles/companies they are targeting — optimization is keyword-driven and
   target-dependent

---

## Naukri

Naukri's search algorithm heavily weights: Headline > Key Skills > Role Titles > Summary.
Inbound recruiter searches are keyword-exact. Optimize for search first, readability second.

### Headline (most important field)
- Max ~80 characters displayed; ~120 stored
- Format: `[Role Title] | [Key Skill 1] | [Key Skill 2] | [X] Years Exp`
- Use exact terms recruiters search: "Product Manager" not "PM"; "React.js" not "React"
- Include seniority: "Senior", "Lead", "Principal" if applicable
- Example: `Senior Product Manager | SaaS | Fintech | 6 Years | 0-1 Products`

### Profile Summary
- First 3 lines visible before "Read more" — hook immediately
- Open with: who you are + domain + years + type of companies
- Follow with: top 2-3 achievements with numbers
- Close with: what you're looking for (helps recruiter qualify you)
- 150-250 words. No generic phrases ("hardworking", "team player").

### Key Skills Section
- 15-30 skills. Naukri shows top skills in search results.
- Add both: broad terms AND specific terms ("Product Management" AND "Roadmap Planning")
- Add tools recruiters search for your domain: JIRA, Figma, SQL, Mixpanel, etc.
- Add domain keywords: Fintech, SaaS, B2B, Consumer, etc.

### Role Descriptions
- Each role needs keywords in the description text — not just title
- Start each role description with a one-line context: team size, product type, users
- 3-5 bullet points per role in Naukri format

### Other Fields to Complete
- Notice Period: keep updated — recruiters filter by this
- Expected CTC: research market first; don't undersell
- Preferred Locations: be specific
- Industry: select the right one — affects search ranking
- Profile completeness: aim for 100% — incomplete profiles rank lower

---

## LinkedIn

LinkedIn's algorithm (2026) weights: Headline > Connection degree > Activity > Skills endorsements.
Recruiter search (LinkedIn Recruiter) filters by: title, skills, location, company, seniority.

### Headline (150 chars)
- Must contain: current/target role + 1-2 skills + value prop
- Avoid: "Open to work" in headline — use the frame instead
- Formula: `[Role] at [Company type] | [Skill 1] + [Skill 2] | [What you build/drive]`
- Example: `Senior PM @ High-Growth Startups | 0-to-1 Products | Fintech & Consumer`

### About Section
- Line 1-3: visible before "see more" — make them count
- Tell a story: what you do → what you've built → what impact you've had → what's next
- Include 3-4 keywords naturally in the text (LinkedIn's algorithm reads this)
- End with a soft CTA: "Open to PM roles at product-first companies — feel free to connect"
- 200-300 words. First person. Sounds like a human wrote it.

### Experience Bullets
- Slightly more narrative than a resume — you have more space
- Still lead with achievement, not responsibility
- Include hyperlinks to products/apps if public
- Add media: screenshots, decks, links (boosts profile completeness and engagement)

### Skills Section
- Top 3 appear on your profile card — choose your most searchable skills
- Get endorsements for top skills — ask colleagues
- Keep skills relevant: remove outdated or irrelevant ones

### Featured Section
- Pin: a strong project write-up, a viral post, your portfolio site, or a case study
- This is the first thing visitors see after the header

### Open to Work
- Enable for recruiters only (not visible to public / your company)
- Set exact role titles — use the same terms as JDs you're targeting
- Set correct seniority, location preferences (include remote)
- Keep it updated

---

## Instahyre

Instahyre is used by high-quality product startups and tech companies in India.
Algorithm weights: skills match > experience at known companies > headline > profile completion.

### Key Differences from Naukri
- Quality over quantity — Instahyre surfaces fewer but better candidates
- Company brand matters: name-drop well-known companies and products you've worked with
- Tech-forward: even for PM/non-engineering roles, list technical skills you have
- Keep profile concise and sharp — recruiters here scan faster

### Optimization Focus
- Headline: shorter, cleaner, more specific than Naukri
- Highlight: product names, user scale, company names
- Skills: prioritize depth over breadth
- Link GitHub/portfolio if available

---

## Wellfound / AngelList

Used primarily by funded startups (Series A–C) and early-stage companies.

### Key Differences
- Investors and founders browse too — not just recruiters
- Equity interest field: fill it in honestly
- "What you're looking for" section: be specific about stage (early, growth)
- Highlight: 0-to-1 experience, generalist capability, ownership mentality
- Keep tone: direct, ambitious, not corporate

---

## Cutshort

Similar to Instahyre. Focuses on tech roles. Algorithm weights profile completeness highly.
- Complete every section — Cutshort penalizes incomplete profiles in search ranking
- Add certifications, courses, and side projects — they count here
- Skills assessment scores boost visibility if you take them

---

## Output Format

For each platform optimization, produce:

1. **Optimized Headline** — ready to paste
2. **Optimized Summary/About** — ready to paste
3. **Key Skills List** — ready to paste
4. **Gaps / Missing Sections** — what to add
5. **Keyword Additions** — 5-10 keywords not currently in profile that should be
6. **Profile Score Estimate** — rough assessment before and after changes

Save the optimized content to `data/profile-[platform].md` and commit.
