// 通用组件：人物卡、季节天色、粒子、示意图（城防四重、水井剖面、地道）、信、奏表
'use strict';

// ---------- 人物卡（文字卡，不画肖像） ----------
// o: name, role, sub, bar(色条), w, h, alpha, off(0..1 熄灭), note(熄灭后的小字), lit(0..1 高亮)
function pcard(cx, cy, o = {}) {
  const w = o.w || 400, h = o.h || 168, a = o.alpha === undefined ? 1 : o.alpha; if (a <= 0.003) return;
  const off = clamp(o.off || 0), lit = clamp(o.lit || 0);
  ctx.save(); ctx.globalAlpha *= a; ctx.translate(cx, cy);
  if (lit > 0 && off < 1) { ctx.shadowColor = o.glow || 'rgba(224,73,47,0.75)'; ctx.shadowBlur = 34 * lit * (1 - off); }
  rrect(-w / 2, -h / 2, w, h, 10); ctx.fillStyle = `rgba(${lerp(20, 9, off)},${lerp(17, 9, off)},${lerp(14, 10, off)},0.93)`; ctx.fill(); ctx.shadowBlur = 0;
  ctx.strokeStyle = `rgba(216,180,106,${lerp(0.45, 0.1, off)})`; ctx.lineWidth = 1.5; rrect(-w / 2, -h / 2, w, h, 10); ctx.stroke();
  ctx.globalAlpha *= lerp(1, 0.28, off);
  ctx.fillStyle = o.bar || C.red; ctx.fillRect(-w / 2, -h / 2, 7, h);
  ctx.restore();
  const ta = a * lerp(1, 0.3, off), big = o.size || 56;
  const hasSub = !!o.sub, y0 = cy - (o.role ? (hasSub ? 34 : 20) : 0);
  text(o.name, cx - w / 2 + 34, y0, { size: big, fam: SERIF, wt: 900, alpha: ta, stroke: 0, color: off > 0.5 ? '#9a948a' : C.cream });
  if (o.role) text(o.role, cx - w / 2 + 36, y0 + big * 0.86, { size: 28, wt: 700, alpha: ta, stroke: 0, color: off > 0.5 ? '#8a8479' : C.gold });
  if (hasSub) text(o.sub, cx - w / 2 + 36, y0 + big * 0.86 + 38, { size: 24, wt: 500, alpha: ta * 0.9, stroke: 0, color: C.dimtxt });
  if (o.tag) { const tw_ = measure(o.tag, 24, SANS, 700) + 22; ctx.save(); ctx.globalAlpha = ta; rrect(cx + w / 2 - tw_ - 14, cy - h / 2 + 14, tw_, 36, 5); ctx.fillStyle = 'rgba(241,231,210,0.12)'; ctx.fill(); ctx.restore(); text(o.tag, cx + w / 2 - 25, cy - h / 2 + 33, { size: 24, wt: 700, alpha: ta, stroke: 0, align: 'right', color: C.cream }); }
  if (o.note && off > 0.05) text(o.note, cx, cy + h / 2 + 30, { size: 26, wt: 500, alpha: a * off * 0.95, align: 'center', color: '#b9b2a6', stroke: 5 });
}
// 卡片之间的虚线（提防）
function wary(x0, y0, x1, y1, a = 1, t = 0, color = 'rgba(224,73,47,0.9)', lw = 3) {
  if (a <= 0) return; ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = color; ctx.lineWidth = lw; ctx.setLineDash([10, 12]); ctx.lineDashOffset = -t * 14;
  ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke(); ctx.restore();
}
function panel(x, y, w, h, a = 1, fill = 'rgba(14,12,10,0.86)') { if (a <= 0) return; ctx.save(); ctx.globalAlpha *= a; rrect(x, y, w, h, 10); ctx.fillStyle = fill; ctx.fill(); ctx.strokeStyle = 'rgba(216,180,106,0.3)'; ctx.lineWidth = 1.5; rrect(x, y, w, h, 10); ctx.stroke(); ctx.restore(); }

