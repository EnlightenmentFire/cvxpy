// 用法: node stills.mjs <outdir> t1 t2 ...   （t 可以是秒，也可以是 cue 名[+偏移]，如 q_die+1.5）
import { createRequire } from 'module'; const { chromium } = createRequire(import.meta.url)('playwright');
import fs from 'fs'; import path from 'path'; import { fileURLToPath } from 'url';
const here = path.dirname(fileURLToPath(import.meta.url));
const [out, ...ts] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
const tl = JSON.parse(fs.readFileSync(path.join(here, '../build/timeline.json')));
const cue = {}; tl.lines.forEach(l => { if (l.cue) cue[l.cue] = l.start; });
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
p.on('pageerror', e => console.error('PAGEERR', e.message));
await p.goto('file://' + path.join(here, 'render/index.html'));
await p.evaluate(() => window.ready);
for (const s of ts) {
  let t; const m = s.match(/^([a-z_0-9]+?)([+-][\d.]+)?$/i);
  if (!isNaN(parseFloat(s)) && isFinite(s)) t = parseFloat(s);
  else t = cue[m[1]] + parseFloat(m[2] || 0);
  await p.evaluate(t => window.renderFrame(t), t);
  const f = path.join(out, `${s.replace(/[^\w.+-]/g, '_')}.png`);
  await p.screenshot({ path: f });
  console.log(f, t.toFixed(2));
}
await b.close();
