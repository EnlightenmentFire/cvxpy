// 通用道具：人形、旗、火把、芦苇、鹤、草木、棋盘、木屐……（全部程序绘制）
'use strict';

function figure(x, y, s, color, o = {}) {
  // 简化兵士剪影：头、身、腿、长矛；不画面孔
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.globalAlpha = o.alpha === undefined ? 1 : o.alpha;
  ctx.fillStyle = color; ctx.strokeStyle = color; ctx.lineCap = 'round';
  const run = o.run || 0, ph = o.phase || 0;
  ctx.beginPath(); ctx.arc(0, -62, 11, 0, Math.PI * 2); ctx.fill();
  ctx.beginPath(); ctx.moveTo(-13, -48); ctx.lineTo(13, -48); ctx.lineTo(9 + run * 6, -12); ctx.lineTo(-9 + run * 6, -12); ctx.closePath(); ctx.fill();
  ctx.lineWidth = 7;
  const sw = Math.sin(ph) * 14 * (0.3 + run);
  ctx.beginPath(); ctx.moveTo(-5 + run * 6, -14); ctx.lineTo(-7 + sw, 0); ctx.moveTo(5 + run * 6, -14); ctx.lineTo(7 - sw, 0); ctx.stroke();
  if (!o.noSpear) { ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(16, -90 + run * 30); ctx.lineTo(16 - run * 20, 0); ctx.stroke(); }
  ctx.restore();
}

function banner(x, y, h, color, ch, t, o = {}) {
  // 旗杆底部 (x,y)，高 h；o.rot 旗杆倾倒角
  ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot || 0); ctx.globalAlpha = o.alpha === undefined ? 1 : o.alpha;
  ctx.strokeStyle = '#2a2018'; ctx.lineWidth = h * 0.018 + 2; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, -h); ctx.stroke();
  const fw = h * 0.5, fh = h * 0.36;
  ctx.beginPath(); ctx.moveTo(0, -h);
  const n = 16;
  for (let i = 0; i <= n; i++) { const u = i / n; ctx.lineTo(u * fw, -h + Math.sin(t * 3.2 - u * 4) * fh * 0.08 * u); }
  for (let i = n; i >= 0; i--) { const u = i / n; ctx.lineTo(u * fw, -h + fh + Math.sin(t * 3.2 - u * 4 + 0.6) * fh * 0.08 * u); }
  ctx.closePath();
  const g = ctx.createLinearGradient(0, -h, fw, -h + fh); g.addColorStop(0, color); g.addColorStop(1, mix(color, '#000000', 0.45));
  ctx.fillStyle = g; ctx.fill();
  ctx.strokeStyle = rgba(C.gold, 0.8); ctx.lineWidth = Math.max(2, h * 0.008); ctx.stroke();
  if (ch) { ctx.save(); ctx.translate(fw * 0.5, -h + fh * 0.52); ctx.font = `900 ${fh * 0.62}px ${SERIF}`; ctx.fillStyle = C.cream; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(ch, 0, 0); ctx.restore(); }
  ctx.restore();
}

function torchGlow(x, y, r, a, warm = 1) {
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, `rgba(255,${200 + 30 * warm | 0},140,${a})`); g.addColorStop(0.25, `rgba(255,150,60,${a * 0.55})`); g.addColorStop(1, 'rgba(255,120,40,0)');
  ctx.fillStyle = g; ctx.fillRect(x - r, y - r, 2 * r, 2 * r);
}

function reeds(t, y0, n, h, color, seed = 1, wind = 1) {
  ctx.save(); ctx.strokeStyle = color; ctx.lineCap = 'round';
  for (let i = 0; i < n; i++) {
    const x = hash(i, seed) * (W + 80) - 40, hh = h * (0.55 + 0.6 * hash(i, seed + 1));
    const bend = (Math.sin(t * 1.6 * wind + i * 0.7) * 0.5 + 0.7) * 0.25 * wind;
    ctx.lineWidth = 2 + 3 * hash(i, seed + 2);
    ctx.beginPath(); ctx.moveTo(x, y0); ctx.quadraticCurveTo(x + hh * bend * 0.3, y0 - hh * 0.6, x + hh * bend, y0 - hh); ctx.stroke();
    if (hash(i, seed + 3) > 0.6) { ctx.fillStyle = color; ctx.beginPath(); ctx.ellipse(x + hh * bend, y0 - hh, 5, 22, bend + 0.2, 0, Math.PI * 2); ctx.fill(); }
  }
  ctx.restore();
}

