// usage: node tools/still.js out_prefix t1 t2 ...   (or id@frac cue syntax not supported; pass seconds)
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [prefix, ...ts] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.log('[page]', m.text()); });
  p.on('pageerror', e => console.log('[pageerror]', e.message));
  await p.goto('file://' + path.resolve('web/index.html'));
  await p.evaluate(() => document.fonts.ready);
  await p.evaluate(async () => { for (const f of ['900 40px Song', '500 40px Hei', '40px Brush', '40px Hand']) await document.fonts.load(f, '傻子瓜子7'); });
  for (const t of ts) {
    await p.evaluate(tt => ENGINE.render(tt), parseFloat(t));
    await p.screenshot({ path: `${prefix}_${String(t).replace('.', '_')}.jpg`, type: 'jpeg', quality: 88 });
  }
  await b.close();
})();
