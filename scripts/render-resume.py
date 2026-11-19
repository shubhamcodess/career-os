#!/usr/bin/env python3
"""
Career OS — Resume renderer: resume.md → resume.html → resume.pdf, fitted to a page target.

    python3 scripts/render-resume.py resumes/<folder>            # build html + pdf, auto-fit to 1 page
    python3 scripts/render-resume.py resumes/<folder> --pages 2
    python3 scripts/render-resume.py resumes/<folder> --density compact --no-pdf
    python3 scripts/render-resume.py resumes/<folder> --template default --header centered

It tries each density (roomy → normal → compact → tight) and keeps the roomiest one that fits
the page target without the content being wider than the page. If nothing fits it says by how
much, and exits 1: the fix is then to cut words, never to shrink further.

────────────────────────────────────────────────────────────────────────────────────────────
resume.md format (this is the contract; skills/resume-builder/SKILL.md explains the writing rules)

    # Full Name

    **Headline · one line**

    City, ST 000000, CC · +00-0000000000 · name@example.com

    [linkedin.com/in/handle](https://www.linkedin.com/in/handle/) · [github.com/handle](https://github.com/handle)

    ## Summary

    One paragraph.

    ## Experience

    ### Company (client: X) | City, CC | Mon YYYY – Present

    **Role · product or team in plain words | Mon YYYY – Present**

    - Bullet.

    ## Projects

    **Project name** | Tech, Tech | [github.com/handle/repo](https://github.com/handle/repo) · [handle.github.io/repo](https://handle.github.io/repo/)

    - Bullet.

    ## Skills

    - **Label:** Item, Item, Item

    ## Certifications

    **Issuer:** [Certificate name](https://verify-url), [Another](https://verify-url)

    ## Education

    **Degree, Field** | Institution | City, ST · YYYY – YYYY

Rules the renderer relies on:
  • fields on a row are separated by " | ", items inside a field by " · "
  • the links line under the contact line is optional; write the visible text as the URL itself
    (an ATS reads visible text, not the hyperlink target)
  • a link whose visible text is a URL gets a small icon chosen from its address
  • any other "## Section" works too: bullets become a list, "**a** | b | c" a row, text a line
"""
import argparse
import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DENSITIES = ["roomy", "normal", "compact", "tight"]

ICONS = {
    "linkedin": '<svg class="ic" viewBox="0 0 16 16" aria-hidden="true"><rect x="1.5" y="1.5" width="13" height="13" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.2"/><path d="M5 7v4.5M5 4.8v.1M7.8 11.5V7m0 1.8c0-1 .8-1.8 1.8-1.8s1.6.8 1.6 1.8v2.7" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>',
    "github": '<svg class="ic" viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>',
    "feed": '<svg class="ic" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 3.5a9.5 9.5 0 0 1 9.5 9.5M3 7.5A5.5 5.5 0 0 1 8.5 13" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><circle cx="3.8" cy="12.2" r="1.1" fill="currentColor"/></svg>',
    "web": '<svg class="ic" viewBox="0 0 16 16" aria-hidden="true"><path d="M9.5 2.5h4v4M13.5 2.5 7.5 8.5M11.5 9.5v3a1 1 0 0 1-1 1h-7a1 1 0 0 1-1-1v-7a1 1 0 0 1 1-1h3" fill="none" stroke="currentColor" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    "globe": '<svg class="ic" viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="6.2" fill="none" stroke="currentColor" stroke-width="1.2"/><ellipse cx="8" cy="8" rx="2.7" ry="6.2" fill="none" stroke="currentColor" stroke-width="1.1"/><path d="M1.9 8h12.2M2.8 4.7h10.4M2.8 11.3h10.4" fill="none" stroke="currentColor" stroke-width="1.1"/></svg>',
}


def inline(text):
    """Markdown inline → HTML: links, bold, code ticks dropped."""
    text = html.escape(text, quote=False)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Keep number compounds ("41-tool", "500-case", "400K-record") on one line: a break after
    # the hyphen strands the number at the end of a line.
    return re.sub(r"(?<![\w/\"=.-])(\d[\w.,%+–]*-[A-Za-z]+)(?![^<]*>)", r'<span class="nb">\1</span>', text)


