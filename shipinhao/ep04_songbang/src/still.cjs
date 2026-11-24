// 用法: node still.cjs out_dir t1 t2 ...   （t 可写成 "id:4.4+1.2" 或秒数）
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
(async () => {
  const [out, ...ts] = process.argv.slice(2);
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  pg.on('console', m => console.log('[page]', m.text())); pg.on('pageerror', e => console.log('[err]', e.message));
  await pg.goto('file://' + path.resolve(__dirname, 'film.html'));
  await pg.evaluate(() => window.ready);
  for (const s of ts) {
    const t = await pg.evaluate(s => { const m = /^id:([\d.]+)([+-][\d.]+)?$/.exec(s); return m ? at(m[1]) + parseFloat(m[2] || 0) : parseFloat(s); }, s);
    await pg.evaluate(t => window.seek(t), t);
    const f = path.join(out, `f_${t.toFixed(2).padStart(7, '0')}.jpg`);
    await pg.screenshot({ path: f, type: 'jpeg', quality: 90 });
    console.log(s, '→', f);
  }
  await b.close();
})();
