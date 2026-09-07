# Contributing to Career OS

Thanks for wanting to improve this. Here's how the project is organized and how to contribute.

## Philosophy

- **Skills over hardcoded logic.** Every capability is a `SKILL.md` file Claude Code reads
  and executes. No capability should require changing `CLAUDE.md` itself unless it's core
  orchestration logic.
- **Data and framework are separate.** Nothing in `skills/`, `templates/`, or root config
  files should ever contain personal data. Personal data lives in `data/`, `config/user.json`,
  and `.env` — all gitignored in forks meant to stay private.
- **Honest about limitations.** If a data source is scraped, fragile, or has caveats, say so
  in the skill's description and in `README.md`. Don't oversell.

## Adding a New Skill

1. Create `skills/[skill-name]/SKILL.md`
2. Follow the existing format: YAML frontmatter with `name` + `description`, then instructions
3. The `description` field is how Claude Code decides when to trigger the skill — be specific
   about trigger phrases and be a little "pushy" in describing when to use it (undertriggering
   is the common failure mode)
4. Add complex reference material to `skills/[skill-name]/references/` if the main SKILL.md
   would exceed ~500 lines
5. Update `CLAUDE.md`'s skill table and `README.md`'s structure diagram
6. Add the skill's commands to `docs/SKILLS.md`

## Adding a New Job Board / Data Source

1. If it has an MCP connector — add to `mcp/.mcp.json` with a clear `description`
2. If it doesn't — build a scraper following the pattern in `skills/naukri-scraper/SKILL.md`:
   Python + Playwright, rate-limited, documented honestly as fragile
3. Wire it into `skills/job-aggregator/SKILL.md`'s fan-out step
4. Update the "Data Sources & What's Really Possible" table in `README.md`

## Adding a Resume Template

1. Create `templates/resume-templates/[name].html`
2. Must include a `{{RESUME_CONTENT}}` placeholder
3. Test render via `node scripts/export-pdf.js templates/resume-templates/[name].html exports/test.pdf`
4. Add a one-line description to `templates/resume-templates/README.md`

## Code Style

- Markdown files: clear headers, tables where structured data helps, no unnecessary prose
- Scripts (Python/JS): comment the "why" not the "what", handle errors gracefully, never
  fail silently — log to `data/logs/`
- No secrets, ever, in committed files — always reference `${ENV_VAR}` or read from `.env`

## Testing Changes

Since this is instruction-driven (not traditional code), "testing" means:
1. Run the skill in a real Claude Code session with sample data
2. Confirm it triggers on the intended phrases and doesn't over-trigger on unrelated requests
3. Confirm it degrades gracefully if a dependency (API key, MCP) is missing
4. Confirm git commits happen with clear messages

## Pull Request Process

1. Fork the repo
2. Create a branch: `feature/[skill-name]` or `fix/[what-you-fixed]`
3. Test your change with real (or realistic dummy) data
4. Update relevant docs (`README.md`, `docs/SKILLS.md`, `CLAUDE.md` if orchestration changed)
5. Open a PR describing what it does and why

## Questions or Ideas

Open an issue. Ideas for what's still missing are as valuable as code.
