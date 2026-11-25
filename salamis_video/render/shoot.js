// node shoot.js still <outdir> <t|v:key[@frac]> ...     |   node shoot.js frames <out.mp4> <f0> <f1> [fps]
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs'); const { spawn } = require('child_process');
(async () => {
  const [mode, out, ...rest] = process.argv.slice(2);
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--force-color-profile=srgb', '--font-render-hinting=none'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('PAGEERROR', e.message));
  page.on('console', m => { if (m.type() === 'error') console.error('CONSOLE', m.text()); });
  await page.goto('file://' + path.join(__dirname, 'index.html'));
  await page.evaluate(() => window.ready);
  const grab = async (t) => {
    const err = await page.evaluate(t => { try { window.renderFrame(t); return null; } catch (e) { return e.stack; } }, t);
    if (err) throw new Error(err);
    const url = await page.evaluate(() => document.getElementById('c').toDataURL('image/jpeg', 0.95));
    return Buffer.from(url.split(',')[1], 'base64');
  };
  if (mode === 'still') {
    fs.mkdirSync(out, { recursive: true });
    for (const spec of rest) {
      let t;
      if (spec.startsWith('v:')) { const [k, fr] = spec.slice(2).split('@'); t = await page.evaluate(([k, fr]) => { const l = window.LINES.find(l => l.v === k); return l.t0 + (l.t1 - l.t0) * fr; }, [k, parseFloat(fr || '0.6')]); }
      else t = parseFloat(spec);
      try { const b = await grab(t); const f = path.join(out, spec.replace(/[:@.]/g, '_') + '.jpg'); fs.writeFileSync(f, b); console.log(spec, t.toFixed(2), f); } catch (e) { console.error('ERR', spec, e.message.split('\n').slice(0, 3).join(' | ')); }
    }
  } else {
    const fps = parseInt(rest[2] || '25'); const f0 = parseInt(rest[0]), f1 = parseInt(rest[1]);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-pix_fmt', 'yuv420p', '-r', String(fps), out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let f = f0; f < f1; f++) {
      const b = await grab(f / fps);
      if (!ff.stdin.write(b)) await new Promise(r => ff.stdin.once('drain', r));
      if ((f - f0) % 500 === 0) console.log(out, f, ((Date.now() - t0) / 1000).toFixed(0) + 's');
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  await browser.close();
})();
