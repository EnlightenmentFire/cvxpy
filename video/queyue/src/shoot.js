// 用法：node shoot.js stills t1 t2 ...   |  node shoot.js range start end outdir [fps]
const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path'); const http = require('http');
const ROOT = path.resolve(__dirname, '..');
function serve() { return new Promise(res => { const mime = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.jpg': 'image/jpeg', '.ttf': 'font/ttf' }; const srv = http.createServer((q, r) => { const p = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); fs.readFile(p, (e, d) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200, { 'Content-Type': mime[path.extname(p)] || 'application/octet-stream' }); r.end(d); } }); }); srv.listen(0, () => res(srv)); }); }
(async () => {
  const srv = await serve(); const port = srv.address().port;
  const br = await chromium.launch({ args: ['--disable-web-security', '--ignore-gpu-blocklist', '--js-flags=--max-old-space-size=4096'] });
  const pg = await br.newPage({ viewport: { width: 1080, height: 1920 } });
  pg.on('console', m => { if (m.type() === 'error') console.error('PAGE:', m.text()); }); pg.on('pageerror', e => console.error('PAGEERR:', e.message));
  await pg.goto(`http://localhost:${port}/src/film.html${process.env.SW === '0' ? '' : '?sw=1'}`);
  await pg.waitForFunction('window.READY||window.BOOTERR', null, { timeout: 120000 });
  const err = await pg.evaluate('window.BOOTERR'); if (err) { console.error(err); process.exit(1); }
  const mode = process.argv[2];
  if (mode === 'stills') {
    const out = process.env.OUT || path.join(ROOT, 'out/stills'); fs.mkdirSync(out, { recursive: true });
    for (const a of process.argv.slice(3)) { const t = parseFloat(a); const t0 = Date.now(); const b64 = await pg.evaluate(([t]) => window.frameJPEG(t, 0.92), [t]); fs.writeFileSync(path.join(out, `t${t.toFixed(1).padStart(6, '0')}.jpg`), Buffer.from(b64, 'base64')); console.log('still', t, Date.now() - t0, 'ms'); }
  } else if (mode === 'bench') {
    for (const a of process.argv.slice(3)) { const t = parseFloat(a); await pg.evaluate(([t]) => window.frameJPEG(t, 0.95).length, [t]); const t0 = Date.now(); for (let k = 0; k < 6; k++) await pg.evaluate(([t]) => window.frameJPEG(t, 0.95).length, [t + k / 30]); console.log('bench', t, ((Date.now() - t0) / 6).toFixed(0), 'ms/frame'); }
  } else if (mode === 'range') {
    const [f0, f1, outdir] = [parseInt(process.argv[3]), parseInt(process.argv[4]), process.argv[5]]; const fps = 30; fs.mkdirSync(outdir, { recursive: true });
    const t0 = Date.now();
    for (let f = f0; f < f1; f++) { const b64 = await pg.evaluate(([t]) => window.frameJPEG(t, 0.95), [f / fps]); fs.writeFileSync(path.join(outdir, `f${String(f).padStart(6, '0')}.jpg`), Buffer.from(b64, 'base64')); if ((f - f0) % 300 === 0) console.log(`[${f0}] ${f - f0}/${f1 - f0} ${((Date.now() - t0) / 1000).toFixed(0)}s`); }
  }
  await br.close(); srv.close();
})();
