#!/usr/bin/env python3
"""
Career OS — ATS check: reads a built resume the way an applicant tracking system does.

    python3 scripts/ats-check.py resumes/<folder>
    python3 scripts/ats-check.py resumes/<folder> --pages 2 --json

It reads resume.pdf (what the ATS parses), resume.md (structure) and, if present,
jd-keywords.json in the same folder (the job's terms, written once per job — see
skills/resume-ats-optimizer/SKILL.md). Exit code is 1 when any FAIL is found.

What it checks
  layout     page count, shrink-to-fit scaling, orphan words, fonts, images, odd characters
  parsing    reading order, contact details as visible text, standard section headings
  content    numbers per role, weak verbs, AI-sounding words, first person, spelling-variant mix,
             repeated facts, links an ATS cannot see
  keywords   coverage of jd-keywords.json, and terms that appear only in a list (thin evidence)

jd-keywords.json
  {
    "required":  {"Google Cloud": ["google cloud", "gcp"], "CI/CD": ["ci/cd", "\\\\bci\\\\b"]},
    "preferred": {"Vector search": ["vector search"]},
    "gaps":      ["Vertex AI"]        # real experience gaps: reported, never counted as fixable
  }
  Each term maps to the spellings that count as a match. Entries are regular expressions,
  matched case-insensitively; plain words work as they are.
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    import pymupdf
except ImportError:                                    # older installs expose it as fitz
    try:
        import fitz as pymupdf
    except ImportError:
        sys.exit("pymupdf is required:  pip install -r scripts/requirements.txt")

STANDARD_SECTIONS = {"summary", "experience", "work experience", "professional experience", "projects",
                     "skills", "technical skills", "education", "certifications", "awards", "publications"}
WEAK = r"\b(helped|assisted|worked on|responsible for|involved in|participated in|supported|tasked with)\b"
AI_TELLS = r"\b(spearheaded|leveraged|leveraging|synergi[sz]ed|orchestrated|facilitated|utili[sz]ed|seamless(ly)?|robust|cutting-edge|passionate|results-driven|proven track record|dynamic)\b"
VARIANTS = [("programme", "program(?!me)"), ("organis", "organiz"), ("optimis", "optimiz"), ("moderni[s]", "moderniz"),
            ("standardis", "standardiz"), ("analys", "analyz"), ("colour", "color"), ("centre", "center"),
            ("licence", "license"), ("behaviour", "behavior")]
SAFE_NON_ASCII = set("·–’‘“”…")


class Report:
    def __init__(self):
        self.rows = []

    def add(self, level, area, message):
        self.rows.append((level, area, message))

    def ok(self, area, message): self.add("PASS", area, message)
    def warn(self, area, message): self.add("WARN", area, message)
    def fail(self, area, message): self.add("FAIL", area, message)
    def info(self, area, message): self.add("INFO", area, message)


def pdf_lines(page):
    """Visual lines as (text, x0, y0, x1, y1), with spans on the same baseline merged."""
    raw = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = "".join(s["text"] for s in line["spans"]).strip()
            if text:
                raw.append([text, *line["bbox"]])
    raw.sort(key=lambda l: (round(l[2]), l[1]))
    merged = []
    for l in raw:
        if merged and abs(merged[-1][2] - l[2]) < 3:
            m = merged[-1]
            m[0] += " " + l[0]; m[3] = max(m[3], l[3]); m[4] = max(m[4], l[4]); m[1] = min(m[1], l[1])
        else:
            merged.append(l)
    return merged


def check_layout(doc, md, r, page_target):
    pages = len(doc)
    (r.ok if pages <= page_target else r.fail)("layout", f"{pages} page(s), target {page_target}")
    page = doc[0]
    if page.get_images():
        r.warn("layout", f"{len(page.get_images())} image(s) on the page — an ATS ignores images; never put text in one")

    # Shrink-to-fit: when a row is wider than the page Chrome scales everything down.
    # The name is the largest text; compare it with the size the template asks for.
    html_path = md.with_suffix(".html")
    if html_path.exists():
        found = re.findall(r"\.name\s*\{[^}]*font-size:\s*([\d.]+)pt", html_path.read_text(encoding="utf-8"))
        m = found[-1] if found else None          # the last rule wins in CSS
        sizes = [s["size"] for b in page.get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"]]
        if m and sizes:
            want, got = float(m), max(sizes)
            if got < want * 0.985:
                r.fail("layout", f"page is scaled to {got / want:.0%} (a row is wider than the page). "
                                 f"Shorten the widest one-line row; do not accept the smaller text")
            else:
                r.ok("layout", "rendered at full size (no shrink-to-fit)")

    fonts = {f[3].split("+")[-1].split("-")[0] for f in page.get_fonts()}
    r.info("layout", "fonts: " + ", ".join(sorted(fonts)))

    lines = pdf_lines(page)
    if lines:
        left = min(l[1] for l in lines); right = max(l[3] for l in lines); width = right - left
        orphans = []
        for prev, cur in zip(lines, lines[1:]):
            wraps = (prev[3] - left) > width * 0.85 and abs(cur[2] - prev[4]) < 6     # prev fills the line, cur follows closely
            short = (cur[3] - cur[1]) < width * 0.16 and len(cur[0].split()) <= 3
            if wraps and short and not cur[0].isupper():
                orphans.append(cur[0])
        if orphans:
            r.warn("layout", "orphan words on their own line (each costs a full line): " + " | ".join(f"'{o}'" for o in orphans))
        else:
            r.ok("layout", "no orphan words")
        free = page.rect.height - 43 - max(l[4] for l in lines)        # 43pt = the 0.6in bottom margin
        if pages == 1 and free > 40:
            r.info("layout", f"about {int(free // 13)} spare line(s) at the bottom — room to add value or restore spacing")

    text = "".join(d.get_text() for d in doc)
    odd = sorted({c for c in text if ord(c) > 127 and c not in SAFE_NON_ASCII and not c.isspace()})
    if odd:
        r.warn("layout", "characters some parsers garble: " + " ".join(odd))
    return text


def check_parsing(text, md_text, r):
    head = "\n".join(text.split("\n")[:8])
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", head)
    phone = re.search(r"\+?\d[\d\s().-]{8,}\d", head)
    (r.ok if email else r.fail)("parsing", "email found in the first lines" if email else "no email in the first lines of the PDF text")
    (r.ok if phone else r.fail)("parsing", "phone found in the first lines" if phone else "no phone number in the first lines")
    name = md_text.split("\n", 1)[0].lstrip("# ").strip()
    if name and not text.lstrip().startswith(name):
        r.warn("parsing", f"the PDF text does not start with the name ('{name}') — check the reading order of the header")
    else:
        r.ok("parsing", "reading order starts with the name")
    if not re.search(r"linkedin\.com/in/[\w-]+", text):
        r.warn("parsing", "no LinkedIn URL as visible text (a link labelled 'LinkedIn' is invisible to an ATS)")
    if not re.search(r"\b\d{5,6}\b", head):
        r.info("parsing", "no postal code in the header (some checkers ask for city, state, postal code, country)")

    for heading in re.findall(r"^## (.+)$", md_text, re.M):
        h = heading.strip().lower()
        if "&" in h or " and " in h:
            r.warn("parsing", f"combined section heading '{heading}' — parsers file everything under the first word; split it")
        elif h not in STANDARD_SECTIONS:
            r.warn("parsing", f"non-standard section heading '{heading}' — use one an ATS recognises")
    dates = re.findall(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b|\b\d{1,2}/\d{4}\b", md_text)
    styles = {"month-name" if d[0].isalpha() else "numeric" for d in dates}
    if len(styles) > 1:
        r.warn("parsing", "mixed date formats (use 'Mon YYYY – Mon YYYY' everywhere)")


def roles(md_text):
    """Yield (role title, [bullets]) for the Experience section."""
    m = re.search(r"^## (?:Work |Professional )?Experience\s*$(.*?)(?=^## |\Z)", md_text, re.M | re.S | re.I)
    if not m:
        return
    title, bullets = None, []
    for line in m.group(1).split("\n"):
        if line.startswith("**") and " | " in line:
            if title:
                yield title, bullets
            title, bullets = line.strip("*").split(" | ")[0], []
        elif line.startswith("- ") and title:
            bullets.append(line[2:])
    if title:
        yield title, bullets


def check_content(text, md_text, r):
    bullets = re.findall(r"^- (?!\*\*)(.+)$", md_text, re.M)
    for title, bl in roles(md_text) or []:
        if bl and not any(re.search(r"\d", re.sub(r"\b(?:v|version )?\d+(?:\.\d+)* to \d+", "", b)) for b in bl):
            r.warn("content", f"no number in any bullet under '{title}' — add one real, defensible figure")
        if not bl:
            r.info("content", f"'{title}' has no bullets")
    for pattern, label in ((WEAK, "weak verb"), (AI_TELLS, "AI-sounding word")):
        hits = sorted({m.group(0).lower() for b in bullets for m in re.finditer(pattern, b, re.I)})
        if hits:
            r.warn("content", f"{label}s: " + ", ".join(hits))
    if "—" in md_text:
        r.warn("content", f"{md_text.count('—')} em dash(es) — use a comma, a colon or two sentences")
    if re.search(r"\bI\b|\bI'm\b|\bI've\b", " ".join(bullets)):
        r.warn("content", "first person ('I') in a bullet — drop the subject")
    low = md_text.lower()
    for brit, amer in VARIANTS:
        if re.search(brit, low) and re.search(amer, low):
            b = re.search(brit, low).group(0); a = re.search(amer, low).group(0)
            if b != a:
                r.warn("content", f"mixed spelling variants: '{b}…' and '{a}…' — pick one (checkers flag the odd one as unknown)")
    # the same number-with-noun stated twice (team size in two places, a metric repeated in the summary)
    seen = {}
    for m in re.finditer(r"\b(\d[\d,.]*\+?%?)\s+([a-z][a-z-]+)", low):
        seen.setdefault(m.group(0), 0); seen[m.group(0)] += 1
    repeats = [k for k, v in seen.items() if v > 1 and not re.match(r"\d{4}\b", k)]
    if repeats:
        r.info("content", "stated more than once (keep each fact in one place): " + ", ".join(sorted(repeats)[:6]))
    labelled = [t for t, u in re.findall(r"\[([^\]]+)\]\((https?://[^)]+)\)", md_text) if "." not in t]
    if labelled:
        r.info("content", f"{len(labelled)} link(s) with a worded label (fine for certificates; for profiles and repos show the URL as text)")
    for line in re.findall(r"^- \*\*[^*]+:\*\* (.+)$", md_text, re.M):
        items = [i.strip() for i in line.split(",")]
        lower = [i for i in items if i and i[0].islower()]
        if lower:
            r.warn("content", "skills starting with a lowercase letter (name the tool, capitalised): " + ", ".join(lower))


def check_keywords(text, md_text, folder, r):
    path = folder / "jd-keywords.json"
    if not path.exists():
        r.info("keywords", "no jd-keywords.json in this folder — write one from the job posting to get a coverage score")
        return None
    spec = json.loads(path.read_text(encoding="utf-8"))
    # Undo line wrapping first: a phrase or hyphenated word split across two PDF lines must still match.
    low = re.sub(r"\s+", " ", text.replace("-\n", "-")).lower()
    # "body" = everything except the pure lists, to tell demonstrated terms from listed ones
    body = re.sub(r"^## (Skills|Technical Skills|Certifications)\s*$.*?(?=^## |\Z)", "", md_text, flags=re.M | re.S | re.I).lower()
    result = {}
    for group in ("required", "preferred"):
        terms = spec.get(group, {})
        hit, miss, thin = [], [], []
        for term, patterns in terms.items():
            pats = patterns if isinstance(patterns, list) else [patterns]
            found = any(re.search(p, low, re.I) for p in pats)
            (hit if found else miss).append(term)
            if found and not any(re.search(p, body, re.I) for p in pats):
                thin.append(term)
        if terms:
            pct = round(100 * len(hit) / len(terms))
            result[group] = pct
            level = r.ok if pct >= 75 else r.warn
            level("keywords", f"{group}: {len(hit)}/{len(terms)} = {pct}%" + (f"  missing: {', '.join(miss)}" if miss else ""))
            if thin:
                r.info("keywords", f"{group} terms that appear only in a list, with no bullet behind them: {', '.join(thin)}")
    gaps = spec.get("gaps", [])
    if gaps:
        r.info("keywords", "real gaps (do not add until true): " + ", ".join(gaps))
    return result


def main():
    ap = argparse.ArgumentParser(description="Check a built resume the way an ATS reads it.")
    ap.add_argument("folder", help="resume folder containing resume.md and resume.pdf")
    ap.add_argument("--pages", type=int, default=1)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    folder = Path(args.folder)
    md, pdf = folder / "resume.md", folder / "resume.pdf"
    for p in (md, pdf):
        if not p.exists():
            sys.exit(f"Not found: {p}  (build it first: python3 scripts/render-resume.py {folder})")

    r = Report()
    md_text = md.read_text(encoding="utf-8")
    doc = pymupdf.open(pdf)
    text = check_layout(doc, md, r, args.pages)
    check_parsing(text, md_text, r)
    check_content(text, md_text, r)
    scores = check_keywords(text, md_text, folder, r)

    fails = sum(1 for l, _, _ in r.rows if l == "FAIL")
    warns = sum(1 for l, _, _ in r.rows if l == "WARN")
    if args.json:
        print(json.dumps({"fails": fails, "warnings": warns, "keywords": scores,
                          "rows": [dict(level=l, area=a, message=m) for l, a, m in r.rows]}, indent=2))
    else:
        mark = {"PASS": "✓", "WARN": "!", "FAIL": "✗", "INFO": "·"}
        area = None
        for level, a, message in r.rows:
            if a != area:
                print(f"\n{a.upper()}"); area = a
            print(f"  {mark[level]} {message}")
        print(f"\n{fails} fail(s), {warns} warning(s)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