// ---------- 季节与天色 ----------
function season(kind, a = 1) {
  if (a <= 0) return; ctx.save();
  if (kind === 'winter') { ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = `rgba(${lerp(255, 150, a)},${lerp(255, 172, a)},${lerp(255, 205, a)},1)`; ctx.fillRect(0, 0, W, H); }
  else if (kind === 'summer') { ctx.globalCompositeOperation = 'overlay'; ctx.fillStyle = `rgba(255,186,96,${0.2 * a})`; ctx.fillRect(0, 0, W, H); ctx.globalCompositeOperation = 'source-over'; const g = ctx.createRadialGradient(W * 0.72, 300, 40, W * 0.72, 300, 900); g.addColorStop(0, `rgba(255,214,150,${0.2 * a})`); g.addColorStop(1, 'rgba(255,214,150,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); }
  else if (kind === 'night') { ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = `rgba(${lerp(255, 92, a)},${lerp(255, 104, a)},${lerp(255, 132, a)},1)`; ctx.fillRect(0, 0, W, H); }
  ctx.restore();
}
// 风雪：斜向飘落的细粒
function snow(t, a = 1, n = 260, wind = 1) {
  if (a <= 0) return; ctx.save(); ctx.fillStyle = '#e9eef4';
  for (let i = 0; i < n; i++) {
    const sp = 90 + 190 * hash(i, 1), z = 0.4 + 0.6 * hash(i, 2);
    const x = ((hash(i, 3) * (W + 500) + t * sp * 1.5 * wind + 60 * Math.sin(t * 0.7 + i)) % (W + 500)) - 250;
    const y = ((hash(i, 4) * (H + 100) + t * sp * z) % (H + 100)) - 50;
    ctx.globalAlpha = a * (0.18 + 0.5 * hash(i, 5)) * z; const r = 1.2 + 2.2 * z * hash(i, 6);
    ctx.beginPath(); ctx.ellipse(x, y, r * (1 + wind * 1.3), r, 0.5, 0, 7); ctx.fill();
  }
  ctx.restore();
}
// 尘：缓慢浮动的暖色微粒（夏日）
function dust(t, a = 1, n = 90) {
  if (a <= 0) return; ctx.save(); ctx.fillStyle = '#f2d9a8';
  for (let i = 0; i < n; i++) { const x = (hash(i, 7) * W + 18 * Math.sin(t * 0.3 + i * 1.7) + t * 6) % W, y = (hash(i, 8) * H + 14 * Math.cos(t * 0.25 + i)) % H; ctx.globalAlpha = a * (0.05 + 0.12 * hash(i, 9)); ctx.beginPath(); ctx.arc(x, y, 1 + 2 * hash(i, 10), 0, 7); ctx.fill(); }
  ctx.restore();
}

// ---------- 军队：密集兵点（确定性抖动） ----------
function dots(cx, cy, n, rx, ry, color, o = {}) {
  ctx.save(); ctx.fillStyle = color; const a = o.alpha === undefined ? 1 : o.alpha, r = o.r || 3, seed = o.seed || 0, keep = o.keep === undefined ? 1 : o.keep;
  for (let i = 0; i < n; i++) {
    if (hash(i, seed + 11) > keep) continue;
    const ang = hash(i, seed + 1) * 6.283, rad = Math.sqrt(hash(i, seed + 2));
    let x = cx + Math.cos(ang) * rad * rx, y = cy + Math.sin(ang) * rad * ry;
    if (o.jit) { x += Math.sin(o.jit * (1 + hash(i, seed + 3)) + i) * 2; y += Math.cos(o.jit * (1 + hash(i, seed + 4)) + i * 2) * 2; }
    if (o.spread) { x += Math.cos(ang) * o.spread * (0.4 + hash(i, seed + 5)); y += Math.sin(ang) * o.spread * (0.4 + hash(i, seed + 5)); }
    ctx.globalAlpha = a * (0.55 + 0.45 * hash(i, seed + 6)); ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill();
    if (o.edge) { ctx.strokeStyle = o.edge; ctx.lineWidth = 1; ctx.stroke(); }
  }
  ctx.restore();
}
// 魏军营垒：玄黑方块 + 浅描边
function weiBlock(x, y, w, h, a = 1, name) {
  if (a <= 0) return; ctx.save(); ctx.globalAlpha *= a; ctx.shadowColor = 'rgba(0,0,0,0.7)'; ctx.shadowBlur = 12; ctx.fillStyle = C.wei; rrect(x - w / 2, y - h / 2, w, h, 4); ctx.fill(); ctx.shadowBlur = 0;
  ctx.strokeStyle = 'rgba(201,211,220,0.75)'; ctx.lineWidth = 2; rrect(x - w / 2, y - h / 2, w, h, 4); ctx.stroke(); ctx.restore();
  if (name) text(name, x, y + 1, { size: 24, wt: 700, align: 'center', stroke: 0, color: C.weiE, alpha: a });
}

// ---------- 示意图：水井剖面 ----------
// u: 图整体显现 0..1；tun: 地道掘进 0..1；lvl: 井内水位 1..0
function wellDiagram(t, o = {}) {
  const a = o.alpha === undefined ? 1 : o.alpha; if (a <= 0.003) return;
  const tun = clamp(o.tun || 0), lvl = clamp(o.lvl === undefined ? 1 : o.lvl), ox = o.ox || 0, oy = o.oy || 0, sc = o.sc || 1;
  ctx.save(); ctx.globalAlpha *= a; ctx.translate(W / 2 + ox, 960 + oy); ctx.scale(sc, sc); ctx.translate(-W / 2, -960);
  // 山体剖面：左（北）临河陡崖，右（南）缓坡
  const top = 700, base = 1290;
  const prof = [[-40, base], [-40, 1230], [150, 1225], [210, 1150], [250, 980], [300, 800], [360, 720], [470, top], [700, top], [800, 730], [900, 820], [1000, 900], [1080, 930], [1080, base]];
  const g = ctx.createLinearGradient(0, top, 0, base); g.addColorStop(0, '#5a4c36'); g.addColorStop(0.5, '#3b3226'); g.addColorStop(1, '#1d1a15');
  ctx.beginPath(); prof.forEach((p, i) => i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])); ctx.closePath(); ctx.fillStyle = g; ctx.fill();
  ctx.strokeStyle = 'rgba(216,180,106,0.55)'; ctx.lineWidth = 2.5; ctx.beginPath(); prof.slice(1, -1).forEach((p, i) => i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])); ctx.stroke();
  // 土层纹理
  ctx.strokeStyle = 'rgba(0,0,0,0.16)'; ctx.lineWidth = 2; for (let k = 0; k < 9; k++) { const y = 780 + k * 56; ctx.beginPath(); ctx.moveTo(250 + 30 * Math.sin(k), y); for (let x = 250; x <= 1060; x += 60) ctx.lineTo(x, y + 9 * Math.sin(x * 0.011 + k * 1.3)); ctx.stroke(); }
  // 河
  ctx.fillStyle = '#7d744f'; ctx.fillRect(-40, 1228, 200, 12); ctx.fillStyle = 'rgba(125,116,79,0.35)'; ctx.fillRect(-40, 1240, 222, 50);
  { const gb = ctx.createLinearGradient(0, 1210, 0, 1296); gb.addColorStop(0, 'rgba(13,12,11,0)'); gb.addColorStop(1, 'rgba(13,12,11,1)'); ctx.fillStyle = gb; ctx.fillRect(-60, 1210, 1200, 90); }
  // 城墙与雉堞
  ctx.fillStyle = '#b9a47a'; ctx.fillRect(455, top - 46, 16, 46); ctx.fillRect(700, top - 46, 16, 46); ctx.fillRect(455, top - 46, 261, 6);
  for (let x = 458; x < 712; x += 22) ctx.fillRect(x, top - 56, 11, 10);
  // 井
  const wx = 600, wb = 1180, ww = 26;
  ctx.fillStyle = '#0d0c0b'; ctx.fillRect(wx - ww / 2, top - 6, ww, wb - top + 6);
  ctx.strokeStyle = 'rgba(216,180,106,0.6)'; ctx.lineWidth = 2; ctx.strokeRect(wx - ww / 2, top - 6, ww, wb - top + 6);
  ctx.fillStyle = '#b9a47a'; ctx.fillRect(wx - 26, top - 16, 52, 10);
  const wh = 150 * lvl; if (wh > 1) { ctx.fillStyle = '#5f8fa0'; ctx.fillRect(wx - ww / 2 + 2, wb - wh, ww - 4, wh); ctx.fillStyle = 'rgba(200,230,240,0.5)'; ctx.fillRect(wx - ww / 2 + 2, wb - wh, ww - 4, 3); }
  // 地道（示意）：自城外坡下斜掘至井底
  const p0 = [985, 890], p1 = [wx + ww / 2, wb - 10], f = tun;
  if (f > 0) {
    const ex = lerp(p0[0], p1[0], f), ey = lerp(p0[1], p1[1], f);
    ctx.strokeStyle = '#0b0b0c'; ctx.lineWidth = 15; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(p0[0], p0[1]); ctx.lineTo(ex, ey); ctx.stroke();
    ctx.strokeStyle = 'rgba(201,211,220,0.75)'; ctx.lineWidth = 2; ctx.setLineDash([9, 9]); ctx.beginPath(); ctx.moveTo(p0[0], p0[1]); ctx.lineTo(ex, ey); ctx.stroke(); ctx.setLineDash([]);
    if (f >= 1 && lvl > 0.02 && lvl < 0.99) { ctx.fillStyle = 'rgba(120,170,190,0.85)'; for (let k = 0; k < 7; k++) { const u = ((t * 0.5 + k / 7) % 1); ctx.beginPath(); ctx.arc(lerp(p1[0], p0[0], u), lerp(p1[1], p0[1], u), 3.2, 0, 7); ctx.fill(); } }
  }
  ctx.restore();
  // 标注
  const L_ = (s, x, y, al, opt) => { const X = W / 2 + ox + (x - W / 2) * sc, Y = 960 + oy + (y - 960) * sc; text(s, X, Y, Object.assign({ size: 28, wt: 700, alpha: a * al, color: C.cream }, opt || {})); };
  L_('虎牢城', 585, top - 86, 1, { align: 'center', fam: SERIF, wt: 900, size: 38 });
  L_('黄河', 104, 1196, 0.9, { align: 'center', size: 24, color: '#d2c497' });
  L_('北', 70, 660, 0.7, { align: 'center', size: 22 }); L_('南', 1010, 660, 0.7, { align: 'center', size: 22 });
  if (o.depth !== 0) {
    ctx.save(); ctx.globalAlpha = a * (o.depth === undefined ? 1 : o.depth); const X = W / 2 + ox + (540 - W / 2) * sc, Y0 = 960 + oy + (top - 960) * sc, Y1 = 960 + oy + (1180 - 960) * sc;
    ctx.strokeStyle = C.gold; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(X, Y0); ctx.lineTo(X, Y1); ctx.moveTo(X - 9, Y0); ctx.lineTo(X + 9, Y0); ctx.moveTo(X - 9, Y1); ctx.lineTo(X + 9, Y1); ctx.stroke(); ctx.restore();
    L_('井深四十丈', 524, 950, o.depth === undefined ? 1 : o.depth, { align: 'right', color: C.gold, size: 30, fam: SERIF, wt: 900 });
  }
  if (tun > 0.15) L_('魏军地道', 880, 1010, Math.min(1, (tun - 0.15) * 4), { align: 'center', color: C.weiE, size: 26 });
}