def plain(text):
    return inline(text).replace("<strong>", "").replace("</strong>", "")


def iconize(fragment):
    """Give links whose visible text is the URL itself a small icon, picked from the address."""
    def rep(m):
        url, text = m.group(1), m.group(2)
        if "." not in text or " " in text.strip():
            return m.group(0)          # a worded label, not a visible URL: leave it alone
        low = url.lower()
        if "linkedin.com" in low:
            icon = ICONS["linkedin"]
        elif "github.com" in low:
            icon = ICONS["github"]
        elif re.fullmatch(r"https?://[\w-]+\.github\.io/?", low):
            icon = ICONS["globe"]          # a portfolio site at the root of *.github.io
        elif re.search(r"newsletter|blog|substack|medium\.com|/feed|rss", low):
            icon = ICONS["feed"]
        else:
            icon = ICONS["web"]
        return f'<a class="plink" href="{url}">{icon}{text}</a>'
    return re.sub(r'<a href="([^"]+)">([^<]+)</a>', rep, fragment)


def render_body(md_text, header="split"):
    lines = md_text.split("\n")
    out, section, in_list = [], None, False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        if line.startswith("# "):                      # ── header block ──
            block = [l.strip() for l in lines[i + 1:] if l.strip()]
            block = block[: next((k for k, l in enumerate(block) if l.startswith("#")), len(block))]
            headline = block[0].strip("*") if block else ""
            contact = block[1] if len(block) > 1 else ""
            links = block[2] if len(block) > 2 else ""
            cls = "header centered" if header == "centered" else "header"
            out.append(f'<div class="{cls}"><div class="id"><h1 class="name">{inline(line[2:])}</h1>')
            out.append(f'<div class="headline">{inline(headline)}</div>')
            out.append('<div class="contact">' + ' <span class="sep">·</span> '.join(inline(p) for p in contact.split(" · ")) + "</div></div>")
            if links:
                out.append('<div class="links">' + "".join(f"<div>{iconize(inline(p))}</div>" for p in links.split(" · ")) + "</div>")
            out.append("</div>")
            while i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                i += 1
            i += 1
            continue

        if line.startswith("## "):                     # ── section ──
            close_list()
            if section:
                out.append("</div>")
            section = line[3:].strip()
            out.append(f'<div class="section"><div class="section-title">{html.escape(section)}</div>')

        elif line.startswith("### "):                  # ── company / organisation row ──
            close_list()
            parts = [p.strip() for p in line[4:].split(" | ")]
            right = " · ".join(parts[1:])
            out.append(f'<div class="row company"><span class="left">{inline(parts[0])}</span><span class="right">{inline(right)}</span></div>')

        elif line.startswith("- "):                    # ── bullet ──
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(line[2:])}</li>")

        elif line.startswith("**") and " | " in line:  # ── role / project / education row ──
            close_list()
            parts = [p.strip() for p in line.replace("**", "").split(" | ")]
            sec = (section or "").lower()
            if "project" in sec:
                tech = f'<span class="tech">{inline(parts[1])}</span>' if len(parts) > 1 and parts[1] else ""
                right = iconize(inline(parts[2])) if len(parts) > 2 else ""
                out.append(f'<div class="row project"><span class="left"><span class="name-tag">{inline(parts[0])}</span> {tech}</span><span class="right">{right}</span></div>')
            elif "education" in sec:
                if len(parts) == 2:     # institution | place · years  (degree goes on the next line)
                    out.append(f'<div class="row edu"><span class="left"><span class="inst">{inline(parts[0])}</span></span><span class="right">{inline(parts[1])}</span></div>')
                else:
                    inst = parts[1] if len(parts) > 1 else ""
                    right = parts[2] if len(parts) > 2 else ""
                    out.append(f'<div class="row edu"><span class="left"><span class="inst">{inline(inst)}</span> · <span class="deg">{inline(parts[0])}</span></span><span class="right">{inline(right)}</span></div>')
            else:
                right = " · ".join(parts[1:])
                out.append(f'<div class="row role"><span class="left">{inline(parts[0])}</span><span class="right">{inline(right)}</span></div>')

        elif line.strip():                             # ── free text ──
            close_list()
            css = "summary" if (section or "").lower() == "summary" else "line"
            out.append(f'<div class="{css}">{inline(line)}</div>')

        i += 1

    close_list()
    if section:
        out.append("</div>")
    return "\n".join(out)


