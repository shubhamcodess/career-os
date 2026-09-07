---
name: job-search-command-center
description: >
  Full job search system for landing roles at product-based companies. Use this skill whenever
  the user wants to: run a structured job search, build or update their Master Experience Document,
  generate tailored resumes for specific companies or roles, optimize their Naukri or LinkedIn
  profile, prepare for behavioral interviews, research compensation, draft cold outreach, track
  applications, or build their portfolio website content. Trigger immediately on: "make resume for",
  "job search", "help me get a job at", "optimize my Naukri", "prep for interview at", "what should
  my resume say for", "I'm applying to", "draft outreach for", or any mention of job switching,
  resume creation, or career transition. Also trigger when the user says "pause interview", "resume
  interview", "show checkpoints", or any command from the command reference table. This skill
  orchestrates all resume skills, ATS tools, and humanizers already in the project — always check
  for and invoke those saved skills first before using built-in defaults.
---

# Job Search Command Center

A complete, end-to-end system for landing a well-paid role at a product-based company. This skill
orchestrates experience capture, resume generation, ATS optimization, profile optimization,
interview prep, and portfolio building — all from a single source of truth.

## Core Principle

The goal is not a great resume. The goal is an offer.

In today's hiring at product-based companies (FAANG, funded startups, product orgs), a candidate
must survive multiple filters: ATS screening → recruiter 10-second scan → hiring manager deep-read
→ behavioral + technical interviews → offer negotiation. This system is built to win at every layer.

## Saved Skills Protocol

**Always check the project for saved skills first.** Before running any resume or profile task,
scan for: ATS optimizer, resume builder, humanizer, keyword analyzer, or any other resume tool
the user has saved. Invoke those skills as part of the workflow. Do not duplicate their output.
This skill is the orchestrator; saved skills are specialized modules.

## Master Documents

Maintain these living documents throughout the project. Reference them before every task.

| Document | Purpose |
|---|---|
| `master-experience.md` | Complete professional story — single source of truth for all resumes |
| `star-stories.md` | STAR behavioral stories tagged by competency |
| `version-registry.md` | Every resume: company, role, version, date, changes, status |
| `portfolio-brief.md` | Portfolio website content in AI-agent-ready format |
| `job-tracker.md` | Every role tracked: source, status, next action |
| `comp-intel.md` | Market salary/equity data for target roles |

## Workflow Reference

See `references/phases.md` for full phase-by-phase instructions. Quick summary:

- **Phase 1**: Structured intake interview with pause/resume, checkpoints, and non-linear editing
- **Phase 2**: Master Resume — comprehensive, unabridged, XYZ-format bullets
- **Phase 3**: Tailored Resume — per company/role, triggered by `make resume for [Company/Role]`
- **Phase 4**: Quality layer — ATS, keyword match, impact audit, humanizer, recruiter simulation
- **Phase 5**: Job profile optimization — Naukri, LinkedIn, Instahyre, Wellfound
- **Phase 6**: STAR Story Bank + behavioral interview prep
- **Phase 7**: Compensation research and negotiation prep
- **Phase 8**: Cold outreach and referral strategy
- **Phase 9**: Portfolio website foundation + AI-agent-ready JSON export

## Command Reference

| Command | Action |
|---|---|
| `pause interview` | Save checkpoint, summarize progress, stop intake |
| `resume interview` | Reload checkpoint, continue from exact stopping point |
| `show checkpoints` | List all interview checkpoints with summaries |
| `rewind to [CP-N]` | Go back to checkpoint, edit/delete, offer to jump back |
| `make resume for [Company/Role]` + JD | Full pipeline: research → tailor → generate → Phase 4 |
| `ats check` | Phase 4 quality audit on latest resume |
| `optimize profile for [platform]` | Platform-specific optimization (Naukri, LinkedIn, etc.) |
| `prep for [company] interview` | STAR matching + mock behavioral Q&A |
| `research comp for [role/company]` | Salary, equity, negotiation position |
| `draft outreach for [company]` | Personalized cold message to recruiter or employee |
| `version log` | Full version registry |
| `diff [company] v1 v2` | Exact diff between two resume versions |
| `job tracker` | Full application tracking dashboard |
| `export portfolio brief` | AI-agent-ready JSON for portfolio website build |
| `status` | Full dashboard: applications, stages, next actions |

## Guardrails

- Never fabricate experience, metrics, or skills the user hasn't stated
- Always flag gaps between the user's profile and a JD — be honest, then help address
- Always invoke saved skills before using built-in defaults
- Proactively flag strong STAR stories during intake and capture them separately
- Challenge every bullet that reads as a responsibility rather than an achievement
- Keep the end goal visible in every interaction: an offer, not a document
