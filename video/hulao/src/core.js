// 孤城·壹 毛德祖守虎牢 —— 渲染核心：工具、镜头、文字、通用图层。所有画面是时间 t 的纯函数。
'use strict';
const W = 1080, H = 1920;
let ctx, TL;
const IMG = {}, PL = {};
const C = {
  red: '#e0492f', redD: '#8a2416', redL: '#ff8f6a',          // 宋（晋）军：暖红
  xia: '#aab4bf', xiaD: '#6d7783', xiaL: '#d5dde5',          // 夏：冷灰
  wei: '#15181d', weiE: '#c9d3dc', weiM: '#39424d',          // 北魏：玄黑（配浅色描边）
  cream: '#f1e7d2', gold: '#d8b46a', goldD: '#9c7b3a', ink: '#0b0a09', dimtxt: 'rgba(241,231,210,0.78)',
};
const SERIF = '"Noto Serif SC"', SANS = '"Noto Sans SC"';

// ---------- 数学 ----------
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const sstep = x => { x = clamp(x); return x * x * (3 - 2 * x); };
const eio = x => { x = clamp(x); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const eout = x => 1 - Math.pow(1 - clamp(x), 3);
const prog = (t, a, b) => clamp((t - a) / (b - a));
const P = (t, a, d) => sstep((t - a) / d);            // 从 a 开始、历时 d 的平滑进度
const fadeIO = (t, a, b, fi = 0.5, fo = 0.5) => Math.min(sstep((t - a) / fi), sstep((b - t) / fo));
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const hash = (i, k = 0) => { let x = Math.sin(i * 127.1 + k * 311.7) * 43758.5453; return x - Math.floor(x); };

// ---------- 时间轴 ----------
const secOf = id => TL.secs[id];
const LN = (sec, k) => TL.lines.find(l => l.sec === sec && l.k === k);
const A = (sec, k) => LN(sec, k).start;
const E = (sec, k) => LN(sec, k).end;
// 按句首文字找时间锚点（稿子增删句子时画面不串位）
const _lt = new Map();
function LT(prefix) { if (!_lt.has(prefix)) { const l = TL.lines.find(l => l.text.startsWith(prefix)); if (!l) throw new Error('no line: ' + prefix); _lt.set(prefix, l); } return _lt.get(prefix); }
const AT = p => LT(p).start, ET = p => LT(p).end;

// ---------- 镜头关键帧 ----------
function kf(keys, t) {   // keys: [[t, ...vals]]，逐段 easeInOut；最后一维若标 log 则对数插值
  if (t <= keys[0][0]) return keys[0].slice(1);
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i], b = keys[i + 1];
    if (t <= b[0]) { const u = eio((t - a[0]) / (b[0] - a[0])); return a.slice(1).map((v, j) => j === a.length - 2 ? Math.exp(lerp(Math.log(v), Math.log(b[j + 1]), u)) : lerp(v, b[j + 1], u)); }
  }
  return keys[keys.length - 1].slice(1);
}

