'use strict';
/* ====================== 金崎撤退 — scenes ====================== */
const PL = {
  kyoto: [135.762, 35.012], biwa: [136.07, 35.26], odani: [136.275, 35.457], ichijo: [136.296, 35.996],
  kane: [136.0786, 35.6658], tezu: [136.090, 35.655], kinome: [136.137, 35.757], tsuruga: [136.066, 35.645],
  kuma: [135.882, 35.463], sagaki: [135.963, 35.596], kutsuki: [135.915, 35.357], ohara: [135.835, 35.118],
  sakamoto: [135.87, 35.07], imazu: [136.03, 35.41], fuchu: [136.17, 35.90], kinomoto: [136.22, 35.50],
  hikida: [136.10, 35.60], anegawa: [136.304, 35.414], nagahama: [136.264, 35.381], wakasa: [135.70, 35.52],
};
const CAMS = {
  wide: [136.0, 35.52, 1000], wideHi: [136.02, 35.52, 1000], north: [136.12, 35.70, 1500],
  bay: [136.075, 35.675, 6200], bayWide: [136.06, 35.665, 4200], castle: [136.082, 35.662, 9000],
  kutsuki: [135.90, 35.34, 2100], azai: [136.2, 35.42, 2200],
};
const ROUTE_OUT = [PL.kyoto, PL.sakamoto, [135.95, 35.20], PL.imazu, PL.kuma, PL.sagaki, [136.02, 35.625], PL.tsuruga];
const ROUTE_BACK = [PL.tsuruga, [136.02, 35.625], PL.sagaki, PL.kuma, PL.kutsuki, PL.ohara, PL.kyoto];
const ASA_IN = [PL.ichijo, PL.fuchu, PL.kinome, [136.11, 35.70]];
const AZ_IN = [PL.odani, PL.kinomoto, [136.17, 35.57], PL.hikida];
const AZ_CUT = [PL.odani, [136.16, 35.40], [136.05, 35.38], [135.97, 35.40]];

/* ---------- small helpers ---------- */
const blk = (t, v1, v2, fi = 0.4, fo = 0.4) => fade(t, A(v1) - 0.3, NX(v2 || v1) + 0.05, fi, fo);
const rise = (t, v, d = 0.6, off = 0) => ease(seg(t, A(v) + off - 0.2, A(v) + off - 0.2 + d));
function bigText(lines, y, a, o = {}) { const { size = 76, color = '#fff3dc', gap = 1.35, w = 900, ls = 4, fam = SONG } = o; lines.forEach((s, i) => txt(s, W / 2, y + i * size * gap, { size, w, color, a, stroke: 7, ls, fam })); }
function dimAll(a) { if (a > 0.003) { ctx.fillStyle = `rgba(2,4,8,${a})`; ctx.fillRect(0, 0, W, H); } }
function tag(s, a = 1, y = 1780) { if (a > 0.01) txt(s, W - 46, y, { size: 22, w: 400, color: 'rgba(230,225,210,0.62)', align: 'right', a, shadow: 0.8 }); }
function stamp(s, x, y, a, rot = -0.1, col = '#e0473a', size = 64) { if (a <= 0.01) return; ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.rotate(rot); const k = 1 + 0.5 * (1 - ease(a)); ctx.scale(k, k); ctx.strokeStyle = col; ctx.lineWidth = 6; font(size, 900, SONG); const w = ctx.measureText(s).width + 56; ctx.strokeRect(-w / 2, -size * 0.85, w, size * 1.7); ctx.fillStyle = col; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(s, 0, 4); ctx.restore(); }
function mixc(a, b, p) { const pa = [1, 3, 5].map(i => parseInt(a.substr(i, 2), 16)), pb = [1, 3, 5].map(i => parseInt(b.substr(i, 2), 16)); return `rgb(${pa.map((v, i) => Math.round(lerp(v, pb[i], p))).join(',')})`; }
function glowDot(x, y, r, col, a = 1) { if (a <= 0.01) return; ctx.save(); ctx.globalAlpha = a; ctx.globalCompositeOperation = 'lighter'; const g = ctx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, col); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill(); ctx.restore(); }
function shake(t, t0, amp = 10, dur = 0.35) { const k = 1 - seg(t, t0, t0 + dur); if (t < t0 || k <= 0) return [0, 0]; return [Math.sin(t * 91) * amp * k, Math.cos(t * 77) * amp * k]; }
function bgGrad(c0, c1, a = 1) { ctx.save(); ctx.globalAlpha = a; const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, c0); g.addColorStop(1, c1); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore(); }
function paperBg(a = 1) {
  if (a <= 0.01) return; ctx.save(); ctx.globalAlpha = a; const g = ctx.createRadialGradient(W / 2, H * 0.45, 100, W / 2, H * 0.5, H * 0.75); g.addColorStop(0, '#2a241c'); g.addColorStop(1, '#0b0907'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.globalAlpha = a * 0.07; ctx.strokeStyle = '#d8c7a0'; ctx.lineWidth = 1; for (let i = 0; i < 70; i++) { const y = hash(i * 3) * H; ctx.beginPath(); ctx.moveTo(0, y); ctx.bezierCurveTo(W * 0.3, y + 20 * Math.sin(i), W * 0.7, y - 20, W, y + 10); ctx.stroke(); } ctx.restore();
}
function rain(t, a = 0.5, n = 220, ang = 0.18) { if (a <= 0.01) return; ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = 'rgba(190,205,230,0.35)'; ctx.lineWidth = 1.4; ctx.beginPath(); for (let i = 0; i < n; i++) { const sp = 1400 + hash(i) * 900; const x = (hash(i * 7) * (W + 400) - 200 + t * sp * ang) % (W + 400) - 100; const y = (hash(i * 13) * H + t * sp) % (H + 200) - 100; ctx.moveTo(x, y); ctx.lineTo(x - 40 * ang * 3, y - 40); } ctx.stroke(); ctx.restore(); }
function smokeField(t, a, seed = 1, n = 16, y0 = 900, y1 = 1500, col = '150,150,160') { if (a <= 0.01) return; ctx.save(); for (let i = 0; i < n; i++) { const x = ((hash(i * 5 + seed) * W * 1.4 + t * (12 + hash(i) * 22)) % (W * 1.4)) - W * 0.2; const y = lerp(y0, y1, hash(i * 9 + seed)) + Math.sin(t * 0.3 + i) * 20; const r = 120 + hash(i * 3 + seed) * 220; const g = ctx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, `rgba(${col},${0.16 * a})`); g.addColorStop(1, `rgba(${col},0)`); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill(); } ctx.restore(); }
function embers(t, a, seed = 1, n = 50) { if (a <= 0.01) return; ctx.save(); ctx.globalCompositeOperation = 'lighter'; for (let i = 0; i < n; i++) { const ph = (t * (0.08 + hash(i + seed) * 0.08) + hash(i * 3 + seed)) % 1; const x = hash(i * 7 + seed) * W + Math.sin(t * 1.3 + i) * 30, y = H * (1.05 - ph * 1.1); ctx.fillStyle = `rgba(255,${140 + 80 * hash(i)},60,${a * 0.8 * Math.sin(ph * Math.PI)})`; ctx.beginPath(); ctx.arc(x, y, 1.5 + 2.5 * hash(i * 11), 0, Math.PI * 2); ctx.fill(); } ctx.restore(); }

/* ---------- landscape: dusk / night / dawn mountain road with lone castle ---------- */
function ridge(seed, y, amp, x0 = -300, x1 = W + 300) { const pts = []; for (let x = x0; x <= x1; x += 12) { const u = x / W; const h = Math.sin(u * 5.1 + seed) * 0.5 + Math.sin(u * 11.7 + seed * 2.3) * 0.25 + Math.sin(u * 23 + seed * 4.1) * 0.12 + Math.sin(u * 47 + seed * 7) * 0.05; pts.push([x, y - amp * (0.6 + h)]); } return pts; }
const RIDGES = [ridge(1.2, 820, 160), ridge(3.4, 960, 190), ridge(5.1, 1160, 230), ridge(7.7, 1500, 260)];
const ROAD = [[620, 1010], [560, 1050], [690, 1110], [470, 1200], [800, 1330], [330, 1500], [900, 1700], [200, 1950], [-200, 2200]];
function sky(mood, a = 1) {
  const S = { dusk: ['#141428', '#4a2a3a', '#b0573a', '#f09a55'], night: ['#03050c', '#0a1222', '#18243a', '#2a3048'], dawn: ['#18223a', '#4a4a62', '#c98a62', '#f6cf96'] }[mood];
  ctx.save(); ctx.globalAlpha = a; const g = ctx.createLinearGradient(0, 0, 0, 1000); S.forEach((c, i) => g.addColorStop(i / 3, c)); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  if (mood !== 'night') { const sg = ctx.createRadialGradient(W * 0.28, 820, 0, W * 0.28, 820, 600); sg.addColorStop(0, mood === 'dawn' ? 'rgba(255,230,170,0.8)' : 'rgba(255,170,90,0.7)'); sg.addColorStop(1, 'rgba(255,150,80,0)'); ctx.fillStyle = sg; ctx.fillRect(0, 0, W, H); }
  else { for (let i = 0; i < 90; i++) { ctx.fillStyle = `rgba(230,235,255,${0.25 + 0.5 * hash(i * 3)})`; ctx.fillRect(hash(i) * W, hash(i * 7) * 700, 1.6, 1.6); } }
  ctx.restore();
}
function landscape(t, o = {}) {
  const { mood = 'dusk', z = 1, fx = 620, fy = 1000, torches = 1, banner = 1, empty = 0, rainA = 0, fireA = 0, seed = 1, mainA = 1 } = o;
  sky(mood);
  const cols = { dusk: ['#5a3a48', '#3a2530', '#22161c', '#0c0809'], night: ['#1a2234', '#121827', '#0b0f19', '#05070b'], dawn: ['#7a6a78', '#4c4352', '#2c2730', '#120f12'] }[mood];
  const par = [0.25, 0.5, 1.0, 1.6];
  for (let k = 0; k < 4; k++) {
    const s = 1 + (z - 1) * par[k];
    ctx.save(); ctx.translate(fx, fy); ctx.scale(s, s); ctx.translate(-fx, -fy);
    ctx.fillStyle = cols[k]; ctx.beginPath(); ctx.moveTo(-400, H + 600); RIDGES[k].forEach(p => ctx.lineTo(p[0], p[1])); ctx.lineTo(W + 400, H + 600); ctx.closePath(); ctx.fill();
    if (k === 1) { // haze
      const hz = ctx.createLinearGradient(0, 700, 0, 1100); hz.addColorStop(0, 'rgba(0,0,0,0)'); hz.addColorStop(1, mood === 'night' ? 'rgba(40,50,80,0.25)' : 'rgba(255,150,100,0.12)'); ctx.fillStyle = hz; ctx.fillRect(-400, 600, W + 800, 600);
    }
    if (k === 2) { castleHill(t, { banner, empty, mood }); roadAndTorches(t, torches, mood, mainA); }
    ctx.restore();
  }
  if (fireA > 0) embers(t, fireA, seed);
  if (rainA > 0) rain(t, rainA);
}
function castleHill(t, o) {
  const { banner = 1, empty = 0, mood } = o;
  const x = 620, y = 1000, dark = mood === 'night' ? '#070a10' : mood === 'dawn' ? '#1e1a20' : '#140c10';
  ctx.save();
  // hill
  ctx.fillStyle = dark; ctx.beginPath(); ctx.moveTo(x - 260, y + 140); ctx.quadraticCurveTo(x - 120, y - 10, x - 40, y - 20); ctx.lineTo(x + 70, y - 22); ctx.quadraticCurveTo(x + 170, y - 5, x + 280, y + 140); ctx.closePath(); ctx.fill();
  // palisade + gate tower (yagura)
  ctx.fillStyle = dark; for (let i = -9; i <= 9; i++) { const px = x + i * 10, ph = 14 + (i % 2) * 3; ctx.fillRect(px - 3, y - 22 - ph, 6, ph); }
  ctx.fillRect(x - 34, y - 70, 54, 50); ctx.beginPath(); ctx.moveTo(x - 46, y - 66); ctx.lineTo(x - 7, y - 92); ctx.lineTo(x + 32, y - 66); ctx.closePath(); ctx.fill();
  // lit window
  const lw = mood === 'dawn' ? 0 : (1 - empty) * (0.7 + 0.3 * Math.sin(t * 7));
  if (lw > 0) { ctx.fillStyle = `rgba(255,170,80,${lw})`; ctx.fillRect(x - 14, y - 56, 12, 8); glowDot(x - 8, y - 52, 30, 'rgba(255,150,60,0.6)', lw); }
  // single banner (nobori) — plain vermilion cloth, no emblem
  if (banner > 0.01) {
    const bx = x + 46, by = y - 30; ctx.strokeStyle = dark; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(bx, by - 120); ctx.stroke();
    ctx.globalAlpha = banner; ctx.fillStyle = '#c8281c'; ctx.beginPath(); ctx.moveTo(bx, by - 116); ctx.lineTo(bx + 4, by - 118);
    for (let k = 0; k <= 10; k++) { const yy = by - 116 + k * 8.5; ctx.lineTo(bx + 26 + Math.sin(t * 5 + k * 0.7) * 4, yy); }
    ctx.lineTo(bx, by - 30); ctx.closePath(); ctx.fill();
    ctx.fillStyle = 'rgba(255,200,160,0.35)'; ctx.fillRect(bx + 1, by - 116, 26, 4);
    ctx.globalAlpha = 1;
  }
  // a few defenders' torches on the wall
  if (!empty && mood !== 'dawn') for (let i = 0; i < 5; i++) glowDot(x - 80 + i * 40, y - 40 + Math.sin(i) * 4, 16 + 4 * Math.sin(t * 9 + i), 'rgba(255,160,70,0.9)', 0.9);
  ctx.restore();
}
function roadPath() { const pts = smooth(ROAD, 10); const L = [0]; for (let i = 1; i < pts.length; i++) L.push(L[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])); return { p: pts, L, len: L[L.length - 1] }; }
const RP = roadPath();
function roadAt(s) { return samplePx(RP, s * RP.len); }
function roadAndTorches(t, a, mood, mainA = 1) {
  // road ribbon
  ctx.save(); ctx.strokeStyle = mood === 'night' ? 'rgba(60,60,70,0.5)' : 'rgba(90,60,50,0.5)'; ctx.lineCap = 'round';
  for (let i = 1; i < RP.p.length; i++) { const s = i / RP.p.length; ctx.lineWidth = 6 + s * 70; ctx.beginPath(); ctx.moveTo(RP.p[i - 1][0], RP.p[i - 1][1]); ctx.lineTo(RP.p[i][0], RP.p[i][1]); ctx.stroke(); }
  ctx.restore();
  if (a <= 0.01) return;
  const N = 230;
  for (let i = 0; i < N; i++) {
    const s = ((hash(i * 3.1) + t * 0.022) % 1); // flow from castle (0) toward viewer (1)
    if (s < 0.06) continue;
    const vis = a * mainA * Math.min(1, (s - 0.06) * 8);
    const [x, y, an] = roadAt(s); const off = (hash(i * 7) - 0.5) * (8 + s * 120);
    const px = x + Math.cos(an + Math.PI / 2) * off, py = y + Math.sin(an + Math.PI / 2) * off;
    const sz = 3 + s * s * 30;
    // marching figure (dark) + torch glow
    ctx.save(); ctx.globalAlpha = vis; ctx.fillStyle = '#050304'; ctx.fillRect(px - sz * 0.35, py - sz * 2.2, sz * 0.7, sz * 2.2); ctx.restore();
    if (hash(i * 5) < 0.55) glowDot(px + sz * 0.5, py - sz * 2.6, sz * 3.4 * (0.85 + 0.15 * Math.sin(t * 11 + i)), 'rgba(255,150,60,0.85)', vis);
    if (hash(i * 13) < 0.12 && s > 0.3) { ctx.save(); ctx.globalAlpha = vis; ctx.strokeStyle = '#050304'; ctx.lineWidth = Math.max(1, sz * 0.12); ctx.beginPath(); ctx.moveTo(px, py - sz * 2); ctx.lineTo(px - sz * 0.3, py - sz * 5); ctx.stroke(); ctx.restore(); }
  }
}

