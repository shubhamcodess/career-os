---
name: dashboard
description: >
  Renders the Career OS help screen or status dashboard as an interactive widget
  using show_widget. Triggered by: help, /help, status, /status, "show dashboard",
  "what can you do", "what commands", "show me the commands", "system status".
---

# Dashboard Skill

This skill handles all dashboard-style outputs — `help` and `status` — by rendering
an interactive widget instead of plain text.

**Always call `show_widget` for these commands. Never output plain ASCII art.**

---

## When to Invoke

| Command | Mode |
|---|---|
| `help`, `/help`, `what can you do`, `show commands` | Help mode |
| `status`, `/status`, `show status`, `system status` | Status mode |

Both modes use the same widget. Status mode shows more data (market freshness,
file counts, vault sync date). Help mode shows the command reference.

---

## Step 1 — Read Live State

Before rendering, read these files to populate the widget with current values:

| Data needed | Source |
|---|---|
| Interview status + checkpoint | `checkpoints/interview-state.md` (exists → parse CP-N; missing → NOT STARTED) |
| Master doc size | `data/master-experience.md` (wc -l or Read; missing → empty) |
| Resume count + latest | `ls resumes/` (count non-.gitkeep dirs; latest = newest by date in name) |
| Job feed last run | `data/market/job-feed.md` first line or frontmatter date; missing → "never run" |
| Last commit message | `git log -1 --format="%s"` |
| Setup checks | Read `.env` (check keys present, PERSONALIZE, PRIVATE_REPO_URL), `config/user.json` (exists?), `node_modules/` (exists?), `exports/test-render.pdf` (exists?), `data/master-experience.md` (content?), `resumes/` (any version?) |
| **Status mode only** | |
| Company intel files | `ls data/market/company-intel/` — count + newest mtime |
| Role portrait files | `ls data/market/role-portraits/` — count + newest mtime |
| Vault sync date | `git -C .personal-worktree log -1 --format="%ar" 2>/dev/null` or "never" |
| Version registry | `data/version-registry.md` — count resume entries |
| Job tracker | `data/job-tracker.md` — count open/applied entries |

Compute status indicators:

```
dot_color(value):
  "in progress" or "partial" → "dot-yellow"
  "complete" or all-green    → "dot-green"
  "never run" or "0" or missing → "dot-gray"
  error / blocked            → "dot-red"
```

---

## Step 2 — Call show_widget

Use the following HTML template. Substitute all `{{PLACEHOLDER}}` values with
live data before calling. Remove `{{PLACEHOLDER}}` tokens — never leave them in.

**loading_messages** for help: `["Loading Career OS…", "Reading your current state…", "Building the command palette…"]`
**loading_messages** for status: `["Reading all data files…", "Checking market intel freshness…", "Building status dashboard…"]`
**title**: `career_os_help` for help mode, `career_os_status` for status mode.