// ---------- 地图（经纬度，墨卡托；多张底图按镜头远近叠加） ----------
const merc = (lon, lat) => [(lon + 180) / 360, (1 - Math.asinh(Math.tan(lat * Math.PI / 180)) / Math.PI) / 2];
function mapCam(v) { const [mx, my] = merc(v[0], v[1]); return { mx, my, k: W / (v[2] / 360), wdeg: v[2], cy: v[3] === undefined ? H / 2 : v[3] }; }   // v: lon, lat, 视野宽(经度)[, 屏幕中心y]
const mw = (cam, lon, lat) => { const [x, y] = merc(lon, lat); return [W / 2 + (x - cam.mx) * cam.k, cam.cy + (y - cam.my) * cam.k]; };
function drawPlate(cam, name, alpha) {
  const p = PL[name]; if (!p || alpha <= 0.003) return;
  const s = cam.k / p.scale;                      // 屏幕像素 / 底图像素
  const sx = (cam.mx - p.mx0) * p.scale - W / 2 / s, sy = (cam.my - p.my0) * p.scale - cam.cy / s;
  ctx.save(); ctx.globalAlpha = alpha; ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(p.img, sx, sy, W / s, H / s, 0, 0, W, H); ctx.restore();
}
function drawMap(cam, dim = 0.12) {
  ctx.fillStyle = '#14161a'; ctx.fillRect(0, 0, W, H);
  drawPlate(cam, 'macro', 1);
  const need = cam.k / PL.macro.scale;             // >1 表示大底图已被放大
  drawPlate(cam, 'gz', sstep((need - 0.9) / 0.8));
  drawPlate(cam, 'hl', sstep((need - 0.9) / 0.8));
  drawPlate(cam, 'hulao', sstep((cam.k / PL.hl.scale - 1.0) / 1.2));
  ctx.fillStyle = `rgba(12,13,16,${dim})`; ctx.fillRect(0, 0, W, H);
}
// Catmull-Rom 平滑折线 -> 屏幕点列
function smooth(pts, n = 10) {
  const out = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
    for (let j = 0; j < n; j++) {
      const u = j / n, u2 = u * u, u3 = u2 * u;
      out.push([0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * u + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * u3),
      0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * u + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * u3)]);
    }
  }
  out.push(pts[pts.length - 1]); return out;
}
const _sm = new Map();
function smoothC(pts) { if (!_sm.has(pts)) _sm.set(pts, smooth(pts)); return _sm.get(pts); }
function pathLen(p) { let s = 0; const cum = [0]; for (let i = 1; i < p.length; i++) { s += Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]); cum.push(s); } return cum; }
function along(p, cum, d) { d = clamp(d, 0, cum[cum.length - 1]); let i = 1; while (i < cum.length - 1 && cum[i] < d) i++; const u = (d - cum[i - 1]) / Math.max(1e-6, cum[i] - cum[i - 1]); return [lerp(p[i - 1][0], p[i][0], u), lerp(p[i - 1][1], p[i][1], u), Math.atan2(p[i][1] - p[i - 1][1], p[i][0] - p[i - 1][0])]; }
// 画地理折线（lon/lat），frac 0..1 画到哪
function geoLine(cam, pts, o = {}) {
  const sp = smoothC(pts).map(q => mw(cam, q[0], q[1]));
  const cum = pathLen(sp), total = cum[cum.length - 1];
  const f0 = (o.from || 0) * total, f1 = (o.frac === undefined ? 1 : o.frac) * total;
  if (f1 <= f0) return null;
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath(); let started = false;
  for (let i = 0; i < sp.length; i++) {
    if (cum[i] < f0) continue; if (cum[i] > f1) break;
    if (!started) { const q = along(sp, cum, f0); ctx.moveTo(q[0], q[1]); started = true; }
    ctx.lineTo(sp[i][0], sp[i][1]);
  }
  const endp = along(sp, cum, f1); ctx.lineTo(endp[0], endp[1]);
  if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = o.blur || 14; }
  if (o.dash) ctx.setLineDash(o.dash);
  ctx.strokeStyle = o.color || '#fff'; ctx.lineWidth = o.w || 4; ctx.globalAlpha = o.alpha === undefined ? 1 : o.alpha; ctx.stroke();
  ctx.restore();
  return endp;
}

