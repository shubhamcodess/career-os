---
name: pdf-export
description: >
  Invoke this skill whenever generating a final resume PDF, exporting any document as PDF,
  or when the user says "export pdf", "generate pdf", "make pdf", "final pdf", or "download resume".
  Also invoke automatically after every tailored resume generation as part of the Phase 3 pipeline.
  This skill uses Puppeteer (headless Chrome) via the Puppeteer MCP or local Node.js script
  to render HTML/CSS to a pixel-perfect PDF with proper margins, padding, typography, and
  page breaks. Never use pandoc, grip, or generic md-to-pdf converters — output quality is unacceptable.
---

# PDF Export Skill

Produces professional, typeset resume PDFs using Puppeteer for HTML-to-PDF rendering.

## Why Puppeteer

Generic markdown-to-PDF tools (pandoc, grip, wkhtmltopdf) produce inconsistent output:
wrong margins, uncontrolled page breaks, poor font rendering, no design control.
Puppeteer renders through a real Chrome engine — what you see in the browser is exactly what
prints to PDF. Full CSS control: margins, padding, font-weight, line-height, color, page breaks.

## Pipeline

Given a resume in `resumes/[folder]/resume.md`:

### Step 1 — Select Template
Read `templates/resume-templates/` directory.
- If user specified a template (`use template [name]`), use that file
- If a template is marked `<!-- default: true -->` in its first line, use that
- If only one template exists, use it
- If none exists, generate the default template (see below) and save it first

### Step 2 — Populate Template
Take the resume content from `resume.md` and inject it into the HTML template.
Map markdown sections to HTML elements:
- `# Name` → `<h1 class="name">`
- `## Experience`, `## Education`, etc. → `<section>` with heading
- Bullet points → `<ul><li>` with proper spacing
- Bold text → `<strong>`
- Dates/locations → right-aligned `<span class="meta">`

### Step 3 — Save HTML
Write populated HTML to `resumes/[folder]/resume.html`

### Step 4 — Generate PDF via Puppeteer

**Option A — Via Puppeteer MCP (if connected):**
Use the Puppeteer MCP to navigate to the HTML file and export as PDF with these settings:
```json
{
  "format": "A4",
  "printBackground": true,
  "margin": {
    "top": "0.6in",
    "bottom": "0.6in",
    "left": "0.65in",
    "right": "0.65in"
  },
  "preferCSSPageSize": false,
  "displayHeaderFooter": false
}
```

**Option B — Via local Node.js script (if MCP not connected):**
Generate and run this script:

```javascript
// scripts/export-pdf.js
const puppeteer = require('puppeteer');
const path = require('path');

async function exportPDF(htmlPath, pdfPath) {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();

  const absolutePath = path.resolve(htmlPath);
  await page.goto(`file://${absolutePath}`, { waitUntil: 'networkidle0' });

  await page.pdf({
    path: pdfPath,
    format: 'A4',
    printBackground: true,
    margin: {
      top: '0.6in',
      bottom: '0.6in',
      left: '0.65in',
      right: '0.65in'
    },
    preferCSSPageSize: false,
    displayHeaderFooter: false
  });

  await browser.close();
  console.log(`PDF exported: ${pdfPath}`);
}

const htmlPath = process.argv[2];
const pdfPath = process.argv[3];
exportPDF(htmlPath, pdfPath);
```

Run with:
```bash
node scripts/export-pdf.js resumes/[folder]/resume.html resumes/[folder]/resume.pdf
```

### Step 5 — Verify and Commit
Confirm PDF was created, then:
```bash
git add -A
git commit -m "export: generated PDF for [Company]_[Role]_[date]_v[N]"
```

---

## Default Resume Template

If no template exists, create `templates/resume-templates/default.html` with this:

```html
<!-- default: true -->
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Calibri', 'Segoe UI', Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.45;
    color: #1a1a1a;
    background: white;
  }

  .page {
    max-width: 100%;
    padding: 0; /* margins handled by Puppeteer */
  }

  /* ── Header ── */
  .header {
    text-align: center;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1.5px solid #2c5282;
  }
  .name {
    font-size: 22pt;
    font-weight: 700;
    color: #1a1a2e;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
  }
  .contact-line {
    font-size: 9pt;
    color: #444;
    display: flex;
    justify-content: center;
    gap: 16px;
    flex-wrap: wrap;
  }
  .contact-line a { color: #2c5282; text-decoration: none; }

  /* ── Section Headings ── */
  .section {
    margin-bottom: 12px;
  }
  .section-title {
    font-size: 10pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #2c5282;
    border-bottom: 1px solid #2c5282;
    padding-bottom: 2px;
    margin-bottom: 7px;
  }

  /* ── Experience Entries ── */
  .entry {
    margin-bottom: 9px;
  }
  .entry-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 1px;
  }
  .company {
    font-weight: 700;
    font-size: 10.5pt;
    color: #1a1a1a;
  }
  .date {
    font-size: 9.5pt;
    color: #555;
    white-space: nowrap;
  }
  .role {
    font-style: italic;
    font-size: 10pt;
    color: #333;
    margin-bottom: 4px;
  }

  /* ── Bullets ── */
  ul {
    padding-left: 16px;
    margin-top: 3px;
  }
  ul li {
    margin-bottom: 2.5px;
    font-size: 10pt;
    line-height: 1.42;
  }
  ul li::marker { color: #2c5282; }

  /* ── Skills ── */
  .skills-grid {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 3px 10px;
    font-size: 10pt;
  }
  .skill-label {
    font-weight: 600;
    color: #333;
    white-space: nowrap;
  }

  /* ── Education ── */
  .edu-entry {
    display: flex;
    justify-content: space-between;
    margin-bottom: 5px;
  }

  /* ── Page Breaks ── */
  .section { page-break-inside: avoid; }
  .entry { page-break-inside: avoid; }
  h1, .section-title { page-break-after: avoid; }

  /* ── Summary ── */
  .summary {
    font-size: 10pt;
    line-height: 1.5;
    color: #222;
    margin-bottom: 2px;
  }
</style>
</head>
<body>
<div class="page">
  <!-- CONTENT INJECTED HERE BY PDF EXPORT SKILL -->
  {{RESUME_CONTENT}}
</div>
</body>
</html>
```

---

## Adding a Custom Template

If the user drops an HTML/CSS file into `templates/resume-templates/`:
1. Read the file to understand its structure
2. Identify the injection point (where resume content goes)
3. Add `{{RESUME_CONTENT}}` placeholder if not present
4. Confirm: *"Template '[name]' loaded. Use it with: `use template [name]`"*

If the user pastes a screenshot or URL of a resume layout they like:
1. Recreate it as HTML/CSS matching the visual design as closely as possible
2. Save to `templates/resume-templates/[descriptive-name].html`
3. Confirm it's ready to use
4. Offer to generate a PDF preview with current resume content

---

## Setup (One-Time)

```bash
npm init -y
npm install puppeteer
```

Or if using the Puppeteer MCP server, ensure it's configured in `mcp/.mcp.json` (already done).
