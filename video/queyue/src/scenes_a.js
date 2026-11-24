// 场景（上）：冷开场、片名、壹～肆
'use strict';

function tacLabels(cam, a = 1) {
  text('北 岸', 90, 0, { alpha: 0 });
}
function dotLegend(a = 1, s = '图中每一点 = 一人 / 一骑') { note(s, 64, 1318, a); }

// ---------------- 冷开场 ----------------
function sceneCold(t) {
  const s = TL.secs.cold; const t0 = A('cold', 0), t1 = E('cold', 1), t2 = A('cold', 2), t3 = A('cold', 3), te = TL.secs.title.start;
  let tb;
  if (t < t2) tb = lerp(BT.mass - 2.5, BT.volley + 2.2, prog(t, t0 - 1, t1 + 0.3));
  else tb = lerp(BT.volley + 2.2, BT.spear + 3, prog(t, t2, te));
  const cam = tacCam(kf([[0, 0, -140, 1.05], [t0 + 1, 0, 60, 0.9], [t1, 0, 215, 0.8], [t2 + 1.2, 0, 120, 0.5], [t3 + 1, 0, 125, 0.5], [te, 0, 170, 0.66]], t));
  drawBattle(cam, tb, { noChase: true });
  bands(0.6, 0.6);
  // 年份
  const a0 = fadeIO(t, t0 - 0.6, t1 + 0.4, 0.7, 0.6);
  if (a0 > 0) {
    text('义熙十三年', 80, 330, { size: 96, fam: SERIF, wt: 900, alpha: a0, ls: 6 });
    text('公元 417 年 · 黄河北岸', 84, 420, { size: 40, fam: SANS, wt: 500, alpha: a0, color: C.gold, ls: 2 });
  }
  const a1 = fadeIO(t, A('cold', 1) + 0.3, t2 + 0.2, 0.5, 0.5);
  if (a1 > 0) {
    const [fx, fy] = tw(cam, 0, Y0 + 70); label('晋军  2,700 人 · 车 100 乘', fx, fy + 30, { size: 32, bar: C.red, alpha: a1 });
    const [wx, wy] = tw(cam, 0, Y0 + 330); const au = fadeIO(t, A('cold', 1) + 3.2, t2 + 0.2, 0.5, 0.5); label('北魏  三万骑', wx, wy, { size: 36, bar: C.wei, alpha: au });
    dotLegend(a1);
  }
  const a2 = fadeIO(t, t2 - 0.1, t3 + 0.3, 0.5, 0.6);
  if (a2 > 0) {
    // 弯月描边
    const [cx, cy] = tw(cam, 0, Y0); const rr = (R_ARC + 6) / cam.mpp; const u = P(t, t2, 1.2);
    ctx.save(); ctx.globalAlpha = a2; ctx.strokeStyle = '#fff1d0'; ctx.lineWidth = 5; ctx.shadowColor = C.redL; ctx.shadowBlur = 26; ctx.beginPath(); ctx.arc(cx, cy, rr, -Math.PI / 2 - Math.PI / 2 * u, -Math.PI / 2 + Math.PI / 2 * u); ctx.stroke(); ctx.restore();
    text('却月阵', W / 2, 400, { size: 150, fam: SERIF, wt: 900, align: 'center', alpha: a2, ls: 14, glow: 'rgba(0,0,0,0.8)', blur: 30 });
  }
  const fo = sstep((t - (te - 0.7)) / 0.7); if (fo > 0) { ctx.fillStyle = `rgba(9,8,7,${fo})`; ctx.fillRect(0, 0, W, H); }
}

// ---------------- 片名 ----------------
function sceneTitle(t) {
  const s = TL.secs.title, u = (t - s.start) / (s.end - s.start);
  ctx.fillStyle = '#090807'; ctx.fillRect(0, 0, W, H);
  const a = fadeIO(t, s.start, s.end, 0.8, 0.7);
  ctx.save(); ctx.globalAlpha = a;
  // 弯月 + 河
  const cx = W / 2, cy = 1010, r = 400; const au = eout(prog(u, 0.02, 0.5));
  ctx.strokeStyle = C.red; ctx.lineWidth = 16; ctx.lineCap = 'butt'; ctx.shadowColor = 'rgba(226,69,46,0.6)'; ctx.shadowBlur = 30;
  ctx.beginPath(); ctx.arc(cx, cy, r, -Math.PI / 2 - Math.PI / 2 * au, -Math.PI / 2 + Math.PI / 2 * au); ctx.stroke(); ctx.shadowBlur = 0;
  ctx.strokeStyle = '#c9b47a'; ctx.lineWidth = 5; const lw = 500 * eout(prog(u, 0.1, 0.6)); ctx.beginPath(); ctx.moveTo(cx - lw, cy + 14); ctx.lineTo(cx + lw, cy + 14); ctx.stroke();
  ctx.strokeStyle = 'rgba(201,180,122,0.45)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(cx - lw * 0.86, cy + 40); ctx.lineTo(cx + lw * 0.86, cy + 40); ctx.stroke();
  ctx.restore();
  text('却月阵', W / 2, 890 + 12 * (1 - eout(u * 2)), { size: 190, fam: SERIF, wt: 900, align: 'center', alpha: a, stroke: 0, ls: 16 });
  text('一个阵 · 一条河 · 一座城', W / 2, 1150, { size: 46, fam: SERIF, wt: 700, align: 'center', alpha: a * sstep((u - 0.25) * 4), color: C.gold, stroke: 0, ls: 6 });
  text('义熙十三年（417）刘裕北伐', W / 2, 1230, { size: 32, fam: SANS, wt: 500, align: 'center', alpha: a * sstep((u - 0.35) * 4) * 0.85, stroke: 0, ls: 3 });
  text('细节与胜负手', W / 2, 520, { size: 34, fam: SANS, wt: 700, align: 'center', alpha: a * 0.8, color: C.cream, stroke: 0, ls: 14 });
  ctx.fillStyle = `rgba(226,69,46,${a})`; ctx.fillRect(W / 2 - 30, 560, 60, 4);
}

