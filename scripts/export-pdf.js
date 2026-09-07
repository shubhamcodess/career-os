/**
 * Career OS — PDF Export Script
 * Renders an HTML resume template to a professional PDF using Puppeteer.
 * Called by Claude Code's pdf-export skill after populating a template.
 *
 * Usage:
 *   node scripts/export-pdf.js <input.html> <output.pdf>
 *
 * Example:
 *   node scripts/export-pdf.js resumes/Razorpay_PM_2026-09-07_v1/resume.html \
 *                              resumes/Razorpay_PM_2026-09-07_v1/resume.pdf
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function exportPDF(htmlPath, pdfPath) {
  const absoluteHtmlPath = path.resolve(htmlPath);
  const absolutePdfPath = path.resolve(pdfPath);

  if (!fs.existsSync(absoluteHtmlPath)) {
    console.error(`Error: HTML file not found: ${absoluteHtmlPath}`);
    process.exit(1);
  }

  console.log(`Rendering: ${absoluteHtmlPath}`);

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    const page = await browser.newPage();

    // Set viewport to A4 width for accurate rendering
    await page.setViewport({ width: 794, height: 1123 });

    await page.goto(`file://${absoluteHtmlPath}`, {
      waitUntil: 'networkidle0',
      timeout: 30000
    });

    // Wait for any fonts to load
    await page.evaluateHandle('document.fonts.ready');

    await page.pdf({
      path: absolutePdfPath,
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

    console.log(`✓ PDF exported: ${absolutePdfPath}`);

    // Print file size as a sanity check
    const stats = fs.statSync(absolutePdfPath);
    const sizeKB = (stats.size / 1024).toFixed(1);
    console.log(`  File size: ${sizeKB} KB`);

    if (stats.size < 10000) {
      console.warn('  Warning: PDF seems very small — check HTML content was injected correctly');
    }

  } finally {
    await browser.close();
  }
}

const args = process.argv.slice(2);
if (args.length < 2) {
  console.error('Usage: node scripts/export-pdf.js <input.html> <output.pdf>');
  process.exit(1);
}

exportPDF(args[0], args[1]).catch(err => {
  console.error('PDF export failed:', err.message);
  process.exit(1);
});
