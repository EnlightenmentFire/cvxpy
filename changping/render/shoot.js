// Usage: node shoot.js still <outdir> <spec> [spec...]   spec = seconds | lineId[@frac]
//        node shoot.js frames <outfile.mp4> <startFrame> <endFrame> [fps]
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs'); const { spawn } = require('child_process');
(async () => {
  const [mode, out, ...rest] = process.argv.slice(2);
  const browser = await chromium.launch({ args: ['--disable-web-security', '--allow-file-access-from-files', '--force-color-profile=srgb', '--font-render-hinting=none'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => { console.error('PAGEERROR', e.message); });
  page.on('console', m => { if (m.type() === 'error') console.error('CONSOLE', m.text()); });
  await page.goto('file://' + path.join(__dirname, 'index.html'));
  await page.evaluate(() => window.ready);
  const total = await page.evaluate(() => window.TOTAL);
  if (mode === 'still') {
    fs.mkdirSync(out, { recursive: true });
    for (const spec of rest) {
      let t; if (/^s\d+\.\d+/.test(spec)) { const [id, fr] = spec.split('@'); t = await page.evaluate(([id, fr]) => window.A_(id) + (window.Z_(id) - window.A_(id)) * fr, [id, parseFloat(fr || '0.5')]); } else t = parseFloat(spec);
      const err = await page.evaluate(t => { try { window.renderFrame(t); return null; } catch (e) { return e.stack; } }, t);
      if (err) { console.error('ERR', spec, err); continue; }
      const f = path.join(out, spec.replace(/[@.]/g, '_') + '.jpg'); await page.locator('#c').screenshot({ path: f, type: 'jpeg', quality: 90 }); console.log(spec, t.toFixed(2), f);
    }
  } else {
    const fps = parseInt(rest[2] || '30'); const f0 = parseInt(rest[0]), f1 = parseInt(rest[1]);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '12', '-pix_fmt', 'yuv420p', '-r', String(fps), out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let f = f0; f < f1; f++) {
      const err = await page.evaluate(t => { try { window.renderFrame(t); return null; } catch (e) { return e.stack; } }, f / fps);
      if (err) { console.error('ERR frame', f, err); process.exit(1); }
      const buf = await page.locator('#c').screenshot({ type: 'jpeg', quality: 96 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if ((f - f0) % 300 === 0) console.log(out, f, ((Date.now() - t0) / 1000).toFixed(0) + 's');
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  console.log('total', total); await browser.close();
})();
