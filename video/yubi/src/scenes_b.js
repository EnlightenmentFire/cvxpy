// 场景（中）：肆 软的接硬的、伍 关西男子、陆 五十天
'use strict';

// ---------- 侧视舞台：左边城外，右边城墙 ----------
const GY = 1180;     // 地面
function stageBG(t, o = {}) {
  const g = ctx.createLinearGradient(0, 560, 0, GY); g.addColorStop(0, '#171a1d'); g.addColorStop(1, '#2a2620'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, GY);
  ctx.fillStyle = '#231c15'; ctx.fillRect(0, GY, W, H - GY);
  if (o.under) { const gg = ctx.createLinearGradient(0, GY, 0, 1420); gg.addColorStop(0, '#4a3a28'); gg.addColorStop(1, '#2b2219'); ctx.fillStyle = gg; ctx.fillRect(0, GY, W, 260); for (let i = 0; i < 90; i++) { ctx.fillStyle = `rgba(20,14,10,${0.25 * hash(i, 4)})`; ctx.fillRect(hash(i, 1) * W, GY + hash(i, 2) * 240, 30 + 60 * hash(i, 3), 3); } }
  ctx.strokeStyle = 'rgba(244,234,214,0.35)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(0, GY); ctx.lineTo(W, GY); ctx.stroke();
}
function wallSide(x0, top, o = {}) {       // 夯土城墙侧面（x0 起向右）
  const breach = o.breach || null;
  ctx.save();
  ctx.fillStyle = '#5c4029';
  if (!breach) ctx.fillRect(x0, top, W - x0, GY - top);
  else { ctx.fillRect(x0, top, breach[0] - x0, GY - top); ctx.fillRect(breach[1], top, W - breach[1], GY - top); const drop = breach[2]; ctx.fillRect(breach[0], top + drop, breach[1] - breach[0], GY - top - drop); }
  for (let y = top + 22; y < GY; y += 22) { ctx.strokeStyle = 'rgba(30,20,12,0.45)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(W, y); ctx.stroke(); }    // 夯层
  ctx.fillStyle = '#6e4d33'; for (let x = x0; x < W; x += 40) { if (breach && x + 26 > breach[0] && x < breach[1]) continue; ctx.fillRect(x, top - 22, 26, 22); }
  ctx.restore();
}
function vsHeader(t, a, atk, def) {
  if (a <= 0) return; ctx.save(); ctx.globalAlpha = a;
  rrect(60, 520, 960, 92, 10); ctx.fillStyle = 'rgba(14,11,8,0.86)'; ctx.fill(); ctx.restore();
  text('攻 · ' + atk, 110, 566, { size: 42, fam: SERIF, wt: 900, alpha: a, stroke: 0, color: '#b9c8d8' });
  text('守 · ' + def, 970, 566, { size: 42, fam: SERIF, wt: 900, alpha: a, stroke: 0, color: '#ff9a7c', align: 'right' });
  text('→', 540, 566, { size: 40, wt: 700, alpha: a, stroke: 0, align: 'center', color: C.gold });
}
function cart(x, o = {}) {        // 攻车：带撞木的车架
  ctx.save(); ctx.translate(x, GY);
  ctx.fillStyle = '#2b3138'; ctx.strokeStyle = C.xuanL; ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(-220, -40); ctx.lineTo(0, -40); ctx.lineTo(-30, -190); ctx.lineTo(-190, -190); ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.fillStyle = '#4d5865'; ctx.fillRect(-200, -128, 250 + (o.ram || 0), 26); ctx.fillStyle = '#9aa6b2'; ctx.fillRect(40 + (o.ram || 0), -134, 22, 38);
  for (const wx of [-185, -45]) { ctx.fillStyle = '#11151a'; ctx.beginPath(); ctx.arc(wx, -32, 32, 0, 7); ctx.fill(); ctx.strokeStyle = C.xuanL; ctx.lineWidth = 3; ctx.stroke(); }
  ctx.restore();
}
function dust(x, y, t0, t, n = 30, col = '200,180,150') {
  const u = (t - t0); if (u < 0 || u > 1.6) return;
  ctx.save(); for (let i = 0; i < n; i++) { const a = hash(i, 7) * Math.PI - Math.PI, sp = 60 + 160 * hash(i, 8); const px = x + Math.cos(a) * sp * u, py = y + Math.sin(a) * sp * u * 0.6 - 30 * u; ctx.globalAlpha = 0.5 * (1 - u / 1.6); ctx.fillStyle = `rgba(${col},1)`; ctx.beginPath(); ctx.arc(px, py, 6 + 18 * u * hash(i, 9), 0, 7); ctx.fill(); } ctx.restore();
}

function sceneS4(t) {
  const s = TL.secs.s4, b = s.body; const T = k => A('s4', k), TE = k => E('s4', k);
  const v1 = [T(1) - 0.2, TE(3) + 0.15], v2 = [T(4) - 0.2, TE(6) + 0.15], v3 = [T(7) - 0.2, TE(9) + 0.15], v4 = [T(10) - 0.2, TE(10) + 0.15], v5 = [T(11) - 0.2, s.end];
  const xf = (r) => fadeIO(t, r[0], r[1], 0.35, 0.35);
  ctx.fillStyle = '#0d0c0b'; ctx.fillRect(0, 0, W, H);
  // 开场：四组对招预览
  if (t < v1[0] + 0.4) {
    const a = fadeIO(t, s.start, v1[0] + 0.35, 0.4, 0.35);
    const pairs = [['攻车', '布幔'], ['火竿', '钩刀'], ['地道烧柱', '随塌立栅'], ['土山', '夺回土山']];
    pairs.forEach((p, i) => { const y = 700 + i * 130, ai = a * P(t, b + i * 0.3, 0.4); ctx.save(); ctx.globalAlpha = ai; rrect(120, y - 50, 840, 100, 10); ctx.fillStyle = 'rgba(30,26,22,0.9)'; ctx.fill(); ctx.restore(); text(p[0], 200, y, { size: 44, fam: SERIF, wt: 900, alpha: ai, stroke: 0, color: '#b9c8d8' }); text('↔', 540, y, { size: 40, alpha: ai, stroke: 0, align: 'center', color: C.gold }); text(p[1], 880, y, { size: 44, fam: SERIF, wt: 900, alpha: ai, stroke: 0, color: '#ff9a7c', align: 'right' }); });
  }
  // ① 攻车 ↔ 布幔
  let a = xf(v1);
  if (a > 0) {
    ctx.save(); ctx.globalAlpha = a; stageBG(t);
    const hit1 = T(1) + 0.9, curtain = CK('s4', 1, 1) + 0.1, hit2 = curtain + 0.9, hit3 = A('s4', 2) + 0.8;
    const top = 760; const crack = t > hit1 ? 1 : 0;
    wallSide(620, top);
    if (crack) { ctx.save(); ctx.strokeStyle = '#1a120c'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(624, 1050); ctx.lineTo(660, 1000); ctx.lineTo(645, 960); ctx.lineTo(690, 920); ctx.stroke(); ctx.restore(); dust(625, 1060, hit1, t); }
    // 布幔：自城头放下，悬空
    const cd = eout(prog(t, curtain, curtain + 0.6));
    if (cd > 0) {
      const ph = 330 * cd; const bill = (t > hit2 ? Math.exp(-(t - hit2) * 3) * Math.sin((t - hit2) * 14) : 0) + (t > hit3 ? Math.exp(-(t - hit3) * 3) * Math.sin((t - hit3) * 14) : 0);
      ctx.save(); ctx.strokeStyle = '#d8b48a'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(640, top - 30); ctx.lineTo(560, top - 30); ctx.stroke();
      ctx.fillStyle = 'rgba(214,196,160,0.95)'; ctx.beginPath(); ctx.moveTo(560, top - 30);
      for (let k = 0; k <= 12; k++) { const yy = top - 30 + ph * k / 12; ctx.lineTo(560 + 18 * Math.sin(k * 1.3 + t * 3) * 0.3 + 40 * bill * Math.sin(k / 12 * Math.PI), yy); }
      ctx.lineTo(600, top - 30 + ph); ctx.lineTo(600, top - 30); ctx.closePath(); ctx.fill(); ctx.restore();
      label('布幔 · 悬空', 520, top - 80, { size: 30, bar: C.red, alpha: P(t, curtain + 0.3, 0.3) });
    }
    // 攻车运动
    let cx = 480;
    if (t < hit1) cx = lerp(-100, 480, eio(prog(t, T(1) - 0.2, hit1)));
    else if (t < curtain) cx = 480 - 120 * Math.sin(prog(t, hit1, curtain) * Math.PI) ;
    else if (t < hit2) cx = lerp(360, 430, ein(prog(t, curtain, hit2)));
    else if (t < hit3) cx = 430 - 90 * Math.sin(prog(t, hit2, hit3) * Math.PI);
    else cx = 430 - 70 * eout(prog(t, hit3, hit3 + 0.6));
    cart(cx, { ram: 0 });
    if (t > hit2 - 0.05 && t < hit2 + 0.4) { ctx.save(); ctx.globalAlpha = 1 - (t - hit2) / 0.45; text('软', 560, 1000, { size: 64, fam: SERIF, wt: 900, color: C.gold, align: 'center', stroke: 0 }); ctx.restore(); }
    ctx.restore(); vsHeader(t, a, '攻车', '布幔');
  }
  // ② 火竿 ↔ 钩刀
  a = xf(v2);
  if (a > 0) {
    ctx.save(); ctx.globalAlpha = a; stageBG(t); const top = 760; wallSide(620, top);
    ctx.fillStyle = 'rgba(214,196,160,0.95)'; ctx.fillRect(560, top - 30, 40, 330); ctx.strokeStyle = '#d8b48a'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(640, top - 30); ctx.lineTo(560, top - 30); ctx.stroke();
    const rise = eio(prog(t, T(4) + 0.1, T(4) + 1.8)), cut = A('s4', 5) - 0.25, fall = prog(t, cut, cut + 1.1);
    const bx = 120, by = GY - 20, ang = lerp(-0.25, -0.62, rise), Lp = 620;
    const tipX = bx + Math.cos(ang) * Lp, tipY = by + Math.sin(ang) * Lp;
    ctx.strokeStyle = '#4d5865'; ctx.lineWidth = 12; ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(tipX, tipY); ctx.stroke();
    // 火团
    const fx = t < cut ? tipX : tipX + 30 * fall, fy = t < cut ? tipY : tipY + (GY - tipY - 20) * ein(fall);
    const fl = 1 + 0.15 * Math.sin(t * 23);
    ctx.save(); ctx.globalCompositeOperation = 'lighter'; const rg = ctx.createRadialGradient(fx, fy, 2, fx, fy, 70 * fl); rg.addColorStop(0, 'rgba(255,230,150,0.95)'); rg.addColorStop(0.4, 'rgba(255,140,40,0.7)'); rg.addColorStop(1, 'rgba(255,60,10,0)'); ctx.fillStyle = rg; ctx.beginPath(); ctx.arc(fx, fy, 70 * fl, 0, 7); ctx.fill(); ctx.restore();
    if (t > cut + 1.0) { const u = clamp((t - cut - 1.0) / 1.2); ctx.save(); ctx.globalAlpha = 1 - u; ctx.fillStyle = 'rgba(255,120,40,0.6)'; ctx.beginPath(); ctx.ellipse(fx, GY - 6, 60, 12, 0, 0, 7); ctx.fill(); ctx.restore(); }
    // 钩刀：从城头伸出，远远一割
    const hk = eio(prog(t, CK('s4', 4, 1) - 0.1, cut)), sw = eio(prog(t, cut, cut + 0.25));
    const hx0 = 640, hy0 = top - 40, ha = lerp(-2.6, -2.95, hk) + sw * 0.9, hl = 260 + 120 * hk;
    const hx = hx0 + Math.cos(ha) * hl, hy = hy0 + Math.sin(ha) * hl;
    ctx.strokeStyle = '#a07a52'; ctx.lineWidth = 9; ctx.beginPath(); ctx.moveTo(hx0, hy0); ctx.lineTo(hx, hy); ctx.stroke();
    ctx.strokeStyle = '#e8eef3'; ctx.lineWidth = 7; ctx.beginPath(); ctx.moveTo(hx, hy); ctx.quadraticCurveTo(hx - 34, hy + 6, hx - 30, hy + 40); ctx.stroke();
    if (sw > 0 && sw < 1) { ctx.save(); ctx.globalAlpha = 1 - sw; ctx.strokeStyle = '#fff'; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(hx0, hy0, hl, ha - 0.5, ha); ctx.stroke(); ctx.restore(); }
    label('长柄钩刀', hx0 - 60, hy0 - 70, { size: 30, bar: C.red, alpha: P(t, CK('s4', 4, 1), 0.3) });
    label('火竿 · 松麻浇油', bx + 140, by - 60, { size: 30, bar: C.xuanL, alpha: P(t, T(4) + 0.4, 0.3) });
    ctx.restore(); vsHeader(t, a, '火竿', '钩刀');
  }
  // ③ 地道烧柱 ↔ 随塌立栅
  a = xf(v3);
  if (a > 0) {
    ctx.save(); ctx.globalAlpha = a; stageBG(t, { under: 1 }); const top = 820;
    const burn = prog(t, T(7) + 1.4, CK('s4', 7, 2) + 0.2), fallT = CK('s4', 7, 2) + 0.4, fall = eio(prog(t, fallT, fallT + 0.7)), pal = eout(prog(t, A('s4', 8) + 0.2, A('s4', 8) + 1.6));
    wallSide(380, top, { breach: fall > 0 ? [560, 820, 330 * fall] : null });
    // 地道 + 木柱（在墙下）
    ctx.fillStyle = '#0d0a08'; ctx.fillRect(200, GY + 70, 700, 90);
    const posts = [600, 660, 720, 780];
    posts.forEach((px, i) => { const broke = fall > 0.1; ctx.fillStyle = broke ? '#2a1a10' : '#8a6238'; if (!broke) ctx.fillRect(px - 9, GY + 70, 18, 90); else { ctx.save(); ctx.translate(px, GY + 160); ctx.rotate(0.9 * (i % 2 ? 1 : -1)); ctx.fillRect(-9, -50, 18, 50); ctx.restore(); }
      if (burn > 0 && fall < 1) { const f = burn * (1 - fall); ctx.save(); ctx.globalCompositeOperation = 'lighter'; const rg = ctx.createRadialGradient(px, GY + 115, 2, px, GY + 115, 50); rg.addColorStop(0, `rgba(255,210,120,${0.9 * f})`); rg.addColorStop(1, 'rgba(255,80,20,0)'); ctx.fillStyle = rg; ctx.beginPath(); ctx.arc(px, GY + 115, 50 + 8 * Math.sin(t * 19 + i), 0, 7); ctx.fill(); ctx.restore(); } });
    text('地道 · 木柱撑着', 215, GY + 115, { size: 26, wt: 700, stroke: 4, color: '#b9c8d8' });
    if (burn > 0.2) label('浇油 · 烧柱', 700, GY + 30, { size: 28, bar: '#ffb24a', alpha: 1 - fall });
    dust(690, top + 180, fallT + 0.3, t, 40);
    // 木栅
    if (pal > 0) { for (let i = 0; i < 9; i++) { const x = 572 + i * 28, h = 300 * clamp(pal * 1.3 - i * 0.04); ctx.fillStyle = '#9a6b3c'; ctx.fillRect(x, GY - h, 18, h); ctx.fillStyle = '#c9925a'; ctx.beginPath(); ctx.moveTo(x, GY - h); ctx.lineTo(x + 9, GY - h - 16); ctx.lineTo(x + 18, GY - h); ctx.fill(); } ctx.fillStyle = '#7a5230'; ctx.fillRect(566, GY - 210 * pal, 262, 12); ctx.fillRect(566, GY - 110 * pal, 262, 12); label('随崩处竖木栅', 690, top - 60, { size: 32, fam: SERIF, wt: 900, bar: C.red, alpha: pal }); }
    note('四面二十余道：《周书》二十一、《通鉴》二十（另有十道攻北面）', 70, 1300, 1, 'left', 22);
    ctx.restore(); vsHeader(t, a, '地道烧柱', '随塌立栅');
  }
  // ④ 夺回土山（局部地形）
  a = xf(v4);
  if (a > 0) {
    ctx.save(); ctx.globalAlpha = a;
    const cam = locCam([...kmLL(0.02, -0.55), 1.5]); drawLocal(cam, { season: 0.45, dim: 0.35 }); drawCity(cam);
    const [mx, my] = lk(cam, ...MOUND); const rr = 0.16 / LKM() * cam.s; const u = eio(prog(t, T(10) + 0.6, TE(10) - 0.3));
    ctx.fillStyle = u > 0.6 ? 'rgba(120,40,25,0.75)' : 'rgba(26,32,40,0.85)'; ctx.beginPath(); ctx.ellipse(mx, my, rr, rr * 0.75, -0.1, 0, 7); ctx.fill();
    ctx.strokeStyle = u > 0.6 ? C.red : C.xuanL; ctx.lineWidth = 4; ctx.stroke();
    const blk = [], red = []; const r = rng(31);
    for (let i = 0; i < 260; i++) { const an = r() * 6.283, rad = Math.sqrt(r()) * rr * 0.9; const bx = mx + Math.cos(an) * rad, by = my + Math.sin(an) * rad * 0.75;
      const push = clamp(u * 1.4 - r() * 0.4); blk.push([bx + Math.cos(an) * push * rr * 1.6, by + (Math.sin(an) * 0.75 + 0.9) * push * rr * 1.4]);
      const [sx, sy] = lk(cam, (r() - 0.5) * 0.3, -0.45 - r() * 0.05); red.push([lerp(sx, bx, clamp(u * 1.3 - 0.1)), lerp(sy, by, clamp(u * 1.3 - 0.1))]); }
    dots(blk.map((p, i) => [p[0], p[1]]), '#10151b', '#9aabbd', 4); if (u > 0.05) dots(red, '#c2321c', '#ffb09a', 4);
    label(u > 0.6 ? '土山易手' : '东魏的土山', mx, my + rr + 40, { size: 32, fam: SERIF, wt: 900, bar: u > 0.6 ? C.red : C.xuanL });
    note('《资治通鉴》：孝宽又夺据其土山 ·《北齐书》：孝宽夺据土山', W / 2, 1318, 1, 'center', 22);
    ctx.restore(); vsHeader(t, a, '土山', '夺回来');
  }
  // ⑤ 两边史书
  a = xf(v5);
  if (a > 0) {
    ctx.save(); ctx.globalAlpha = a;
    const cam = locCam([...kmLL(0, -0.1), 3.0]); drawLocal(cam, { season: 0.5, dim: 0.62 }); drawCity(cam, { alpha: 0.6 });
    ctx.restore();
    const at = T(11), bk = (x, title, side, lines, al) => { ctx.save(); ctx.globalAlpha = al; rrect(x, 620, 440, 520, 12); ctx.fillStyle = 'rgba(16,13,10,0.92)'; ctx.fill(); ctx.fillStyle = side === 'w' ? C.red : C.xuanL; ctx.fillRect(x, 620, 440, 8); ctx.restore(); text(title, x + 220, 690, { size: 46, fam: SERIF, wt: 900, align: 'center', alpha: al, stroke: 0 }); text(side === 'w' ? '西边的记载' : '东边的记载', x + 220, 745, { size: 26, wt: 500, align: 'center', alpha: al * 0.85, stroke: 0, color: side === 'w' ? '#ff9a7c' : '#b9c8d8' }); lines.forEach((l, i) => text(l, x + 40, 820 + i * 62, { size: 34, fam: SERIF, wt: 700, alpha: al, stroke: 0 })); };
    bk(80, '《周书》', 'w', ['截地道 · 鼓风', '布幔 · 钩刀', '随塌立栅'], a * P(t, at + 0.2, 0.4));
    bk(560, '《北齐书》', 'e', ['城上铁面', '元盗射之', '每中其目'], a * P(t, CK('s4', 11, 1) - 0.1, 0.4));
    // 铁面：面具 + 箭射中眼孔（不画人）
    const am = a * P(t, CK('s4', 11, 2) - 0.2, 0.4);
    if (am > 0) {
      const mx = 780, my = 1062; ctx.save(); ctx.globalAlpha = am; ctx.fillStyle = '#6f7880'; ctx.beginPath(); ctx.ellipse(mx, my, 50, 62, 0, 0, 7); ctx.fill(); ctx.strokeStyle = '#c8d0d8'; ctx.lineWidth = 3; ctx.stroke();
      ctx.fillStyle = '#0b0d0f'; ctx.fillRect(mx - 32, my - 16, 21, 8); ctx.fillRect(mx + 11, my - 16, 21, 8);
      const hu = prog(t, CK('s4', 11, 2), CK('s4', 11, 2) + 0.5);
      [[mx - 21, my - 12], [mx + 21, my - 12]].forEach(([ex, ey], i) => { const u2 = clamp(hu * 2 - i * 0.6); if (u2 <= 0) return; const sx = ex - 420, sy = ey + 160; ctx.strokeStyle = '#d8d0c0'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(lerp(sx, ex, u2 * 0.85), lerp(sy, ey, u2 * 0.85)); ctx.lineTo(lerp(sx, ex, u2), lerp(sy, ey, u2)); ctx.stroke(); if (u2 >= 1) { ctx.fillStyle = '#fff1d0'; ctx.beginPath(); ctx.arc(ex, ey, 5, 0, 7); ctx.fill(); } });
      ctx.restore();
    }
    const ae = fadeIO(t, CK('s4', 11, 3) - 0.2, T(12), 0.4, 0.4); label('两边史书，各记自己好看的一面', W / 2, 1230, { size: 32, fam: SERIF, wt: 900, bar: C.gold, alpha: ae });
    // 结论
    const a12 = fadeIO(t, T(12) - 0.1, s.end, 0.4, 0.4);
    if (a12 > 0) {
      ctx.save(); ctx.globalAlpha = a12; ctx.fillStyle = 'rgba(10,9,8,0.96)'; ctx.fillRect(0, 590, W, 720); ctx.restore();
      ['力气', '材料', '心思'].forEach((w2, i) => { const al = a12 * P(t, CK('s4', 12, 1) + i * 0.35, 0.35); text(w2, 230 + i * 310, 880, { size: 84, fam: SERIF, wt: 900, align: 'center', alpha: al, stroke: 0, color: '#ff9a7c' }); });
      text('城里一直都有', W / 2, 1040, { size: 40, fam: SERIF, wt: 900, align: 'center', alpha: a12 * P(t, CK('s4', 12, 1), 0.4), stroke: 0 });
      note('《周书》：多积战具以御之 · 兵食有余', W / 2, 1120, a12 * P(t, CK('s4', 12, 1) + 0.5, 0.4), 'center', 24);
    }
  }
  bands(0.4, 0.5);
}

// ---------------- 伍 · 关西男子 ----------------
function silhouette(x, y, s = 1, o = {}) {       // 简笔剪影（不画写实人像）
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.fillStyle = o.color || '#050506';
  ctx.beginPath(); ctx.arc(0, -150, 18, 0, 7); ctx.fill();
  ctx.beginPath(); ctx.moveTo(-26, -128); ctx.lineTo(26, -128); ctx.lineTo(34, -40); ctx.lineTo(18, 0); ctx.lineTo(-18, 0); ctx.lineTo(-34, -40); ctx.closePath(); ctx.fill();
  if (o.bound) { ctx.strokeStyle = o.rope || '#6b5a44'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(-30, -80); ctx.lineTo(30, -90); ctx.moveTo(-30, -60); ctx.lineTo(30, -70); ctx.stroke(); }
  if (o.cape) { ctx.beginPath(); ctx.moveTo(-26, -128); ctx.lineTo(-60, -10); ctx.lineTo(-30, -20); ctx.closePath(); ctx.fill(); }
  ctx.restore();
}
function nightWall(t, warm = 0) {
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#070a10'); g.addColorStop(0.55, '#111722'); g.addColorStop(1, '#0a0b0d'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.save(); for (let i = 0; i < 120; i++) { ctx.globalAlpha = 0.2 + 0.5 * hash(i, 3) * (0.7 + 0.3 * Math.sin(t * 2 + i)); ctx.fillStyle = '#dfe6f0'; ctx.fillRect(hash(i, 1) * W, hash(i, 2) * 620, 2, 2); } ctx.restore();
  // 城墙（右侧高处），城外地面（左下）
  ctx.fillStyle = '#16120f'; ctx.beginPath(); ctx.moveTo(470, 980); ctx.lineTo(W, 980); ctx.lineTo(W, H); ctx.lineTo(440, H); ctx.closePath(); ctx.fill();
  ctx.fillStyle = '#1d1712'; for (let x = 480; x < W; x += 46) ctx.fillRect(x, 952, 30, 28);
  ctx.fillStyle = '#0c0d0e'; ctx.fillRect(0, 1300, 470, H - 1300);
  // 火把
  for (const tx of [560, 1010]) { const fl = 0.8 + 0.2 * Math.sin(t * 11 + tx); const rg = ctx.createRadialGradient(tx, 930, 2, tx, 930, 240); rg.addColorStop(0, `rgba(255,170,80,${0.45 * fl})`); rg.addColorStop(1, 'rgba(255,120,40,0)'); ctx.fillStyle = rg; ctx.fillRect(tx - 240, 690, 480, 480); }
  if (warm > 0) { const rg = ctx.createRadialGradient(780, 960, 10, 780, 960, 700); rg.addColorStop(0, `rgba(255,120,70,${0.35 * warm})`); rg.addColorStop(1, 'rgba(255,90,50,0)'); ctx.fillStyle = rg; ctx.fillRect(0, 300, W, 1300); }
}
function speakWaves(x, y, t, a, col) { if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = col; ctx.lineWidth = 3; for (let k = 0; k < 3; k++) { const u = ((t * 1.3 + k / 3) % 1); ctx.globalAlpha = a * (1 - u); ctx.beginPath(); ctx.arc(x, y, 30 + u * 60, -0.6, 0.6); ctx.stroke(); } ctx.restore(); }
function sceneS5(t) {
  const s = TL.secs.s5, b = s.body; const T = k => A('s5', k), TE = k => E('s5', k);
  const moved = P(t, T(12) - 0.2, 2.5);
  nightWall(t, moved);
  // 城上士兵（暗）→ 被打动后亮起
  for (let i = 0; i < 9; i++) { const x = 520 + i * 62; if (Math.abs(x - 780) < 40) continue; const lit = clamp(moved * 2 - hash(i, 5)); silhouette(x, 952, 0.56, { color: lit > 0 ? `rgb(${Math.round(lerp(10, 120, lit))},${Math.round(lerp(10, 50, lit))},${Math.round(lerp(12, 34, lit))})` : '#0a0a0c' }); }
  silhouette(780, 952, 0.86, { color: '#120d0b', cape: 1 });
  const zt = fadeIO(t, s.start, T(11) + 0.4, 0.6, 0.6);
  silhouette(250, 1300, 0.86, { color: '#050608' });
  label('祖珽（孝征）', 250, 1340, { size: 28, bar: C.xuanL, alpha: zt * P(t, b + 0.6, 0.4) });
  label('韦孝宽', 780, 1020, { size: 28, bar: C.red, alpha: P(t, b + 1.0, 0.4) });
  speakWaves(320, 1190, t, (t > b && t < TE(0)) || (t > T(10) && t < TE(10)) ? 0.8 : 0, '#b9c8d8');
  speakWaves(840, 840, t, (t > T(1) && t < TE(9)) ? 0.8 : 0, '#ff9a7c');
  // “孤城”
  const ag = fadeIO(t, CK('s5', 0, 1), T(1) + 0.3, 0.4, 0.4); if (ag > 0) { label('“君独守孤城，而西方无救”', W / 2, 640, { size: 34, fam: SERIF, wt: 900, bar: C.xuanL, alpha: ag }); note('《资治通鉴》卷一百五十九', W / 2, 692, ag, 'center'); }
  // 攻者自劳，守者常逸：单独停留
  const a8 = fadeIO(t, T(4) - 0.3, TE(5) + 0.5, 0.5, 0.6);
  if (a8 > 0) {
    ctx.save(); ctx.globalAlpha = a8; ctx.fillStyle = 'rgba(8,8,9,0.72)'; ctx.fillRect(0, 230, W, 560); ctx.restore();
    const sh = (T(4) + 0.1); const c1 = '攻者自劳', c2 = '守者常逸';
    [...c1].forEach((ch, i) => text(ch, 210 + i * 110, 380, { size: 104, fam: SERIF, wt: 900, align: 'center', alpha: a8 * P(t, sh + i * 0.22, 0.3), stroke: 0, color: '#b9c8d8' }));
    [...c2].forEach((ch, i) => text(ch, 540 + i * 110, 560, { size: 104, fam: SERIF, wt: 900, align: 'center', alpha: a8 * P(t, sh + 1.0 + i * 0.22, 0.3), stroke: 0, color: '#ff9a7c' }));
    const ae = P(t, T(5) + 0.2, 0.5);
    text('越打越累', 375, 465, { size: 34, wt: 700, align: 'center', alpha: a8 * ae, stroke: 0, color: '#b9c8d8' });
    text('以逸待劳', 705, 645, { size: 34, wt: 700, align: 'center', alpha: a8 * ae, stroke: 0, color: '#ff9a7c' });
    text('—— 《周书·韦孝宽传》', 990, 730, { size: 26, fam: SERIF, wt: 700, align: 'right', alpha: a8, stroke: 0, color: C.gold });
    note('兵法所谓“先为不可胜”（见兵法系列）', 90, 730, a8 * P(t, CK('s5', 5, 1), 0.5), 'left', 24);
  }
  // 关西男子：关中→玉璧的暖光
  const ak = fadeIO(t, T(8) - 0.2, TE(9) + 0.3, 0.4, 0.5); if (ak > 0) { const rg = ctx.createRadialGradient(780, 860, 10, 780, 860, 420); rg.addColorStop(0, `rgba(255,140,90,${0.4 * ak})`); rg.addColorStop(1, 'rgba(255,120,80,0)'); ctx.fillStyle = rg; ctx.fillRect(300, 400, 900, 900); }
  // 悬赏令再射进来
  const ar = prog(t, CK('s5', 10, 2) - 0.2, CK('s5', 10, 2) + 0.7);
  if (ar > 0 && ar < 1) drawArrow(lerp(300, 760, eio(ar)), lerp(1150, 880, eio(ar)), Math.atan2(-270, 460), 220, { blur: 1, scroll: 1 });
  const am = fadeIO(t, CK('s5', 10, 1) - 0.2, TE(10) + 0.3, 0.4, 0.4); if (am > 0) label('对城里的兵：何事相随入汤火中', 250, 1230, { size: 28, bar: C.xuanL, alpha: am, align: 'left' });
  // 侄子：被缚的剪影 + 一道冷光
  const an = fadeIO(t, T(11) - 0.1, TE(14) + 0.3, 0.5, 0.6);
  if (an > 0) {
    ctx.save(); ctx.globalAlpha = an; silhouette(410, 1300, 0.8, { color: '#060708', bound: 1 });
    const gl = 0.6 + 0.4 * Math.sin(t * 3); const lg = ctx.createLinearGradient(330, 1150, 470, 1120); lg.addColorStop(0, 'rgba(200,225,255,0)'); lg.addColorStop(0.5, `rgba(220,235,255,${0.9 * gl})`); lg.addColorStop(1, 'rgba(200,225,255,0)'); ctx.strokeStyle = lg; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(330, 1150); ctx.lineTo(470, 1120); ctx.stroke();
    ctx.restore(); label('侄子 韦迁', 400, 1340, { size: 28, bar: C.red, alpha: an * P(t, T(11) + 0.8, 0.4) });
  }
  const aq = fadeIO(t, T(14) - 0.2, TE(14) + 0.3, 0.4, 0.4); if (aq > 0) note('韦迁后来下落：史书没有交代', 90, 1075, aq, 'left', 26);
  // 结论
  const a14 = fadeIO(t, T(15) - 0.1, s.end, 0.4, 0.4);
  if (a14 > 0) {
    ctx.save(); ctx.globalAlpha = a14; rrect(60, 262, 960, 210, 10); ctx.fillStyle = 'rgba(14,11,8,0.88)'; ctx.fill(); ctx.restore();
    text('想把城主和士兵拆开来买', 100, 320, { size: 40, fam: SERIF, wt: 900, alpha: a14, stroke: 0, color: '#b9c8d8' });
    text('守城的人知道为什么守 —— 买不到', 100, 410, { size: 40, fam: SERIF, wt: 900, alpha: a14 * P(t, CK('s5', 15, 1) - 0.1, 0.4), stroke: 0, color: '#ff9a7c' });
  }
  // 高潮留白（约 2 秒）：城头一线暖光
  const ah = fadeIO(t, TE(13) - 0.3, T(14) + 0.6, 0.9, 0.9);
  if (ah > 0) { const rg = ctx.createRadialGradient(700, 930, 20, 700, 930, 520); rg.addColorStop(0, `rgba(255,150,90,${0.32 * ah})`); rg.addColorStop(1, 'rgba(255,120,80,0)'); ctx.fillStyle = rg; ctx.fillRect(100, 450, 1000, 900); }
  bands(0.35, 0.5);
}

// ---------------- 陆 · 五十天 ----------------
let FOG = null;
function sceneS6(t) {
  const s = TL.secs.s6, b = s.body; const T = k => A('s6', k), TE = k => E('s6', k);
  const cam = locCam(kf([[s.start, ...kmLL(0, -0.3), 7.5], [s.end, ...kmLL(0, -0.2), 6.0]], t));
  const u = prog(t, s.start, s.end);
  drawLocal(cam, { season: lerp(0.6, 0.95, u), dim: 0.35 });
  drawCamp(cam, t, 1, 1, u * 0.55);
  drawCity(cam);
  // 病气：灰雾从营地升起
  if (!FOG) { FOG = []; const r = rng(8); for (let i = 0; i < 70; i++) FOG.push([(r() - 0.5) * 5, -1 - r() * 2.3, r()]); }
  ctx.save(); for (const [x, y, h] of FOG) { const [px, py] = lk(cam, x, y); const k = clamp(u * 1.5 - h * 0.5); if (k <= 0) continue; const rr = (40 + 90 * h) * (0.6 + 0.6 * k); const g = ctx.createRadialGradient(px, py - 40 * k, 2, px, py - 40 * k, rr); g.addColorStop(0, `rgba(150,156,160,${0.25 * k})`); g.addColorStop(1, 'rgba(150,156,160,0)'); ctx.fillStyle = g; ctx.fillRect(px - rr, py - 40 * k - rr, rr * 2, rr * 2); } ctx.restore();
  bands(0.55, 0.55);
  // 日历：九月 → 十一月
  const months = ['九月', '十月', '十一月'];
  months.forEach((m, i) => { const x = 330 + i * 210, on = u > i * 0.4; text(m, x, 640, { size: 34, fam: SERIF, wt: 900, align: 'center', alpha: on ? 0.95 : 0.3, stroke: 5, color: on ? C.cream : '#888' }); });
  // 三本书三个数字
  const books = [['《周书》', '苦战六旬', '伤及病死', '十之四五', T(0) + 1.8], ['《资治通鉴》', '凡五十日', '战及病死', '七万人 · 共为一冢', T(3)], ['《北齐书》', '顿军五旬', '死者', '七万人 · 聚为一冢', T(6)]];
  books.forEach(([nm, d, k, v, t0], i) => {
    const al = P(t, t0, 0.5), x = 70 + i * 320, y = 720;
    if (al <= 0) return;
    ctx.save(); ctx.globalAlpha = al; rrect(x, y, 300, 420, 12); ctx.fillStyle = 'rgba(14,12,10,0.9)'; ctx.fill(); ctx.fillStyle = C.gold; ctx.fillRect(x, y, 300, 6); ctx.restore();
    text(nm, x + 150, y + 60, { size: i === 1 ? 36 : 40, fam: SERIF, wt: 900, align: 'center', alpha: al, stroke: 0, color: C.gold });
    text(d, x + 150, y + 150, { size: 46, fam: SERIF, wt: 900, align: 'center', alpha: al, stroke: 0 });
    text(k, x + 150, y + 245, { size: 30, wt: 700, align: 'center', alpha: al, stroke: 0, color: 'rgba(244,234,214,0.8)' });
    const vs = v.split(' · '); vs.forEach((vv, j) => text(vv, x + 150, y + 310 + j * 52, { size: j ? 30 : 44, fam: SERIF, wt: 900, align: 'center', alpha: al, stroke: 0, color: j ? 'rgba(244,234,214,0.85)' : '#ff9a7c' }));
  });
  const a7 = fadeIO(t, T(7) - 0.1, s.end, 0.4, 0.4);
  if (a7 > 0) { label('不光战死，还有病死', W / 2, 1210, { size: 34, fam: SERIF, wt: 900, bar: '#9aa0a5', alpha: a7 }); label('攻者自劳 —— 有了数字', W / 2, 1290, { size: 38, fam: SERIF, wt: 900, bar: C.red, alpha: a7 * P(t, CK('s6', 7, 2) - 0.1, 0.4) }); }
}