/* ---------- horse + rider silhouette (side view, facing +x) ---------- */
function rider(x, y, s, ph, o = {}) {
  const { col = '#050506', a = 1, flag = '#b8261a', dir = 1 } = o; if (a <= 0.01) return;
  ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.scale(s * dir, s); ctx.fillStyle = col; ctx.strokeStyle = col; ctx.lineCap = 'round';
  const bob = Math.sin(ph * 2) * 3;
  ctx.translate(0, bob);
  // legs
  ctx.lineWidth = 7; const L = (hx, hy, p) => { const k = Math.sin(p); ctx.beginPath(); ctx.moveTo(hx, hy); const kx = hx + k * 22, ky = hy + 34; ctx.lineTo(kx, ky); ctx.lineTo(kx + Math.sin(p + 1.2) * 16, ky + 32); ctx.stroke(); };
  L(40, -6, ph); L(30, -6, ph + 2.4); L(-38, -6, ph + 1.1); L(-48, -6, ph + 3.6);
  // body
  ctx.beginPath(); ctx.ellipse(-4, -22, 62, 24, 0, 0, Math.PI * 2); ctx.fill();
  // neck/head
  ctx.beginPath(); ctx.moveTo(40, -36); ctx.lineTo(74, -78 + Math.sin(ph * 2) * 4); ctx.lineTo(98, -66 + Math.sin(ph * 2) * 4); ctx.lineTo(96, -56); ctx.lineTo(70, -52); ctx.lineTo(58, -16); ctx.closePath(); ctx.fill();
  // tail
  ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(-64, -30); ctx.quadraticCurveTo(-96, -26 + Math.sin(ph * 2) * 8, -104, 6); ctx.stroke();
  // rider
  ctx.beginPath(); ctx.moveTo(-14, -42); ctx.lineTo(10, -42); ctx.lineTo(18, -98); ctx.lineTo(-4, -100); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.arc(10, -112, 12, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.moveTo(-6, -120); ctx.lineTo(28, -120); ctx.lineTo(10, -132); ctx.closePath(); ctx.fill(); // jingasa hat
  // sashimono (back flag)
  ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(-6, -90); ctx.lineTo(-14, -176); ctx.stroke();
  ctx.fillStyle = flag; ctx.beginPath(); ctx.moveTo(-14, -176); ctx.lineTo(-44 - Math.sin(ph) * 4, -172); ctx.lineTo(-40 - Math.sin(ph + 1) * 4, -128); ctx.lineTo(-10, -132); ctx.closePath(); ctx.fill();
  ctx.restore();
}
/* ashigaru gunner silhouette (kneeling, facing +x) */
function gunner(x, y, s, fire, o = {}) {
  const { col = '#060506', a = 1, dir = 1 } = o; if (a <= 0.01) return;
  ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.scale(s * dir, s); ctx.fillStyle = col; ctx.strokeStyle = col;
  ctx.beginPath(); ctx.moveTo(-24, 0); ctx.lineTo(18, 0); ctx.lineTo(10, -30); ctx.lineTo(-8, -34); ctx.lineTo(-30, -16); ctx.closePath(); ctx.fill(); // legs kneel
  ctx.beginPath(); ctx.moveTo(-14, -30); ctx.lineTo(10, -32); ctx.lineTo(14, -78); ctx.lineTo(-10, -80); ctx.closePath(); ctx.fill(); // torso
  ctx.beginPath(); ctx.arc(8, -92, 11, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.moveTo(-16, -98); ctx.lineTo(32, -98); ctx.lineTo(8, -112); ctx.closePath(); ctx.fill();
  ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(-6, -74); ctx.lineTo(84, -80); ctx.stroke(); // musket
  ctx.restore();
  if (fire > 0) { const mx = x + 88 * s * dir, my = y - 80 * s; glowDot(mx, my, 110 * s * fire, 'rgba(255,240,190,1)', fire); glowDot(mx + 50 * s * dir, my, 230 * s * fire, 'rgba(255,140,40,0.9)', fire); ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.globalAlpha = fire; ctx.fillStyle = 'rgba(255,230,170,0.9)'; ctx.beginPath(); ctx.moveTo(mx, my - 6 * s); ctx.lineTo(mx + 90 * s * dir, my); ctx.lineTo(mx, my + 6 * s); ctx.fill(); ctx.restore(); }
}
function smokePuff(x, y, age, s = 1, a = 1) { if (age < 0 || age > 3) return; const r = (30 + age * 70) * s; ctx.save(); const g = ctx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, `rgba(210,205,200,${0.35 * a * (1 - age / 3)})`); g.addColorStop(1, 'rgba(210,205,200,0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x + age * 40 * s, y - age * 20 * s, r, 0, Math.PI * 2); ctx.fill(); ctx.restore(); }
function soldier(x, y, s, o = {}) { const { col = '#060506', a = 1, spear = 1, ph = 0, run = 0 } = o; if (a <= 0.01) return; ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.scale(s, s); ctx.fillStyle = col; ctx.strokeStyle = col; ctx.lineCap = 'round'; ctx.lineWidth = 6; const k = Math.sin(ph) * run; ctx.beginPath(); ctx.moveTo(0, -40); ctx.lineTo(-10 + k * 14, 0); ctx.moveTo(0, -40); ctx.lineTo(10 - k * 14, 0); ctx.stroke(); ctx.beginPath(); ctx.moveTo(-10, -40); ctx.lineTo(10, -40); ctx.lineTo(8, -84); ctx.lineTo(-8, -84); ctx.closePath(); ctx.fill(); ctx.beginPath(); ctx.arc(0, -96, 10, 0, Math.PI * 2); ctx.fill(); ctx.beginPath(); ctx.moveTo(-18, -100); ctx.lineTo(18, -100); ctx.lineTo(0, -114); ctx.closePath(); ctx.fill(); if (spear) { ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(12, -20); ctx.lineTo(20, -190); ctx.stroke(); } ctx.restore(); }

/* ---------- night camp (jinmaku) ---------- */
function camp(t, a = 1, o = {}) {
  if (a <= 0.01) return; const { lead = 0 } = o;
  ctx.save(); ctx.globalAlpha = a;
  bgGrad('#05060a', '#140d0a');
  // curtain
  const cy = 860, ch = 420; ctx.fillStyle = '#d9d0bd'; ctx.fillRect(-20, cy, W + 40, ch);
  ctx.fillStyle = '#1c1612'; ctx.fillRect(-20, cy + ch * 0.38, W + 40, ch * 0.24);
  for (let x = 0; x < W; x += 180) { ctx.fillStyle = 'rgba(0,0,0,0.25)'; ctx.fillRect(x, cy, 6, ch); }
  const sh = ctx.createLinearGradient(0, cy, 0, cy + ch); sh.addColorStop(0, 'rgba(0,0,0,0.1)'); sh.addColorStop(1, 'rgba(0,0,0,0.55)'); ctx.fillStyle = sh; ctx.fillRect(-20, cy, W + 40, ch);
  // ground
  ctx.fillStyle = '#0b0807'; ctx.fillRect(0, cy + ch, W, H - cy - ch);
  // torches
  for (const tx_ of [120, W - 120]) { ctx.fillStyle = '#120c08'; ctx.fillRect(tx_ - 6, 700, 12, 700); fire(tx_, 700, t, 0.9, 1, tx_); glowDot(tx_, 700, 380, 'rgba(255,140,50,0.35)', 1); }
  // seated commander from behind (generic silhouette, not a portrait)
  ctx.fillStyle = '#060404'; const bx = W / 2, by = 1370;
  ctx.beginPath(); ctx.moveTo(bx - 150, by); ctx.lineTo(bx - 120, by - 200); ctx.quadraticCurveTo(bx, by - 250, bx + 120, by - 200); ctx.lineTo(bx + 150, by); ctx.closePath(); ctx.fill();
  ctx.beginPath(); ctx.arc(bx, by - 260, 48, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.moveTo(bx - 60, by - 290); ctx.lineTo(bx + 60, by - 290); ctx.lineTo(bx + 30, by - 320); ctx.lineTo(bx - 30, by - 320); ctx.closePath(); ctx.fill();
  ctx.restore();
  embers(t, a * 0.7, 9, 40);
}
/* ---------- letter (dramatized) ---------- */
function letter(x, y, s, a, cols, o = {}) {
  if (a <= 0.01) return; const { rot = 0 } = o;
  ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s);
  ctx.shadowColor = 'rgba(0,0,0,0.7)'; ctx.shadowBlur = 30; ctx.fillStyle = '#e9dcbc'; ctx.fillRect(-230, -330, 460, 660); ctx.shadowBlur = 0;
  ctx.fillStyle = 'rgba(120,90,50,0.15)'; for (let i = 0; i < 8; i++) ctx.fillRect(-230, -330 + i * 82, 460, 2);
  font(54, 700, JP); ctx.fillStyle = '#1b130c'; ctx.textAlign = 'center'; ctx.textBaseline = 'top';
  cols.forEach((c, j) => { [...c].forEach((ch, i) => ctx.fillText(ch, 160 - j * 100, -290 + i * 62)); });
  ctx.restore();
}

/* ---------- diagrams ---------- */
function unitBox(x, y, w, h, col, a, o = {}) { if (a <= 0.01) return; const { label: lb = '', hi = '#fff', glow = 18 } = o; ctx.save(); ctx.globalAlpha = a; ctx.shadowColor = col; ctx.shadowBlur = glow; ctx.fillStyle = col; ctx.fillRect(x - w / 2, y - h / 2, w, h); ctx.shadowBlur = 0; ctx.strokeStyle = hi; ctx.lineWidth = 2; ctx.strokeRect(x - w / 2, y - h / 2, w, h); ctx.restore(); if (lb) txt(lb, x, y, { size: Math.min(34, h * 0.6), w: 800, color: '#fff', a, shadow: 0.8 }); }
function arrow2(x0, y0, x1, y1, a, col, w = 10) { if (a <= 0.01) return; const an = Math.atan2(y1 - y0, x1 - x0); ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = w; ctx.shadowColor = col; ctx.shadowBlur = 12; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1 - Math.cos(an) * w * 2, y1 - Math.sin(an) * w * 2); ctx.stroke(); ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x1 - Math.cos(an - 0.5) * w * 3.4, y1 - Math.sin(an - 0.5) * w * 3.4); ctx.lineTo(x1 - Math.cos(an + 0.5) * w * 3.4, y1 - Math.sin(an + 0.5) * w * 3.4); ctx.fill(); ctx.restore(); }
function nameCard(x, y, name, sub, col, a, o = {}) { if (a <= 0.01) return; const { w = 300, h = 140 } = o; panel(x - w / 2, y - h / 2, w, h, a, 'rgba(8,10,14,0.85)'); ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = col; ctx.fillRect(x - w / 2, y - h / 2, 8, h); ctx.restore(); txt(name, x, y - (sub ? 18 : 0), { size: 46, w: 900, color: '#fff3dc', a }); if (sub) txt(sub, x, y + 36, { size: 26, w: 500, color: C.bone, a }); }
function checkMark(x, y, s, a, col = '#7fe08a') { if (a <= 0.01) return; ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = col; ctx.lineWidth = s * 0.2; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x - s, y); ctx.lineTo(x - s * 0.3, y + s * 0.7); ctx.lineTo(x + s, y - s * 0.8); ctx.stroke(); ctx.restore(); }
function crossMark(x, y, s, a, col = '#ff4a3a') { if (a <= 0.01) return; ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = col; ctx.lineWidth = s * 0.2; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x - s, y - s); ctx.lineTo(x + s, y + s); ctx.moveTo(x + s, y - s); ctx.lineTo(x - s, y + s); ctx.stroke(); ctx.restore(); }
function pincerJaws(cx, cy, p, a) { // stylized jaws closing on a red core
  if (a <= 0.01) return; ctx.save(); ctx.globalAlpha = a;
  const op = lerp(1.0, 0.12, ease(p));
  for (const [sgn, col] of [[-1, C.pe], [1, C.az]]) { ctx.save(); ctx.translate(cx, cy); ctx.rotate(sgn * op * 0.9); ctx.fillStyle = col; ctx.shadowColor = col; ctx.shadowBlur = 30; ctx.beginPath(); ctx.moveTo(-420, sgn * 30); ctx.quadraticCurveTo(-120, sgn * 230, 60, sgn * 40); ctx.lineTo(40, sgn * 10); ctx.quadraticCurveTo(-140, sgn * 140, -420, sgn * 70); ctx.closePath(); ctx.fill(); ctx.restore(); }
  ctx.restore();
}

