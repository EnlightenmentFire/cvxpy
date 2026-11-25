const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
(async () => { const b = await chromium.launch({ args: ['--allow-file-access-from-files', '--force-color-profile=srgb'] }); const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => console.log('ERR', e.message)); await p.goto('file://' + path.join(__dirname, 'index.html')); await p.evaluate(() => window.ready);
  await p.evaluate(() => window.renderCover()); const u = await p.evaluate(() => document.getElementById('c').toDataURL('image/png'));
  fs.writeFileSync(process.argv[2], Buffer.from(u.split(',')[1], 'base64')); await b.close(); })();
