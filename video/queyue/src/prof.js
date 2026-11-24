const { chromium } = require('playwright'); const path = require('path'); const http = require('http'); const fs = require('fs');
const ROOT = path.resolve(__dirname, '..');
(async () => {
  const srv = http.createServer((q, r) => { const p = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); fs.readFile(p, (e, d) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200); r.end(d); } }); }); await new Promise(r => srv.listen(0, r));
  const br = await chromium.launch(); const pg = await br.newPage({ viewport: { width: 1080, height: 1920 } });
  await pg.goto(`http://localhost:${srv.address().port}/src/film.html?sw=1`); await pg.waitForFunction('window.READY||window.BOOTERR', null, { timeout: 120000 });
  const t = parseFloat(process.argv[2]);
  const res = await pg.evaluate(([t]) => {
    const out = {}; const wrap = n => { const f = window[n]; window[n] = function () { const a = performance.now(); const r = f.apply(this, arguments); out[n] = (out[n] || 0) + performance.now() - a; return r; }; };
    ['drawTac', 'drawFlow', 'drawShips', 'drawRiders', 'drawFormation', 'drawMissiles', 'drawMacro', 'drawRivers', 'bands', 'quotes', 'subtitles', 'post', 'chapterCard', 'drawSpearDiagram', 'sceneKangzu'].forEach(wrap);
    const a = performance.now(); render(t); out.total = performance.now() - a; const b = performance.now(); document.getElementById('c').toDataURL('image/jpeg', 0.95); out.jpeg = performance.now() - b; return out;
  }, [t]);
  console.log(t, Object.entries(res).map(([k, v]) => k + '=' + v.toFixed(0)).join(' '));
  await br.close(); srv.close();
})();
