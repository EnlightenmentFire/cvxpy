// 开发用：node src/frames.cjs <outdir> <t1,t2,...|id+offset,...> [scale]   例: node src/frames.cjs build/dev 12.5,r3+1.2
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
(async () => {
  const [,, out, list, scale = '0.5'] = process.argv; fs.mkdirSync(out, { recursive: true });
  const TL = JSON.parse(fs.readFileSync(path.join(__dirname, '../build/timeline.json')));
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: +scale });
  p.on('console', m => console.log('console:', m.text())); p.on('pageerror', e => console.log('pageerror:', e.message));
  await p.goto('file://' + path.join(__dirname, 'film.html')); await p.evaluate(() => window.ready);
  for (const it of list.split(',')) {
    let t = parseFloat(it); const m = it.match(/^([a-z]+\d*)([+-][\d.]+)?$/);
    if (m && TL.segs.find(s => s.id === m[1])) t = TL.segs.find(s => s.id === m[1]).s + parseFloat(m[2] || 0);
    await p.evaluate(tt => window.setTime(tt), t);
    await p.screenshot({ path: path.join(out, `f_${it.replace(/[^a-z0-9.+-]/g, '_')}.png`) }); console.log(it, t.toFixed(2));
  }
  await b.close();
})();
