// 低清晰度巡检：node review2.js out.jpg t1 t2 ... （每张缩到 360x640 拼成一排）
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path'); const http = require('http');
const ROOT = path.resolve(__dirname, '..');
(async () => {
  const srv = http.createServer((q, r) => { const p = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); fs.readFile(p, (e, d) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200); r.end(d); } }); }); await new Promise(r => srv.listen(0, r));
  const br = await chromium.launch({ args: ['--js-flags=--max-old-space-size=4096'] }); const pg = await br.newPage({ viewport: { width: 1080, height: 1920 } });
  pg.on('pageerror', e => console.error('PAGEERR:', e.message));
  await pg.goto(`http://localhost:${srv.address().port}/src/film.html?sw=1`); await pg.waitForFunction('window.READY||window.BOOTERR', null, { timeout: 120000 });
  const err = await pg.evaluate('window.BOOTERR'); if (err) { console.error(err); process.exit(1); }
  const out = process.argv[2], ts = process.argv.slice(3).map(Number);
  const b64 = await pg.evaluate(([ts]) => { const w = 432, h = 768, c = document.createElement('canvas'); c.width = w * ts.length; c.height = h; const g = c.getContext('2d'); g.imageSmoothingQuality = 'high'; const errs = [];
    ts.forEach((t, i) => { try { render(t); } catch (e) { errs.push(t + ': ' + e.message); } g.drawImage(document.getElementById('c'), i * w, 0, w, h); g.fillStyle = '#ff0'; g.font = '20px sans-serif'; g.fillText(String(t), i * w + 6, 22); });
    return [c.toDataURL('image/jpeg', 0.86).slice(23), errs]; }, [ts]);
  if (b64[1].length) console.error('ERR', b64[1]);
  fs.writeFileSync(out, Buffer.from(b64[0], 'base64')); await br.close(); srv.close();
})();
