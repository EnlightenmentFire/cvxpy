'use strict';
/* ================= basics ================= */
const W = 1080, H = 1920, D = window.DATA;
const cv = document.getElementById('c'), ctx = cv.getContext('2d');
const lay = document.createElement('canvas'); lay.width = W; lay.height = H; const lx = lay.getContext('2d');
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, p) => a + (b - a) * p;
const seg = (t, a, b) => clamp((t - a) / (b - a));
const ease = x => { x = clamp(x); return x * x * (3 - 2 * x); };
const eio = x => { x = clamp(x); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const eout = x => 1 - Math.pow(1 - clamp(x), 3);
const fade = (t, a, b, fi = .5, fo = .5) => Math.min(ease(seg(t, a, a + fi)), 1 - ease(seg(t, b - fo, b)));
function rng(seed) { let s = seed >>> 0; return () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const hash = (n) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

/* ================= colors ================= */
const C = {
  bone: '#efe7d6', gold: '#e2c27a', goldDim: '#9c8658', ink: '#05080b',
  gr: '#ff3b2a', grHi: '#ffab7a', grDim: '#8a2016',          // Oda (+Tokugawa): vermilion
  pe: '#3d8bff', peHi: '#9cd0ff', peDim: '#1d3d70',          // Asakura: cold blue
  az: '#7d97bd', azHi: '#c3d4ee', azDim: '#3a4a66',          // Azai: cold grey-blue
  grey: '#a9adb2', sea: '#0d2230',
};
const SONG = '"Noto Serif CJK SC"', HEI = '"Noto Sans CJK SC"', GRK = '"Noto Serif CJK JP"', JP = '"Noto Serif CJK JP"';

/* ================= timeline ================= */
const LINES = []; const BYV = {};
D.script.forEach(s => s.lines.forEach(l => { const tl = D.tl.lines[l.id]; const o = { ...l, scene: s.id, t0: tl.t0, t1: tl.t1, sub: tl.sub }; LINES.push(o); if (l.v) BYV[l.v] = o; }));
const SC = {}; D.tl.scenes.forEach(s => SC[s.id] = s);
const TOTAL = D.tl.total;
function lv(v) { const l = BYV[v]; if (!l) throw new Error('no line v=' + v); return l; }
const A = v => lv(v).t0, Z = v => lv(v).t1;
const LP = (t, v) => seg(t, A(v), Z(v));
const NX = v => { const i = LINES.indexOf(lv(v)); return i + 1 < LINES.length ? LINES[i + 1].t0 : TOTAL; };   // next line start

/* ================= maps & camera ================= */
const my = lat => 180 / Math.PI * Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360));
const MAPS = {};
const cam = { lon: 23.5, lat: 37.95, ppd: 9000, rot: 0 };
function loadImg(src) { return new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = src; }); }
async function loadAll() {
  for (const k of 'ABC') { const m = D.maps[k]; MAPS[k] = { ...m, Y0: my(m.lat0), Y1: my(m.lat1), img: await loadImg(`../assets/maps/${k}.jpg`) }; }
  const fs = [];
  for (const w of [400, 500, 600, 700, 900]) { fs.push(document.fonts.load(`${w} 40px ${SONG}`, '金崎撤退')); fs.push(document.fonts.load(`${w} 40px ${HEI}`, '金崎撤退')); fs.push(document.fonts.load(`${w} 40px ${JP}`, '残しをかせられ')); }
  await Promise.all(fs); await document.fonts.ready;
}
const P = (lon, lat) => [W / 2 + (lon - cam.lon) * cam.ppd, H / 2 - (my(lat) - my(cam.lat)) * cam.ppd];
const setCam = c => { cam.lon = c[0]; cam.lat = c[1]; cam.ppd = c[2]; };
function camMix(a, b, p) { return [lerp(a[0], b[0], p), lerp(a[1], b[1], p), Math.exp(lerp(Math.log(a[2]), Math.log(b[2]), p))]; }
function camKeys(t, keys) {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) if (t <= keys[i][0]) { const p = (keys[i][2] || eio)(seg(t, keys[i - 1][0], keys[i][0])); return camMix(keys[i - 1][1], keys[i][1], p); }
  return keys[keys.length - 1][1];
}
function drawTex(k, alpha) {
  const m = MAPS[k]; if (alpha <= 0.003) return;
  const x0 = W / 2 + (m.lon0 - cam.lon) * cam.ppd, x1 = W / 2 + (m.lon1 - cam.lon) * cam.ppd;
  const y0 = H / 2 - (m.Y1 - my(cam.lat)) * cam.ppd, y1 = H / 2 - (m.Y0 - my(cam.lat)) * cam.ppd;
  if (x1 < 0 || x0 > W || y1 < 0 || y0 > H) return;
  const covers = x0 <= 0 && x1 >= W && y0 <= 0 && y1 >= H;
  // crop source to the visible part (faster + better sampling)
  const sx0 = Math.max(0, (0 - x0) / (x1 - x0) * m.w), sx1 = Math.min(m.w, (W - x0) / (x1 - x0) * m.w);
  const sy0 = Math.max(0, (0 - y0) / (y1 - y0) * m.h), sy1 = Math.min(m.h, (H - y0) / (y1 - y0) * m.h);
  const dx0 = x0 + sx0 / m.w * (x1 - x0), dx1 = x0 + sx1 / m.w * (x1 - x0), dy0 = y0 + sy0 / m.h * (y1 - y0), dy1 = y0 + sy1 / m.h * (y1 - y0);
  const g = covers ? ctx : lx;
  if (!covers) lx.clearRect(0, 0, W, H);
  g.save(); g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
  if (covers) g.globalAlpha = alpha;
  g.drawImage(m.img, sx0, sy0, sx1 - sx0, sy1 - sy0, dx0, dy0, dx1 - dx0, dy1 - dy0);
  g.restore();
  if (!covers) {
    const f = 140; lx.save(); lx.globalCompositeOperation = 'destination-out';
    const edge = (gx0, gy0, gx1, gy1, rx, ry, rw, rh) => { const gr = lx.createLinearGradient(gx0, gy0, gx1, gy1); gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); lx.fillStyle = gr; lx.fillRect(rx, ry, rw, rh); };
    edge(x0, 0, x0 + f, 0, x0 - 2, 0, f + 2, H); edge(x1, 0, x1 - f, 0, x1 - f, 0, f + 2, H);
    edge(0, y0, 0, y0 + f, 0, y0 - 2, W, f + 2); edge(0, y1, 0, y1 - f, 0, y1 - f, W, f + 2);
    lx.restore(); ctx.save(); ctx.globalAlpha = alpha; ctx.drawImage(lay, 0, 0); ctx.restore();
  }
}
function covered(k) { const m = MAPS[k]; const hw = W / 2 / cam.ppd, hh = H / 2 / cam.ppd; return cam.lon - hw >= m.lon0 && cam.lon + hw <= m.lon1 && my(cam.lat) - hh >= m.Y0 && my(cam.lat) + hh <= m.Y1; }
const sstep = (a, b, x) => ease((x - a) / (b - a));
function drawMap() {
  ctx.fillStyle = '#081620'; ctx.fillRect(0, 0, W, H);
  const aC = sstep(1300, 2100, cam.ppd), aB = sstep(3200, 4600, cam.ppd);
  if (!(aB >= 1 && covered('B')) && !(aC >= 1 && covered('C') && aB <= 0)) drawTex('A', 1);
  if (aB < 1 || !covered('B')) drawTex('C', aC);
  drawTex('B', aB);
}
/* grading overlays */
function grade(kind, a = 1) {
  if (a <= 0.003) return;
  ctx.save(); ctx.globalAlpha = a;
  if (kind === 'night') {
    ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = '#5c74a8'; ctx.fillRect(0, 0, W, H);
    ctx.globalCompositeOperation = 'source-over'; ctx.fillStyle = 'rgba(2,6,16,0.18)'; ctx.fillRect(0, 0, W, H);
    const g = ctx.createRadialGradient(W * 0.72, H * 0.2, 0, W * 0.72, H * 0.2, H * 0.6); g.addColorStop(0, 'rgba(150,180,230,0.16)'); g.addColorStop(1, 'rgba(150,180,230,0)');
    ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  } else if (kind === 'dawn') {
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, 'rgba(255,150,70,0.38)'); g.addColorStop(0.45, 'rgba(255,120,60,0.10)'); g.addColorStop(1, 'rgba(20,30,60,0.25)');
    ctx.globalCompositeOperation = 'soft-light'; ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    const g2 = ctx.createRadialGradient(W * 0.85, -100, 0, W * 0.85, -100, H * 0.8); g2.addColorStop(0, 'rgba(255,190,120,0.35)'); g2.addColorStop(1, 'rgba(255,190,120,0)');
    ctx.globalCompositeOperation = 'screen'; ctx.fillStyle = g2; ctx.fillRect(0, 0, W, H);
  } else if (kind === 'dim') {
    ctx.fillStyle = 'rgba(3,6,10,0.55)'; ctx.fillRect(0, 0, W, H);
  } else if (kind === 'black') {
    ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  }
  ctx.restore();
}
function vignette(s = 1) {
  const g = ctx.createRadialGradient(W / 2, H * 0.46, H * 0.22, W / 2, H * 0.5, H * 0.78);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${0.78 * s})`);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  // top/bottom bands for text legibility
  const t = ctx.createLinearGradient(0, 0, 0, 380); t.addColorStop(0, `rgba(0,0,0,${0.62 * s})`); t.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = t; ctx.fillRect(0, 0, W, 380);
  const b = ctx.createLinearGradient(0, H - 700, 0, H); b.addColorStop(0, 'rgba(0,0,0,0)'); b.addColorStop(0.55, `rgba(0,0,0,${0.6 * s})`); b.addColorStop(1, `rgba(0,0,0,${0.8 * s})`); ctx.fillStyle = b; ctx.fillRect(0, H - 700, W, 700);
}
let GRAIN = null;
function grain(t, a = 0.06) {
  if (!GRAIN) { GRAIN = []; for (let k = 0; k < 4; k++) { const c = document.createElement('canvas'); c.width = 540; c.height = 960; const g = c.getContext('2d'); const id = g.createImageData(540, 960); const r = rng(77 + k); for (let i = 0; i < id.data.length; i += 4) { const v = r() * 255; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255; } g.putImageData(id, 0, 0); GRAIN.push(c); } }
  ctx.save(); ctx.globalAlpha = a; ctx.globalCompositeOperation = 'overlay'; ctx.drawImage(GRAIN[Math.floor(t * 12) % 4], 0, 0, W, H); ctx.restore();
}

/* ================= text ================= */
function font(size, weight = 600, fam = SONG, it = false) { ctx.font = `${it ? 'italic ' : ''}${weight} ${size}px ${fam}`; }
function txt(s, x, y, o = {}) {
  const { size = 40, w = 600, fam = SONG, color = C.bone, align = 'center', a = 1, ls = 0, shadow = 1, base = 'middle', stroke = 0, it = false } = o;
  if (a <= 0.003) return 0;
  ctx.save(); font(size, w, fam, it); ctx.textAlign = align; ctx.textBaseline = base; ctx.globalAlpha = a;
  try { ctx.letterSpacing = ls + 'px'; } catch (e) { }
  if (stroke) { ctx.lineWidth = stroke; ctx.strokeStyle = 'rgba(0,0,0,0.85)'; ctx.lineJoin = 'round'; ctx.strokeText(s, x, y); }
  if (shadow) { ctx.shadowColor = `rgba(0,0,0,${0.9 * shadow})`; ctx.shadowBlur = size * 0.25; ctx.shadowOffsetY = 2; }
  ctx.fillStyle = color; ctx.fillText(s, x, y);
  const wd = ctx.measureText(s).width; ctx.restore(); return wd;
}
const NOHEAD = '，。：；？！、）」』》”’…—', NOTAIL = '（「『《“‘';
function wrap(s, maxW, size, w = 600, fam = SONG, it = false) {
  ctx.save(); font(size, w, fam, it);
  const out = []; let cur = '';
  const isLatin = /[A-Za-zΑ-ωἀ-ῼ]/.test(s) && !/[一-鿿]/.test(s);
  const toks = isLatin ? s.split(/(\s+)/) : [...s];
  for (const ch of toks) {
    if (ch === '\n') { out.push(cur); cur = ''; continue; }
    if (ctx.measureText(cur + ch).width > maxW && cur.trim() && !NOHEAD.includes(ch)) {
      if (!isLatin && NOTAIL.includes(cur.slice(-1))) { const k = cur.slice(-1); out.push(cur.slice(0, -1)); cur = k + ch; } else { out.push(cur.trimEnd()); cur = isLatin ? ch.trimStart() : ch; }
    } else cur += ch;
  }
  if (cur) out.push(cur); ctx.restore(); return out;
}
// balance CJK lines so the last line isn't a stub
function wrapBal(s, maxW, size, w = 600) {
  let lines = wrap(s, maxW, size, w); if (lines.length < 2) return lines;
  for (let mw = maxW; mw > maxW * 0.55; mw -= 10) { const l2 = wrap(s, mw, size, w); if (l2.length > lines.length) break; lines = l2; }
  return lines;
}

/* ================= subtitles ================= */
function curLine(t) { for (const l of LINES) if (t >= l.t0 - 0.05 && t < l.t1 + 0.25) return l; return null; }
function subtitles(t) {
  const l = curLine(t); if (!l) return;
  let ch = null; for (const c of l.sub) if (t >= c.t0 - 0.05 && t < c.t1 + 0.05) ch = c;
  if (!ch) ch = t < l.sub[0].t0 ? l.sub[0] : l.sub[l.sub.length - 1];
  const a = Math.min(ease(seg(t, ch.t0 - 0.05, ch.t0 + 0.12)), 1 - ease(seg(t, l.t1 + 0.1, l.t1 + 0.25)));
  const size = 56, lh = 80;
  const lines = wrapBal(ch.text, 940, size, 700);
  const y0 = 1500 - (lines.length - 1) * lh / 2;
  lines.forEach((s, i) => txt(s, W / 2, y0 + i * lh, { size, w: 700, color: '#fff8ea', a, stroke: 7, shadow: 1 }));
}

/* ================= quote card ================= */
function quoteCard(t) {
  const l = curLine(t); if (!l || !l.q) return;
  const q = l.q, a = fade(t, l.t0 - 0.1, l.t1 + 0.6, 0.5, 0.45);
  if (a <= 0.003) return;
  const hasOrig = !!q.orig, cjkOrig = hasOrig && /[一-鿿]/.test(q.orig);
  const x0 = 70, x1 = W - 70, cw = x1 - x0;
  // measure
  let ol = [], osz = cjkOrig ? (q.orig.length > 34 ? 50 : 58) : 46;
  if (hasOrig) ol = cjkOrig ? q.orig.split('\n').flatMap(s => wrapBal(s, cw - 120, osz, 700)) : q.orig.split('\n').flatMap(s => wrap(s, cw - 110, osz, 400, GRK, true));
  const zsz = hasOrig ? 40 : 50; const zl = wrapBal((hasOrig ? '' : '「') + q.zh + (hasOrig ? '' : '」'), cw - 120, zsz, hasOrig ? 500 : 700);
  const oh = ol.length * osz * 1.45, zh = zl.length * zsz * 1.5;
  const ch = 70 + oh + (hasOrig ? 46 : 0) + zh + 90;
  const yc = 760, y0 = yc - ch / 2;
  const rise = (1 - eout(seg(t, l.t0 - 0.1, l.t0 + 0.6))) * 30;
  ctx.save(); ctx.globalAlpha = a; ctx.translate(0, rise);
  ctx.fillStyle = 'rgba(8,10,14,0.80)'; ctx.fillRect(x0, y0, cw, ch);
  ctx.strokeStyle = 'rgba(226,194,122,0.85)'; ctx.lineWidth = 2; ctx.strokeRect(x0 + 10, y0 + 10, cw - 20, ch - 20);
  ctx.strokeStyle = 'rgba(226,194,122,0.35)'; ctx.lineWidth = 1; ctx.strokeRect(x0 + 18, y0 + 18, cw - 36, ch - 36);
  // meander corners
  for (const [cx, cy, sx, sy] of [[x0 + 10, y0 + 10, 1, 1], [x1 - 10, y0 + 10, -1, 1], [x0 + 10, y0 + ch - 10, 1, -1], [x1 - 10, y0 + ch - 10, -1, -1]]) {
    ctx.beginPath(); ctx.moveTo(cx, cy + sy * 34); ctx.lineTo(cx + sx * 34, cy + sy * 34); ctx.lineTo(cx + sx * 34, cy + sy * 12); ctx.lineTo(cx + sx * 18, cy + sy * 12); ctx.lineTo(cx + sx * 18, cy + sy * 24);
    ctx.strokeStyle = C.gold; ctx.lineWidth = 2.5; ctx.stroke();
  }
  ctx.restore();
  let y = y0 + 70 + rise;
  if (hasOrig) {
    ol.forEach((s, i) => txt(s, W / 2, y + osz * 0.5 + i * osz * 1.45, cjkOrig ? { size: osz, w: 700, fam: q.jp === false ? SONG : JP, color: C.gold, a, shadow: 0.6, ls: 2 } : { size: osz, w: 400, fam: GRK, it: true, color: C.gold, a, shadow: 0.6 }));
    y += oh + 10;
    ctx.save(); ctx.globalAlpha = a * 0.7; ctx.strokeStyle = C.goldDim; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(W / 2 - 120, y + 8); ctx.lineTo(W / 2 + 120, y + 8); ctx.stroke(); ctx.restore();
    y += 36;
  }
  zl.forEach((s, i) => txt(s, W / 2, y + zsz * 0.5 + i * zsz * 1.5, { size: zsz, w: hasOrig ? 500 : 700, color: hasOrig ? '#e9e2d0' : C.bone, a }));
  y += zh + 26;
  txt('—— ' + q.src, x1 - 60, y + 12, { size: 30, w: 500, color: C.goldDim, a, align: 'right', shadow: 0 });
}

/* ================= chrome ================= */
function chapterCard(t) {
  for (const s of D.tl.scenes) {
    if (!s.title || t < s.t0 || t > s.t0 + 5.2) continue;
    const a = fade(t, s.t0 + 0.1, s.t0 + 5.0, 0.6, 0.8);
    const [num, ...rest] = s.title.split('　'); const name = rest.join('');
    const sc = 1 + 0.04 * seg(t, s.t0, s.t0 + 5);
    ctx.save(); ctx.translate(W / 2, 300); ctx.scale(sc, sc);
    txt(num, 0, -62, { size: 40, w: 600, color: C.gold, a, ls: 6 });
    txt(name, 0, 20, { size: 92, w: 900, color: '#fff3dc', a, ls: 14, stroke: 6 });
    ctx.globalAlpha = a; ctx.strokeStyle = C.gold; ctx.lineWidth = 2;
    const wd = 300 * ease(seg(t, s.t0 + 0.2, s.t0 + 1.2));
    ctx.beginPath(); ctx.moveTo(-wd, 92); ctx.lineTo(wd, 92); ctx.stroke();
    ctx.restore();
  }
}
function badges(t, mapOn) {
  txt('AI配音', 46, 70, { size: 26, w: 500, color: 'rgba(240,235,220,0.75)', align: 'left', shadow: 0.8 });
  txt('从无名小卒到天下人 · 第2集', W - 46, 70, { size: 26, w: 500, color: 'rgba(240,235,220,0.75)', align: 'right', shadow: 0.8 });
  if (mapOn > 0.01) txt('地图示意 · 地形为今日数据', W - 46, 1700, { size: 22, w: 400, color: 'rgba(230,225,210,0.6)', align: 'right', a: mapOn, shadow: 0.8 });
}

/* ================= map annotations ================= */
function dot(lon, lat, o = {}) {
  const { r = 7, color = C.bone, a = 1, ring = 0 } = o; if (a <= 0.003) return;
  const [x, y] = P(lon, lat);
  ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = color; ctx.shadowColor = 'rgba(0,0,0,0.8)'; ctx.shadowBlur = 6;
  ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill();
  if (ring) { ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.globalAlpha = a * (1 - ring); ctx.beginPath(); ctx.arc(x, y, r + 40 * ring, 0, Math.PI * 2); ctx.stroke(); }
  ctx.restore();
}
function label(lon, lat, s, o = {}) {
  const { dx = 0, dy = -38, size = 46, a = 1, color = C.bone, sub = null, w = 700, align = 'center', pt = true } = o;
  if (a <= 0.003) return;
  const [x, y] = P(lon, lat);
  if (pt) dot(lon, lat, { r: 6, color, a });
  txt(s, x + dx, y + dy, { size, w, color, a, stroke: 5, align });
  if (sub) txt(sub, x + dx, y + dy + size * 0.85, { size: size * 0.5, w: 400, color: 'rgba(235,228,210,0.85)', a, stroke: 3, align, fam: GRK, it: true });
}
function areaLabel(lon, lat, s, o = {}) { const { size = 50, a = 1, color = 'rgba(240,230,205,0.85)', ls = 10 } = o; const [x, y] = P(lon, lat); txt(s, x, y, { size, w: 400, color, a, ls, stroke: 4 }); }

// polyline in lon/lat -> pixel, cumulative length
function pathPx(pts) { const p = pts.map(q => P(q[0], q[1])); const L = [0]; for (let i = 1; i < p.length; i++) L.push(L[i - 1] + Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1])); return { p, L, len: L[L.length - 1] }; }
// Catmull-Rom smoothing of lon/lat control points
function smooth(pts, n = 12) {
  if (pts.length < 3) return pts; const out = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
    for (let k = 0; k < n; k++) { const t = k / n, t2 = t * t, t3 = t2 * t; out.push([0, 1].map(j => 0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3))); }
  }
  out.push(pts[pts.length - 1]); return out;
}
function samplePx(pp, d) { d = clamp(d, 0, pp.len); let i = 1; while (i < pp.L.length - 1 && pp.L[i] < d) i++; const s = (d - pp.L[i - 1]) / Math.max(1e-6, pp.L[i] - pp.L[i - 1]); const a = pp.p[i - 1], b = pp.p[i]; return [lerp(a[0], b[0], s), lerp(a[1], b[1], s), Math.atan2(b[1] - a[1], b[0] - a[0])]; }
/* big tapered arrow along a lon/lat path; p in [0,1] = drawn fraction */
function arrow(pts, p, o = {}) {
  const { color = C.gr, hi = C.grHi, w = 34, a = 1, dash = false, head = 1.0, glow = 1, tail = 0 } = o;
  if (a <= 0.003 || p <= 0.002) return;
  const pp = pathPx(smooth(pts)); const end = pp.len * clamp(p), st = pp.len * clamp(tail);
  const N = Math.max(8, Math.ceil((end - st) / 6)); const hl = w * 2.0 * head;
  const left = [], right = [];
  const bodyEnd = Math.max(st, end - hl * 0.85);
  for (let i = 0; i <= N; i++) {
    const d = lerp(st, bodyEnd, i / N); const [x, y, an] = samplePx(pp, d);
    const ww = w * 0.5 * lerp(0.42, 1, Math.pow((d - st) / Math.max(1, end - st), 0.6));
    left.push([x + Math.cos(an - Math.PI / 2) * ww, y + Math.sin(an - Math.PI / 2) * ww]); right.push([x + Math.cos(an + Math.PI / 2) * ww, y + Math.sin(an + Math.PI / 2) * ww]);
  }
  const [hx, hy, ha] = samplePx(pp, end); const [bx, by, ba] = samplePx(pp, bodyEnd);
  ctx.save(); ctx.globalAlpha = a;
  const shape = () => {
    ctx.beginPath(); left.forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]));
    ctx.lineTo(bx + Math.cos(ba - Math.PI / 2) * w * 1.05, by + Math.sin(ba - Math.PI / 2) * w * 1.05);
    ctx.lineTo(hx, hy);
    ctx.lineTo(bx + Math.cos(ba + Math.PI / 2) * w * 1.05, by + Math.sin(ba + Math.PI / 2) * w * 1.05);
    for (let i = right.length - 1; i >= 0; i--) ctx.lineTo(right[i][0], right[i][1]); ctx.closePath();
  };
  if (dash) {
    ctx.setLineDash([w * 0.9, w * 0.7]); ctx.lineWidth = w * 0.32; ctx.strokeStyle = color; ctx.lineCap = 'round';
    ctx.shadowColor = color; ctx.shadowBlur = 18 * glow;
    ctx.beginPath(); for (let d = st, k = 0; d <= bodyEnd; d += 6, k++) { const [x, y] = samplePx(pp, d); k ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke(); ctx.setLineDash([]);
    ctx.beginPath(); ctx.moveTo(hx, hy); ctx.lineTo(bx + Math.cos(ba - Math.PI / 2) * w * 0.8, by + Math.sin(ba - Math.PI / 2) * w * 0.8); ctx.lineTo(bx + Math.cos(ba + Math.PI / 2) * w * 0.8, by + Math.sin(ba + Math.PI / 2) * w * 0.8); ctx.closePath(); ctx.fillStyle = color; ctx.fill();
  } else {
    ctx.shadowColor = color; ctx.shadowBlur = 26 * glow; shape(); ctx.fillStyle = color; ctx.globalAlpha = a * 0.92; ctx.fill();
    ctx.shadowBlur = 0; ctx.globalAlpha = a; ctx.lineWidth = 3; ctx.strokeStyle = hi; ctx.stroke();
    // inner highlight streak
    const g = ctx.createLinearGradient(bx - Math.cos(ba) * 200, by - Math.sin(ba) * 200, hx, hy); g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(1, 'rgba(255,255,255,0.35)');
    ctx.fillStyle = g; shape(); ctx.fill();
  }
  ctx.restore();
}

/* ================= ships ================= */
// top-down trireme glyph; L = length px; col fill
function ship(x, y, ang, L, col, o = {}) {
  const { a = 1, oar = 0, broken = 0, hi = null, glow = 0, sink = 0 } = o; if (a <= 0.003) return;
  ctx.save(); ctx.translate(x, y); ctx.rotate(ang); ctx.globalAlpha = a * (1 - sink * 0.8);
  const bw = L * 0.16;
  if (glow) { ctx.shadowColor = o.halo || col; ctx.shadowBlur = glow; }
  // oars
  if (L > 10) {
    ctx.strokeStyle = hi || col; ctx.lineWidth = Math.max(1, L * 0.025); ctx.globalAlpha *= 0.85;
    const n = L > 40 ? 9 : 5, sw = Math.sin(oar) * 0.45;
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      const ox = -L * 0.32 + i * L * 0.58 / (n - 1);
      if (!(broken && i % 2)) { ctx.moveTo(ox, -bw * 0.5); ctx.lineTo(ox + L * 0.12 * sw, -bw * 0.5 - L * 0.17); }
      if (!(broken > 0.5 && i % 3 === 0)) { ctx.moveTo(ox, bw * 0.5); ctx.lineTo(ox + L * 0.12 * sw, bw * 0.5 + L * 0.17); }
    }
    ctx.stroke(); ctx.globalAlpha /= 0.85;
  }
  ctx.beginPath(); ctx.moveTo(L * 0.5, 0); ctx.quadraticCurveTo(L * 0.25, -bw * 0.62, -L * 0.3, -bw * 0.5); ctx.lineTo(-L * 0.5, -bw * 0.15); ctx.lineTo(-L * 0.5, bw * 0.15); ctx.lineTo(-L * 0.3, bw * 0.5); ctx.quadraticCurveTo(L * 0.25, bw * 0.62, L * 0.5, 0); ctx.closePath();
  ctx.fillStyle = col; ctx.fill(); ctx.shadowBlur = 0;
  if (L > 14) { ctx.strokeStyle = 'rgba(0,0,0,0.55)'; ctx.lineWidth = 1; ctx.stroke(); ctx.fillStyle = 'rgba(255,255,255,0.25)'; ctx.fillRect(-L * 0.3, -bw * 0.12, L * 0.55, bw * 0.24); }
  // ram
  ctx.fillStyle = '#c98f3c'; ctx.beginPath(); ctx.moveTo(L * 0.58, 0); ctx.lineTo(L * 0.47, -bw * 0.18); ctx.lineTo(L * 0.47, bw * 0.18); ctx.closePath(); ctx.fill();
  ctx.restore();
}
function wake(x, y, ang, len, a = 0.35) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(ang); const g = ctx.createLinearGradient(0, 0, -len, 0); g.addColorStop(0, `rgba(220,235,245,${a})`); g.addColorStop(1, 'rgba(220,235,245,0)');
  ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(0, -len * 0.06); ctx.lineTo(-len, -len * 0.18); ctx.lineTo(-len, len * 0.18); ctx.lineTo(0, len * 0.06); ctx.fill(); ctx.restore();
}
/* particles */
function fire(x, y, t, s = 1, a = 1, seed = 1) {
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 40; i++) {
    const ph = (t * (0.55 + hash(i + seed) * 0.5) + hash(i * 7 + seed)) % 1;
    const px = x + (hash(i * 3 + seed) - 0.5) * 60 * s + Math.sin(t * 3 + i) * 6 * s, py = y - ph * 120 * s;
    const r = (1 - ph) * 22 * s + 4;
    const g = ctx.createRadialGradient(px, py, 0, px, py, r); g.addColorStop(0, `rgba(255,220,140,${0.55 * a * (1 - ph)})`); g.addColorStop(0.4, `rgba(255,110,30,${0.4 * a * (1 - ph)})`); g.addColorStop(1, 'rgba(120,20,0,0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(px, py, r, 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
  ctx.save();
  for (let i = 0; i < 18; i++) {
    const ph = (t * 0.12 + hash(i * 11 + seed)) % 1; const px = x + (hash(i * 5 + seed) - 0.3) * 50 * s + ph * 160 * s, py = y - 60 * s - ph * 420 * s; const r = 20 * s + ph * 90 * s;
    ctx.fillStyle = `rgba(30,26,24,${0.35 * a * Math.sin(ph * Math.PI)})`; ctx.beginPath(); ctx.arc(px, py, r, 0, Math.PI * 2); ctx.fill();
  }
  ctx.restore();
}
function sparks(x, y, t, t0, a = 1, seed = 3, s = 1) {
  const age = t - t0; if (age < 0 || age > 1.2) return;
  ctx.save(); ctx.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 16; i++) {
    const an = hash(i + seed) * Math.PI * 2, v = (60 + hash(i * 3 + seed) * 140) * s; const px = x + Math.cos(an) * v * age, py = y + Math.sin(an) * v * age + 40 * age * age;
    ctx.fillStyle = `rgba(255,${180 + 60 * hash(i)},120,${a * (1 - age / 1.2)})`; ctx.beginPath(); ctx.arc(px, py, 2.4 * s, 0, Math.PI * 2); ctx.fill();
  }
  const fl = Math.max(0, 1 - age * 4); if (fl > 0) { const g = ctx.createRadialGradient(x, y, 0, x, y, 60 * s); g.addColorStop(0, `rgba(255,230,180,${0.8 * fl * a})`); g.addColorStop(1, 'rgba(255,120,40,0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, 60 * s, 0, Math.PI * 2); ctx.fill(); }
  ctx.restore();
}
function ripples(t, a = 1, seed = 1, n = 60) {
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  for (let i = 0; i < n; i++) {
    const x = hash(i * 3 + seed) * W, y = hash(i * 5 + seed) * H; const ph = (t * 0.4 + hash(i * 9 + seed)) % 1;
    ctx.strokeStyle = `rgba(200,225,240,${0.12 * a * Math.sin(ph * Math.PI)})`; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.ellipse(x, y, 20 + 40 * ph, 4 + 8 * ph, 0, 0, Math.PI * 2); ctx.stroke();
  }
  ctx.restore();
}
function panel(x, y, w, h, a = 1, fill = 'rgba(8,10,14,0.78)') { ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = fill; ctx.fillRect(x, y, w, h); ctx.strokeStyle = 'rgba(226,194,122,0.6)'; ctx.lineWidth = 1.5; ctx.strokeRect(x + 6, y + 6, w - 12, h - 12); ctx.restore(); }
