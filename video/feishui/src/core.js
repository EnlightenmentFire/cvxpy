// 淝水之战 —— 渲染核心。所有画面都是时间 t 的纯函数（同一 t 永远画出同一帧）。
'use strict';
const W = 1080, H = 1920, FPS = 25;
let cv, ctx, TL, GEO;
const IMG = {};
const C = {
  qin: '#5ea6ea', qinL: '#b4dcff', qinD: '#2d5f92', qinDD: '#1b3a5c',
  jin: '#e2482f', jinL: '#ff9070', jinD: '#8e2214',
  gold: '#e3bf72', goldD: '#9c7a3a', cream: '#f4ead6', paper: '#e9dcc0',
  ink: '#0b0b0d', night: '#070a10', water: '#16283a', waterL: '#3a5a78', grey: '#8b8f96',
};
const SERIF = '"Noto Serif SC"', SANS = '"Noto Sans SC"';

// ---------- 数学 ----------
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, u) => a + (b - a) * u;
const sstep = x => { x = clamp(x); return x * x * (3 - 2 * x); };
const eio = x => { x = clamp(x); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const eout = x => 1 - Math.pow(1 - clamp(x), 3);
const ein = x => Math.pow(clamp(x), 3);
const P = (t, a, d) => sstep((t - a) / d);
const fadeIO = (t, a, b, fi = 0.5, fo = 0.5) => Math.min(sstep((t - a) / fi), sstep((b - t) / fo));
const hash = (i, k = 0) => { const x = Math.sin(i * 127.1 + k * 311.7 + 0.1) * 43758.5453; return x - Math.floor(x); };
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
function rgba(hex, a) { const n = parseInt(hex.slice(1), 16); return `rgba(${n >> 16 & 255},${n >> 8 & 255},${n & 255},${a})`; }
function mix(h1, h2, u) { const a = parseInt(h1.slice(1), 16), b = parseInt(h2.slice(1), 16); const r = Math.round(lerp(a >> 16 & 255, b >> 16 & 255, u)), g = Math.round(lerp(a >> 8 & 255, b >> 8 & 255, u)), bl = Math.round(lerp(a & 255, b & 255, u)); return `rgb(${r},${g},${bl})`; }

// ---------- 时间轴 ----------
const LINE = {};
const A = id => LINE[id].start, E = id => LINE[id].end;
const N = id => { const i = TL.lines.findIndex(l => l.id === id); return TL.lines[i + 1] ? TL.lines[i + 1].start : TL.total; };
const S0 = s => TL.secs[s].start, S1 = s => TL.secs[s].end;
function curLine(t) { let c = null; for (const l of TL.lines) { if (l.start <= t + 1e-6) c = l; else break; } return c; }

// ---------- 关键帧镜头 ----------
function kf(keys, t, logLast = true) {
  if (t <= keys[0][0]) return keys[0].slice(1);
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i], b = keys[i + 1];
    if (t <= b[0]) {
      const u = eio((t - a[0]) / (b[0] - a[0]));
      return a.slice(1).map((v, j) => (logLast && j === a.length - 2) ? Math.exp(lerp(Math.log(v), Math.log(b[j + 1]), u)) : lerp(v, b[j + 1], u));
    }
  }
  return keys[keys.length - 1].slice(1);
}