// ---------- 示意图：四重城 ----------
// broken: [外, 二, 三, 内] 各 0..1；shown: 各圈显现 0..1；core: 内城亮度
function ringPath(cx, cy, r, k) {
  ctx.beginPath(); const n = 72;
  for (let i = 0; i <= n; i++) { const a = i / n * 6.2832, rr = r * (1 + 0.035 * Math.sin(a * 3 + k * 1.7) + 0.025 * Math.sin(a * 5 + k)); const sq = Math.pow(Math.abs(Math.cos(a)) ** 4 + Math.abs(Math.sin(a)) ** 4, -0.25); const x = cx + Math.cos(a) * rr * sq, y = cy + Math.sin(a) * rr * sq * 0.92; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
}
const RING_R = [400, 300, 215, 132];
function walls(cx, cy, o = {}) {
  const a = o.alpha === undefined ? 1 : o.alpha; if (a <= 0.003) return; const br = o.broken || [0, 0, 0, 0], sh = o.shown || [1, 1, 1, 1], sc = o.sc || 1, t = o.t || 0;
  ctx.save(); ctx.globalAlpha *= a;
  for (let k = 0; k < 4; k++) {
    if (sh[k] <= 0) continue; const r = RING_R[k] * sc, b = clamp(br[k]);
    ctx.save(); ctx.globalAlpha *= sh[k];
    // 城内地面
    if (k === 3) { ringPath(cx, cy, r, k); ctx.fillStyle = `rgba(224,73,47,${0.10 * (o.core === undefined ? 1 : o.core) * (1 - b)})`; ctx.fill(); }
    ringPath(cx, cy, r, k);
    ctx.lineWidth = (k === 0 ? 15 : 11) * sc; ctx.lineJoin = 'round';
    if (b > 0) { const seg = 46 - 26 * b, gap = 4 + 40 * b; ctx.setLineDash([seg, gap]); ctx.lineDashOffset = k * 17; }
    const cr = Math.round(lerp(224, 104, b)), cg = Math.round(lerp(73, 98, b)), cb = Math.round(lerp(47, 92, b));
    ctx.strokeStyle = `rgb(${cr},${cg},${cb})`; if (b < 0.5) { ctx.shadowColor = 'rgba(224,73,47,0.55)'; ctx.shadowBlur = 16 * (1 - b * 2) * (k === 3 ? (o.core === undefined ? 1 : o.core) : 1); }
    ctx.globalAlpha *= lerp(1, 0.8, b) * (k === 3 ? lerp(0.25, 1, o.core === undefined ? 1 : o.core) : 1);
    ctx.stroke(); ctx.restore();
  }
  ctx.restore();
}

// ---------- 信（涂改痕迹，纯示意，不拟内容） ----------
function letter(cx, cy, o = {}) {
  const a = o.alpha === undefined ? 1 : o.alpha; if (a <= 0.003) return; const w = o.w || 420, h = o.h || 560, wr = clamp(o.write === undefined ? 1 : o.write), fix = clamp(o.fix || 0);
  ctx.save(); ctx.globalAlpha *= a; ctx.translate(cx, cy); ctx.rotate(o.rot || 0);
  ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = 30; ctx.fillStyle = '#cdbb94'; ctx.fillRect(-w / 2, -h / 2, w, h); ctx.shadowBlur = 0;
  const g = ctx.createLinearGradient(-w / 2, 0, w / 2, 0); g.addColorStop(0, 'rgba(90,70,40,0.25)'); g.addColorStop(0.5, 'rgba(90,70,40,0)'); g.addColorStop(1, 'rgba(90,70,40,0.3)'); ctx.fillStyle = g; ctx.fillRect(-w / 2, -h / 2, w, h);
  // 竖排字迹（以短划代字）
  const cols = 8, rows = 15, dx = (w - 80) / (cols - 1), dy = (h - 90) / rows; let idx = 0; const total = cols * rows;
  for (let c = 0; c < cols; c++) for (let r = 0; r < rows; r++) {
    const x = w / 2 - 40 - c * dx, y = -h / 2 + 50 + r * dy; idx++;
    if (idx / total > wr || (c === cols - 1 && r > 8)) continue;
    const k = c * 31 + r; ctx.fillStyle = 'rgba(28,22,16,0.86)'; const ww = 16 + 8 * hash(k, 1), hh = 13 + 7 * hash(k, 2);
    ctx.fillRect(x - ww / 2, y - hh / 2, ww, 3.2); ctx.fillRect(x - 1.6, y - hh / 2, 3.2, hh); if (hash(k, 3) > 0.45) ctx.fillRect(x - ww / 2, y + hh / 2 - 3, ww * 0.8, 3); if (hash(k, 4) > 0.6) ctx.fillRect(x + ww / 2 - 4, y - hh / 3, 3, hh * 0.7);
    // 涂改：墨团、勾划、旁添小字
    const mark = hash(k, 5) < 0.2 && fix > hash(k, 6) * 0.8;
    if (mark) { const m = hash(k, 7); ctx.fillStyle = 'rgba(14,10,8,0.92)'; if (m < 0.45) { ctx.beginPath(); ctx.ellipse(x, y, ww * 0.72, hh * 0.62, hash(k, 8), 0, 7); ctx.fill(); } else if (m < 0.8) { ctx.save(); ctx.strokeStyle = 'rgba(14,10,8,0.95)'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(x - ww * 0.8, y - hh * 0.5); ctx.lineTo(x + ww * 0.8, y + hh * 0.5); ctx.moveTo(x + ww * 0.8, y - hh * 0.5); ctx.lineTo(x - ww * 0.8, y + hh * 0.5); ctx.stroke(); ctx.restore(); } ctx.fillStyle = 'rgba(28,22,16,0.8)'; ctx.fillRect(x + ww * 0.75, y - 4, 8, 2.6); ctx.fillRect(x + ww * 0.75 + 3, y - 8, 2.6, 10); }
  }
  ctx.restore();
}

// ---------- 城楼剪影 ----------
function towerSilhouette(a = 1, y0 = 1560) {
  if (a <= 0) return; ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = '#060607';
  ctx.fillRect(0, y0, W, H - y0); for (let x = 0; x < W; x += 54) ctx.fillRect(x, y0 - 24, 30, 24);
  const cx = 540; ctx.fillRect(cx - 190, y0 - 150, 380, 150);
  const roof = (yy, hw, th) => { ctx.beginPath(); ctx.moveTo(cx - hw - 46, yy + 8); ctx.quadraticCurveTo(cx - hw + 10, yy - 2, cx - hw * 0.62, yy - th); ctx.lineTo(cx + hw * 0.62, yy - th); ctx.quadraticCurveTo(cx + hw - 10, yy - 2, cx + hw + 46, yy + 8); ctx.closePath(); ctx.fill(); };
  roof(y0 - 150, 210, 42); ctx.fillRect(cx - 132, y0 - 290, 264, 100); roof(y0 - 290, 150, 50);
  // 城楼上的人影（极小，背向观众）
  ctx.beginPath(); ctx.arc(cx + 250, y0 - 62, 9, 0, 7); ctx.fill(); ctx.fillRect(cx + 242, y0 - 54, 16, 34);
  ctx.restore();
}