/* ---------- map layer helpers ---------- */
function baseLabels(a, set = 'all') {
  if (a <= 0.01) return;
  areaLabel(PL.biwa[0], PL.biwa[1], '琵琶湖', { a: a * 0.9, size: 40, color: 'rgba(200,225,240,0.85)' });
  label(...PL.kyoto, '京都', { a, color: '#fff3dc' });
  if (set !== 'nok') {
    label(...PL.odani, '小谷城', { a, color: C.azHi, sub: '浅井', dx: 70, dy: -10 });
    label(...PL.ichijo, '一乘谷', { a, color: C.peHi, sub: '朝仓', dx: 0, dy: -36 });
    label(...PL.tsuruga, '敦贺', { a, color: '#fff3dc', dx: -70, dy: 10 });
    areaLabel(135.62, 35.58, '若狭', { a: a * 0.8, size: 46 });
    areaLabel(136.33, 35.85, '越前', { a: a * 0.8, size: 46 });
    areaLabel(136.28, 35.22, '近江', { a: a * 0.8, size: 46 });
  }
}
function mapCam(t, keys) { setCam(camKeys(t, keys)); drawMap(); }
function regionGlow(lon, lat, rDeg, col, a) { if (a <= 0.01) return; const [x, y] = P(lon, lat); const r = rDeg * cam.ppd; ctx.save(); ctx.globalAlpha = a; ctx.globalCompositeOperation = 'screen'; const g = ctx.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, col); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill(); ctx.restore(); }
function armyBlob(lon, lat, col, a, t, n = 40, spread = 0.025, seed = 1) { if (a <= 0.01) return; const [cx, cy] = P(lon, lat); const R = spread * cam.ppd; ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = col; ctx.shadowColor = col; ctx.shadowBlur = 10; for (let i = 0; i < n; i++) { const r = Math.sqrt(hash(i * 3 + seed)) * R, an = hash(i * 7 + seed) * Math.PI * 2 + t * 0.05; const x = cx + Math.cos(an) * r, y = cy + Math.sin(an) * r * 0.8; ctx.fillRect(x - 5, y - 3, 10, 6); } ctx.restore(); }
function routeLine(pts, p, col, a, w = 6, dash = true) { if (a <= 0.01 || p <= 0) return; const pp = pathPx(smooth(pts)); ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = col; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.shadowColor = col; ctx.shadowBlur = 14; if (dash) ctx.setLineDash([w * 2.4, w * 1.6]); ctx.beginPath(); const end = pp.len * p; for (let d = 0, k = 0; d <= end; d += 5, k++) { const [x, y] = samplePx(pp, d); k ? ctx.lineTo(x, y) : ctx.moveTo(x, y); } ctx.stroke(); ctx.restore(); const [hx, hy] = samplePx(pp, end); glowDot(hx, hy, w * 5, col, a); }

/* ================= SCENES ================= */
const SCN = {};

/* ---------- s0 hook ---------- */
SCN.s0 = function (t) {
  let mapOn = 0;
  // A. landscape: dusk retreat, camera pushes against the flow toward lone castle (0 → hook_name end)
  const aL = 1 - ease(seg(t, NX('hook_name') - 0.4, NX('hook_name') + 0.1));
  if (aL > 0) {
    const z = lerp(1.2, 1.95, eio(seg(t, 0, NX('hook_name'))));
    landscape(t, { mood: 'dusk', z, fireA: 0.8 });
    let [sx, sy] = shake(t, 1.05, 16, 0.5); const q2 = shake(t, 1.45, 12, 0.5); sx += q2[0]; sy += q2[1];
    const fl = t >= 1.05 ? 1 - seg(t, 1.05, 1.35) : 0; if (fl > 0) { ctx.save(); ctx.globalAlpha = fl * 0.35; ctx.fillStyle = '#ffd9a0'; ctx.fillRect(0, 0, W, H); ctx.restore(); }
    ctx.save(); ctx.translate(sx, sy);
    const a1 = 1 - ease(seg(t, A('hook') + 4.6, A('hook') + 5.0));
    txt('元龟元年 · 1570', W / 2, 250, { size: 40, w: 700, color: C.gold, a: a1, ls: 8 });
    bigText(['三万大军', '掉头南撤'], 380, a1, { size: 104, ls: 10 });
    const a2 = ease(seg(t, A('hook') + 3.2, A('hook') + 3.8)) * (1 - ease(seg(t, A('hook_name') - 0.4, A('hook_name'))));
    const a2b = a2 * ease(seg(t, A('hook') + 4.6, A('hook') + 5.0));
    txt('留在原地断后的是——', W / 2, 650 - 440 * a2b, { size: 46, w: 700, color: C.bone, a: a2, stroke: 5 });
    const a3 = ease(seg(t, A('hook_name') - 0.3, A('hook_name') + 0.3)) * aL;
    txt('木下藤吉郎', W / 2, 330, { size: 110, w: 900, color: '#fff3dc', a: Math.max(a3, ease(seg(t, A('hook') + 5.0, A('hook') + 5.6)) * aL), stroke: 8, ls: 12 });
    txt('后来的 丰臣秀吉', W / 2, 470, { size: 58, w: 800, color: C.grHi, a: a3, stroke: 6, ls: 8 });
    ctx.restore();
    tag('情景演绎 · 示意', aL, 1780);
  }
  // B. map B: two days earlier — Tezutsuyama & Kanegasaki fall (twodays → tezutsu)
  const aB = blk(t, 'twodays', 'tezutsu');
  if (aB > 0) {
    mapCam(t, [[A('twodays') - 0.3, CAMS.bayWide], [Z('tezutsu'), CAMS.castle]]);
    dimAll(1 - aB);
    mapOn = aB;
    label(...PL.kane, '金崎城', { a: aB, color: '#fff3dc', dx: -110, dy: -10 });
    label(...PL.tezu, '手筒山', { a: aB, color: '#fff3dc', dx: 110, dy: 20 });
    areaLabel(136.06, 35.70, '敦贺湾', { a: aB * 0.85, size: 40, color: 'rgba(200,225,240,0.85)' });
    const p1 = seg(t, A('tezutsu') - 0.2, A('tezutsu') + 1.6), p2 = seg(t, A('tezutsu') + 2.0, A('tezutsu') + 3.6);
    arrow([[136.04, 35.60], [136.07, 35.625], [136.087, 35.650]], eout(p1), { w: 44, a: aB });
    arrow([[136.05, 35.62], [136.065, 35.645], [136.077, 35.662]], eout(p2), { w: 40, a: aB });
    stamp('4月25日 攻下', 760, 1150, aB * ease(seg(t, A('tezutsu') + 1.4, A('tezutsu') + 1.8)), -0.08, '#ff6a4a', 50);
    stamp('4月26日 开城', 330, 650, aB * ease(seg(t, A('tezutsu') + 3.4, A('tezutsu') + 3.8)), 0.06, '#ff6a4a', 50);
    txt('两天前', W / 2, 270, { size: 72, w: 900, color: '#fff3dc', a: aB * (1 - ease(seg(t, A('tezutsu'), A('tezutsu') + 0.5))), stroke: 6, ls: 10 });
    txt('越前门户 · 已经推开', W / 2, 270, { size: 58, w: 900, color: C.grHi, a: aB * ease(seg(t, A('tezutsu') + 4.2, A('tezutsu') + 4.8)), stroke: 6, ls: 6 });
  }
  // C. camp night + riders + letters (report1, pincer_hint quick map, disbelief, reports, turn)
  const aC = blk(t, 'report1', 'turn');
  if (aC > 0) {
    camp(t, aC);
    // riders gallop in from left at report1 and repeatedly during reports
    const ridesAt = [A('report1') - 0.2, A('reports') - 0.1, A('reports') + 1.1, A('reports') + 2.2];
    ridesAt.forEach((r0, k) => { const p = seg(t, r0, r0 + 1.6); if (p > 0 && p < 1) rider(lerp(-200, W + 250, p), 1560 + k * 40, 1.6 - k * 0.15, t * 14 + k, { a: aC, flag: k % 2 ? '#8a8f99' : '#b8261a' }); });
    const aR = aC * ease(seg(t, A('report1') + 0.6, A('report1') + 1.0));
    stamp('急报', W / 2, 430, aR * (1 - ease(seg(t, A('pincer_hint') - 0.2, A('pincer_hint')))), -0.06, '#ff4a3a', 96);
    txt('浅井 反了', W / 2, 620, { size: 110, w: 900, color: '#fff3dc', a: aR * (1 - ease(seg(t, A('pincer_hint') - 0.2, A('pincer_hint')))), stroke: 8, ls: 16 });
    // letters during disbelief/reports
    const aD = aC * ease(seg(t, A('disbelief') - 0.2, A('disbelief') + 0.4));
    for (let k = 0; k < 4; k++) { const ak = aC * ease(seg(t, A('reports') + k * 0.9, A('reports') + k * 0.9 + 0.35)) * (1 - ease(seg(t, A('turn') + 0.6, A('turn') + 1.0))); letter(330 + k * 140, 520 + (k % 2) * 60, 0.62, ak, [['江北浅井', '手の反覆'], ['浅井備前', '別心之由'], ['事実之', '注進'], ['急ぎ', '御帰陣']][k], { rot: (k - 1.5) * 0.08 }); }
    const cnt = Math.min(4, Math.floor(seg(t, A('reports'), A('reports') + 3.6) * 4) + 1);
    if (t > A('reports') && t < A('turn')) txt(`第 ${cnt} 封`, W / 2, 1020, { size: 50, w: 800, color: C.grHi, a: aC, stroke: 5 });
    const aT = aC * ease(seg(t, A('turn') + 0.2, A('turn') + 0.6));
    if (aT > 0) { dimAll(aT * 0.55); const [sx, sy] = shake(t, A('turn') + 0.25, 16, 0.5); txt('不及是非', W / 2 + sx, 560 + sy, { size: 150, w: 900, color: '#fff1d6', a: aT, stroke: 10, ls: 18 }); txt('是非に及ばず · 没什么好说的了', W / 2, 720, { size: 40, w: 600, color: C.gold, a: aT, fam: JP }); txt('全军掉头', W / 2, 840, { size: 64, w: 900, color: C.gr, a: aC * ease(seg(t, A('turn') + 2.2, A('turn') + 2.6)), stroke: 6, ls: 10 }); }
    tag('情景演绎 · 书信为示意', aC);
  }
  // C2. quick map flash for pincer_hint
  const aP = blk(t, 'pincer_hint', 'pincer_hint', 0.3, 0.3);
  if (aP > 0) {
    ctx.save(); ctx.globalAlpha = aP; mapCam(t, [[A('pincer_hint'), CAMS.wideHi], [NX('pincer_hint'), [136.02, 35.50, 1080]]]); ctx.restore(); mapOn = Math.max(mapOn, aP);
    baseLabels(aP);
    routeLine(ROUTE_OUT, 1, C.gr, aP * 0.8, 6);
    armyBlob(...PL.tsuruga, C.gr, aP, t, 40, 0.03);
    const pr = seg(t, A('pincer_hint') + 1.8, A('pincer_hint') + 3.2); regionGlow(...PL.odani, 0.22, 'rgba(125,151,189,0.9)', aP * (0.4 + 0.4 * Math.sin(t * 6)) * ease(pr));
    nameCard(W / 2, 420, '浅井长政', '信长的妹夫 · 盟友', C.az, aP * ease(seg(t, A('pincer_hint') + 0.2, A('pincer_hint') + 0.6)), { w: 420 });
    txt('卡在回家的路上', W / 2, 1290, { size: 56, w: 900, color: C.azHi, a: aP * ease(pr), stroke: 6 });
  }
  // D. leftq: lone castle, red dot stays (on map B, night)
  const aQ = blk(t, 'leftq', 'leftq');
  if (aQ > 0) {
    mapCam(t, [[A('leftq') - 0.3, [136.075, 35.69, 6200]], [NX('leftq'), [136.08, 35.682, 7600]]]); grade('night', 0.9); dimAll(1 - aQ); mapOn = Math.max(mapOn, aQ);
    routeLine([PL.kane, [136.04, 35.635], [136.0, 35.62], [135.96, 35.60]], seg(t, A('leftq'), Z('leftq')), C.gr, aQ * 0.7, 7);
    const [x, y] = P(...PL.kane); glowDot(x, y, 70 + 10 * Math.sin(t * 5), 'rgba(255,60,40,0.9)', aQ); dot(...PL.kane, { r: 12, color: C.gr, a: aQ, ring: (t * 0.8) % 1 });
    txt('金崎城：木下藤吉郎', x, y + 110, { size: 44, w: 900, color: '#fff3dc', a: aQ * ease(seg(t, Z('leftq') - 2, Z('leftq') - 1.5)), stroke: 6 });
  }
  // E. front_back diagram
  const aF = blk(t, 'front_back', 'front_back');
  if (aF > 0) {
    paperBg(aF);
    const half = A('front_back') + (Z('front_back') - A('front_back')) * 0.48; const pr = ease(seg(t, half - 0.4, half + 0.4));
    txt(pr < 0.5 ? '进攻' : '撤退', W / 2, 330, { size: 90, w: 900, color: pr < 0.5 ? C.grHi : C.peHi, a: aF * Math.abs(1 - 2 * pr), stroke: 6, ls: 20 });
    for (let i = 0; i < 9; i++) { const y = 560 + i * 95; const dir = pr < 0.5 ? -1 : 1; const hiIdx = pr < 0.5 ? 0 : 8; const isHi = i === hiIdx; unitBox(W / 2 + Math.sin(t * 2 + i) * 4, y + Math.sin(t * 3 + i) * 3 * dir, 240, 62, isHi ? '#ff3b2a' : '#5a2a22', aF, { glow: isHi ? 40 : 4 }); }
    arrow2(W / 2, 520, W / 2, 420, aF * (1 - pr), C.gr, 16); arrow2(W / 2, 1360, W / 2, 1470, aF * pr, C.gr, 16);
    txt('敌', W / 2, pr < 0.5 ? 470 : 1450, { size: 1, a: 0 });
    txt('敌人 ▲', 230, 480, { size: 40, w: 800, color: C.peHi, a: aF * (1 - pr) }); txt('敌人 ▼', 230, 1440, { size: 40, w: 800, color: C.peHi, a: aF * pr });
    txt('最危险：最前面', 790, 565, { size: 40, w: 800, color: '#fff3dc', a: aF * (1 - pr) }); txt('最危险：最后面', 790, 1320, { size: 40, w: 800, color: '#fff3dc', a: aF * pr });
  }
  // F. three questions
  const aQ3 = blk(t, 'q3', 'q3b');
  if (aQ3 > 0) {
    landscape(t, { mood: 'night', z: 1.3, torches: 0.6, fireA: 0.5 }); dimAll(0.55);
    const qs = ['撤退，为什么比进攻更难打？', '殿军靠什么才不被吃掉？', '对一个出身低微的人意味着什么？'];
    const ts = [A('q3') + 1.6, A('q3') + 5.0, A('q3b')];
    qs.forEach((q, i) => { const ai = aQ3 * ease(seg(t, ts[i] - 0.2, ts[i] + 0.4)); txt(`${'一二三'[i]}`, 150, 520 + i * 200, { size: 80, w: 900, color: C.gr, a: ai }); txt(q, 590, 520 + i * 200, { size: 46, w: 800, color: '#fff3dc', a: ai, stroke: 5 }); });
  }
  return mapOn;
};

