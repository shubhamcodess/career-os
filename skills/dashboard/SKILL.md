---
name: dashboard
description: >
  Renders the Career OS help screen or status dashboard as an interactive widget.
  Triggered by: help, /help, status, /status, "show dashboard", "what can you do",
  "what commands are available", "show commands", "show me the commands".
---

# Dashboard Skill

When the user asks for `help`, `status`, or any dashboard-style command — render an
interactive widget using `show_widget`. **Never output plain ASCII text for these commands.**

---

## When to Invoke

| Trigger | Notes |
|---|---|
| `help`, `/help`, `show commands`, `what can you do` | Same widget — help + status combined |
| `status`, `/status`, `show dashboard`, `show status` | Same widget — help + status combined |

Both triggers use the same single widget. There is no "help mode" vs "status mode" —
everything lives in one tabbed widget.

---

## Step 1 — Read Live State

Before rendering, read these sources:

| Data | Source |
|---|---|
| Interview status + checkpoint | `checkpoints/interview-state.md` (parse CP-N; missing → NOT STARTED) |
| Master doc size | `data/master-experience.md` (line count; missing → empty) |
| Resume count | `ls resumes/` (count dirs, exclude .gitkeep) |
| Latest resume name | most recent `[Co]_[Role]_[date]_vN` dir by date |
| Job feed status | `data/market/job-feed.md` frontmatter date; missing → "Never run" |
| Last commit | `git log -1 --format="%s"` |
| Setup checks | read `.env` keys, `config/user.json` exists, `node_modules/` exists, `exports/test-render.pdf` exists |
| Vault sync date | `git -C .personal-worktree log -1 --format="%ar" 2>/dev/null` or "never" |
| Outreach files | `ls data/outreach/*.md 2>/dev/null | wc -l` |

Derive dot classes for the state bar:
- `dot-y` (yellow) — in progress / partial
- `dot-g` (green) — complete / has content
- `dot-n` (neutral gray) — never run / 0 / missing

Derive next action (pick first that applies):
1. interview-state.md missing or empty → `begin intake interview` / "No intake data yet — start here."
2. Interview IN PROGRESS → `resume interview` / "Phase N deep-dive next. N phases remaining."
3. Interview COMPLETE, 0 resumes → `make resume for [Company/Role]` / "Intake done — paste a JD to generate your first resume."
4. Resumes exist, job feed never run → `find jobs` / "Pipeline ready — pull live listings."
5. All data fresh → `refresh job feed` / "Keep the job feed current."

---

## Step 2 — Call show_widget

**loading_messages**: `["Reading live state…", "Wiring up commands…", "Almost there…"]`
**title**: `career_os_help`

Substitute all `{{PLACEHOLDER}}` values with live data. Remove all `{{PLACEHOLDER}}` tokens.