// ---------------- 壹 · 被河岸牵着走 ----------------
const S1SHIPS = [];
function sceneS1(t) {
  const s = TL.secs.s1; const tx = A('s1', 2) - 0.5;     // 切到河面
  if (t < tx + 0.9) {
    const cam = macCam(kf([[s.start, 113.9, 33.7, 12.2], [A('s1', 0) + 1, 113.9, 33.7, 12.2], [E('s1', 0), 113.4, 33.9, 11.2], [A('s1', 1) + 1.0, 115.2, 35.2, 6.6], [tx + 0.9, 115.0, 35.7, 5.2]], t));
    drawMacro(cam); drawRivers(cam);
    const b = s.body;
    region(cam, '北魏', 114.8, 38.3, C.wei, P(t, b, 1)); region(cam, '后秦', 108.2, 35.4, C.qin, P(t, b, 1)); region(cam, '东晋', 116.6, 30.9, C.red, P(t, b, 1)); region(cam, '夏', 108.6, 38.6, C.xia, P(t, b, 1), 44);
    riverNames(cam, P(t, b + 0.5, 1), 'he,wei,jiang');
    // 水军：建康→彭城（义熙十二年）
    const fa = P(t, A('s1', 0) - 0.3, 2.2); geoLine(cam, G.routeA, { color: C.red, w: 7, frac: fa, glow: 'rgba(226,69,46,0.7)' });
    // 前锋陆路
    const fv = P(t, A('s1', 0) + 2.4, 3.6); const ev = geoLine(cam, G.routeV, { color: C.redL, w: 5, frac: fv, dash: [14, 10] });
    if (ev && fv > 0.1) label('前锋 王镇恶、檀道济（陆路）', Math.max(ev[0] + 20, 70), ev[1] + 62, { size: 26, bar: C.redL, alpha: P(t, A('s1', 0) + 2.8, 0.6), align: 'left' });
    // 主力入河
    const fb = P(t, A('s1', 1) - 0.2, 2.6); const eb = geoLine(cam, G.routeB, { color: C.red, w: 7, frac: fb, glow: 'rgba(226,69,46,0.7)' });
    const fc = P(t, A('s1', 1) + 2.2, 3.2) * 0.17; const ec = geoLine(cam, G.routeC, { color: C.red, w: 7, frac: fc, glow: 'rgba(226,69,46,0.7)' });
    const head = ec || eb || null;
    const ca = P(t, b + 0.2, 0.8);
    city(cam, ...G.jiankang, '建康', { alpha: ca, color: C.red, capital: 1, dy: 44 }); city(cam, ...G.pengcheng, '彭城', { alpha: ca, color: C.red, dx: 16, dy: 0, align: 'left' });
    city(cam, ...G.luoyang, '洛阳', { alpha: ca, dy: 42, color: C.qin }); city(cam, ...G.tongguan, '潼关', { alpha: ca, dy: 44, color: C.qin, r: 7, size: 30 }); city(cam, ...G.changan, '长安', { alpha: ca, color: C.qin, capital: 1, dy: 46 });
    city(cam, ...G.pingcheng, '平城', { alpha: ca, color: C.wei, capital: 1 });
    if (head && fb > 0.02) unitBox(head[0], head[1] - 10, { type: 'navy', color: C.red, name: '刘裕 水军主力', alpha: P(t, A('s1', 1), 0.6) });
    const am = fadeIO(t, A('s1', 1) + 0.3, tx + 0.6, 0.5, 0.4); if (am > 0) label('义熙十三年三月 · 入河', W / 2, 600, { size: 34, bar: C.red, alpha: am });
    bands(0.5, 0.55); compass(990, 250, ca);
  }
  if (t >= tx) {
    const al = sstep((t - tx) / 0.9); ctx.save(); ctx.globalAlpha = al; sceneS1River(t); ctx.restore();
  }
}
function sceneS1River(t) {
  const t2 = A('s1', 2), tq = A('s1', 3), te = TL.secs.s1.end;
  const V = 4.0, drift = (t - t2) * V;                 // 船队西行（画面随行）
  const cam = tacCam(kf([[t2 - 1, 200, -205, 0.66], [tq, 200, -200, 0.63], [A('s1', 5), 200, -175, 0.62], [A('s1', 6) + 0.5, 200, -110, 0.56], [A('s1', 7), 200, -130, 0.6], [te, 200, -190, 0.7]], t));
  cam.cx -= drift;
  drawTac(cam); drawFlow(cam, t, 0.2);
  const sc = 1 / cam.mpp, SL = 54;
  const shipX = i => 560 - i * 88, snap = tq + 2.0, hit = A('s1', 4) + 1.4;
  const dsx0 = shipX(4) - (snap - t2) * V, dsx1 = dsx0 + 110;          // 漂船起止 x
  // 北岸魏骑：缘河随行
  const land = A('s1', 6) + 0.3, back = A('s1', 6) + 2.7, lx0 = 150 - (land - t2) * V;
  const paths = [new Path2D(), new Path2D()], ps = Math.max(2.6, 1.9 * sc);
  for (let k = 0; k < 1100; k++) {
    let x = 700 - hash(k, 1) * 1150 - drift + Math.sin(t * 0.7 + k) * 3, y = bankN(x) + 26 + hash(k, 2) * 110 + Math.sin(t * 1.3 + k * 2) * 1.5;
    const lx = lx0 - (t - land) * V; const near = clamp(1 - Math.abs(x - lx) / 200);
    const ret = sstep((t - land + 0.6) / 1.4) * (1 - sstep((t - back - 0.8) / 2.0)); y += near * ret * (130 + 70 * hash(k, 3));
    if (k < 90) { const u = eio(prog(t, hit - 2.4 + hash(k, 4), hit - 0.3 + hash(k, 4) * 0.4)), v = eio(prog(t, hit + 1.8, hit + 4.5)); const tx = dsx1 + (hash(k, 5) - 0.5) * 60, ty = bankN(dsx1) + 3 + hash(k, 6) * 18; x = lerp(x, tx, u * (1 - v)); y = lerp(y, ty, u * (1 - v)); }
    const [px, py] = tw(cam, x, y); if (px < -5 || px > W + 5) continue; paths[k % 2].rect(px - ps / 2, py - ps / 2, ps, ps * 0.9);
  }
  ctx.save(); ctx.translate(1.5, 1.8); ctx.fillStyle = 'rgba(12,22,30,0.6)'; ctx.fill(paths[0]); ctx.fill(paths[1]); ctx.restore();
  ctx.fillStyle = '#6fbfec'; ctx.fill(paths[0]); ctx.fillStyle = '#d2efff'; ctx.fill(paths[1]);
  // 船队：贴南岸，纤夫在岸上
  for (let i = 0; i < 9; i++) {
    let x = shipX(i) - drift, y = bankS(x) + 44 + (i % 2) * 22, dark = 0, ang = Math.PI, tow = true;
    const hx = x - 70, hy = bankS(hx) - 10;
    if (i === 4 && t > snap) { tow = false; const u = prog(t, snap, hit - 0.2); x = lerp(dsx0, dsx1, u); y = lerp(bankS(dsx0) + 44, bankN(dsx1) - 16, eio(u)); ang = Math.PI + eio(u) * 1.1; if (t > hit) dark = sstep((t - hit) / 1.0); }
    const [px, py] = tw(cam, x, y);
    if (tow) { const [qx, qy] = tw(cam, hx, hy); ctx.strokeStyle = 'rgba(244,232,200,0.9)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(px - SL * 0.45 * sc, py); ctx.lineTo(qx, qy); ctx.stroke(); ctx.fillStyle = C.redL; for (let k = 0; k < 14; k++) { const [ax, ay] = tw(cam, hx - k * 2.6 + Math.sin(t * 6 + k) * 0.3, hy - (k % 2) * 2.2); ctx.fillRect(ax - 2, ay - 2, 4, 4); } }
    drawShip(px, py, SL * sc, ang, i === 2, 1, dark);
    if (i === 4 && t > snap) {
      if (t > hit - 0.1) cross(px, py, 34, '#fff1d0', 7, sstep((t - hit) / 0.3) * fadeIO(t, hit, A('s1', 5) + 1, 0.3, 0.6));
      const la = fadeIO(t, snap + 0.2, A('s1', 5) + 0.6, 0.4, 0.5); if (la > 0) label(t < hit - 0.3 ? '纤断 · 漂向北岸' : '为虏所杀略', px, py + 74, { size: 30, bar: C.redL, alpha: la });
    }
    if (i === 6) { const la = fadeIO(t, t2 + 0.6, tq + 5.5, 0.5, 0.5); if (la > 0) { const [qx, qy] = tw(cam, hx, hy); const mx = (px + qx) / 2 - 10, my = (py + qy) / 2; leader(mx, my, mx + 30, my - 110); label('百丈 = 纤绳', mx + 30, my - 136, { size: 32, alpha: la, bar: C.gold }); const [ax, ay] = tw(cam, hx - 20, hy); label('纤夫', ax - 10, ay + 44, { size: 26, alpha: la, bar: C.redL }); } }
  }
  // 登岸分队
  if (t > land - 2.6 && t < back + 3.6) {
    const u = eio(prog(t, land - 2.4, land - 0.2)), v = eio(prog(t, back, back + 2.6)); const bx = lx0 - (t - land) * V;
    for (let b = 0; b < 4; b++) { const x = bx + (b - 1.5) * 24, y = lerp(bankN(x) - 300, bankN(x) - 9, u) - v * 300; const [px, py] = tw(cam, x, y); drawShip(px, py, 20 * sc, v > 0 ? Math.PI / 2 : -Math.PI / 2, false); }
    const w = eio(prog(t, land - 0.2, land + 1.2)) * (1 - eio(prog(t, back - 1.0, back + 0.2)));
    if (t > land - 0.2 && t < back + 0.3) { ctx.fillStyle = C.red; for (let k = 0; k < 220; k++) { const x = bx + (hash(k, 7) - 0.5) * 100, y = bankN(x) - 2 + w * (8 + hash(k, 8) * 66); const [px, py] = tw(cam, x, y); ctx.fillRect(px - 2, py - 2, 4, 4); } }
    const la = fadeIO(t, land - 0.4, back + 3.4, 0.4, 0.5); const [px, py] = tw(cam, bx, bankN(bx) + 250);
    label(t < back ? '遣军登岸 —— 魏军退走' : '军还 —— 魏军复来', W / 2, py, { size: 34, bar: C.gold, alpha: la });
  }
  // 标注
  const a = P(t, t2 - 0.3, 0.8);
  const [, ny] = tw(cam, 0, bankN(cam.cx) + 185), [, sy] = tw(cam, 0, bankS(cam.cx) - 55), [, ry] = tw(cam, 0, (bankN(cam.cx) + bankS(cam.cx)) / 2 + 20);
  const quoteOn = t > tq - 0.6 && t < A('s1', 5);
  text('北岸 · 北魏', 1010, Math.max(ny, 560), { size: 36, fam: SERIF, wt: 900, alpha: a * (quoteOn ? 0 : 0.95), color: C.wei, align: 'right' });
  text('南岸 · 东晋', 1010, Math.min(sy, 1350), { size: 36, fam: SERIF, wt: 900, alpha: a * 0.95, color: C.redL, align: 'right' });
  text('黄  河', W / 2, ry, { size: 46, fam: SERIF, wt: 900, alpha: a * 0.3, align: 'center', ls: 30, stroke: 0, color: '#f0e4c0' });
  arrow(800, ry + 84, 960, ry + 84, { color: 'rgba(240,228,192,0.5)', w: 4, head: 14, alpha: a }); text('水流', 880, ry + 120, { size: 26, wt: 500, align: 'center', alpha: a * 0.7, stroke: 4 });
  arrow(280, ry + 84, 120, ry + 84, { color: C.redL, w: 5, head: 16, alpha: a * 0.95 }); text('船队逆流西上', 200, ry + 120, { size: 26, wt: 500, align: 'center', alpha: a * 0.95, stroke: 4 });
  const a5 = fadeIO(t, A('s1', 5) + 0.2, A('s1', 6) + 0.1, 0.5, 0.5);
  if (a5 > 0) { const [, y] = tw(cam, 0, bankN(cam.cx) + 250); label('北魏 步骑十万 屯河北', W / 2, y - 64, { size: 34, bar: C.wei, alpha: a5 }); label('数千骑 缘河随行', W / 2, y, { size: 34, bar: C.wei, alpha: sstep((t - A('s1', 5) - 2.4) / 0.5) * a5 }); }
  bands(0.5, 0.6); note('示意：船与人已放大', 64, 1318, a * 0.9);
}

// ---------------- 贰 · 平城的算盘 ----------------
function sceneS2(t) {
  const s = TL.secs.s2, b = s.body;
  const cam = macCam(kf([[s.start, 113.9, 37.3, 8.6], [A('s2', 1), 114.2, 37.2, 8.0], [A('s2', 2), 112.3, 37.0, 9.6], [A('s2', 4), 112.3, 37.0, 9.6], [A('s2', 4) + 2.5, 114.6, 37.2, 6.6], [s.end, 114.8, 37.0, 6.0]], t));
  drawMacro(cam, 0.12); drawRivers(cam);
  region(cam, '北魏', 115.3, 38.6, C.wei, 1); region(cam, '后秦', 108.4, 35.6, C.qin, 1, 46); riverNames(cam, 1, 'he');
  const fleet = mw(cam, 115.62, 36.18);
  // 群臣：拦
  const a1 = fadeIO(t, A('s2', 1) + 1.6, A('s2', 2) + 0.2, 0.5, 0.6);
  if (a1 > 0) {
    const p0 = mw(cam, 114.4, 37.9), p1 = mw(cam, 115.2, 36.25);
    arrow(p0[0], p0[1], p1[0], p1[1], { color: C.wei, w: 9, head: 26, frac: P(t, A('s2', 1) + 1.7, 1.0), alpha: a1, glow: 'rgba(120,200,240,0.6)' });
    label('群臣：发兵断河上流，勿令西过', p0[0] - 30, p0[1] - 34, { size: 28, bar: C.wei, alpha: a1 });
    const q0 = mw(cam, 115.75, 36.45), q1 = mw(cam, 116.3, 37.6);
    arrow(q0[0], q0[1], q1[0], q1[1], { color: C.redL, w: 6, head: 20, dash: [12, 10], frac: P(t, A('s2', 1) + 4.2, 1.0), alpha: a1 });
    label('恐其“声西而实北”？', q1[0] - 20, q1[1] - 36, { size: 28, bar: C.redL, alpha: a1 * P(t, A('s2', 1) + 4.6, 0.5) });
  }
  // 崔浩：假道
  const a2 = fadeIO(t, A('s2', 2) + 0.3, A('s2', 4) + 0.6, 0.6, 0.6);
  if (a2 > 0) {
    const f = P(t, A('s2', 2) + 0.6, 4.0); geoLine(cam, G.routeC, { color: C.redL, w: 7, from: 0.14, frac: 0.14 + 0.86 * f, glow: 'rgba(255,138,102,0.6)', alpha: a2, dash: [18, 10] });
    geoLine(cam, G.routeD, { color: C.redL, w: 7, frac: P(t, A('s2', 2) + 4.2, 1.2), alpha: a2, dash: [18, 10] });
    const g = mw(cam, 109.0, 34.4); const u = P(t, A('s2', 2) + 5.0, 0.8);
    ctx.save(); ctx.globalAlpha = a2 * u; ctx.strokeStyle = C.gold; ctx.lineWidth = 4; ctx.setLineDash([10, 8]); ctx.beginPath(); ctx.ellipse(g[0], g[1], 150 * cam.s / 0.4, 70 * cam.s / 0.4, -0.1, 0, 7); ctx.stroke(); ctx.restore();
    label('关中：悬远难守', g[0] + 10, g[1] + 86, { size: 30, bar: C.gold, alpha: a2 * u });
    const m = mw(cam, 112.6, 35.5); label('崔浩：假之水道，纵裕西入', m[0], m[1] - 6, { size: 28, bar: C.redL, alpha: a2 * P(t, A('s2', 2) + 1.2, 0.6) });
    // 柔然（崔浩的理由）
    const ru = P(t, A('s2', 3) + 0.3, 0.6); const pc = mw(cam, ...G.pingcheng);
    arrow(pc[0] - 130, pc[1] + 180, pc[0] - 130, pc[1] + 110, { color: '#d7d2c4', w: 6, head: 18, alpha: a2 * ru }); label('北有柔然入寇 · 国内乏食（崔浩语）', pc[0] + 110, pc[1] + 146, { size: 26, bar: '#d7d2c4', alpha: a2 * ru });
  }
  const ca = P(t, b - 0.4, 0.8);
  city(cam, ...G.pingcheng, '平城', { alpha: ca, color: C.wei, capital: 1, pulse: t < A('s2', 1) ? t - b + 10 : 0, sub: '北魏都城 · 明元帝拓跋嗣', dy: 48 });
  city(cam, ...G.luoyang, '洛阳', { alpha: ca, dy: 42, color: C.qin, size: 30, r: 7 }); city(cam, ...G.tongguan, '潼关', { alpha: ca, dy: 42, color: C.qin, r: 7, size: 30 }); city(cam, ...G.changan, '长安', { alpha: ca, color: C.qin, capital: 1, dy: 46 });
  unitBox(fleet[0], fleet[1], { type: 'navy', color: C.red, name: '刘裕 水军', alpha: ca, w: 76, h: 50 });
  // 长孙嵩南下
  const a4 = P(t, A('s2', 4) + 0.6, 0.6);
  if (a4 > 0) {
    const u = eio(prog(t, A('s2', 4) + 1.0, A('s2', 4) + 3.6)); const p = [lerp(113.5, 115.05, u), lerp(39.6, 37.15, u)]; const q = mw(cam, p[0], p[1]);
    unitBox(q[0], q[1], { type: 'cav', color: C.wei, name: '司徒 长孙嵩', sub: u > 0.95 ? '步骑十万 屯河北岸' : '', alpha: a4 });
    // 跟、咬、走
    const t5 = A('s2', 4) + 4.4; if (t > t5) for (let k = 0; k < 3; k++) { const ph = ((t - t5) / 2.2 + k / 3) % 1; const x0 = mw(cam, 115.3 + k * 0.3, 36.85 - k * 0.02), x1 = mw(cam, 115.4 + k * 0.3, 36.42 + k * 0.08); const f = ph < 0.5 ? ph * 2 : 2 - ph * 2; arrow(x0[0], x0[1], x1[0], x1[1], { color: C.wei, w: 5, head: 14, frac: eio(f), alpha: 0.9 }); }
  }
  bands(0.5, 0.55); compass(990, 250, ca);
}

// ---------------- 叁 · 一道弯月 ----------------
function sceneS3(t) {
  const s = TL.secs.s3;
  const zy = Y0 + 128;
  const cam = tacCam(kf([[s.start, 0, 10, 0.74], [A('s3', 1) + 1, 0, 60, 0.5], [A('s3', 2) + 0.5, 0, 82, 0.44], [E('s3', 2), 0, 82, 0.44], [A('s3', 3) + 1.8, 0, zy, 0.105], [A('s3', 3) + 3.0, 0, zy - 22, 0.14], [E('s3', 3) - 0.2, 0, zy - 30, 0.16], [A('s3', 4) + 1.6, 0, 290, 0.8], [E('s3', 5) + 0.3, 0, 280, 0.78], [A('s3', 6) + 1.8, 0, 78, 0.46], [E('s3', 6) - 1.4, 0, 82, 0.44], [A('s3', 7) + 1.2, 30, zy + 10, 0.075], [s.end, 30, zy + 6, 0.082]], t));
  drawBattle(cam, t, { noMissiles: true });
  bands(0.55, 0.6);
  const sc = 1 / cam.mpp;
  // 丁旿 登岸
  const a1 = fadeIO(t, BT.land + 0.4, A('s3', 3) + 0.6, 0.5, 0.6);
  if (a1 > 0) {
    const [x, y] = tw(cam, 0, Y0 + 40); label('白直队主 丁旿 · 七百人 · 车百乘', x, y + 150 / cam.mpp * 0 + 36 * sc * 0 + 30, { size: 32, bar: C.red, alpha: a1 * (1 - P(t, A('s3', 2) + 0.2, 0.5)) });
  }
  // 尺寸标注
  const a2 = fadeIO(t, BT.arcDone + 3.4, E('s3', 2) + 0.3, 0.6, 0.5);
  if (a2 > 0) {
    const [x0, y0] = tw(cam, 0, Y0), [x1, y1] = tw(cam, 0, Y0 + R_ARC); const u = P(t, BT.arcDone + 3.5, 1.0);
    ctx.save(); ctx.globalAlpha = a2; ctx.strokeStyle = C.gold; ctx.lineWidth = 4; ctx.setLineDash([12, 8]); ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x0, lerp(y0, y1, u)); ctx.stroke(); ctx.setLineDash([]);
    ctx.beginPath(); ctx.moveTo(x0 - 14, y0); ctx.lineTo(x0 + 14, y0); ctx.moveTo(x0 - 14, y1); ctx.lineTo(x0 + 14, y1); ctx.stroke(); ctx.restore();
    label('去水百余步', x0 + 26, (y0 + y1) / 2 - 24, { size: 34, fam: SERIF, wt: 900, align: 'left', alpha: a2 * u, bar: C.gold });
    label('≈150 米（晋尺折算 · 推算）', x0 + 26, (y0 + y1) / 2 + 32, { size: 24, wt: 500, align: 'left', alpha: a2 * u });
    const e0 = tw(cam, -R_ARC, Y0), e1 = tw(cam, R_ARC, Y0); const v = P(t, A('s3', 2) + 5.0, 0.6);
    for (const e of [e0, e1]) { ctx.save(); ctx.globalAlpha = a2 * v; ctx.strokeStyle = '#fff1d0'; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(e[0], e[1] - 6, 30, 0, 7); ctx.stroke(); ctx.restore(); }
    label('两头抱河', e0[0] + 6, e0[1] + 58, { size: 30, fam: SERIF, wt: 900, alpha: a2 * v }); label('两头抱河', e1[0] - 6, e1[1] + 58, { size: 30, fam: SERIF, wt: 900, alpha: a2 * v });
    note('若近半圆，弧长约 470 米：百车首尾相接（推算）', W / 2, 1300, a2 * P(t, A('s3', 2) + 6.5, 0.6), 'center');
  }
  // 每车七人
  const a3 = fadeIO(t, A('s3', 3) + 1.4, A('s3', 3) + 3.2, 0.5, 0.4);
  if (a3 > 0) { const w = WAG[50]; const [x, y] = tw(cam, w.x, w.y - 4); leader(x, y + 20, x + 150, y + 190); label('车置七仗士（每车七人）', x + 150, y + 220, { size: 32, bar: C.red, alpha: a3 }); }
  const a3b = fadeIO(t, BT.flag + 0.5, E('s3', 3) + 0.2, 0.4, 0.4);
  if (a3b > 0) { const [x, y] = tw(cam, 0, Y0 + 62); leader(x + 30, y - 40, x + 170, y - 120); label('白毦：举起，即是信号', x + 170, y - 150, { size: 32, bar: '#ffffff', alpha: a3b, align: 'left' }); }
  // 魏骑观望
  const a4 = fadeIO(t, A('s3', 4) + 1.0, E('s3', 5) + 0.6, 0.6, 0.5);
  if (a4 > 0) { const [x, y] = tw(cam, 0, Y0 + 610); label('魏军 数千骑', x, y - 40, { size: 36, bar: C.wei, alpha: a4 }); }
  // 朱超石
  const a6 = fadeIO(t, BT.zhu + 0.2, E('s3', 6) - 1.2, 0.5, 0.5);
  if (a6 > 0) { const [x, y] = tw(cam, 0, Y0 - 30); label('宁朔将军 朱超石 · 二千人 · 大弩百张', x, y + 70, { size: 32, bar: C.red, alpha: a6 * (1 - P(t, BT.shields - 0.5, 0.5)) }); const [ax, ay] = tw(cam, 0, Y0 + R_ARC + 14); label('设彭排于辕上 —— 车辕架起大盾', ax, ay - 46, { size: 32, bar: '#f2dfb4', alpha: a6 * P(t, BT.shields + 0.2, 0.5) }); }
  // 27 人/车
  const a7 = P(t, A('s3', 7) + 1.2, 0.6);
  if (a7 > 0) {
    const y = 600; ctx.save(); ctx.globalAlpha = a7; rrect(120, y - 70, 840, 250, 10); ctx.fillStyle = 'rgba(12,10,8,0.8)'; ctx.fill(); ctx.restore();
    text('7 + 20 = 27 人 / 车', W / 2, y, { size: 64, fam: SERIF, wt: 900, align: 'center', alpha: a7, stroke: 0 });
    const a8 = P(t, A('s3', 7) + 3.4, 0.6); text('× 100 车 = 2,700 人', W / 2, y + 100, { size: 64, fam: SERIF, wt: 900, align: 'center', alpha: a8, color: C.redL, stroke: 0 });
  }
  dotLegend(fadeIO(t, s.body, s.end, 0.6, 0.6) * 0.9, '图中每一点 = 一人 / 一骑');
}

