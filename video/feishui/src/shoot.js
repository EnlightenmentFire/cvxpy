// 用法：node shoot.js stills t1 t2 ...  |  node shoot.js range f0 f1 outdir  |  node shoot.js bench t
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path'); const http = require('http');
const ROOT = path.resolve(__dirname, '..'); const FPS = 25;
function serve() { return new Promise(res => { const mime = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.jpg': 'image/jpeg', '.png': 'image/png', '.ttf': 'font/ttf' }; const srv = http.createServer((q, r) => { const p = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); fs.readFile(p, (e, d) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200, { 'Content-Type': mime[path.extname(p)] || 'application/octet-stream' }); r.end(d); } }); }); srv.listen(0, () => res(srv)); }); }
(async () => {
  const srv = await serve(); const port = srv.address().port;
  const br = await chromium.launch({ args: ['--disable-web-security', '--js-flags=--max-old-space-size=4096'] });
  const pg = await br.newPage({ viewport: { width: 1080, height: 1920 } });
  pg.on('console', m => { if (m.type() === 'error') console.error('PAGE:', m.text()); }); pg.on('pageerror', e => console.error('PAGEERR:', e.message));
  await pg.goto(`http://localhost:${port}/src/film.html`);
  await pg.waitForFunction('window.READY||window.BOOTERR', null, { timeout: 180000 });
  const err = await pg.evaluate('window.BOOTERR'); if (err) { console.error(err); process.exit(1); }
  const mode = process.argv[2];
  if (mode === 'stills') {
    const out = process.env.OUT || path.join(ROOT, 'cache/stills'); fs.mkdirSync(out, { recursive: true });
    for (const a of process.argv.slice(3)) { const t = parseFloat(a); const b64 = await pg.evaluate(([t]) => window.frameJPEG(t, 0.9), [t]); fs.writeFileSync(path.join(out, `t${t.toFixed(1).padStart(6, '0')}.jpg`), Buffer.from(b64, 'base64')); }
    console.log('stills done');
  } else if (mode === 'bench') {
    for (const a of process.argv.slice(3)) { const t = parseFloat(a); await pg.evaluate(([t]) => window.frameJPEG(t).length, [t]); const t0 = Date.now(); for (let k = 0; k < 8; k++) await pg.evaluate(([t]) => window.frameJPEG(t).length, [t + k / FPS]); console.log('bench', t, ((Date.now() - t0) / 8).toFixed(0), 'ms/frame'); }
  } else if (mode === 'range') {
    const [f0, f1, outdir] = [parseInt(process.argv[3]), parseInt(process.argv[4]), process.argv[5]]; fs.mkdirSync(outdir, { recursive: true });
    const t0 = Date.now();
    for (let f = f0; f < f1; f++) { const p = path.join(outdir, `f${String(f).padStart(6, '0')}.jpg`); if (fs.existsSync(p)) continue; const b64 = await pg.evaluate(([t]) => window.frameJPEG(t, 0.93), [f / FPS]); fs.writeFileSync(p + '.tmp', Buffer.from(b64, 'base64')); fs.renameSync(p + '.tmp', p); if ((f - f0) % 500 === 0) console.log(`[${f0}] ${f - f0}/${f1 - f0} ${((Date.now() - t0) / 1000).toFixed(0)}s`); }
    console.log('range done', f0, f1);
  }
  await br.close(); srv.close();
})();