/* ---------- s1 background ---------- */
SCN.s1 = function (t) {
  const s = SC.s1; let mapOn = 0;
  const aM = blk(t, 'mapA', 'depart') ; const aM2 = blk(t, 'turn_ne', 'turn_ne');
  // map run 1: mapA → summon → tokichiro(overlay) → depart → turn_ne
  const aMap = Math.max(fade(t, s.t0, NX('turn_ne') + 0.05, 0.5, 0.4), 0);
  if (aMap > 0) {
    mapCam(t, [[s.t0, [136.05, 35.55, 820]], [A('geo') + 2, CAMS.wide], [A('depart'), CAMS.wide], [Z('turn_ne'), [136.0, 35.42, 1250]]]); mapOn = aMap; dimAll(1 - aMap);
    baseLabels(aMap * ease(seg(t, A('geo') - 0.2, A('geo') + 0.8)));
    // summon: dashed lines from Kyoto to provinces; Echizen no
    const aS = aMap * blk(t, 'summon', 'summon');
    if (aS > 0) { const [kx, ky] = P(...PL.kyoto); glowDot(kx, ky, 120, 'rgba(255,210,140,0.9)', aS); for (const [lo, la, ok] of [[135.2, 35.3, 1], [136.7, 35.0, 1], [135.5, 34.85, 1], [136.296, 35.996, 0]]) { const [x, y] = P(lo, la); const p = ease(seg(t, A('summon') + 0.5, A('summon') + 2.5)); ctx.save(); ctx.globalAlpha = aS; ctx.setLineDash([10, 10]); ctx.strokeStyle = C.gold; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(kx, ky); ctx.lineTo(lerp(kx, x, p), lerp(ky, y, p)); ctx.stroke(); ctx.restore(); if (!ok) crossMark(x, y + 70, 30, aS * ease(seg(t, A('summon') + 5.5, A('summon') + 6))); }
      txt('将军之名 · 召各国大名进京', W / 2, 300, { size: 48, w: 800, color: C.gold, a: aS, stroke: 5 }); txt('朝仓义景：迟迟不来', W / 2, 1290, { size: 52, w: 900, color: C.peHi, a: aS * ease(seg(t, A('summon') + 5.5, A('summon') + 6)), stroke: 6 }); }
    const aDp = aMap * fade(t, A('depart') - 0.2, NX('turn_ne'), 0.4, 0.3);
    if (aDp > 0) {
      const p = seg(t, A('depart') + 0.3, Z('turn_ne') - 0.5); const split = 0.62;
      arrow(ROUTE_OUT.slice(0, 5), eio(clamp(p / split)), { w: 40, a: aDp });
      if (p > split) arrow(ROUTE_OUT.slice(4), eio(clamp((p - split) / (1 - split))), { w: 46, a: aDp });
      txt('4月20日 出京', W / 2, 300, { size: 54, w: 900, color: '#fff3dc', a: aDp, stroke: 6 }); txt('（西历1570年5月24日）', W / 2, 370, { size: 32, w: 500, color: C.bone, a: aDp });
      const aW = aDp * ease(seg(t, A('depart') + 2.5, A('depart') + 3)); txt('名义：讨伐若狭武藤氏', 300, 1290, { size: 40, w: 800, color: C.bone, a: aW * (1 - ease(seg(t, A('turn_ne'), A('turn_ne') + 0.4))), stroke: 5 });
      const aE = aDp * ease(seg(t, A('turn_ne') + 3.0, A('turn_ne') + 3.5)); txt('真正目标：朝仓', W / 2, 1290, { size: 60, w: 900, color: C.peHi, a: aE, stroke: 6 }); regionGlow(...PL.ichijo, 0.15, 'rgba(61,139,255,0.9)', aE * 0.6);
    }
  }
  // tokichiro card overlay
  const aK = blk(t, 'tokichiro', 'tokichiro');
  if (aK > 0) {
    dimAll(aK * 0.7);
    panel(110, 560, 860, 760, aK, 'rgba(10,9,8,0.9)');
    soldier(300, 1180, 3.2, { a: aK, col: '#1a1412', spear: 0 });
    glowDot(300, 950, 260, 'rgba(255,90,50,0.22)', aK);
    txt('木下藤吉郎', 640, 700, { size: 64, w: 900, color: '#fff3dc', a: aK });
    ['三十出头', '尾张平民出身', '没有显赫家世', '经手京都政务'].forEach((s_, i) => txt(s_, 640, 820 + i * 92, { size: 42, w: 700, color: i === 3 ? C.gold : C.bone, a: aK * ease(seg(t, A('tokichiro') + 0.6 + i * 1.6, A('tokichiro') + 1 + i * 1.6)) }));
    txt('织田家的「能干中层」', 540, 1240, { size: 40, w: 800, color: C.grHi, a: aK * ease(seg(t, Z('tokichiro') - 2.5, Z('tokichiro') - 2)) });
    tag('人物剪影为示意', aK, 1360);
  }
  // relations diagram: azai → choose2
  const aR = blk(t, 'azai', 'choose2');
  if (aR > 0) {
    paperBg(aR);
    const ax = W / 2, ay = 900, ox = 260, oy = 1250, kx = 820, ky = 1250;
    nameCard(ax, ay, '浅井长政', '北近江', C.az, aR * rise(t, 'azai'), { w: 380 });
    const aO = aR * rise(t, 'marriage'), aA = aR * rise(t, 'oldties');
    nameCard(ox, oy, '织田信长', '', C.gr, aO, { w: 360, h: 110 }); nameCard(kx, ky, '朝仓义景', '', C.pe, aA, { w: 360, h: 110 });
    const snap = ease(seg(t, A('choose2') - 0.1, A('choose2') + 0.4));
    // Oda link (marriage)
    if (aO > 0) { ctx.save(); ctx.globalAlpha = aO * (1 - snap); ctx.strokeStyle = C.gr; ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo(ax - 60, ay + 72); ctx.lineTo(ox + 40, oy - 58); ctx.stroke(); ctx.restore(); txt('姻亲：妹妹阿市', (ax + ox) / 2 - 70, (ay + oy) / 2, { size: 38, w: 800, color: C.grHi, a: aO * (1 - snap), stroke: 4 }); }
    if (snap > 0 && snap < 1) for (let k = 0; k < 2; k++) sparks((ax + ox) / 2, (ay + oy) / 2, t, A('choose2'), aR, 5 + k, 2);
    if (aA > 0) { ctx.save(); ctx.globalAlpha = aA; ctx.strokeStyle = C.pe; ctx.lineWidth = 8 + 10 * snap; ctx.shadowColor = C.pe; ctx.shadowBlur = 20 * snap; ctx.beginPath(); ctx.moveTo(ax + 60, ay + 72); ctx.lineTo(kx - 40, ky - 58); ctx.stroke(); ctx.restore(); txt('往来更久', (ax + kx) / 2 + 70, (ay + ky) / 2, { size: 38, w: 800, color: C.peHi, a: aA, stroke: 4 }); }
    const aDu = aR * blk(t, 'dual', 'choose'); txt('同时向几家称臣，两边都不得罪', W / 2, 520, { size: 44, w: 800, color: C.bone, a: aDu * (1 - ease(seg(t, A('choose'), A('choose') + 0.4))), stroke: 4 }); txt('学者长谷川裕子的看法', W / 2, 590, { size: 30, w: 500, color: C.goldDim, a: aDu * (1 - ease(seg(t, A('choose'), A('choose') + 0.4))) });
    const aCh = aR * ease(seg(t, A('choose') + 2.0, A('choose') + 2.5)); txt('信长打朝仓 → 只能选一边', W / 2, 560, { size: 50, w: 900, color: '#fff3dc', a: aCh * (1 - snap), stroke: 5 });
    txt('他选了朝仓', W / 2, 520, { size: 100, w: 900, color: C.peHi, a: aR * snap, stroke: 8, ls: 12 });
  }
  // pincer map
  const aPn = blk(t, 'pincer', 'pincer2');
  if (aPn > 0) {
    mapCam(t, [[A('pincer') - 0.3, CAMS.wide], [Z('pincer2'), [136.08, 35.58, 1500]]]); dimAll(1 - aPn); mapOn = Math.max(mapOn, aPn);
    baseLabels(aPn);
    routeLine(ROUTE_OUT, 1, C.gr, aPn * 0.6, 5);
    armyBlob(...PL.tsuruga, C.gr, aPn, t, 60, 0.035);
    const p1 = seg(t, A('pincer') + 2.0, A('pincer') + 4.5), p2 = seg(t, A('pincer') + 4.5, Z('pincer'));
    arrow(ASA_IN, eio(p1), { color: C.pe, hi: C.peHi, w: 54, a: aPn });
    arrow(AZ_IN, eio(p2), { color: C.az, hi: C.azHi, w: 50, a: aPn });
    arrow(AZ_CUT, eio(seg(t, A('pincer2') - 0.5, A('pincer2') + 1.5)), { color: C.az, hi: C.azHi, w: 42, a: aPn * 0.9 });
    const [x, y] = P(...PL.tsuruga); const rr = aPn * ease(seg(t, A('pincer2'), A('pincer2') + 0.6)); if (rr > 0) { ctx.save(); ctx.globalAlpha = rr; ctx.strokeStyle = '#ff3b2a'; ctx.lineWidth = 6; ctx.shadowColor = '#ff3b2a'; ctx.shadowBlur = 20; const R = lerp(320, 110, ease(seg(t, A('pincer2'), Z('pincer2')))); ctx.setLineDash([24, 14]); ctx.lineDashOffset = -t * 60; ctx.beginPath(); ctx.arc(x, y, R, 0, Math.PI * 2); ctx.stroke(); ctx.restore(); }
    txt('前有朝仓 · 后有浅井', W / 2, 300, { size: 62, w: 900, color: '#fff3dc', a: aPn * ease(seg(t, A('pincer') + 4, A('pincer') + 4.5)), stroke: 6 });
    txt('钳形合拢', W / 2, 1280, { size: 80, w: 900, color: C.azHi, a: aPn * ease(seg(t, A('pincer2'), A('pincer2') + 0.5)), stroke: 7, ls: 16 });
  }
  return mapOn;
};

/* ---------- s2 decision ---------- */
function gauge(t, x, y, w, h, fill, thr, a, o = {}) {
  if (a <= 0.01) return; const { label: lb = '证据' } = o;
  ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = 'rgba(255,255,255,0.08)'; ctx.fillRect(x, y, w, h); ctx.strokeStyle = 'rgba(226,194,122,0.7)'; ctx.lineWidth = 2; ctx.strokeRect(x, y, w, h);
  const fh = h * clamp(fill); const g = ctx.createLinearGradient(0, y + h, 0, y); g.addColorStop(0, '#7a1a10'); g.addColorStop(1, fill >= thr ? '#ff5a36' : '#c23a22'); ctx.fillStyle = g; ctx.fillRect(x + 4, y + h - fh, w - 8, fh);
  const ty_ = y + h * (1 - thr); ctx.strokeStyle = '#fff3dc'; ctx.lineWidth = 4; ctx.setLineDash([14, 10]); ctx.beginPath(); ctx.moveTo(x - 40, ty_); ctx.lineTo(x + w + 40, ty_); ctx.stroke(); ctx.restore();
  txt('相信的门槛', x + w + 60, ty_, { size: 34, w: 800, color: '#fff3dc', a, align: 'left' }); txt(lb, x + w / 2, y + h + 50, { size: 34, w: 700, color: C.bone, a });
}
function scale(t, cx, cy, tilt, a, L, R) { if (a <= 0.01) return; ctx.save(); ctx.globalAlpha = a; ctx.translate(cx, cy); ctx.strokeStyle = C.gold; ctx.fillStyle = C.gold; ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 420); ctx.stroke(); ctx.fillRect(-90, 410, 180, 16); ctx.rotate(tilt); ctx.beginPath(); ctx.moveTo(-340, 0); ctx.lineTo(340, 0); ctx.stroke(); ctx.restore();
  const pan = (sx, lines, col) => { const px = cx + Math.cos(tilt) * sx, py = cy + Math.sin(tilt) * sx; ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = C.goldDim; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(px - 110, py + 150); ctx.moveTo(px, py); ctx.lineTo(px + 110, py + 150); ctx.stroke(); ctx.fillStyle = 'rgba(20,16,12,0.9)'; ctx.fillRect(px - 170, py + 150, 340, 200); ctx.strokeStyle = col; ctx.strokeRect(px - 170, py + 150, 340, 200); ctx.restore(); lines.forEach((s, i) => txt(s, px, py + 195 + i * 54, { size: 34, w: 800, color: i ? C.bone : col, a })); };
  pan(-340, L, C.grHi); pan(340, R, C.peHi); }
