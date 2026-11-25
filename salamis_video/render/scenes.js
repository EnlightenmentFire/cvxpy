'use strict';
/* ================= places (lon, lat) ================= */
const PL = {
  psy: [23.586, 37.9425], kyn: [23.566, 37.9468], perama: [23.575, 37.966], piraeus: [23.637, 37.938], munychia: [23.655, 37.939],
  phaleron: [23.685, 37.933], athens: [23.7267, 37.9715], eleusis: [23.543, 38.038], megara: [23.345, 37.996], aegina: [23.47, 37.735],
  troezen: [23.36, 37.505], isthmus: [22.99, 37.925], corinth: [22.88, 37.905], laurium: [24.05, 37.715], xerxes: [23.588, 37.9705],
  ambelaki: [23.538, 37.952], westCh: [23.415, 37.972], salamis: [23.47, 37.905], sparta: [22.43, 37.075], thermo: [22.54, 38.80],
  artem: [23.25, 39.01], delphi: [22.50, 38.48], plataea: [23.27, 38.21], sardis: [28.04, 38.49], abydos: [26.41, 40.19], athos: [23.93, 40.39],
  therma: [22.94, 40.64], doriskos: [26.1, 40.87], thessaly: [22.4, 39.55], siris: [16.65, 40.18],
};
const CAM = {
  aegean: [24.4, 38.75, 165], aegeanS: [23.6, 38.4, 260], saronic: [23.30, 37.80, 950], saronicN: [23.42, 37.90, 1500],
  strait: [23.565, 37.955, 11000], straitW: [23.56, 37.952, 8200], straitClose: [23.556, 37.956, 17000], psy: [23.58, 37.947, 15000],
};