// ---------- 地图（Web 墨卡托；两块底图 macro / region） ----------
function merc(lon, lat) { return [(lon + 180) / 360, (1 - Math.asinh(Math.tan(lat * Math.PI / 180)) / Math.PI) / 2]; }
function plateCam(pl, v) { const g = GEO[pl]; const [X, Y] = merc(v[0], v[1]); const px = (X - g.mx0) * g.scale, py = (Y - g.my0) * g.scale; const s = W / (v[2] * g.scale / 360); return { pl, px, py, s }; }
function mw(cam, lon, lat) { const g = GEO[cam.pl]; const [X, Y] = merc(lon, lat); return [W / 2 + ((X - g.mx0) * g.scale - cam.px) * cam.s, H / 2 + ((Y - g.my0) * g.scale - cam.py) * cam.s]; }
function drawPlate(cam, dim = 0.25, tint = null) {
  ctx.fillStyle = '#15171a'; ctx.fillRect(0, 0, W, H);
  const sw = W / cam.s, sh = H / cam.s;
  ctx.drawImage(IMG[cam.pl + 'X'] || IMG[cam.pl], cam.px - sw / 2, cam.py - sh / 2, sw, sh, 0, 0, W, H);
  if (dim > 0) { ctx.fillStyle = `rgba(8,10,14,${dim})`; ctx.fillRect(0, 0, W, H); }
  if (tint) { ctx.fillStyle = tint; ctx.fillRect(0, 0, W, H); }
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
function cumLen(p) { let s = 0; const c = [0]; for (let i = 1; i < p.length; i++) { s += Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]); c.push(s); } return c; }
function along(p, c, d) { d = clamp(d, 0, c[c.length - 1]); let i = 1; while (i < c.length - 1 && c[i] < d) i++; const u = (d - c[i - 1]) / Math.max(1e-6, c[i] - c[i - 1]); return [lerp(p[i - 1][0], p[i][0], u), lerp(p[i - 1][1], p[i][1], u), Math.atan2(p[i][1] - p[i - 1][1], p[i][0] - p[i - 1][0])]; }
function subPath(p, c, d0, d1) { const out = [along(p, c, d0)]; for (let i = 0; i < p.length; i++) if (c[i] > d0 && c[i] < d1) out.push(p[i]); out.push(along(p, c, d1)); return out; }
function strokePath(pts, color, w, o = {}) {
  if (pts.length < 2) return;
  ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = o.blur || 16; }
  if (o.dash) ctx.setLineDash(o.dash);
  if (o.dashOff) ctx.lineDashOffset = o.dashOff;
  ctx.globalAlpha = o.alpha === undefined ? 1 : o.alpha;
  ctx.strokeStyle = color; ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
  ctx.stroke(); ctx.restore();
}
function geoPts(cam, ll) { return ll.map(q => mw(cam, q[0], q[1])); }
function geoStroke(cam, ll, color, w, o = {}) { strokePath(smooth(geoPts(cam, ll), 6), color, w, o); }

// 粗大箭头：沿屏幕路径 pts 画到 frac 处；尾细头粗，带箭头和外发光
function bigArrow(pts, frac, color, w = 34, o = {}) {
  if (frac <= 0.001) return;
  const sp = smooth(pts, 10), c = cumLen(sp), L = c[c.length - 1];
  const from = (o.from || 0) * L, d1 = frac * L;
  if (d1 - from < 4) return;
  const head = Math.min(w * 1.9, (d1 - from) * 0.6), body = subPath(sp, c, from, Math.max(from + 1, d1 - head * 0.75));
  const left = [], right = [];
  const bc = cumLen(body), BL = bc[bc.length - 1];
  for (let i = 0; i < body.length; i++) {
    const a = i < body.length - 1 ? Math.atan2(body[i + 1][1] - body[i][1], body[i + 1][0] - body[i][0]) : Math.atan2(body[i][1] - body[i - 1][1], body[i][0] - body[i - 1][0]);
    const hw = w / 2 * lerp(o.tail === undefined ? 0.35 : o.tail, 1, bc[i] / Math.max(1, BL));
    left.push([body[i][0] + Math.cos(a - Math.PI / 2) * hw, body[i][1] + Math.sin(a - Math.PI / 2) * hw]);
    right.push([body[i][0] + Math.cos(a + Math.PI / 2) * hw, body[i][1] + Math.sin(a + Math.PI / 2) * hw]);
  }
  const tip = along(sp, c, d1), base = along(sp, c, d1 - head), a = tip[2];
  const hw2 = w * 1.05;
  ctx.save();
  ctx.globalAlpha = o.alpha === undefined ? 1 : o.alpha;
  ctx.shadowColor = o.glow || color; ctx.shadowBlur = o.blur === undefined ? 22 : o.blur;
  ctx.beginPath(); ctx.moveTo(left[0][0], left[0][1]);
  for (const q of left) ctx.lineTo(q[0], q[1]);
  ctx.lineTo(base[0] + Math.cos(a - Math.PI / 2) * hw2, base[1] + Math.sin(a - Math.PI / 2) * hw2);
  ctx.lineTo(tip[0], tip[1]);
  ctx.lineTo(base[0] + Math.cos(a + Math.PI / 2) * hw2, base[1] + Math.sin(a + Math.PI / 2) * hw2);
  for (let i = right.length - 1; i >= 0; i--) ctx.lineTo(right[i][0], right[i][1]);
  ctx.closePath();
  const g = ctx.createLinearGradient(sp[0][0], sp[0][1], tip[0], tip[1]);
  g.addColorStop(0, rgba(color, 0.35)); g.addColorStop(0.5, rgba(color, 0.85)); g.addColorStop(1, color);
  ctx.fillStyle = g; ctx.fill();
  ctx.shadowBlur = 0; ctx.lineWidth = 2.5; ctx.strokeStyle = rgba('#ffffff', 0.35); ctx.stroke();
  ctx.restore();
  return tip;
}