SCN.s2 = function (t) {
  const s = SC.s2; let mapOn = 0;
  // camp + the two sentences
  const aC = fade(t, s.t0, NX('thr_q') + 0.05, 0.5, 0.4);
  if (aC > 0) {
    camp(t, aC); dimAll(aC * 0.6);
    const items = [['可為虚説と思食候処', '认定是谣言', C.peHi], ['従方々事実之注進候', '各方面报来：是真的', C.gold], ['不及是非之由にて', '撤', C.gr]];
    const t0 = A('two_sent') + 0.5;
    items.forEach((it, i) => { const ai = aC * ease(seg(t, t0 + i * 2.6, t0 + i * 2.6 + 0.5)); txt(it[0], W / 2, 560 + i * 230, { size: 58, w: 700, color: it[2], a: ai, fam: JP, ls: 4 }); txt(it[1], W / 2, 640 + i * 230, { size: 38, w: 700, color: '#fff3dc', a: ai }); if (i < 2) txt('↓', W / 2, 715 + i * 230, { size: 40, w: 700, color: C.goldDim, a: ai }); });
    txt('《信长公记》卷三', W / 2, 400, { size: 36, w: 600, color: C.goldDim, a: aC * ease(seg(t, A('two_sent'), A('two_sent') + 0.5)) });
    txt('坏消息，要多少证据才信？', W / 2, 1330, { size: 58, w: 900, color: '#fff3dc', a: aC * ease(seg(t, A('thr_q') + 0.6, A('thr_q') + 1.1)), stroke: 6 });
  }
  // threshold gauge & scale (threshold → decide)
  const aG = fade(t, A('threshold') - 0.3, NX('decide') + 0.05, 0.4, 0.4);
  if (aG > 0) {
    paperBg(aG);
    const thr = lerp(0.45, 0.78, ease(seg(t, A('threshold') + 0.5, A('threshold') + 2.5)));
    const fill = t < A('multiply') ? 0.3 + 0.03 * Math.sin(t * 2) : lerp(0.3, 0.95, ease(seg(t, A('multiply') + 1.0, A('multiply') + 7.0)));
    const aGa = aG * (1 - blk(t, 'cost1', 'asym'));
    gauge(t, 200, 560, 160, 800, fill, thr, aGa);
    txt('不愿相信 → 门槛抬高', 700, 520, { size: 40, w: 800, color: C.gold, a: aGa * ease(seg(t, A('threshold') + 0.8, A('threshold') + 1.3)) });
    const aRs = aGa * blk(t, 'reasons', 'reasons'); ['浅井是亲戚', '刚把北近江交给他', '他没有理由反'].forEach((r, i) => txt(r, 700, 900 + i * 90, { size: 42, w: 700, color: '#fff3dc', a: aRs * ease(seg(t, A('reasons') + i * 1.2, A('reasons') + i * 1.2 + 0.4)) }));
    // scale block
    const aSc = aG * blk(t, 'cost1', 'asym');
    if (aSc > 0) {
      const tilt = t < A('cost2') ? -0.18 * ease(seg(t, A('cost1'), A('cost1') + 1)) : lerp(-0.18, 0.32, ease(seg(t, A('cost2') + 0.5, A('cost2') + 2.5)));
      scale(t, W / 2, 620, tilt, aSc, ['信了谣言就撤', '顺仗白打', '被天下人笑话'], ['不信，留下', '退路被断', '三万人困死']);
      const aSk = aSc * blk(t, 'sunk', 'sunk2'); if (aSk > 0) { panel(120, 1030, 840, 280, aSk, 'rgba(10,8,6,0.95)'); txt('沉没成本', W / 2, 1095, { size: 60, w: 900, color: C.gold, a: aSk }); txt('打下的城 · 花掉的粮 · 死掉的人', W / 2, 1180, { size: 40, w: 700, color: '#fff3dc', a: aSk }); txt('都在拉着你留下', W / 2, 1250, { size: 40, w: 700, color: C.bone, a: aSk * ease(seg(t, A('sunk2') - 0.5, A('sunk2'))) }); }
      txt('两种错误 · 代价不对称', W / 2, 1300, { size: 56, w: 900, color: '#fff3dc', a: aSc * blk(t, 'asym', 'asym'), stroke: 5 });
    }
    // multiply: three letters with x
    const aMu = aG * blk(t, 'multiply', 'decide');
    if (aMu > 0) { const xs = [520, 720, 920]; xs.forEach((x, i) => { const ai = aMu * ease(seg(t, A('multiply') + i * 1.0, A('multiply') + i * 1.0 + 0.4)); letter(x - 40, 760, 0.32, ai, [['注', '進'], ['注', '進'], ['注', '進']][i], { rot: (i - 1) * 0.1 }); if (i) txt('×', x - 140, 760, { size: 70, w: 900, color: C.gold, a: ai }); });
      txt('互不相干的来源：可信度相乘', 650, 1040, { size: 38, w: 800, color: '#fff3dc', a: aMu * ease(seg(t, A('multiply') + 4, A('multiply') + 4.6)) }); }
    const aDe = aG * ease(seg(t, A('decide') - 0.2, A('decide') + 0.3)); if (aDe > 0) { const [sx, sy] = shake(t, A('decide'), 14, 0.5); stamp('撤', 650 + sx, 1250 + sy, aDe, -0.12, '#ff3b2a', 150); }
  }
  const aL = blk(t, 'lesson2', 'next_prob');
  if (aL > 0) {
    landscape(t, { mood: 'night', z: 1.15, torches: 0.4 }); dimAll(0.5);
    bigText(['坏消息不一定早信', '证据一够，转身最快'], 620, aL * (1 - ease(seg(t, A('next_prob') - 0.2, A('next_prob') + 0.2))), { size: 64 });
    txt('真正的难题，才刚开始', W / 2, 700, { size: 72, w: 900, color: C.grHi, a: aL * ease(seg(t, A('next_prob'), A('next_prob') + 0.5)), stroke: 7 });
  }
  return mapOn;
};

/* ---------- s3 rearguard (climax) ---------- */
function columnScene(t, a, mode, p) { // side view: troops; mode 'attack' faces right, 'retreat' backs to enemy
  if (a <= 0.01) return;
  bgGrad('#0a0c12', '#18110c', a);
  ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = '#0c0907'; ctx.fillRect(0, 1250, W, H - 1250); ctx.restore();
  const ret = mode === 'retreat';
  glowDot(W / 2, 1100, 700, 'rgba(255,110,50,0.25)', a);
  for (let i = 0; i < 12; i++) { const x = 90 + (i % 6) * 100 + (i > 5 ? 50 : 0), y = 1230 + (i > 5 ? 80 : 0); ctx.save(); if (ret) { ctx.translate(x, 0); ctx.scale(-1, 1); ctx.translate(-x, 0); } soldier(x + (ret ? -1 : 1) * Math.sin(t * 6 + i) * 3, y, 2.0, { a, col: '#8a2416', ph: t * 10 + i, run: ret ? 1 : 0.2 }); ctx.restore(); }
  for (let i = 0; i < 5; i++) { soldier(860 + i * 44, 1230 + (i % 2) * 50, 2.0, { a, col: '#2a4a8a', ph: t * 10 + i, run: 0.6 }); }
  txt('敌', 940, 860, { size: 60, w: 900, color: C.peHi, a });
  txt(ret ? '背对敌人' : '面朝敌人', W / 2, 640, { size: 72, w: 900, color: ret ? C.peHi : C.grHi, a, stroke: 6 });
}
function cascadeGrid(t, a, t0) {
  if (a <= 0.01) return; const n = 12, m = 9, gx = 80, gy = 560, d = 80;
  for (let i = 0; i < n; i++) for (let j = 0; j < m; j++) {
    const dist = Math.hypot(i - 2, j - 4); const flip = ease(seg(t, t0 + dist * 0.45, t0 + dist * 0.45 + 0.35));
    const x = gx + j * 0 + i * d * 0.82 + 30, y = gy + j * d + Math.sin(t * 3 + i + j) * 2;
    const col = mixc('#8a2a20', '#3d8bff', 0); ctx.save(); ctx.globalAlpha = a; ctx.translate(x + flip * 30 * ((i * 7 + j) % 3) / 2, y); ctx.rotate(Math.PI * flip);
    ctx.fillStyle = flip > 0.5 ? '#ff6a4a' : '#8a2a20'; ctx.beginPath(); ctx.moveTo(0, -18); ctx.lineTo(14, 14); ctx.lineTo(-14, 14); ctx.closePath(); ctx.fill(); ctx.restore();
  }
}
function battleNight(t, a, o = {}) { // side view: rearguard gun lines (left) vs pursuers (right), rain, smoke, fire
  if (a <= 0.01) return; const { t0 = 0, volleys = [], counter = -1 } = o;
  ctx.save(); ctx.globalAlpha = a;
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#04060c'); g.addColorStop(0.45, '#1c1420'); g.addColorStop(0.62, '#4a2416'); g.addColorStop(1, '#0a0605'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const fg = ctx.createRadialGradient(W * 0.75, 1080, 0, W * 0.75, 1080, 700); fg.addColorStop(0, 'rgba(255,120,40,0.35)'); fg.addColorStop(1, 'rgba(255,120,40,0)'); ctx.fillStyle = fg; ctx.fillRect(0, 0, W, H);
  ctx.translate(0, -260);
  ctx.fillStyle = '#100c14'; ctx.beginPath(); ctx.moveTo(0, 1000); for (let x = 0; x <= W; x += 20) ctx.lineTo(x, 900 - 120 * Math.sin(x / 260 + 1) - 50 * Math.sin(x / 90)); ctx.lineTo(W, H + 300); ctx.lineTo(0, H + 300); ctx.fill();
  ctx.fillStyle = '#0a070a'; ctx.beginPath(); ctx.moveTo(0, 1180); for (let x = 0; x <= W; x += 20) ctx.lineTo(x, 1160 - 25 * Math.sin(x / 200) + (x > 640 ? -(x - 640) * 0.12 : 0)); ctx.lineTo(W, H + 300); ctx.lineTo(0, H + 300); ctx.fill();
  ctx.restore(); ctx.save(); ctx.translate(0, -260);
  // pursuers: advance, recoil after each volley, some fall
  let push = 0; for (const v of volleys) push += 120 * ease(seg(t, v + 0.05, v + 0.45)) * (1 - 0.7 * ease(seg(t, v + 0.8, v + 2.2)));
  if (counter > 0) push += 240 * ease(seg(t, counter + 0.3, counter + 0.9));
  const adv = Math.min(320, 60 * (t - t0));
  for (let i = 0; i < 30; i++) {
    const row = Math.floor(i / 10), x = 640 + (i % 10) * 52 + row * 30 - adv + push + hash(i) * 24, y = 1190 + row * 46 - (x - 640) * 0.12;
    let fall = 0; for (const v of volleys) if (hash(i * 7 + v) < 0.18 && t > v + 0.1) fall = Math.max(fall, ease(seg(t, v + 0.1, v + 0.5)));
    ctx.save(); ctx.translate(x, y); ctx.rotate(fall * 1.3); ctx.translate(-x, -y); soldier(x, y, 1.35 - row * 0.12, { a: a * (1 - fall * 0.5), col: '#0e1a30', ph: t * 9 + i, run: 0.9 }); ctx.restore();
    if (i % 3 === 0 && fall < 0.5) glowDot(x + 12, y - 150, 34, 'rgba(120,170,255,0.75)', a);
  }
  // two gun lines, volleys alternate rows (front row k even, back row k odd)
  for (let r = 1; r >= 0; r--) for (let i = 0; i < 6; i++) {
    const x = 70 + i * 82 + r * 40, y = 1330 + r * 120; let f = 0; volleys.forEach((v, k) => { if (k % 2 !== r) return; const d = t - (v + i * 0.05); if (d >= 0 && d < 0.16) f = Math.max(f, 1 - d / 0.16); });
    gunner(x, y, 1.75 + r * 0.25, f, { a, col: r ? '#050404' : '#0b0706' });
    volleys.forEach((v, k) => { if (k % 2 === r) smokePuff(x + 160, y - 140, t - (v + i * 0.05), 1.4, a); });
  }
  if (counter > 0) { const p = seg(t, counter - 0.2, counter + 1.6); const k = Math.sin(Math.PI * p); if (p > 0 && p < 1) for (let i = 0; i < 7; i++) soldier(360 + k * 300 + i * 34, 1250 + (i % 2) * 30, 1.6, { a, col: '#4a100a', ph: t * 14 + i, run: 1 }); }
  for (const v of volleys) { const fl = 1 - seg(t, v, v + 0.22); if (t >= v && fl > 0) { ctx.save(); ctx.globalAlpha = a * fl * 0.3; ctx.fillStyle = '#ffd8a0'; ctx.fillRect(0, 0, W, H); ctx.restore(); } }
  smokeField(t, a * 0.6, 3, 12, 950, 1300, '170,160,155');
  ctx.restore();
  embers(t, a * 0.8, 5, 40);
  rain(t, a * 0.5, 280);
}
function leapfrog(t, a, t0, t1) {
  if (a <= 0.01) return; paperBg(a);
  // a winding mountain road (screen space) from top (north, enemy) to bottom (south, home)
  const road = [[540, 380], [640, 530], [460, 690], [620, 850], [480, 1010], [600, 1170], [540, 1320]];
  const rp = pathPx2(road);
  ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = 'rgba(200,180,140,0.35)'; ctx.lineWidth = 60; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.beginPath(); rp.p.forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])); ctx.stroke(); ctx.restore();
  // passes (holding points)
  const passes = [0.1, 0.26, 0.42, 0.58, 0.74, 0.9];
  passes.forEach((s, i) => { const [x, y] = samplePx(rp, s * rp.len); txt('▲', x + 90, y, { size: 34, w: 900, color: C.goldDim, a }); });
  const T = clamp((t - t0) / Math.max(1, t1 - t0)) * 4; const step = Math.min(3, Math.floor(T)), fr = ease(T - step);
  const pa = step % 2 === 0 ? lerp(passes[step], passes[step + 2], fr) : passes[step + 1];
  const pb = step % 2 === 1 ? lerp(passes[step], passes[step + 2], fr) : passes[step + 1];
  const [xa, ya] = samplePx(rp, pa * rp.len), [xb, yb] = samplePx(rp, pb * rp.len);
  const holdA = step % 2 === 1, holdB = step % 2 === 0; const sA = pa, sB = pb;
  unitBox(xa - 60, ya, 120, 56, C.gr, a, { label: holdA ? '守' : '退', glow: holdA ? 34 : 8 });
  unitBox(xb + 60, yb, 120, 56, C.grDim, a, { label: holdB ? '守' : '退', hi: C.grHi, glow: holdB ? 34 : 8 });
  // pursuers
  const sE = clamp(Math.min(sA, sB) - 0.14); const [xe, ye] = samplePx(rp, sE * rp.len);
  for (let i = 0; i < 5; i++) unitBox(xe + (i - 2) * 50, ye - 40 - (i % 2) * 30, 36, 24, C.pe, a, { glow: 10 });
  txt('追兵', xe + 200, ye - 50, { size: 34, w: 800, color: C.peHi, a });
  // guns from holder
  const [hx, hy] = holdA ? [xa - 60, ya] : [xb + 60, yb]; if (Math.sin(t * 6) > 0.85) { arrow2(hx, hy - 30, xe, ye - 10, a * 0.8, '#ffd27a', 4); }
  txt('北 · 敌', 900, 380, { size: 32, w: 700, color: C.peHi, a }); txt('南 · 京都', 880, 1320, { size: 32, w: 700, color: C.grHi, a });
}
function pathPx2(pts) { const p = smooth(pts, 10); const L = [0]; for (let i = 1; i < p.length; i++) L.push(L[i - 1] + Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1])); return { p, L, len: L[L.length - 1] }; }