def find_template(name):
    folder = ROOT / "templates" / "resume-templates"
    if name:
        path = folder / (name if name.endswith(".html") else name + ".html")
        if not path.exists():
            sys.exit(f"Template not found: {path}")
        return path
    for path in sorted(folder.glob("*.html")):
        if path.read_text(encoding="utf-8").lstrip().startswith("<!-- default: true -->"):
            return path
    candidates = sorted(folder.glob("*.html"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        sys.exit(f"No templates in {folder}")
    return candidates[-1]


def page_count(pdf_path):
    data = pdf_path.read_bytes()
    return len(re.findall(rb"/Type\s*/Page[^s]", data))


def export_pdf(html_path, pdf_path):
    """Returns (ok, overflow_px). overflow_px > 0 means Chrome will shrink the whole page."""
    run = subprocess.run(["node", str(ROOT / "scripts" / "export-pdf.js"), str(html_path), str(pdf_path)],
                         capture_output=True, text=True, cwd=ROOT)
    if run.returncode != 0:
        sys.exit(f"PDF export failed:\n{run.stdout}\n{run.stderr}")
    m = re.search(r"OVERFLOW_X=(\d+)", run.stdout)
    return True, int(m.group(1)) if m else 0


def main():
    ap = argparse.ArgumentParser(description="Render resume.md to HTML and PDF, fitted to a page target.")
    ap.add_argument("target", help="resume folder (containing resume.md) or a path to a .md file")
    ap.add_argument("--template", default=None, help="template name in templates/resume-templates/ (default: the one marked default)")
    ap.add_argument("--density", default="auto", choices=["auto"] + DENSITIES)
    ap.add_argument("--pages", type=int, default=1, help="page target (default 1)")
    ap.add_argument("--header", default="split", choices=["split", "centered"])
    ap.add_argument("--no-pdf", action="store_true", help="write the HTML only")
    args = ap.parse_args()

    target = Path(args.target)
    md_path = target / "resume.md" if target.is_dir() else target
    if not md_path.exists():
        sys.exit(f"Not found: {md_path}")
    html_path, pdf_path = md_path.with_suffix(".html"), md_path.with_suffix(".pdf")

    template = find_template(args.template).read_text(encoding="utf-8")
    body = render_body(md_path.read_text(encoding="utf-8"), header=args.header)

    def write(density):
        html_path.write_text(template.replace("{{DENSITY}}", density).replace("{{RESUME_CONTENT}}", body), encoding="utf-8")

    order = DENSITIES if args.density == "auto" else [args.density]
    if args.no_pdf:
        write(order[1] if args.density == "auto" else order[0])
        print(f"HTML written: {html_path}")
        return

    last = None
    for density in order:
        write(density)
        _, overflow = export_pdf(html_path, pdf_path)
        pages = page_count(pdf_path)
        last = (density, pages, overflow)
        if pages <= args.pages and overflow == 0:
            print(f"OK  density={density}  pages={pages}  → {pdf_path}")
            return
        if overflow:
            break       # width overflow is not a density problem: stop and report

    density, pages, overflow = last
    if overflow:
        print(f"FAIL  a row is {overflow}px wider than the page, so Chrome shrinks everything to fit.\n"
              f"      Shorten the widest single-line row (header contact line, a project row with long URLs).")
    else:
        where = "the tightest density" if args.density == "auto" else f"density={density}"
        print(f"FAIL  {pages} pages at {where} (target {args.pages}).\n"
              f"      Cut words: run scripts/ats-check.py to see orphan lines, then shorten those bullets first.")
    sys.exit(1)


if __name__ == "__main__":
    main()