// ---------------- 肆 · 截槊 ----------------
function sceneS4(t) {
  const s = TL.secs.s4; const d0 = A('s4', 6) + 0.9, d1 = E('s4', 8) - 1.6;
  const cam = tacCam(kf([[s.start, 0, 170, 0.66], [A('s4', 1), 0, 170, 0.62], [A('s4', 3) - 1.2, 0, 170, 0.6], [A('s4', 3) + 1.2, 0, 255, 0.86], [E('s4', 3), 0, 255, 0.84], [A('s4', 4) + 0.6, 0, 180, 0.62], [A('s4', 5) + 2.2, 0, 165, 0.52], [d0, 0, 160, 0.5], [d1, -80, Y0 + 148, 0.2], [d1 + 0.01, -80, Y0 + 148, 0.2], [A('s4', 9) - 0.2, -70, Y0 + 150, 0.24], [A('s4', 9) + 2.6, 0, 300, 0.88], [A('s4', 10) + 2, 0, 330, 0.9], [s.end, 0, 380, 0.92]], t));
  drawBattle(cam, t);
  bands(0.55, 0.6);
  // 标签
  const a0 = fadeIO(t, BT.adv1 + 1.0, A('s4', 1) + 0.2, 0.5, 0.4); if (a0 > 0) { const [x, y] = tw(cam, 0, Y0 + 340); label('魏军进围', x, y, { size: 34, bar: C.wei, alpha: a0 }); }
  const a1 = fadeIO(t, BT.soft + 0.8, A('s4', 3) - 0.3, 0.5, 0.4); if (a1 > 0) { const [x, y] = tw(cam, 0, Y0 + 70); label('软弓 · 小箭 —— 示弱', x, y, { size: 34, bar: C.red, alpha: a1 }); const [x2, y2] = tw(cam, 0, Y0 + 300); label('“众少兵弱” —— 四面俱至', x2, y2, { size: 32, bar: C.wei, alpha: a1 * P(t, BT.adv2, 0.6) }); }
  const a3 = fadeIO(t, BT.mass + 1.6, A('s4', 4) + 0.2, 0.5, 0.4); if (a3 > 0) { const [x, y] = tw(cam, 0, Y0 + 520); label('南平公 长孙嵩 · 三万骑', x, y, { size: 40, bar: C.wei, alpha: a3 }); const [x2, y2] = tw(cam, 0, Y0 + 76); label('2,700 人', x2, y2, { size: 32, bar: C.red, alpha: a3 }); }
  const a4 = fadeIO(t, BT.volley - 0.1, A('s4', 5) - 0.2, 0.2, 0.4); if (a4 > 0) { const [x, y] = tw(cam, 0, Y0 + 60); label('百弩俱发', x, y, { size: 44, fam: SERIF, wt: 900, bar: C.redL, alpha: a4 }); }
  // 断槊示意图
  const ad = fadeIO(t, d0, d1, 0.6, 0.6); if (ad > 0) drawSpearDiagram(t - d0, ad, A('s4', 7) - d0);
  // 阵前近景标注
  const a9 = fadeIO(t, d1 + 0.2, A('s4', 9) + 0.6, 0.4, 0.4); if (a9 > 0) { label('一矟辄洞贯三四虏', W / 2, 640, { size: 40, fam: SERIF, wt: 900, bar: C.redL, alpha: a9 }); }
  const ar = fadeIO(t, BT.rout + 1.2, A('s4', 10) + 0.4, 0.5, 0.5); if (ar > 0) { const [x, y] = tw(cam, 0, Y0 + 520); label('魏军奔溃', x, y, { size: 44, fam: SERIF, wt: 900, bar: C.wei, alpha: ar }); }
  // 阵斩阿薄干
  const ab = fadeIO(t, A('s4', 10) + 0.2, BT.chase + 0.12 * BT.D, 0.4, 0.5);
  if (ab > 0) { const [x, y] = tw(cam, -52, Y0 + 176); cross(x, y, 16, '#fff1d0', 6, ab); leader(x - 12, y - 6, x - 150, y - 110); label('临阵斩 阿薄干', x - 150, y - 140, { size: 34, bar: C.redL, alpha: ab }); }
  const ac = fadeIO(t, BT.chase + 0.1 * BT.D, s.end, 0.4, 0.4);
  if (ac > 0) { const u = eio(prog(t, BT.chase, BT.chase + 0.3 * BT.D)); const [x, y] = tw(cam, 30, Y0 + R_ARC + 14 + u * 330); const late = t > BT.chase + 0.36 * BT.D; label(late ? '复为虏所围 · 奋击尽日，杀虏千计' : '朱超石、胡藩、刘荣祖 追击', x, y - 130, { size: 32, bar: late ? C.gold : C.red, alpha: ac }); }
  dotLegend(fadeIO(t, s.body, s.end, 0.6, 0.6) * (1 - ad) * 0.9);
}

