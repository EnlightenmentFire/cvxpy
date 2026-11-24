// 逐帧渲染：node render.cjs <outDir> <startFrame> <endFrame(不含)> [fps=30]
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
(async () => {
  const [out, a, b, fpsS] = process.argv.slice(2); const fps = +(fpsS || 30);
  fs.mkdirSync(out, { recursive: true });
  const br = await chromium.launch({ args: ['--disable-gpu', '--font-render-hinting=none'] });
  const pg = await br.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  pg.on('pageerror', e => console.log('[err]', e.message));
  await pg.goto('file://' + path.resolve(__dirname, 'film.html'));
  await pg.evaluate(() => window.ready);
  const total = await pg.evaluate(() => window.TOTAL);
  const end = Math.min(+b, Math.ceil(total * fps));
  const t0 = Date.now();
  for (let f = +a; f < end; f++) {
    await pg.evaluate(t => window.seek(t), f / fps);
    await pg.screenshot({ path: path.join(out, String(f).padStart(6, '0') + '.jpg'), type: 'jpeg', quality: 94 });
    if ((f - a) % 300 === 0) console.log(`[${a}] frame ${f}/${end}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  await br.close(); console.log(`[${a}] done ${(Date.now() - t0) / 1000}s`);
})();