function crane(x, y, s, t, alpha = 1) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.globalAlpha = alpha; ctx.fillStyle = '#0d0f14'; ctx.strokeStyle = '#0d0f14';
  const f = Math.sin(t * 5) * 0.6;
  ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(-40, 0); ctx.lineTo(48, -4); ctx.stroke();               // 身+颈
  ctx.beginPath(); ctx.moveTo(48, -4); ctx.lineTo(62, -2); ctx.stroke();                                    // 喙
  ctx.beginPath(); ctx.moveTo(-40, 0); ctx.lineTo(-78, 6); ctx.stroke();                                    // 腿
  ctx.beginPath(); ctx.moveTo(0, 0); ctx.quadraticCurveTo(-10, -50 * f - 10, -30, -90 * f); ctx.quadraticCurveTo(-5, -30 * f, 14, 0); ctx.fill();
  ctx.restore();
}

// 草木 ⇄ 人形：u=0 草木，u=1 人形
function grassMan(x, y, s, u, seed, color) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.fillStyle = color; ctx.strokeStyle = color; ctx.lineCap = 'round';
  const k = hash(seed, 3);
  if (u < 0.999) {
    ctx.globalAlpha = 1 - u;
    if (k > 0.5) { // 小树
      ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, -40); ctx.stroke();
      ctx.beginPath(); ctx.ellipse(0, -62, 26, 32, 0, 0, Math.PI * 2); ctx.fill();
    } else { // 草丛
      ctx.lineWidth = 4;
      for (let j = 0; j < 7; j++) { const a = -Math.PI / 2 + (j - 3) * 0.22; ctx.beginPath(); ctx.moveTo(0, 0); ctx.quadraticCurveTo(Math.cos(a) * 30, -40, Math.cos(a) * 46, -60 - 20 * hash(seed, j)); ctx.stroke(); }
    }
  }
  if (u > 0.001) { ctx.globalAlpha = u; ctx.restore(); figure(x, y, s * 0.95, color, { alpha: u }); return; }
  ctx.restore();
}

function goBoard(cx, cy, size, rot = 0) {
  ctx.save(); ctx.translate(cx, cy); ctx.rotate(rot);
  const g = ctx.createLinearGradient(-size, -size, size, size); g.addColorStop(0, '#c99a58'); g.addColorStop(1, '#a87a3e');
  ctx.fillStyle = g; ctx.fillRect(-size, -size, 2 * size, 2 * size);
  // 木纹
  ctx.globalAlpha = 0.12; ctx.strokeStyle = '#5a3a14';
  for (let i = 0; i < 40; i++) { ctx.lineWidth = 1 + 2 * hash(i, 4); ctx.beginPath(); const y = -size + 2 * size * hash(i, 5); ctx.moveTo(-size, y); ctx.bezierCurveTo(-size / 2, y + 20 * hash(i, 6) - 10, size / 2, y - 20 * hash(i, 7) + 10, size, y + 8); ctx.stroke(); }
  ctx.globalAlpha = 0.85; ctx.strokeStyle = '#2d1c0a'; ctx.lineWidth = 2;
  const st = 2 * size / 10;
  for (let i = 0; i <= 10; i++) { ctx.beginPath(); ctx.moveTo(-size + st * 0.5, -size + st * (i + 0.5)); ctx.lineTo(size, -size + st * (i + 0.5)); ctx.stroke(); ctx.beginPath(); ctx.moveTo(-size + st * (i + 0.5), -size + st * 0.5); ctx.lineTo(-size + st * (i + 0.5), size); ctx.stroke(); }
  ctx.restore();
  return (i, j) => { const st2 = 2 * size / 10; const lx = -size + st2 * (i + 0.5), ly = -size + st2 * (j + 0.5); return [cx + lx * Math.cos(rot) - ly * Math.sin(rot), cy + lx * Math.sin(rot) + ly * Math.cos(rot), st2]; };
}
function stone(x, y, r, black, a = 1) {
  ctx.save(); ctx.globalAlpha = a;
  ctx.shadowColor = 'rgba(0,0,0,0.5)'; ctx.shadowBlur = r * 0.5; ctx.shadowOffsetY = r * 0.15;
  const g = ctx.createRadialGradient(x - r * 0.35, y - r * 0.35, r * 0.1, x, y, r);
  if (black) { g.addColorStop(0, '#666'); g.addColorStop(1, '#0a0a0a'); } else { g.addColorStop(0, '#ffffff'); g.addColorStop(1, '#c9c4b8'); }
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fill(); ctx.restore();
}

