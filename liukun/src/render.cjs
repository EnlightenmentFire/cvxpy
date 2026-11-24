// usage: node render.mjs stills 12.5,40,...   |  node render.mjs range <t0> <t1> <out.mp4>
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs'), path = require('path');
const dir = __dirname;
(async () => {
const mode = process.argv[2];
const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--disable-web-security'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
page.on('console', m => console.log('[page]', m.text())); page.on('pageerror', e => console.log('[pageerror]', e.message));
await page.goto('file://' + path.join(dir, 'index.html')); await page.evaluate(() => window.ready);
const grab = (t, q = 0.95) => page.evaluate(([t, q]) => { renderAt(t); return document.getElementById('c').toDataURL('image/jpeg', q).split(',')[1]; }, [t, q]);
if (mode === 'stills') {
  const out = path.join(dir, '..', 'out', 'stills'); fs.mkdirSync(out, { recursive: true });
  for (const s of process.argv[3].split(',')) { const t = parseFloat(s); const t0 = Date.now(); const b = await grab(t, 0.93); fs.writeFileSync(path.join(out, `t${t.toFixed(1).padStart(6, '0')}.jpg`), Buffer.from(b, 'base64')); console.log('still', t, Date.now() - t0, 'ms'); }
} else if (mode === 'range') {
  const t0 = parseFloat(process.argv[3]), t1 = parseFloat(process.argv[4]), outf = process.argv[5], fps = 30;
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-c:v', 'mjpeg', '-r', String(fps), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '12', '-pix_fmt', 'yuv420p', '-r', String(fps), outf], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n0 = Math.round(t0 * fps), n1 = Math.round(t1 * fps); const st = Date.now();
  for (let n = n0; n < n1; n++) { const b = Buffer.from(await grab(n / fps, 0.96), 'base64'); if (!ff.stdin.write(b)) await new Promise(r => ff.stdin.once('drain', r)); if ((n - n0) % 300 === 0) console.log(outf, n - n0, '/', n1 - n0, ((Date.now() - st) / 1000).toFixed(0) + 's'); }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
}
await browser.close();
})();