// ---------- 文字 ----------
function font(sz, fam = SANS, wt = 700) { return `${wt} ${sz}px ${fam}`; }
function text(s, x, y, o = {}) {
  ctx.save();
  ctx.font = font(o.size || 34, o.fam || SANS, o.wt || 700);
  ctx.textAlign = o.align || 'left'; ctx.textBaseline = o.base || 'middle';
  ctx.globalAlpha = (o.alpha === undefined ? 1 : o.alpha) * ctx.globalAlpha;
  if (o.ls) ctx.letterSpacing = o.ls + 'px';
  if (o.stroke !== 0) { ctx.lineJoin = 'round'; ctx.strokeStyle = o.strokeColor || 'rgba(8,7,6,0.88)'; ctx.lineWidth = o.stroke || Math.max(4, (o.size || 34) * 0.2); ctx.strokeText(s, x, y); }
  if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = o.blur || 16; }
  ctx.fillStyle = o.color || C.cream; ctx.fillText(s, x, y);
  ctx.restore();
}
function measure(s, sz, fam = SANS, wt = 700, ls = 0) { ctx.save(); ctx.font = font(sz, fam, wt); if (ls) ctx.letterSpacing = ls + 'px'; const w = ctx.measureText(s).width; ctx.restore(); return w; }
function wrap(s, maxw, sz, fam, wt) {   // 中文逐字折行，避免行首标点
  const lines = []; let cur = '';
  for (const ch of s) {
    if (measure(cur + ch, sz, fam, wt) > maxw && cur && !'，。；：？！、”》）…—'.includes(ch)) { lines.push(cur); cur = ch; } else cur += ch;
  }
  if (cur) lines.push(cur); return lines;
}
function rrect(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
// 标签（带底板），跟随单位
function label(s, x, y, o = {}) {
  const sz = o.size || 30, padx = o.padx || 14, w = measure(s, sz, o.fam || SANS, o.wt || 700) + padx * 2, h = sz + 16;
  const ax = o.align === 'left' ? x : o.align === 'right' ? x - w : x - w / 2;
  ctx.save(); ctx.globalAlpha *= (o.alpha === undefined ? 1 : o.alpha);
  rrect(ax, y - h / 2, w, h, 6); ctx.fillStyle = o.bg || 'rgba(12,10,8,0.78)'; ctx.fill();
  if (o.bar) { ctx.fillStyle = o.bar; ctx.fillRect(ax, y - h / 2, 5, h); }
  if (o.border) { ctx.strokeStyle = o.border; ctx.lineWidth = 1.5; rrect(ax, y - h / 2, w, h, 6); ctx.stroke(); }
  text(s, ax + padx + (o.bar ? 2 : 0), y + 1, { size: sz, color: o.color || C.cream, stroke: 0, fam: o.fam, wt: o.wt });
  ctx.restore(); return w;
}
function leader(x0, y0, x1, y1, color = 'rgba(244,234,214,0.8)', w = 2) { ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke(); ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x0, y0, 4, 0, 7); ctx.fill(); ctx.restore(); }
function arrow(x0, y0, x1, y1, o = {}) {
  const f = o.frac === undefined ? 1 : o.frac; if (f <= 0) return;
  const xe = lerp(x0, x1, f), ye = lerp(y0, y1, f), a = Math.atan2(y1 - y0, x1 - x0), hw = o.head || 18;
  ctx.save(); ctx.globalAlpha *= (o.alpha === undefined ? 1 : o.alpha); ctx.strokeStyle = ctx.fillStyle = o.color || C.cream; ctx.lineWidth = o.w || 6; ctx.lineCap = 'round';
  if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = 14; }
  if (o.dash) ctx.setLineDash(o.dash);
  ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(xe - Math.cos(a) * hw * 0.6, ye - Math.sin(a) * hw * 0.6); ctx.stroke(); ctx.setLineDash([]);
  ctx.beginPath(); ctx.moveTo(xe, ye); ctx.lineTo(xe - Math.cos(a - 0.45) * hw, ye - Math.sin(a - 0.45) * hw); ctx.lineTo(xe - Math.cos(a + 0.45) * hw, ye - Math.sin(a + 0.45) * hw); ctx.closePath(); ctx.fill();
  ctx.restore();
}
function curveArrow(pts, o = {}) {  // 屏幕坐标点列（平滑），带箭头
  const sp = smooth(pts, 14), cum = pathLen(sp), tot = cum[cum.length - 1], f = (o.frac === undefined ? 1 : clamp(o.frac)) * tot; if (f <= 2) return;
  ctx.save(); ctx.globalAlpha *= (o.alpha === undefined ? 1 : o.alpha); ctx.strokeStyle = ctx.fillStyle = o.color || C.cream; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.lineWidth = o.w || 7;
  if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = 16; }
  if (o.dash) ctx.setLineDash(o.dash);
  const hw = o.head || 22; ctx.beginPath(); ctx.moveTo(sp[0][0], sp[0][1]);
  for (let i = 1; i < sp.length && cum[i] < f - hw * 0.5; i++) ctx.lineTo(sp[i][0], sp[i][1]);
  ctx.stroke(); ctx.setLineDash([]);
  const e = along(sp, cum, f), a = e[2];
  ctx.beginPath(); ctx.moveTo(e[0], e[1]); ctx.lineTo(e[0] - Math.cos(a - 0.42) * hw, e[1] - Math.sin(a - 0.42) * hw); ctx.lineTo(e[0] - Math.cos(a + 0.42) * hw, e[1] - Math.sin(a + 0.42) * hw); ctx.closePath(); ctx.fill();
  ctx.restore(); return e;
}
// 城市标记
function city(cam, lon, lat, name, o = {}) {
  const [x, y] = mw(cam, lon, lat); const a = o.alpha === undefined ? 1 : o.alpha; if (a <= 0) return [x, y];
  ctx.save(); ctx.globalAlpha *= a;
  const r = o.r || 9, col = o.color || C.cream;
  if (o.pulse) { const u = (o.pulse % 1.6) / 1.6; ctx.strokeStyle = col; ctx.globalAlpha = a * (1 - u) * 0.8; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(x, y, r + u * 46, 0, 7); ctx.stroke(); ctx.globalAlpha = a; }
  ctx.fillStyle = 'rgba(10,9,8,0.9)'; ctx.beginPath(); ctx.arc(x, y, r + 3, 0, 7); ctx.fill();
  ctx.fillStyle = col; if (o.sq) { ctx.fillRect(x - r, y - r, 2 * r, 2 * r); } else { ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); }
  if (o.capital) { ctx.strokeStyle = col; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.arc(x, y, r + 8, 0, 7); ctx.stroke(); }
  const dx = o.dx === undefined ? 0 : o.dx, dy = o.dy === undefined ? -r - 26 : o.dy;
  text(name, x + dx, y + dy, { size: o.size || 34, fam: SERIF, wt: 900, align: o.align || 'center', color: o.tcolor || C.cream });
  if (o.sub) text(o.sub, x + dx, dy < 0 ? y + r + (o.capital ? 32 : 24) : y + dy + (o.size || 34) * 0.95, { size: 24, fam: SANS, wt: 500, align: o.align || 'center', color: 'rgba(244,234,214,0.85)' });
  ctx.restore(); return [x, y];
}