// ---------- 文字 ----------
function txt(s, x, y, o = {}) {
  ctx.save();
  ctx.globalAlpha = o.alpha === undefined ? 1 : o.alpha;
  ctx.font = `${o.weight || 600} ${o.size || 48}px ${o.font || SERIF}`;
  ctx.textAlign = o.align || 'center'; ctx.textBaseline = o.base || 'middle';
  if (o.ls) ctx.letterSpacing = o.ls + 'px';
  if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = o.blur || 20; }
  if (o.stroke) { ctx.lineJoin = 'round'; ctx.lineWidth = o.sw || 6; ctx.strokeStyle = o.stroke; ctx.strokeText(s, x, y); }
  ctx.fillStyle = o.color || C.cream; ctx.fillText(s, x, y);
  ctx.restore();
}
function measure(s, size, font = SERIF, weight = 600) { ctx.save(); ctx.font = `${weight} ${size}px ${font}`; const w = ctx.measureText(s).width; ctx.restore(); return w; }
// 按字数自动换行（中文）
function wrapCN(s, maxc) { const out = []; let cur = ''; for (const ch of s) { cur += ch; if (cur.length >= maxc && !'，。！？、；：」』）'.includes(ch)) { out.push(cur); cur = ''; } } if (cur) { if (out.length && cur.length <= 2 && /^[，。！？、；：」』）]+$/.test(cur)) out[out.length - 1] += cur; else out.push(cur); } return out; }
// 优先在标点/空格处断行
function phraseWrap(s, maxc, seps = '，；：、　') {
  const parts = []; let cur = '';
  for (const ch of s) { cur += ch; if (seps.includes(ch)) { parts.push(cur); cur = ''; } }
  if (cur) parts.push(cur);
  const rows = []; let row = '';
  for (const p of parts) {
    const pl = [...p.replace(/[　]+$/, '')].length;
    if ([...row].length + pl <= maxc) row += p;
    else { if (row) rows.push(row); if (pl > maxc) { const sub = balancedWrap(p, maxc); rows.push(...sub.slice(0, -1)); row = sub[sub.length - 1]; } else row = p; }
  }
  if (row) rows.push(row);
  return rows.map(r => r.replace(/^[　]+|[　]+$/g, ''));
}
function balancedWrap(s, maxc) { const n = [...s].length; if (n <= maxc) return [s]; const rows = Math.ceil(n / maxc); return wrapCN(s, Math.ceil(n / rows)); }

// 地名标注：点 + 字
function placeLabel(x, y, name, o = {}) {
  const a = o.alpha === undefined ? 1 : o.alpha; if (a <= 0.01) return;
  ctx.save(); ctx.globalAlpha = a;
  const r = o.r || 9;
  ctx.fillStyle = o.dot || C.cream; ctx.strokeStyle = 'rgba(0,0,0,0.7)'; ctx.lineWidth = 3;
  ctx.beginPath(); if (o.square) ctx.rect(x - r, y - r, 2 * r, 2 * r); else ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
  ctx.restore();
  const dx = o.dx === undefined ? 18 : o.dx, dy = o.dy || 0;
  txt(name, x + dx, y + dy, { size: o.size || 40, align: o.align || 'left', color: o.color || C.cream, stroke: 'rgba(8,8,10,0.85)', sw: 8, alpha: a, weight: o.weight || 700 });
}

