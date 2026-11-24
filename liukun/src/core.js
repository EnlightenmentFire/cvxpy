// ───────── core utilities: math, noise, ink, text, map, figures ─────────
const W = 1080, H = 1920;
const SC = {}; let SEGL = {}; const ln = (seg, i) => SEGL[seg][i];
const C = {
  night0: '#070b10', night1: '#0f1922', night2: '#1b2a36', slate: '#3b4f5e', mist: '#8ea3b0',
  pale: '#d8d3c3', paper: '#cfc8b4', ink: '#05070a', yellow: '#c9a65c', yellowDim: '#8c7645',
  red: '#8e2b22', redDim: '#5a1c17', steel: '#b9c7cf', fire: '#e0a04a',
};
const F = { serif: 'NotoSerif', brush: 'MaShan', kai: 'WenKai' };

const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, u) => a + (b - a) * u;
const sstep = (a, b, x) => { const u = clamp((x - a) / (b - a)); return u * u * (3 - 2 * u); };
const easeOut = u => 1 - Math.pow(1 - clamp(u), 3);
const easeIO = u => { u = clamp(u); return u < .5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2; };
// window: fade in over fi starting at a, fade out over fo ending at b
const win = (t, a, b, fi = .6, fo = .6) => Math.min(sstep(a, a + fi, t), 1 - sstep(b - fo, b, t));

function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const hash = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
const hash2 = (x, y) => { const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453; return s - Math.floor(s); };
function noise1(x, seed = 0) { const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f); return lerp(hash(i + seed * 57.3), hash(i + 1 + seed * 57.3), u); }
function fbm1(x, seed = 0, oct = 4) { let a = .5, s = 0, f = 1; for (let o = 0; o < oct; o++) { s += a * noise1(x * f, seed + o * 7.1); a *= .5; f *= 2; } return s; }
function noise2(x, y, seed = 0) { const i = Math.floor(x), j = Math.floor(y), fx = x - i, fy = y - j, u = fx * fx * (3 - 2 * fx), v = fy * fy * (3 - 2 * fy); const o = seed * 13.7; return lerp(lerp(hash2(i + o, j), hash2(i + 1 + o, j), u), lerp(hash2(i + o, j + 1), hash2(i + 1 + o, j + 1), u), v); }
function fbm2(x, y, seed = 0, oct = 4) { let a = .5, s = 0, f = 1; for (let o = 0; o < oct; o++) { s += a * noise2(x * f, y * f, seed + o * 3.3); a *= .5; f *= 2; } return s; }

