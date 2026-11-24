// 中间片不加颗粒、近无损；颗粒和最终码率在 build.sh 的成片压制里做。
// 用法：
//   node render.js stills 3.5,42,97          → build/stills/still_XXXX.png（2x 像素密度，给人看）
//   node render.js video [workers]           → build/video_silent.mp4（1080x1920，30fps）
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const FPS = 30;
const ROOT = __dirname;
const URL = 'file://' + path.join(ROOT, 'video.html');

async function openPage(browser, scale) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: scale });
  page.on('pageerror', e => { console.error('PAGE ERROR', e.message); process.exitCode = 1; });
  page.on('console', m => { if (m.type() === 'error') console.error('CONSOLE', m.text()); });
  await page.goto(URL);
  await page.evaluate(() => window.initEngine());
  return page;
}

async function stills(times) {
  const browser = await chromium.launch();
  const page = await openPage(browser, 2);
  fs.mkdirSync(path.join(ROOT, 'build/stills'), { recursive: true });
  for (const t of times) {
    await page.evaluate(t => window.seek(t), t);
    const f = path.join(ROOT, 'build/stills', `still_${String(Math.round(t * 10)).padStart(5, '0')}.png`);
    await page.screenshot({ path: f });
    console.log(f);
  }
  await browser.close();
}

async function worker(idx, f0, f1) {
  const browser = await chromium.launch();
  const page = await openPage(browser, 1);
  const out = path.join(ROOT, `build/part_${idx}.mp4`);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-vf', 'format=yuv420p', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '8', '-g', '60', '-threads', '1', '-r', String(FPS),
    '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error('ffmpeg ' + c))));
  for (let f = f0; f < f1; f++) {
    await page.evaluate(t => window.seek(t), f / FPS);
    const buf = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (idx === 0 && (f - f0) % 300 === 0) console.log(`worker0 frame ${f - f0}/${f1 - f0}`);
  }
  ff.stdin.end(); await done; await browser.close();
  return out;
}

async function video(nw) {
  const browser = await chromium.launch();
  const page = await openPage(browser, 1);
  const dur = await page.evaluate(() => TL.duration);
  await browser.close();
  const total = Math.ceil(dur * FPS);
  const per = Math.ceil(total / nw / 60) * 60;        // 分段落在关键帧间隔上
  const jobs = [];
  for (let i = 0; i < nw; i++) { const a = i * per, b = Math.min(total, (i + 1) * per); if (a < b) jobs.push(worker(i, a, b)); }
  const parts = await Promise.all(jobs);
  const list = path.join(ROOT, 'build/parts.txt');
  fs.writeFileSync(list, parts.map(p => `file '${p}'`).join('\n'));
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list, '-c', 'copy', path.join(ROOT, 'build/video_silent.mp4')]);
  console.log('frames', total, 'duration', dur);
}

(async () => {
  const [mode, arg] = process.argv.slice(2);
  if (mode === 'stills') await stills(arg.split(',').map(Number));
  else if (mode === 'video') await video(parseInt(arg || '4'));
  else console.log('usage: node render.js stills t1,t2 | video [workers]');
})();