// 木屐侧视：鞋板 + 前后两齿；brk 0..1 前齿折断飞出
function clog(x, y, s, brk, t) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
  const wood = ctx.createLinearGradient(0, -30, 0, 60); wood.addColorStop(0, '#b98d55'); wood.addColorStop(1, '#6e4c25');
  // 鞋板
  ctx.fillStyle = wood; ctx.strokeStyle = '#2b1a08'; ctx.lineWidth = 3;
  ctx.beginPath(); ctx.roundRect(-210, -28, 420, 40, 14); ctx.fill(); ctx.stroke();
  // 系带
  ctx.strokeStyle = '#5a1a12'; ctx.lineWidth = 12; ctx.beginPath(); ctx.moveTo(-60, -28); ctx.quadraticCurveTo(40, -120, 150, -28); ctx.stroke();
  // 后齿
  ctx.fillStyle = wood; ctx.strokeStyle = '#2b1a08'; ctx.lineWidth = 3;
  ctx.beginPath(); ctx.rect(-150, 12, 46, 92); ctx.fill(); ctx.stroke();
  // 前齿（折断）
  if (brk <= 0) { ctx.beginPath(); ctx.rect(104, 12, 46, 92); ctx.fill(); ctx.stroke(); }
  else {
    ctx.beginPath(); ctx.rect(104, 12, 46, 22); ctx.fill(); ctx.stroke();            // 残根
    // 断口
    ctx.strokeStyle = '#e8d2a6'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(104, 34); for (let i = 0; i <= 6; i++) ctx.lineTo(104 + i * 46 / 6, 34 + (i % 2 ? 5 : -3)); ctx.stroke();
    const u = eout(brk);
    ctx.save(); ctx.translate(127 + 160 * u, 70 + 140 * u * u); ctx.rotate(1.9 * u);
    ctx.fillStyle = wood; ctx.strokeStyle = '#2b1a08'; ctx.lineWidth = 3; ctx.beginPath(); ctx.rect(-23, -36, 46, 70); ctx.fill(); ctx.stroke();
    ctx.restore();
    // 木屑
    for (let i = 0; i < 9; i++) { const a = -0.8 + 1.6 * hash(i, 2); const d = 40 + 120 * hash(i, 3); ctx.fillStyle = `rgba(222,190,140,${(1 - u) * 0.9})`; ctx.fillRect(127 + Math.cos(a) * d * u, 34 + Math.sin(a) * d * u, 5, 5); }
  }
  ctx.restore();
}

function letterIcon(x, y, s, color = C.paper, rot = 0, a = 1) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s); ctx.globalAlpha = a;
  ctx.fillStyle = color; ctx.strokeStyle = '#3a2a14'; ctx.lineWidth = 2.5;
  ctx.beginPath(); ctx.rect(-60, -40, 120, 80); ctx.fill(); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-60, -40); ctx.lineTo(0, 8); ctx.lineTo(60, -40); ctx.stroke();
  ctx.fillStyle = '#9c2a18'; ctx.beginPath(); ctx.arc(0, 8, 10, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}

function tent(x, y, s, color, a = 1) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.globalAlpha = a;
  ctx.fillStyle = color; ctx.beginPath(); ctx.moveTo(-160, 0); ctx.lineTo(0, -170); ctx.lineTo(160, 0); ctx.closePath(); ctx.fill();
  ctx.fillStyle = 'rgba(0,0,0,0.45)'; ctx.beginPath(); ctx.moveTo(-30, 0); ctx.lineTo(0, -80); ctx.lineTo(30, 0); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = '#1a1208'; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(0, -170); ctx.lineTo(0, -215); ctx.stroke();
  ctx.restore();
}

// 圆角面板
function panel(x, y, w, h, a = 0.7, border = C.goldD) {
  ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = '#0e0d0b'; ctx.beginPath(); ctx.roundRect(x, y, w, h, 18); ctx.fill();
  ctx.globalAlpha = Math.min(1, a * 1.2); ctx.strokeStyle = border; ctx.lineWidth = 2; ctx.stroke(); ctx.restore();
}
// 小号引文框（场景内的次要原文）
function miniQuote(t, t0, t1, text, src, y = 1180) {
  const a = fadeIO(t, t0, t1, 0.4, 0.5); if (a <= 0) return;
  const rows = phraseWrap(text, 12);
  const h = rows.length * 70 + 100;
  panel(80, y - h / 2, W - 160, h, a * 0.82);
  rows.forEach((r, i) => txt(r, W / 2, y - h / 2 + 62 + i * 70, { size: 54, weight: 800, color: C.cream, alpha: a }));
  txt('—— ' + src, W - 120, y + h / 2 - 34, { size: 28, align: 'right', color: C.gold, alpha: a });
}
// 标题字条
function caption(s, y, t, t0, t1, o = {}) {
  const a = fadeIO(t, t0, t1, o.fi || 0.4, o.fo || 0.5); if (a <= 0) return;
  txt(s, o.x || W / 2, y, { size: o.size || 60, weight: o.weight || 800, color: o.color || C.cream, alpha: a, glow: o.glow || 'rgba(0,0,0,0.95)', blur: 22, align: o.align, ls: o.ls, font: o.font, stroke: o.stroke, sw: o.sw });
}
