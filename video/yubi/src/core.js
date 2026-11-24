// 玉璧 —— 渲染核心：工具、时间轴、镜头、地图、文字、通用图层。所有画面都是时间 t 的纯函数。
'use strict';
const W = 1080, H = 1920;
let ctx, TL, MACRO, LOCAL, RIV, FEN;
const IMG = {};
const C = {
  red: '#e2452e', redD: '#8f2014', redL: '#ff8a66', redG: 'rgba(226,69,46,0.7)',          // 西魏（韦孝宽一方）：暖红
  xuan: '#141a21', xuanL: '#9fb0c3', xuanM: '#5d6d80', xuanG: 'rgba(150,170,195,0.55)',     // 东魏：冷黑（玄色），配冷钢色描边
  liang: '#8c8470',
  cream: '#f4ead6', gold: '#dcb76c', goldD: '#9c7b3a', ink: '#0c0a08', water: '#7fb0c2', snow: '#eef2f4',
};
const SERIF = '"Noto Serif SC"', SANS = '"Noto Sans SC"';

// ---------- 数学 ----------
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const sstep = x => { x = clamp(x); return x * x * (3 - 2 * x); };
const eio = x => { x = clamp(x); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const eout = x => 1 - Math.pow(1 - clamp(x), 3);
const ein = x => Math.pow(clamp(x), 3);
const prog = (t, a, b) => clamp((t - a) / (b - a));
const P = (t, a, d) => sstep((t - a) / d);
const fadeIO = (t, a, b, fi = 0.5, fo = 0.5) => Math.min(sstep((t - a) / fi), sstep((b - t) / fo));
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const hash = (i, k = 0) => { let x = Math.sin(i * 127.1 + k * 311.7) * 43758.5453; return x - Math.floor(x); };

// ---------- 时间轴 ----------
const LN = (sec, k) => TL.lines.find(l => l.sec === sec && l.k === k);
const A = (sec, k) => LN(sec, k).start;
const E = (sec, k) => LN(sec, k).end;
// 一句话里第 j 个字幕块的开始（用于把画面动作卡在说到某个词的时候）
const CK = (sec, k, j) => { const l = LN(sec, k); return l.chunks[Math.min(j, l.chunks.length - 1)].start; };

function kf(keys, t) {   // keys: [[t, ...vals]]；最后一维按对数插值（缩放）
  if (t <= keys[0][0]) return keys[0].slice(1);
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i], b = keys[i + 1];
    if (t <= b[0]) { const u = eio((t - a[0]) / (b[0] - a[0])); return a.slice(1).map((v, j) => j === a.length - 2 ? Math.exp(lerp(Math.log(v), Math.log(b[j + 1]), u)) : lerp(v, b[j + 1], u)); }
  }
  return keys[keys.length - 1].slice(1);
}