// ---------- 通用叠加层 ----------
let _grain = null, _vig = null;
function post(t) {
  if (!_vig) {
    _vig = document.createElement('canvas'); _vig.width = W / 4; _vig.height = H / 4; const g = _vig.getContext('2d');
    const gr = g.createRadialGradient(W / 8, H / 8 * 0.95, H / 4 * 0.28, W / 8, H / 8, H / 4 * 0.74); gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(0,0,0,0.58)'); g.fillStyle = gr; g.fillRect(0, 0, W / 4, H / 4);
    _grain = []; for (let k = 0; k < 6; k++) { const c = document.createElement('canvas'); c.width = 540; c.height = 960; const gg = c.getContext('2d'); const id = gg.createImageData(540, 960); const r = rng(77 + k); for (let i = 0; i < id.data.length; i += 4) { const v = 128 + (r() - 0.5) * 110; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255; } gg.putImageData(id, 0, 0); _grain.push(c); }
  }
  ctx.save(); ctx.imageSmoothingEnabled = true; ctx.drawImage(_vig, 0, 0, W, H);
  ctx.globalCompositeOperation = 'overlay'; ctx.globalAlpha = 0.045; ctx.drawImage(_grain[0], 0, 0, W, H); ctx.restore();   // 静态颗粒：给暗部渐变做抖动，不随时间变化（低码率下更干净）
}
// 顶部与底部压暗带，保证字幕/引文可读
function bands(top = 0.5, bot = 0.5) {
  top *= 0.85; bot *= 0.66;
  let g = ctx.createLinearGradient(0, 0, 0, 640); g.addColorStop(0, `rgba(8,7,6,${top})`); g.addColorStop(1, 'rgba(8,7,6,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, 640);
  g = ctx.createLinearGradient(0, 1180, 0, H); g.addColorStop(0, 'rgba(8,7,6,0)'); g.addColorStop(0.45, `rgba(8,7,6,${bot})`); g.addColorStop(1, `rgba(8,7,6,${bot + 0.2})`); ctx.fillStyle = g; ctx.fillRect(0, 1180, W, H - 1180);
}
// 字幕：安全区 y≈1390–1470（避开视频号底部信息区与右侧按钮）
const SUB_Y = 1432;
function subtitles(t) {
  for (const l of TL.lines) {
    if (t < l.start - 0.05 || t > l.end + 0.25 || l.kind !== 'n' || l.sec === 's12' || l.nosub) continue;
    for (let i = 0; i < l.chunks.length; i++) {
      const c = l.chunks[i]; const last = i === l.chunks.length - 1;
      if (t >= c.start - 0.03 && t < (last ? l.end + 0.22 : c.end - 0.03)) {
        const a = Math.min(sstep((t - c.start + 0.03) / 0.12), last ? sstep((l.end + 0.22 - t) / 0.15) : 1);
        let s = c.text.replace(/[，。；：、]$/, '').replace(/——$/, '');
        text(s, 512, SUB_Y, { size: 48, wt: 700, align: 'center', alpha: a, stroke: 9, strokeColor: 'rgba(6,5,4,0.92)' });
      }
    }
  }
}
// 史书原文卡：文言逐字显现，随后的白话解释期间保持
const QUOTE_Y = 250;
function quotes(t) {
  for (let n = 0; n < TL.lines.length; n++) {
    const l = TL.lines[n]; if (l.kind !== 'q') continue;
    const nx = TL.lines[n + 1]; const hold = (nx && nx.kind === 'n' && nx.sec === l.sec) ? Math.min(nx.end, l.end + clamp(l.text.length * 0.3, 2.6, 7.5)) : l.end + 0.9;
    const t0 = l.start - 0.45; if (t < t0 || t > hold + 0.4) continue;
    const a = Math.min(sstep((t - t0) / 0.4), sstep((hold + 0.4 - t) / 0.4));
    const sz = l.text.length > 34 ? 46 : 52, lh = sz * 1.5, maxw = 850;
    const lines = wrap(l.text, maxw, sz, SERIF, 900);
    const h = lines.length * lh + 96, y0 = QUOTE_Y;
    ctx.save(); ctx.globalAlpha = a;
    rrect(60, y0, 960, h, 10); ctx.fillStyle = 'rgba(14,11,8,0.84)'; ctx.fill();
    ctx.fillStyle = C.gold; ctx.fillRect(60, y0, 8, h);
    ctx.strokeStyle = 'rgba(220,183,108,0.35)'; ctx.lineWidth = 1.5; rrect(60, y0, 960, h, 10); ctx.stroke();
    // 逐字显现
    const total = l.text.length; const shown = (t - l.start) / (l.end - l.start) * total + 1.5;
    let idx = 0;
    for (let i = 0; i < lines.length; i++) {
      let x = 106; const y = y0 + 52 + i * lh + lh * 0.32;
      for (const ch of lines[i]) {
        const ca = clamp(shown - idx, 0, 1); const wch = measure(ch, sz, SERIF, 900);
        if (ca > 0) text(ch, x, y, { size: sz, fam: SERIF, wt: 900, color: t > l.end + 0.3 ? '#e9dcc0' : '#fff3d6', stroke: 0, alpha: ca });
        x += wch; idx++;
      }
    }
    text('原文', 960, y0 + 34, { size: 24, wt: 700, color: C.gold, stroke: 0, align: 'right', fam: SANS });
    if (l.src) text('—— ' + l.src, 990, y0 + h - 30, { size: 28, fam: SERIF, wt: 700, color: C.gold, stroke: 0, align: 'right' });
    ctx.restore();
  }
}
const SEC_IDS = ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10'];
// 左上角章节条
function chip(t) {
  let cur = null; for (const id of SEC_IDS) { const s = TL.secs[id]; if (!s.title) continue; if (t >= s.body - 0.2 && t < s.end) cur = s; }
  if (!cur) return; const a = Math.min(sstep((t - cur.body + 0.2) / 0.6), sstep((cur.end - t) / 0.5)) * 0.95;
  ctx.save(); ctx.globalAlpha = a;
  ctx.fillStyle = C.red; ctx.fillRect(60, 178, 44, 44); text(cur.num, 82, 201, { size: 28, fam: SERIF, wt: 900, align: 'center', stroke: 0, color: '#fff' });
  text(cur.title, 118, 201, { size: 30, fam: SERIF, wt: 900, color: C.cream, stroke: 6 });
  ctx.restore();
}
// 章节卡
function chapterCard(t) {
  for (const id of SEC_IDS) {
    const s = TL.secs[id]; if (!s.card) continue; const [a, b] = s.card; if (t < a - 0.5 || t > b + 0.1) continue;
    const al = Math.min(sstep((t - (a - 0.5)) / 0.5), sstep((b + 0.1 - t) / 0.7));
    ctx.save(); ctx.fillStyle = `rgba(9,8,7,${al})`; ctx.fillRect(0, 0, W, H);
    const u = (t - a) / (b - a); ctx.globalAlpha = Math.min(sstep((t - a + 0.1) / 0.5), sstep((b - 0.1 - t) / 0.45));
    const cy = 860;
    ctx.fillStyle = C.red; const lw = 300 * eout(u * 2.2); ctx.fillRect(W / 2 - lw / 2, cy - 150, lw, 4);
    text(s.num, W / 2, cy - 70, { size: 76, fam: SERIF, wt: 900, color: C.red, align: 'center', stroke: 0 });
    text(s.title, W / 2, cy + 60 - 10 * (1 - eout(u * 2)), { size: 92, fam: SERIF, wt: 900, color: C.cream, align: 'center', stroke: 0, ls: 6 });
    ctx.fillStyle = 'rgba(244,234,214,0.5)'; ctx.fillRect(W / 2 - lw / 2, cy + 160, lw, 2);
    ctx.restore();
  }
}
// 军事标识：方框兵牌（步兵×/骑兵/）
function unitBox(x, y, o = {}) {
  const w = o.w || 86, h = o.h || 56, col = o.color || C.red;
  ctx.save(); ctx.globalAlpha *= (o.alpha === undefined ? 1 : o.alpha); ctx.translate(x, y);
  ctx.shadowColor = 'rgba(0,0,0,0.7)'; ctx.shadowBlur = 10; ctx.fillStyle = o.fill || 'rgba(14,12,10,0.86)'; ctx.fillRect(-w / 2, -h / 2, w, h); ctx.shadowBlur = 0;
  ctx.strokeStyle = col; ctx.lineWidth = 4; ctx.strokeRect(-w / 2, -h / 2, w, h); ctx.lineWidth = 3;
  if (o.type === 'cav') { ctx.beginPath(); ctx.moveTo(-w / 2, h / 2); ctx.lineTo(w / 2, -h / 2); ctx.stroke(); }
  else if (o.type === 'inf') { ctx.beginPath(); ctx.moveTo(-w / 2, -h / 2); ctx.lineTo(w / 2, h / 2); ctx.moveTo(-w / 2, h / 2); ctx.lineTo(w / 2, -h / 2); ctx.stroke(); }
  else if (o.type === 'navy') { ctx.beginPath(); ctx.moveTo(-w * 0.3, -h * 0.12); ctx.quadraticCurveTo(0, h * 0.42, w * 0.3, -h * 0.12); ctx.closePath(); ctx.fillStyle = col; ctx.fill(); ctx.beginPath(); ctx.moveTo(0, -h * 0.36); ctx.lineTo(0, -h * 0.1); ctx.stroke(); }
  ctx.restore();
  if (o.name) text(o.name, x, y + h / 2 + 26, { size: o.size || 30, fam: SERIF, wt: 900, align: 'center', color: o.tcolor || C.cream, alpha: o.alpha });
  if (o.sub) text(o.sub, x, y + h / 2 + 60, { size: 24, wt: 500, align: 'center', color: 'rgba(244,234,214,0.9)', alpha: o.alpha });
}
function cross(x, y, r, col, w = 6, alpha = 1) { ctx.save(); ctx.globalAlpha *= alpha; ctx.strokeStyle = col; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x - r, y - r); ctx.lineTo(x + r, y + r); ctx.moveTo(x + r, y - r); ctx.lineTo(x - r, y + r); ctx.stroke(); ctx.restore(); }
function compass(x, y, a = 1) { ctx.save(); ctx.globalAlpha *= a * 0.85; ctx.translate(x, y); ctx.fillStyle = C.cream; ctx.beginPath(); ctx.moveTo(0, -26); ctx.lineTo(9, 8); ctx.lineTo(0, 2); ctx.lineTo(-9, 8); ctx.closePath(); ctx.fill(); ctx.restore(); text('北', x, y + 30, { size: 22, wt: 700, align: 'center', alpha: a * 0.85 }); }
function scaleBar(x, y, px, labelStr, a = 1) { ctx.save(); ctx.globalAlpha *= a * 0.9; ctx.strokeStyle = C.cream; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(x, y - 8); ctx.lineTo(x, y); ctx.lineTo(x + px, y); ctx.lineTo(x + px, y - 8); ctx.stroke(); ctx.restore(); text(labelStr, x + px / 2, y - 22, { size: 24, wt: 500, align: 'center', alpha: a * 0.9 }); }
function note(s, x, y, a = 1, align = 'left') { text(s, x, y, { size: 24, wt: 500, color: 'rgba(244,234,214,0.82)', alpha: a, align, stroke: 5 }); }