// 计数器
function fmtWan(n) { return n >= 10000 ? (Math.round(n / 1000) / 10).toFixed(n >= 100000 ? 0 : 1).replace(/\.0$/, '') + '万' : Math.round(n).toLocaleString(); }

// ---------- 全局叠加层 ----------
function chapterCard(t) {
  for (const [sid, num] of [['s2', '第一层'], ['s3', '第二层'], ['s4', '第三层'], ['s5', '关键一幕'], ['s6', '溃散'], ['s7', '尾声']]) {
    const s = TL.secs[sid]; if (!s) continue;
    const a = fadeIO(t, s.start - 0.3, s.start + 3.6, 0.5, 0.8);
    if (a <= 0) continue;
    const y = 300;
    ctx.save(); ctx.globalAlpha = a * 0.75;
    const g = ctx.createLinearGradient(0, y - 120, 0, y + 120); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(0.5, 'rgba(0,0,0,0.75)'); g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = g; ctx.fillRect(0, y - 120, W, 240); ctx.restore();
    txt(num, W / 2, y - 48, { size: 34, color: C.gold, alpha: a, ls: 8, weight: 700 });
    txt(s.title, W / 2, y + 22, { size: 74, color: C.cream, alpha: a, weight: 800, ls: 6, glow: 'rgba(0,0,0,0.9)', blur: 18 });
    ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = C.gold; ctx.lineWidth = 2; const L = 220 * eout((t - s.start) / 1.2);
    ctx.beginPath(); ctx.moveTo(W / 2 - L, y + 82); ctx.lineTo(W / 2 + L, y + 82); ctx.stroke(); ctx.restore();
  }
}

function subtitle(t) {
  const l = curLine(t); if (!l) return;
  let sub = null;
  for (const s of l.subs) if (t >= s.t0 - 0.05 && t < s.t1 + 0.25) sub = s;
  if (!sub) {
    // 句与句的停顿里保留上一块字幕，直到下一句开始
    if (l.subs.length && t >= l.end && t < N(l.id)) sub = l.subs[l.subs.length - 1]; else return;
  }
  const clean = sub.txt.replace(/[，、；：]/g, '　').replace(/[。]/g, '').replace(/　+$/, '');
  const rows = phraseWrap(clean, 15);
  const size = 54, lh = 74, y0 = 1612 - (rows.length - 1) * lh / 2;
  const a = Math.min(sstep((t - sub.t0 + 0.08) / 0.12), 1);
  rows.forEach((r, i) => txt(r, W / 2, y0 + i * lh, { size, font: SANS, weight: 700, color: '#fbf6ea', stroke: 'rgba(0,0,0,0.88)', sw: 10, alpha: a }));
}

