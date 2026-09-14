---
name: dashboard
description: >
  Two separate widgets. `help` is instant and static: every skill and command, grouped
  into tabs, with no state reading. `status` pulls live state (interview, master doc,
  resumes, job store, registry, profiles, connectors, budgets, backup, setup) with one
  script call and renders it.
  Triggered by: help, /help, "show commands", "what can you do", "what commands are
  available" → help. status, /status, "show dashboard", "show status", "where am I" → status.
---

# Dashboard Skill

Two commands, two widgets. Never plain ASCII for either.

| Trigger | Widget | Cost |
|---|---|---|
| `help`, `/help`, `show commands`, `what can you do` | **Help**: static command + skill reference | One file read, no state |
| `status`, `/status`, `show dashboard`, `show status`, `where am I` | **Status**: live progress | One script + one connector call |

---

## `help` — fast path

Do exactly this, nothing else:

1. `Read` `skills/dashboard/help.html`.
2. Call `show_widget` with its contents **verbatim**:
   - `title`: `career_os_help`
   - `loading_messages`: `["Laying out commands…"]`
3. No text after the widget, or at most one sentence.

Do **not** read `.env`, config, checkpoints, the job store, git or connectors for help,
and don't substitute anything. The page is static on purpose, which is what makes it
fast. It points at `status` for live state.

**Keeping help complete:** when a skill or command is added, renamed or removed, update
`help.html` in the same commit: the command in its tab, and the skill in the
**all skills** tab. The Command Reference in `CLAUDE.md` is the source of truth. Only
commands that need no parameters get a `run ↗` button.

---

## `status` — live path

### Step 1: Gather, in parallel

```bash
python3 scripts/status.py
```

Read-only and local, it returns JSON with:
- `env`: which keys are set, never their values
- `config`
- `interview`
- `master_doc`, `star_stories`, `job_tracker`
- `resumes`
- `job_store`: counts by status, last run day, feed counts, Google applications in 30 days
- `registry`: fetchable, careers recipes, unreachable, low confidence
- `budgets`
- `profiles`: LinkedIn/Naukri `last_synced`, content files
- `outreach_files`
- `setup`
- `git`: last commit, unpushed public commits, vault sync age

At the same time, call `session_connectors_status` for live connector state. Never
infer connectors from `mcp/.mcp.json`.

### Step 2: Derive

**Dots:** `dot-g` done / healthy, `dot-y` partial or needs attention, `dot-n` never run / missing.

**Next action** (first that applies):
1. `config.exists` false, 0 target companies, or registry not built → `setup`
2. Interview not COMPLETE → `resume interview` (or `begin intake interview` if 0 checkpoints)
3. No job store runs → `find jobs`
4. Last run day before today → `find jobs` ("last fetched N days ago")
5. `job_store.by_status.new` > 0 → `show current feed` ("N undecided jobs")
6. Shortlist (interested + saved + pinned) > 0 and 0 resumes → `make resume for [top shortlisted role]`
7. LinkedIn or Naukri never synced → `polish my naukri` / `polish my linkedin`
8. Otherwise → `what should I post`

**Attention items** (list only those that are true, max 5):
- low-confidence boards
- unreachable companies count
- budget at ≥ 80% of cap
- a job connector not connected
- unpushed public commits
- vault synced more than 3 days ago
- LinkedIn/Naukri `last_synced` more than 30 days ago
- Google applications at 3/3
- setup checklist items open

### Step 3: Render

`show_widget` with `title: career_os_status`, `loading_messages: ["Reading live state…"]`.
Fill every `{{PLACEHOLDER}}` and leave none in the output. Use `—` for missing values.

