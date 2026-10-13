/**
 * Prints an HTML file to an A4 PDF with a page-numbered footer.
 * Used by docs/panduan/build_manual.py:
 *
 *   node e2e/print-pdf.mjs <input.html> <output.pdf> "<footer text>"
 */
import { chromium } from '@playwright/test'
import { pathToFileURL } from 'node:url'

const [input, output, footer = ''] = process.argv.slice(2)
if (!input || !output) {
  console.error('usage: node e2e/print-pdf.mjs <input.html> <output.pdf> [footer]')
  process.exit(2)
}

const escapeHtml = (text) =>
  text.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' })[c])

const browser = await chromium.launch()
try {
  const page = await browser.newPage()
  await page.goto(pathToFileURL(input).href, { waitUntil: 'load' })
  await page.pdf({
    path: output,
    format: 'A4',
    printBackground: true,
    preferCSSPageSize: true,
    displayHeaderFooter: true,
    headerTemplate: '<span></span>',
    footerTemplate:
      '<div style="width:100%;text-align:center;font-family:Calibri,Arial,sans-serif;' +
      `font-size:8px;color:#595959">${escapeHtml(footer)} - halaman ` +
      '<span class="pageNumber"></span> dari <span class="totalPages"></span></div>',
  })
} finally {
  await browser.close()
}