SCN.s3 = function (t) {
  const s = SC.s3; let mapOn = 0;
  // hard/backs
  const aH = fade(t, s.t0, NX('backs') + 0.05, 0.5, 0.4);
  if (aH > 0) { columnScene(t, aH, t < A('backs') + 3.5 ? 'attack' : 'retreat'); txt('撤退比进攻难', W / 2, 420, { size: 86, w: 900, color: '#fff3dc', a: aH, stroke: 7, ls: 10 }); }
  // du Picq: casualties chart (qualitative)
  const aDp = blk(t, 'dupicq', 'chase');
  if (aDp > 0) {
    paperBg(aDp);
    txt('杜皮克《战斗研究》', W / 2, 360, { size: 40, w: 700, color: C.gold, a: aDp }); txt('Ardant du Picq · 19世纪', W / 2, 420, { size: 30, w: 500, color: C.goldDim, a: aDp });
    const b1 = ease(seg(t, A('dupicq') + 3, A('dupicq') + 4)), b2 = ease(seg(t, A('dupicq') + 5.5, A('dupicq') + 7.5));
    ctx.save(); ctx.globalAlpha = aDp; ctx.fillStyle = '#7a6a5a'; ctx.fillRect(260, 1150 - 160 * b1, 200, 160 * b1); ctx.fillStyle = '#ff3b2a'; ctx.shadowColor = '#ff3b2a'; ctx.shadowBlur = 30; ctx.fillRect(620, 1150 - 520 * b2, 200, 520 * b2); ctx.restore();
    txt('对阵时', 360, 1210, { size: 44, w: 800, color: C.bone, a: aDp * b1 }); txt('转身逃跑后', 720, 1210, { size: 44, w: 800, color: C.grHi, a: aDp * b2 });
    txt('败军伤亡（示意）', W / 2, 1290, { size: 30, w: 500, color: C.goldDim, a: aDp * b2 });
    txt('一转身，就没法还手', W / 2, 540, { size: 58, w: 900, color: '#fff3dc', a: aDp * blk(t, 'dupicq2', 'dupicq2'), stroke: 6 });
    txt('追的越追越勇 · 跑的越跑越怕', W / 2, 540, { size: 50, w: 900, color: '#fff3dc', a: aDp * blk(t, 'chase', 'chase'), stroke: 6 });
  }
  // panic cascade
  const aPa = blk(t, 'panic', 'feishui');
  if (aPa > 0) {
    bgGrad('#07090e', '#120a0a', aPa);
    cascadeGrid(t, aPa * (1 - blk(t, 'feishui', 'feishui')), A('cascade') + 1.0);
    txt('恐慌会传染', W / 2, 330, { size: 86, w: 900, color: '#fff3dc', a: aPa, stroke: 7, ls: 8 });
    txt('信息级联 · Bikhchandani 等 1992', W / 2, 440, { size: 34, w: 600, color: C.gold, a: aPa * rise(t, 'cascade') * (1 - blk(t, 'feishui', 'feishui')) });
    const aF = aPa * blk(t, 'feishui', 'feishui');
    if (aF > 0) { panel(110, 600, 860, 640, aF, 'rgba(10,8,6,0.9)'); txt('淝水之战 · 383年', W / 2, 720, { size: 44, w: 800, color: C.gold, a: aF }); txt('前秦大军「往后让一让」', W / 2, 860, { size: 50, w: 800, color: '#fff3dc', a: aF }); txt('一声「秦军败矣」', W / 2, 980, { size: 66, w: 900, color: C.grHi, a: aF * ease(seg(t, A('feishui') + 3, A('feishui') + 3.5)) }); txt('后退 → 溃逃', W / 2, 1120, { size: 56, w: 900, color: '#fff3dc', a: aF * ease(seg(t, A('feishui') + 5, A('feishui') + 5.5)) }); }
  }
  // rout headline + 殿 + gate + task
  const aRo = blk(t, 'rout', 'task');
  if (aRo > 0) {
    landscape(t, { mood: 'night', z: 1.5, torches: 1, fireA: 0.6, rainA: 0.25 }); dimAll(0.45 * aRo);
    ctx.save(); ctx.globalAlpha = 1 - aRo; ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H); ctx.restore();
    txt('真正的敌人：退却变成溃散', W / 2, 400, { size: 56, w: 900, color: '#fff3dc', a: aRo * blk(t, 'rout', 'rout'), stroke: 6 });
    const aS = aRo * blk(t, 'shingari', 'gate'); if (aS > 0) { const sc = 1 + 0.06 * seg(t, A('shingari'), Z('gate')); ctx.save(); ctx.translate(W / 2, 640); ctx.scale(sc, sc); txt('殿', 0, 0, { size: 380, w: 900, color: '#fff1d6', a: aS, stroke: 12, fam: SONG }); ctx.restore(); txt('しんがり · 走在最后的部队', W / 2, 920, { size: 42, w: 700, color: C.gold, a: aS, fam: JP }); txt('全军最后一道闸门', W / 2, 1040, { size: 54, w: 900, color: C.grHi, a: aS * rise(t, 'gate'), stroke: 6 }); }
    const aT = aRo * blk(t, 'task', 'task'); bigText(['不是打赢', '是换时间'], 560, aT, { size: 110, ls: 14 });
  }
  // buytime timeline
  const aBt = blk(t, 'buytime', 'buytime');
  if (aBt > 0) {
    paperBg(aBt);
    const T0 = A('buytime'), dur = Z('buytime') - T0; const p = seg(t, T0, T0 + dur);
    const main = lerp(300, 1500, p); const steps = 5; let pur = 300 - 260; for (let k = 0; k < steps; k++) { const a0 = k / steps, a1 = (k + 0.6) / steps; pur += 140 * ease(seg(p, a0, a1)); }
    // vertical track: north top -> south bottom (rotate) — draw as horizontal for clarity
    const y = 980; ctx.save(); ctx.globalAlpha = aBt; ctx.strokeStyle = 'rgba(226,194,122,0.5)'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(60, y); ctx.lineTo(W - 60, y); ctx.stroke(); ctx.restore();
    const mx = lerp(260, 1000, p), px = lerp(80, 560, (pur - 40) / 700);
    unitBox(mx, y, 120, 70, C.gr, aBt, { label: '主力' }); unitBox(260 + 0 * p, y + 140, 120, 60, C.grDim, aBt * 0, {});
    for (let i = 0; i < 4; i++) unitBox(px - 40 - i * 34, y - 6 + (i % 2) * 18, 30, 22, C.pe, aBt, { glow: 8 });
    const sx_ = px + 30; unitBox(sx_ + 40, y, 70, 50, '#ff8a4a', aBt, { label: '殿', glow: 26 });
    // gap meter
    ctx.save(); ctx.globalAlpha = aBt; ctx.strokeStyle = C.gold; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(sx_ + 80, y + 90); ctx.lineTo(mx - 60, y + 90); ctx.stroke(); ctx.restore(); txt('距离', (sx_ + mx) / 2, y + 140, { size: 40, w: 800, color: C.gold, a: aBt });
    for (let k = 0; k < steps; k++) { const at = (k + 0.62) / steps; const ak = aBt * Math.max(0, 1 - Math.abs(p - at) * 12); stamp('停 · 列阵', px - 60, y - 170, ak, -0.08, '#7fb0ff', 40); }
    txt('每往前一段：停下、列阵、付出代价', W / 2, 520, { size: 46, w: 900, color: '#fff3dc', a: aBt, stroke: 5 });
  }
  // castle (map B) + guns/counter (battle) + leapfrog + fires + caveat
  const aCa = blk(t, 'castle', 'castle');
  if (aCa > 0) {
    mapCam(t, [[A('castle') - 0.3, CAMS.bayWide], [Z('castle'), CAMS.bay]]); grade('night', 0.85); dimAll(1 - aCa); mapOn = aCa;
    label(...PL.kane, '金崎城', { a: aCa, color: '#fff3dc', dx: -120, dy: -10 }); label(...PL.tezu, '手筒山', { a: aCa, color: '#fff3dc', dx: 120, dy: 20 }); label(...PL.kinome, '木芽峠', { a: aCa, color: C.peHi, dx: 0, dy: -36 });
    const [x, y] = P(...PL.kane); glowDot(x, y, 90, 'rgba(255,60,40,0.8)', aCa);
    arrow([PL.kinome, [136.12, 35.72], [136.10, 35.685]], eio(seg(t, A('castle') + 1, A('castle') + 4)), { color: C.pe, hi: C.peHi, w: 46, a: aCa });
    arrow([PL.tsuruga, [136.03, 35.63], [135.97, 35.60]], eio(seg(t, A('castle') + 2, A('castle') + 6)), { color: C.gr, hi: C.grHi, w: 30, a: aCa * 0.8, dash: true });
    arrow([[136.10, 35.685], [136.07, 35.655], [136.03, 35.62]], 0.55 * eio(seg(t, A('castle') + 6, Z('castle'))), { color: C.pe, hi: C.peHi, w: 30, a: aCa * 0.6, dash: true });
    crossMark(...P(136.06, 35.645), 30, aCa * ease(seg(t, Z('castle') - 1.5, Z('castle') - 1.0)));
    txt('第一件武器：阵地', W / 2, 300, { size: 66, w: 900, color: '#fff3dc', a: aCa, stroke: 6 });
    txt('城在，追兵就不敢放心绕过去', W / 2, 1290, { size: 46, w: 800, color: C.grHi, a: aCa * ease(seg(t, A('castle') + 5, A('castle') + 5.5)), stroke: 5 });
  }
  const aBn = blk(t, 'guns', 'counter');
  if (aBn > 0) {
    const g0 = A('guns'); const vol = []; for (let v = g0 + 1.6; v < NX('counter') - 0.5; v += 1.45) if (!(v > A('counter') + 1.2 && v < A('counter') + 3.6)) vol.push(v);
    let sh = [0, 0]; for (const v of vol) { const q = shake(t, v, 9, 0.3); sh = [sh[0] + q[0], sh[1] + q[1]]; } ctx.save(); ctx.translate(sh[0], sh[1]);
    battleNight(t, aBn, { t0: g0, volleys: vol, counter: A('counter') + 1.6 }); ctx.restore();
    txt(t < A('counter') ? '第二件武器：铁炮' : '第三件：短促反击', W / 2, 330, { size: 70, w: 900, color: '#fff3dc', a: aBn, stroke: 7 });
    txt(t < A('counter') ? '一排齐射 · 打乱前锋 · 再退一段' : '回头咬一口 · 让追兵不敢贴近', W / 2, 430, { size: 42, w: 800, color: C.gold, a: aBn, stroke: 4 });
    tag('情景演绎 · 示意', aBn);
  }
  const aLf = blk(t, 'leapfrog', 'leapfrog');
  if (aLf > 0) { leapfrog(t, aLf, A('leapfrog') + 0.5, Z('leapfrog') + 0.3); txt('交替掩护', W / 2, 250, { size: 76, w: 900, color: '#fff3dc', a: aLf, stroke: 7, ls: 10 }); }
  const aFi = blk(t, 'fires', 'caveat');
  if (aFi > 0) {
    landscape(t, { mood: 'night', z: 1.9, torches: 0.15, fireA: 0.9, rainA: 0.2 }); dimAll(1 - aFi);
    // many campfires around the castle + flags
    const n = Math.floor(6 + 24 * ease(seg(t, A('fires'), A('fires') + 3)));
    for (let i = 0; i < n; i++) { const x = 300 + hash(i * 3) * 620, y = 980 + hash(i * 7) * 220; glowDot(x, y, 26 + 6 * Math.sin(t * 9 + i), 'rgba(255,150,60,0.95)', aFi); }
    for (let i = 0; i < 9; i++) { const x = 330 + i * 60, y = 960 + (i % 3) * 30; ctx.save(); ctx.globalAlpha = aFi * ease(seg(t, A('fires') + 1 + i * 0.2, A('fires') + 1.4 + i * 0.2)); ctx.fillStyle = '#05060a'; ctx.fillRect(x, y - 110, 3, 110); ctx.fillStyle = '#a3241a'; ctx.fillRect(x + 3, y - 108, 18 + Math.sin(t * 5 + i) * 2, 46); ctx.restore(); }
    txt('篝火多点几堆 · 旗多插几面', W / 2, 330, { size: 54, w: 900, color: '#fff3dc', a: aFi * blk(t, 'fires', 'fires'), stroke: 6 });
    const aCv = aFi * blk(t, 'caveat', 'caveat'); if (aCv > 0) { dimAll(aCv * 0.5); panel(90, 580, 900, 360, aCv, 'rgba(10,8,6,0.92)'); txt('说明', W / 2, 660, { size: 40, w: 800, color: C.gold, a: aCv }); txt('以上是战国撤退的一般打法', W / 2, 760, { size: 44, w: 800, color: '#fff3dc', a: aCv }); txt('金崎那几天的具体战况，史料几乎无细节', W / 2, 850, { size: 38, w: 700, color: C.bone, a: aCv }); }
    tag('情景演绎 · 示意', aFi);
  }
  // cohesion
  const aCo = blk(t, 'why_stay', 'leader');
  if (aCo > 0) {
    bgGrad('#05070c', '#120c0a', aCo);
    txt('殿军的人，为什么不跑？', W / 2, 360, { size: 66, w: 900, color: '#fff3dc', a: aCo, stroke: 6 });
    const aC1 = aCo * rise(t, 'cohesion');
    txt('Shils & Janowitz 1948 · 德军战俘访谈', W / 2, 470, { size: 32, w: 600, color: C.gold, a: aC1 * (1 - rise(t, 'leader')) });
    const cx = W / 2, cy = 960; for (let i = 0; i < 6; i++) { const an = i / 6 * Math.PI * 2 - Math.PI / 2; const x = cx + Math.cos(an) * 230, y = cy + Math.sin(an) * 230; ctx.save(); ctx.globalAlpha = aC1 * 0.7; ctx.strokeStyle = C.gold; ctx.lineWidth = 3; for (let j = i + 1; j < 6; j++) { const an2 = j / 6 * Math.PI * 2 - Math.PI / 2; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(cx + Math.cos(an2) * 230, cy + Math.sin(an2) * 230); ctx.stroke(); } ctx.restore(); soldier(x, y + 60, 1.3, { a: aC1, col: '#5a1a12', spear: 1 }); }
    txt('撑住士兵的，是身边那几个同伴', W / 2, 1290, { size: 48, w: 900, color: '#fff3dc', a: aC1 * ease(seg(t, A('cohesion') + 4, A('cohesion') + 4.6)), stroke: 5 });
    const aLd = aCo * rise(t, 'leader'); if (aLd > 0) { glowDot(cx, cy + 20, 200, 'rgba(255,90,50,0.5)', aLd); soldier(cx, cy + 80, 2.0, { a: aLd, col: '#ff5a36', spear: 1 }); dimAll(0); txt('指挥官留在最后 = 最有力的命令', W / 2, 560, { size: 46, w: 900, color: C.grHi, a: aLd * ease(seg(t, A('leader') + 4, A('leader') + 4.5)), stroke: 5 }); }
  }
  // alone: main body leaves; silence beat
  const aAl = blk(t, 'alone', 'alone', 0.4, 0.6);
  if (aAl > 0) {
    landscape(t, { mood: 'night', z: 1.6, torches: 1, mainA: 1 - ease(seg(t, A('alone'), Z('alone'))), fireA: 0.4 });
    dimAll(0.25);
    txt('身后，再也没有人了', W / 2, 420, { size: 72, w: 900, color: '#fff3dc', a: aAl * ease(seg(t, Z('alone') - 2.5, Z('alone') - 1.8)), stroke: 7, ls: 6 });
  }
  // Kutsuki route (map C)
  const aK = blk(t, 'where', 'kyoto');
  if (aK > 0) {
    mapCam(t, [[A('where') - 0.3, CAMS.wide], [A('kutsuki') + 1, [135.98, 35.36, 1500]], [A('matsunaga'), CAMS.kutsuki], [Z('kyoto'), [135.86, 35.22, 1700]]]); grade('night', 0.55); dimAll(1 - aK); mapOn = aK;
    baseLabels(aK, 'nok'); label(...PL.tsuruga, '敦贺', { a: aK, dx: 70, dy: -10 });
    label(...PL.kutsuki, '朽木谷', { a: aK, color: C.gold, dx: -110, dy: 0 }); label(...PL.kuma, '熊川', { a: aK * 0.8, dx: -80, dy: 0, size: 32 });
    regionGlow(136.22, 35.33, 0.22, 'rgba(125,151,189,0.55)', aK * ease(seg(t, A('kutsuki') + 1, A('kutsuki') + 2))); areaLabel(136.25, 35.30, '浅井的地盘', { a: aK * ease(seg(t, A('kutsuki') + 1, A('kutsuki') + 2)), size: 40, color: C.azHi });
    arrow(AZ_CUT, ease(seg(t, A('kutsuki'), A('kutsuki') + 2)), { color: C.az, hi: C.azHi, w: 36, a: aK * 0.8 });
    routeLine(ROUTE_BACK, ease(seg(t, A('kutsuki') + 2.5, Z('kyoto') - 1)), C.gr, aK, 8, false);
    const aMt = aK * blk(t, 'matsunaga', 'matsunaga'); if (aMt > 0) { nameCard(300, 420, '朽木元纲', '朽木谷领主', C.gold, aMt, { w: 380 }); nameCard(780, 420, '松永久秀', '随军', C.gr, aMt * rise(t, 'matsunaga', 0.6, 3), { w: 360 }); arrow2(600, 420, 500, 420, aMt * rise(t, 'matsunaga', 0.6, 4), C.gold, 8); txt('说服 · 放行（据《朝仓记》）', W / 2, 560, { size: 38, w: 700, color: C.bone, a: aMt * rise(t, 'matsunaga', 0.6, 4) }); }
    const aKy = aK * blk(t, 'kyoto', 'kyoto'); txt('4月30日 回到京都', W / 2, 330, { size: 62, w: 900, color: '#fff3dc', a: aKy, stroke: 6 }); txt('（西历6月3日）· 随从约十人（《继芥记》）', W / 2, 420, { size: 34, w: 600, color: C.gold, a: aKy });
  }
  // ten riders silhouette in gorge (overlay at end of kyoto line)
  // loss / anegawa / result
  const aLo = blk(t, 'loss', 'loss2');
  if (aLo > 0) {
    paperBg(aLo);
    txt('《多闻院日记》', W / 2, 400, { size: 44, w: 800, color: C.gold, a: aLo });
    txt('廿五日人数二千余も損歟', W / 2, 540, { size: 66, w: 700, color: '#fff3dc', a: aLo * rise(t, 'loss', 0.6, 1.5), fam: JP, ls: 4 });
    txt('传闻：二十五日一战，损兵两千多人？', W / 2, 650, { size: 40, w: 700, color: C.bone, a: aLo * rise(t, 'loss', 0.6, 3) });
    stamp('传闻 · 实否不知', W / 2, 800, aLo * rise(t, 'loss', 0.5, 6.5), -0.06, '#c9a24a', 46);
    const aL2 = aLo * rise(t, 'loss2'); ['木下藤吉郎', '明智光秀', '池田胜正'].forEach((n, i) => { txt(n, 430, 1000 + i * 110, { size: 52, w: 900, color: '#fff3dc', a: aL2 * rise(t, 'loss2', 0.4, 2 + i * 0.6), align: 'left' }); checkMark(360, 1000 + i * 110, 26, aL2 * rise(t, 'loss2', 0.4, 2.2 + i * 0.6)); });
    txt('活着回到京都', W / 2, 1310, { size: 46, w: 800, color: '#7fe08a', a: aL2 * rise(t, 'loss2', 0.5, 4.5) });
  }
  const aAn = blk(t, 'anegawa', 'result2');
  if (aAn > 0) {
    mapCam(t, [[A('anegawa') - 0.3, CAMS.azai], [Z('anegawa'), [136.2, 35.45, 1900]], [A('result'), CAMS.wide], [Z('result2'), CAMS.wide]]); dimAll(1 - aAn); mapOn = aAn;
    baseLabels(aAn);
    const aA1 = aAn * (1 - ease(seg(t, A('result') - 0.3, A('result') + 0.2)));
    label(...PL.anegawa, '姉川', { a: aA1, color: '#fff3dc', dx: -80, dy: 10 });
    arrow([[136.18, 35.36], [136.25, 35.39], [136.29, 35.408]], eio(seg(t, A('anegawa') + 0.5, A('anegawa') + 2.5)), { w: 46, a: aA1 });
    arrow([[136.33, 35.48], [136.315, 35.44], [136.305, 35.42]], eio(seg(t, A('anegawa') + 0.5, A('anegawa') + 2.5)), { color: C.az, hi: C.azHi, w: 40, a: aA1 });
    const [ax, ay] = P(...PL.anegawa); for (let k = 0; k < 4; k++) sparks(ax, ay, t, A('anegawa') + 2.5 + k * 0.35, aA1, k + 3, 1.6);
    txt('元龟元年6月 · 姉川之战', W / 2, 300, { size: 52, w: 900, color: '#fff3dc', a: aA1, stroke: 6 });
    txt('1573年 · 朝仓、浅井先后灭亡', W / 2, 1260, { size: 50, w: 900, color: C.grHi, a: aA1 * rise(t, 'anegawa', 0.5, 5), stroke: 5 });
    const aRs = aAn * ease(seg(t, A('result') - 0.3, A('result') + 0.2));
    routeLine(ROUTE_BACK, 1, C.gr, aRs, 6, false); armyBlob(...PL.kyoto, C.gr, aRs, t, 50, 0.03);
    txt('一场可能全军覆没的包围', W / 2, 300, { size: 54, w: 900, color: '#fff3dc', a: aRs, stroke: 6 }); txt('→ 一场狼狈的撤退', W / 2, 390, { size: 54, w: 900, color: C.grHi, a: aRs * rise(t, 'result', 0.5, 2.5), stroke: 6 });
    const aR2 = aAn * rise(t, 'result2'); txt('信长：败仗', 320, 1260, { size: 56, w: 900, color: C.bone, a: aR2, stroke: 5 }); txt('殿军：赢了', 760, 1260, { size: 56, w: 900, color: C.gold, a: aR2 * rise(t, 'result2', 0.5, 2), stroke: 5 });
  }
  return mapOn;
};
/* kutsuki gorge riders overlay (inside s3, drawn after map at kyoto line) */
const _s3 = SCN.s3;
SCN.s3 = function (t) {
  const m = _s3(t);
  const aG = blk(t, 'kyoto', 'kyoto', 0.5, 0.5) * ease(seg(t, A('kyoto') + 1.0, A('kyoto') + 1.8));
  if (aG > 0) {
    ctx.save(); ctx.globalAlpha = aG; landscape(t, { mood: 'dawn', z: 1.1, torches: 0, banner: 0, empty: 1 }); ctx.fillStyle = '#040304'; ctx.beginPath(); ctx.moveTo(0, 1300); for (let x = 0; x <= W; x += 30) ctx.lineTo(x, 1270 + 18 * Math.sin(x / 140)); ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.fill(); ctx.restore();
    for (let i = 0; i < 11; i++) { const p = ((t - A('kyoto')) * 0.06 + i * 0.075) % 1.25; rider(lerp(1250, -350, p), 1290 - (i % 3) * 6, 1.25 - (i % 3) * 0.08, t * 13 + i * 1.7, { a: aG, dir: -1, col: '#020203' }); if (i % 4 === 0) glowDot(lerp(1250, -350, p) - 10, 1290 - 180, 30, 'rgba(255,150,60,0.8)', aG); }
    txt('4月30日 · 回到京都', W / 2, 330, { size: 66, w: 900, color: '#fff3dc', a: aG, stroke: 6 }); txt('（西历6月3日）', W / 2, 410, { size: 34, w: 600, color: C.bone, a: aG }); txt('随从约十人 ·《继芥记》', W / 2, 500, { size: 44, w: 800, color: C.gold, a: aG, stroke: 4 });
    tag('情景演绎 · 示意', aG);
  }
  return m;
};