// ---------- 墨卡托 ----------
const merc = (lon, lat) => [(lon + 180) / 360, (1 - Math.asinh(Math.tan(lat * Math.PI / 180)) / Math.PI) / 2];
// 大尺度地图
function mp(lon, lat) { const [X, Y] = merc(lon, lat); return [(X - MACRO.mx0) * MACRO.scale, (Y - MACRO.my0) * MACRO.scale]; }
function macCam(v) { const [px, py] = mp(v[0], v[1]); return { px, py, s: W / (v[2] * MACRO.scale / 360), kind: 'mac' }; }   // v: lon, lat, 视野宽(经度)
const mw = (cam, lon, lat) => { const [x, y] = mp(lon, lat); return [W / 2 + (x - cam.px) * cam.s, H / 2 + (y - cam.py) * cam.s]; };
function drawMacro(cam, dim = 0.25) {
  ctx.fillStyle = '#16181a'; ctx.fillRect(0, 0, W, H);
  const sw = W / cam.s, sh = H / cam.s;
  ctx.drawImage(IMG.macro, cam.px - sw / 2, cam.py - sh / 2, sw, sh, 0, 0, W, H);
  ctx.fillStyle = `rgba(12,13,14,${dim})`; ctx.fillRect(0, 0, W, H);
}
// 玉璧局部地图（真实高程）。v: lon, lat, 视野宽(公里)
const LKM = () => 40075 * Math.cos(35.56 * Math.PI / 180) / LOCAL.scale;     // 每像素公里数（底图像素）
function lp(lon, lat) { const [X, Y] = merc(lon, lat); return [(X - LOCAL.mx0) * LOCAL.scale, (Y - LOCAL.my0) * LOCAL.scale]; }
function locCam(v) { const [px, py] = lp(v[0], v[1]); return { px, py, s: W / (v[2] / LKM()), kind: 'loc', km: v[2] }; }
const lw = (cam, lon, lat) => { const [x, y] = lp(lon, lat); return [W / 2 + (x - cam.px) * cam.s, H / 2 + (y - cam.py) * cam.s]; };
// 公里偏移（以玉璧为原点，x 东 y 北）→ 屏幕
const YB = [110.9418, 35.5631];
const kmLL = (dx, dy) => [YB[0] + dx / (111.32 * Math.cos(YB[1] * Math.PI / 180)), YB[1] + dy / 110.57];
const lk = (cam, dx, dy) => lw(cam, ...kmLL(dx, dy));
// 季节：0=初秋 1=初冬；snow 0..1
function drawLocal(cam, o = {}) {
  ctx.fillStyle = '#1b1c17'; ctx.fillRect(0, 0, W, H);
  const sw = W / cam.s, sh = H / cam.s;
  ctx.drawImage(IMG.local, cam.px - sw / 2, cam.py - sh / 2, sw, sh, 0, 0, W, H);
  const season = o.season || 0;
  ctx.save();
  // 秋：暖褐；冬：去饱和、偏冷
  ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = `rgba(${Math.round(lerp(236, 196, season))},${Math.round(lerp(214, 204, season))},${Math.round(lerp(176, 206, season))},1)`; ctx.fillRect(0, 0, W, H);
  if (season > 0) { ctx.globalCompositeOperation = 'saturation'; ctx.globalAlpha = 0.38 * season; ctx.fillStyle = '#808080'; ctx.fillRect(0, 0, W, H); }
  ctx.restore();
  if (o.snow > 0) {
    ctx.save(); ctx.globalAlpha = o.snow * 0.85;
    const k = IMG.snow.width / LOCAL.w; ctx.drawImage(IMG.snow, (cam.px - sw / 2) * k, (cam.py - sh / 2) * k, sw * k, sh * k, 0, 0, W, H); ctx.restore();
  }
  ctx.fillStyle = `rgba(10,11,12,${o.dim === undefined ? 0.2 : o.dim})`; ctx.fillRect(0, 0, W, H);
}
// Catmull-Rom 平滑
function smooth(pts, n = 8) {
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
function smoothC(pts, n = 8) { if (!_sm.has(pts)) _sm.set(pts, smooth(pts, n)); return _sm.get(pts); }
function pathLen(p) { let s = 0; const cum = [0]; for (let i = 1; i < p.length; i++) { s += Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]); cum.push(s); } return cum; }
function along(p, cum, d) { d = clamp(d, 0, cum[cum.length - 1]); let i = 1; while (i < cum.length - 1 && cum[i] < d) i++; const u = (d - cum[i - 1]) / Math.max(1e-6, cum[i] - cum[i - 1]); return [lerp(p[i - 1][0], p[i][0], u), lerp(p[i - 1][1], p[i][1], u), Math.atan2(p[i][1] - p[i - 1][1], p[i][0] - p[i - 1][0])]; }
// 屏幕点列描线（可画一部分）
function strokePts(sp, o = {}) {
  const cum = pathLen(sp), total = cum[cum.length - 1];
  const f0 = (o.from || 0) * total, f1 = (o.frac === undefined ? 1 : o.frac) * total;
  if (f1 <= f0 + 0.5) return null;
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.beginPath(); let started = false;
  for (let i = 0; i < sp.length; i++) {
    if (cum[i] < f0) continue; if (cum[i] > f1) break;
    if (!started) { const q = along(sp, cum, f0); ctx.moveTo(q[0], q[1]); started = true; }
    ctx.lineTo(sp[i][0], sp[i][1]);
  }
  const e = along(sp, cum, f1); if (!started) ctx.moveTo(e[0], e[1]); ctx.lineTo(e[0], e[1]);
  if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = o.blur || 14; }
  if (o.dash) ctx.setLineDash(o.dash);
  ctx.strokeStyle = o.color || '#fff'; ctx.lineWidth = o.w || 4; ctx.globalAlpha *= o.alpha === undefined ? 1 : o.alpha; ctx.stroke();
  ctx.restore(); return e;
}
function geoLine(cam, pts, o = {}) {
  const f = cam.kind === 'loc' ? lw : mw;
  return strokePts(smoothC(pts, o.n || 8).map(q => f(cam, q[0], q[1])), o);
}
function drawRivers(cam, a = 1, hi = '') {
  const w = clamp(cam.s * 0.09 * 360 / MACRO.scale * 1000, 2.2, 7);
  for (const [nm, lines] of Object.entries(RIV)) {
    const main = nm === '黄河', fen = nm === '汾水', minor = !['黄河', '汾水', '渭水', '洛水', '漳水', '淮水', '汉水'].includes(nm);
    for (const pts of lines) geoLine(cam, pts, { color: main ? '#c8b27a' : '#7fa6b3', w: main ? w * 1.35 : (minor ? w * 0.55 : w * 0.8), alpha: a * (minor ? 0.5 : 0.85) * (hi && hi !== nm ? 0.55 : 1), glow: main ? 'rgba(220,190,120,0.35)' : (hi === nm ? 'rgba(130,200,230,0.8)' : null), blur: 10, n: 3 });
  }
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
const _mc = new Map();
function measure(s, sz, fam = SANS, wt = 700, ls = 0) {
  const key = s + '|' + sz + fam + wt + ls; if (_mc.has(key)) return _mc.get(key);
  ctx.save(); ctx.font = font(sz, fam, wt); if (ls) ctx.letterSpacing = ls + 'px'; const w = ctx.measureText(s).width; ctx.restore(); _mc.set(key, w); return w;
}
function wrap(s, maxw, sz, fam, wt) {
  const lines = []; let cur = '';
  for (const ch of s) {
    if (measure(cur + ch, sz, fam, wt) > maxw && cur && !'，。；：？！、”》）…—'.includes(ch)) { lines.push(cur); cur = ch; } else cur += ch;
  }
  if (cur) lines.push(cur); return lines;
}
// 竖排文字（自右向左成列）。chars 每列字数
function vtext(s, x, y, o = {}) {
  const sz = o.size || 44, lh = o.lh || sz * 1.18, colw = o.colw || sz * 1.45, per = o.per || 99;
  const cols = []; let cur = '';
  for (const ch of s) { if ('，。、；：！'.includes(ch)) { if (o.punct) cur += ch; if (!o.punct) { cols.push(cur); cur = ''; } continue; } cur += ch; if (cur.length >= per) { cols.push(cur); cur = ''; } }
  if (cur) cols.push(cur);
  let idx = 0; const shown = o.shown === undefined ? 1e9 : o.shown;
  cols.forEach((c, ci) => {
    for (let j = 0; j < c.length; j++) {
      const a = clamp(shown - idx); idx++;
      if (a <= 0) continue;
      const hl = o.hl && o.hl(c[j], ci, j);
      text(c[j], x - ci * colw, y + j * lh, { size: sz, fam: o.fam || SERIF, wt: o.wt || 900, align: 'center', color: hl ? (o.hlColor || C.redL) : (o.color || C.cream), alpha: a * (o.alpha === undefined ? 1 : o.alpha), stroke: o.stroke === undefined ? 0 : o.stroke, glow: hl ? 'rgba(255,138,102,0.6)' : o.glow, blur: 14 });
    }
  });
  return cols;
}
function rrect(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
function label(s, x, y, o = {}) {
  const sz = o.size || 30, padx = o.padx || 14, w = measure(s, sz, o.fam || SANS, o.wt || 700) + padx * 2, h = sz + 16;
  const ax = o.align === 'left' ? x : o.align === 'right' ? x - w : x - w / 2;
  ctx.save(); ctx.globalAlpha *= (o.alpha === undefined ? 1 : o.alpha);
  rrect(ax, y - h / 2, w, h, 6); ctx.fillStyle = o.bg || 'rgba(12,10,8,0.8)'; ctx.fill();
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
function curveArrow(pts, o = {}) {
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
// 城市标记（地图任一种镜头）
function city(cam, lon, lat, name, o = {}) {
  const [x, y] = (cam.kind === 'loc' ? lw : mw)(cam, lon, lat); const a = o.alpha === undefined ? 1 : o.alpha; if (a <= 0) return [x, y];
  ctx.save(); ctx.globalAlpha *= a;
  const r = o.r || 9, col = o.color || C.cream;
  if (o.pulse) { const u = (o.pulse % 1.6) / 1.6; ctx.strokeStyle = col; ctx.globalAlpha = a * (1 - u) * 0.8; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(x, y, r + u * 46, 0, 7); ctx.stroke(); ctx.globalAlpha = a; }
  ctx.fillStyle = 'rgba(10,9,8,0.9)'; ctx.beginPath(); ctx.arc(x, y, r + 3, 0, 7); ctx.fill();
  ctx.fillStyle = col; if (o.sq) ctx.fillRect(x - r, y - r, 2 * r, 2 * r); else { ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); }
  if (o.capital) { ctx.strokeStyle = col; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.arc(x, y, r + 8, 0, 7); ctx.stroke(); }
  const dx = o.dx === undefined ? 0 : o.dx, dy = o.dy === undefined ? -r - 26 : o.dy;
  if (name) text(name, x + dx, y + dy, { size: o.size || 34, fam: SERIF, wt: 900, align: o.align || 'center', color: o.tcolor || C.cream });
  if (o.sub) text(o.sub, x + dx, y + dy + (o.size || 34) * 0.95, { size: 24, fam: SANS, wt: 500, align: o.align || 'center', color: 'rgba(244,234,214,0.85)' });
  ctx.restore(); return [x, y];
}
// 玉璧：一颗钉子（红色楔形标志）
function nail(x, y, s = 1, a = 1, glow = 0.6) {
  ctx.save(); ctx.globalAlpha *= a; ctx.translate(x, y); ctx.scale(s, s);
  ctx.shadowColor = `rgba(255,120,90,${glow})`; ctx.shadowBlur = 24;
  ctx.fillStyle = C.red; ctx.beginPath(); ctx.moveTo(0, 6); ctx.lineTo(-9, -30); ctx.lineTo(9, -30); ctx.closePath(); ctx.fill();
  ctx.fillRect(-16, -40, 32, 11); ctx.shadowBlur = 0;
  ctx.strokeStyle = '#ffd2c2'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(-16, -40); ctx.lineTo(16, -40); ctx.stroke();
  ctx.restore();
}
function unitBox(x, y, o = {}) {
  const w = o.w || 86, h = o.h || 56, col = o.color || C.red;
  ctx.save(); ctx.globalAlpha *= (o.alpha === undefined ? 1 : o.alpha); ctx.translate(x, y);
  ctx.shadowColor = 'rgba(0,0,0,0.7)'; ctx.shadowBlur = 10; ctx.fillStyle = o.fill || 'rgba(14,12,10,0.88)'; ctx.fillRect(-w / 2, -h / 2, w, h); ctx.shadowBlur = 0;
  ctx.strokeStyle = col; ctx.lineWidth = 4; ctx.strokeRect(-w / 2, -h / 2, w, h); ctx.lineWidth = 3;
  if (o.type === 'cav') { ctx.beginPath(); ctx.moveTo(-w / 2, h / 2); ctx.lineTo(w / 2, -h / 2); ctx.stroke(); }
  else if (o.type === 'inf') { ctx.beginPath(); ctx.moveTo(-w / 2, -h / 2); ctx.lineTo(w / 2, h / 2); ctx.moveTo(-w / 2, h / 2); ctx.lineTo(w / 2, -h / 2); ctx.stroke(); }
  else if (o.type === 'hq') { ctx.fillStyle = col; ctx.fillRect(-w / 2, -h / 2, 6, h + 24); }
  ctx.restore();
  if (o.name) text(o.name, x, y + h / 2 + 26, { size: o.size || 30, fam: SERIF, wt: 900, align: 'center', color: o.tcolor || C.cream, alpha: o.alpha });
  if (o.sub) text(o.sub, x, y + h / 2 + 60, { size: 24, wt: 500, align: 'center', color: 'rgba(244,234,214,0.9)', alpha: o.alpha });
}
function cross(x, y, r, col, w = 6, alpha = 1) { ctx.save(); ctx.globalAlpha *= alpha; ctx.strokeStyle = col; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x - r, y - r); ctx.lineTo(x + r, y + r); ctx.moveTo(x + r, y - r); ctx.lineTo(x - r, y + r); ctx.stroke(); ctx.restore(); }
function compass(x, y, a = 1) { ctx.save(); ctx.globalAlpha *= a * 0.85; ctx.translate(x, y); ctx.fillStyle = C.cream; ctx.beginPath(); ctx.moveTo(0, -26); ctx.lineTo(9, 8); ctx.lineTo(0, 2); ctx.lineTo(-9, 8); ctx.closePath(); ctx.fill(); ctx.restore(); text('北', x, y + 30, { size: 22, wt: 700, align: 'center', alpha: a * 0.85 }); }
function scaleBar(x, y, px, s, a = 1) { ctx.save(); ctx.globalAlpha *= a * 0.9; ctx.strokeStyle = C.cream; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(x, y - 8); ctx.lineTo(x, y); ctx.lineTo(x + px, y); ctx.lineTo(x + px, y - 8); ctx.stroke(); ctx.restore(); text(s, x + px / 2, y - 22, { size: 24, wt: 500, align: 'center', alpha: a * 0.9 }); }
function note(s, x, y, a = 1, align = 'left', sz = 24) { text(s, x, y, { size: sz, wt: 500, color: 'rgba(244,234,214,0.82)', alpha: a, align, stroke: 5 }); }
// 兵点（密集小方块），两色交替
function dots(list, c1, c2, ps = 3) {
  const p1 = new Path2D(), p2 = new Path2D();
  for (let i = 0; i < list.length; i++) { const [x, y] = list[i]; if (x < -6 || x > W + 6 || y < -6 || y > H + 6) continue; (i & 1 ? p2 : p1).rect(x - ps / 2, y - ps / 2, ps, ps); }
  ctx.fillStyle = 'rgba(0,0,0,0.45)'; ctx.save(); ctx.translate(1.2, 1.5); ctx.fill(p1); ctx.fill(p2); ctx.restore();
  ctx.fillStyle = c1; ctx.fill(p1); ctx.fillStyle = c2; ctx.fill(p2);
}

// ---------- 通用叠加层 ----------
let _grain = null, _vig = null;
function post(t) {
  if (!_vig) {
    _vig = document.createElement('canvas'); _vig.width = W / 4; _vig.height = H / 4; const g = _vig.getContext('2d');
    const gr = g.createRadialGradient(W / 8, H / 8 * 0.95, H / 4 * 0.27, W / 8, H / 8, H / 4 * 0.74); gr.addColorStop(0, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(0,0,0,0.55)'); g.fillStyle = gr; g.fillRect(0, 0, W / 4, H / 4);
    _grain = []; for (let k = 0; k < 2; k++) { const c = document.createElement('canvas'); c.width = 540; c.height = 960; const gg = c.getContext('2d'); const id = gg.createImageData(540, 960); const r = rng(77 + k); for (let i = 0; i < id.data.length; i += 4) { const v = 128 + (r() - 0.5) * 100; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255; } gg.putImageData(id, 0, 0); _grain.push(c); }
  }
  ctx.save(); ctx.drawImage(_vig, 0, 0, W, H);
  // 颗粒每 0.5 秒才换一次（克制，也省码率）
  ctx.globalCompositeOperation = 'overlay'; ctx.globalAlpha = 0.05; ctx.drawImage(_grain[Math.floor(t * 2) % 2], 0, 0, W, H); ctx.restore();
}
function bands(top = 0.5, bot = 0.5) {
  top *= 0.85; bot *= 0.7;
  let g = ctx.createLinearGradient(0, 0, 0, 640); g.addColorStop(0, `rgba(8,7,6,${top})`); g.addColorStop(1, 'rgba(8,7,6,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, 640);
  g = ctx.createLinearGradient(0, 1180, 0, H); g.addColorStop(0, 'rgba(8,7,6,0)'); g.addColorStop(0.45, `rgba(8,7,6,${bot})`); g.addColorStop(1, `rgba(8,7,6,${Math.min(1, bot + 0.2)})`); ctx.fillStyle = g; ctx.fillRect(0, 1180, W, H - 1180);
}
// 字幕：安全区 y≈1432（避开视频号底部信息区与右侧按钮）
const SUB_Y = 1432;
let SUB_HIDE = null;     // 某些段落由画面自己呈现文字时，隐藏字幕（返回 true 则不显示）
function subtitles(t) {
  for (const l of TL.lines) {
    if (t < l.start - 0.05 || t > l.end + 0.25 || l.kind !== 'n') continue;
    if (SUB_HIDE && SUB_HIDE(l)) continue;
    for (let i = 0; i < l.chunks.length; i++) {
      const c = l.chunks[i]; const last = i === l.chunks.length - 1;
      if (t >= c.start - 0.03 && t < (last ? l.end + 0.22 : c.end - 0.03)) {
        const a = Math.min(sstep((t - c.start + 0.03) / 0.12), last ? sstep((l.end + 0.22 - t) / 0.15) : 1);
        const s = c.text.replace(/[，。；：、]$/, '').replace(/——$/, '').replace(/[《》]/g, m => m);
        text(s, 520, SUB_Y, { size: 48, wt: 700, align: 'center', alpha: a, stroke: 9, strokeColor: 'rgba(6,5,4,0.92)' });
      }
    }
  }
}
// 史书原文卡：文言逐字显现，随后的白话解释期间保持
const QUOTE_Y = 250;
let QUOTE_SKIP = null;   // 某些原文由场景自己呈现（如敕勒歌、童谣）
function quoteHold(n) {
  const l = TL.lines[n], nx = TL.lines[n + 1];
  return (nx && nx.kind === 'n' && nx.sec === l.sec) ? Math.min(nx.end, l.end + clamp(l.text.length * 0.35, 2.6, 7.5)) : l.end + 0.9;
}
function quotes(t) {
  for (let n = 0; n < TL.lines.length; n++) {
    const l = TL.lines[n]; if (l.kind !== 'q') continue;
    if (QUOTE_SKIP && QUOTE_SKIP(l)) continue;
    const hold = quoteHold(n), t0 = l.start - 0.45; if (t < t0 || t > hold + 0.4) continue;
    const a = Math.min(sstep((t - t0) / 0.4), sstep((hold + 0.4 - t) / 0.4));
    const sz = l.text.length > 30 ? 46 : 52, lh = sz * 1.5, maxw = 850;
    const lines = wrap(l.text, maxw, sz, SERIF, 900);
    const h = lines.length * lh + 96, y0 = QUOTE_Y;
    ctx.save(); ctx.globalAlpha = a;
    rrect(60, y0, 960, h, 10); ctx.fillStyle = 'rgba(14,11,8,0.86)'; ctx.fill();
    ctx.fillStyle = C.gold; ctx.fillRect(60, y0, 8, h);
    ctx.strokeStyle = 'rgba(220,183,108,0.35)'; ctx.lineWidth = 1.5; rrect(60, y0, 960, h, 10); ctx.stroke();
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
const CHAPS = ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9'];
function chip(t) {
  let cur = null; for (const id of CHAPS) { const s = TL.secs[id]; if (t >= s.body - 0.2 && t < s.end) cur = s; }
  if (!cur) return; const a = Math.min(sstep((t - cur.body + 0.2) / 0.6), sstep((cur.end - t) / 0.5)) * 0.95;
  ctx.save(); ctx.globalAlpha = a;
  ctx.fillStyle = C.red; ctx.fillRect(60, 178, 44, 44); text(cur.num, 82, 201, { size: 28, fam: SERIF, wt: 900, align: 'center', stroke: 0, color: '#fff' });
  text(cur.title, 118, 201, { size: 30, fam: SERIF, wt: 900, color: C.cream, stroke: 6 });
  ctx.restore();
}
function chapterCard(t) {
  for (const id of CHAPS) {
    const s = TL.secs[id]; if (!s.card) continue; const [a, b] = s.card; if (t < a - 0.45 || t > b + 0.1) continue;
    const al = Math.min(sstep((t - (a - 0.45)) / 0.45), sstep((b + 0.1 - t) / 0.6));
    ctx.save(); ctx.fillStyle = `rgba(9,8,7,${al})`; ctx.fillRect(0, 0, W, H);
    const u = (t - a) / (b - a); ctx.globalAlpha = Math.min(sstep((t - a + 0.1) / 0.45), sstep((b - 0.05 - t) / 0.4));
    const cy = 860;
    ctx.fillStyle = C.red; const lw2 = 300 * eout(u * 2.2); ctx.fillRect(W / 2 - lw2 / 2, cy - 150, lw2, 4);
    text(s.num, W / 2, cy - 70, { size: 76, fam: SERIF, wt: 900, color: C.red, align: 'center', stroke: 0 });
    text(s.title, W / 2, cy + 60 - 10 * (1 - eout(u * 2)), { size: 92, fam: SERIF, wt: 900, color: C.cream, align: 'center', stroke: 0, ls: 6 });
    ctx.fillStyle = 'rgba(244,234,214,0.5)'; ctx.fillRect(W / 2 - lw2 / 2, cy + 160, lw2, 2);
    ctx.restore();
  }
}
// 雪花粒子（只作氛围）
function snowfall(t, a = 1, n = 260, seed = 5, speed = 1) {
  if (a <= 0) return; ctx.save(); ctx.fillStyle = '#f2f4f6';
  for (let i = 0; i < n; i++) {
    const s = 0.4 + hash(i, seed) * 1.0, x = (hash(i, seed + 1) * W + Math.sin(t * 0.6 + i) * 22 + t * 14 * s) % W, y = (hash(i, seed + 2) * H + t * 70 * s * speed) % H;
    ctx.globalAlpha = a * (0.25 + 0.55 * hash(i, seed + 3)); ctx.beginPath(); ctx.arc(x, y, 1.2 + 2.4 * s, 0, 7); ctx.fill();
  }
  ctx.restore();
}