// 人物/马匹简笔
function limb(x0, y0, x1, y1, w, col) { ctx.strokeStyle = col; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke(); }
function horseman(x, gy, k, col, colD, hit = 0, lean = 0) {     // 面向左；k=像素/米
  ctx.save(); ctx.translate(x, gy); ctx.rotate(lean);
  const bl = 1.9 * k, bh = 0.62 * k, by = -1.25 * k, ol = '#0f1a22';
  ctx.lineJoin = 'round';
  // 腿（先描边后填色）
  for (const lx of [-0.72, -0.5, 0.52, 0.74]) { limb(lx * k, by + bh * 0.3, lx * k + (lx < 0 ? -0.1 : 0.08) * k, -0.04 * k, 0.15 * k + 6, ol); limb(lx * k, by + bh * 0.3, lx * k + (lx < 0 ? -0.1 : 0.08) * k, -0.04 * k, 0.15 * k, colD); }
  limb(0.92 * k, by - 0.1 * k, 1.2 * k, by + 0.5 * k, 0.11 * k + 6, ol); limb(0.92 * k, by - 0.1 * k, 1.2 * k, by + 0.5 * k, 0.11 * k, colD);       // 尾
  // 躯干 + 颈头
  const shape = () => { ctx.beginPath(); ctx.ellipse(0, by, bl / 2, bh / 2, 0, 0, 7); ctx.moveTo(-0.62 * k, by - 0.2 * k); ctx.lineTo(-1.12 * k, by - 0.88 * k); ctx.lineTo(-1.2 * k, by - 1.0 * k); ctx.lineTo(-1.26 * k, by - 0.86 * k); ctx.lineTo(-1.6 * k, by - 0.58 * k); ctx.lineTo(-1.5 * k, by - 0.42 * k); ctx.lineTo(-1.14 * k, by - 0.5 * k); ctx.lineTo(-0.74 * k, by + 0.16 * k); ctx.closePath(); };
  shape(); ctx.strokeStyle = ol; ctx.lineWidth = 7; ctx.stroke(); ctx.fillStyle = col; ctx.fill();
  // 骑手
  const ry = by - bh / 2, rc = hit ? '#7a4b40' : colD;
  limb(-0.02 * k, ry + 0.1 * k, -0.22 * k, ry + 0.86 * k, 0.17 * k + 6, ol); limb(-0.02 * k, ry + 0.1 * k, -0.22 * k, ry + 0.86 * k, 0.17 * k, rc);
  limb(0, ry + 0.06 * k, -0.08 * k, ry - 0.66 * k, 0.34 * k + 6, ol); limb(0, ry + 0.06 * k, -0.08 * k, ry - 0.66 * k, 0.34 * k, rc);
  ctx.fillStyle = ol; ctx.beginPath(); ctx.arc(-0.12 * k, ry - 0.98 * k, 0.17 * k + 3, 0, 7); ctx.fill(); ctx.fillStyle = rc; ctx.beginPath(); ctx.arc(-0.12 * k, ry - 0.98 * k, 0.17 * k, 0, 7); ctx.fill();
  limb(-0.1 * k, ry - 0.5 * k, -0.6 * k, ry - 0.36 * k, 0.12 * k, rc);
  ctx.restore();
}
function footman(x, fy, k, col, o = {}) {       // 面向右
  ctx.save(); ctx.translate(x, fy);
  const hip = -0.88 * k, sh = -1.42 * k, lean = o.lean || 0;
  limb(-0.02 * k, hip, -0.2 * k + (o.stride || 0) * -k, 0, 0.17 * k, col); limb(0.02 * k, hip, 0.24 * k + (o.stride || 0) * k, 0, 0.17 * k, col);
  limb(0, hip, lean * k, sh, 0.36 * k, col);
  ctx.fillStyle = col; ctx.beginPath(); ctx.arc(lean * k + 0.03 * k, sh - 0.3 * k, 0.17 * k, 0, 7); ctx.fill();
  if (o.hands) { limb(lean * k, sh + 0.08 * k, o.hands[0], o.hands[1], 0.13 * k, col); }
  if (o.hands2) { limb(lean * k, sh + 0.08 * k, o.hands2[0], o.hands2[1], 0.13 * k, col); }
  ctx.restore();
}
function drawSpearDiagram(lt, a, tq) {
  const k = 104, gy = 1235, y0 = 560, y1 = 1330;
  ctx.save(); ctx.globalAlpha = a;
  ctx.fillStyle = 'rgba(16,13,10,0.95)'; ctx.fillRect(0, y0, W, y1 - y0);
  ctx.fillStyle = C.gold; ctx.fillRect(0, y0, W, 3); ctx.fillRect(0, y1 - 3, W, 3);
  // 细网格
  ctx.strokeStyle = 'rgba(220,183,108,0.07)'; ctx.lineWidth = 1; for (let x = 0; x < W; x += 52) { ctx.beginPath(); ctx.moveTo(x, y0); ctx.lineTo(x, y1); ctx.stroke(); } for (let y = y0; y < y1; y += 52) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  text('断矟锤击 · 剖面示意', 60, y0 + 50, { size: 38, fam: SERIF, wt: 900, stroke: 0, color: C.cream });
  text('示意图：史书只记其事，器械形制与比例为推测', 60, y0 + 98, { size: 24, wt: 500, stroke: 0, color: 'rgba(244,234,214,0.7)' });
  // 地面
  ctx.strokeStyle = 'rgba(244,234,214,0.55)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(30, gy); ctx.lineTo(W - 30, gy); ctx.stroke();
  // 击打循环
  const per = 2.3; const ph = ((lt - 1.1) % per + per) % per; const strike = 1.0;      // 每周期 strike 时刻命中
  const cyc = lt < 1.1 ? -1 : Math.floor((lt - 1.1) / per);
  const wind = lt < 1.1 ? 0 : (ph < strike ? eio(ph / strike) : 1 - eout((ph - strike) / 0.5));   // 0 蓄力后摆 →1 命中
  const fly = lt >= 1.1 && ph >= strike ? (ph - strike) : -1;            // 槊飞出后的时间
  const bedY = gy - 0.95 * k, spearY = bedY - 1.22 * k;
  const shX = 520;
  // 车：轮、舆、辕
  const col = '#c9a66e', colD = '#7a5a34';
  ctx.strokeStyle = col; ctx.lineWidth = 7; ctx.beginPath(); ctx.arc(300, gy - 0.72 * k, 0.72 * k, 0, 7); ctx.stroke(); ctx.lineWidth = 3;
  for (let i = 0; i < 12; i++) { const an = i * Math.PI / 6; ctx.beginPath(); ctx.moveTo(300, gy - 0.72 * k); ctx.lineTo(300 + Math.cos(an) * 0.72 * k, gy - 0.72 * k + Math.sin(an) * 0.72 * k); ctx.stroke(); }
  ctx.fillStyle = col; ctx.beginPath(); ctx.arc(300, gy - 0.72 * k, 9, 0, 7); ctx.fill();
  ctx.fillStyle = colD; ctx.fillRect(110, bedY, 330, 16); ctx.fillStyle = col; ctx.fillRect(110, bedY - 6, 330, 8);
  ctx.fillStyle = colD; ctx.fillRect(110, bedY - 0.5 * k, 10, 0.5 * k);
  ctx.strokeStyle = col; ctx.lineWidth = 9; ctx.beginPath(); ctx.moveTo(440, bedY + 6); ctx.lineTo(shX + 28, bedY + 22); ctx.stroke();      // 辕
  // 彭排（大盾）
  ctx.save(); ctx.translate(shX, gy); ctx.rotate(0.05);
  ctx.fillStyle = '#e9d5a6'; ctx.fillRect(-9, -2.42 * k, 18, 1.12 * k); ctx.fillRect(-9, -1.18 * k, 18, 1.0 * k); ctx.fillStyle = C.red; ctx.fillRect(-9, -2.42 * k, 18, 12); ctx.fillRect(-9, -0.3 * k, 18, 12);
  ctx.restore();
  // 持槊者（蹲）与抡锤者
  const cR = C.red;
  footman(410, bedY - 4, k * 0.92, cR, { lean: 0.12, hands: [0.5 * k, -1.2 * k], stride: 0.05 });
  // 锤：绕肩摆动
  const sx = 215, sy = bedY - 1.42 * k * 0.98; const ang = lerp(-2.25, -0.12, wind);        // 柄角
  const hl = 1.15 * k; const hx = sx + 0.25 * k + Math.cos(ang) * hl, hy = sy - 0.1 * k + Math.sin(ang) * hl * 0.9 + 0.22 * k * wind;
  footman(sx, bedY - 4, k * 0.98, cR, { lean: lerp(-0.08, 0.2, wind), hands: [(hx - sx) * 0.55, (hy - (bedY - 4)) * 0.55 - 0.5 * k * (1 - wind) * 0.2 - 0.62 * k], hands2: [(hx - sx) * 0.4, (hy - (bedY - 4)) * 0.4 - 0.75 * k], stride: 0.16 });
  ctx.strokeStyle = '#d8c08a'; ctx.lineWidth = 9; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(sx + 0.2 * k, sy + 0.05 * k); ctx.lineTo(hx, hy); ctx.stroke();
  ctx.save(); ctx.translate(hx, hy); ctx.rotate(ang + Math.PI / 2); ctx.fillStyle = '#8d8a84'; ctx.fillRect(-0.3 * k, -0.17 * k, 0.6 * k, 0.34 * k); ctx.strokeStyle = '#d9d6cf'; ctx.lineWidth = 3; ctx.strokeRect(-0.3 * k, -0.17 * k, 0.6 * k, 0.34 * k); ctx.restore();
  // 魏骑：四骑前后相挤
  const rx = [668, 806, 944, 1082];
  for (let i = 3; i >= 0; i--) { const hitT = fly >= 0 ? fly - 0.03 - i * 0.035 : -1; const isHit = cyc >= 0 && hitT > 0 && i < 3 + (cyc % 2); const rec = isHit ? Math.min(1, hitT / 0.25) * (1 - clamp((hitT - 0.5) / 0.7)) : 0; horseman(rx[i] + 34 - 30 * Math.min(1, lt / 1.0) + rec * 8, gy, k * 0.9, ['#9fd6f2', '#74b4d8', '#8cc7e6', '#5f9fc6'][i], ['#3f7da6', '#346d93', '#3a7299', '#2f6488'][i], isHit ? 1 : 0, rec * 0.1); }
  // 断槊
  const sl = 0.9 * k; let tipX = shX + 44;
  if (fly >= 0) tipX = shX + 44 + Math.min(1, fly / 0.16) * 470;
  const tail = tipX - sl;
  if (fly >= 0) { const g = ctx.createLinearGradient(shX - 20, 0, tipX, 0); g.addColorStop(0, 'rgba(255,220,160,0)'); g.addColorStop(1, `rgba(255,236,200,${0.8 * (1 - clamp(fly / 0.9))})`); ctx.strokeStyle = g; ctx.lineWidth = 16; ctx.beginPath(); ctx.moveTo(shX - 20, spearY); ctx.lineTo(tail, spearY); ctx.stroke(); }
  const sa = fly < 0 ? 1 : 1 - clamp((fly - 0.75) / 0.4);
  ctx.save(); ctx.globalAlpha = a * sa; ctx.shadowColor = '#ffb070'; ctx.shadowBlur = 16; ctx.strokeStyle = '#fff0cf'; ctx.lineWidth = 11; ctx.lineCap = 'butt'; ctx.beginPath(); ctx.moveTo(tail, spearY); ctx.lineTo(tipX - 26, spearY); ctx.stroke();
  ctx.fillStyle = '#ffffff'; ctx.beginPath(); ctx.moveTo(tipX, spearY); ctx.lineTo(tipX - 34, spearY - 11); ctx.lineTo(tipX - 34, spearY + 11); ctx.closePath(); ctx.fill(); ctx.restore();
  // 命中火花
  if (fly >= 0 && fly < 0.22) { ctx.fillStyle = `rgba(255,224,160,${1 - fly / 0.22})`; ctx.beginPath(); ctx.arc(shX + 44 - sl, spearY, 26 + fly * 160, 0, 7); ctx.fill(); }
  // 标注
  const la = sstep((lt - 0.5) / 0.6);
  const L = (s, x, y, tx, ty, al = 'center') => { leader(x, y, tx, ty, 'rgba(244,234,214,0.7)'); label(s, tx, ty - 26, { size: 27, alpha: la, align: al }); };
  ctx.globalAlpha = a * la;
  L('彭排（大盾）', shX, gy - 2.44 * k, shX - 40, gy - 3.05 * k);
  L('车辕', 480, bedY + 14, 500, bedY + 100 + 26);
  L('大锤', 165, gy - 3.18 * k + 0, 150, gy - 3.5 * k + 0);
  ctx.globalAlpha = a * sstep((lt - (tq + 0.5)) / 0.6);
  label('断矟 · 长三四尺', 800, gy - 3.75 * k, { size: 34, fam: SERIF, wt: 900, bar: C.redL });
  label('约 0.7–1 米（晋尺折算）', 800, gy - 3.75 * k + 56, { size: 24, wt: 500 });
  ctx.restore();
}