/* ---------- s4 source conflicts ---------- */
function claimCard(t, y, n, q, ans, col, a, aAns) {
  if (a <= 0.01) return; panel(70, y - 120, 940, 240, a, 'rgba(12,10,8,0.92)');
  txt(n, 150, y - 40, { size: 64, w: 900, color: C.gold, a }); const ql = wrapBal(q, 760, 42, 800); ql.forEach((s, i) => txt(s, 560, y - 50 - (ql.length - 1) * 26 + i * 54, { size: 42, w: 800, color: '#fff3dc', a }));
  stamp(ans, 560, y + 64, aAns, -0.05, col, 44);
}
SCN.s4 = function (t) {
  const s = SC.s4; let mapOn = 0;
  const aB = fade(t, s.t0, NX('c5b') + 0.05, 0.5, 0.4);
  if (aB > 0) {
    paperBg(aB);
    txt('流行说法 · 逐条核对', W / 2, 220, { size: 62, w: 900, color: '#fff3dc', a: aB, stroke: 6, ls: 6 });
    const cards = [['c1', 'c1b', '一', '被留下，还是自己请缨？', '奉命在先 · 请缨晚出', '#e0a040'], ['c2', 'c2b', '二', '秀吉是殿军总大将？', '一员 · 很可能非总指挥', '#e0a040'], ['c3', 'c3', '三', '德川家康参加断后？', '存疑', '#a0a8b8'], ['c4', 'c4', '四', '阿市送两头扎紧的小豆袋？', '后世创作', '#e0473a'], ['c5', 'c5b', '五', '撤退其实没那么惊险？', '一说 · 待考', '#a0a8b8']];
    cards.forEach(([v1, v2, n, q, ans, col], i) => {
      const aC = aB * fade(t, A(v1) - 0.3, NX(v2) + 0.05, 0.4, 0.4); if (aC <= 0) return;
      claimCard(t, 410, n, q, ans, col, aC, aC * ease(seg(t, (v1 === 'c3' || v1 === 'c4') ? Z(v2) - 2.4 : A(v2) + 0.3, (v1 === 'c3' || v1 === 'c4') ? Z(v2) - 1.8 : A(v2) + 0.9)));
      // evidence row
      if (v1 === 'c1') { const ae = aC * rise(t, 'c1a'); txt('《信长公记》：残しをかせられ（被留下）', W / 2, 1090, { size: 38, w: 700, color: C.bone, a: ae, fam: JP }); txt('《当代记》（江户初期）：吾を可被残（请留下我）', W / 2, 1160, { size: 38, w: 700, color: C.bone, a: ae * rise(t, 'c1a', 0.5, 2.5), fam: JP }); }
      if (v1 === 'c2') { const ae = aC * rise(t, 'c2b'); txt('池田胜正：摄津大领主，地位远高于秀吉', W / 2, 1100, { size: 38, w: 700, color: C.bone, a: ae }); }
      if (v1 === 'c3') { const ae = aC * rise(t, 'c3', 0.5, 3); txt('只见于《宽永诸家系图传》《德川实纪》（江户）', W / 2, 700, { size: 36, w: 700, color: C.bone, a: ae }); txt('同时代一手史料：无其名', W / 2, 780, { size: 36, w: 700, color: C.bone, a: ae * rise(t, 'c3', 0.5, 6) }); }
      if (v1 === 'c4') { const ae = aC * rise(t, 'c4', 0.5, 4); txt('出自《朝仓家记》 · 《信长公记》未提', W / 2, 720, { size: 38, w: 700, color: C.bone, a: ae }); }
      if (v1 === 'c5') { const ae = aC * rise(t, 'c5b'); txt('写给盟友的信 · 也可能是在保面子', W / 2, 1100, { size: 38, w: 700, color: C.bone, a: ae }); }
    });
  }
  const aW = blk(t, 'why_ver', 'credit2');
  if (aW > 0) {
    bgGrad('#07080c', '#150f0a', aW);
    txt('为什么有这么多版本？', W / 2, 330, { size: 62, w: 900, color: '#fff3dc', a: aW, stroke: 6 });
    txt('因为秀吉后来成了天下人', W / 2, 450, { size: 54, w: 900, color: C.gold, a: aW * rise(t, 'why2'), stroke: 5 });
    // credit diagram: names on a line; one grows, others fade
    const names = ['池田胜正', '明智光秀', '木下藤吉郎', '其他人'];
    const g = ease(seg(t, A('credit') + 1, Z('credit2')));
    names.forEach((n, i) => { const isH = i === 2; const x = W / 2, y = 680 + i * 150; const sc = isH ? 1 + 0.7 * g : 1 - 0.2 * g; const aa = aW * rise(t, 'credit', 0.6, i * 0.3) * (isH ? 1 : 1 - 0.75 * g); ctx.save(); ctx.translate(x, y); ctx.scale(sc, sc); txt(n, 0, 0, { size: 56, w: 900, color: isH ? C.grHi : C.bone, a: aa, stroke: 5 }); ctx.restore(); });
    txt('功劳，按后来谁当了老大来改写', W / 2, 1310, { size: 46, w: 900, color: '#fff3dc', a: aW * rise(t, 'credit', 0.6, 3), stroke: 5 });
  }
  return mapOn;
};