```html
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--font-mono);font-size:12px;color:var(--text-primary);line-height:1.5}
.w{border:0.5px solid var(--border);border-radius:8px;overflow:hidden;background:var(--surface-1)}
.hdr{display:flex;align-items:center;justify-content:space-between;padding:7px 12px;background:var(--surface-2);border-bottom:0.5px solid var(--border)}
.title{font-size:12px;font-weight:500}.title .sub{font-weight:400;color:var(--text-muted)}
.hint{font-size:10px;color:var(--text-muted)}
.bar{display:flex;flex-wrap:wrap;border-bottom:0.5px solid var(--border)}
.sc{flex:1;min-width:130px;padding:7px 12px;border-right:0.5px solid var(--border)}
.sc:last-child{border-right:none}
.sk{font-size:10px;color:var(--text-muted);letter-spacing:.4px;margin-bottom:2px}
.sv{font-size:11px;color:var(--text-secondary);display:flex;align-items:center;gap:5px}
.dot{width:6px;height:6px;border-radius:50%;flex-shrink:0}
.dot-y{background:#c9993a}.dot-g{background:#4a9e5c}.dot-n{background:var(--border-strong)}
.next{display:flex;align-items:center;gap:8px;padding:7px 12px;border-bottom:0.5px solid var(--border);font-size:11px}
.next-k{color:var(--text-muted)}.next-v{font-weight:500}.next-d{color:var(--text-muted);font-family:var(--font-sans)}
.rb{font-family:var(--font-mono);font-size:10px;color:var(--text-muted);background:none;border:0.5px solid var(--border);border-radius:3px;padding:1px 5px;cursor:pointer;margin-left:auto}
.rb:hover{color:var(--text-primary);border-color:var(--border-strong)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr))}
.card{padding:8px 12px;border-bottom:0.5px solid var(--border);border-right:0.5px solid var(--border)}
.ch{font-size:10px;letter-spacing:.5px;color:var(--text-muted);margin-bottom:4px}
.row{display:flex;justify-content:space-between;gap:8px;font-size:11px;padding:1px 0}
.row .k{color:var(--text-muted);font-family:var(--font-sans)}.row .v{color:var(--text-secondary);text-align:right}
.att{padding:6px 12px;border-bottom:0.5px solid var(--border);font-size:11px;font-family:var(--font-sans);color:var(--text-secondary)}
.att div::before{content:'⚠ ';color:#c9993a}
.ft{padding:6px 12px;font-size:10px;color:var(--text-muted)}
</style>

<div class="w">
<div class="hdr"><span class="title">career-os <span class="sub">· status · {{GENERATED}}</span></span><span class="hint">type <b>help</b> for all commands</span></div>

<div class="bar">
  <div class="sc"><div class="sk">INTERVIEW</div><div class="sv"><span class="dot {{INTERVIEW_DOT}}"></span>{{INTERVIEW_LABEL}}</div></div>
  <div class="sc"><div class="sk">MASTER DOC</div><div class="sv"><span class="dot {{MASTER_DOT}}"></span>{{MASTER_LABEL}}</div></div>
  <div class="sc"><div class="sk">RESUMES</div><div class="sv"><span class="dot {{RESUME_DOT}}"></span>{{RESUME_LABEL}}</div></div>
  <div class="sc"><div class="sk">JOBS</div><div class="sv"><span class="dot {{JOBS_DOT}}"></span>{{JOBS_LABEL}}</div></div>
  <div class="sc"><div class="sk">PROFILES</div><div class="sv"><span class="dot {{PROFILES_DOT}}"></span>{{PROFILES_LABEL}}</div></div>
</div>

<div class="next"><span class="next-k">next →</span><span class="next-v">{{NEXT_CMD}}</span><span class="next-d">{{NEXT_DESC}}</span><button class="rb" onclick="sendPrompt('{{NEXT_CMD}}')">run ↗</button></div>

{{ATTENTION_BLOCK}}

<div class="grid">
  <div class="card"><div class="ch">JOB SEARCH</div>
    <div class="row"><span class="k">last fetched</span><span class="v">{{LAST_RUN_DAY}}</span></div>
    <div class="row"><span class="k">in store</span><span class="v">{{STORE_TOTAL}}</span></div>
    <div class="row"><span class="k">undecided (new / shown)</span><span class="v">{{NEW}} / {{SHOWN}}</span></div>
    <div class="row"><span class="k">shortlist (interested·saved·pinned)</span><span class="v">{{SHORTLIST}}</span></div>
    <div class="row"><span class="k">applied</span><span class="v">{{APPLIED}}</span></div>
    <div class="row"><span class="k">stale / expired</span><span class="v">{{STALE}} / {{EXPIRED}}</span></div>
    <div class="row"><span class="k">last feed</span><span class="v">{{FEED_TARGETED}} targeted · {{FEED_DISCOVERY}} discovery</span></div>
  </div>
  <div class="card"><div class="ch">COMPANIES</div>
    <div class="row"><span class="k">targets</span><span class="v">{{TARGETS}}</span></div>
    <div class="row"><span class="k">job boards reachable</span><span class="v">{{FETCHABLE}} / {{REGISTRY_TOTAL}}</span></div>
    <div class="row"><span class="k">careers-page recipes</span><span class="v">{{RECIPES}}</span></div>
    <div class="row"><span class="k">unreachable</span><span class="v">{{UNREACHABLE}}</span></div>
    <div class="row"><span class="k">Naukri</span><span class="v">{{NAUKRI_STATE}}</span></div>
  </div>
  <div class="card"><div class="ch">PROFILES &amp; CONTENT</div>
    <div class="row"><span class="k">LinkedIn synced</span><span class="v">{{LINKEDIN_SYNCED}}</span></div>
    <div class="row"><span class="k">Naukri synced</span><span class="v">{{NAUKRI_SYNCED}}</span></div>
    <div class="row"><span class="k">story bank / calendar</span><span class="v">{{CONTENT_STATE}}</span></div>
    <div class="row"><span class="k">outreach drafts</span><span class="v">{{OUTREACH_COUNT}}</span></div>
    <div class="row"><span class="k">Google apps (30 days)</span><span class="v">{{GOOGLE_APPS}} / 3</span></div>
  </div>
  <div class="card"><div class="ch">CONNECTORS &amp; BUDGETS</div>
    {{CONNECTOR_ROWS}}
    {{BUDGET_ROWS}}
  </div>
  <div class="card"><div class="ch">BACKUP &amp; GIT</div>
    <div class="row"><span class="k">vault synced</span><span class="v">{{VAULT_SYNC}}</span></div>
    <div class="row"><span class="k">unpushed public commits</span><span class="v">{{UNPUSHED}}</span></div>
    <div class="row"><span class="k">last commit</span><span class="v">{{LAST_COMMIT}}</span></div>
  </div>
  <div class="card"><div class="ch">SETUP</div>
    {{SETUP_ROWS}}
  </div>
</div>
<div class="ft">read-only snapshot · nothing was fetched</div>
</div>
```

