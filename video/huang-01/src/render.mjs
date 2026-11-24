// 整片逐帧渲染：N 个页面并行截图 -> build/frames/%06d.jpg
// 用法: node render.mjs [startSec] [endSec] [workers]
import { createRequire } from 'module'; const { chromium } = createRequire(import.meta.url)('playwright');
import fs from 'fs'; import path from 'path'; import { fileURLToPath } from 'url';
const here = path.dirname(fileURLToPath(import.meta.url));
const tl = JSON.parse(fs.readFileSync(path.join(here, '../build/timeline.json')));
const FPS = 30, t0 = parseFloat(process.argv[2] || 0), t1 = parseFloat(process.argv[3] || tl.duration), NW = parseInt(process.argv[4] || 4);
const f0 = Math.round(t0 * FPS), f1 = Math.round(t1 * FPS);
const out = path.join(here, '../build/frames'); fs.mkdirSync(out, { recursive: true });
const b = await chromium.launch({ args: ['--disable-gpu-vsync', '--font-render-hinting=none'] });
const started = Date.now(); let done = 0;
await Promise.all([...Array(NW).keys()].map(async w => {
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  p.on('pageerror', e => { console.error('PAGEERR', e.message); process.exit(1); });
  await p.goto('file://' + path.join(here, 'render/index.html'));
  await p.evaluate(() => window.ready);
  for (let f = f0 + w; f < f1; f += NW) {
    await p.evaluate(t => window.renderFrame(t), f / FPS);
    await p.screenshot({ path: path.join(out, String(f - f0).padStart(6, '0') + '.jpg'), type: 'jpeg', quality: 96 });
    if (++done % 300 === 0) console.log(done, '/', f1 - f0, ((Date.now() - started) / 1000).toFixed(0) + 's');
  }
}));
await b.close();
console.log('frames', f1 - f0, 'in', ((Date.now() - started) / 1000).toFixed(0) + 's');
