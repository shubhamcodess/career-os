# Resume Templates

HTML/CSS templates used by the pdf-export skill to render professional resume PDFs via Puppeteer.

## How Templates Work

Each template is a self-contained HTML/CSS file with a `{{RESUME_CONTENT}}` placeholder where
the generated resume content gets injected before PDF rendering.

The pdf-export skill handles the injection automatically — you never edit templates manually
during a job search session.

## Adding Templates

**Option 1 — Drop a file here:**
Save any `.html` file to this folder. Claude will detect it automatically and make it available.
Say `use template [filename without extension]` to activate it.

**Option 2 — Screenshot or URL:**
Share a screenshot or link of a resume layout you like.
Claude will recreate it as HTML/CSS and save it here.

**Option 3 — Describe what you want:**
Tell Claude what you want ("minimal, single column, blue accent, ATS-safe") and it will
design and save a new template.

## Setting a Default

Add `<!-- default: true -->` as the very first line of any template file.
The pdf-export skill will use it automatically unless you specify another.

## Template Naming Convention

`[style]-[variant].html`

Examples:
- `default.html` — the baseline professional template
- `minimal-clean.html` — single column, no color, maximum ATS safety
- `modern-sidebar.html` — two-column with sidebar (use carefully — some ATS fail on columns)
- `executive.html` — conservative, serif font, traditional layout
- `startup-friendly.html` — clean, slightly modern, good for product companies

## ATS Safety Note

For roles at companies using automated ATS screening:
- Use single-column templates only
- Avoid tables, text boxes, headers/footers with critical info
- Stick to standard section names: Experience, Education, Skills, Projects
- Fonts: Arial, Calibri, Times New Roman, Georgia — embedded in PDF

For direct-to-human applications (referrals, cold outreach, portfolio):
- Any template is fine — design can shine here