```html
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--font-sans);font-size:14px;color:var(--text-primary)}
.wrap{border:0.5px solid var(--border);border-radius:12px;overflow:hidden;background:var(--surface-2)}
.topbar{display:flex;align-items:center;justify-content:space-between;padding:10px 16px;background:var(--surface-1);border-bottom:0.5px solid var(--border)}
.topbar-left{display:flex;align-items:center;gap:10px}
.logo{font-size:13px;font-weight:500;color:var(--text-primary);letter-spacing:.3px}
.logo span{font-family:var(--font-mono);font-size:11px;color:var(--text-muted);margin-left:4px}
.badge{font-size:11px;font-weight:500;padding:2px 8px;border-radius:4px;background:var(--bg-success);color:var(--text-success)}
.avatar{width:26px;height:26px;border-radius:50%;background:var(--bg-accent);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:500;color:var(--text-accent)}
.state-strip{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:0.5px solid var(--border)}
.state-cell{padding:10px 14px;border-right:0.5px solid var(--border)}
.state-cell:last-child{border-right:none}
.state-label{font-size:11px;color:var(--text-muted);margin-bottom:3px;text-transform:uppercase;letter-spacing:.6px}
.state-val{font-size:13px;font-weight:500;color:var(--text-primary);display:flex;align-items:center;gap:5px}
.dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.dot-yellow{background:#d29922}
.dot-green{background:#3fb950}
.dot-gray{background:var(--border-strong)}
.dot-red{background:#f85149}
.next-banner{display:flex;align-items:center;gap:10px;padding:10px 16px;background:var(--bg-accent);border-bottom:0.5px solid var(--border-accent)}
.next-label{font-size:11px;font-weight:500;text-transform:uppercase;letter-spacing:.6px;color:var(--text-accent);white-space:nowrap}
.next-cmd{font-family:var(--font-mono);font-size:13px;color:var(--text-accent);font-weight:500}
.next-desc{font-size:12px;color:var(--text-accent);opacity:.75;margin-left:2px}
.tabs{display:flex;border-bottom:0.5px solid var(--border);background:var(--surface-1);padding:0 8px}
.tab{font-size:12px;font-weight:500;color:var(--text-secondary);padding:9px 12px;cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap;user-select:none;transition:color .12s}
.tab:hover{color:var(--text-primary)}
.tab.active{color:var(--text-accent);border-bottom-color:var(--border-accent)}
.panel{display:none;padding:4px 0}
.panel.active{display:block}
.cmd-group{padding:6px 16px 2px;font-size:11px;font-weight:500;text-transform:uppercase;letter-spacing:.6px;color:var(--text-muted);margin-top:4px}
.cmd-row{display:flex;align-items:baseline;gap:0;padding:6px 16px;cursor:default}
.cmd-row:hover{background:var(--surface-1)}
.cmd{font-family:var(--font-mono);font-size:12.5px;color:var(--text-accent);white-space:nowrap;min-width:240px;flex-shrink:0}
.cmd-desc{font-size:12px;color:var(--text-secondary);line-height:1.5}
.cmd-row.dim .cmd{color:var(--text-muted)}
.divider{height:0.5px;background:var(--border);margin:6px 16px}
.checklist{padding:8px 16px}
.check-row{display:flex;align-items:center;gap:10px;padding:5px 0;border-bottom:0.5px solid var(--border)}
.check-row:last-child{border-bottom:none}
.check-icon{font-size:13px;width:18px;flex-shrink:0}
.check-label{font-size:13px;color:var(--text-primary)}
.check-sub{font-size:11px;color:var(--text-muted);margin-top:1px}
.run-btn{font-family:var(--font-mono);font-size:11px;color:var(--text-accent);background:none;border:0.5px solid var(--border-accent);border-radius:4px;padding:2px 7px;cursor:pointer;margin-left:auto;flex-shrink:0}
.run-btn:hover{background:var(--bg-accent)}
.stat-grid{display:grid;grid-template-columns:1fr 1fr;gap:0;padding:8px 0}
.stat-cell{padding:8px 16px;border-bottom:0.5px solid var(--border);border-right:0.5px solid var(--border)}
.stat-cell:nth-child(even){border-right:none}
.stat-name{font-size:11px;color:var(--text-muted);margin-bottom:2px}
.stat-val{font-size:13px;font-weight:500;color:var(--text-primary)}
.stat-sub{font-size:11px;color:var(--text-muted);margin-top:1px}
.last-action{padding:10px 16px;background:var(--surface-1);border-top:0.5px solid var(--border);display:flex;align-items:center;gap:8px;font-size:11px;color:var(--text-muted)}
.last-action code{font-family:var(--font-mono);font-size:11px;color:var(--text-secondary)}
</style>

<div class="wrap">
  <div class="topbar">
    <div class="topbar-left">
      <div class="logo">Career OS <span>v0.1 · personal mode</span></div>
      <div class="badge">PERSONALIZE=true</div>
    </div>
    <div class="avatar">SP</div>
  </div>

  <!-- STATE STRIP — 4 cells. Use dot class: dot-yellow / dot-green / dot-gray / dot-red -->
  <div class="state-strip">
    <div class="state-cell">
      <div class="state-label">Interview</div>
      <div class="state-val"><span class="dot {{INTERVIEW_DOT}}"></span>{{INTERVIEW_LABEL}}</div>
    </div>
    <div class="state-cell">
      <div class="state-label">Master doc</div>
      <div class="state-val"><span class="dot {{MASTER_DOT}}"></span>{{MASTER_LABEL}}</div>
    </div>
    <div class="state-cell">
      <div class="state-label">Resumes</div>
      <div class="state-val"><span class="dot {{RESUME_DOT}}"></span>{{RESUME_LABEL}}</div>
    </div>
    <div class="state-cell">
      <div class="state-label">Job feed</div>
      <div class="state-val"><span class="dot {{FEED_DOT}}"></span>{{FEED_LABEL}}</div>
    </div>
  </div>

  <!-- NEXT ACTION BANNER -->
  <div class="next-banner">
    <div class="next-label">Next →</div>
    <div class="next-cmd">{{NEXT_CMD}}</div>
    <div class="next-desc">— {{NEXT_DESC}}</div>
  </div>

  <!-- TABS — for help mode: Intake | Resume | Jobs | Intel | Outreach | System -->
  <!--        for status mode: Overview | Data | Market | Setup -->
  <div class="tabs" id="tabs">
    {{TABS_HTML}}
  </div>

  {{PANELS_HTML}}

  <div class="last-action">
    Last commit: <code>{{LAST_COMMIT}}</code>
  </div>
</div>

<script>
document.getElementById('tabs').addEventListener('click',function(e){
  var t=e.target.closest('.tab');
  if(!t)return;
  document.querySelectorAll('.tab').forEach(function(x){x.classList.remove('active')});
  document.querySelectorAll('.panel').forEach(function(x){x.classList.remove('active')});
  t.classList.add('active');
  document.getElementById(t.dataset.tab).classList.add('active');
});
</script>
```

