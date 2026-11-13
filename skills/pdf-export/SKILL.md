---
name: pdf-export
description: >
  Invoke this skill whenever generating a final resume PDF, exporting any document as PDF,
  or when the user says "export pdf", "generate pdf", "make pdf", "final pdf", or "download resume".
  Also invoke automatically after every tailored resume generation as part of the Phase 3 pipeline.
  Builds resume.md into HTML and a typeset PDF with scripts/render-resume.py (Puppeteer underneath),
  fitted to the page target. Never use pandoc, grip, or generic md-to-pdf converters — output
  quality is unacceptable.
---

# PDF Export Skill

Turns `resume.md` into `resume.html` and `resume.pdf` with one command. Rendering goes through
a real Chrome engine (Puppeteer), so the PDF is exactly what the HTML shows.

## Pipeline

```bash
python3 scripts/render-resume.py resumes/[folder]                 # auto-fit to 1 page
python3 scripts/render-resume.py resumes/[folder] --pages 2       # two-page target
python3 scripts/render-resume.py resumes/[folder] --template [name]
python3 scripts/ats-check.py resumes/[folder]                     # always run after a build
```

`render-resume.py`:

1. Picks the template: `--template`, else the file whose first line is `<!-- default: true -->`,
   else the newest in `templates/resume-templates/`.
2. Converts `resume.md` (format in `skills/resume-builder/SKILL.md`) into the template's markup.
3. Builds the PDF at each density — `roomy`, `normal`, `compact`, `tight` — and keeps the
   **roomiest one that fits the page target**. You do not tune font sizes or margins by hand.
4. Prints `OK density=… pages=…`, or `FAIL` with the reason and exits 1.

Do not write the HTML by hand and do not write one-off conversion scripts: if the renderer
cannot express something, fix the renderer or the template, and commit that.

## When the build fails

| Message | Meaning | Fix |
|---|---|---|
| `N pages at the tightest density` | Too much text | Cut words in `resume.md`. Run `ats-check.py` and remove orphan lines first, then shorten the oldest role |
| `a row is Npx wider than the page` | One single-line row cannot wrap, so Chrome would shrink the whole page | Shorten that row: the header contact line, or a project row with a long name, tech list and URLs. Move a project's tech list into its bullet if needed |

The second failure is easy to miss by eye: the PDF still looks tidy, but every font is smaller
and there is an unexplained gap at the bottom. The renderer and the checker both detect it;
never work around it by accepting the scaled page.

## Always look at the result

After a successful build, open the PDF (Read tool) once and check what a script cannot:
alignment of the right-hand column, a header that looks crowded, two rows that nearly touch,
a section that looks heavier than the others. Then run `ats-check.py`.

Report to the user with a link to the PDF, the density chosen only if it is `compact` or
`tight` (it means the page is full), and the checker result.

## Templates

Templates live in `templates/resume-templates/` as self-contained HTML/CSS with two
placeholders: `{{RESUME_CONTENT}}` and `{{DENSITY}}` (a class on `<body>`).

The renderer emits these classes; a template styles them:

| Class | What it is |
|---|---|
| `.header` (`.id`, `.name`, `.headline`, `.contact`, `.links`) | Name block and links. `.header.centered` when built with `--header centered` |
| `.summary` | Summary paragraph |
| `.section`, `.section-title` | A section and its heading |
| `.row.company`, `.row.role`, `.row.project`, `.row.edu` (`.left`, `.right`) | Label left, detail right |
| `ul li` | Bullets |
| `.line` | Free text lines (certifications) |
| `a.plink`, `.ic` | A visible URL and its small icon |

Density is expressed as CSS variables on `body`, `body.roomy`, `body.compact`, `body.tight`
(bullet size, bullet gap, line height, section gap). A new template must define all four, or
auto-fit has nothing to step through.

ATS rules for any template: single column, real text (no text in images), standard fonts,
the identity block first in the DOM, and no row that cannot wrap except those the renderer
measures.

### Adding a custom template

If the user drops an HTML/CSS file into `templates/resume-templates/`:
1. Read it, map its structure onto the classes above, add the two placeholders and the four
   density blocks.
2. Build an existing resume with it and run `ats-check.py`.
3. Confirm: *"Template '[name]' loaded. Use it with: `use template [name]`"*

If the user pastes a screenshot or URL of a layout they like: recreate it as HTML/CSS with the
same classes, save it as `templates/resume-templates/[descriptive-name].html`, build a preview
with the current resume and show it.

## Other documents

For cover letters and other one-off HTML, write the HTML and export it directly:

```bash
node scripts/export-pdf.js <input.html> <output.pdf>
```

`export-pdf.js` uses A4 with 0.6in top/bottom and 0.65in side margins, and prints
`OVERFLOW_X=<px>` so a too-wide page is caught there as well.

## Setup (one-time)

```bash
npm install                                  # puppeteer
pip install -r scripts/requirements.txt      # pymupdf for ats-check.py
```

## Commit

Resume folders are personal data: they are gitignored and backed up with
`bash scripts/sync-vault.sh -m "resume: …"`, never committed to the framework repo.
Template, script and skill changes are framework changes and are committed normally.
