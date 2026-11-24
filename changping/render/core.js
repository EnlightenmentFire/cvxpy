'use strict';
/* ---------- basics ---------- */
const W = 1080, H = 1920, D = window.DATA;
const cv = document.getElementById('c'), ctx = cv.getContext('2d');
const lay = document.createElement('canvas'); lay.width = W; lay.height = H; const lx = lay.getContext('2d');
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, p) => a + (b - a) * p;
const seg = (t, a, b) => clamp((t - a) / (b - a));
const ease = x => x * x * (3 - 2 * x);
const eio = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
const eout = x => 1 - Math.pow(1 - x, 3);
const fade = (t, a, b, fi = .5, fo = .5) => Math.min(ease(seg(t, a, a + fi)), 1 - ease(seg(t, b - fo, b)));
function rng(seed) { let s = seed >>> 0; return () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function gauss(r) { let u = 0, v = 0; while (u === 0) u = r(); v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }

/* ---------- colors ---------- */
const C = {
  bone: '#ece4d2', gold: '#e3c98a', goldDim: '#a8946a', ink: '#07090c', grey: '#9aa0a6',
  zhao: '#d9482f', zhaoHi: '#ff8a66', zhaoDim: '#6e2a1f',
  qin: '#0b0e13', qinRim: '#8fb0d0', qinHi: '#c9dcf0',
  han: '#c8a94e', wei: '#7f9a6a', qi: '#6f8fb5', chu: '#9a6fa8', yan: '#7fa7a0',
  river: 'rgba(132,164,186,', note: '#b9ad92',
};
const SONG = 'Song', HEI = 'Hei';

/* ---------- timeline ---------- */
const LINES = []; D.script.forEach(s => s.lines.forEach(l => { l.sec = s.sec; l.t0 = D.tl.lines[l.id].t0; l.t1 = D.tl.lines[l.id].t1; l.pauses = D.tl.lines[l.id].pauses || []; LINES.push(l); }));
const SECS = {}; D.script.forEach((s, i) => { SECS[s.sec] = { key: s.sec, title: s.title, a: s.lines[0].t0, b: s.lines[s.lines.length - 1].t1, i }; });
const TOTAL = D.tl.total;
function ln(key, nth = 0) { const m = LINES.filter(l => l.text.includes(key)); if (!m[nth]) throw new Error('no line: ' + key); return m[nth]; }
const A = (key, n) => ln(key, n).t0, Z = (key, n) => ln(key, n).t1;
const LP = (t, key, n) => { const l = ln(key, n); return seg(t, l.t0, l.t1); };

/* ---------- maps & camera ---------- */
const my = lat => 180 / Math.PI * Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360));
const MAPS = {};
const cam = { lon: 112.9, lat: 35.8, ppd: 1700 };
function loadImg(src) { return new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = rej; im.src = src; }); }
async function loadAll() {
  for (const k of 'ABC') {
    const m = D.maps[k];
    MAPS[k] = { ...m, Y0: my(m.lat0), Y1: my(m.lat1), ppd: m.w / (m.lon1 - m.lon0), summer: await loadImg(`../assets/maps/${k}_summer.jpg`), autumn: await loadImg(`../assets/maps/${k}_autumn.jpg`) };
  }
  const fs = [];
  for (const w of [400, 500, 600, 700, 900]) { fs.push(document.fonts.load(`${w} 40px Song`, '长平之战')); fs.push(document.fonts.load(`${w} 40px Hei`, '长平之战')); }
  await Promise.all(fs); await document.fonts.ready;
}
const P = (lon, lat) => [W / 2 + (lon - cam.lon) * cam.ppd, H / 2 - (my(lat) - my(cam.lat)) * cam.ppd];
const setCam = (c) => { cam.lon = c[0]; cam.lat = c[1]; cam.ppd = c[2]; };
// zoom-aware camera interpolation (log scale for ppd)
function camMix(a, b, p) { return [lerp(a[0], b[0], p), lerp(a[1], b[1], p), Math.exp(lerp(Math.log(a[2]), Math.log(b[2]), p))]; }
function camKeys(t, keys) { // keys: [[time, cam, easeFn?], ...]
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) if (t <= keys[i][0]) { const p = (keys[i][2] || eio)(seg(t, keys[i - 1][0], keys[i][0])); return camMix(keys[i - 1][1], keys[i][1], p); }
  return keys[keys.length - 1][1];
}
function drawTex(k, season, alpha) {
  const m = MAPS[k]; if (alpha <= 0.003) return;
  const x0 = W / 2 + (m.lon0 - cam.lon) * cam.ppd, x1 = W / 2 + (m.lon1 - cam.lon) * cam.ppd;
  const y0 = H / 2 - (m.Y1 - my(cam.lat)) * cam.ppd, y1 = H / 2 - (m.Y0 - my(cam.lat)) * cam.ppd;
  if (x1 < 0 || x0 > W || y1 < 0 || y0 > H) return;
  const covers = x0 <= 0 && x1 >= W && y0 <= 0 && y1 >= H;
  const g = covers ? ctx : lx;
  if (!covers) lx.clearRect(0, 0, W, H);
  g.save(); g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
  if (covers) g.globalAlpha = alpha;
  g.drawImage(m.summer, x0, y0, x1 - x0, y1 - y0);
  if (season > 0.003) { g.globalAlpha = (covers ? alpha : 1) * season; g.drawImage(m.autumn, x0, y0, x1 - x0, y1 - y0); }
  g.restore();
  if (!covers) {
    const f = 160; lx.save(); lx.globalCompositeOperation = 'destination-out';
    const edge = (gx0, gy0, gx1, gy1, rx, ry, rw, rh) => { const gr = lx.createLinearGradient(gx0, gy0, gx1, gy1); gr.addColorStop(0, 'rgba(0,0,0,1)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); lx.fillStyle = gr; lx.fillRect(rx, ry, rw, rh); };
    edge(x0, 0, x0 + f, 0, x0 - 2, 0, f + 2, H); edge(x1, 0, x1 - f, 0, x1 - f, 0, f + 2, H);
    edge(0, y0, 0, y0 + f, 0, y0 - 2, W, f + 2); edge(0, y1, 0, y1 - f, 0, y1 - f, W, f + 2);
    lx.restore(); ctx.save(); ctx.globalAlpha = alpha; ctx.drawImage(lay, 0, 0); ctx.restore();
  }
}
const sstep = (a, b, x) => ease(clamp((x - a) / (b - a)));
function drawMap(season = 0, bright = 1) {
  ctx.fillStyle = '#0a0d0f'; ctx.fillRect(0, 0, W, H);
  const aB = sstep(230, 400, cam.ppd), aC = sstep(1000, 1500, cam.ppd);
  if (aB < 1 || !covered('B')) drawTex('A', season, 1);
  if (aC < 1 || !covered('C')) drawTex('B', season, aB);
  drawTex('C', season, aC);
  drawRivers(aB, aC);
  if (bright < 1) { ctx.fillStyle = `rgba(5,7,9,${1 - bright})`; ctx.fillRect(0, 0, W, H); }
}
function covered(k) { const m = MAPS[k]; const hw = W / 2 / cam.ppd, hh = H / 2 / cam.ppd; return cam.lon - hw >= m.lon0 && cam.lon + hw <= m.lon1 && my(cam.lat) - hh >= m.Y0 && my(cam.lat) + hh <= m.Y1; }
function poly(pts, close) { ctx.beginPath(); for (let i = 0; i < pts.length; i++) { const [x, y] = P(pts[i][0], pts[i][1]); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } if (close) ctx.closePath(); }
function drawRivers(aB, aC) {
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  const hw = W / 2 / cam.ppd + .3, hh = H / 2 / cam.ppd + .3, cy = cam.lat;
  // overview rivers (Natural Earth)
  const aA = 1 - sstep(500, 900, cam.ppd);
  if (aA > 0.01) for (const r of D.ne) { ctx.strokeStyle = C.river + (0.5 * aA) + ')'; ctx.lineWidth = r.w * clamp(cam.ppd / 150, .8, 2.2); poly(r.pts); ctx.stroke(); }
  if (aA > 0.01) { ctx.strokeStyle = `rgba(150,170,180,${0.25 * aA})`; ctx.lineWidth = 1.2; for (const c of D.coast) { poly(c); ctx.stroke(); } }
  const draw = (arr, alpha, base, k) => { if (alpha < 0.01) return; for (const r of arr) { const p0 = r.pts[0]; if (Math.abs(p0[0] - cam.lon) > hw + 1.5 || Math.abs(p0[1] - cy) > hh + 1.5) continue; const w = clamp(0.5 + Math.log10(r.a[1] / base) * k, .5, 6) * clamp(cam.ppd / 1500, .55, 1.5); ctx.strokeStyle = C.river + (0.42 * alpha) + ')'; ctx.lineWidth = w; poly(r.pts); ctx.stroke(); } };
  draw(D.rivB, aB * (1 - aC), 150, 1.3);
  draw(D.rivC, aC, 12, 1.5);
  ctx.restore();
}
/* ---------- text ---------- */
function font(size, weight = 600, fam = SONG) { ctx.font = `${weight} ${size}px ${fam}`; }
function txt(s, x, y, o = {}) {
  const { size = 40, w = 600, fam = SONG, color = C.bone, align = 'center', a = 1, ls = 0, shadow = 1, base = 'middle', stroke = 0 } = o;
  if (a <= 0.003) return 0;
  ctx.save(); font(size, w, fam); ctx.textAlign = align; ctx.textBaseline = base; ctx.globalAlpha = a;
  try { ctx.letterSpacing = ls + 'px'; } catch (e) { }
  if (shadow) { ctx.shadowColor = `rgba(0,0,0,${0.85 * shadow})`; ctx.shadowBlur = size * 0.22; ctx.shadowOffsetY = 2; }
  if (stroke) { ctx.lineWidth = stroke; ctx.strokeStyle = 'rgba(0,0,0,0.8)'; ctx.lineJoin = 'round'; ctx.strokeText(s, x, y); }
  ctx.fillStyle = color; ctx.fillText(s, x, y);
  const wd = ctx.measureText(s).width; ctx.restore(); return wd;
}
const NOHEAD = '，。：；？！、）」』》”’…—', NOTAIL = '（「『《“‘';
function wrap(s, maxChars) { // CJK wrap with basic kinsoku
  const out = []; let cur = '';
  const cnt = x => [...x].reduce((n, ch) => n + (/[，。：；？！、「」《》“”]/.test(ch) ? 0.5 : 1), 0);
  for (const ch of [...s]) {
    if (ch === '\n') { out.push(cur); cur = ''; continue; }
    if (cnt(cur + ch) > maxChars && !NOHEAD.includes(ch)) { if (NOTAIL.includes(cur.slice(-1))) { const k = cur.slice(-1); out.push(cur.slice(0, -1)); cur = k + ch; } else { out.push(cur); cur = ch; } }
    else cur += ch;
  }
  if (cur) out.push(cur); return out;
}
function balance(s, maxChars) { // wrap into roughly equal rows
  let rows = wrap(s, maxChars); if (rows.length < 2) return rows;
  const n = rows.length; let best = rows, mc = maxChars;
  while (mc > 4) { mc -= .5; const r = wrap(s, mc); if (r.length > n) break; best = r; }
  return best;
}
/* ---------- primitives ---------- */
function glow(lon, lat, r, color, a) { const [x, y] = P(lon, lat); const R = r * cam.ppd; const g = ctx.createRadialGradient(x, y, 0, x, y, R); g.addColorStop(0, color); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, R, 0, 7); ctx.fill(); ctx.restore(); }
function place(lon, lat, name, o = {}) {
  const { a = 1, size = 34, dx = 14, dy = 0, color = C.bone, dot = 5, sub = '', align = 'left', w = 600, ring = 0, fam = SONG } = o; if (a <= 0.003) return;
  const [x, y] = P(lon, lat); ctx.save(); ctx.globalAlpha = a;
  if (dot) { ctx.fillStyle = 'rgba(0,0,0,.6)'; ctx.beginPath(); ctx.arc(x, y, dot + 2.5, 0, 7); ctx.fill(); ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x, y, dot, 0, 7); ctx.fill(); }
  if (ring) { ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.globalAlpha = a * (1 - ring); ctx.beginPath(); ctx.arc(x, y, dot + 6 + ring * 46, 0, 7); ctx.stroke(); }
  ctx.restore();
  const tx = x + (align === 'left' ? dx : align === 'right' ? -dx : 0);
  txt(name, tx, y + dy, { size, color, align, a, w, fam, stroke: 4 });
  if (sub) txt(sub, tx, y + dy + size * 0.95, { size: size * 0.62, color: C.note, align, a: a * .95, w: 500, fam: HEI, stroke: 3 });
}
function spline(pts, n = 24) { // Catmull-Rom through lon/lat points -> dense lon/lat
  const out = []; const g = i => pts[clamp(i, 0, pts.length - 1)];
  for (let i = 0; i < pts.length - 1; i++) { const p0 = g(i - 1), p1 = g(i), p2 = g(i + 1), p3 = g(i + 2); for (let k = 0; k < n; k++) { const t = k / n, t2 = t * t, t3 = t2 * t; out.push([0, 1].map(d => .5 * ((2 * p1[d]) + (-p0[d] + p2[d]) * t + (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * t2 + (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * t3))); } }
  out.push(pts[pts.length - 1]); return out;
}
function along(dense, p) { // point at fraction p of a dense lon/lat path
  const f = clamp(p) * (dense.length - 1), i = Math.min(dense.length - 2, Math.floor(f)), u = f - i; return [lerp(dense[i][0], dense[i + 1][0], u), lerp(dense[i][1], dense[i + 1][1], u)];
}
function arrow(pts, p, o = {}) { // animated tapered arrow along lon/lat control points
  const { color = C.zhao, width = 16, a = 1, head = 2.4, tail = 0.25, dash = 0, glowC = null, from = 0 } = o;
  if (p <= 0.002 || a <= 0.003) return;
  const d = spline(pts).map(q => P(q[0], q[1])); const n = d.length; const cum = [0]; for (let i = 1; i < n; i++) cum.push(cum[i - 1] + Math.hypot(d[i][0] - d[i - 1][0], d[i][1] - d[i - 1][1]));
  const Ltot = cum[n - 1], hl = Math.min(width * head, Ltot * .45), L = Math.max(hl + 2, Ltot * clamp(p)), L0 = Ltot * from;
  const at = s => { s = clamp(s, 0, Ltot); let i = 1; while (i < n - 1 && cum[i] < s) i++; const u = (s - cum[i - 1]) / Math.max(1e-6, cum[i] - cum[i - 1]); const x = lerp(d[i - 1][0], d[i][0], u), y = lerp(d[i - 1][1], d[i][1], u); const tx = d[i][0] - d[i - 1][0], ty = d[i][1] - d[i - 1][1], m = Math.hypot(tx, ty) || 1; return [x, y, tx / m, ty / m]; };
  const body = L - hl; const left = [], right = []; const steps = Math.max(8, Math.ceil(body / 8));
  for (let k = 0; k <= steps; k++) { const s = lerp(L0, body, k / steps); if (dash && Math.floor(s / dash) % 2) { } const [x, y, tx, ty] = at(s); const wv = width * (tail + (1 - tail) * ((s - L0) / Math.max(1, body - L0))) / 2; left.push([x - ty * wv, y + tx * wv]); right.push([x + ty * wv, y - tx * wv]); }
  const [bx, by, btx, bty] = at(body), [hx, hy] = at(L); const hw = width * 1.25;
  ctx.save(); ctx.globalAlpha = a;
  if (glowC) { ctx.shadowColor = glowC; ctx.shadowBlur = 22; }
  ctx.beginPath(); left.forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]));
  ctx.lineTo(bx - bty * hw, by + btx * hw); ctx.lineTo(hx + btx * 2, hy + bty * 2); ctx.lineTo(bx + bty * hw, by - btx * hw);
  for (let i = right.length - 1; i >= 0; i--) ctx.lineTo(right[i][0], right[i][1]); ctx.closePath();
  ctx.fillStyle = color; ctx.fill();
  if (o.rim) { ctx.shadowBlur = 0; ctx.strokeStyle = o.rim; ctx.lineWidth = 2; ctx.stroke(); }
  ctx.restore(); return [hx, hy];
}
function dashLine(pts, o = {}) { const { color = C.note, width = 3, a = 1, dash = [14, 10], p = 1, smooth = true } = o; if (a <= .003 || p <= 0) return; const d = smooth ? spline(pts, 16) : pts; const m = Math.max(2, Math.ceil(d.length * clamp(p))); ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = color; ctx.lineWidth = width; ctx.setLineDash(dash); ctx.lineCap = 'butt'; ctx.shadowColor = 'rgba(0,0,0,.7)'; ctx.shadowBlur = 6; poly(d.slice(0, m)); ctx.stroke(); ctx.restore(); }
function wall(pts, o = {}) { // fortification: thick segmented line with rim
  const { color = '#15191f', rim = C.qinRim, width = 11, a = 1, p = 1 } = o; if (a <= .003 || p <= 0) return; const d = spline(pts, 14); const m = Math.max(2, Math.ceil(d.length * clamp(p)));
  ctx.save(); ctx.globalAlpha = a; ctx.lineCap = 'butt'; ctx.lineJoin = 'round';
  ctx.shadowColor = 'rgba(0,0,0,.8)'; ctx.shadowBlur = 10; ctx.strokeStyle = rim; ctx.lineWidth = width + 4; ctx.setLineDash([18, 5]); poly(d.slice(0, m)); ctx.stroke();
  ctx.shadowBlur = 0; ctx.strokeStyle = color; ctx.lineWidth = width; poly(d.slice(0, m)); ctx.stroke(); ctx.restore();
}
/* ---------- troops ---------- */
function Troop(n, seed) { const r = rng(seed); this.n = n; this.g = []; for (let i = 0; i < n; i++) this.g.push([gauss(r), gauss(r), r(), r()]); }
const F = { // formations: i -> [lon,lat] using per-dot randoms g=[g1,g2,u1,u2]
  blob: (c, sx, sy, rot = 0) => g => { const cs = Math.cos(rot), sn = Math.sin(rot); const x = g[0] * sx, y = g[1] * sy; return [c[0] + x * cs - y * sn, c[1] + (x * sn + y * cs) * .82]; },
  band: (pts, hw) => { const d = spline(pts, 12); return g => { const q = along(d, g[2]); const q2 = along(d, Math.min(1, g[2] + .01)); const tx = q2[0] - q[0], ty = q2[1] - q[1], m = Math.hypot(tx, ty) || 1; return [q[0] - ty / m * g[0] * hw, q[1] + tx / m * g[0] * hw * .82]; }; },
  ell: (c, rx, ry, th) => g => { const an = g[2] * 6.2832, k = 1 + (g[3] - .5) * th; return [c[0] + Math.cos(an) * rx * k, c[1] + Math.sin(an) * ry * k]; },
  ring: (c, r0, r1, a0 = 0, a1 = 6.2832) => g => { const an = lerp(a0, a1, g[2]), rr = lerp(r0, r1, g[3]); return [c[0] + Math.cos(an) * rr, c[1] + Math.sin(an) * rr * .82]; },
};
function mixF(fa, fb, p, stag = .5) { return (g, i) => { const q = eio(clamp((p * (1 + stag) - g[3] * stag))); const a = fa(g, i), b = fb(g, i); return [lerp(a[0], b[0], q), lerp(a[1], b[1], q)]; }; }
function drawTroop(tr, f, o = {}) {
  const { side = 'zhao', a = 1, r = 3.1, alive = 1, dim = 0, t = 0, jit = 0 } = o; if (a <= .003) return [0, 0];
  const zhao = side === 'zhao'; let sx = 0, sy = 0, cnt = 0; const R = r * clamp(cam.ppd / 1750, .7, 1.25);
  ctx.save();
  for (let i = 0; i < tr.n; i++) {
    const g = tr.g[i]; if (g[3] > alive) continue;
    let [lo, la] = f(g, i); if (jit) { lo += Math.sin(t * 1.3 + i * 2.1) * jit; la += Math.cos(t * 1.1 + i * 1.7) * jit; }
    const [x, y] = P(lo, la); sx += x; sy += y; cnt++;
    if (x < -10 || x > W + 10 || y < -10 || y > H + 10) continue;
    const da = a * (1 - dim * (0.35 + 0.65 * g[2]));
    ctx.globalAlpha = da * .55; ctx.fillStyle = '#000'; ctx.beginPath(); ctx.arc(x, y + 1.5, R + 1.8, 0, 7); ctx.fill();
    ctx.globalAlpha = da;
    if (zhao) { ctx.fillStyle = C.zhao; ctx.beginPath(); ctx.arc(x, y, R, 0, 7); ctx.fill(); ctx.fillStyle = C.zhaoHi; ctx.beginPath(); ctx.arc(x - R * .25, y - R * .3, R * .42, 0, 7); ctx.fill(); }
    else { ctx.fillStyle = C.qinRim; ctx.beginPath(); ctx.arc(x, y, R + .9, 0, 7); ctx.fill(); ctx.fillStyle = C.qin; ctx.beginPath(); ctx.arc(x, y, R - .4, 0, 7); ctx.fill(); }
  }
  ctx.restore(); return cnt ? [sx / cnt, sy / cnt] : [0, 0];
}
function plate(x, y, s, o = {}) { // unit label plate at screen coords
  const { side = 'zhao', a = 1, size = 30, sub = '' } = o; if (a <= .003) return; ctx.save(); font(size, 700, SONG); const w = ctx.measureText(s).width + 26, h = size + 16; ctx.globalAlpha = a;
  ctx.shadowColor = 'rgba(0,0,0,.7)'; ctx.shadowBlur = 10; ctx.fillStyle = side === 'zhao' ? 'rgba(120,30,18,.92)' : side === 'qin' ? 'rgba(9,12,17,.94)' : 'rgba(30,30,30,.9)'; ctx.fillRect(x - w / 2, y - h / 2, w, h);
  ctx.shadowBlur = 0; ctx.strokeStyle = side === 'zhao' ? C.zhaoHi : side === 'qin' ? C.qinRim : C.note; ctx.lineWidth = 1.6; ctx.strokeRect(x - w / 2, y - h / 2, w, h); ctx.restore();
  txt(s, x, y + 1, { size, w: 700, color: side === 'zhao' ? '#ffe9df' : side === 'qin' ? C.qinHi : C.bone, a, shadow: 0 });
  if (sub) txt(sub, x, y + h / 2 + size * .5, { size: size * .68, fam: HEI, w: 500, color: C.note, a, stroke: 3 });
}
/* ---------- overlays ---------- */
function shade(a, y0 = 0, y1 = H) { if (a <= .003) return; ctx.fillStyle = `rgba(5,7,9,${a})`; ctx.fillRect(0, y0, W, y1 - y0); }
function band(y0, y1, a, soft = 90) { if (a <= .003) return; const g = ctx.createLinearGradient(0, y0 - soft, 0, y1 + soft); const k = soft / (y1 - y0 + 2 * soft); g.addColorStop(0, 'rgba(5,7,9,0)'); g.addColorStop(k, `rgba(5,7,9,${a})`); g.addColorStop(1 - k, `rgba(5,7,9,${a})`); g.addColorStop(1, 'rgba(5,7,9,0)'); ctx.fillStyle = g; ctx.fillRect(0, y0 - soft, W, y1 - y0 + 2 * soft); }
function rule(x0, x1, y, a, color = C.goldDim, w = 2) { if (a <= .003) return; ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = color; ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x1, y); ctx.stroke(); ctx.restore(); }
function quoteCard(text, src, a, o = {}) { // classical quote: big Song, gold; reveal by progress
  const { y = 560, size = 66, max = 11, p = 1, gloss = '', note = '', bg = .93 } = o; if (a <= .003) return;
  const rows = text.includes('\n') ? text.split('\n') : balance(text, max); const lh = size * 1.5; const h = rows.length * lh + (src ? 70 : 0) + (gloss ? 80 : 0) + (note ? 50 : 0);
  band(y - 70, y + h + 10, bg * a);
  rule(120, 960, y - 44, a * .8); const total = [...rows.join('')].length; let seen = 0;
  rows.forEach((r, i) => { const chars = [...r]; ctx.save(); font(size, 700, SONG); const wd = ctx.measureText(r).width; ctx.restore(); let x = W / 2 - wd / 2; chars.forEach(ch => { const ca = clamp((p * (total + 4) - seen)) * a; seen++; ctx.save(); font(size, 700, SONG); const cw = ctx.measureText(ch).width; ctx.restore(); txt(ch, x, y + i * lh + size * .5, { size, w: 700, color: C.gold, align: 'left', a: ca, shadow: .8 }); x += cw; }); });
  let yy = y + rows.length * lh + 8;
  if (src) { txt('—— ' + src, W / 2, yy + 14, { size: 30, fam: HEI, w: 500, color: C.goldDim, a: a * .95 }); yy += 62; }
  if (gloss) { txt(gloss, W / 2, yy + 18, { size: 36, fam: HEI, w: 500, color: C.bone, a: a * clamp(p * 3 - 1.6) }); yy += 70; }
  if (note) { txt(note, W / 2, yy + 8, { size: 26, fam: HEI, w: 400, color: C.note, a: a * .9 }); yy += 44; }
  rule(120, 960, yy + 6, a * .8);
}
function termCard(term, def, a, o = {}) { // glossary card
  const { y = 1110, sub = '' } = o; if (a <= .003) return; const rows = wrap(def, 15); const h = 96 + rows.length * 50 + (sub ? 40 : 0);
  ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = 'rgba(8,10,13,.86)'; ctx.fillRect(110, y, 860, h); ctx.fillStyle = C.gold; ctx.fillRect(110, y, 6, h); ctx.restore();
  txt(term, 150, y + 52, { size: 54, w: 800, color: C.gold, align: 'left', a, shadow: 0 });
  rows.forEach((r, i) => txt(r, 150, y + 118 + i * 50, { size: 36, fam: HEI, w: 500, color: C.bone, align: 'left', a, shadow: 0 }));
  if (sub) txt(sub, 150, y + 118 + rows.length * 50 + 4, { size: 25, fam: HEI, w: 400, color: C.note, align: 'left', a, shadow: 0 });
}
function tag(s, x, y, a, o = {}) { const { size = 25, color = C.note, align = 'left' } = o; if (a <= .003) return; ctx.save(); font(size, 500, HEI); const w = ctx.measureText(s).width + 20; const x0 = align === 'left' ? x : align === 'right' ? x - w : x - w / 2; ctx.globalAlpha = a * .8; ctx.fillStyle = 'rgba(6,8,10,.72)'; ctx.fillRect(x0, y - size * .75, w, size * 1.5); ctx.restore(); txt(s, x0 + 10, y, { size, fam: HEI, w: 500, color, align: 'left', a, shadow: 0 }); }
function header(t) { // persistent chapter label + chapter card
  const NUM = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九'];
  for (const k in SECS) { const s = SECS[k]; if (!s.title) continue; const nx = Object.values(SECS).find(q => q.i === s.i + 1); const end = nx ? nx.a - 1.0 : TOTAL;
    const ca = fade(t, s.a - 1.15, s.a + 1.5, .35, .5);
    if (ca > 0) { band(760, 1010, .82 * ca, 120); txt(NUM[s.i], W / 2, 800, { size: 40, w: 600, color: C.goldDim, a: ca, ls: 8 }); rule(430, 650, 842, ca * .9); txt(s.title, W / 2, 925, { size: [...s.title].length > 6 ? 92 : 112, w: 900, color: C.bone, a: ca, ls: 6 }); }
    const la = fade(t, s.a + 1.2, end, .5, .5); if (la > 0) { txt(NUM[s.i] + ' · ' + s.title, 64, 268, { size: 30, w: 600, color: C.goldDim, align: 'left', a: la * .95, stroke: 3 }); }
  }
}
function dateTag(s, a) { txt(s, W - 64, 268, { size: 32, w: 700, color: C.bone, align: 'right', a, stroke: 3 }); }
function vignette() { const g = ctx.createRadialGradient(W / 2, H * .5, H * .28, W / 2, H * .5, H * .72); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,.62)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); const g2 = ctx.createLinearGradient(0, 0, 0, H); g2.addColorStop(0, 'rgba(0,0,0,.5)'); g2.addColorStop(.16, 'rgba(0,0,0,0)'); g2.addColorStop(.68, 'rgba(0,0,0,0)'); g2.addColorStop(1, 'rgba(0,0,0,.72)'); ctx.fillStyle = g2; ctx.fillRect(0, 0, W, H); }
/* ---------- subtitles ---------- */
const SUBHIDE = []; // [t0,t1] ranges where subtitles are suppressed (quote shown on card)
function chunksOf(l) {
  if (l._c) return l._c; const parts = []; let cur = '';
  const chars = [...l.text]; let inQ = false;
  for (let i = 0; i < chars.length; i++) { const ch = chars[i]; cur += ch; if (ch === '「') inQ = true; if (ch === '」') inQ = false;
    const nx = chars[i + 1] || ''; const end = '。？！；'.includes(ch) && !'」”'.includes(nx) || (ch === '」' && '。？！；，：'.includes(chars[i - 1] || '')) || ('”'.includes(ch) && '。？！'.includes(chars[i - 1] || ''));
    const soft = '，：'.includes(ch) && !'」”'.includes(nx);
    if (end || (soft && [...cur].length >= 12 && chars.length - i > 5)) { parts.push(cur); cur = ''; } }
  if (cur) { if (parts.length && [...cur].length < 3) parts[parts.length - 1] += cur; else parts.push(cur); }
  // merge tiny pieces forward
  const m = []; for (const p of parts) { if (m.length && [...m[m.length - 1]].length + [...p].length <= 15 && !/[。？！]$/.test(m[m.length - 1].replace(/[」”]$/, ''))) m[m.length - 1] += p; else m.push(p); }
  const han = s => (s.match(/[一-鿿〇]/g) || []).length + 0.6 * (s.match(/[，。：；？！、]/g) || []).length;
  const tot = m.reduce((n, s) => n + han(s), 0); let acc = 0; const bounds = [l.t0];
  for (let i = 0; i < m.length - 1; i++) { acc += han(m[i]); let te = l.t0 + (l.t1 - l.t0) * acc / tot; let best = null, bd = .9; for (const p of l.pauses) { const mid = (p[0] + p[1]) / 2; if (mid <= bounds[bounds.length - 1] + .25) continue; const d = Math.abs(mid - te); if (d < bd) { bd = d; best = p; } } if (best) te = best[1] - .04; bounds.push(te); }
  bounds.push(l.t1); const out = m.map((s, i) => ({ s, a: bounds[i], b: bounds[i + 1] }));
  l._c = out; return out;
}
function subtitles(t) {
  for (const l of LINES) { if (t < l.t0 - .05 || t > l.t1 + .22) continue;
    const cs = chunksOf(l); for (let i = 0; i < cs.length; i++) { const c = cs[i]; const b = i === cs.length - 1 ? c.b + .22 : c.b; if (t < c.a - .02 || t >= b) continue;
      const a = Math.min(seg(t, c.a - .02, c.a + .1), 1 - seg(t, b - .08, b)); drawSub(c.s, a); return; } }
}
function drawSub(s, a) {
  s = s.replace(/[，。；：]$/, '').replace(/[，。；：]([」”])$/, '$1');
  const rows = balance(s, 15.5); const size = 52, lh = 74; const y0 = 1418 - (rows.length - 1) * lh / 2;
  band(y0 - 44, y0 + (rows.length - 1) * lh + 44, .5 * a, 46);
  let inQ = false;
  rows.forEach((r, i) => { ctx.save(); let wd = 0; const segs = []; let cur = '', q = inQ; for (const ch of [...r]) { if (ch === '「') { if (cur) segs.push([cur, q]); cur = ch; q = true; } else if (ch === '」') { cur += ch; segs.push([cur, true]); cur = ''; q = false; } else cur += ch; } if (cur) segs.push([cur, q]); inQ = q;
    segs.forEach(sg => { font(size, sg[1] ? 700 : 600, sg[1] ? SONG : HEI); sg[2] = ctx.measureText(sg[0]).width; wd += sg[2]; }); ctx.restore(); let x = W / 2 - wd / 2;
    segs.forEach(sg => { txt(sg[0], x, y0 + i * lh, { size, w: sg[1] ? 700 : 600, fam: sg[1] ? SONG : HEI, color: sg[1] ? C.gold : '#f4f1ea', align: 'left', a, stroke: 6, shadow: .9 }); x += sg[2]; }); });
}

/* ---------- grain ---------- */
const grainTile = (() => { const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d'); const im = g.createImageData(256, 256); const r = rng(999); for (let i = 0; i < 256 * 256; i++) { const v = 128 + (r() - .5) * 255; im.data[i * 4] = im.data[i * 4 + 1] = im.data[i * 4 + 2] = v; im.data[i * 4 + 3] = 255; } g.putImageData(im, 0, 0); return c; })();
function grain(t) { const f = Math.floor(t * 15); const r = rng(f * 7 + 1); const ox = Math.floor(r() * 256), oy = Math.floor(r() * 256); ctx.save(); ctx.globalAlpha = .05; ctx.globalCompositeOperation = 'overlay'; ctx.fillStyle = ctx.createPattern(grainTile, 'repeat'); ctx.translate(-ox, -oy); ctx.fillRect(0, 0, W + 256, H + 256); ctx.restore(); }