// 古文卡片（LITE：放在上部、背景轻，不遮挡画面主体）
const LITE = new Set(['s5_13', 's7_10']);
function quoteCard(t) {
  for (const l of TL.lines) {
    if (l.k !== 'q' || l.text === '秦兵敗矣！') continue;
    const t0 = l.start - 0.35, t1 = Math.max(l.end + 1.2, Math.min(N(l.id) + 0.6, l.end + 4.5));
    const a = fadeIO(t, t0, t1, 0.45, 0.6); if (a <= 0) continue;
    const lite = LITE.has(l.id);
    const cy = lite ? 560 : 900;
    const rows = phraseWrap(l.text, 10);
    const size = rows.length > 2 ? 72 : 84, lh = size * 1.32;
    const hh = rows.length * lh + 300;
    ctx.save(); ctx.globalAlpha = a * (lite ? 0.3 : 0.86); ctx.fillStyle = '#0c0b09'; ctx.fillRect(0, 0, W, H); ctx.restore();
    ctx.save(); ctx.globalAlpha = a * (lite ? 0.88 : 1);
    const x0 = 70, y0 = cy - hh / 2, ww = W - 140;
    const g = ctx.createLinearGradient(0, y0, 0, y0 + hh); g.addColorStop(0, '#221d15'); g.addColorStop(1, '#16120c');
    ctx.fillStyle = g; ctx.fillRect(x0, y0, ww, hh);
    ctx.strokeStyle = C.goldD; ctx.lineWidth = 3; ctx.strokeRect(x0 + 14, y0 + 14, ww - 28, hh - 28);
    ctx.strokeStyle = rgba(C.gold, 0.4); ctx.lineWidth = 1.5; ctx.strokeRect(x0 + 24, y0 + 24, ww - 48, hh - 48);
    ctx.restore();
    const reveal = clamp((t - l.start) / Math.max(0.6, (l.end - l.start) * 0.85));
    const total = rows.join('').length; let shown = Math.ceil(reveal * total + 0.001);
    rows.forEach((r, i) => {
      const y = y0 + 130 + i * lh;
      const chars = [...r]; const wtot = measure(r, size, SERIF, 800); let x = W / 2 - wtot / 2;
      for (const ch of chars) {
        const cw = measure(ch, size, SERIF, 800);
        const k = shown > 0 ? 1 : 0.12; shown--;
        txt(ch, x + cw / 2, y, { size, weight: 800, color: C.cream, alpha: a * k, glow: 'rgba(226,190,114,0.35)', blur: 14 });
        x += cw;
      }
    });
    const ys = y0 + 130 + rows.length * lh + 6;
    txt('—— ' + l.src, W - 120, ys, { size: 34, align: 'right', color: C.gold, alpha: a, weight: 600 });
    if (l.gloss) {
      const gr = phraseWrap(l.gloss, 18);
      gr.forEach((r, i) => txt(r, W / 2, ys + 78 + i * 52, { size: 38, font: SANS, weight: 500, color: '#d9d2c2', alpha: a * sstep((t - l.end + 0.2) / 0.5) }));
    }
  }
}

function badges(t, o = {}) {
  // 角标：AI 配音（全程），示意 / 情景演绎（按场景）
  const pill = (s, x, y, a) => {
    if (a <= 0) return; ctx.save(); ctx.globalAlpha = a * 0.85; ctx.font = `600 26px ${SANS}`; const w = ctx.measureText(s).width + 28;
    ctx.fillStyle = 'rgba(0,0,0,0.45)'; ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.roundRect(x - w, y - 20, w, 40, 20); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#eee'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(s, x - w / 2, y + 1); ctx.restore();
  };
  pill('AI配音', W - 36, 70, 1);
  pill('示意图', W - 36, 120, o.map || 0);
  pill('情景演绎', W - 36, o.map > 0.01 ? 170 : 120, o.act || 0);
  // 栏目名
  txt('历史的关键一局 · 淝水之战', 40, 70, { size: 30, align: 'left', color: rgba(C.gold, 0.9), weight: 700, ls: 2, stroke: 'rgba(0,0,0,0.6)', sw: 5 });
}

function vignette(a = 0.55) {
  const g = ctx.createRadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 0.75);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${a})`);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  // 字幕区压暗，保证可读
  const g2 = ctx.createLinearGradient(0, 1440, 0, 1780); g2.addColorStop(0, 'rgba(0,0,0,0)'); g2.addColorStop(0.5, 'rgba(0,0,0,0.42)'); g2.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g2; ctx.fillRect(0, 1440, W, 340);
}

// 胶片颗粒（确定性）
let GRAIN;
function grain(t, a = 0.06) {
  if (!GRAIN) { GRAIN = document.createElement('canvas'); GRAIN.width = 270; GRAIN.height = 480; const g = GRAIN.getContext('2d'); const im = g.createImageData(270, 480); const r = rng(7); for (let i = 0; i < im.data.length; i += 4) { const v = r() * 255; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; } g.putImageData(im, 0, 0); }
  const f = Math.floor(t * FPS);
  ctx.save(); ctx.globalAlpha = a; ctx.globalCompositeOperation = 'overlay';
  ctx.drawImage(GRAIN, (f * 37) % 270 - 270, (f * 53) % 480 - 480, 270 * 4 + 270, 480 * 4 + 480);
  ctx.restore();
}
