// 场景（下）：伍～收尾、片尾，以及总调度
'use strict';

// ---------------- 伍 · 阵为什么成立 ----------------
function sceneS5(t) {
  const s = TL.secs.s5; const tk = A('s5', 6) - 0.7;      // 切到刘康祖
  if (t < tk + 0.8) {
    const tb = BT.spear - 0.6 + (t - s.start) * 0.05;
    const cam = tacCam(kf([[s.start, 0, 150, 0.6], [A('s5', 1), 0, 70, 0.66], [E('s5', 1), 0, 60, 0.68], [A('s5', 2) + 1.5, 0, 150, 0.5], [E('s5', 3), 0, 160, 0.5], [A('s5', 4) + 1.5, 0, 150, 0.6], [tk + 0.8, 0, 160, 0.64]], t));
    drawBattle(cam, tb, { noChase: true, noMissiles: true, dim: 0.34 });
    const [cx, cy] = tw(cam, 0, Y0), sc = 1 / cam.mpp;
    const act = k => fadeIO(t, A('s5', k) - 0.1, E('s5', k) + 0.3, 0.5, 0.5);
    // ① 河
    let a = act(1);
    if (a > 0) {
      const yb = tw(cam, 0, Y0 - 4)[1]; const g = ctx.createLinearGradient(0, yb, 0, yb + 500); g.addColorStop(0, `rgba(120,190,220,${0.3 * a})`); g.addColorStop(1, 'rgba(120,190,220,0)'); ctx.fillStyle = g; ctx.fillRect(0, yb, W, 520);
      const u = P(t, A('s5', 1) + 0.6, 1.4);
      for (const dx of [-70, 0, 70]) { const p0 = tw(cam, dx, Y0 - 200), p1 = tw(cam, dx * 0.7, Y0 + 26); arrow(p0[0], p0[1], p1[0], p1[1], { color: C.redL, w: 8, head: 22, frac: u, alpha: a, glow: 'rgba(255,138,102,0.7)' }); }
      const p = tw(cam, 0, Y0 - 120); label('援兵 · 弩槊 · 退路：都在船上', p[0], Math.min(p[1], 1290), { size: 30, bar: C.redL, alpha: a * u });
      // 骑兵绕后被河挡住
      const v = P(t, A('s5', 1) + 4.2, 1.6);
      for (const sg of [-1, 1]) { const e = curveArrow([tw(cam, sg * 330, Y0 + 210), tw(cam, sg * 300, Y0 + 60), tw(cam, sg * 215, Y0 - 6)], { color: C.wei, w: 8, frac: v, alpha: a }); if (v > 0.95) { const q = tw(cam, sg * 200, Y0 - 16); cross(q[0], q[1], 18, '#fff', 7, a); } }
      const q = tw(cam, 250, Y0 + 250); label('背后这一面，骑兵过不去', W / 2, q[1], { size: 30, bar: C.wei, alpha: a * v });
    }
    // ② 车
    a = act(2);
    if (a > 0) {
      ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = '#fff1d0'; ctx.lineWidth = 9; ctx.shadowColor = '#ffd9a0'; ctx.shadowBlur = 26; ctx.beginPath(); ctx.arc(cx, cy, (R_ARC + 1.5) * sc, Math.PI, 2 * Math.PI); ctx.stroke(); ctx.restore();
      const u = P(t, A('s5', 2) + 1.4, 1.2);
      for (let i = 0; i < 9; i++) { const th = Math.PI * (i + 0.5) / 9; const p0 = tw(cam, 330 * Math.cos(th), Y0 + 330 * Math.sin(th)), p1 = tw(cam, 166 * Math.cos(th), Y0 + 166 * Math.sin(th)); arrow(p0[0], p0[1], p1[0], p1[1], { color: C.wei, w: 7, head: 18, frac: u, alpha: a * 0.95 }); }
    }
    // ③ 弩与槊
    a = act(3);
    if (a > 0) {
      const u = ((t - A('s5', 3)) % 1.3) / 1.3;
      ctx.save(); ctx.globalAlpha = a; ctx.lineCap = 'round';
      for (let i = 0; i < 40; i++) { const th = Math.PI * (i + 0.5) / 40; const r0 = R_ARC + 4 + u * 70, r1 = r0 + 30; const p0 = tw(cam, r0 * Math.cos(th), Y0 + r0 * Math.sin(th)), p1 = tw(cam, r1 * Math.cos(th), Y0 + r1 * Math.sin(th)); ctx.strokeStyle = `rgba(255,236,200,${1 - u})`; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(p0[0], p0[1]); ctx.lineTo(p1[0], p1[1]); ctx.stroke(); }
      ctx.restore();
    }
    bands(0.62, 0.6);
    // 顶部四要素面板
    const pa = fadeIO(t, s.body + 0.3, tk + 0.3, 0.6, 0.5);
    const items = [['河', '背靠舰队，敌骑绕不到身后'], ['车', '车盾成墙，冲锋变成拥堵'], ['弩', '弩与槊，专打停住的密集目标'], ['纪律', '登岸、候令、示弱、齐射，一步不乱']];
    ctx.save(); ctx.globalAlpha = pa; rrect(60, 262, 960, 250, 10); ctx.fillStyle = 'rgba(14,11,8,0.84)'; ctx.fill(); ctx.restore();
    let cur = -1; for (let k = 1; k <= 4; k++) if (t >= A('s5', k) - 0.1) cur = k - 1; const all = t >= A('s5', 5) - 0.1;
    for (let i = 0; i < 4; i++) {
      const x = 60 + 120 + i * 240, on = all || i === cur, seen = i <= cur; const ia = pa * (seen ? 1 : 0.28);
      ctx.save(); ctx.globalAlpha = ia; rrect(x - 96, 290, 192, 120, 8); ctx.fillStyle = on ? C.red : 'rgba(60,50,40,0.6)'; ctx.fill(); if (!on && seen) { ctx.strokeStyle = C.red; ctx.lineWidth = 3; ctx.stroke(); } ctx.restore();
      text(items[i][0], x, 352, { size: i === 3 ? 62 : 78, fam: SERIF, wt: 900, align: 'center', alpha: ia, stroke: 0, color: '#fff7e6' });
    }
    if (all) text('少一样，都不成', W / 2, 462, { size: 40, fam: SERIF, wt: 900, align: 'center', alpha: pa * P(t, A('s5', 5), 0.5), stroke: 0, color: C.gold, ls: 4 });
    else if (cur >= 0) text(items[cur][1], W / 2, 462, { size: 34, wt: 700, align: 'center', alpha: pa * P(t, A('s5', cur + 1) + 0.1, 0.5), stroke: 0 });
    else text('把这个阵拆开看', W / 2, 462, { size: 34, wt: 700, align: 'center', alpha: pa, stroke: 0 });
    // ④ 纪律：步骤条
    a = act(4);
    if (a > 0) {
      const steps = ['七百人敌前登岸', '白毦一举', '二千人入阵', '软弓示弱', '百弩齐发']; const n = steps.length;
      for (let i = 0; i < n; i++) { const u = P(t, A('s5', 4) + 0.5 + i * 1.15, 0.5); const y = 640 + i * 78; label(`${'①②③④⑤'[i]} ${steps[i]}`, 76, y, { size: 32, align: 'left', alpha: a * u, bar: C.red }); }
    }
  }
  if (t >= tk) { const al = sstep((t - tk) / 0.8); ctx.save(); ctx.globalAlpha = al; sceneKangzu(t); ctx.restore(); }
}
// 刘康祖尉武之战（元嘉二十七年，450）—— 平地车营示意
let KZ = null;
function sceneKangzu(t) {
  const s = TL.secs.s5; const t6 = A('s5', 6), t7 = A('s5', 7), t8 = A('s5', 8), t9 = A('s5', 9);
  const CX = 0, CY = 960, RR = 108;
  if (!KZ) { const r = rng(99); KZ = { b: [], r: [] }; for (let i = 0; i < 20000; i++) KZ.b.push([r() * 6.2832, r(), r(), r()]); for (let i = 0; i < 2000; i++) KZ.r.push([r() * 6.2832, Math.sqrt(r()) * (RR - 6), r()]); }
  const cam = tacCam(kf([[t6 - 1, CX, CY + 20, 0.6], [t7, CX, CY, 0.7], [s.end, CX, CY - 10, 0.76]], t));
  drawTac(cam, 0.3);
  const sc = 1 / cam.mpp; const fire = t8 - 0.6, fall = t8 + 2.6;
  const col = eio(prog(t, fall, fall + 3.5));                 // 崩溃进度
  // 魏骑：三部轮番
  const arrive = t6 + 2.6; const paths = [new Path2D(), new Path2D()], ps = Math.max(2.8, 1.8 * sc);
  for (let i = 0; i < KZ.b.length; i++) {
    const [a, h1, h2, h3] = KZ.b[i]; const grp = Math.floor(a / (2 * Math.PI / 3));
    const ph = ((t - t7) / 3.3 - grp / 3) % 1; const pp = ((ph % 1) + 1) % 1; const attack = t > t7 - 0.5 ? sstep(1 - Math.abs(pp - 0.25) / 0.25) : 0;   // 轮到本部进攻
    const rRest = Math.sqrt(lerp(215 * 215, 470 * 470, h1)), rAtk = Math.sqrt(lerp(116 * 116, 300 * 300, h1));
    let rr = lerp(rRest, rAtk, attack * (0.6 + 0.4 * h3));
    const u = eout(prog(t, arrive + h2 * 3 - 2, arrive + 3 + h2 * 3)); rr = lerp(1500 + 500 * h2, rr, u);
    rr = lerp(rr, 8 + (rr - 8) * (0.25 + 0.75 * h2), col * (h3 < 0.5 ? 1 : 0));
    const an = a + Math.sin(t * 0.6 + h2 * 20) * 0.02;
    const [px, py] = tw(cam, CX + rr * Math.cos(an), CY + rr * Math.sin(an)); if (px < -4 || px > W + 4 || py < -4 || py > H + 4) continue; paths[i & 1].rect(px - ps / 2, py - ps / 2, ps, ps * 0.9);
  }
  ctx.fillStyle = '#5db9f2'; ctx.fill(paths[0]); ctx.fillStyle = '#e2f5ff'; ctx.fill(paths[1]);
  // 晋(宋)军
  const pr = [new Path2D(), new Path2D()];
  for (let i = 0; i < KZ.r.length; i++) { const [a, rr, h] = KZ.r[i]; const dead = col > h * 0.92 + 0.05; const [px, py] = tw(cam, CX + rr * Math.cos(a), CY + rr * Math.sin(a)); pr[dead ? 1 : 0].rect(px - ps / 2, py - ps / 2, ps, ps); }
  ctx.fillStyle = '#ff5a3c'; ctx.fill(pr[0]); ctx.fillStyle = '#2a1f1c'; ctx.fill(pr[1]);
  // 车营（环）
  const nw = 150; for (let i = 0; i < nw; i++) { const th = 2 * Math.PI * i / nw; const [px, py] = tw(cam, CX + RR * Math.cos(th), CY + RR * Math.sin(th)); const burn = clamp((t - fire) / 3 - (0.5 + 0.5 * Math.cos(th - 2.3)) * 0.9); ctx.save(); ctx.translate(px, py); ctx.rotate(-(th + Math.PI / 2)); const L = 4.2 * sc, Wd = 1.9 * sc; ctx.fillStyle = burn > 0.5 ? '#1c1410' : '#3a2716'; ctx.fillRect(-L / 2, -Wd / 2, L, Wd); if (burn <= 0.5) { ctx.fillStyle = '#b58a52'; ctx.fillRect(-L / 2 + 1, -Wd / 2 + 1, L - 2, Wd - 2); } ctx.restore();
    if (burn > 0 && burn < 1.6) { const fl = 0.6 + 0.4 * Math.sin(t * 17 + i * 3); ctx.save(); ctx.globalCompositeOperation = 'lighter'; const g = ctx.createRadialGradient(px, py, 0, px, py, 14 * sc * fl); g.addColorStop(0, `rgba(255,190,90,${0.75 * Math.min(1, burn * 2) * (1 - clamp(burn - 0.9) / 0.7)})`); g.addColorStop(1, 'rgba(255,90,20,0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(px, py, 14 * sc, 0, 7); ctx.fill(); ctx.restore(); } }
  bands(0.62, 0.6);
  // 标题面板
  const pa = fadeIO(t, t6 - 0.2, s.end, 0.6, 0.5);
  ctx.save(); ctx.globalAlpha = pa; rrect(60, 262, 960, 150, 10); ctx.fillStyle = 'rgba(14,11,8,0.84)'; ctx.fill(); ctx.fillStyle = C.gold; ctx.fillRect(60, 262, 8, 150); ctx.restore();
  if (t < t7 - 0.4 || t > E('s5', 8) + 0.2) {
    text('三十三年后 · 元嘉二十七年（450）', 100, 310, { size: 38, fam: SERIF, wt: 900, alpha: pa, stroke: 0 });
    text('尉武：宋将刘康祖 八千人  对  魏 八万骑', 100, 368, { size: 32, wt: 700, alpha: pa, stroke: 0, color: C.gold });
  }
  const [cx, cy] = tw(cam, CX, CY);
  const a6 = fadeIO(t, t6 + 1.0, t7 - 0.2, 0.5, 0.4); if (a6 > 0) { label('结车营而进 · 无河可依', cx, cy + 150 * sc, { size: 32, bar: C.red, alpha: a6 }); }
  const a7 = fadeIO(t, E('s5', 7) - 0.5, t8 + 3.4, 0.5, 0.5);
  if (a7 > 0) {
    for (let g = 0; g < 3; g++) { const ph = ((((t - t7) / 3.3 - g / 3) % 1) + 1) % 1; const on = ph < 0.5; const th = (g + 0.5) * 2 * Math.PI / 3; const [x, y] = tw(cam, CX + 300 * Math.cos(th), CY + 300 * Math.sin(th)); label(on ? `第${'一二三'[g]}部 · 进攻` : `第${'一二三'[g]}部 · 休整`, clamp(x, 200, 880), clamp(y, 600, 1290), { size: 28, bar: on ? '#fff' : C.weiD, alpha: a7 * (on ? 1 : 0.75) }); }
  }
  const a8 = fadeIO(t, fire + 0.6, fall + 1.2, 0.4, 0.5); if (a8 > 0) { const [x, y] = tw(cam, CX - 150, CY + 140); label('以骑负草烧车营', x, y, { size: 32, bar: '#ffb24a', alpha: a8 }); }
  const a9 = fadeIO(t, fall + 1.4, s.end, 0.5, 0.4); if (a9 > 0) label('举营沦覆 · 自免者裁数十人（《宋书》）', cx, cy + 190 * sc, { size: 30, bar: C.redL, alpha: a9 });
  dotLegend(pa * 0.9, '示意：一点 ≈ 四人');
}

// ---------------- 陆 · 入长安 ----------------
function sceneS6(t) {
  const s = TL.secs.s6, b = s.body, t2 = A('s6', 2), t3 = A('s6', 3);
  const d3 = E('s6', 3) - t3, tk = t3 + 0.82 * d3;
  const cam = macCam(kf([[s.start, 114.6, 37.9, 7.4], [E('s6', 1), 114.6, 37.9, 7.2], [t2 + 1.4, 115.5, 36.4, 3.2], [t3 + 0.2, 115.4, 36.35, 3.0], [t3 + 0.2 * d3, 113.9, 35.5, 5.4], [t3 + 0.48 * d3, 110.8, 34.8, 4.6], [t3 + 0.75 * d3, 109.6, 34.5, 3.2], [s.end, 109.4, 34.5, 3.0]], t));
  drawMacro(cam, 0.2); drawRivers(cam); riverNames(cam, 1, 'he,wei');
  // 败报北传
  const p0 = mw(cam, 115.5, 36.75), p1 = mw(cam, ...G.pingcheng);
  const fm = P(t, b, 2.2); if (t < t2 + 1) arrow(p0[0], p0[1], p1[0], p1[1] + 30, { color: '#d7d2c4', w: 5, head: 18, dash: [10, 10], frac: fm, alpha: 1 - P(t, t2, 0.8) });
  city(cam, ...G.pingcheng, '平城', { color: C.wei, capital: 1, pulse: t > b + 2 && t < t2 ? t : 0, dy: 48 });
  // 西进
  const fw = sstep(prog(t, t3 + 0.2, t3 + 0.5 * d3)); const head = geoLine(cam, G.routeC, { color: C.red, w: 8, from: 0.14, frac: 0.14 + 0.86 * fw, glow: 'rgba(226,69,46,0.7)' });
  const fd = sstep(prog(t, t3 + 0.52 * d3, tk - 0.3)); const hd = geoLine(cam, G.routeD, { color: C.red, w: 8, frac: fd, glow: 'rgba(226,69,46,0.7)' });
  const taken = t > tk;
  city(cam, ...G.luoyang, '洛阳', { dy: 42, color: C.red, size: 30, r: 7 }); city(cam, ...G.tongguan, '潼关', { dy: 44, color: fw > 0.98 ? C.red : C.qin, r: 7, size: 30 });
  city(cam, ...G.changan, '长安', { color: taken ? C.red : C.qin, capital: 1, dy: 48, pulse: taken ? t : 0 });
  const fl = mw(cam, 115.62, 36.18), cs = mw(cam, 115.5, 36.78);
  if (t < t3 + 0.6) {
    unitBox(cs[0], cs[1] - 14, { type: 'cav', color: C.wei, name: '长孙嵩', w: 76, h: 50, alpha: 1 - P(t, t3, 0.6) });
    unitBox(fl[0], fl[1] + 10, { type: 'navy', color: C.red, name: '刘裕', w: 76, h: 50, alpha: 1 - P(t, t3, 0.6) });
    const ag = fadeIO(t, t2 + 2.2, t3 + 0.2, 0.5, 0.4);
    if (ag > 0) { const u = P(t, t2 + 2.4, 1.2); curveArrow([[fl[0] + 60, fl[1] - 6], [fl[0] + 120, (fl[1] + cs[1]) / 2 - 20], [cs[0] + 62, cs[1] - 6]], { color: C.gold, w: 5, head: 16, frac: u, alpha: ag }); label('遗以酃酒及江南食物', W / 2, cs[1] - 150, { size: 32, fam: SERIF, wt: 900, bar: C.gold, alpha: ag }); note('—— 《魏书·长孙嵩传》', W / 2, cs[1] - 102, ag, 'center'); label('诏假裕道（下诏借道）', W / 2, fl[1] + 150, { size: 32, bar: C.wei, alpha: ag }); }
  } else {
    const h = hd && fd > 0 ? hd : head; if (h) unitBox(h[0], h[1] - 6, { type: 'navy', color: C.red, name: fd > 0 ? '王镇恶 水军' : '舰队西进', w: 76, h: 50 });
  }
  if (taken) { const c = mw(cam, ...G.changan); const a = P(t, tk + 0.2, 0.6); label('义熙十三年八月 · 后秦亡', c[0], c[1] - 190, { size: 38, fam: SERIF, wt: 900, bar: C.red, alpha: a }); }
  const a3 = fadeIO(t, t3 + 0.54 * d3, tk + 0.2, 0.5, 0.4); if (a3 > 0) { const c = mw(cam, 109.6, 34.5); label('自河入渭 · 直抵长安城北', c[0], c[1] - 110, { size: 30, bar: C.redL, alpha: a3 }); }
  bands(0.5, 0.55); compass(990, 250, 1);
}

// ---------------- 柒 · 建康 ----------------
function sceneS7(t) {
  const s = TL.secs.s7, b = s.body; const T = k => A('s7', k), TE = k => E('s7', k);
  const wide = [113.85, 33.2, 12.6];
  const cam = macCam(kf([[s.start, 109.3, 34.6, 3.8], [TE(0) - 0.4, 109.5, 34.6, 3.6], [T(1) + 0.8, ...wide], [T(1) + 2.3, 118.2, 32.6, 4.6], [TE(3) + 0.2, 118.1, 32.7, 4.4], [T(4) + 2.2, ...wide], [TE(4), 113.85, 33.2, 12.2], [T(5) + 1.6, 109.2, 34.7, 3.4], [TE(5), 109.2, 34.7, 3.3], [T(6) + 1.8, 108.9, 36.1, 7.0], [TE(8), 108.9, 36.05, 6.7], [T(9) + 1.6, 109.25, 34.35, 2.3], [TE(9), 109.3, 34.35, 2.2], [T(10) + 1.6, 109.8, 34.6, 3.0], [s.end, 109.9, 34.6, 2.9]], t));
  drawMacro(cam, 0.22); drawRivers(cam); riverNames(cam, 1, 'he,wei,jiang');
  const lost = t > T(9) + 6.5;       // 长安易手
  // 长安—建康 直线
  const a4 = fadeIO(t, T(4) + 1.6, TE(4) + 0.3, 0.6, 0.5);
  if (a4 > 0) { const p0 = mw(cam, ...G.changan), p1 = mw(cam, ...G.jiankang); const u = P(t, T(4) + 1.8, 1.6); ctx.save(); ctx.globalAlpha = a4; ctx.strokeStyle = C.gold; ctx.lineWidth = 4; ctx.setLineDash([16, 12]); ctx.beginPath(); ctx.moveTo(p0[0], p0[1]); ctx.lineTo(lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u)); ctx.stroke(); ctx.restore(); label('直线约 950 公里（今地测距）', (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + 60, { size: 32, bar: C.gold, alpha: a4 * u }); }
  // 东归
  const fb = P(t, T(4) + 2.6, 4.2); if (t > T(4) && t < T(5) + 1) { const e = geoLine(cam, G.routeBack, { color: C.red, w: 8, frac: fb, glow: 'rgba(226,69,46,0.7)', alpha: 1 - P(t, T(5), 0.8) }); if (e) unitBox(e[0], e[1] - 8, { type: 'navy', color: C.red, name: '刘裕东归', sub: '十二月', w: 72, h: 46, alpha: 1 - P(t, T(5), 0.8) }); }
  // 夏军南下
  if (t > T(6)) { const fx = P(t, T(6) + 1.6, 5.0); const e = geoLine(cam, G.routeXia, { color: C.xia, w: 9, frac: fx, glow: 'rgba(170,150,240,0.7)', alpha: t > T(10) ? 0.5 : 1 }); if (e && t < T(9) + 1) unitBox(e[0], e[1], { type: 'cav', color: C.xia, name: '夏 · 赫连勃勃', w: 76, h: 50, alpha: 1 - P(t, T(9), 0.8) }); }
  // 青泥
  if (t > T(9)) {
    const fq = P(t, T(9) + 2.0, 2.4); geoLine(cam, G.routeQingni, { color: C.redL, w: 7, frac: fq, dash: [14, 10] });
    const q = mw(cam, ...G.qingni); const aq = P(t, T(9) + 4.2, 0.5); cross(q[0], q[1], 22, '#fff1d0', 8, aq); label('青泥 · 晋军大败', q[0] + 20, q[1] + 64, { size: 34, fam: SERIF, wt: 900, bar: C.redL, alpha: aq, align: 'left' });
    if (t < T(10)) { const c = mw(cam, ...G.changan); label('义熙十四年十一月 · 弃城东撤', c[0], c[1] - 250, { size: 32, bar: C.gold, alpha: fadeIO(t, T(9) + 0.4, T(9) + 6.3, 0.5, 0.4) }); label('长安易手 —— 距刘裕东归，不到一年', c[0] + 40, c[1] - 250, { size: 32, bar: C.xia, alpha: fadeIO(t, T(9) + 6.6, TE(9) + 0.4, 0.5, 0.4) }); }
  }
  // 城
  city(cam, ...G.changan, '长安', { color: lost ? C.xia : C.red, capital: 1, dy: 48, pulse: (t > T(5) && t < T(6)) || (lost && t < T(10)) ? t : 0 });
  city(cam, ...G.jiankang, '建康', { color: C.red, capital: 1, dy: 46, pulse: t > T(1) + 2.6 && t < T(4) ? t : 0 });
  city(cam, ...G.pengcheng, '彭城', { color: C.red, dx: 16, dy: 0, align: 'left', size: 30, r: 7 }); city(cam, ...G.luoyang, '洛阳', { color: C.red, dy: 42, size: 30, r: 7 }); city(cam, ...G.tongguan, '潼关', { color: C.red, dy: 44, size: 28, r: 6 });
  if (t > T(6) - 0.5) city(cam, ...G.tongwan, '统万', { color: C.xia, capital: 1, alpha: P(t, T(6) - 0.5, 0.6), sub: '夏都' });
  // k0：经略赵魏
  const a0 = fadeIO(t, T(0) + 0.3, TE(0) + 0.3, 0.5, 0.5);
  if (a0 > 0) { const c = mw(cam, ...G.changan); unitBox(c[0] - 150, c[1] - 30, { type: 'inf', color: C.red, name: '刘裕', sub: '九月至长安', alpha: a0, w: 76, h: 50 }); const u = P(t, T(0) + 3.4, 1.4); const q0 = mw(cam, 109.6, 34.9), q1 = mw(cam, 111.3, 36.0); arrow(q0[0], q0[1], q1[0], q1[1], { color: C.redL, w: 6, head: 20, dash: [12, 10], frac: u, alpha: a0 }); label('欲息驾长安，经略赵、魏', q1[0] - 40, q1[1] - 40, { size: 30, bar: C.redL, alpha: a0 * u }); }
  // k1-3：刘穆之
  const a1 = fadeIO(t, T(1) + 1.9, TE(3) + 0.3, 0.5, 0.5);
  if (a1 > 0) {
    const c = mw(cam, ...G.jiankang); label('十一月 · 刘穆之 卒', c[0] - 20, c[1] + 120, { size: 40, fam: SERIF, wt: 900, bar: '#fff', alpha: a1 * (1 - P(t, T(3) - 0.5, 0.4)) }); label('留守建康 · 总管后方：“事无大小，皆决于穆之”', c[0] - 60, c[1] + 190, { size: 26, alpha: a1 * (1 - P(t, T(2) + 0.2, 0.4)) });
    const a2 = fadeIO(t, T(2) + 0.6, TE(3) + 0.3, 0.5, 0.5);
    if (a2 > 0) { const p0 = mw(cam, ...G.pengcheng); const u = P(t, T(2) + 1.2, 1.6); curveArrow([[p0[0] - 6, p0[1] + 20], [p0[0] + 30, (p0[1] + c[1]) / 2], [c[0] - 20, c[1] - 70]], { color: C.gold, w: 6, head: 20, frac: u, alpha: a2 }); label('王弘还建康 · 讽朝廷求九锡', (p0[0] + c[0]) / 2 - 190, (p0[1] + c[1]) / 2 - 40, { size: 30, bar: C.gold, alpha: a2 * u }); label('旨从北来 —— 穆之愧惧', c[0] - 20, c[1] + 120, { size: 40, fam: SERIF, wt: 900, bar: C.gold, alpha: a2 * P(t, T(3) - 0.1, 0.5) }); }
  }
  // k4：十二岁
  const a4b = fadeIO(t, T(4) + 5.2, TE(4) + 0.3, 0.5, 0.5); if (a4b > 0) { const c = mw(cam, ...G.changan); label('留守：刘义真 · 年十二', c[0] + 20, c[1] - 120, { size: 34, fam: SERIF, wt: 900, bar: C.red, alpha: a4b, align: 'left' }); }
  bands(0.55, 0.58);
  // k5：内讧链
  const a5 = fadeIO(t, T(5) + 1.0, TE(5) + 0.5, 0.5, 0.5);
  if (a5 > 0) {
    const rows = [['沈田子', '王镇恶', '义熙十四年正月'], ['王修', '沈田子', '随即'], ['刘义真', '王修', '其后']];
    ctx.save(); ctx.globalAlpha = a5; rrect(60, 262, 960, 366, 10); ctx.fillStyle = 'rgba(14,11,8,0.86)'; ctx.fill(); ctx.fillStyle = C.red; ctx.fillRect(60, 262, 8, 366); ctx.restore();
    const dur = (TE(5) - T(5) - 2.6) / 3;
    for (let i = 0; i < 3; i++) { const t0 = T(5) + 2.2 + i * dur; const u = P(t, t0, 0.5) * a5, v = P(t, t0 + 0.6, 0.35); const y = 330 + i * 116;
      text(rows[i][0], 250, y, { size: 54, fam: SERIF, wt: 900, align: 'center', alpha: u, stroke: 0 }); arrow(380, y, 600, y, { color: C.redL, w: 6, head: 20, frac: P(t, t0 + 0.2, 0.4), alpha: a5 }); text('杀', 490, y - 34, { size: 30, fam: SERIF, wt: 900, align: 'center', alpha: u, color: C.redL, stroke: 0 });
      text(rows[i][1], 760, y, { size: 54, fam: SERIF, wt: 900, align: 'center', alpha: u * (1 - 0.45 * v), stroke: 0 }); if (v > 0) { ctx.save(); ctx.globalAlpha = a5; ctx.strokeStyle = C.red; ctx.lineWidth = 7; ctx.beginPath(); ctx.moveTo(660, y); ctx.lineTo(660 + 200 * v, y); ctx.stroke(); ctx.restore(); }
    }
    label('“人情离骇，莫相统壹”', W / 2, 690, { size: 36, fam: SERIF, wt: 900, alpha: a5 * P(t, TE(5) - 1.6, 0.5), bar: C.gold }); note('—— 《资治通鉴》卷一百一十八', W / 2, 742, a5 * P(t, TE(5) - 1.4, 0.5), 'center');
  }
  // k10：朱超石
  const a10 = fadeIO(t, T(10) + 0.8, s.end, 0.6, 0.5);
  if (a10 > 0) {
    const q = mw(cam, 110.3, 34.66); cross(q[0], q[1] - 30, 14, '#fff1d0', 6, a10); leader(q[0] + 14, q[1] - 40, q[0] + 120, q[1] - 150); label('曹公垒：朱龄石、朱超石兄弟被执', q[0] + 60, q[1] - 180, { size: 28, alpha: a10, bar: C.xia });
    ctx.save(); ctx.globalAlpha = a10; rrect(60, 262, 960, 210, 10); ctx.fillStyle = 'rgba(14,11,8,0.86)'; ctx.fill(); ctx.fillStyle = C.red; ctx.fillRect(60, 262, 8, 210); ctx.restore();
    text('朱超石', 110, 330, { size: 66, fam: SERIF, wt: 900, alpha: a10, stroke: 0 }); text('却月阵指挥者', 360, 340, { size: 32, wt: 700, alpha: a10, stroke: 0, color: C.gold });
    text('“为佛佛所杀，时年三十七”', 110, 420, { size: 40, fam: SERIF, wt: 700, alpha: a10, stroke: 0 }); text('《宋书·朱超石传》', 985, 424, { size: 26, fam: SERIF, wt: 700, alpha: a10, stroke: 0, color: C.gold, align: 'right' });
  }
  compass(990, 250, 1 - Math.max(a5, a10));
}

// ---------------- 收尾 ----------------
function sceneS8(t) {
  const s = TL.secs.s8; const T = k => A('s8', k), TE = k => E('s8', k);
  const x1 = TE(2) + 0.02, x2 = T(4) - 0.5, x3 = T(5) - 0.5, x4 = T(6) - 0.8, d2 = TE(2) - T(2);
  const big = (str, a, y = 640, sz = 76, col = C.cream) => text(str, W / 2, y, { size: sz, fam: SERIF, wt: 900, align: 'center', alpha: a, ls: 5, stroke: 12, color: col });
  if (t < x1 + 0.8) {
    const cam = macCam(kf([[s.start, 113.85, 33.6, 12.4], [T(2), 113.6, 33.7, 11.8], [T(2) + 1.6, 116.6, 33.6, 6.6], [x1 + 0.8, 116.8, 33.5, 6.2]], t));
    drawMacro(cam, 0.3); drawRivers(cam); riverNames(cam, 1, 'he,jiang');
    geoLine(cam, G.routeXia, { color: C.xia, w: 7, alpha: 0.6 });
    city(cam, ...G.changan, '长安', { color: C.xia, capital: 1, dy: 48 }); city(cam, ...G.jiankang, '建康', { color: t > T(2) + 0.74 * d2 ? C.gold : C.red, capital: 1, dy: 46, pulse: t > T(2) ? t : 0 });
    const pc = city(cam, ...G.pengcheng, '彭城', { color: C.red, dx: 18, dy: 0, align: 'left' });
    const a0 = fadeIO(t, s.body - 0.4, T(2) + 0.6, 0.6, 0.6);
    if (a0 > 0) { const c = mw(cam, ...G.changan); const u = P(t, T(0) + 0.3, 2.2); ctx.save(); ctx.globalAlpha = a0; const g = ctx.createLinearGradient(pc[0], pc[1], c[0], c[1]); g.addColorStop(0, 'rgba(255,241,208,0.95)'); g.addColorStop(1, 'rgba(255,241,208,0.05)'); ctx.strokeStyle = g; ctx.lineWidth = 5; ctx.setLineDash([6, 12]); ctx.beginPath(); ctx.moveTo(pc[0], pc[1]); ctx.lineTo(lerp(pc[0], c[0], u), lerp(pc[1], c[1], u)); ctx.stroke(); ctx.restore(); unitBox(pc[0], pc[1] + 80, { type: 'inf', color: C.red, name: '宋公 刘裕', alpha: a0, w: 76, h: 50 }); }
    bands(0.55, 0.58);
    const a2 = fadeIO(t, T(2) + 0.22 * d2, x1 + 0.5, 0.5, 0.4);
    if (a2 > 0) {
      ctx.save(); ctx.globalAlpha = a2; rrect(60, 560, 960, 330, 10); ctx.fillStyle = 'rgba(14,11,8,0.86)'; ctx.fill(); ctx.restore();
      const rows = [['义熙十四年六月', '受相国、宋公、九锡', C.gold, T(2) + 0.30 * d2], ['同年十一月', '长安失守', C.xia, T(2) + 0.52 * d2], ['元熙二年六月（420）', '代晋称帝，国号宋', C.red, T(2) + 0.74 * d2]];
      ctx.save(); ctx.globalAlpha = a2; ctx.strokeStyle = 'rgba(244,234,214,0.4)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(120, 618); ctx.lineTo(120, 838); ctx.stroke(); ctx.restore();
      rows.forEach((r, i) => { const u = P(t, r[3], 0.5) * a2; const y = 618 + i * 110; ctx.save(); ctx.globalAlpha = u; ctx.fillStyle = r[2]; ctx.beginPath(); ctx.arc(120, y, 12, 0, 7); ctx.fill(); ctx.restore(); text(r[0], 160, y - 20, { size: 28, wt: 500, alpha: u, stroke: 0, color: 'rgba(244,234,214,0.85)' }); text(r[1], 160, y + 26, { size: 44, fam: SERIF, wt: 900, alpha: u, stroke: 0, color: i === 1 ? '#d9cfee' : C.cream }); });
    }
  }
  if (t >= x1 && t < x3 + 0.8) {     // 一个阵 / 一条河
    const al = sstep((t - x1) / 0.8); ctx.save(); ctx.globalAlpha = al;
    const tb = BT.pack + 1.5 + (t - x1) * 0.35;
    const cam = tacCam(kf([[x1, 0, 170, 0.6], [x2, 0, 165, 0.66], [x2 + 2.2, 0, -150, 1.0], [x3 + 0.8, 0, -190, 1.05]], t));
    drawBattle(cam, tb, { noChase: true }); bands(0.6, 0.6); ctx.restore();
    if (t > x2 + 0.6) { const a = fadeIO(t, x2 + 1.0, x3 + 0.4, 0.6, 0.4); for (const dx of [-90, 0, 90]) { const p0 = tw(cam, dx, Y0 - 300), p1 = tw(cam, dx * 0.6, Y0 + 20); arrow(p0[0], p0[1], p1[0], p1[1], { color: C.redL, w: 8, head: 22, frac: P(t, x2 + 1.2, 1.2), alpha: a, glow: 'rgba(255,138,102,0.7)' }); } }
  }
  if (t >= x3 && t < x4 + 0.9) {     // 一座建康城
    const al = sstep((t - x3) / 0.8); ctx.save(); ctx.globalAlpha = al;
    const cam = macCam(kf([[x3, 113.85, 33.3, 12.4], [x4 + 0.9, 114.6, 33.1, 11.2]], t));
    drawMacro(cam, 0.3); drawRivers(cam);
    const u = eio(prog(t, x3 + 0.6, x3 + 3.6)); const e = geoLine(cam, G.routeBack, { color: C.red, w: 9, frac: Math.min(1, u * 1.35), glow: 'rgba(226,69,46,0.8)' });
    const pa = mw(cam, ...G.pengcheng), j = mw(cam, ...G.jiankang); if (u > 0.74) arrow(pa[0], pa[1], j[0], j[1] - 16, { color: C.red, w: 9, head: 26, frac: (u - 0.74) / 0.26, glow: 'rgba(226,69,46,0.8)' });
    city(cam, ...G.changan, '长安', { color: C.xia, capital: 1, dy: 48 }); city(cam, ...G.jiankang, '建康', { color: C.gold, capital: 1, dy: 48, pulse: t, size: 44, r: 12 });
    bands(0.6, 0.6); ctx.restore();
  }
  // 三句大字
  const l1 = fadeIO(t, T(3) - 0.2, x4 + 0.3, 0.5, 0.6), l2 = fadeIO(t, T(4) - 0.1, x4 + 0.3, 0.5, 0.6), l3 = fadeIO(t, T(5) - 0.1, x4 + 0.3, 0.5, 0.6);
  if (l1 > 0) big('一个阵，挡住了三万骑', l1 * (t > T(4) - 0.2 ? 0.55 + 0.45 * (1 - P(t, T(4) - 0.2, 0.5)) : 1), 300, 64);
  if (l2 > 0) big('一条河，撑起了这个阵', l2 * (t > T(5) - 0.2 ? 0.55 + 0.45 * (1 - P(t, T(5) - 0.2, 0.5)) : 1), 400, 64);
  if (l3 > 0) big('一座建康城，拉回了整支军队', l3, 500, 64, C.gold);
  if (t >= x4) {
    const al = sstep((t - x4) / 0.9); ctx.fillStyle = `rgba(9,8,7,${al})`; ctx.fillRect(0, 0, W, H);
    const a = fadeIO(t, x4 + 0.5, s.end, 0.8, 0.8); const u = P(t, x4 + 0.4, 1.6);
    ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = C.red; ctx.lineWidth = 12; ctx.shadowColor = 'rgba(226,69,46,0.6)'; ctx.shadowBlur = 26; ctx.beginPath(); ctx.arc(W / 2, 1000, 250, -Math.PI / 2 - Math.PI / 2 * u, -Math.PI / 2 + Math.PI / 2 * u); ctx.stroke(); ctx.shadowBlur = 0; ctx.strokeStyle = '#c9b47a'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(W / 2 - 360 * u, 1012); ctx.lineTo(W / 2 + 360 * u, 1012); ctx.stroke(); ctx.restore();
    const ch = LN('s8', 6).chunks, c1 = ch[ch.length - 1].start, c2 = lerp(c1, TE(6), 0.42);
    text('却月阵是真的。', W / 2, 860, { size: 64, fam: SERIF, wt: 900, align: 'center', alpha: a * P(t, T(6), 0.5), stroke: 0 });
    text('只是刘裕要的，', W / 2, 1110, { size: 56, fam: SERIF, wt: 900, align: 'center', alpha: a * P(t, c1 - 0.1, 0.4), stroke: 0 });
    text('从来不只是长安。', W / 2, 1200, { size: 72, fam: SERIF, wt: 900, align: 'center', alpha: a * P(t, c2 - 0.1, 0.4), stroke: 0, color: C.gold });
  }
}
function sceneEnd(t) {
  const s = TL.secs.end; ctx.fillStyle = '#090807'; ctx.fillRect(0, 0, W, H);
  const a = fadeIO(t, s.start, s.end, 0.8, 1.0);
  text('却月阵', W / 2, 420, { size: 110, fam: SERIF, wt: 900, align: 'center', alpha: a, stroke: 0, ls: 12 });
  ctx.fillStyle = `rgba(226,69,46,${a})`; ctx.fillRect(W / 2 - 40, 510, 80, 4);
  const L = [['史料', C.gold, 34], ['《宋书》武帝纪、朱龄石传附朱超石传、', 0, 30], ['刘康祖传、王弘传、庐陵王义真传', 0, 30], ['《魏书》太宗纪、崔浩传、长孙嵩传', 0, 30], ['《资治通鉴》卷一百一十七、一百一十八、一百二十五', 0, 30], ['', 0, 20], ['说明', C.gold, 34], ['引文、人数、日期均据上列原文', 0, 28], ['尺寸折算、阵形与器械画法为推算和示意', 0, 28], ['古河道与城址为示意；海岸线为今貌', 0, 28], ['地形据公开高程数据（SRTM）晕渲', 0, 28]];
  let y = 620; for (const [s2, c, sz] of L) { if (s2) text(s2, W / 2, y, { size: sz, fam: c ? SANS : SERIF, wt: c ? 700 : 700, align: 'center', alpha: a * (c ? 1 : 0.88), stroke: 0, color: c || C.cream, ls: c ? 10 : 0 }); y += sz + 26; }
}

// ---------------- 总调度 ----------------
function render(t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.shadowBlur = 0; ctx.setLineDash([]);
  const S = TL.secs;
  if (t < S.title.start) sceneCold(t);
  else if (t < S.title.end) sceneTitle(t);
  else if (t < S.s2.start) sceneS1(t);
  else if (t < S.s3.start) sceneS2(t);
  else if (t < S.s4.start) sceneS3(t);
  else if (t < S.s5.start) sceneS4(t);
  else if (t < S.s6.start) sceneS5(t);
  else if (t < S.s7.start) sceneS6(t);
  else if (t < S.s8.start) sceneS7(t);
  else if (t < S.end.start) sceneS8(t);
  else sceneEnd(t);
  ctx.globalAlpha = 1;
  chip(t); quotes(t); subtitles(t); chapterCard(t); post(t);
  if (t < 0.8) { ctx.fillStyle = `rgba(9,8,7,${1 - t / 0.8})`; ctx.fillRect(0, 0, W, H); }
}
async function boot() {
  const cv = document.getElementById('c'); ctx = cv.getContext('2d', { alpha: false, willReadFrequently: location.search.includes('sw=1') });
  const j = async u => (await fetch(u)).json();
  [TL, MACRO, TAC] = await Promise.all([j('timeline.json?' + Date.now()), j('../assets/macro.json'), j('../assets/tactical.json')]);
  const load = (k, u) => new Promise((res, rej) => { const im = new Image(); im.onload = () => { IMG[k] = im; res(); }; im.onerror = rej; im.src = u; });
  await Promise.all([load('macro', '../assets/macro.jpg'), load('tac', '../assets/tactical.jpg')]);
  await document.fonts.load('900 40px "Noto Serif SC"', '却月阵'); await document.fonts.load('700 40px "Noto Sans SC"', '却月阵'); await document.fonts.load('500 40px "Noto Sans SC"', '却月阵'); await document.fonts.load('700 40px "Noto Serif SC"', '却月阵');
  await document.fonts.ready;
  initBattle();
  window.READY = true;
}
window.renderAt = t => { render(t); return true; };
window.frameJPEG = (t, q) => { render(t); return document.getElementById('c').toDataURL('image/jpeg', q || 0.93).slice(23); };
