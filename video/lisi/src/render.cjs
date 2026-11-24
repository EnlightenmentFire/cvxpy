// 分段渲染：node src/render.cjs <startFrame> <endFrame> <out.mp4>   （帧 → JPEG → ffmpeg 管道）
const { chromium } = require('playwright'); const path = require('path'); const { spawn } = require('child_process');
(async () => {
  const [,, f0, f1, out] = process.argv; const FPS = 30;
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '12', '-pix_fmt', 'yuv420p', '-color_range', 'tv', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const b = await chromium.launch({ args: ['--disable-gpu', '--font-render-hinting=none'] });
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  p.on('pageerror', e => { console.error('pageerror:', e.message); process.exit(2); });
  await p.goto('file://' + path.join(__dirname, 'film.html')); await p.evaluate(() => window.ready);
  const t0 = Date.now();
  for (let f = +f0; f < +f1; f++) {
    await p.evaluate(t => window.setTime(t), f / FPS);
    const buf = await p.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if ((f - f0) % 300 === 0) console.log(`[${f0}-${f1}] frame ${f} (${((Date.now() - t0) / 1000 / (f - f0 + 1)).toFixed(3)} s/frame)`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close();
})();