```html
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--font-mono);font-size:12px;color:var(--text-primary);line-height:1.5}
.w{border:0.5px solid var(--border);border-radius:8px;overflow:hidden;background:var(--surface-1)}
.hdr{display:flex;align-items:center;justify-content:space-between;padding:7px 12px;background:var(--surface-2);border-bottom:0.5px solid var(--border)}
.hdr-l{display:flex;align-items:center;gap:10px}
.title{font-size:12px;font-weight:500;color:var(--text-primary)}
.title .sep{color:var(--border-strong);margin:0 3px}
.title .sub{font-weight:400;color:var(--text-muted)}
.mode-pill{font-size:10px;color:var(--text-muted);border:0.5px solid var(--border);border-radius:3px;padding:1px 6px}
.state-bar{display:flex;align-items:stretch;border-bottom:0.5px solid var(--border)}
.sc{flex:1;padding:7px 12px;border-right:0.5px solid var(--border)}
.sc:last-child{border-right:none}
.sk{font-size:10px;color:var(--text-muted);letter-spacing:.4px;margin-bottom:2px}
.sv{font-size:11px;color:var(--text-secondary);display:flex;align-items:center;gap:5px}
.dot{width:5px;height:5px;border-radius:50%;flex-shrink:0;opacity:.8}
.dot-y{background:#c9993a}
.dot-g{background:#4a9e5c}
.dot-n{background:var(--border-strong)}
.next{display:flex;align-items:center;gap:8px;padding:7px 12px;border-bottom:0.5px solid var(--border);font-size:11px}
.next-k{color:var(--text-muted);white-space:nowrap}
.next-v{color:var(--text-primary);font-weight:500}
.next-d{color:var(--text-muted)}
.tabs{display:flex;border-bottom:0.5px solid var(--border);background:var(--surface-2);overflow-x:auto;padding:0 6px}
.tab{font-size:11px;color:var(--text-muted);padding:7px 10px;cursor:pointer;border-bottom:1.5px solid transparent;white-space:nowrap;user-select:none}
.tab:hover{color:var(--text-secondary)}
.tab.on{color:var(--text-primary);border-bottom-color:var(--text-primary)}
.panel{display:none}
.panel.on{display:block}
.sg{padding:7px 12px 3px;font-size:10px;letter-spacing:.5px;color:var(--text-muted);margin-top:2px}
.cr{display:flex;align-items:center;padding:4px 12px;gap:6px}
.cr:hover{background:var(--surface-2)}
.cc{color:var(--text-secondary);min-width:195px;flex-shrink:0;font-size:11px}
.cd{color:var(--text-muted);font-size:11px;flex:1;font-family:var(--font-sans)}
.rb{font-family:var(--font-mono);font-size:10px;color:var(--text-muted);background:none;border:0.5px solid var(--border);border-radius:3px;padding:1px 5px;cursor:pointer;white-space:nowrap;flex-shrink:0}
.rb:hover{color:var(--text-primary);border-color:var(--border-strong)}
.pr{display:flex;align-items:center;padding:3px 12px;gap:6px;font-size:11px;color:var(--text-muted)}
.pr.done::before{content:'✓ ';opacity:.5}
.pr.todo::before{content:'○ '}
.pr.todo{color:var(--text-secondary)}
.div{height:0.5px;background:var(--border);margin:5px 0}
.ck-r{display:flex;align-items:flex-start;gap:8px;padding:4px 12px;font-size:11px}
.ck-i{flex-shrink:0;width:14px;color:var(--text-secondary)}
.ck-l{color:var(--text-primary)}
.ck-s{color:var(--text-muted);font-family:var(--font-sans)}
.ft{padding:6px 12px;border-top:0.5px solid var(--border);font-size:10px;color:var(--text-muted);display:flex;align-items:center;gap:6px}
.ft code{color:var(--text-secondary)}
</style>

<div class="w">
<div class="hdr">
  <div class="hdr-l">
    <span class="title">career-os<span class="sep">·</span><span class="sub">personal mode</span></span>
    <span class="mode-pill">PERSONALIZE=true</span>
  </div>
  <span style="font-size:10px;color:var(--text-muted)">v0.1 · SP</span>
</div>

<div class="state-bar">
  <div class="sc"><div class="sk">INTERVIEW</div><div class="sv"><span class="dot {{INTERVIEW_DOT}}"></span>{{INTERVIEW_LABEL}}</div></div>
  <div class="sc"><div class="sk">MASTER DOC</div><div class="sv"><span class="dot {{MASTER_DOT}}"></span>{{MASTER_LABEL}}</div></div>
  <div class="sc"><div class="sk">RESUMES</div><div class="sv"><span class="dot {{RESUME_DOT}}"></span>{{RESUME_LABEL}}</div></div>
  <div class="sc"><div class="sk">JOB FEED</div><div class="sv"><span class="dot {{FEED_DOT}}"></span>{{FEED_LABEL}}</div></div>
</div>

<div class="next">
  <span class="next-k">next →</span>
  <span class="next-v">{{NEXT_CMD}}</span>
  <span class="next-d">{{NEXT_DESC}}</span>
  <button class="rb" style="margin-left:auto" onclick="sendPrompt('{{NEXT_CMD}}')">run ↗</button>
</div>

<div class="tabs" id="tabs">
  <div class="tab on" data-t="intake">intake</div>
  <div class="tab" data-t="resume">resume</div>
  <div class="tab" data-t="jobs">jobs</div>
  <div class="tab" data-t="intel">intel</div>
  <div class="tab" data-t="outreach">outreach</div>
  <div class="tab" data-t="sync">sync</div>
  <div class="tab" data-t="setup">setup</div>
</div>

<!-- INTAKE TAB -->
<div id="intake" class="panel on">
  <div class="sg">INTERVIEW COMMANDS</div>
  <div class="cr"><span class="cc">resume interview</span><span class="cd">Continue from {{CHECKPOINT}} — {{NEXT_PHASE}} next</span><button class="rb" onclick="sendPrompt('resume interview')">run ↗</button></div>
  <div class="cr"><span class="cc">begin intake interview</span><span class="cd">Start the full intake from scratch</span><button class="rb" onclick="sendPrompt('begin intake interview')">run ↗</button></div>
  <div class="cr"><span class="cc">pause interview</span><span class="cd">Save checkpoint and stop</span><button class="rb" onclick="sendPrompt('pause interview')">run ↗</button></div>
  <div class="cr"><span class="cc">show checkpoints</span><span class="cd">Display the checkpoint log</span><button class="rb" onclick="sendPrompt('show checkpoints')">run ↗</button></div>
  <div class="cr"><span class="cc">rewind to [CP-N]</span><span class="cd">Go back to a specific checkpoint</span></div>
  <div class="cr"><span class="cc">update master</span><span class="cd">Re-run intake to update master-experience.md</span><button class="rb" onclick="sendPrompt('update master')">run ↗</button></div>
  <div class="div"></div>
  <div class="sg">PROGRESS · {{CHECKPOINT_LABEL}}</div>
  {{INTAKE_PROGRESS_ROWS}}
</div>

<!-- RESUME TAB -->
<div id="resume" class="panel">
  <div class="sg">GENERATION</div>
  <div class="cr"><span class="cc">make resume for [Co/Role]</span><span class="cd">Full pipeline: intel → tailor → ATS → humanize → PDF → commit</span></div>
  <div class="cr"><span class="cc">make cover letter for [Co/Role]</span><span class="cd">From targeted resume.md + master doc → humanized → PDF</span></div>
  <div class="cr"><span class="cc">jd check</span><span class="cd">Analyze a JD for red/yellow/green flags before applying</span><button class="rb" onclick="sendPrompt('jd check\n')">run ↗</button></div>
  <div class="cr"><span class="cc">ats check</span><span class="cd">Full ATS audit on latest resume</span><button class="rb" onclick="sendPrompt('ats check')">run ↗</button></div>
  <div class="cr"><span class="cc">export pdf</span><span class="cd">Re-export PDF from latest resume.html via Puppeteer</span><button class="rb" onclick="sendPrompt('export pdf')">run ↗</button></div>
  <div class="div"></div>
  <div class="sg">MANAGEMENT</div>
  <div class="cr"><span class="cc">use template [name]</span><span class="cd">Switch active HTML template for next export</span></div>
  <div class="cr"><span class="cc">add template [name]</span><span class="cd">Paste screenshot or URL — recreated as HTML/CSS</span></div>
  <div class="cr"><span class="cc">version log</span><span class="cd">All resume versions, companies, status</span><button class="rb" onclick="sendPrompt('version log')">run ↗</button></div>
  <div class="cr"><span class="cc">diff [company] v1 v2</span><span class="cd">Compare two resume versions</span></div>
</div>

<!-- JOBS TAB -->
<div id="jobs" class="panel">
  <div class="sg">SEARCH</div>
  <div class="cr"><span class="cc">find jobs</span><span class="cd">Aggregate live listings across all sources</span><button class="rb" onclick="sendPrompt('find jobs')">run ↗</button></div>
  <div class="cr"><span class="cc">find jobs at [company]</span><span class="cd">Filter to one specific company</span></div>
  <div class="cr"><span class="cc">refresh job feed</span><span class="cd">Re-run last search, surface new listings</span><button class="rb" onclick="sendPrompt('refresh job feed')">run ↗</button></div>
  <div class="cr"><span class="cc">jd check</span><span class="cd">Paste or link a JD → scored analysis with apply/pass verdict</span><button class="rb" onclick="sendPrompt('jd check\n')">run ↗</button></div>
  <div class="div"></div>
  <div class="sg">TRACKING</div>
  <div class="cr"><span class="cc">job tracker</span><span class="cd">View all applications, status, next action</span><button class="rb" onclick="sendPrompt('job tracker')">run ↗</button></div>
  <div class="div"></div>
  <div class="sg">ACTIVE SOURCES</div>
  <div class="cr"><span class="cc" style="color:var(--text-muted)">ATS Direct</span><span class="cd">Greenhouse + Lever JSON APIs — no auth</span></div>
  <div class="cr"><span class="cc" style="color:var(--text-muted)">Indeed · ZipRecruiter · Dice</span><span class="cd">MCP — free, authless, parallel</span></div>
  <div class="cr"><span class="cc" style="color:var(--text-muted)">Naukri</span><span class="cd">Playwright + system Chrome — Indian market, optional</span></div>
</div>

<!-- INTEL TAB -->
<div id="intel" class="panel">
  <div class="sg">MARKET INTELLIGENCE</div>
  <div class="cr"><span class="cc">profile intel for [company]</span><span class="cd">GitHub org + Firecrawl → who works there, what they know</span></div>
  <div class="cr"><span class="cc">github market map for [role]</span><span class="cd">Public GitHub → what people in this role actually build</span></div>
  <div class="cr"><span class="cc">research comp for [role/co]</span><span class="cd">Market salary, equity ranges, negotiation position</span></div>
  <div class="div"></div>
  <div class="sg">INTERVIEW & PROFILE</div>
  <div class="cr"><span class="cc">prep for [company] interview</span><span class="cd">STAR story matching to JD + mock behavioral Q&amp;A</span></div>
  <div class="cr"><span class="cc">optimize profile for [platform]</span><span class="cd">Naukri / LinkedIn / Instahyre / Wellfound</span></div>
  <div class="cr"><span class="cc">export portfolio brief</span><span class="cd">Generate exports/portfolio-brief.json from master doc</span><button class="rb" onclick="sendPrompt('export portfolio brief')">run ↗</button></div>
</div>

<!-- OUTREACH TAB -->
<div id="outreach" class="panel">
  <div class="sg">EMAIL</div>
  <div class="cr"><span class="cc">draft outreach for [company]</span><span class="cd">Cold email — ONE hook + ONE achievement, 100-150w, humanized, card render</span></div>
  <div class="cr"><span class="cc">cold email to [name] at [co]</span><span class="cd">Personalized to a specific recruiter or hiring manager</span></div>
  <div class="div"></div>
  <div class="sg">LINKEDIN</div>
  <div class="cr"><span class="cc">LinkedIn message to [name]</span><span class="cd">Connection note (≤280 chars) + DM/InMail — both rendered as cards</span></div>
  <div class="cr"><span class="cc">connection request for [co]</span><span class="cd">Just the ≤280-char connection note</span></div>
  <div class="div"></div>
  <div class="sg">AFTER DRAFTING</div>
  <div class="cr"><span class="cc">save this outreach</span><span class="cd">Persist all variants → data/outreach/ → commit → vault sync</span></div>
  <div class="cr"><span class="cc">follow-up version</span><span class="cd">2-sentence follow-up for 7 days after no reply</span></div>
  <div class="cr"><span class="cc">make it shorter</span><span class="cd">Quick iteration without re-running the full research pipeline</span></div>
  <div class="cr"><span class="cc">different hook</span><span class="cd">Try a different personalization angle</span></div>
</div>

<!-- SYNC TAB -->
<div id="sync" class="panel">
  <div class="sg">VAULT BACKUP</div>
  <div class="cr"><span class="cc">backup</span><span class="cd">Sync personal data to career-os-sp with a meaningful commit message</span><button class="rb" onclick="sendPrompt('backup')">run ↗</button></div>
  <div class="div"></div>
  <div class="sg">FRAMEWORK PUSH</div>
  <div class="cr"><span class="cc">git push personal main</span><span class="cd">Push framework commits to career-os-sp (private)</span><button class="rb" onclick="sendPrompt('git push personal main')">run ↗</button></div>
  <div class="cr"><span class="cc">git push origin main</span><span class="cd">Push framework commits to career-os (public)</span><button class="rb" onclick="sendPrompt('git push origin main')">run ↗</button></div>
  <div class="div"></div>
  <div class="sg">DATA FRESHNESS</div>
  <div class="cr"><span class="cc" style="color:var(--text-muted)">master-experience.md</span><span class="cd">{{MASTER_FRESHNESS}}</span></div>
  <div class="cr"><span class="cc" style="color:var(--text-muted)">resumes/</span><span class="cd">{{RESUME_FRESHNESS}}</span></div>
  <div class="cr"><span class="cc" style="color:var(--text-muted)">data/market/job-feed.md</span><span class="cd">{{FEED_FRESHNESS}}</span></div>
  <div class="cr"><span class="cc" style="color:var(--text-muted)">vault last synced</span><span class="cd">{{VAULT_SYNC}}</span></div>
  <div class="cr"><span class="cc" style="color:var(--text-muted)">data/outreach/</span><span class="cd">{{OUTREACH_COUNT}} files · gitignored, backed up to vault</span></div>
</div>

<!-- SETUP TAB -->
<div id="setup" class="panel">
  <div class="sg">SETUP CHECKLIST</div>
  {{SETUP_CHECKLIST_ROWS}}
  <div class="div"></div>
  <div class="sg">SYSTEM</div>
  <div class="cr"><span class="cc">add skill [name]</span><span class="cd">Scaffold a new skill in skills/[name]/SKILL.md</span></div>
  <div class="cr"><span class="cc">add template [name]</span><span class="cd">Save a new resume template</span></div>
  <div class="cr"><span class="cc">help</span><span class="cd">Show this screen</span><button class="rb" onclick="sendPrompt('help')">run ↗</button></div>
</div>

<div class="ft"><i class="ti ti-git-commit" aria-hidden="true"></i> <code>{{LAST_COMMIT}}</code></div>
</div>

<script>
document.getElementById('tabs').addEventListener('click',function(e){
  var t=e.target.closest('.tab');if(!t)return;
  document.querySelectorAll('.tab').forEach(function(x){x.classList.remove('on')});
  document.querySelectorAll('.panel').forEach(function(x){x.classList.remove('on')});
  t.classList.add('on');document.getElementById(t.dataset.t).classList.add('on');
});
</script>
```

