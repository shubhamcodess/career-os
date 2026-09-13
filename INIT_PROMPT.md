# Career OS — Init Prompt

Paste this as your FIRST message after opening Career OS in Claude.

---

I've just cloned Career OS. Read `skills/setup/SKILL.md` and run the guided setup with me.

Work through it one phase at a time — verify each before moving to the next, and tell me
what actually worked rather than assuming. Specifically:

1. **Config files** — create `config/user.json` and `.env` from the examples if they're
   missing. Don't overwrite anything that already exists. Ask me for `PERSONALIZE`.

2. **My profile and targets** — ask me for my name, email, location, LinkedIn, GitHub,
   target roles, target locations and years of experience. For companies, just take
   **names** — you work out the rest.

3. **Company registry** — run `resolve-ats.py --from-config`, then
   `careers-probe.py --all-unreachable --apply` to recover anything it missed. Show me
   the result by status and tell me which companies still need a careers URL. Flag
   anything marked LOW CONFIDENCE so I can verify it.

4. **Connectors** — check what's already connected, then **render the one-click install
   cards** for whatever is missing (Dice, Indeed, ZipRecruiter, Gmail, Slack). Don't
   send me into a settings menu, and don't tell me to edit `mcp/.mcp.json`.

5. **Optional extras** — ask whether I want Naukri (India job board), Slack
   notifications, Gmail outreach drafting, a GitHub token, and a private vault repo for
   backups. Any of these can be skipped.

6. **Budgets** — show me the Indeed/ZipRecruiter caps and explain why they exist.

7. **Verify** — `npm install`, then report real numbers: how many companies are
   fetchable, how many jobs are reachable, which connectors are live, and what's still
   open. Finish with the single next action.

If anything fails, tell me exactly what and why — don't report success you haven't
verified, and don't invent values for anything you should be asking me about.
