const { chromium } = require('playwright'); const fs = require('fs'); const path = require('path'); const http = require('http');
const ROOT = path.resolve(__dirname, '..');
const srv = http.createServer((q, r) => { const p = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); fs.readFile(p, (e, d) => { if (e) { r.writeHead(404); r.end(); } else { r.writeHead(200); r.end(d); } }); });
srv.listen(0, async () => {
  const br = await chromium.launch(); const pg = await br.newPage({ viewport: { width: 1080, height: 1920 } });
  await pg.goto(`http://localhost:${srv.address().port}/src/film.html`); await pg.waitForFunction('window.READY||window.BOOTERR');
  const b64 = await pg.evaluate(() => window.coverJPEG()); fs.writeFileSync(process.argv[2], Buffer.from(b64, 'base64'));
  await br.close(); srv.close(); console.log('cover ok');
});