---

## Step 3 — Tab Content Templates

### Help Mode Tabs

Generate `{{TABS_HTML}}`:
```html
<div class="tab active" data-tab="intake">Intake</div>
<div class="tab" data-tab="resume">Resume</div>
<div class="tab" data-tab="jobs">Jobs</div>
<div class="tab" data-tab="intel">Intel</div>
<div class="tab" data-tab="outreach">Outreach</div>
<div class="tab" data-tab="system">System</div>
```

Generate `{{PANELS_HTML}}` — one `<div id="[tab]" class="panel [active?]">` per tab.

**Intake panel** — show interview checkpoint progress as `.cmd-row.dim` rows with `✓` for done,
`○` for pending. Add a `run-btn` on `resume interview` that calls
`onclick="sendPrompt('resume interview')"`.

**Resume panel** — full resume pipeline commands (make resume, jd check, cover letter, ats check,
export pdf, use template, version log, diff).

**Jobs panel** — find jobs, refresh feed, jd check, job tracker. List active data sources
(ATS Direct, Indeed/Zip/Dice, Naukri) as `.dim` rows.

**Intel panel** — profile intel, github market map, research comp, prep for interview,
optimize profile, export portfolio brief.

**Outreach panel** — draft outreach, cold email to, LinkedIn message, connection request,
save outreach, follow-up version, iteration commands (make it shorter, different hook, etc.).

**System panel** — setup checklist as `.check-row` entries (9 items, read live state to set
✅ / ⚠️ / ❌), then: status, backup, add skill, add template, help.

### Status Mode Tabs

Generate `{{TABS_HTML}}`:
```html
<div class="tab active" data-tab="overview">Overview</div>
<div class="tab" data-tab="data">Personal Data</div>
<div class="tab" data-tab="market">Market Intel</div>
<div class="tab" data-tab="setup">Setup</div>
```

**Overview panel** — `.stat-grid` 2-col with cells for each data source:

| Cell | Value source |
|---|---|
| Interview | checkpoint label + CP-N |
| Master doc | line count + section count if parseable |
| Resumes | count + latest name |
| Job feed | last run date + listing count if in frontmatter |
| Star stories | count entries in `data/star-stories.md` |
| Vault sync | `git -C .personal-worktree log -1 --format="%ar"` |

**Data panel** — freshness rows for each personal data file. Format:
```html
<div class="cmd-row">
  <span class="cmd">data/master-experience.md</span>
  <span class="cmd-desc">312 lines · last modified: [date]</span>
</div>
```
Show `⚠️ stale` if file is missing or empty.

**Market panel** — freshness for:
- `data/market/job-feed.md` — last run date
- `data/market/company-intel/` — N files, newest: [date]
- `data/market/role-portraits/` — N files, newest: [date]
- `data/market/jd-analyses/` — N files

**Setup panel** — same 9-item checklist as help/system tab.

---

## Next Action Logic

Derive `{{NEXT_CMD}}` and `{{NEXT_DESC}}` from this priority order:

1. If `checkpoints/interview-state.md` missing or empty → `begin intake interview` / "No intake data yet — start here to unlock the resume pipeline."
2. If interview IN PROGRESS (any CP-N) → `resume interview` / "Pick up at [next phase]. [N] phases remaining."
3. If interview COMPLETE but no resumes → `make resume for [Company/Role]` / "Intake is done — paste a JD to generate your first targeted resume."
4. If resumes exist but job feed never run → `find jobs` / "Pipeline is ready — pull live listings to find roles to target."
5. If all data fresh and resumes exist → `refresh job feed` / "Everything is set up. Keep the job feed current."

---

## Notes

- Always use `show_widget` — never render help/status as plain text.
- After calling `show_widget`, output one sentence max in text (e.g., "Here's the current state." or nothing at all).
- If any file read fails (missing file), use graceful defaults: "—" for missing values, `dot-gray` for missing data.
- Framework mode (`PERSONALIZE=false`): render only the command reference tabs (Resume, Jobs, Intel, Outreach, System). Skip state strip personal data. Set all state cells to `dot-gray` with label "—".