### Placeholder notes

| Placeholder | From |
|---|---|
| `{{GENERATED}}` | `generated` |
| `{{INTERVIEW_LABEL}}` | `interview.status` + `· CP-N` (last checkpoint id) |
| `{{MASTER_LABEL}}` | `master_doc.lines` lines · updated date, or `Empty` |
| `{{RESUME_LABEL}}` | `resumes.count` generated, latest name shortened |
| `{{JOBS_LABEL}}` | `N undecided · last run DAY` |
| `{{PROFILES_LABEL}}` | e.g. `LinkedIn ✓ · Naukri —`; `dot-y` if either is missing or older than 30 days |
| `{{SHORTLIST}}` | interested + saved + pinned |
| `{{UNREACHABLE}}` | count, then the first 4 names |
| `{{ATTENTION_BLOCK}}` | `<div class="att"><div>item</div>…</div>`, or empty string if nothing needs attention |
| `{{CONNECTOR_ROWS}}` | one `.row` per job/comms connector: `✓ connected` / `○ not connected — what's off` |
| `{{BUDGET_ROWS}}` | one `.row` per budget: `3/60 today` or `unmetered` |
| `{{SETUP_ROWS}}` | `.row`s with `✓` / `○`: PERSONALIZE, private repo URL, GitHub token, config, playwright, node_modules, PDF export tested |

---

## Notes

- After either widget, output nothing, or at most one sentence. For `status`, if setup is
  incomplete, that sentence says so and points at `setup`; a dashboard full of zeroes
  otherwise reads as "no jobs out there".
- Connect requests from either widget → `mcp__mcp-registry__suggest_connectors` install
  cards (UUIDs in `skills/setup/SKILL.md`). Never tell the user to edit `mcp/.mcp.json`.
- There is no push button on either widget. Pushing to the public repo and syncing the
  vault follow the git rules in `CLAUDE.md` (`scripts/sync-vault.sh` only for the vault).
- Framework mode (`PERSONALIZE=false`): `help` is unchanged. `status` shows only setup,
  connectors and git; personal cards show `—`.