/* ---------- s5 reward ---------- */
function koban(x, y, s, a, rot = 0) { if (a <= 0.01) return; ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s); const g = ctx.createLinearGradient(-50, -80, 50, 80); g.addColorStop(0, '#fff0a8'); g.addColorStop(0.5, '#d6a63a'); g.addColorStop(1, '#8a6418'); ctx.fillStyle = g; ctx.shadowColor = 'rgba(255,200,80,0.6)'; ctx.shadowBlur = 30; ctx.beginPath(); ctx.ellipse(0, 0, 52, 82, 0, 0, Math.PI * 2); ctx.fill(); ctx.shadowBlur = 0; ctx.strokeStyle = 'rgba(120,80,20,0.6)'; ctx.lineWidth = 2; for (let i = -5; i <= 5; i++) { ctx.beginPath(); ctx.moveTo(-40, i * 13); ctx.lineTo(40, i * 13); ctx.stroke(); } ctx.restore(); }
SCN.s5 = function (t) {
  const s = SC.s5; let mapOn = 0;
  const aG = fade(t, s.t0, NX('reward') + 0.05, 0.5, 0.4);
  if (aG > 0) {
    bgGrad('#0a0806', '#1a120a', aG);
    txt('留下来，值不值？', W / 2, 360, { size: 72, w: 900, color: '#fff3dc', a: aG, stroke: 6 });
    for (let i = 0; i < 7; i++) koban(260 + i * 95, 820 + Math.sin(t * 2 + i) * 8, 1.0, aG * rise(t, 'gold', 0.5, i * 0.2), (i - 3) * 0.08);
    txt('？', W / 2, 820, { size: 200, w: 900, color: '#fff3dc', a: aG * rise(t, 'gold', 0.5, 5), stroke: 10 });
    txt('「赏了黄金」出自《武功夜话》一类后世书', W / 2, 1100, { size: 40, w: 700, color: C.bone, a: aG * rise(t, 'gold', 0.5, 2) });
    txt('其书真伪有争议 · 一手史料无具体数目', W / 2, 1170, { size: 40, w: 700, color: C.bone, a: aG * rise(t, 'gold', 0.5, 5) });
    txt('真正的回报，不在赏赐', W / 2, 1360, { size: 56, w: 900, color: C.gold, a: aG * rise(t, 'reward'), stroke: 5 });
  }
  const aV = blk(t, 'lowborn', 'survive');
  if (aV > 0) {
    columnScene(t, aV, 'retreat');
    // one figure facing back, spotlit
    const sp = aV * rise(t, 'visible', 0.8, 2.5); if (sp > 0) { ctx.save(); ctx.globalAlpha = sp; const g = ctx.createRadialGradient(780, 1150, 0, 780, 1150, 420); g.addColorStop(0, 'rgba(255,220,160,0.45)'); g.addColorStop(1, 'rgba(255,220,160,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore(); soldier(780, 1260, 1.9, { a: sp, col: '#ff5a36' }); }
    txt('出身低微 · 没有家族靠山', W / 2, 360, { size: 56, w: 900, color: '#fff3dc', a: aV * blk(t, 'lowborn', 'lowborn'), stroke: 5 });
    txt('全军都看得见 · 主帅也记得住', W / 2, 360, { size: 52, w: 900, color: '#fff3dc', a: aV * blk(t, 'visible', 'visible'), stroke: 5 });
    bigText(['最危险的位置', '也是最被看见的位置'], 340, aV * blk(t, 'visible2', 'visible2'), { size: 64 });
    txt('前提：你得活着回来', W / 2, 400, { size: 72, w: 900, color: C.gold, a: aV * blk(t, 'survive', 'survive'), stroke: 6 });
  }
  const aN = blk(t, 'nagahama', 'irony');
  if (aN > 0) {
    mapCam(t, [[A('nagahama') - 0.3, CAMS.wide], [Z('irony'), CAMS.azai]]); dimAll(1 - aN); mapOn = aN;
    baseLabels(aN);
    regionGlow(136.27, 35.42, 0.2, 'rgba(255,80,50,0.8)', aN * rise(t, 'nagahama', 1, 2));
    label(...PL.nagahama, '长滨', { a: aN * rise(t, 'nagahama', 0.6, 3), color: C.grHi, dx: -80, dy: 10 });
    txt('浅井旧领 · 北近江', W / 2, 300, { size: 58, w: 900, color: '#fff3dc', a: aN, stroke: 6 });
    txt('→ 羽柴秀吉（1573）', W / 2, 390, { size: 58, w: 900, color: C.grHi, a: aN * rise(t, 'nagahama', 0.6, 3.5), stroke: 6 });
    txt('倒戈者的地盘，落到了断后者手里', W / 2, 1260, { size: 46, w: 900, color: C.gold, a: aN * rise(t, 'irony', 0.6, 1.5), stroke: 5 });
  }
  return mapOn;
};

/* ---------- s6 ending ---------- */
SCN.s6 = function (t) {
  const s = SC.s6; let mapOn = 0;
  const aE = fade(t, s.t0, NX('fear2') + 0.05, 0.6, 0.5);
  if (aE > 0) {
    // dawn, empty Kanegasaki castle
    landscape(t, { mood: 'dawn', z: lerp(1.6, 1.35, seg(t, s.t0, NX('fear2'))), torches: 0, banner: 0, empty: 1 });
    ctx.save(); ctx.globalAlpha = 1 - aE; ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H); ctx.restore();
    txt('子路问：子行三军，则谁与？', W / 2, 330, { size: 48, w: 800, color: '#fff3dc', a: aE * blk(t, 'zilu', 'zilu'), stroke: 5 });
    bigText(['不是不怕死', '是怕死，而且有办法'], 360, aE * blk(t, 'fear', 'fear'), { size: 74 });
    const aF2 = aE * blk(t, 'fear2', 'fear2'); txt('先看好下一个山口', W / 2, 360, { size: 60, w: 900, color: '#fff3dc', a: aF2, stroke: 6 }); txt('自己站在最后', W / 2, 460, { size: 60, w: 900, color: C.grHi, a: aF2 * rise(t, 'fear2', 0.5, 3.2), stroke: 6 });
    tag('晨光中的金崎城 · 示意', aE);
  }
  const aW = blk(t, 'hideyoshi_later', 'work');
  if (aW > 0) {
    paperBg(aW);
    const items = [['鸟取城', '断粮'], ['高松城', '水淹'], ['本能寺之变后', '大军回师']]; const tb = A('hideyoshi_later') + 3.0;
    items.forEach((r, i) => { const ai = aW * blk(t, 'hideyoshi_later', 'hideyoshi_later') * ease(seg(t, tb + i * 1.4, tb + i * 1.4 + 0.4)); txt(r[0], 380, 640 + i * 160, { size: 54, w: 900, color: '#fff3dc', a: ai, align: 'right' }); txt('→ ' + r[1], 440, 640 + i * 160, { size: 54, w: 900, color: C.gold, a: ai, align: 'left' }); });
    txt('秀吉出名的不是硬冲，是算账', W / 2, 400, { size: 54, w: 900, color: '#fff3dc', a: aW * blk(t, 'hideyoshi_later', 'hideyoshi_later'), stroke: 5 });
    const aK = aW * blk(t, 'work', 'work'); if (aK > 0) { panel(70, 560, 940, 640, aK, 'rgba(12,10,8,0.92)'); txt('撤退时最该被奖励的', W / 2, 700, { size: 56, w: 900, color: C.bone, a: aK }); txt('是那个愿意留下来断后', W / 2, 840, { size: 62, w: 900, color: '#fff3dc', a: aK * rise(t, 'work', 0.5, 2.5) }); txt('而且有办法断后的人', W / 2, 960, { size: 62, w: 900, color: C.grHi, a: aK * rise(t, 'work', 0.5, 4.5) }); }
  }
  const aN = fade(t, A('next') - 0.3, TOTAL, 0.5, 0.01);
  if (aN > 0) {
    // Takamatsu: castle and rising water (stylized)
    ctx.save(); ctx.globalAlpha = aN; sky('dusk'); ctx.restore();
    const wl = lerp(1350, 1120, ease(seg(t, A('next') + 2, TOTAL - 1)));
    ctx.save(); ctx.globalAlpha = aN; ctx.fillStyle = '#1a1014'; ctx.beginPath(); ctx.moveTo(0, 1200); ctx.lineTo(W, 1180); ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.fill();
    ctx.fillStyle = '#0d0809'; ctx.fillRect(450, 1020, 180, 160); ctx.beginPath(); ctx.moveTo(430, 1030); ctx.lineTo(540, 960); ctx.lineTo(650, 1030); ctx.closePath(); ctx.fill(); ctx.fillRect(490, 900, 100, 70); ctx.beginPath(); ctx.moveTo(470, 910); ctx.lineTo(540, 860); ctx.lineTo(610, 910); ctx.closePath(); ctx.fill();
    // dike
    ctx.fillStyle = '#2a1d18'; ctx.beginPath(); ctx.moveTo(0, 1330); ctx.quadraticCurveTo(W / 2, 1270, W, 1330); ctx.lineTo(W, 1360); ctx.quadraticCurveTo(W / 2, 1300, 0, 1360); ctx.fill();
    const g = ctx.createLinearGradient(0, wl, 0, H); g.addColorStop(0, 'rgba(70,110,140,0.85)'); g.addColorStop(1, 'rgba(10,20,30,0.95)'); ctx.fillStyle = g; ctx.fillRect(0, wl, W, H - wl);
    ctx.restore(); ripples(t, aN, 9, 70);
    txt('十二年后 · 1582', W / 2, 300, { size: 46, w: 700, color: C.gold, a: aN, ls: 8 });
    txt('备中高松城', W / 2, 410, { size: 96, w: 900, color: '#fff3dc', a: aN, stroke: 8, ls: 12 });
    txt('一道长堤 · 一片湖', W / 2, 520, { size: 54, w: 800, color: C.peHi, a: aN * rise(t, 'next', 0.5, 4), stroke: 5 });
    txt('下一集', W / 2, 650, { size: 46, w: 700, color: C.bone, a: aN * rise(t, 'next2'), ls: 10 });
    txt('从无名小卒到天下人', W / 2, 740, { size: 52, w: 900, color: C.gold, a: aN * rise(t, 'next2'), ls: 8 });
    tag('示意', aN);
  }
  return mapOn;
};

/* ================= main ================= */
function renderFrame(t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  let sc = D.tl.scenes[0]; for (const s of D.tl.scenes) if (t >= s.t0) sc = s;
  const mapOn = SCN[sc.id](t) || 0;
  const i = D.tl.scenes.indexOf(sc);
  if (i > 0) { const k = 1 - ease(seg(t, sc.t0, sc.t0 + 0.5)); if (k > 0) { ctx.fillStyle = `rgba(0,0,0,${k})`; ctx.fillRect(0, 0, W, H); } }
  const nx = D.tl.scenes[i + 1]; if (nx) { const k = ease(seg(t, nx.t0 - 0.45, nx.t0)); if (k > 0) { ctx.fillStyle = `rgba(0,0,0,${k})`; ctx.fillRect(0, 0, W, H); } }
  if (t > TOTAL - 1.2) { ctx.fillStyle = `rgba(0,0,0,${ease(seg(t, TOTAL - 1.2, TOTAL - 0.1))})`; ctx.fillRect(0, 0, W, H); }
  vignette(0.9);
  chapterCard(t);
  quoteCard(t);
  subtitles(t);
  badges(t, mapOn);
}
function renderCover() {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  const t = 7.3; landscape(t, { mood: 'dusk', z: 1.55, fireA: 0.9 });
  vignette(1.0);
  const g = ctx.createLinearGradient(0, 0, 0, 820); g.addColorStop(0, 'rgba(0,0,0,0.8)'); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, 820);
  txt('从无名小卒到天下人 · 2', W / 2, 200, { size: 40, w: 700, color: C.gold, ls: 10 });
  txt('全军撤退时', W / 2, 360, { size: 120, w: 900, color: '#fff1d6', ls: 10, stroke: 10 });
  txt('谁留下来断后？', W / 2, 520, { size: 120, w: 900, color: C.grHi, ls: 8, stroke: 10 });
  const b = ctx.createLinearGradient(0, H - 600, 0, H); b.addColorStop(0, 'rgba(0,0,0,0)'); b.addColorStop(1, 'rgba(0,0,0,0.9)'); ctx.fillStyle = b; ctx.fillRect(0, H - 600, W, 600);
  txt('金崎撤退 · 1570', W / 2, 1540, { size: 64, w: 900, color: '#fff1d6', ls: 8, stroke: 6 });
  txt('最危险的位置：殿军', W / 2, 1640, { size: 46, w: 700, color: C.gold, ls: 6 });
  txt('情景演绎 · 示意', W - 46, 1860, { size: 22, w: 400, color: 'rgba(230,225,210,0.6)', align: 'right' });
}
window.renderCover = renderCover;
window.renderFrame = renderFrame; window.TOTAL = TOTAL; window.A_ = A; window.LINES = LINES;
window.ready = loadAll();
