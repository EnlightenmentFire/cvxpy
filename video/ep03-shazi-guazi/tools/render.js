// node tools/render.js <outdir> [t0] [t1] [workers]   -> <outdir>/seg_XX.mp4 (video only, high quality intermediate)
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path'), fs = require('fs');
const FPS = 30;
(async () => {
  const out = process.argv[2] || 'build/render';
  fs.mkdirSync(out, { recursive: true });
  const TL = JSON.parse(fs.readFileSync(process.env.TLJSON || 'build/timeline.json'));
  const t0 = parseFloat(process.argv[3] || '0'), t1 = parseFloat(process.argv[4] || TL.total);
  const NW = parseInt(process.argv[5] || '4');
  const f0 = Math.round(t0 * FPS), f1 = Math.round(t1 * FPS), per = Math.ceil((f1 - f0) / NW);
  const browser = await chromium.launch({ args: ['--disable-gpu', '--force-color-profile=srgb'] });
  let done = 0; const T = Date.now();
  await Promise.all(Array.from({ length: NW }, async (_, w) => {
    const a = f0 + w * per, b = Math.min(f1, a + per); if (a >= b) return;
    const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
    page.on('pageerror', e => console.log('[pageerror]', e.message));
    await page.goto('file://' + path.resolve('web/index.html'));
    await page.evaluate(async () => { await document.fonts.ready; for (const f of ['900 40px Song', '500 40px Hei', '40px Brush', '40px Hand']) await document.fonts.load(f, '傻子瓜子7'); });
    await page.evaluate(() => ENGINE.render(0)); await page.waitForTimeout(300);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '12', '-pix_fmt', 'yuv420p', '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-vf', 'scale=in_range=pc:out_range=tv:out_color_matrix=bt709', '-threads', '1', `${out}/seg_${String(w).padStart(2, '0')}.mp4`], { stdio: ['pipe', 'inherit', 'inherit'] });
    const closed = new Promise(r => ff.on('close', r));
    for (let f = a; f < b; f++) {
      await page.evaluate(t => ENGINE.render(t), f / FPS);
      const buf = await page.screenshot({ type: 'jpeg', quality: 96 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (++done % 300 === 0) console.log(`${done}/${f1 - f0} frames, ${((Date.now() - T) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end(); await closed; await page.close();
  }));
  await browser.close();
  fs.writeFileSync(`${out}/list.txt`, Array.from({ length: NW }, (_, w) => `file 'seg_${String(w).padStart(2, '0')}.mp4'`).filter((_, w) => fs.existsSync(`${out}/seg_${String(w).padStart(2, '0')}.mp4`)).join('\n'));
  console.log('rendered', f1 - f0, 'frames in', ((Date.now() - T) / 1000).toFixed(0), 's');
})();
