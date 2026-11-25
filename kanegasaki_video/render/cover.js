// cover: node cover.js <out.png> [w h]
const { chromium } = require('playwright'); const path = require('path');
(async () => {
  const out = process.argv[2]; const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(__dirname, 'index.html')); await page.evaluate(() => window.ready);
  await page.evaluate(() => window.renderCover());
  const url = await page.evaluate(() => document.getElementById('c').toDataURL('image/png'));
  require('fs').writeFileSync(out, Buffer.from(url.split(',')[1], 'base64')); await browser.close();
})();