---

## Step 3 — Placeholder Reference

| Placeholder | Value |
|---|---|
| `{{INTERVIEW_DOT}}` | `dot-y` / `dot-g` / `dot-n` |
| `{{INTERVIEW_LABEL}}` | e.g. `In progress · CP-01` |
| `{{MASTER_DOT}}` | `dot-y` (partial) / `dot-g` (complete) / `dot-n` (empty) |
| `{{MASTER_LABEL}}` | e.g. `Partial · 312 lines` or `Empty` |
| `{{RESUME_DOT}}` | `dot-g` (>0) / `dot-n` (0) |
| `{{RESUME_LABEL}}` | e.g. `3 generated` or `0 generated` |
| `{{FEED_DOT}}` | `dot-g` (has date) / `dot-n` (never run) |
| `{{FEED_LABEL}}` | e.g. `Last run: 2026-09-10` or `Never run` |
| `{{NEXT_CMD}}` | e.g. `resume interview` |
| `{{NEXT_DESC}}` | e.g. `Phase 1 deep-dive next. 6 phases remaining.` |
| `{{CHECKPOINT}}` | e.g. `CP-01` |
| `{{NEXT_PHASE}}` | e.g. `Phase 1 (Tax Engine)` |
| `{{CHECKPOINT_LABEL}}` | e.g. `CP-01 COMPLETE` or `NOT STARTED` |
| `{{INTAKE_PROGRESS_ROWS}}` | `.pr.done` / `.pr.todo` rows — one per phase, derived from interview-state.md |
| `{{MASTER_FRESHNESS}}` | e.g. `312 lines · intake in progress at CP-01` |
| `{{RESUME_FRESHNESS}}` | e.g. `0 generated — complete intake first` |
| `{{FEED_FRESHNESS}}` | e.g. `Never run` or `34 listings · last run: 2026-09-10` |
| `{{VAULT_SYNC}}` | e.g. `2 days ago` or `never` |
| `{{OUTREACH_COUNT}}` | integer |
| `{{SETUP_CHECKLIST_ROWS}}` | `.ck-r` rows — 9 items, each ✓ / ⚠ / ○ based on live checks |
| `{{LAST_COMMIT}}` | output of `git log -1 --format="%s"` |