function mkCanvas(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }
const cache = {};
function cached(key, fn) { return cache[key] || (cache[key] = fn()); }
function rgba(hex, a) { const n = parseInt(hex.slice(1), 16); return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`; }

// ── static textures ──
function paperTex() {
  return cached('paper', () => {
    const c = mkCanvas(W / 2, H / 2), x = c.getContext('2d'), im = x.createImageData(c.width, c.height), d = im.data, r = rng(7);
    for (let j = 0; j < c.height; j++) for (let i = 0; i < c.width; i++) {
      const k = (j * c.width + i) * 4;
      const n = fbm2(i / 90, j / 90, 3, 4) * .55 + fbm2(i / 7, j / 9, 9, 2) * .25 + r() * .2;
      const v = Math.floor(255 * clamp(n));
      d[k] = d[k + 1] = d[k + 2] = v; d[k + 3] = 255;
    }
    x.putImageData(im, 0, 0); return c;
  });
}
function blotTex(seed = 1, soft = .35) {
  return cached('blot' + seed + '_' + soft, () => {
    const S = 256, c = mkCanvas(S, S), x = c.getContext('2d'), im = x.createImageData(S, S), d = im.data;
    for (let j = 0; j < S; j++) for (let i = 0; i < S; i++) {
      const dx = (i - S / 2) / (S / 2), dy = (j - S / 2) / (S / 2), r = Math.hypot(dx, dy);
      const n = fbm2(i / 38, j / 38, seed, 4);
      const a = 1 - sstep(.55 - soft, .98, r + (n - .5) * .7);
      const k = (j * S + i) * 4; d[k] = d[k + 1] = d[k + 2] = 255; d[k + 3] = Math.floor(255 * a * (0.75 + .25 * fbm2(i / 9, j / 9, seed + 5, 2)));
    }
    x.putImageData(im, 0, 0); return c;
  });
}
function tinted(tex, color, key) {
  return cached('tint' + key + color, () => { const c = mkCanvas(tex.width, tex.height), x = c.getContext('2d'); x.drawImage(tex, 0, 0); x.globalCompositeOperation = 'source-in'; x.fillStyle = color; x.fillRect(0, 0, c.width, c.height); return c; });
}
function blot(ctx, x, y, r, color, alpha = 1, seed = 1, rot = 0, soft = .35) {
  if (alpha <= 0 || r <= 0) return;
  const t = tinted(blotTex(seed, soft), color, 'b' + seed + soft);
  ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(x, y); ctx.rotate(rot); ctx.drawImage(t, -r, -r, 2 * r, 2 * r); ctx.restore();
}
function glow(ctx, x, y, r, color, alpha = 1) {
  if (alpha <= 0) return;
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, rgba(color, alpha)); g.addColorStop(.35, rgba(color, alpha * .35)); g.addColorStop(1, rgba(color, 0));
  ctx.fillStyle = g; ctx.fillRect(x - r, y - r, 2 * r, 2 * r);
}
function bgGrad(ctx, top, mid, bot, midAt = .55) {
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, top); g.addColorStop(midAt, mid); g.addColorStop(1, bot);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}

// ── ink mountains (cached layer) ──
function mountains(key, { seed = 1, w = W, h = 700, layers }) {
  return cached('mt' + key, () => {
    const c = mkCanvas(w, h), x = c.getContext('2d');
    layers.forEach((L, li) => {
      const pts = []; for (let i = 0; i <= w; i += 4) {
        const n = fbm1(i * (L.freq || .004) + li * 31, seed + li * 5, L.oct || 5);
        const sharp = Math.pow(n, L.pow || 1.6);
        pts.push([i, L.y - L.amp * sharp * 1.8]);
      }
      x.beginPath(); x.moveTo(0, h); pts.forEach(p => x.lineTo(p[0], p[1])); x.lineTo(w, h); x.closePath();
      const top = L.y - L.amp * 1.2, g = x.createLinearGradient(0, top, 0, L.y + (L.fade || 160));
      g.addColorStop(0, rgba(L.col, L.a ?? 1)); g.addColorStop(1, rgba(L.col, 0));
      x.fillStyle = g; x.fill();
    });
    return c;
  });
}

// ── ink stroke (tapered polyline) ──
function stroke(ctx, pts, w, color, alpha = 1, { taper = .6, seed = 1, u0 = 0, u1 = 1 } = {}) {
  if (alpha <= 0 || u1 <= u0) return;
  const n = pts.length - 1; ctx.save(); ctx.strokeStyle = color; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.globalAlpha *= alpha;
  const i0 = Math.floor(u0 * n), i1 = Math.ceil(u1 * n);
  for (let i = i0; i < i1; i++) {
    const u = (i + .5) / n; const prof = 1 - taper * Math.pow(Math.abs(u * 2 - 1), 2.2);
    ctx.lineWidth = Math.max(.5, w * prof * (.85 + .3 * noise1(i * .7, seed)));
    let a = pts[i], b = pts[i + 1];
    if (i === i1 - 1) { const f = u1 * n - i; if (f < 1) b = [lerp(a[0], b[0], f), lerp(a[1], b[1], f)]; }
    ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
  }
  ctx.restore();
}
function curve(p0, p1, p2, n = 24) { const o = []; for (let i = 0; i <= n; i++) { const u = i / n, a = (1 - u) * (1 - u), b = 2 * u * (1 - u), c = u * u; o.push([a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]]); } return o; }
function smoothPath(pts, sub = 6) { // Catmull-Rom resample
  const o = []; for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
    for (let s = 0; s < sub; s++) { const u = s / sub, u2 = u * u, u3 = u2 * u;
      o.push([.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * u + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * u3),
        .5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * u + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * u3)]); }
  } o.push(pts[pts.length - 1]); return o;
}
function pathLen(pts) { let s = 0; for (let i = 1; i < pts.length; i++) s += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); return s; }
function pointAt(pts, u) { u = clamp(u); const L = pathLen(pts) * u; let s = 0; for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); if (s + d >= L) { const f = d ? (L - s) / d : 0; return [lerp(pts[i - 1][0], pts[i][0], f), lerp(pts[i - 1][1], pts[i][1], f), Math.atan2(pts[i][1] - pts[i - 1][1], pts[i][0] - pts[i - 1][0])]; } s += d; } const p = pts[pts.length - 1]; return [p[0], p[1], 0]; }
function dashed(ctx, pts, u, color, w = 3, dash = [10, 12], alpha = 1) {
  if (u <= 0 || alpha <= 0) return; const L = pathLen(pts);
  ctx.save(); ctx.globalAlpha *= alpha; ctx.strokeStyle = color; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.setLineDash(dash);
  ctx.beginPath(); let s = 0; ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); if (s + d > L * u) { const f = (L * u - s) / d; ctx.lineTo(lerp(pts[i - 1][0], pts[i][0], f), lerp(pts[i - 1][1], pts[i][1], f)); break; } ctx.lineTo(pts[i][0], pts[i][1]); s += d; }
  ctx.stroke(); ctx.restore();
}
function arrowHead(ctx, x, y, ang, size, color, alpha = 1) {
  ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(x, y); ctx.rotate(ang); ctx.fillStyle = color;
  ctx.beginPath(); ctx.moveTo(size, 0); ctx.lineTo(-size * .7, size * .62); ctx.lineTo(-size * .35, 0); ctx.lineTo(-size * .7, -size * .62); ctx.closePath(); ctx.fill(); ctx.restore();
}
function arrow(ctx, pts, u, color, w = 6, alpha = 1, head = 20) {
  if (u <= 0 || alpha <= 0) return; stroke(ctx, pts, w, color, alpha, { taper: .35, u1: u });
  const p = pointAt(pts, u); arrowHead(ctx, p[0], p[1], p[2], head, color, alpha * sstep(0, .15, u));
}

// ── text ──
function font(size, fam = F.serif, weight = 600) { return `${weight} ${size}px ${fam}`; }
function htext(ctx, str, x, y, size, color, { fam = F.serif, weight = 600, align = 'center', alpha = 1, reveal = 1, spacing = 0, outline = 0, outlineColor = 'rgba(3,6,9,.85)' } = {}) {
  if (alpha <= 0) return 0; ctx.save(); ctx.font = font(size, fam, weight); ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
  const chars = [...str]; const ws = chars.map(ch => ctx.measureText(ch).width + spacing); const tw = ws.reduce((a, b) => a + b, 0) - spacing;
  let cx = align === 'center' ? x - tw / 2 : align === 'right' ? x - tw : x; const n = chars.length;
  chars.forEach((ch, i) => { const a = alpha * clamp(reveal * (n + 2) - i); if (a > 0) { ctx.globalAlpha = a; if (outline) { ctx.lineWidth = outline; ctx.strokeStyle = outlineColor; ctx.lineJoin = 'round'; ctx.strokeText(ch, cx, y); } ctx.fillStyle = color; ctx.fillText(ch, cx, y); } cx += ws[i]; });
  ctx.restore(); return tw;
}
const VPUNCT = { '，': '︐', '。': '︒', '、': '︑', '：': '︓', '；': '︔', '！': '︕', '？': '︖', '「': '﹁', '」': '﹂', '《': '︽', '》': '︾', '…': '︙', '—': '︱', '·': '·' };
function vtext(ctx, str, x, y, size, color, { fam = F.serif, weight = 600, alpha = 1, reveal = 1, lh = 1.12, outline = 0 } = {}) {
  if (alpha <= 0) return; ctx.save(); ctx.font = font(size, fam, weight); ctx.textBaseline = 'middle'; ctx.textAlign = 'center';
  const chars = [...str], n = chars.length; let cy = y;
  chars.forEach((ch, i) => {
    const a = alpha * clamp(reveal * (n + 2) - i); const isP = '，。、：；！？'.includes(ch);
    if (a > 0) { ctx.globalAlpha = a; ctx.fillStyle = color;
      if (isP) { ctx.fillText(ch, x + size * .32, cy - size * .38); }
      else { if (outline) { ctx.lineWidth = outline; ctx.strokeStyle = 'rgba(3,6,9,.8)'; ctx.strokeText(ch, x, cy); } ctx.fillText(ch, x, cy); } }
    cy += size * lh * (isP ? .45 : 1);
  }); ctx.restore();
}
// multi-column vertical text, right-to-left; cols = array of strings
function vcols(ctx, cols, xRight, y, size, color, opt = {}) {
  const gap = opt.gap || size * 1.55, total = cols.reduce((a, c) => a + [...c].length, 0); let acc = 0;
  cols.forEach((c, i) => { const n = [...c].length; const r = opt.reveal === undefined ? 1 : clamp((opt.reveal * (total + 2) - acc) / (n + 2)); vtext(ctx, c, xRight - i * gap, y, size, color, { ...opt, reveal: r }); acc += n; });
}
function seal(ctx, x, y, size, str, alpha = 1) { // small red seal-like tag
  ctx.save(); ctx.globalAlpha *= alpha; const n = [...str].length; ctx.fillStyle = C.red; const w = size * 1.25, h = size * (n * 1.08 + .3);
  ctx.beginPath(); ctx.roundRect(x - w / 2, y, w, h, 4); ctx.fill(); ctx.restore();
  vtext(ctx, str, x, y + size * .68, size, '#e9dcc8', { weight: 700, alpha, lh: 1.08 });
}

// ── map ──
const MAP = {
  coast: [[124.3, 39.9], [123.2, 39.7], [122.2, 39.2], [121.3, 38.8], [121.6, 39.3], [122.1, 40.4], [121.9, 40.8], [121.1, 40.9], [120.4, 40.3], [119.6, 39.9], [119.0, 39.2], [118.1, 39.1], [117.7, 38.8], [117.6, 38.4], [118.0, 38.1], [118.8, 37.9], [119.1, 37.4], [119.6, 37.1], [120.3, 37.6], [120.8, 37.8], [121.5, 37.5], [122.6, 37.4], [122.5, 36.9], [121.5, 36.7], [120.7, 36.3], [120.2, 36.0], [119.6, 35.5], [119.3, 35.0], [119.3, 34.6], [119.9, 34.3], [120.4, 33.7], [120.9, 32.9], [121.4, 32.3], [121.9, 31.7], [121.6, 31.1], [121.9, 30.8], [121.0, 30.6], [120.3, 30.3], [121.2, 30.2], [122.0, 29.8], [121.7, 29.0], [121.5, 27.5]],
  huang: [[102.8, 36.0], [103.8, 36.1], [104.6, 37.0], [105.9, 38.0], [106.6, 39.0], [107.0, 40.3], [107.8, 40.8], [109.5, 40.6], [111.0, 40.3], [111.4, 39.6], [111.1, 38.8], [110.7, 37.8], [110.5, 36.8], [110.5, 35.6], [110.3, 34.7], [111.2, 34.8], [112.4, 34.9], [113.5, 34.95], [114.3, 35.2], [115.0, 35.7], [115.9, 36.4], [116.8, 37.0], [117.6, 37.5], [118.4, 37.75], [118.9, 37.85]],
  fen: [[112.3, 38.7], [112.5, 37.9], [112.1, 37.2], [111.7, 36.5], [111.5, 36.0], [110.9, 35.5], [110.55, 35.4]],
  wei: [[105.5, 34.7], [107.5, 34.4], [108.9, 34.4], [110.25, 34.65]],
  chang: [[103.5, 28.2], [105.0, 28.9], [106.5, 29.6], [108.0, 30.5], [109.5, 31.0], [111.0, 30.8], [112.2, 30.3], [113.0, 29.5], [114.3, 30.6], [115.3, 30.0], [116.0, 29.8], [117.0, 30.5], [117.8, 31.0], [118.4, 31.4], [118.8, 32.1], [119.5, 32.25], [120.5, 32.0], [121.2, 31.8], [121.9, 31.5]],
  huai: [[113.5, 32.3], [115.0, 32.4], [116.5, 32.6], [117.5, 32.9], [118.5, 33.1], [119.2, 33.6], [119.9, 34.2]],
  ranges: [
    [[113.2, 35.3], [113.7, 36.2], [113.9, 37.2], [114.1, 38.2], [114.6, 39.2], [115.3, 40.0]],   // 太行
    [[110.95, 36.0], [111.2, 37.2], [111.5, 38.3], [111.9, 39.0]],                                // 吕梁
    [[112.3, 39.35], [113.2, 39.5], [114.1, 39.6]],                                                // 恒山
    [[111.9, 36.7], [112.5, 36.45], [113.0, 36.6]],                                                // 太岳
    [[115.5, 40.4], [117.0, 40.55], [118.5, 40.35], [119.5, 40.1]],                                // 燕山
    [[106.5, 33.95], [108.5, 33.85], [110.5, 34.15], [112.0, 34.2]],                               // 秦岭
    [[108.5, 41.1], [110.5, 41.0], [112.5, 40.9]],                                                 // 阴山
  ],
  city: { luoyang: [112.45, 34.7], changan: [108.95, 34.3], jinyang: [112.55, 37.85], ji: [116.35, 39.9], jiankang: [118.8, 32.05], huguan: [113.2, 36.1], pingyang: [111.5, 36.1], xiangguo: [114.5, 37.05], pingcheng: [113.3, 40.1], leping: [113.7, 37.6], yongqiu: [114.8, 34.55], guan: [116.3, 39.35], lingzhi: [118.9, 40.0], feihu: [114.6, 39.45] },
};
const KX = .82;
function mkCam(lon, lat, scale, cx = 540, cy = 760) { return { lon, lat, scale, cx, cy }; }
function camLerp(a, b, u) { u = easeIO(u); return { lon: lerp(a.lon, b.lon, u), lat: lerp(a.lat, b.lat, u), scale: Math.exp(lerp(Math.log(a.scale), Math.log(b.scale), u)), cx: lerp(a.cx, b.cx, u), cy: lerp(a.cy, b.cy, u) }; }
function proj(cam, p) { return [cam.cx + (p[0] - cam.lon) * KX * cam.scale, cam.cy - (p[1] - cam.lat) * cam.scale]; }
function projAll(cam, pts) { return pts.map(p => proj(cam, p)); }
const CAM_ALL = mkCam(114.3, 35.9, 74, 540, 760), CAM_NORTH = mkCam(113.6, 37.3, 118, 540, 760), CAM_BING = mkCam(112.9, 37.3, 205, 540, 760);

function drawMap(ctx, cam, { alpha = 1, landA = 1, detail = 1 } = {}) {
  ctx.save(); ctx.globalAlpha *= alpha;
  // land wash
  ctx.fillStyle = rgba('#1a2732', .9 * landA); ctx.fillRect(0, 0, W, H);
  // subtle land mottling (cached big blot field, pans with camera roughly)
  const tex = paperTex(); ctx.save(); ctx.globalCompositeOperation = 'soft-light'; ctx.globalAlpha *= .5;
  const o = proj(cam, [105, 44]), sc = cam.scale / 74; ctx.drawImage(tex, o[0], o[1], W * 1.6 * sc, H * 1.0 * sc); ctx.restore();
  // sea
  const co = projAll(cam, smoothPath(MAP.coast, 4));
  ctx.beginPath(); ctx.moveTo(co[0][0], co[0][1]); co.forEach(p => ctx.lineTo(p[0], p[1]));
  const e1 = proj(cam, [130, 27.5]), e2 = proj(cam, [130, 39.9]); ctx.lineTo(e1[0], e1[1]); ctx.lineTo(e2[0], e2[1]); ctx.closePath();
  ctx.fillStyle = rgba('#070c12', .92); ctx.fill();
  ctx.strokeStyle = rgba(C.mist, .35); ctx.lineWidth = 1.6; ctx.stroke();
  // rivers
  const riv = (pts, w, a) => stroke(ctx, projAll(cam, smoothPath(pts, 6)), w * Math.sqrt(cam.scale / 74), '#7f9db0', a, { taper: .25, seed: 3 });
  riv(MAP.huang, 4.2, .62); riv(MAP.chang, 4.6, .58); riv(MAP.fen, 2.2, .42 * detail); riv(MAP.wei, 2.4, .42 * detail); riv(MAP.huai, 2.4, .36 * detail);
  // mountain hatch
  const r = rng(11); const s = Math.sqrt(cam.scale / 74);
  MAP.ranges.forEach((rg, ri) => { const pts = smoothPath(rg, 8);
    for (let i = 0; i < pts.length; i += 2) { const p = proj(cam, pts[i]); const jx = (r() - .5) * 26 * s, jy = (r() - .5) * 20 * s, hh = (12 + r() * 12) * s, ww = (11 + r() * 9) * s;
      const x = p[0] + jx, y = p[1] + jy; if (x < -40 || x > W + 40 || y < -40 || y > H + 40) continue;
      ctx.beginPath(); ctx.moveTo(x - ww, y + hh * .5); ctx.lineTo(x - ww * .1, y - hh * .6); ctx.lineTo(x + ww, y + hh * .5);
      ctx.strokeStyle = rgba('#93a7b3', .34); ctx.lineWidth = 1.5 * s; ctx.lineJoin = 'round'; ctx.stroke();
      ctx.beginPath(); ctx.moveTo(x - ww * .1, y - hh * .6); ctx.lineTo(x + ww, y + hh * .5); ctx.lineTo(x + ww * .2, y + hh * .5); ctx.closePath(); ctx.fillStyle = rgba('#05080b', .35); ctx.fill(); } });
  ctx.restore();
}
function cityDot(ctx, cam, key, label, { alpha = 1, color = C.pale, size = 34, dx = 16, dy = 0, lit = 0, litColor = C.yellow, sq = false, sub = '', dim = 0 } = {}) {
  if (alpha <= 0) return; const p = proj(cam, MAP.city[key]); ctx.save(); ctx.globalAlpha *= alpha;
  if (lit > 0) glow(ctx, p[0], p[1], 70 * lit + 20, litColor, .55 * lit);
  ctx.fillStyle = dim ? rgba('#5d6a73', 1) : color; ctx.strokeStyle = rgba('#05080b', .9); ctx.lineWidth = 2;
  ctx.beginPath(); if (sq) ctx.rect(p[0] - 7, p[1] - 7, 14, 14); else ctx.arc(p[0], p[1], 6.5, 0, 7); ctx.fill(); ctx.stroke();
  ctx.restore();
  if (label) { htext(ctx, label, p[0] + dx, p[1] + dy, size, dim ? '#6c7880' : color, { align: dx >= 0 ? 'left' : 'right', alpha, weight: 700, outline: 5 });
    if (sub) htext(ctx, sub, p[0] + dx, p[1] + dy + size * .95, size * .62, rgba(C.mist, 1), { align: dx >= 0 ? 'left' : 'right', alpha: alpha * .9, weight: 500, outline: 4 }); }
  return p;
}
function regionLabel(ctx, cam, lonlat, str, size, alpha = 1, color = '#9fb0ba') { const p = proj(cam, lonlat); htext(ctx, str, p[0], p[1], size, color, { alpha: alpha * .75, weight: 500, spacing: size * .5, outline: 4 }); }

// ── figures (ink silhouettes) ──
// feet at (x,y); h = height; facing ±1; lean = shear; arm: angle (rad, 0 = forward horizontal, + = up); sword length in h units
function figure(ctx, x, y, h, { facing = 1, lean = 0, arm = null, sword = 0, swordA = 0, color = C.ink, alpha = 1, back = false, sit = false, robeW = 1, glint = 0 } = {}) {
  if (alpha <= 0) return; ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(x, y); ctx.scale(facing * h, h);
  const sh = yy => lean * yy; // x shear as function of (negative) y
  const P = (px, py) => [px + sh(py), py];
  ctx.fillStyle = color;
  const top = sit ? -.62 : -1, sy = top + .22, wy = sit ? -.3 : -.5; // shoulder / waist y
  // robe
  ctx.beginPath();
  if (sit) { let a = P(-.25 * robeW, 0); ctx.moveTo(a[0], a[1]); a = P(.3 * robeW, 0); ctx.lineTo(a[0], a[1]); ctx.quadraticCurveTo(...P(.3 * robeW, -.1), ...P(.2 * robeW, -.14)); ctx.quadraticCurveTo(...P(.13, -.2), ...P(.125, wy)); }
  else { let a = P(-.2 * robeW, 0); ctx.moveTo(a[0], a[1]); ctx.quadraticCurveTo(...P(0, .025), ...P(.24 * robeW, 0)); ctx.quadraticCurveTo(...P(.17 * robeW, -.25), ...P(.115, wy)); }
  ctx.quadraticCurveTo(...P(.15, sy + .1), ...P(.135, sy)); ctx.quadraticCurveTo(...P(.07, sy - .05), ...P(.045, sy - .055));
  ctx.lineTo(...P(-.045, sy - .055)); ctx.quadraticCurveTo(...P(-.08, sy - .05), ...P(-.14, sy));
  if (sit) { ctx.quadraticCurveTo(...P(-.165, sy + .12), ...P(-.15, wy)); ctx.quadraticCurveTo(...P(-.2 * robeW, -.2), ...P(-.25 * robeW, 0)); }
  else { ctx.quadraticCurveTo(...P(-.16, sy + .12), ...P(-.12, wy)); ctx.quadraticCurveTo(...P(-.16 * robeW, -.25), ...P(-.2 * robeW, 0)); }
  ctx.closePath(); ctx.fill();
  // head + topknot
  const hc = P(back ? 0 : .012, sy - .125); ctx.beginPath(); ctx.ellipse(hc[0], hc[1], .062, .072, 0, 0, 7); ctx.fill();
  const tk = P(back ? 0 : -.01, sy - .215); ctx.beginPath(); ctx.ellipse(tk[0], tk[1], .028, .034, 0, 0, 7); ctx.fill();
  ctx.fillRect(tk[0] - .05, tk[1] - .006, .1, .012);
  // arm with sleeve + sword
  if (arm !== null) {
    const s0 = P(.1, sy + .04), L = .34, hx = s0[0] + Math.cos(arm) * L, hy = s0[1] - Math.sin(arm) * L;
    const nx = Math.sin(arm), ny = Math.cos(arm);
    ctx.beginPath(); ctx.moveTo(s0[0] - nx * .05, s0[1] - ny * .05); ctx.lineTo(hx, hy); ctx.quadraticCurveTo(hx - Math.cos(arm) * .1 + nx * .16, hy + Math.sin(arm) * .1 + ny * .2, s0[0] + nx * .1, s0[1] + ny * .12); ctx.closePath(); ctx.fill();
    if (sword > 0) { const a = arm + swordA, ex = hx + Math.cos(a) * sword, ey = hy - Math.sin(a) * sword;
      ctx.strokeStyle = rgba(C.steel, .95); ctx.lineWidth = .013; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(hx, hy); ctx.lineTo(ex, ey); ctx.stroke();
      ctx.strokeStyle = color; ctx.lineWidth = .022; ctx.beginPath(); ctx.moveTo(hx - Math.cos(a) * .07, hy + Math.sin(a) * .07); ctx.lineTo(hx + Math.cos(a) * .02, hy - Math.sin(a) * .02); ctx.stroke();
      if (glint > 0) { ctx.globalAlpha *= glint; ctx.strokeStyle = '#ffffff'; ctx.lineWidth = .02; ctx.beginPath(); ctx.moveTo(lerp(hx, ex, .5), lerp(hy, ey, .5)); ctx.lineTo(ex, ey); ctx.stroke(); } }
  }
  ctx.restore();
}
// Chinese roof building silhouette: base centered x, ground y
function hall(ctx, x, y, w, h, color, { tiers = 1, alpha = 1 } = {}) {
  ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = color; let cy = y, cw = w, ch = h;
  for (let t = 0; t < tiers; t++) {
    const body = ch * .52, roof = ch * .48;
    ctx.fillRect(x - cw * .36, cy - body, cw * .72, body);
    const ry = cy - body; ctx.beginPath(); ctx.moveTo(x - cw * .62, ry + roof * .06); ctx.quadraticCurveTo(x - cw * .3, ry - roof * .25, x - cw * .16, ry - roof); ctx.lineTo(x + cw * .16, ry - roof);
    ctx.quadraticCurveTo(x + cw * .3, ry - roof * .25, x + cw * .62, ry + roof * .06); ctx.quadraticCurveTo(x + cw * .5, ry + roof * .18, x + cw * .44, ry + roof * .2); ctx.lineTo(x - cw * .44, ry + roof * .2); ctx.quadraticCurveTo(x - cw * .5, ry + roof * .18, x - cw * .62, ry + roof * .06); ctx.fill();
    cy = ry - roof * .92; cw *= .72; ch *= .8;
  } ctx.restore();
}
function cityWall(ctx, x0, x1, y, h, color, { alpha = 1, crenel = 22 } = {}) {
  ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = color; ctx.fillRect(x0, y - h, x1 - x0, h + 400);
  if (crenel > 0) for (let x = x0; x < x1; x += crenel * 2) ctx.fillRect(x, y - h - crenel * .6, crenel, crenel * .6 + 1); ctx.restore();
}
function tree(ctx, x, y, h, seed, color, alpha = 1) {
  const r = rng(seed); ctx.save(); ctx.globalAlpha *= alpha; ctx.strokeStyle = color; ctx.lineCap = 'round';
  const br = (x, y, a, len, w, d) => { const x2 = x + Math.cos(a) * len, y2 = y - Math.sin(a) * len; ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(x, y); ctx.quadraticCurveTo(x + Math.cos(a + .3) * len * .5, y - Math.sin(a + .3) * len * .5, x2, y2); ctx.stroke();
    if (d > 0) { const n = 2 + (r() > .6 ? 1 : 0); for (let i = 0; i < n; i++) br(x2, y2, a + (r() - .5) * 1.5, len * (.55 + r() * .25), w * .62, d - 1); } };
  br(x, y, Math.PI / 2 + (r() - .5) * .3, h * .36, h * .035, 5); ctx.restore();
}
function flame(ctx, x, y, s, t, seed = 0, alpha = 1) {
  const fl = .8 + .2 * noise1(t * 7 + seed * 3.1, seed) + .1 * Math.sin(t * 11 + seed);
  glow(ctx, x, y - s * .4, s * 5.5 * fl, C.fire, .26 * alpha); glow(ctx, x, y - s * .5, s * 1.9 * fl, '#f4c877', .9 * alpha);
  ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = '#fbe5ae'; ctx.beginPath(); ctx.ellipse(x + Math.sin(t * 5 + seed) * s * .08, y - s * .55 * fl, s * .28, s * .72 * fl, 0, 0, 7); ctx.fill(); ctx.restore();
}