/* ================= battle simulation (metres; local tangent plane) ================= */
const M_LON = 87800, M_LAT = 111000, O_LON = 23.56, O_LAT = 37.95;
const toM = (lon, lat) => [(lon - O_LON) * M_LON, (lat - O_LAT) * M_LAT];
const toLL = (x, y) => [O_LON + x / M_LON, O_LAT + y / M_LAT];
const BS = (() => {
  const K = 9, N = 14, SP0 = 230, G = 120, V = 40, TAU = 0.7;
  const lanes = [];
  for (let k = 0; k < K; k++) {
    const f = k / (K - 1);                       // 0 = south lane, 1 = north lane
    const front = toM(lerp(23.5545, 23.5530, f), lerp(37.9505, 37.9625, f));
    const gate = toM(lerp(23.5745, 23.5785, f), lerp(37.9500, 37.9555, f));
    const mid = toM(lerp(23.598, 23.604, f), lerp(37.9400, 37.9475, f));
    const far = toM(lerp(23.625, 23.640, f), lerp(37.9230, 37.9330, f));
    const farther = toM(lerp(23.650, 23.672, f), lerp(37.912, 37.922, f));
    const pts = smooth([far, mid, gate, front], 16);
    const L = [0]; for (let i = 1; i < pts.length; i++) L.push(L[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
    lanes.push({ pts, L, len: L[L.length - 1], f, delay: Math.abs(f - 0.5) * 18 + hash(k) * 6 });
  }
  function at(lane, s) {
    s = clamp(s, 0, lane.len); let i = 1; while (i < lane.L.length - 1 && lane.L[i] < s) i++;
    const u = (s - lane.L[i - 1]) / Math.max(1e-6, lane.L[i] - lane.L[i - 1]); const a = lane.pts[i - 1], b = lane.pts[i];
    return [lerp(a[0], b[0], u), lerp(a[1], b[1], u), Math.atan2(-(b[1] - a[1]), b[0] - a[0])];   // screen angle (y down)
  }
  // phases (sim seconds): contact at front ~ when leader reaches end; FLEE when front turns
  const FLEE = 290;
  function lead(lane, sg) {
    const free = V * (sg - lane.delay);
    let s = Math.min(free, lane.len - 2);
    if (sg > FLEE) s = Math.min(s, lane.len - 2 - 14 * (sg - FLEE - lane.delay * 0.3));
    return s;
  }
  function pos(lane, i, sg, memo) {
    const key = i * 100000 + Math.round(sg * 50); if (memo.has(key)) return memo.get(key);
    const free = V * (sg - lane.delay) - i * SP0;
    let s;
    if (i === 0) s = lead(lane, sg);
    else { const g = sg > FLEE + 8 ? lerp(G, 60, clamp((sg - FLEE - 8) / 25)) : G; s = Math.min(free, pos(lane, i - 1, sg - TAU, memo) - g); }
    memo.set(key, s); return s;
  }
  function state(sg) {
    const out = [];
    for (const lane of lanes) {
      const memo = new Map(); const ss = [];
      for (let i = 0; i < N; i++) ss.push(pos(lane, i, sg, memo));
      for (let i = 0; i < N; i++) {
        const s = ss[i]; if (s < -40) continue;
        const gap = i ? ss[i - 1] - s : 999;
        const comp = i ? clamp((SP0 - gap) / (SP0 - G + 1)) : (sg > lane.delay + lane.len / V - 2 ? 1 : 0);
        const [x, y, an] = at(lane, Math.max(0, s));
        const coll = i && gap < 95 ? clamp((95 - gap) / 70) : 0;
        const flee = i === 0 && sg > FLEE + lane.delay * 0.3 ? clamp((sg - FLEE - lane.delay * 0.3) / 6) : 0;
        out.push({ x, y, an: an + Math.PI * flee + (coll ? (hash(i * 13 + lane.f * 99) - 0.5) * 1.6 * coll : 0), comp, coll, k: lanes.indexOf(lane), i, s, flee, moving: s < Math.min(V * (sg - lane.delay) - i * SP0, lane.len) - 5 ? 0 : 1 });
      }
    }
    return out;
  }
  // Greek line: two ranks along lon ~23.546 facing east
  const greeks = [];
  for (let r = 0; r < 2; r++) for (let j = 0; j < 15; j++) { const f = j / 14; greeks.push({ ll: [lerp(23.5462, 23.5440, f) - r * 0.0016, lerp(37.9500, 37.9720, f)], r, j }); }
  return { lanes, state, greeks, FLEE, V, K, N };
})();
function drawGreeks(t, o = {}) {
  const { a = 1, L = 20, form = 1, strike = 0, sg = 0 } = o;
  for (const g of BS.greeks) {
    let [lon, lat] = g.ll; let an = 0;
    // formation: start beached along Salamis shore, slide out
    lon = lerp(lon - 0.004, lon, form);
    if (strike > 0 && g.r === 0 && (g.j < 4 || g.j > 10)) {
      const side = g.j < 4 ? -1 : 1; const p = eio(strike);
      lon += 0.010 * p; lat += side * -0.0035 * p * (1 - p) * 2 + side * -0.002 * p; an = -side * 0.6 * Math.sin(p * Math.PI);
    } else if (strike > 0 && g.r === 0) { lon += 0.004 * eio(strike); }
    const [x, y] = P(lon, lat);
    ship(x, y, an, L, C.gr, { a, oar: t * 6 + g.j, hi: C.grHi, glow: 10 });
  }
}
function drawPersians(t, sg, o = {}) {
  const { a = 1, L = 20, waveHi = 0, collFx = 1 } = o;
  const st = BS.state(sg);
  for (const s of st) {
    const [lon, lat] = toLL(s.x, s.y); const [x, y] = P(lon, lat);
    if (x < -60 || x > W + 60 || y < -60 || y > H + 60) continue;
    if (s.moving && !s.comp) wake(x, y, s.an, L * 1.6, 0.25 * a);
    const hot = waveHi * s.comp;
    ship(x, y, s.an, L, C.pe, { a, oar: s.comp > 0.6 ? 0 : t * 6 + s.i, hi: C.peHi, glow: 6 + hot * 14, halo: hot > 0.1 ? '#ffb040' : null, broken: s.coll });
    if (collFx && s.coll > 0.5) sparks(x, y, t, Math.floor(t * 1.3 + s.i) / 1.3, 0.8 * a, s.i * 7 + s.k, 0.6);
  }
  return st;
}
function mixc(a, b, p) { const pa = [1, 3, 5].map(i => parseInt(a.substr(i, 2), 16)), pb = [1, 3, 5].map(i => parseInt(b.substr(i, 2), 16)); return `rgb(${pa.map((v, i) => Math.round(lerp(v, pb[i], p))).join(',')})`; }

/* ================= illustrations ================= */
function bigText(lines, y, a, o = {}) { const { size = 76, color = '#fff3dc', gap = 1.35, w = 900 } = o; lines.forEach((s, i) => txt(s, W / 2, y + i * size * gap, { size, w, color, a, stroke: 6, ls: 4 })); }
function seaBg(t, kind = 'dawn') {
  const g = ctx.createLinearGradient(0, 0, 0, H);
  if (kind === 'dawn') { g.addColorStop(0, '#3a2418'); g.addColorStop(0.28, '#b8632e'); g.addColorStop(0.36, '#e9a050'); g.addColorStop(0.37, '#3a4450'); g.addColorStop(1, '#0b1620'); }
  else if (kind === 'night') { g.addColorStop(0, '#05070f'); g.addColorStop(0.36, '#16213a'); g.addColorStop(0.37, '#0f1a2a'); g.addColorStop(1, '#03060b'); }
  else { g.addColorStop(0, '#0a0d12'); g.addColorStop(1, '#020305'); }
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  // sea glints
  ctx.save(); ctx.globalCompositeOperation = 'screen';
  for (let i = 0; i < 160; i++) {
    const yy = H * 0.37 + Math.pow(hash(i * 3), 1.6) * H * 0.63, xx = (hash(i * 7) * W + Math.sin(t * 0.6 + i) * 20 + W) % W; const wl = 10 + (yy - H * 0.37) * 0.08;
    ctx.strokeStyle = kind === 'night' ? `rgba(170,190,230,${0.18 * (0.5 + 0.5 * Math.sin(t * 2 + i))})` : `rgba(255,190,120,${0.22 * (0.5 + 0.5 * Math.sin(t * 2 + i))})`;
    ctx.lineWidth = 1 + (yy - H * 0.37) / 500; ctx.beginPath(); ctx.moveTo(xx - wl, yy); ctx.lineTo(xx + wl, yy); ctx.stroke();
  }
  ctx.restore();
}
// side-view trireme (for diagram); x,y = waterline centre, L = length px
function triremeSide(x, y, L, t, o = {}) {
  const { a = 1, col = '#2a1c12', ram = '#c98f3c', oars = true, labels = 0, eye = true, dir = 1 } = o;
  ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.scale(dir, 1);
  const h = L * 0.075;
  // oars (three banks)
  if (oars) for (let b = 0; b < 3; b++) for (let i = 0; i < 26; i++) {
    const ox = -L * 0.36 + i * L * 0.70 / 25, oy = -h * (0.35 + b * 0.28); const ph = Math.sin(t * 5 - i * 0.05 + b * 0.3);
    ctx.strokeStyle = `rgba(${200 - b * 30},${170 - b * 25},${120 - b * 20},0.9)`; ctx.lineWidth = Math.max(1.2, L * 0.0028);
    ctx.beginPath(); ctx.moveTo(ox, oy); ctx.lineTo(ox + ph * L * 0.03 - L * 0.01, h * 1.5 + b * L * 0.004); ctx.stroke();
  }
  // hull
  ctx.beginPath(); ctx.moveTo(L * 0.5, h * 0.55); ctx.lineTo(L * 0.42, -h * 0.9); ctx.lineTo(-L * 0.40, -h * 0.9);
  ctx.quadraticCurveTo(-L * 0.52, -h * 1.2, -L * 0.5, -h * 3.4); ctx.quadraticCurveTo(-L * 0.47, -h * 0.6, -L * 0.38, h * 0.55); ctx.closePath();
  const g = ctx.createLinearGradient(0, -h, 0, h); g.addColorStop(0, '#5a3b22'); g.addColorStop(1, col); ctx.fillStyle = g; ctx.fill();
  ctx.strokeStyle = 'rgba(0,0,0,0.6)'; ctx.lineWidth = 2; ctx.stroke();
  // outrigger / deck lines
  ctx.strokeStyle = '#8a6a44'; ctx.lineWidth = Math.max(1.5, L * 0.004); ctx.beginPath(); ctx.moveTo(-L * 0.38, -h * 0.35); ctx.lineTo(L * 0.40, -h * 0.35); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-L * 0.38, -h * 0.9); ctx.lineTo(L * 0.42, -h * 0.9); ctx.stroke();
  // ram
  ctx.fillStyle = ram; ctx.beginPath(); ctx.moveTo(L * 0.58, h * 0.35); ctx.lineTo(L * 0.47, h * 0.0); ctx.lineTo(L * 0.47, h * 0.75); ctx.closePath(); ctx.fill();
  ctx.fillRect(L * 0.53, h * 0.25, L * 0.02, h * 0.22);
  // eye
  if (eye) { ctx.fillStyle = '#efe4c8'; ctx.beginPath(); ctx.ellipse(L * 0.43, -h * 0.4, L * 0.016, L * 0.009, 0, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(L * 0.435, -h * 0.4, L * 0.006, 0, Math.PI * 2); ctx.fill(); }
  ctx.restore();
}
function xerxesSil(x, y, s, a = 1, scribe = 1, t = 0) {
  ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.scale(s, s); ctx.fillStyle = '#07080a';
  // hill
  ctx.beginPath(); ctx.moveTo(-700, 260); ctx.quadraticCurveTo(-200, -40, 120, 40); ctx.quadraticCurveTo(400, 120, 700, 300); ctx.lineTo(700, 600); ctx.lineTo(-700, 600); ctx.fill();
  // parasol
  ctx.fillRect(-12, -300, 6, 300); ctx.beginPath(); ctx.moveTo(-160, -270); ctx.quadraticCurveTo(-9, -360, 142, -270); ctx.lineTo(-160, -270); ctx.fill();
  for (let i = 0; i < 9; i++) ctx.fillRect(-160 + i * 37, -270, 4, 18);
  // throne
  ctx.fillRect(-90, -150, 16, 175); ctx.fillRect(-90, -40, 150, 22); ctx.fillRect(48, -40, 12, 65); ctx.fillRect(-100, -170, 36, 26);
  // seated king: body, head with tall crown (no face)
  ctx.beginPath(); ctx.moveTo(-70, -30); ctx.lineTo(-56, -150); ctx.quadraticCurveTo(-30, -175, 0, -150); ctx.lineTo(18, -40); ctx.lineTo(70, -38); ctx.lineTo(70, 20); ctx.lineTo(40, 20); ctx.lineTo(40, -14); ctx.lineTo(-70, -10); ctx.fill();
  ctx.beginPath(); ctx.arc(-30, -178, 22, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.moveTo(-50, -190); ctx.lineTo(-46, -232); ctx.lineTo(-14, -232); ctx.lineTo(-10, -190); ctx.fill();
  ctx.beginPath(); ctx.moveTo(-14, -168); ctx.quadraticCurveTo(-4, -140, -20, -120); ctx.lineTo(-30, -150); ctx.fill();   // beard
  // arm with sceptre pointing
  ctx.save(); ctx.translate(-10, -120); ctx.rotate(-0.25 + 0.05 * Math.sin(t)); ctx.fillRect(0, -6, 80, 14); ctx.restore();
  if (scribe) { ctx.globalAlpha = a * scribe;
    ctx.beginPath(); ctx.arc(190, -60, 18, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.moveTo(165, -42); ctx.lineTo(215, -42); ctx.lineTo(225, 40); ctx.lineTo(160, 40); ctx.fill();
    ctx.save(); ctx.translate(150, -25); ctx.rotate(-0.5); ctx.fillRect(-30, -4, 50, 34); ctx.restore();
  }
  ctx.restore();
}
function temple(x, y, s, a = 1) {
  ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.scale(s, s); ctx.fillStyle = '#0a0b0d';
  ctx.beginPath(); ctx.moveTo(-320, -300); ctx.lineTo(0, -400); ctx.lineTo(320, -300); ctx.fill(); ctx.fillRect(-330, -300, 660, 30); ctx.fillRect(-340, 0, 680, 30); ctx.fillRect(-360, 30, 720, 30);
  for (let i = 0; i < 7; i++) { const cx = -290 + i * 96.6; ctx.fillRect(cx - 18, -270, 36, 270); }
  ctx.restore();
}
function tripodSmoke(x, y, t, a = 1) {
  ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = '#c9a466'; ctx.lineWidth = 6;
  ctx.beginPath(); ctx.moveTo(x - 60, y + 120); ctx.lineTo(x - 30, y); ctx.moveTo(x + 60, y + 120); ctx.lineTo(x + 30, y); ctx.moveTo(x, y + 130); ctx.lineTo(x, y); ctx.stroke();
  ctx.fillStyle = '#8a6a3a'; ctx.beginPath(); ctx.ellipse(x, y, 70, 22, 0, 0, Math.PI); ctx.fill();
  for (let i = 0; i < 26; i++) { const ph = (t * 0.1 + hash(i * 5)) % 1; const px = x + Math.sin(ph * 6 + i) * 40 * ph + (hash(i) - 0.5) * 30, py = y - ph * 600; const r = 20 + ph * 110;
    const g = ctx.createRadialGradient(px, py, 0, px, py, r); g.addColorStop(0, `rgba(200,195,185,${0.16 * Math.sin(ph * Math.PI)})`); g.addColorStop(1, 'rgba(200,195,185,0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(px, py, r, 0, Math.PI * 2); ctx.fill(); }
  ctx.restore();
}
function theatre(x, y, s, a = 1, t = 0) {
  ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.scale(s, s);
  for (let r = 0; r < 14; r++) { ctx.strokeStyle = `rgba(${190 - r * 6},${160 - r * 6},${120 - r * 5},0.9)`; ctx.lineWidth = 10; ctx.beginPath(); ctx.ellipse(0, 0, 160 + r * 28, 70 + r * 13, 0, Math.PI * 1.02, Math.PI * 1.98); ctx.stroke(); }
  ctx.fillStyle = '#d8c7a0'; ctx.beginPath(); ctx.ellipse(0, 10, 140, 50, 0, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#2a2018'; ctx.fillRect(-260, 70, 520, 60);
  // tiny audience dots
  for (let i = 0; i < 260; i++) { const r = 2 + Math.floor(hash(i) * 12), an = Math.PI * (1.05 + hash(i * 3) * 0.9); ctx.fillStyle = 'rgba(30,22,16,0.8)'; ctx.beginPath(); ctx.arc(Math.cos(an) * (160 + r * 28), Math.sin(an) * (70 + r * 13) - 6, 4, 0, Math.PI * 2); ctx.fill(); }
  ctx.restore();
}
function coin(x, y, r, a = 1, rot = 0) {
  ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.scale(Math.cos(rot), 1);
  const g = ctx.createRadialGradient(-r * 0.3, -r * 0.3, 0, 0, 0, r); g.addColorStop(0, '#f4f4f0'); g.addColorStop(1, '#8b8e93');
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, r, 0, Math.PI * 2); ctx.fill(); ctx.strokeStyle = '#5c5f64'; ctx.lineWidth = 2; ctx.stroke();
  // owl
  ctx.fillStyle = '#5c5f64'; ctx.beginPath(); ctx.ellipse(0, r * 0.1, r * 0.35, r * 0.48, 0, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = '#e8e8e4'; ctx.beginPath(); ctx.arc(-r * 0.14, -r * 0.12, r * 0.11, 0, Math.PI * 2); ctx.arc(r * 0.14, -r * 0.12, r * 0.11, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}
function shipGrid(n, x0, y0, cols, dx, dy, L, a, p = 1, col = C.gr) { for (let i = 0; i < n; i++) { const q = clamp(p * n - i); if (q <= 0) break; ship(x0 + (i % cols) * dx, y0 + Math.floor(i / cols) * dy, -Math.PI / 2, L, col, { a: a * q, glow: 6 }); } }
function cross(x, y, s, a, col = '#ff4a3a') { ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = col; ctx.lineWidth = s * 0.18; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x - s, y - s); ctx.lineTo(x + s, y + s); ctx.moveTo(x + s, y - s); ctx.lineTo(x - s, y + s); ctx.stroke(); ctx.restore(); }
function tick(x, y, s, a, col = '#7fe08a') { ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = col; ctx.lineWidth = s * 0.2; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x - s, y); ctx.lineTo(x - s * 0.3, y + s * 0.7); ctx.lineTo(x + s, y - s * 0.8); ctx.stroke(); ctx.restore(); }
function stamp(s, x, y, a, rot = -0.12, col = '#e0473a') { ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.rotate(rot); ctx.scale(1 + 0.6 * (1 - ease(a)), 1 + 0.6 * (1 - ease(a))); ctx.strokeStyle = col; ctx.lineWidth = 6; font(64, 900, SONG); const w = ctx.measureText(s).width + 60; ctx.strokeRect(-w / 2, -54, w, 108); ctx.fillStyle = col; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(s, 0, 4); ctx.restore(); }
function dimAll(a) { if (a > 0.003) { ctx.fillStyle = `rgba(2,4,8,${a})`; ctx.fillRect(0, 0, W, H); } }
function wall(lonA, latA, lonB, latB, p, a) { const [x0, y0] = P(lonA, latA), [x1, y1] = P(lonB, latB); const x = lerp(x0, x1, p), y = lerp(y0, y1, p); ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = '#e8d5a8'; ctx.lineWidth = 10; ctx.shadowColor = '#000'; ctx.shadowBlur = 8; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x, y); ctx.stroke(); const n = Math.floor(Math.hypot(x - x0, y - y0) / 16); const an = Math.atan2(y1 - y0, x1 - x0); ctx.fillStyle = '#e8d5a8'; for (let i = 0; i < n; i += 2) { const cx = x0 + Math.cos(an) * i * 16, cy = y0 + Math.sin(an) * i * 16; ctx.save(); ctx.translate(cx, cy); ctx.rotate(an); ctx.fillRect(0, -14, 10, 10); ctx.restore(); } ctx.restore(); }
function fleetBlob(lon, lat, n, col, a, t, spread = 0.03, L = 14, seed = 1, ang = 0) { const [cx, cy] = P(lon, lat); const R = spread * cam.ppd; for (let i = 0; i < n; i++) { const r = Math.sqrt(hash(i * 3 + seed)) * R, an = hash(i * 7 + seed) * Math.PI * 2; ship(cx + Math.cos(an) * r * 1.3, cy + Math.sin(an) * r * 0.8, ang + (hash(i + seed) - 0.5) * 0.4, L, col, { a, oar: t * 5 + i, glow: 8 }); } }

/* ================= scenes ================= */
const SCN = {};

/* ---------- s0: hook ---------- */
SCN.s0 = (t) => {
  let mapOn = 1;
  const tq = A('numbers'), tx = A('xerxes'), txo = A('xerxes_out'), ttw = A('twist'), tqr = A('quarrel'), tlt = A('letter'), tq3 = A('q3');
  if (t < tq + 0.4 || (t >= tx - 0.2 && t < txo + 0.5)) {
    // dawn strait, battle approach
    const k = camKeys(t, [[0, [23.573, 37.951, 17000]], [A('place') - 1.5, [23.568, 37.953, 14000]], [A('place') + 1, [23.565, 37.957, 11500]], [Z('place'), [23.565, 37.957, 10500]], [tx, [23.575, 37.958, 12500]], [Z('xerxes'), [23.580, 37.962, 14000]]]);
    setCam(k); drawMap(); grade('dawn', 1);
    const sg = 115 + t * 5.5; const Ls = clamp(cam.ppd / 11000 * 21, 16, 34);
    drawPersians(t, sg, { L: Ls, waveHi: 0.6 }); drawGreeks(t, { L: Ls });
    ripples(t, 0.6, 3);
    // title + strait width marker
    const a1 = fade(t, A('place') - 0.2, tq + 0.3, 0.6, 0.4);
    label(23.556, 37.986, '萨拉米斯海峡', { a: a1, size: 46, pt: false, sub: 'Salamis' });
    label(...PL.athens, '雅典 →', { a: a1, dx: -300, dy: 0, size: 36, pt: false });
    label(23.50, 37.94, '萨拉米斯岛', { a: a1, size: 40, pt: false });
    if (a1 > 0) { const [x0, y0] = P(23.541, 37.976), [x1, y1] = P(23.557, 37.976); ctx.save(); ctx.globalAlpha = a1; ctx.strokeStyle = C.gold; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.moveTo(x0, y0 - 16); ctx.lineTo(x0, y0 + 16); ctx.moveTo(x1, y1 - 16); ctx.lineTo(x1, y1 + 16); ctx.stroke(); ctx.restore(); txt('最窄处约1.6公里', (x0 + x1) / 2, y0 - 44, { size: 32, w: 700, color: C.gold, a: a1, stroke: 5 }); txt('（据Strauss；示意）', (x0 + x1) / 2, y0 + 40, { size: 24, w: 400, color: C.gold, a: a1, stroke: 4 }); }
    // opening title
    const a0 = fade(t, -1, A('place') + 0.2, 0.01, 0.6);
    txt('萨拉米斯', W / 2, 300, { size: 120, w: 900, color: '#fff1d6', a: a0, ls: 24, stroke: 8 });
    txt('公元前480年 · 九月', W / 2, 410, { size: 40, w: 600, color: C.gold, a: a0, ls: 8 });
    // xerxes overlay
    const ax = fade(t, tx - 0.2, txo + 0.6, 0.6, 0.6);
    if (ax > 0) { dimAll(0.35 * ax); xerxesSil(W / 2 + 40, 1240, 1.05, ax, ease(seg(t, tx + 2.5, tx + 3.5)), t); label(...PL.xerxes, '', { a: 0 }); txt('薛西斯观战（剪影示意）', W / 2, 1060, { size: 30, w: 500, color: C.gold, a: ax, stroke: 4 }); }
    if (t > txo - 0.3) { const ao = ease(seg(t, txo - 0.3, txo + 0.5)); grade('black', ao * 0.0); }
  }
  if (t >= tq - 0.4 && t < tx) {
    // number card
    const a = fade(t, tq - 0.3, tx + 0.1, 0.5, 0.4);
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = '#05080c'; ctx.fillRect(0, 0, W, H); ctx.restore();
    const p1 = ease(seg(t, tq + 0.4, tq + 3.5)), p2 = ease(seg(t, tq + 3.8, tq + 5.8));
    txt('古书里的数字', W / 2, 330, { size: 40, w: 600, color: C.gold, a, ls: 6 });
    const dotsN = (n, x0, y0, cols, col, p) => { ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = col; ctx.shadowColor = col; ctx.shadowBlur = 6; const m = Math.floor(n * p); for (let i = 0; i < m; i++) { ctx.fillRect(x0 + (i % cols) * 13, y0 + Math.floor(i / cols) * 13, 9, 9); } ctx.restore(); };
    dotsN(1207, 90, 470, 34, C.pe, p1); txt(String(Math.round(1207 * p1)), 310, 430, { size: 64, w: 900, color: C.peHi, a, stroke: 5 }); txt('波斯舰队', 310, 1010, { size: 40, w: 700, color: C.peHi, a });
    dotsN(378, 620, 470, 28, C.gr, p2); txt(String(Math.round(378 * p2)), 800, 430, { size: 64, w: 900, color: C.grHi, a, stroke: 5 }); txt('希腊联军', 800, 1010, { size: 40, w: 700, color: C.grHi, a });
    txt('希罗多德《历史》7.89、8.48', W / 2, 1080, { size: 28, w: 500, color: C.goldDim, a });
    const a2 = fade(t, A('numbers2'), tx + 0.1, 0.6, 0.3);
    panel(90, 1130, W - 180, 210, a2);
    txt('今天学者的估计：波斯约600–800艘', W / 2, 1185, { size: 38, w: 700, color: C.peHi, a: a2 });
    txt('埃斯库罗斯《波斯人》另说：1000（+207快船）对310', W / 2, 1245, { size: 30, w: 500, color: '#d8d0bf', a: a2 });
    txt('数字不一，但「船多」这一点没有争议', W / 2, 1295, { size: 30, w: 500, color: '#d8d0bf', a: a2 });
    mapOn = 0;
  }
  if (t >= txo - 0.2 && t < ttw + 0.3) {
    // zoom out: retreat arrow to Asia
    const p = eio(seg(t, txo, Z('xerxes_out') - 0.5));
    const a = ease(seg(t, txo - 0.2, txo + 0.6));
    setCam(camMix([23.58, 37.96, 12000], [25.4, 39.0, 150], Math.pow(p, 0.5))); ctx.save(); ctx.globalAlpha = a; drawMap(); ctx.restore(); grade('dim', 0.25);
    arrow([PL.athens, [24.6, 38.6], [25.8, 39.6], PL.abydos, [27.2, 39.4], PL.sardis], ease(seg(t, txo + 1.0, Z('xerxes_out') + 0.3)), { color: C.pe, hi: C.peHi, w: 40, a });
    label(...PL.sardis, '撤回亚洲', { a: a * ease(seg(t, Z('xerxes_out') - 1, Z('xerxes_out'))), dy: -40, color: C.peHi });
  }
  if (t >= ttw - 0.2 && t < tqr + 0.2) { ctx.fillStyle = '#030507'; ctx.fillRect(0, 0, W, H); const a = fade(t, ttw - 0.1, tqr + 0.2, 0.3, 0.3); bigText(['这一仗', '本来不该在这里打'], 760, a, { size: 84 }); mapOn = 0; }
  if (t >= tqr - 0.2 && t < tlt + 0.3) {
    const a = ease(seg(t, tqr - 0.2, tqr + 0.3));
    setCam(camKeys(t, [[tqr, [23.25, 37.86, 1100]], [Z('quarrel'), [23.22, 37.86, 1050]]])); ctx.save(); ctx.globalAlpha = a; drawMap(); ctx.restore();
    fleetBlob(23.53, 37.955, 26, C.gr, a, t, 0.02, 16, 5);
    for (let i = 0; i < 3; i++) arrow([[23.50, 37.94], [23.3, 37.90 - i * 0.02], [23.05, 37.92 - i * 0.01]], ease(seg(t, tqr + 0.3 + i * 0.4, Z('quarrel'))), { color: C.gr, hi: C.grHi, w: 22, dash: true, a: a * 0.9 });
    label(...PL.isthmus, '科林斯地峡', { a, dy: 50 }); txt('撤？还是打？', W / 2, 560, { size: 64, w: 900, color: '#fff1d6', a, stroke: 6 });
  }
  if (t >= tlt - 0.2 && t < tq3 + 0.3) {
    const a = ease(seg(t, tlt - 0.2, tlt + 0.4));
    setCam([23.60, 37.93, 3200]); ctx.save(); ctx.globalAlpha = a; drawMap(); ctx.restore(); grade('night', a);
    const p = seg(t, tlt, Z('letter')); const [x0, y0] = P(23.53, 37.95), [x1, y1] = P(23.68, 37.93); const x = lerp(x0, x1, p), y = lerp(y0, y1, p) + Math.sin(t * 2) * 3;
    ctx.save(); ctx.globalAlpha = a; ctx.setLineDash([6, 10]); ctx.strokeStyle = 'rgba(255,230,180,0.6)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x, y); ctx.stroke(); ctx.restore();
    ship(x, y, Math.atan2(y1 - y0, x1 - x0), 26, '#d8c39a', { a }); ctx.save(); ctx.globalCompositeOperation = 'lighter'; const g = ctx.createRadialGradient(x, y, 0, x, y, 50); g.addColorStop(0, `rgba(255,200,120,${0.7 * a})`); g.addColorStop(1, 'rgba(255,200,120,0)'); ctx.fillStyle = g; ctx.fillRect(x - 50, y - 50, 100, 100); ctx.restore();
    fleetBlob(...PL.phaleron, 30, C.pe, a, t, 0.012, 12, 9);
    txt('假情报', W / 2, 520, { size: 110, w: 900, color: '#ffd9a0', a: a * ease(seg(t, tlt + 0.5, tlt + 1.2)), stroke: 8, ls: 20 });
    txt('写信人：雅典将军 地米斯托克利', W / 2, 650, { size: 40, w: 700, color: C.bone, a: a * ease(seg(t, tlt + 3, tlt + 3.8)), stroke: 5 });
    txt('Themistocles', W / 2, 705, { size: 30, w: 400, fam: GRK, it: true, color: C.gold, a: a * ease(seg(t, tlt + 3, tlt + 3.8)) });
  }
  if (t >= tq3 - 0.2) {
    ctx.fillStyle = '#04070a'; ctx.fillRect(0, 0, W, H); mapOn = 0; const a = ease(seg(t, tq3 - 0.2, tq3 + 0.3));
    setCam([23.565, 37.958, 9000]); ctx.save(); ctx.globalAlpha = 0.35 * a; drawMap(); ctx.restore(); grade('dawn', 0.4 * a);
    txt('三个问题', W / 2, 420, { size: 54, w: 700, color: C.gold, a, ls: 12 });
    const qs = [['①', '希腊人为什么留下？'], ['②', '波斯人为什么跟进来？'], ['③', '船多，为什么成了负担？']];
    const tb = A('q3b'), dd = (Z('q3b') - tb) / 3;
    qs.forEach((q, i) => { const ai = a * ease(seg(t, tb + i * dd - 0.2, tb + i * dd + 0.4)); const xo = (1 - eout(seg(t, tb + i * dd - 0.2, tb + i * dd + 0.5))) * 80; txt(q[0], 170 + xo, 620 + i * 180, { size: 72, w: 900, color: i === 2 ? C.peHi : C.grHi, a: ai }); txt(q[1], 250 + xo, 620 + i * 180, { size: 60, w: 800, color: '#fff3dc', a: ai, align: 'left', stroke: 5 }); });
  }
  return mapOn;
};

/* ---------- s1: Athens lost ---------- */
SCN.s1 = (t) => {
  const s = SC.s1;
  const k = camKeys(t, [[s.t0, [25.2, 39.3, 150]], [A('route'), [24.9, 39.2, 160]], [Z('route_fleet'), [24.4, 39.0, 165]], [A('thermo'), [23.8, 39.1, 200]], [A('open_road'), [23.6, 38.7, 230]], [A('evac') + 0.5, [23.42, 37.72, 900]], [Z('evac'), [23.45, 37.74, 950]], [A('burn'), [23.58, 37.88, 1500]], [Z('burn_dist'), [23.60, 37.92, 1700]]]);
  setCam(k); drawMap(); grade('dim', 0.15);
  const ar = (p, path, o = {}) => arrow(path, p, { color: C.pe, hi: C.peHi, w: 36, ...o });
  const aMap = 1 - ease(seg(t, A('evac') - 0.2, A('evac') + 0.6));
  // army route
  ar(ease(seg(t, A('route'), Z('route'))), [PL.sardis, [27.3, 39.6], PL.abydos, [25.8, 40.8], PL.doriskos, [24.6, 40.9], [23.6, 40.85], PL.therma, [22.6, 40.0], PL.thermo], { a: aMap });
  ar(ease(seg(t, A('route_fleet'), Z('route_fleet'))), [PL.doriskos, [25.0, 40.6], PL.athos, [23.4, 40.1], [23.3, 39.6], PL.artem], { dash: true, w: 30, a: aMap });
  label(...PL.sardis, '萨迪斯', { a: aMap * ease(seg(t, A('route'), A('route') + 0.8)), dy: 40 });
  label(...PL.abydos, '赫勒斯滂', { a: aMap * ease(seg(t, A('route') + 1, A('route') + 1.8)), dy: 44, sub: 'Hellespont' });
  const asup = fade(t, A('route_fleet'), Z('route_fleet') + 0.6);
  if (asup > 0) { panel(150, 1110, 780, 200, asup); txt('陆军沿岸走，舰队贴岸跟', W / 2, 1170, { size: 40, w: 700, a: asup, color: C.bone }); txt('大军的口粮，很大一部分靠船运', W / 2, 1240, { size: 36, w: 500, a: asup, color: C.peHi }); }
  const at = ease(seg(t, A('thermo'), A('thermo') + 0.6)) * aMap;
  label(...PL.thermo, '温泉关', { a: at, dx: -20, dy: -46, sub: 'Thermopylae · 前480年8–9月', color: '#ffd0a0' }); if (at > 0) cross(...P(...PL.thermo), 26, at * ease(seg(t, A('thermo') + 1, A('thermo') + 1.6)));
  const aa = ease(seg(t, A('artemisium'), A('artemisium') + 0.6)) * aMap;
  label(...PL.artem, '阿尔忒弥西昂', { a: aa, dx: 40, dy: -40, align: 'left', sub: 'Artemisium' });
  if (aa > 0) sparks(...P(...PL.artem), t, Math.floor(t * 1.5) / 1.5, aa, 5, 1.2);
  arrow([PL.artem, [23.9, 38.6], [24.2, 38.1], [23.7, 37.75], [23.5, 37.9]], ease(seg(t, A('artemisium') + 1.5, Z('artemisium'))), { color: C.gr, hi: C.grHi, w: 30, a: aMap });
  ar(ease(seg(t, A('open_road'), Z('open_road') + 0.4)), [PL.thermo, [23.0, 38.45], PL.athens], { a: aMap, w: 44 });
  label(...PL.athens, '雅典', { a: aMap * ease(seg(t, A('open_road'), A('open_road') + 0.5)), dy: 44, color: '#ffd0a0' });
  // evacuation on saronic map
  const ae = ease(seg(t, A('evac') + 0.2, A('evac') + 1));
  if (ae > 0) {
    label(...PL.athens, '雅典', { a: ae, dy: -40 }); label(...PL.salamis, '萨拉米斯', { a: ae, dy: 60 }); label(...PL.aegina, '埃吉那', { a: ae, dy: 50 }); label(...PL.troezen, '特罗曾', { a: ae, dy: 50 });
    const ee = A('evac') + 1.5, ez = Z('evac');
    arrow([PL.athens, [23.6, 37.9], [23.5, 37.91]], ease(seg(t, ee, ee + 2)), { color: C.gr, hi: C.grHi, w: 22, a: ae });
    arrow([PL.athens, [23.62, 37.82], [23.52, 37.75]], ease(seg(t, ee + 0.6, ee + 2.6)), { color: C.gr, hi: C.grHi, w: 22, a: ae });
    arrow([PL.athens, [23.62, 37.72], [23.45, 37.55], [23.38, 37.52]], ease(seg(t, ee + 1.2, ee + 3.4)), { color: C.gr, hi: C.grHi, w: 22, a: ae });
    const ap = fade(t, ee + 3, ez + 0.5); if (ap > 0) { panel(140, 1100, 800, 220, ap); txt('老人、妇女、孩子 → 岛上', W / 2, 1165, { size: 40, w: 700, a: ap }); txt('能打仗的男人 → 全部上船', W / 2, 1245, { size: 40, w: 700, a: ap, color: C.grHi }); }
  }
  const ab = ease(seg(t, A('burn'), A('burn') + 1.0));
  if (ab > 0) { const [x, y] = P(...PL.athens); fire(x, y, t, 1.4, ab, 3); fire(x + 18, y + 6, t + 3, 1.0, ab, 7); txt('卫城被焚', x - 40, y + 80, { size: 40, w: 800, color: '#ffb070', a: ab, stroke: 5 }); }
  const ad = ease(seg(t, A('burn_dist'), A('burn_dist') + 0.6));
  if (ad > 0) { const [x0, y0] = P(23.535, 37.955), [x1, y1] = P(...PL.athens); const p = ease(seg(t, A('burn_dist'), A('burn_dist') + 1.5)); ctx.save(); ctx.globalAlpha = ad; ctx.setLineDash([14, 10]); ctx.strokeStyle = C.gold; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(lerp(x0, x1, p), lerp(y0, y1, p)); ctx.stroke(); ctx.restore(); txt('不到20公里', (x0 + x1) / 2, (y0 + y1) / 2 - 50, { size: 46, w: 800, color: C.gold, a: ad, stroke: 6 }); }
  return 1;
};

/* ---------- s2: who has an exit ---------- */
SCN.s2 = (t) => {
  const s = SC.s2;
  let mapOn = 1;
  const k = camKeys(t, [[s.t0, CAM.saronic], [A('isthmus'), [23.20, 37.84, 1000]], [Z('wall'), [23.17, 37.84, 1000]], [A('athens_noexit'), [23.45, 37.85, 1050]], [A('table') - 0.5, [23.3, 37.6, 600]], [A('mnesiphilus'), [23.0, 37.55, 420]], [A('argument'), [23.0, 37.55, 420]],
  [A('threat0'), [23.2, 38.0, 300]], [A('threat') + 1, [19.6, 38.7, 118]], [Z('threat') + 0.5, [19.6, 38.7, 118]], [A('share'), [21.0, 38.3, 160]], [A('bypass'), [23.0, 37.6, 380]], [A('stay'), [23.30, 37.85, 950]], [s.t1, [23.32, 37.85, 1000]]]);
  setCam(k); drawMap(); grade('dim', 0.18);
  // Greek fleet at Salamis throughout
  const fleetA = 1 - ease(seg(t, A('threat0'), A('threat0') + 1)) * 0.5;
  fleetBlob(23.535, 37.955, 30, C.gr, fleetA, t, 0.018, 16, 5);
  const a0 = fade(t, s.t0 + 1.5, A('isthmus') + 0.2);
  if (a0 > 0) { panel(120, 1090, 840, 220, a0); txt('希腊联军 · 约370艘', W / 2, 1155, { size: 44, w: 800, a: a0, color: C.grHi }); txt('总指挥：斯巴达人 欧律比亚德', W / 2, 1235, { size: 38, w: 600, a: a0 }); }
  label(...PL.salamis, '萨拉米斯', { a: ease(seg(t, s.t0, s.t0 + 1)) * (1 - ease(seg(t, A('table') - 0.5, A('table')))), dy: 70 });
  // isthmus + wall
  const ai = ease(seg(t, A('isthmus'), A('isthmus') + 0.6)) * (1 - ease(seg(t, A('table') - 0.6, A('table'))));
  label(...PL.isthmus, '科林斯地峡', { a: ai, dy: -60, sub: 'Isthmus' });
  arrow([[23.50, 37.94], [23.25, 37.86], [23.05, 37.89]], ease(seg(t, A('isthmus') + 0.5, Z('isthmus'))), { color: C.gr, hi: C.grHi, w: 26, dash: true, a: ai });
  wall(22.965, 37.95, 23.015, 37.895, ease(seg(t, A('wall') + 1.5, A('wall') + 4)), ai);
  const aw = fade(t, A('wall') + 1, Z('wall') + 0.4); if (aw > 0) { txt('地峡墙 · 最窄处约6公里', W / 2, 1180, { size: 40, w: 700, color: '#f0dcae', a: aw, stroke: 5 }); txt('打输了，还能上岸回家', W / 2, 1250, { size: 36, w: 500, color: C.bone, a: aw, stroke: 5 }); }
  const an = ease(seg(t, A('athens_noexit'), A('athens_noexit') + 0.6)) * (1 - ease(seg(t, A('table') - 0.6, A('table'))));
  if (an > 0) { const [x, y] = P(...PL.athens); fire(x, y, t, 0.8, an * 0.7, 3); cross(x, y, 24, an); label(...PL.athens, '雅典：城已失', { a: an, dy: -56, pt: false, color: '#ffb070' }); label(...PL.aegina, '埃吉那 · 妇孺', { a: an, dy: 50 }); label(23.47, 37.92, '萨拉米斯 · 妇孺', { a: an, dy: 80, pt: false });
    arrow([[23.95, 37.95], [23.80, 37.88], [23.60, 37.90]], ease(seg(t, A('athens_noexit') + 3, Z('athens_noexit'))), { color: C.pe, hi: C.peHi, w: 30, a: an }); }
  // exit-options panel
  const at = fade(t, A('table') - 0.3, Z('table2') + 0.3, 0.5, 0.5);
  if (at > 0) {
    dimAll(0.55 * at);
    txt('同一张桌子，不同的退路', W / 2, 470, { size: 54, w: 800, color: C.gold, a: at, stroke: 5 });
    const rows = [['科林斯', '地峡后方 · 家在', 1], ['斯巴达', '伯罗奔尼撒 · 家在', 1], ['麦加拉等', '各有各的盘算', 1], ['雅典', '城已焚 · 家人在岛上', 0]];
    rows.forEach((r, i) => { const ai = at * ease(seg(t, A('table') + 0.3 + i * 0.5, A('table') + 0.9 + i * 0.5)); const y = 640 + i * 130; txt(r[0], 140, y, { size: 46, w: 800, align: 'left', a: ai, color: r[2] ? C.bone : C.grHi }); txt(r[1], 560, y, { size: 36, w: 500, align: 'left', a: ai, color: '#d8d0bf' }); r[2] ? tick(500, y, 22, ai) : cross(500, y, 20, ai); });
    const a2 = at * ease(seg(t, A('table2'), A('table2') + 0.6)); txt('退路不同，想法就不同', W / 2, 1220, { size: 62, w: 900, color: '#fff1d6', a: a2, stroke: 6 });
  }
  // scatter arrows (Mnesiphilus)
  const am = fade(t, A('mnesiphilus') - 0.2, A('argument') + 0.2);
  if (am > 0) { const homes = [PL.corinth, PL.megara, PL.aegina, PL.troezen, [22.6, 37.3]]; homes.forEach((h, i) => arrow([[23.50, 37.93], [lerp(23.5, h[0], 0.5), lerp(37.93, h[1], 0.5) + 0.05], h], ease(seg(t, A('mnesiphilus') + 0.5 + i * 0.3, A('mnesiphilus') + 2.5 + i * 0.3)), { color: C.gr, hi: C.grHi, w: 18, a: am * 0.9, dash: true })); }
  // narrows vs open sea diagram
  const ag = fade(t, A('argument') - 0.2, Z('argument_q') + 0.4, 0.5, 0.5);
  if (ag > 0) { dimAll(0.75 * ag); diagramOpenVsNarrow(t, ag, A('argument'), Z('argument_q')); mapOn = 0; }
  // corinth / ships_city
  const ac = fade(t, A('corinth') - 0.2, Z('ships_city') + 0.4, 0.4, 0.5);
  if (ac > 0) {
    dimAll(0.75 * ac); mapOn = 0;
    const a1 = ac * ease(seg(t, A('corinth'), A('corinth') + 0.5)); txt('科林斯将领 阿得曼托斯', W / 2, 430, { size: 38, w: 600, color: C.grey, a: a1 }); txt('「无城之人，无权表决。」', W / 2, 520, { size: 58, w: 800, color: '#e8e0cc', a: a1, stroke: 5 });
    const a2 = ac * ease(seg(t, A('ships_city'), A('ships_city') + 0.5)); txt('地米斯托克利', W / 2, 650, { size: 38, w: 600, color: C.gold, a: a2 });
    shipGrid(200, 160, 740, 20, 38, 34, 26, a2, seg(t, A('ships_city') + 0.6, A('ships_city') + 4));
    txt('200艘坐满人的战船，就是一座城', W / 2, 1150, { size: 48, w: 800, color: C.grHi, a: a2 * ease(seg(t, A('ships_city') + 3.5, A('ships_city') + 4.2)), stroke: 5 });
    txt('希罗多德《历史》8.61', W / 2, 1220, { size: 28, w: 500, color: C.goldDim, a: a2 });
  }
  // threat: Italy
  const ath = fade(t, A('threat0'), Z('threat') + 0.6);
  arrow([[23.45, 37.9], [22.0, 37.3], [20.0, 37.6], [18.0, 39.0], PL.siris], ease(seg(t, A('threat0') + 0.5, A('threat') + 2.5)), { color: C.gr, hi: C.grHi, w: 40, a: ath });
  if (ath > 0) { label(...PL.siris, '意大利 · 西里斯', { a: ath * ease(seg(t, A('threat') + 1.5, A('threat') + 2.5)), dy: -50, sub: 'Siris' }); }
  // share
  const as = fade(t, A('share') - 0.2, Z('share') + 0.5);
  if (as > 0) { dimAll(0.7 * as); mapOn = 0; const p = ease(seg(t, A('share') + 0.5, A('share') + 3)); const cx = W / 2, cy = 820, R = 260;
    ctx.save(); ctx.globalAlpha = as; ctx.lineWidth = 90; ctx.strokeStyle = 'rgba(200,190,170,0.25)'; ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.stroke(); ctx.strokeStyle = C.gr; ctx.shadowColor = C.gr; ctx.shadowBlur = 20; ctx.beginPath(); ctx.arc(cx, cy, R, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * (180 / 378) * p); ctx.stroke(); ctx.restore();
    txt(String(Math.round(180 * p)), cx, cy - 20, { size: 110, w: 900, color: C.grHi, a: as }); txt('雅典战船 / 378', cx, cy + 70, { size: 36, w: 600, color: C.bone, a: as }); txt('将近一半', cx, 1210, { size: 64, w: 900, color: '#fff1d6', a: as * ease(seg(t, A('share') + 3, A('share') + 3.6)), stroke: 6 }); txt('希罗多德《历史》8.44、8.48', cx, 1280, { size: 28, w: 500, color: C.goldDim, a: as }); }
  // bypass
  const abp = fade(t, A('bypass') - 0.2, Z('bypass_q') + 0.4);
  if (abp > 0) { wall(22.965, 37.95, 23.015, 37.895, 1, abp); label(...PL.isthmus, '地峡墙', { a: abp, dy: -50 });
    arrow([[23.65, 37.85], [23.55, 37.55], [23.2, 37.25], [22.9, 37.05], [22.75, 36.9]], ease(seg(t, A('bypass') + 0.5, A('bypass') + 3.5)), { color: C.pe, hi: C.peHi, w: 34, a: abp });
    arrow([[23.65, 37.85], [23.45, 37.6], [23.1, 37.55], [22.85, 37.70]], ease(seg(t, A('bypass') + 1, A('bypass') + 4)), { color: C.pe, hi: C.peHi, w: 28, a: abp, dash: true });
    const [wx, wy] = P(22.99, 37.92); cross(wx, wy, 30, abp * ease(seg(t, A('bypass') + 3.5, A('bypass') + 4.2))); }
  const ast = fade(t, A('stay'), A('plutarch'), 0.6, 0.3);
  if (ast > 0) { txt('留在萨拉米斯', W / 2, 1180, { size: 66, w: 900, color: C.grHi, a: ast * ease(seg(t, A('stay') + 3.5, A('stay') + 4.2)), stroke: 6, ls: 8 }); }
  const apl = fade(t, A('plutarch') - 0.2, Z('plutarch2') + 0.4);
  if (apl > 0) { dimAll(0.6 * apl); stamp('传说', W / 2, 1120, apl * ease(seg(t, A('plutarch2'), A('plutarch2') + 0.5))); txt('普鲁塔克，约公元100年前后成书', W / 2, 1250, { size: 32, w: 500, color: C.grey, a: apl * ease(seg(t, A('plutarch2'), A('plutarch2') + 0.5)) }); }
  return mapOn;
};
function diagramOpenVsNarrow(t, a, t0, t1) {
  const p = ease(seg(t, t0 + 0.5, t0 + 4)), q = ease(seg(t, t0 + 2.5, t0 + 6));
  // left: open sea
  const pane = (x0, title, narrow) => {
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = 'rgba(16,40,56,0.9)'; ctx.fillRect(x0, 420, 440, 640); if (narrow) { ctx.fillStyle = '#4b3f2e'; ctx.fillRect(x0, 420, 120, 640); ctx.fillRect(x0 + 320, 420, 120, 640); } ctx.strokeStyle = C.goldDim; ctx.strokeRect(x0, 420, 440, 640); ctx.restore();
    txt(title, x0 + 220, 380, { size: 42, w: 800, color: narrow ? C.grHi : C.peHi, a });
    // greek line (few)
    for (let i = 0; i < 5; i++) ship(x0 + 220 + (i - 2) * 34, 540, Math.PI / 2, 26, C.gr, { a, glow: 6 });
    // persian mass
    for (let r = 0; r < 6; r++) for (let i = 0; i < 9; i++) {
      let x = x0 + 220 + (i - 4) * 40, y = 880 + r * 34; const pp = narrow ? q : p;
      if (narrow) { x = x0 + 220 + clamp((i - 4) * 40, -70, 70) * 1 + (Math.abs(i - 4) > 2 ? (hash(i + r * 9) - 0.5) * 10 : 0); y = lerp(y + 60, 640 + r * 40 + (Math.abs(i - 4) > 2 ? 30 : 0), pp); }
      else { const side = i < 3 ? -1 : i > 5 ? 1 : 0; y = lerp(y + 60, 640 + r * 30 - (side ? 120 : 0), pp); x += side * 90 * pp; }
      ship(x, y, -Math.PI / 2 + (narrow && Math.abs(i - 4) > 2 ? (hash(i * r) - 0.5) * 0.8 * pp : 0), 26, C.pe, { a: a * (narrow && Math.abs(i - 4) > 2 ? 0.8 : 1), glow: 4 });
    }
    if (!narrow) { arrow2(x0 + 60, 820, x0 + 60, 540, a * p, C.pe); arrow2(x0 + 380, 820, x0 + 380, 540, a * p, C.pe); txt('包抄侧翼', x0 + 220, 1110, { size: 34, w: 600, color: C.peHi, a }); }
    else { txt('只能正面接敌', x0 + 220, 1110, { size: 34, w: 600, color: C.grHi, a }); }
  };
  pane(70, '开阔海面', false); pane(570, '窄海峡', true);
}
function arrow2(x0, y0, x1, y1, a, col) { if (a <= 0.01) return; const an = Math.atan2(y1 - y0, x1 - x0); ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 10; ctx.shadowColor = col; ctx.shadowBlur = 12; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1 - Math.cos(an) * 20, y1 - Math.sin(an) * 20); ctx.stroke(); ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x1 - Math.cos(an - 0.5) * 34, y1 - Math.sin(an - 0.5) * 34); ctx.lineTo(x1 - Math.cos(an + 0.5) * 34, y1 - Math.sin(an + 0.5) * 34); ctx.fill(); ctx.restore(); }

/* ---------- s3: wooden wall ---------- */
SCN.s3 = (t) => {
  const s = SC.s3;
  const aMap = 1 - ease(seg(t, A('oracle1') - 0.4, A('oracle1') + 0.2));
  if (aMap > 0) {
    setCam(camKeys(t, [[s.t0, [23.75, 37.80, 700]], [A('silver'), [23.95, 37.74, 1200]]])); drawMap(); grade('dim', 0.25);
    label(...PL.laurium, '劳里昂银矿', { a: aMap * ease(seg(t, A('silver') - 0.5, A('silver') + 0.3)), dy: -50, sub: 'Laurion' });
    const ac = aMap * ease(seg(t, A('silver'), A('silver') + 0.5)) * (1 - ease(seg(t, A('silver_ships') + 0.3, A('silver_ships') + 1.5)));
    if (ac > 0) { dimAll(0.4 * ac); for (let i = 0; i < 40; i++) { const ph = (t * 0.35 + hash(i)) % 1; coin(140 + hash(i * 3) * 800, 300 + ph * 900, 34, ac * Math.sin(ph * Math.PI), t * 3 + i); } txt('每人10德拉克马？', W / 2, 1180, { size: 50, w: 800, color: '#e6e6e0', a: ac, stroke: 5 }); }
    const as = aMap * ease(seg(t, A('silver_ships') + 0.3, A('silver_ships') + 1.2));
    if (as > 0) { dimAll(0.6 * as); shipGrid(200, 160, 600, 20, 38, 34, 26, as, seg(t, A('silver_ships') + 0.5, Z('silver_ships'))); txt('→ 200艘战船', W / 2, 1100, { size: 60, w: 900, color: C.grHi, a: as, stroke: 6 }); txt('希罗多德《历史》7.144', W / 2, 1170, { size: 28, w: 500, color: C.goldDim, a: as }); }
  }
  if (t > A('oracle1') - 0.5) {
    const a = ease(seg(t, A('oracle1') - 0.4, A('oracle1') + 0.4));
    ctx.save(); ctx.globalAlpha = a; seaBg(t, 'dark'); ctx.restore();
    const ad = a * (1 - ease(seg(t, A('hedge') - 0.3, A('hedge') + 0.3)));
    if (ad > 0) { ctx.save(); ctx.globalAlpha = ad; const g = ctx.createRadialGradient(W / 2, 1000, 0, W / 2, 1000, 700); g.addColorStop(0, 'rgba(200,140,70,0.35)'); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore(); temple(W / 2, 1290, 1.25, ad); tripodSmoke(W / 2, 1120, t, ad); txt('德尔斐', W / 2, 400, { size: 60, w: 800, color: C.gold, a: ad, ls: 12 }); }
    const a1 = fade(t, A('oracle1') + 1.5, A('oracle2') + 0.2);
    if (a1 > 0) { txt('第一道神谕', W / 2, 560, { size: 36, w: 600, color: C.grey, a: a1 }); txt('「逃吧，逃到天涯海角。」', W / 2, 650, { size: 58, w: 800, color: '#f2e6cc', a: a1, stroke: 5 }); txt('希罗多德《历史》7.140', W / 2, 730, { size: 28, w: 500, color: C.goldDim, a: a1 }); }
    const a2 = fade(t, A('oracle2'), A('oracle_q'));
    if (a2 > 0) txt('第二道神谕', W / 2, 600, { size: 44, w: 700, color: C.gold, a: a2 });
    // hedge -> ships
    const ah = ease(seg(t, A('hedge') - 0.3, A('hedge') + 0.4)) * (1 - ease(seg(t, A('divine') - 0.3, A('divine') + 0.3)));
    if (ah > 0) {
      const m = ease(seg(t, A('ships') + 0.3, A('ships') + 2.3));
      // acropolis hill
      ctx.save(); ctx.globalAlpha = ah * (1 - m); ctx.fillStyle = '#2a2622'; ctx.beginPath(); ctx.moveTo(140, 1150); ctx.quadraticCurveTo(300, 860, 540, 850); ctx.quadraticCurveTo(780, 860, 940, 1150); ctx.fill(); temple(W / 2, 845, 0.35, ah * (1 - m)); ctx.restore();
      for (let i = 0; i < 26; i++) { const f = i / 25; const hx = lerp(150, 930, f), hy = 1150 - Math.sin(f * Math.PI) * 220; const sx = 150 + f * 780, sy = 1100; const x = lerp(hx, sx, m), y = lerp(hy, sy, m);
        if (m < 0.5) { ctx.save(); ctx.globalAlpha = ah * (1 - m * 2); ctx.strokeStyle = '#7d6a44'; ctx.lineWidth = 3; for (let j = 0; j < 5; j++) { const an = hash(i * 5 + j) * Math.PI * 2; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + Math.cos(an) * 22, y + Math.sin(an) * 22); ctx.stroke(); } ctx.restore(); }
        else if (i % 2 === 0) triremeSide(x, y + (i % 4 ? 0 : 60), 160, t, { a: ah * (m * 2 - 1), oars: true }); }
      txt(m < 0.5 ? '木墙 = 卫城的荆棘篱笆？' : '木墙 = 船', W / 2, 620, { size: 64, w: 900, color: m < 0.5 ? '#d8d0bf' : C.grHi, a: ah * (m < 0.5 ? 1 - m * 2 : m * 2 - 1), stroke: 6 });
      txt('希罗多德《历史》7.142–143', W / 2, 700, { size: 28, w: 500, color: C.goldDim, a: ah });
    }
    const av = fade(t, A('divine') - 0.2, Z('divine') + 0.4);
    if (av > 0) { txt('「残酷的萨拉米斯」', W / 2, 640, { size: 62, w: 800, color: '#9a948a', a: av }); cross(W / 2 + 300, 640, 26, av * ease(seg(t, A('divine') + 1, A('divine') + 1.6))); txt('「神圣的萨拉米斯」', W / 2, 820, { size: 62, w: 800, color: C.gold, a: av * ease(seg(t, A('divine') + 2.5, A('divine') + 3.2)), stroke: 5 }); txt('→ 要死的是敌人', W / 2, 940, { size: 48, w: 700, color: C.grHi, a: av * ease(seg(t, A('divine') + 5, A('divine') + 5.6)) }); }
    const ai = fade(t, A('interp') - 0.2, s.t1 + 0.4);
    if (ai > 0) { txt('神谕一个字没改', W / 2, 620, { size: 60, w: 800, color: '#d8d0bf', a: ai }); txt('变的，是谁来解释它', W / 2, 740, { size: 60, w: 800, color: '#d8d0bf', a: ai * ease(seg(t, A('interp') + 1.6, A('interp') + 2.2)) });
      const a3 = ai * ease(seg(t, A('interp2') + 1.0, A('interp2') + 1.8)); txt('解释权 = 决策权', W / 2, 940, { size: 92, w: 900, color: C.gold, a: a3, stroke: 7, ls: 6 }); }
  }
  return 1 - ease(seg(t, A('oracle1') - 0.4, A('oracle1')));
};

/* ---------- s4: the false message ---------- */
SCN.s4 = (t) => {
  const s = SC.s4; let mapOn = 1;
  const k = camKeys(t, [[s.t0, [23.45, 37.88, 1000]], [A('boat'), [23.60, 37.93, 3000]], [Z('message'), [23.60, 37.93, 3000]], [A('scatter'), [23.1, 37.7, 330]], [A('blockade'), [23.45, 37.88, 1000]], [Z('blockade'), [23.48, 37.88, 1000]], [A('psyttaleia'), CAM.psy], [A('night_rowers'), [23.575, 37.948, 12000]],
  [A('aristides'), [23.48, 37.85, 1000]], [A('tenos'), [23.57, 37.952, 9000]], [A('sealed'), [23.50, 37.92, 1600]], [s.t1, [23.52, 37.93, 1800]]]);
  setCam(k); drawMap(); grade('night', 1);
  const fl = fade(t, s.t0, A('boat') + 0.5);
  fleetBlob(23.535, 37.955, 30, C.gr, 1, t, 0.018 * Math.min(1, 1000 / cam.ppd * 1.0), 14, 5);
  if (cam.ppd < 4000) fleetBlob(...PL.phaleron, 40, C.pe, fl + (1 - fl) * (t < A('blockade') ? 1 : 0), t, 0.02 * 1000 / cam.ppd * 1.0, 14, 9);
  const ap = ease(seg(t, A('phaleron'), A('phaleron') + 0.5)) * (1 - ease(seg(t, A('boat') - 0.5, A('boat'))));
  label(...PL.phaleron, '法勒隆湾', { a: ap, dy: 60, sub: 'Phaleron' });
  arrow([PL.athens, [23.45, 38.02], [23.15, 37.98], [23.02, 37.93]], ease(seg(t, A('phaleron') + 1, A('phaleron') + 4)), { color: C.pe, hi: C.peHi, w: 30, a: ap });
  const sn = fade(t, A('sicinnus0'), A('boat') + 0.2);
  if (sn > 0) { dimAll(0.6 * sn); mapOn = 0; ctx.save(); ctx.globalAlpha = sn; const g = ctx.createRadialGradient(W / 2, 900, 0, W / 2, 900, 380); g.addColorStop(0, 'rgba(255,190,110,0.45)'); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore();
    // silhouette of a man with a lamp
    ctx.save(); ctx.globalAlpha = sn; ctx.fillStyle = '#06070a'; ctx.beginPath(); ctx.arc(W / 2, 760, 46, 0, Math.PI * 2); ctx.fill(); ctx.beginPath(); ctx.moveTo(W / 2 - 80, 1220); ctx.lineTo(W / 2 - 60, 830); ctx.quadraticCurveTo(W / 2, 800, W / 2 + 60, 830); ctx.lineTo(W / 2 + 80, 1220); ctx.fill(); ctx.restore();
    const a2 = sn * ease(seg(t, A('sicinnus'), A('sicinnus') + 0.6)); txt('西金诺斯', W / 2, 470, { size: 72, w: 900, color: '#ffe0b0', a: a2, stroke: 6, ls: 10 }); txt('Sicinnus · 家仆、孩子们的教师', W / 2, 560, { size: 34, w: 500, color: C.gold, a: a2 }); txt('（剪影示意）', W / 2, 1280, { size: 26, w: 400, color: C.grey, a: a2 }); }
  // boat crossing
  const ab = fade(t, A('boat') - 0.2, Z('message') + 0.5);
  if (ab > 0) { const p = ease(seg(t, A('boat'), A('message') + 4)); const [x0, y0] = P(23.54, 37.952), [x1, y1] = P(23.675, 37.935); const x = lerp(x0, x1, p), y = lerp(y0, y1, p) + Math.sin(t * 2) * 3;
    ctx.save(); ctx.globalAlpha = ab; ctx.setLineDash([6, 10]); ctx.strokeStyle = 'rgba(255,230,180,0.7)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x, y); ctx.stroke(); ctx.restore();
    ship(x, y, Math.atan2(y1 - y0, x1 - x0), 30, '#d8c39a', { a: ab }); ctx.save(); ctx.globalCompositeOperation = 'lighter'; const g = ctx.createRadialGradient(x, y, 0, x, y, 60); g.addColorStop(0, `rgba(255,200,120,${0.8 * ab})`); g.addColorStop(1, 'rgba(255,200,120,0)'); ctx.fillStyle = g; ctx.fillRect(x - 60, y - 60, 120, 120); ctx.restore();
    label(...PL.salamis, '', { a: 0 }); }
  // truth table
  const atr = fade(t, A('truth') - 0.2, Z('truth2') + 0.4);
  if (atr > 0) { dimAll(0.78 * atr); mapOn = 0; txt('这封信里，哪句是真的？', W / 2, 440, { size: 52, w: 800, color: C.gold, a: atr });
    const rows = [['希腊人在争吵', 1], ['有人打算逃跑', 1], ['他们彼此不和', 1], ['雅典将军站在国王一边', 0]];
    rows.forEach((r, i) => { const ai = atr * ease(seg(t, A('truth') + 0.4 + i * 0.5, A('truth') + 0.9 + i * 0.5)); const y = 600 + i * 120; txt(r[0], 200, y, { size: 48, w: 700, align: 'left', a: ai, color: r[1] ? C.bone : '#ffb0a0' }); r[1] ? txt('真', 860, y, { size: 52, w: 900, color: '#7fe08a', a: ai }) : txt('假', 860, y, { size: 52, w: 900, color: '#ff5a4a', a: ai }); });
    txt('最好的谎言，主体是真话', W / 2, 1180, { size: 60, w: 900, color: '#fff1d6', a: atr * ease(seg(t, A('truth2') + 2, A('truth2') + 2.6)), stroke: 6 }); }
  // scatter
  const asc = fade(t, A('scatter') - 0.2, Z('scatter2') + 0.4);
  if (asc > 0) { const ports = [PL.corinth, PL.aegina, PL.troezen, [22.75, 37.55], [23.1, 37.35], PL.megara]; ports.forEach((h, i) => { arrow([[23.5, 37.93], h], ease(seg(t, A('scatter') + 0.5 + i * 0.25, A('scatter') + 2 + i * 0.25)), { color: C.gr, hi: C.grHi, w: 16, a: asc }); arrow([PL.phaleron, [lerp(23.68, h[0], 0.5), lerp(37.93, h[1], 0.5) - 0.08], h], ease(seg(t, A('scatter') + 3 + i * 0.4, A('scatter') + 5 + i * 0.4)), { color: C.pe, hi: C.peHi, w: 14, a: asc * 0.85, dash: true }); });
    txt('一个港口一个港口地打？', W / 2, 1180, { size: 54, w: 800, color: C.peHi, a: asc * ease(seg(t, A('scatter') + 3, A('scatter') + 3.6)), stroke: 6 }); }
  // blockade
  const abk = fade(t, A('blockade') - 0.3, Z('night_rowers') + 0.4);
  if (abk > 0) { const pb = seg(t, A('blockade') + 0.5, Z('blockade'));
    arrow([PL.phaleron, [23.58, 37.88], [23.50, 37.82], [23.38, 37.83], [23.33, 37.90], [23.39, 37.96]], ease(pb * 1.2), { color: C.pe, hi: C.peHi, w: 26, dash: true, a: abk });
    const [ax, ay] = P(23.572, 37.95), [bx, by] = P(...PL.munychia); const q = ease(seg(t, A('blockade') + 2.5, Z('blockade'))); ctx.save(); ctx.globalAlpha = abk; ctx.strokeStyle = C.pe; ctx.shadowColor = C.pe; ctx.shadowBlur = 16; ctx.lineWidth = 9; ctx.setLineDash([16, 10]); ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(lerp(bx, ax, q), lerp(by, ay, q)); ctx.stroke(); ctx.restore();
    if (cam.ppd > 5000) { for (let i = 0; i < 18; i++) { const f = i / 17; const [x, y] = P(lerp(23.575, 23.645, f), lerp(37.9505, 37.9390, f) - 0.0012); ship(x, y, Math.PI * 0.9, 22, C.pe, { a: abk, oar: t * 5 + i, glow: 8 }); } }
    label(...PL.westCh, '西口', { a: abk * ease(seg(t, A('blockade') + 3, A('blockade') + 4)), color: C.peHi, dy: -40 }); label(23.62, 37.94, '东口', { a: abk * ease(seg(t, A('blockade') + 4, A('blockade') + 5)) * (cam.ppd < 5000 ? 1 : 0), color: C.peHi, dy: 50, pt: false });
    const apy = ease(seg(t, A('psyttaleia') + 0.4, A('psyttaleia') + 1.2)); if (apy > 0) { label(...PL.psy, '普西塔利亚岛', { a: apy * abk, dy: -60, sub: 'Psyttaleia' }); const [px, py] = P(...PL.psy); for (let i = 0; i < 24; i++) { ctx.save(); ctx.globalAlpha = apy * abk; ctx.fillStyle = C.peHi; ctx.fillRect(px - 60 + (i % 8) * 16, py - 10 + Math.floor(i / 8) * 16, 10, 10); ctx.restore(); } txt('波斯步兵登岛', W / 2, 1180, { size: 44, w: 800, color: C.peHi, a: apy * abk * fade(t, A('psyttaleia'), Z('psyttaleia') + 0.3), stroke: 5 }); }
    const anr = fade(t, A('night_rowers'), Z('night_rowers') + 0.4); if (anr > 0) { txt('整夜划船、待命，没有合眼', W / 2, 1180, { size: 48, w: 800, color: '#cfe0ff', a: anr, stroke: 5 }); txt('希罗多德《历史》8.76', W / 2, 1250, { size: 28, w: 500, color: C.goldDim, a: anr }); }
  }
  // Aristides
  const aar = fade(t, A('aristides') - 0.2, Z('aristides2') + 0.5);
  if (aar > 0) { label(...PL.aegina, '埃吉那', { a: aar, dy: 50 }); arrow([PL.aegina, [23.52, 37.83], [23.535, 37.93]], ease(seg(t, A('aristides') + 0.5, A('aristides') + 3.5)), { color: C.gr, hi: C.grHi, w: 22, a: aar });
    txt('阿里斯提德', W / 2, 1180, { size: 52, w: 800, color: C.grHi, a: aar * fade(t, A('aristides') + 1, A('aristides2')), stroke: 5 }); txt('地米斯托克利的老对头 · 曾遭放逐', W / 2, 1250, { size: 34, w: 500, color: C.bone, a: aar * fade(t, A('aristides') + 1, A('aristides2')), stroke: 4 }); }
  // Tenos defector
  const ate = fade(t, A('tenos') - 0.2, Z('tenos') + 0.4);
  if (ate > 0) { for (let i = 0; i < 18; i++) { const f = i / 17; const [x, y] = P(lerp(23.575, 23.645, f), lerp(37.9505, 37.9390, f) - 0.0012); ship(x, y, Math.PI * 0.9, 18, C.pe, { a: ate, glow: 6 }); }
    const p = ease(seg(t, A('tenos') + 0.5, Z('tenos'))); const [x0, y0] = P(23.585, 37.9475), [x1, y1] = P(23.548, 37.957); const x = lerp(x0, x1, p), y = lerp(y0, y1, p); ship(x, y, Math.atan2(y1 - y0, x1 - x0), 26, mixc(C.pe, C.gr, p), { a: ate, glow: 16, oar: t * 6 }); txt('特诺斯船倒戈', x, y - 50, { size: 34, w: 700, color: '#ffe0b0', a: ate, stroke: 4 }); }
  // sealed
  const ase = fade(t, A('sealed') - 0.2, A('sunzi') + 0.3);
  if (ase > 0) { const [wx, wy] = P(...PL.westCh), [ex, ey] = P(23.59, 37.945); cross(wx, wy, 34, ase, C.pe); cross(ex, ey, 34, ase, C.pe); txt('退路已断', W / 2, 1180, { size: 72, w: 900, color: '#fff1d6', a: ase * ease(seg(t, A('sealed') + 1, A('sealed') + 1.6)), stroke: 6, ls: 10 }); txt('封死它的，是敌人自己', W / 2, 1270, { size: 42, w: 700, color: C.peHi, a: ase * ease(seg(t, A('sealed') + 2.5, A('sealed') + 3.1)), stroke: 5 }); }
  const asz = fade(t, A('sunzi') - 0.2, Z('sealed2') + 0.4); if (asz > 0) { dimAll(0.6 * asz); mapOn *= 1 - asz; txt('自己下不了的决心，借敌人的手下了', W / 2, 1240, { size: 44, w: 800, color: '#fff1d6', a: asz * ease(seg(t, A('sealed2'), A('sealed2') + 0.6)), stroke: 5 }); }
  const ado = fade(t, A('doubt') - 0.2, s.t1 + 0.3); if (ado > 0) { dimAll(0.7 * ado); mapOn = 0; panel(110, 520, 400, 300, ado); panel(570, 520, 400, 300, ado); txt('希罗多德', 310, 600, { size: 46, w: 800, a: ado }); txt('《历史》8.75', 310, 670, { size: 32, w: 500, color: C.goldDim, a: ado }); txt('埃斯库罗斯', 770, 600, { size: 46, w: 800, a: ado }); txt('《波斯人》355起', 770, 670, { size: 32, w: 500, color: C.goldDim, a: ado }); txt('≠', W / 2, 680, { size: 90, w: 900, color: C.gold, a: ado }); stamp('存疑', W / 2, 1010, ado * ease(seg(t, A('doubt') + 3, A('doubt') + 3.6)), -0.1, '#e0a03a'); }
  return mapOn;
};

/* ---------- s5: the squeeze ---------- */
SCN.s5 = (t) => {
  const s = SC.s5; let mapOn = 1;
  const k = camKeys(t, [[s.t0, [23.565, 37.957, 7600]], [A('deploy'), CAM.strait], [A('wings') + 3, [23.560, 37.956, 12000]], [A('front'), [23.562, 37.955, 11500]], [A('wave0'), [23.566, 37.953, 12500]], [Z('wave2'), [23.568, 37.951, 14000]], [A('broadside'), CAM.straitClose], [A('command'), [23.57, 37.96, 9000]],
  [A('nobody_turns'), [23.568, 37.957, 10500]], [A('hdt889'), [23.566, 37.953, 13000]], [A('artemisia'), [23.565, 37.955, 15000]], [A('swim'), [23.56, 37.955, 13000]], [A('psy_kill'), CAM.psy], [A('aftermath'), [23.565, 37.955, 10500]], [s.t1, [23.565, 37.955, 9800]]]);
  setCam(k); drawMap();
  const dawn = 1 - 0.6 * ease(seg(t, A('aftermath') - 1, s.t1)); grade('dawn', dawn); if (t > A('aftermath') - 1) grade('dim', 0.3 * ease(seg(t, A('aftermath') - 1, s.t1)));
  // sim time mapping
  const sg = t < A('deploy') ? 40 : t < A('wave0') ? lerp(40, 205, seg(t, A('deploy'), A('wave0'))) : t < A('command') ? lerp(205, 282, seg(t, A('wave0'), A('command'))) : t < A('hdt889') ? 282 : lerp(282, 345, seg(t, A('hdt889'), A('push') + 3));
  const L = clamp(cam.ppd / 11000 * 21, 16, 34);
  const strike = ease(seg(t, A('greek_strike'), A('greek_strike') + 6)) * (t < A('command') ? 1 : 1);
  drawGreeks(t, { L, form: ease(seg(t, s.t0, A('deploy') + 4)), strike });
  const st = drawPersians(t, sg, { L, waveHi: t > A('wave0') ? 1 : 0, collFx: t > A('wave2') });
  ripples(t, 0.5, 8);
  // labels
  const al = fade(t, A('deploy'), A('trireme'));
  label(23.535, 37.968, '希腊舰队', { a: al, color: C.grHi, pt: false, size: 42 }); label(23.600, 37.940, '波斯舰队', { a: al, color: C.peHi, pt: false, size: 42 });
  const aw = fade(t, A('wings'), Z('wings') + 0.6);
  label(23.535, 37.9715, '雅典', { a: aw, color: C.grHi, pt: false, size: 36, dy: 0 }); label(23.537, 37.949, '斯巴达', { a: aw, color: C.grHi, pt: false, size: 36, dy: 0 });
  label(23.566, 37.9635, '腓尼基', { a: aw, color: C.peHi, pt: false, size: 36, dy: 0 }); label(23.566, 37.9455, '伊奥尼亚', { a: aw, color: C.peHi, pt: false, size: 36, dy: 0 });
  // trireme diagram
  const atr = fade(t, A('trireme') - 0.2, Z('ram2') + 0.4);
  if (atr > 0) { dimAll(0.8 * atr); mapOn *= 1 - atr; const sv = fade(t, A('trireme') - 0.2, A('ram') + 0.3);
    if (sv > 0) { ctx.save(); ctx.globalAlpha = sv; seaBg(t, 'dawn'); ctx.restore(); triremeSide(W / 2, 900, 880, t, { a: sv });
      const lb = (s, x, y, a) => { txt(s, x, y, { size: 36, w: 700, color: '#fff1d6', a: a * sv, stroke: 5 }); };
      lb('长约37米', W / 2, 700, ease(seg(t, A('trireme') + 2, A('trireme') + 2.6))); lb('170名桨手 · 三层', W / 2 - 60, 1060, ease(seg(t, A('trireme') + 3.5, A('trireme') + 4.1))); lb('青铜撞角', W / 2 + 380, 1010, ease(seg(t, A('trireme') + 5.5, A('trireme') + 6.1)));
      txt('参考复原船 Olympias（示意）', W / 2, 1230, { size: 28, w: 400, color: C.goldDim, a: sv }); }
    const ar = fade(t, A('ram') - 0.2, Z('ram2') + 0.4);
    if (ar > 0) { ctx.save(); ctx.globalAlpha = ar; ctx.fillStyle = '#0e2a3a'; ctx.fillRect(0, 0, W, H); ctx.restore(); ripples(t, ar, 2, 80);
      const p = ease(seg(t, A('ram') + 0.5, A('ram') + 4)); const vx = W / 2 + 40, vy = 860; ship(vx, vy, 0, 220, C.pe, { a: ar, broken: p > 0.95 ? 1 : 0 });
      const ax = lerp(W / 2 - 40, vx - 10, p), ay = lerp(1380, vy + 40, p); ship(ax, ay, -Math.PI / 2 - 0.1, 220, C.gr, { a: ar, oar: t * 8 }); if (p > 0.97) sparks(vx, vy + 30, t, A('ram') + 4, ar, 9, 2.2);
      const a2 = ar * ease(seg(t, A('ram2') + 0.3, A('ram2') + 1)); txt('① 冲刺的距离', W / 2, 460, { size: 52, w: 800, color: C.grHi, a: a2, stroke: 5 }); txt('② 转向的空间', W / 2, 560, { size: 52, w: 800, color: C.grHi, a: ar * ease(seg(t, A('ram2') + 2, A('ram2') + 2.6)), stroke: 5 }); }
  }
  // open sea reminder
  const ao = fade(t, A('open_sea') - 0.2, Z('open_sea') + 0.3); if (ao > 0) { dimAll(0.75 * ao); diagramOpenVsNarrow(t, ao, A('open_sea') - 2, Z('open_sea') + 4); mapOn *= 1 - ao; }
  // front highlight
  const af = fade(t, A('front'), Z('front') + 0.5);
  if (af > 0) { const [x0, y0] = P(23.5562, 37.9495), [x1, y1] = P(23.5545, 37.9640); ctx.save(); ctx.globalAlpha = af; ctx.strokeStyle = '#ffe08a'; ctx.lineWidth = 6; ctx.shadowColor = '#ffe08a'; ctx.shadowBlur = 20; ctx.beginPath(); ctx.moveTo(x0 + 26, y0); ctx.lineTo(x1 + 26, y1); ctx.stroke(); ctx.restore(); txt('能同时接敌的，只有最前几排', W / 2, 1230, { size: 46, w: 800, color: '#ffe08a', a: af, stroke: 6 }); }
  // compression wave annotation
  const awv = fade(t, A('wave1'), Z('wave2') + 1.2);
  if (awv > 0) { const [fx, fy] = P(23.556, 37.956), [bx, by] = P(23.60, 37.944); const ph = (t - A('wave1')) * 0.35 % 1;
    ctx.save(); ctx.globalAlpha = awv * 0.6; ctx.globalCompositeOperation = 'lighter'; const wx = lerp(fx, bx, ph), wy = lerp(fy, by, ph); const g = ctx.createRadialGradient(wx, wy, 0, wx, wy, 160); g.addColorStop(0, 'rgba(255,200,120,0.6)'); g.addColorStop(1, 'rgba(255,200,120,0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(wx, wy, 160, 0, Math.PI * 2); ctx.fill(); ctx.restore();
    arrow2(fx + 60, fy + 260, bx + 30, by + 300, awv, '#ffd27a'); txt('减速像波一样向后传', (fx + bx) / 2 + 40, (fy + by) / 2 + 330, { size: 42, w: 800, color: '#ffd27a', a: awv, stroke: 6 }); txt('「压缩波」', W / 2, 1240, { size: 64, w: 900, color: '#fff1d6', a: awv * ease(seg(t, A('wave2'), A('wave2') + 0.6)), stroke: 6, ls: 8 }); }
  const afl = fade(t, A('greek_strike') - 0.3, Z('order') + 0.4);
  if (afl > 0) { const p = ease(seg(t, A('greek_strike') - 0.2, A('greek_strike') + 2.2));
    arrow([[23.5435, 37.9715], [23.552, 37.9665], [23.5585, 37.9590]], p, { color: C.gr, hi: C.grHi, w: 46, a: afl });
    arrow([[23.5440, 37.9480], [23.553, 37.9490], [23.5600, 37.9530]], p, { color: C.gr, hi: C.grHi, w: 46, a: afl }); }
  const abr = fade(t, A('broadside'), Z('greek_strike') + 0.5);
  if (abr > 0) { const [x, y] = P(23.560, 37.955); txt('侧舷朝向撞角', x + 60, y - 160, { size: 40, w: 800, color: '#ffd0a0', a: abr * fade(t, A('broadside') + 1, A('greek_strike')), stroke: 5 }); sparks(x, y, t, Math.floor((t - A('broadside')) * 0.8) / 0.8 + A('broadside'), abr, 5, 1.6); }
  // Xerxes on Aigaleos
  const acm = fade(t, A('command'), Z('nobody_turns') + 0.5);
  if (acm > 0) { label(...PL.xerxes, '薛西斯观战处', { a: acm, dy: -60, color: '#ffe0b0', sub: '埃加莱奥斯山脚（示意）' }); const [x, y] = P(...PL.xerxes); ctx.save(); ctx.globalAlpha = acm * 0.25; ctx.fillStyle = '#ffd890'; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - 700, y + 500); ctx.lineTo(x - 200, y + 700); ctx.closePath(); ctx.fill(); ctx.restore(); }
  const aag = fade(t, A('aigaleos') - 0.2, Z('aigaleos') + 0.5); if (aag > 0) { dimAll(0.45 * aag); xerxesSil(W / 2 + 60, 1330, 0.85, aag, 1, t); }
  const ant = fade(t, A('nobody_turns'), Z('nobody_turns') + 0.4); if (ant > 0) txt('没人愿意第一个掉头', W / 2, 1230, { size: 54, w: 800, color: '#ffe0b0', a: ant, stroke: 6 });
  const apu = fade(t, A('push'), Z('push') + 0.4); if (apu > 0) { txt('看台 → 推力', W / 2, 1230, { size: 72, w: 900, color: '#ffd27a', a: apu, stroke: 6, ls: 6 }); }
  // Artemisia episode
  const aa = fade(t, A('artemisia0'), Z('misjudge') + 0.4);
  if (aa > 0) { const p = ease(seg(t, A('artemisia') + 0.5, A('artemisia') + 5)); const [ax0, ay0] = P(23.556, 37.9585), [ax1, ay1] = P(23.566, 37.9585); const x = lerp(ax0, ax1, p), y = lerp(ay0, ay1, p);
    const [cx, cy] = P(23.5672, 37.9588); const sunk = ease(seg(t, A('artemisia') + 4.6, A('artemisia') + 7));
    ship(cx, cy, Math.PI / 2 + sunk * 0.8, L * 1.5, C.pe, { a: aa * (1 - sunk * 0.9), broken: sunk }); ship(x - 70, y + 6, 0, L * 1.5, C.gr, { a: aa * ease(seg(t, A('artemisia'), A('artemisia') + 1)), oar: t * 8, glow: 14 }); ship(x, y, 0, L * 1.5, '#b388ff', { a: aa, oar: t * 8, glow: 18 });
    if (t > A('artemisia') + 4.6) sparks(cx, cy, t, A('artemisia') + 4.6, aa, 4, 1.8);
    txt('阿尔忒弥西亚', x, y - 60, { size: 34, w: 800, color: '#dcc8ff', a: aa * fade(t, A('artemisia'), Z('artemisia2')), stroke: 4 }); txt('自己人的船', cx + 10, cy + 70, { size: 30, w: 700, color: C.peHi, a: aa * fade(t, A('artemisia') + 3, Z('artemisia2')), stroke: 4 });
    const a3 = aa * fade(t, A('artemisia2'), Z('artemisia2') + 0.2); txt('「看，她撞沉了一艘敌船！」', W / 2, 1230, { size: 46, w: 800, color: '#ffe0b0', a: a3, stroke: 5 });
    const a4 = aa * fade(t, A('misjudge'), Z('misjudge') + 0.4); txt('远远看一眼，赏罚就会落错人', W / 2, 1230, { size: 46, w: 800, color: '#ffe0b0', a: a4, stroke: 5 }); }
  // swimmers
  const asw = fade(t, A('swim'), Z('swim') + 0.4);
  if (asw > 0) { for (let i = 0; i < 40; i++) { const g = i < 20; const p = seg(t, A('swim') + hash(i) * 2, Z('swim')); const [x0, y0] = P(23.551 + hash(i * 3) * 0.008, 37.951 + hash(i * 5) * 0.012); const [sx] = P(23.540, 37.956); const x = g ? lerp(x0, sx, p) : x0 + Math.sin(t + i) * 3, y = y0 + Math.cos(t * 2 + i) * 2;
      ctx.save(); ctx.globalAlpha = asw * (g ? 1 : 1 - p); ctx.fillStyle = g ? C.grHi : C.peHi; ctx.beginPath(); ctx.arc(x, y, 5, 0, Math.PI * 2); ctx.fill(); ctx.restore(); }
    txt('会游泳 → 游回萨拉米斯', W / 2, 1200, { size: 42, w: 800, color: C.grHi, a: asw, stroke: 5 }); txt('不会游泳 → 沉入海中', W / 2, 1270, { size: 42, w: 800, color: C.peHi, a: asw * ease(seg(t, A('swim') + 3, A('swim') + 3.6)), stroke: 5 }); txt('希罗多德《历史》8.89', W / 2, 1330, { size: 26, w: 500, color: C.goldDim, a: asw }); }
  // Psyttaleia
  const apk = fade(t, A('psy_kill'), Z('psy_kill') + 0.5);
  if (apk > 0) { label(...PL.psy, '普西塔利亚岛', { a: apk, dy: -70 }); const [px, py] = P(...PL.psy); const p = ease(seg(t, A('psy_kill') + 1, Z('psy_kill')));
    for (let i = 0; i < 24; i++) { ctx.save(); ctx.globalAlpha = apk * (1 - clamp(p * 1.6 - hash(i) * 0.6)); ctx.fillStyle = C.peHi; ctx.fillRect(px - 60 + (i % 8) * 16, py - 10 + Math.floor(i / 8) * 16, 10, 10); ctx.restore(); }
    arrow([[23.566, 37.947], [23.575, 37.944], [23.583, 37.9425]], p, { color: C.gr, hi: C.grHi, w: 30, a: apk }); txt('阿里斯提德登岛', W / 2, 1220, { size: 46, w: 800, color: C.grHi, a: apk, stroke: 5 }); txt('希罗多德《历史》8.95', W / 2, 1290, { size: 26, w: 500, color: C.goldDim, a: apk }); }
  // aftermath debris
  const aft = ease(seg(t, A('aftermath') - 0.5, A('aftermath') + 2));
  if (aft > 0) { for (let i = 0; i < 140; i++) { const x = W * 0.15 + hash(i * 3) * W * 0.8, y = H * 0.3 + hash(i * 7) * H * 0.45; ctx.save(); ctx.globalAlpha = aft * 0.8; ctx.translate(x, y + Math.sin(t + i) * 2); ctx.rotate(hash(i) * 6); ctx.fillStyle = i % 3 ? '#3a2c1e' : '#6b5236'; ctx.fillRect(-14 * hash(i * 9) - 4, -2, 28 * hash(i * 9) + 8, 4); ctx.restore(); } }
  return mapOn;
};

/* ---------- s6: who chose the battlefield ---------- */
SCN.s6 = (t) => {
  const s = SC.s6; let mapOn = 1;
  const aMap = 1 - ease(seg(t, A('theatre') - 0.4, A('theatre') + 0.2));
  if (aMap > 0) {
    setCam(camKeys(t, [[s.t0, [23.9, 38.6, 220]], [A('bridge'), [24.9, 39.3, 165]], [Z('retreat') + 0.3, [24.9, 39.3, 165]], [A('plataea') + 0.8, [23.3, 38.4, 420]], [Z('plataea'), [23.3, 38.35, 480]]])); ctx.save(); ctx.globalAlpha = aMap; drawMap(); grade('dim', 0.2); ctx.restore();
    arrow([[23.55, 37.93], [24.3, 38.3], [25.2, 39.3], [26.0, 40.0], PL.abydos], ease(seg(t, s.t0 + 1.5, A('bridge'))), { color: C.pe, hi: C.peHi, w: 34, a: aMap * (1 - ease(seg(t, A('retreat'), A('retreat') + 1))), dash: true });
    const ab = fade(t, A('bridge'), A('plataea'), 0.8, 0.6) * aMap; if (ab > 0) { label(...PL.abydos, '赫勒斯滂浮桥', { a: ab, dy: -50, color: '#ffe0b0' }); const [x, y] = P(...PL.abydos); ctx.save(); ctx.globalAlpha = ab; ctx.strokeStyle = '#e8d5a8'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(x - 20, y - 14); ctx.lineTo(x + 20, y + 14); ctx.stroke(); ctx.restore(); arrow([[24.6, 39.2], [25.6, 39.9], [26.3, 40.15]], ease(seg(t, A('bridge') + 1.5, A('bridge') + 3.5)), { color: C.gr, hi: C.grHi, w: 26, a: ab }); }
    arrow([PL.athens, [23.0, 38.6], [22.7, 39.4], [23.3, 40.4], [24.8, 40.9], [26.2, 40.6], PL.abydos, PL.sardis], ease(seg(t, A('retreat') + 0.5, A('retreat') + 4.5)), { color: C.pe, hi: C.peHi, w: 38, a: aMap * (1 - ease(seg(t, A('plataea') - 0.2, A('plataea') + 0.6))) });
    label(...PL.thessaly, '马多尼乌斯留守', { a: aMap * ease(seg(t, A('retreat') + 1, A('retreat') + 1.8)), dy: -50, color: C.peHi });
    const ap = ease(seg(t, A('plataea'), A('plataea') + 0.8)) * aMap; if (ap > 0) { label(...PL.plataea, '普拉提亚 · 前479年', { a: ap, dy: -56, color: '#ffe0b0' }); sparks(...P(...PL.plataea), t, Math.floor(t * 1.2) / 1.2, ap, 4, 1.4); }
  }
  if (t > A('theatre') - 0.5) {
    const a = ease(seg(t, A('theatre') - 0.4, A('theatre') + 0.4)); mapOn = 0;
    const at = a * (1 - ease(seg(t, A('cry0') - 0.3, A('cry0') + 0.4)));
    if (at > 0) { ctx.save(); ctx.globalAlpha = at; const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#1a1410'); g.addColorStop(1, '#050403'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore(); theatre(W / 2, 1050, 1.25, at, t);
      txt('前472年 · 雅典', W / 2, 440, { size: 40, w: 600, color: C.gold, a: at, ls: 6 }); txt('《波斯人》', W / 2, 540, { size: 96, w: 900, color: '#fff1d6', a: at, stroke: 6, ls: 10 }); txt('埃斯库罗斯', W / 2, 640, { size: 44, w: 700, color: C.bone, a: at });
      const a2 = at * ease(seg(t, A('theatre2'), A('theatre2') + 0.6)); txt('从波斯王宫的角度讲述 · 剧中无一个希腊人名', W / 2, 1300, { size: 34, w: 600, color: '#d8d0bf', a: a2 }); }
    const ac = a * ease(seg(t, A('cry0') - 0.3, A('cry0') + 0.4)) * (1 - ease(seg(t, A('answer0') - 0.4, A('answer0') + 0.2)));
    if (ac > 0) { ctx.save(); ctx.globalAlpha = ac; seaBg(t, 'dawn'); ctx.restore(); for (let i = 0; i < 5; i++) { const p = ease(seg(t, A('cry0') + i * 0.4, Z('cry2') + 2)); triremeSide(lerp(-500, 200, p) + i * 260, 900 + i * 90, 380 + i * 60, t + i, { a: ac, dir: 1 }); } }
    const aa = a * ease(seg(t, A('answer0') - 0.4, A('answer0') + 0.2)) * (1 - ease(seg(t, A('pericles0') - 0.4, A('pericles0') + 0.2)));
    if (aa > 0) { ctx.save(); ctx.globalAlpha = aa; ctx.fillStyle = '#05080c'; ctx.fillRect(0, 0, W, H); ctx.restore(); setCam([23.565, 37.957, 9000]); ctx.save(); ctx.globalAlpha = aa * 0.3; drawMap(); ctx.restore();
      txt('船多一倍，为什么输在窄水道？', W / 2, 430, { size: 50, w: 800, color: C.gold, a: aa }); txt('战场不是它选的', W / 2, 560, { size: 84, w: 900, color: '#fff1d6', a: aa * ease(seg(t, A('answer1'), A('answer1') + 0.5)), stroke: 6 });
      const it = [['一道神谕', '选定战场'], ['一次威胁', '留住盟友'], ['一封假信', '请进对手']]; const tb = A('answer2'), dd = (Z('answer2') - tb) / 3;
      it.forEach((r, i) => { const ai = aa * ease(seg(t, tb + i * dd - 0.3, tb + i * dd + 0.3)); txt(r[0], 340, 780 + i * 150, { size: 56, w: 800, color: C.grHi, a: ai }); txt('→', W / 2, 780 + i * 150, { size: 56, w: 800, color: C.gold, a: ai }); txt(r[1], 740, 780 + i * 150, { size: 56, w: 800, color: '#fff1d6', a: ai }); }); }
    const ae = a * ease(seg(t, A('pericles0') - 0.4, A('pericles0') + 0.2));
    if (ae > 0) { ctx.save(); ctx.globalAlpha = ae; const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#2a1a12'); g.addColorStop(0.4, '#6a3a1e'); g.addColorStop(0.42, '#1a2630'); g.addColorStop(1, '#03060a'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore(); ripples(t, ae, 4, 90);
      for (let i = 0; i < 7; i++) { const x = 160 + hash(i * 3) * 760, y = 1000 + hash(i * 5) * 520; ctx.save(); ctx.globalAlpha = ae * 0.9; ctx.translate(x + Math.sin(t * 0.5 + i) * 8, y + Math.sin(t * 0.8 + i * 2) * 4); ctx.rotate(hash(i) * 3 + Math.sin(t * 0.3 + i) * 0.05); ctx.fillStyle = '#4a3624'; ctx.fillRect(-160, -5, 260, 10); ctx.beginPath(); ctx.ellipse(110, 0, 42, 13, 0, 0, Math.PI * 2); ctx.fill(); ctx.restore(); }
      const al = ae * ease(seg(t, A('lesson'), A('lesson') + 0.8)); txt('优势资源，只有在对的地形上才算优势', W / 2, 1170, { size: 44, w: 700, color: C.bone, a: al, stroke: 5 }); txt('先问：战场是谁选的？', W / 2, 1270, { size: 70, w: 900, color: C.gold, a: al * ease(seg(t, A('lesson') + 3, A('lesson') + 3.8)), stroke: 6 });
      const aend = ease(seg(t, Z('lesson') + 0.8, Z('lesson') + 2.0)); if (aend > 0) { txt('历史的关键一局', W / 2, 440, { size: 46, w: 700, color: C.gold, a: aend, ls: 10 }); txt('萨拉米斯 · 前480年', W / 2, 520, { size: 34, w: 500, color: C.bone, a: aend, ls: 6 }); } }
  }
  return mapOn;
};

/* ================= main ================= */
function renderFrame(t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  let sc = D.tl.scenes[0]; for (const s of D.tl.scenes) if (t >= s.t0) sc = s;
  const mapOn = SCN[sc.id](t) || 0;
  // crossfade-from-black at scene boundaries (except very first frame)
  const i = D.tl.scenes.indexOf(sc);
  if (i > 0) { const k = 1 - ease(seg(t, sc.t0, sc.t0 + 0.5)); if (k > 0) { ctx.fillStyle = `rgba(0,0,0,${k})`; ctx.fillRect(0, 0, W, H); } }
  const nx = D.tl.scenes[i + 1]; if (nx) { const k = ease(seg(t, nx.t0 - 0.45, nx.t0)); if (k > 0) { ctx.fillStyle = `rgba(0,0,0,${k})`; ctx.fillRect(0, 0, W, H); } }
  if (t > TOTAL - 1.5) { ctx.fillStyle = `rgba(0,0,0,${ease(seg(t, TOTAL - 1.5, TOTAL - 0.2))})`; ctx.fillRect(0, 0, W, H); }
  vignette(0.9);
  chapterCard(t);
  quoteCard(t);
  subtitles(t);
  badges(t, mapOn);
  grain(t, 0.0);
}

function renderCover() {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  setCam([23.566, 37.953, 15500]); drawMap(); grade('dawn', 1);
  const t = 12; const L = clamp(cam.ppd / 11000 * 21, 16, 34);
  drawGreeks(t, { L, form: 1 }); drawPersians(t, 300, { L, waveHi: 1, collFx: 0 });
  arrow([[23.5435, 37.9715], [23.552, 37.9665], [23.5585, 37.9590]], 1, { color: C.gr, hi: C.grHi, w: 50 });
  arrow([[23.5440, 37.9480], [23.553, 37.9490], [23.5600, 37.9530]], 1, { color: C.gr, hi: C.grHi, w: 50 });
  vignette(1.1);
  const g = ctx.createLinearGradient(0, 0, 0, 760); g.addColorStop(0, 'rgba(0,0,0,0.85)'); g.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, 760);
  txt('历史的关键一局', W / 2, 210, { size: 40, w: 600, color: C.gold, ls: 12 });
  txt('船多一倍', W / 2, 360, { size: 150, w: 900, color: '#fff1d6', ls: 10, stroke: 10 });
  txt('为什么偏偏输在', W / 2, 520, { size: 92, w: 900, color: '#fff1d6', ls: 6, stroke: 8 });
  txt('一条窄水道？', W / 2, 650, { size: 92, w: 900, color: C.grHi, ls: 6, stroke: 8 });
  const b = ctx.createLinearGradient(0, H - 620, 0, H); b.addColorStop(0, 'rgba(0,0,0,0)'); b.addColorStop(1, 'rgba(0,0,0,0.9)'); ctx.fillStyle = b; ctx.fillRect(0, H - 620, W, 620);
  txt('萨拉米斯海战 · 公元前480年', W / 2, 1520, { size: 56, w: 800, color: '#fff1d6', ls: 6, stroke: 6 });
  txt('一封假情报，一条海峡，一次压缩波', W / 2, 1610, { size: 38, w: 500, color: C.gold, ls: 4 });
  txt('地图示意', W - 46, 1860, { size: 22, w: 400, color: 'rgba(230,225,210,0.6)', align: 'right' });
}
window.renderCover = renderCover;
window.renderFrame = renderFrame; window.TOTAL = TOTAL; window.A_ = A; window.LINES = LINES;
window.ready = loadAll();
