// 启动与总调度
'use strict';
async function boot() {
  const cv = document.getElementById('c'); ctx = cv.getContext('2d', { alpha: false, willReadFrequently: location.search.includes('sw=1') });
  const j = async u => (await fetch(u)).json();
  TL = await j('timeline.json?' + Date.now());
  for (const id of Object.keys(TL.secs)) { }
  const load = (k, u) => new Promise((res, rej) => { const im = new Image(); im.onload = () => { IMG[k] = im; res(); }; im.onerror = rej; im.src = u; });
  for (const nm of ['macro', 'gz', 'hl', 'hulao']) { PL[nm] = await j(`../assets/${nm}.json`); await load(nm, `../assets/${nm}.jpg`); PL[nm].img = IMG[nm]; }
  // 区域底图边缘羽化，叠在大底图上不露接缝
  for (const nm of ['gz', 'hl', 'hulao']) {
    const p = PL[nm], c = document.createElement('canvas'); c.width = p.w; c.height = p.h; const g = c.getContext('2d'); g.drawImage(p.img, 0, 0);
    g.globalCompositeOperation = 'destination-out'; const F = Math.round(Math.min(p.w, p.h) * 0.07);
    const ed = (x0, y0, x1, y1, rx, ry, rw, rh) => { const gr = g.createLinearGradient(x0, y0, x1, y1); gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = gr; g.fillRect(rx, ry, rw, rh); };
    ed(0, 0, F, 0, 0, 0, F, p.h); ed(p.w, 0, p.w - F, 0, p.w - F, 0, F, p.h); ed(0, 0, 0, F, 0, 0, p.w, F); ed(0, p.h, 0, p.h - F, 0, p.h - F, p.w, F);
    p.img = c;
  }
  const S = '孤城毛德祖守虎牢';
  for (const f of ['900 40px "Noto Serif SC"', '700 40px "Noto Serif SC"', '700 40px "Noto Sans SC"', '500 40px "Noto Sans SC"']) await document.fonts.load(f, S);
  await document.fonts.ready;
  window.READY = true;
}
const ORDER = [['cold', sceneCold], ['title', sceneTitle], ['s1', sceneS1], ['s2', sceneS2], ['s3', sceneS3], ['s4', sceneS4], ['s5', sceneS5], ['s6', sceneS6], ['s7', sceneS7], ['s8', sceneS8], ['s9', sceneS9], ['s10', sceneS10], ['s11', sceneS11], ['s12', sceneS12], ['end', sceneEnd]];
function render(t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.shadowBlur = 0; ctx.setLineDash([]); ctx.filter = 'none';
  const S = TL.secs; let fn = sceneCold;
  for (const [id, f] of ORDER) { const st = id === 'cold' ? 0 : S[id].start; if (t >= st) fn = f; }
  fn(t);
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.shadowBlur = 0; ctx.setLineDash([]); ctx.filter = 'none';
  chip(t); quotes(t); subtitles(t); chapterCard(t); post(t);
  if (t < 0.8) { ctx.fillStyle = `rgba(9,8,7,${1 - t / 0.8})`; ctx.fillRect(0, 0, W, H); }
}
window.frameJPEG = (t, q) => { render(t); return document.getElementById('c').toDataURL('image/jpeg', q || 0.93).slice(23); };