### Setup checklist row template

Use `✓` for passing, `⚠` (with `style="color:#c9993a"`) for partial/warning, `○` (with `style="color:var(--text-muted)"`) for not done:

```html
<div class="ck-r"><span class="ck-i">✓</span><div><div class="ck-l">PERSONALIZE=true in .env</div></div></div>
<div class="ck-r"><span class="ck-i" style="color:#c9993a">⚠</span><div><div class="ck-l">master-experience.md has content</div><div class="ck-s">Partial — 312 lines. Complete intake to fill it.</div></div></div>
<div class="ck-r"><span class="ck-i" style="color:var(--text-muted)">○</span><div><div class="ck-l">At least one resume generated</div><div class="ck-s">Complete the intake first, then: make resume for [Company/Role]</div></div></div>
```

### Intake progress row template

```html
<div class="pr done">Career arc — IBM → IKEA, 6yr, 6 project phases identified</div>
<div class="pr todo">Phase deep-dives — Tax Engine, CBD O3S, STOC O3S, RIMS O3S, IV4INGKA, OFM</div>
```

---

## Notes

- Call `show_widget` — never output plain ASCII for help/status.
- After the widget, output nothing (or at most one sentence).
- If any file read fails, use graceful defaults: `—` for missing values, `dot-n` for missing data.
- In Framework mode (`PERSONALIZE=false`): set all state cells to `dot-n` / `—`. Skip personal data rows in the sync tab.
- The `run ↗` buttons use `sendPrompt()` only for commands that need no parameters. Commands requiring `[Company]`, `[name]`, etc. have no run button.
