// Render the user manual to PDF (needs a running Erisma server and Playwright for Node):
//   erisma serve &
//   node tools/build_manual_pdf.js http://127.0.0.1:8000 docs
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const base = process.argv[2] || 'http://127.0.0.1:8000';
const out = process.argv[3] || 'docs';
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  const page = await b.newPage();
  for (const [lang, name] of [['el', 'Erisma_Egxeiridio.pdf'], ['en', 'Erisma_Manual.pdf']]) {
    await page.goto(`${base}/manual?lang=${lang}`);
    await page.pdf({ path: path.join(out, name), format: 'A4', printBackground: true,
      displayHeaderFooter: true, headerTemplate: '<span></span>',
      footerTemplate: '<div style="font-size:8px;width:100%;text-align:center;color:#888">Erisma — <span class="pageNumber"></span> / <span class="totalPages"></span></div>',
      margin: { top: '14mm', bottom: '16mm', left: '14mm', right: '14mm' } });
    console.log(path.join(out, name));
  }
  await b.close();
})();
