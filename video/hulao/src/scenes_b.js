// 场景（中）：伍～捌
'use strict';
// 说话人标记（贴在原文卡上沿）
function speaker(name, a, color = C.gold) { if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; const w = measure(name, 30, SERIF, 900) + 36; rrect(W - 60 - w, 196, w, 46, 6); ctx.fillStyle = color; ctx.fill(); ctx.restore(); text(name, W - 60 - w + 18, 220, { size: 30, fam: SERIF, wt: 900, stroke: 0, color: '#14110d', alpha: a }); }
// 魏军箭头：玄黑 + 浅描边
function weiLine(cam, pts, frac, a = 1, w = 11) {
  geoLine(cam, pts, { color: 'rgba(201,211,220,0.85)', w: w + 5, frac, alpha: a });
  return geoLine(cam, pts, { color: C.wei, w, frac, alpha: a });
}
function weiHead(e, a = 1) { if (!e) return; ctx.save(); ctx.globalAlpha *= a; ctx.translate(e[0], e[1]); ctx.rotate(e[2]); ctx.fillStyle = C.wei; ctx.strokeStyle = 'rgba(201,211,220,0.9)'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(20, 0); ctx.lineTo(-10, -15); ctx.lineTo(-10, 15); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.restore(); }
function fort(cam, p, name, o = {}) {      // 据点：方形红点，可翻黑
  const [x, y] = mw(cam, p[0], p[1]), a = o.alpha === undefined ? 1 : o.alpha, f = clamp(o.fall || 0), r = o.r || 12; if (a <= 0) return [x, y];
  ctx.save(); ctx.globalAlpha *= a; if (o.pulse && f < 0.5) { const u = (o.pulse % 1.8) / 1.8; ctx.strokeStyle = C.redL; ctx.globalAlpha = a * (1 - u) * 0.8; ctx.lineWidth = 3; ctx.strokeRect(x - r - u * 34, y - r - u * 34, 2 * (r + u * 34), 2 * (r + u * 34)); ctx.globalAlpha = a; }
  ctx.fillStyle = 'rgba(8,8,8,0.9)'; ctx.fillRect(x - r - 3, y - r - 3, 2 * r + 6, 2 * r + 6);
  ctx.fillStyle = f > 0.5 ? C.wei : C.red; ctx.fillRect(x - r, y - r, 2 * r, 2 * r); ctx.strokeStyle = f > 0.5 ? 'rgba(201,211,220,0.9)' : 'rgba(255,200,170,0.7)'; ctx.lineWidth = 2; ctx.strokeRect(x - r, y - r, 2 * r, 2 * r); ctx.restore();
  text(name, x + (o.dx || 0), y + (o.dy === undefined ? -r - 26 : o.dy), { size: o.size || 34, fam: SERIF, wt: 900, align: o.align || 'center', alpha: a, color: f > 0.5 ? '#c9d3dc' : C.cream });
  if (o.sub) { const ny = y + (o.dy === undefined ? -r - 26 : o.dy), sy = (o.dy !== undefined && o.dy > 0) ? ny + 36 : y + r + 24; text(o.sub, x + (o.dx || 0), sy, { size: 24, wt: 500, align: o.align || 'center', alpha: a * 0.9, color: C.dimtxt }); }
  return [x, y];
}

// ---------------- 伍 · 全军而归 ----------------
function sceneS5(t) {
  const S = TL.secs.s5;
  const k0 = AT('现在说毛德祖'), k1 = AT('北伐时，他给王镇恶'), k2 = AT('镇恶克立大功'), k3 = AT('王镇恶的大功'), k4 = AT('关中崩溃前后'), k5 = AT('德祖不能御'), k6 = AT('守不住，但他把军队'), k7 = AT('虎牢，在今天河南荥阳'), k8 = AT('他的官职是荥阳太守'), e = S.end;
  const cam = mapCam(kf([[k0, 113.2, 34.7, 9.5], [k4 - 0.4, 113.4, 34.7, 9.2], [k4 + 2, 111.4, 34.75, 5.2], [k5, 111.6, 34.7, 5.6], [k5 + 3, 113.7, 34.5, 9.2], [k7 - 0.5, 114.4, 34.55, 8.6], [k7 + 3.2, 113.16, 34.8, 0.78], [k8 - 0.3, 113.18, 34.8, 0.74], [k8 + 2.6, 113.55, 34.86, 1.75], [e, 113.56, 34.87, 1.7]], t));
  const far = sstep((cam.wdeg - 2.5) / 3), near = P(t, k7 + 1.6, 1.4);
  const cardA = fadeIO(t, k0 + 0.2, k4 - 0.2, 0.7, 0.7);
  drawMap(cam, lerp(0.12, 0.62, cardA));
  drawRivers(cam, 1 - cardA * 0.5); riverNames(cam, far * (1 - cardA), 'he');
  // —— 人物文字卡
  if (cardA > 0) {
    panel(70, 560, 940, 740, cardA, 'rgba(14,12,10,0.9)');
    ctx.save(); ctx.globalAlpha = cardA; ctx.fillStyle = C.red; ctx.fillRect(70, 560, 9, 740); ctx.restore();
    text('毛德祖', 124, 668, { size: 132, fam: SERIF, wt: 900, alpha: cardA, stroke: 0, ls: 10 });
    text('约 365 — 429', 950, 690, { size: 34, wt: 500, alpha: cardA * 0.85, stroke: 0, align: 'right', color: C.gold });
    const rows = [['籍贯', '荥阳阳武（今河南原阳一带）', k0 + 1.2], ['出身', '东晋末，自北方乡里南归', k0 + 4.2], ['履历', '刘道规将佐 → 太尉参军', k0 + 6.2], ['北伐', '王镇恶龙骧司马 · 前锋', k1 + 0.3]];
    rows.forEach((r, i) => { const a = cardA * P(t, r[2], 0.5), y = 790 + i * 62; text(r[0], 124, y, { size: 30, wt: 700, alpha: a, stroke: 0, color: C.gold }); text(r[1], 222, y, { size: 34, fam: SERIF, wt: 700, alpha: a, stroke: 0 }); });
    const wins = ['柏谷 · 斩赵玄石', '梨城 · 破尹雅', '泾水 · 破姚难，斩姚强'];
    wins.forEach((w, i) => { const a = cardA * P(t, k1 + 1.8 + i * 0.9, 0.5), y = 1056 + i * 54; ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = C.red; ctx.fillRect(226, y - 7, 14, 14); ctx.restore(); text(w, 256, y, { size: 32, fam: SERIF, wt: 700, alpha: a, stroke: 0, color: C.cream }); });
    text('打下关中，有他一份', 124, 1246, { size: 36, fam: SERIF, wt: 900, alpha: cardA * P(t, k3 + 1.6, 0.6), stroke: 0, color: C.redL });
    note('籍贯：《宋书》各本作“南武阳”，点校本据《晋书·毛宝传》改“阳武”', W / 2, 1332, cardA * P(t, k0 + 2.4, 0.6), 'center');
  }
  // —— 蒲阪 → 彭城 → 虎牢
  const m1 = eio(prog(t, k5 + 1.2, k6 + 2.6)), m2 = eio(prog(t, k6 + 3.2, k7 - 0.2));
  const mapA = (1 - cardA) * (1 - near);
  if (mapA > 0) {
    region(cam, '夏', 108.9, 35.4, C.xia, mapA * far * 1.2, 60);
    tint(cam, GUANZHONG, 'rgba(150,160,172,1)', 0.24 * mapA);
    city(cam, ...G.changan, '长安', { color: C.xia, alpha: mapA, size: 30 });
    const [px, py] = mw(cam, ...G.puban);
    const xa = fadeIO(t, k4 + 2.6, k5 + 2.0, 0.6, 0.8) * mapA, xf = eio(prog(t, k4 + 3, k5 + 0.8));
    arrow(px - 250, py - 150, px - 34, py - 20, { color: C.xia, w: 12, head: 26, frac: xf, alpha: xa, glow: 'rgba(190,200,211,0.5)' });
    tag('夏军 · 步骑二万', px - 250, py - 196, xa, { bar: C.xia, size: 28, align: 'left' });
    geoLine(cam, G.routeMao1, { color: C.red, w: 9, frac: m1, alpha: mapA, glow: 'rgba(224,73,47,0.75)', blur: 18 });
    if (m1 > 0 && m1 < 1) unitOn(cam, G.routeMao1, m1, { color: C.red, type: 'inf', alpha: mapA });
    geoLine(cam, G.routeMao2, { color: C.redL, w: 7, frac: m2, alpha: mapA, dash: [18, 10] });
    fort(cam, G.puban, '蒲阪', { alpha: mapA, sub: '今山西永济 · 黄河渡口', pulse: t < k5 + 1 ? t : 0, dy: 44 });
    city(cam, ...G.pengcheng, '彭城', { color: C.red, alpha: mapA * far, size: 34, capital: true, dy: 46 });
    city(cam, ...G.luoyang, '洛阳', { color: C.red, alpha: mapA * far, size: 28, dy: -34, r: 7 });
    if (m2 > 0.02) fort(cam, G.hulao, '虎牢', { alpha: mapA * P(t, k6 + 3.4, 0.6), pulse: t, size: 38 });
    tag('全军归彭城 · 419 年正月', W / 2, 1260, mapA * fadeIO(t, k5 + 2.2, k6 + 3.4, 0.5, 0.5), { bar: C.red, size: 30 });
    tag('二月 · 以德祖为荥阳太守，戍虎牢', W / 2, 1260, mapA * fadeIO(t, k6 + 3.8, k7 + 1.2, 0.5, 0.5), { bar: C.red, size: 30 });
    note('赴蒲阪的时间：《宋书》系于刘裕东还时，《通鉴》系于青泥败后', W / 2, 1326, mapA * fadeIO(t, k4 + 1, k5 + 0.5, 0.5, 0.5), 'center');
  }
  // —— 虎牢地形
  if (near > 0) {
    const [hx, hy] = fort(cam, G.hulao, '虎牢', { alpha: near, size: 54, pulse: t, r: 15, dy: -52 });
    text('又名成皋 · 今荥阳汜水镇一带', hx, hy + 52, { size: 28, wt: 500, align: 'center', alpha: near * (1 - P(t, k8 + 0.6, 1)), color: C.cream });
    const T_ = (s, lon, lat, sz, col, ls, al = 1) => { const [x, y] = mw(cam, lon, lat); text(s, x, y, { size: sz, fam: SERIF, wt: 900, align: 'center', color: col, alpha: near * al, ls }); };
    T_('黄　河', 113.02, 34.925, 44, '#e2d3a2', 20, P(t, k7 + 3.0, 0.6) * (1 - P(t, k8 + 0.4, 0.8))); T_('黄　河', 113.72, 35.14, 40, '#e2d3a2', 20, P(t, k8 + 2.2, 0.8));
    T_('嵩山余脉', 113.12, 34.66, 44, C.cream, 14, P(t, k7 + 5.0, 0.6) * (1 - P(t, k8 + 0.4, 0.8)));
    const [lx, ly] = mw(cam, 112.86, 34.8); const la = near * P(t, k7 + 6.6, 0.6) * (1 - P(t, k8 + 0.4, 0.8));
    arrow(lx + 90, ly, lx - 60, ly - 6, { color: C.cream, w: 5, head: 18, alpha: la }); text('洛阳', lx + 110, ly, { size: 36, fam: SERIF, wt: 900, alpha: la });
    tag('北临黄河 · 南靠山 · 洛阳东面的大门', W / 2, 1290, near * fadeIO(t, k7 + 6.8, k8 + 0.2, 0.5, 0.4), { size: 30, bar: C.gold });
    // 阳武：老家
    const ay = near * P(t, k8 + 2.4, 0.8);
    if (ay > 0) {
      const [yx, yy] = mw(cam, ...G.yangwu);
      ctx.save(); ctx.globalAlpha = ay * 0.85; ctx.strokeStyle = C.gold; ctx.lineWidth = 3; ctx.setLineDash([12, 10]); ctx.beginPath(); ctx.moveTo(hx, hy); ctx.lineTo(yx, yy); ctx.stroke(); ctx.restore();
      city(cam, ...G.yangwu, '阳武', { color: C.gold, alpha: ay, size: 40, sub: '毛德祖的家乡', dy: -62 });
      tag('直线约 75 公里（今地测距）', (hx + yx) / 2, (hy + yy) / 2 + 44, ay, { size: 26 });
      tag('荥阳太守 —— 守的是自己的家乡', W / 2, 1290, ay * P(t, k8 + 3.4, 0.6), { size: 32, bar: C.red, fam: SERIF, wt: 900 });
    }
  }
  bands(0.55, 0.6);
}

// ---------------- 陆 · 乘丧 ----------------
function sceneS6(t) {
  const S = TL.secs.s6;
  const k0 = AT('四二〇年，刘裕称帝'), k1 = AT('北边的魏，就是拓跋氏'), k2 = AT('遽乘丧伐之'), k3 = AT('人家刚办丧事'), k4 = AT('拓跋嗣回他'), k5 = AT('刘裕乘姚兴之死'), k6 = AT('刘裕当年就是趁后秦皇帝姚兴'), k7 = AT('崔浩又提醒'), k8 = AT('南人长于守城'), k9 = AT('南方人擅长守城'), k10 = AT('十月，魏将奚斤'), k11 = AT('刘裕留下的防线'), e = S.end;
  const cam = mapCam(kf([[k0, 115.2, 35.6, 13.4], [k1 + 2, 114.9, 36.0, 13.0], [k7, 114.6, 35.9, 12.2], [k9 + 1, 114.0, 35.2, 5.4], [k10 + 1, 114.2, 35.45, 3.6], [k11, 113.95, 35.25, 3.2], [e, 113.85, 35.15, 3.0]], t));
  const far = sstep((cam.wdeg - 6) / 4);
  const dlg = fadeIO(t, k1 + 5.5, k9 + 2, 0.8, 1.2);
  drawMap(cam, lerp(0.14, 0.34, dlg));
  drawRivers(cam); riverNames(cam, far * 0.9, 'he jiang');
  region(cam, '北 魏', 114.3, 38.4, C.weiE, far * 1.3, 64); region(cam, '宋', 116.2, 32.9, C.redL, far * 1.2, 64); region(cam, '夏', 109.9, 37.2, C.xia, far, 54);
  // 两个皇帝
  const [px, py] = mw(cam, ...G.pingcheng), [jx, jy] = mw(cam, ...G.jiankang);
  city(cam, ...G.pingcheng, '平城', { color: C.weiE, alpha: far, size: 34, capital: true, sub: t > k1 + 1.5 ? '今山西大同 · 魏都' : '' });
  city(cam, ...G.jiankang, '建康', { color: C.red, alpha: far, size: 34, capital: true });
  const cS = fadeIO(t, k0 + 0.4, k9 + 0.6, 0.6, 0.8), cW = fadeIO(t, k1 + 0.6, k9 + 0.6, 0.6, 0.8);
  const died = P(t, k0 + 4.4, 1.2);
  pcard(700, 1120, { name: died > 0.5 ? '刘义符' : '刘裕', role: died > 0.5 ? '宋 · 少帝　年十七' : '宋 · 武帝', sub: died > 0.5 ? '422 年五月即位' : '420 年称帝，422 年五月卒', alpha: cS, bar: C.red, w: 430, h: 160, off: 0, lit: fadeIO(t, k0 + 4.4, k1, 0.4, 0.6) });
  pcard(380, 640, { name: '拓跋嗣', role: '北魏 · 明元帝', sub: '欲乘丧南取河南地', alpha: cW, bar: C.weiE, w: 430, h: 160, glow: 'rgba(201,211,220,0.7)', lit: fadeIO(t, k4, k7, 0.4, 0.6) });
  pcard(700, 830, { name: '崔浩', role: '北魏 · 谋臣', sub: '反对乘丧出兵', alpha: cW * P(t, k1 + 7.4, 0.6), bar: C.weiE, w: 360, h: 150, size: 50, glow: 'rgba(201,211,220,0.7)', lit: fadeIO(t, k2 - 0.5, k4, 0.4, 0.5) + fadeIO(t, k7, k9 + 3, 0.4, 0.5) });
  speaker('崔浩', fadeIO(t, k2 - 0.4, k4 - 0.1, 0.3, 0.3) + fadeIO(t, k8 - 0.4, k9 + 4.2, 0.3, 0.3));
  speaker('拓跋嗣', fadeIO(t, k5 - 0.4, k7 - 0.2, 0.3, 0.3), C.weiE);
  tag('上一集：417 年，刘裕乘后秦主姚兴新丧北伐', W / 2, 1290, fadeIO(t, k6 + 0.4, k7 + 0.4, 0.5, 0.4), { size: 26, bar: C.red });
  // 河南三镇
  const fa = P(t, k9 + 1.2, 0.8);
  const hf = P(t, AT('十月，魏将奚斤') + 9.6, 1.0);
  const w1 = eio(prog(t, k10 + 0.6, k10 + 5.0)), w2 = eio(prog(t, k11 - 0.5, e - 0.5));
  if (w1 > 0) { const e1 = weiLine(cam, G.routeWei, lerp(0.62, 1, w1), 1, 12); if (w1 < 1) weiHead(e1); }
  if (w2 > 0) { const e2 = weiLine(cam, G.routeWei2, w2, 1, 10); weiHead(e2); }
  fort(cam, G.huatai, '滑台', { alpha: fa, fall: hf, pulse: t > k10 + 3 ? t : 0, sub: t > k10 + 4.4 ? '今河南滑县' : '', dx: 92, dy: 4, size: 38 });
  fort(cam, G.hulao, '虎牢', { alpha: fa, dy: 46, size: 38, pulse: t > k11 ? t : 0 });
  fort(cam, G.luoyang, '洛阳', { alpha: fa, dy: 44, size: 32, r: 10 });
  tag('黄河南岸的三座重镇', W / 2, 1290, fadeIO(t, k9 + 1.6, k10 + 0.2, 0.5, 0.4), { size: 30, bar: C.red });
  const [hx, hy] = mw(cam, ...G.huatai);
  tag('奚斤 · 步骑二万', hx + 30, hy - 150, fadeIO(t, k10 + 1.4, k11 + 0.5, 0.5, 0.5), { align: 'left', bar: C.weiE, size: 30 });
  tag('十一月 滑台陷 · 守将王景度出走', hx - 20, hy + 96, fadeIO(t, k10 + 9.8, e - 0.3, 0.5, 0.4), { size: 26, align: 'center' });
  tag('司马阳瓒：不降，被杀', hx - 20, hy + 146, fadeIO(t, k10 + 12, e - 0.3, 0.5, 0.4), { size: 28, bar: C.red, align: 'center' });
  bands(0.6, 0.62);
}

// ---------------- 柒 · 守城三招 ----------------
function tunnelDiagram(t, u) {   // u: {a, dig, split, sortie, scatter}
  const a = u.a; if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a;
  // 上：剖面
  const gy = 760;                                    // 地面线
  const g = ctx.createLinearGradient(0, gy, 0, gy + 330); g.addColorStop(0, '#54462f'); g.addColorStop(1, '#17140f'); ctx.fillStyle = g; ctx.fillRect(0, gy, W, 330);
  ctx.strokeStyle = 'rgba(216,180,106,0.55)'; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(W, gy); ctx.stroke();
  // 城墙
  ctx.fillStyle = '#b9a47a'; ctx.fillRect(250, gy - 120, 44, 120); for (let y = gy - 132; y < gy - 120; y += 1) { } for (let x = 250; x < 294; x += 16) ctx.fillRect(x, gy - 134, 9, 14);
  ctx.fillStyle = 'rgba(224,73,47,0.16)'; ctx.fillRect(0, gy - 118, 250, 118);
  // 竖井 + 横道
  const dig = clamp(u.dig), sp = clamp(u.split);
  const sx = 150, depth = 210 * Math.min(1, dig * 2.2), hx = sx + (860 - sx) * clamp((dig - 0.45) / 0.55);
  ctx.strokeStyle = '#0a0a0b'; ctx.lineWidth = 22; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.beginPath(); ctx.moveTo(sx, gy - 4); ctx.lineTo(sx, gy + depth); if (dig > 0.45) ctx.lineTo(hx, gy + 210); if (dig >= 1) ctx.lineTo(900, gy + 2); ctx.stroke();
  ctx.strokeStyle = 'rgba(224,73,47,0.9)'; ctx.lineWidth = 3; ctx.setLineDash([10, 10]); ctx.lineDashOffset = -t * 20; ctx.beginPath(); ctx.moveTo(sx, gy - 4); ctx.lineTo(sx, gy + depth); if (dig > 0.45) ctx.lineTo(hx, gy + 210); if (dig >= 1) ctx.lineTo(900, gy + 2); ctx.stroke(); ctx.setLineDash([]);
  // 魏军营（剖面上）
  for (let i = 0; i < 5; i++) { const x = 520 + i * 58; ctx.fillStyle = C.wei; ctx.strokeStyle = 'rgba(201,211,220,0.8)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x - 22, gy); ctx.lineTo(x, gy - 34); ctx.lineTo(x + 22, gy); ctx.closePath(); ctx.fill(); ctx.stroke(); }
  ctx.restore();
  text('城内', 120, 700, { size: 30, wt: 700, align: 'center', alpha: a, color: C.redL });
  text('魏军围阵', 636, 690, { size: 30, wt: 700, align: 'center', alpha: a, color: C.weiE });
  text('阵后', 930, 700, { size: 30, wt: 700, align: 'center', alpha: a * P(dig, 0.9, 0.1) });
  // 深度标
  const ad = a * sstep((dig - 0.25) * 6);
  ctx.save(); ctx.globalAlpha = ad; ctx.strokeStyle = C.gold; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(86, gy); ctx.lineTo(86, gy + 210); ctx.moveTo(76, gy); ctx.lineTo(96, gy); ctx.moveTo(76, gy + 210); ctx.lineTo(96, gy + 210); ctx.stroke(); ctx.restore();
  text('入七丈', 210, gy + 120, { size: 32, fam: SERIF, wt: 900, color: C.gold, alpha: ad });
  text('剖面', 1010, gy + 300, { size: 24, wt: 500, align: 'right', alpha: a * 0.7 });
  // 下：平面——二道出城，再分六道
  const py = 1215; ctx.save(); ctx.globalAlpha = a * sstep((dig - 0.5) * 4);
  ctx.fillStyle = 'rgba(14,12,10,0.6)'; ctx.fillRect(0, 1100, W, 232);
  ctx.strokeStyle = C.red; ctx.lineWidth = 12; ctx.beginPath(); ctx.arc(-40, py, 290, -0.42, 0.42); ctx.stroke();       // 城墙弧
  // 魏军围阵带
  const sc = clamp(u.scatter || 0);
  ctx.restore();
  dots(640, py, 190, 80 + sc * 120, 100 + sc * 60, C.wei, { alpha: a * sstep((dig - 0.5) * 4), r: 5, seed: 9, edge: 'rgba(201,211,220,0.55)', spread: sc * 60 });
  ctx.save(); ctx.globalAlpha = a * sstep((dig - 0.5) * 4); ctx.lineCap = 'round';
  const br = (y0, ys) => { ctx.strokeStyle = 'rgba(224,73,47,0.95)'; ctx.lineWidth = 5; ctx.setLineDash([9, 9]); ctx.lineDashOffset = -t * 18; ctx.beginPath(); ctx.moveTo(250, py + y0); ctx.lineTo(430, py + y0); ctx.stroke(); ys.forEach(y1 => { const fx = lerp(430, 880, sp), fy = lerp(py + y0, py + y1, sp); ctx.beginPath(); ctx.moveTo(430, py + y0); ctx.lineTo(fx, fy); ctx.stroke(); }); ctx.setLineDash([]); };
  br(-34, [-96, -62, -28]); br(34, [28, 62, 96]);
  ctx.restore();
  text('二道', 330, py - 62, { size: 28, wt: 700, align: 'center', color: C.redL, alpha: a * sstep((dig - 0.6) * 4) });
  text('六道', 800, py - 122, { size: 28, wt: 700, align: 'center', color: C.redL, alpha: a * sp });
  text('平面', 1010, 1316, { size: 24, wt: 500, align: 'right', alpha: a * 0.7 * sstep((dig - 0.5) * 4) });
  // 敢死四百，自阵后出
  const so = clamp(u.sortie || 0);
  if (so > 0) { for (let k = 0; k < 6; k++) { const y1 = [-96, -62, -28, 28, 62, 96][k]; dots(lerp(890, 730, so), py + y1 * lerp(1, 0.7, so), 14, 22, 9, C.redL, { alpha: a * Math.min(1, so * 3), r: 4.2, seed: 30 + k, jit: t * 3 }); }
    // 攻具起火：只画几处橙色光点
    for (let k = 0; k < 5; k++) { const fx = 560 + k * 44 + 10 * Math.sin(k * 3), fy = py - 60 + 34 * ((k * 7) % 4), fl = 0.6 + 0.4 * Math.sin(t * 9 + k * 2); const al = a * sstep((so - 0.45 - k * 0.06) * 6) * (1 - sstep((sc - 0.6) * 3)); if (al <= 0) continue; const gr = ctx.createRadialGradient(fx, fy, 1, fx, fy, 30 * fl); gr.addColorStop(0, `rgba(255,170,70,${0.95 * al})`); gr.addColorStop(1, 'rgba(255,120,40,0)'); ctx.fillStyle = gr; ctx.fillRect(fx - 34, fy - 34, 68, 68); } }
}
function sceneS7(t) {
  const S = TL.secs.s7;
  const k0 = AT('魏军转头围住虎牢'), k1 = AT('于城内穴地'), k2 = AT('从城里往地下挖七丈'), k3 = AT('虏虽退散'), k4 = AT('魏军散了，很快又合拢'), k5 = AT('第二招，他出城野战'), k6 = AT('第三招，是几封信'), k7 = AT('每答表书'), k8 = AT('每次回信，都故意'), k9 = AT('朝里又有人告他的状'), k10 = AT('办法，他都用上了'), e = S.end;
  // 背景：虎牢近景，压暗
  const cam = mapCam(kf([[k0, 113.3, 34.9, 1.5], [k1, 113.22, 34.86, 0.62], [e, 113.2, 34.85, 0.5]], t));
  const dA = fadeIO(t, k1 - 0.3, k5 - 0.1, 0.8, 0.6), bA = fadeIO(t, k5, k6 - 0.1, 0.6, 0.6), lA = fadeIO(t, k6, k10 - 0.1, 0.6, 0.6), rA = fadeIO(t, k10, e, 0.5, 0.3);
  const dg = fadeIO(t, k1 - 0.3, e + 1, 0.8, 0.3);
  drawMap(cam, lerp(0.2, 0.86, dg)); season('summer', 0.35);
  drawRivers(cam, 0.7 * (1 - dg));
  const [hx, hy] = mw(cam, ...G.hulao);
  if (t < k1 + 0.6) { const a0 = 1 - P(t, k1 - 0.3, 0.8); fort(cam, G.hulao, '虎牢', { alpha: a0, size: 44, pulse: t, r: 14, dy: -50 }); const wf = eio(prog(t, k0, k0 + 2.6)); [[1, -0.4], [0.7, 0.9], [-0.9, 0.7]].forEach((d, i) => { const r = lerp(520, 150, wf); weiBlock(hx + d[0] * r, hy + d[1] * r, 92, 50, a0 * Math.min(1, wf * 3), '魏'); }); tag('第一招 · 地道', W / 2, 1290, a0 * P(t, k0 + 2.2, 0.5), { size: 32, bar: C.red, fam: SERIF, wt: 900 }); }
  // —— 地道
  if (dA > 0) {
    const dig = prog(t, k1 + 0.2, k2 + 4.6), split = eio(prog(t, k2 + 3.2, k2 + 6.4)), so = eio(prog(t, k2 + 6.2, k2 + 9.2)), sc = t < k3 ? eio(prog(t, k2 + 8.6, k3)) : 1 - eio(prog(t, k3 + 0.8, k4 + 1.8));
    tunnelDiagram(t, { a: dA, dig, split, sortie: so * (1 - P(t, k3 + 0.5, 1.2)), scatter: sc });
    tag('敢死四百：范道基二百为前驱，郭王符、刘规二百为后继', W / 2, 640, dA * fadeIO(t, k2 + 6.6, k3 + 0.2, 0.5, 0.4), { size: 25, bar: C.red });
    tag('斩首数百 · 焚烧攻具', W / 2, 640, dA * fadeIO(t, k3 + 0.4, k4 + 0.4, 0.4, 0.4), { size: 28, bar: C.red });
    tag('虽退散，随复更合', W / 2, 640, dA * fadeIO(t, k4 + 0.6, k5 - 0.3, 0.4, 0.4), { size: 30, bar: C.weiE });
    note('地道走向史书无图，此为示意', 76, 1340, dA * 0.9);
  }
  // —— 野战
  if (bA > 0) {
    const u = prog(t, k5, k6), out = eio(prog(u, 0.08, 0.3)), hit = eio(prog(u, 0.48, 0.66)), back = eio(prog(u, 0.7, 0.92));
    ctx.save(); ctx.globalAlpha = bA; ctx.strokeStyle = C.red; ctx.lineWidth = 14; ctx.beginPath(); ctx.arc(60, 960, 300, -0.75, 0.75); ctx.stroke(); ctx.fillStyle = 'rgba(224,73,47,0.12)'; ctx.beginPath(); ctx.arc(60, 960, 293, -0.75, 0.75); ctx.lineTo(0, 1160); ctx.lineTo(0, 760); ctx.closePath(); ctx.fill(); ctx.restore();
    text('虎牢', 150, 960, { size: 46, fam: SERIF, wt: 900, align: 'center', alpha: bA });
    const rx = lerp(250, 540, out) - back * 300, keep = 1 - hit * 0.38;
    dots(rx, 960, 150, 86, 110, C.red, { alpha: bA * (1 - back * 0.5), r: 5, seed: 41, keep, jit: t * 2 });
    dots(770, 940, 170, 90, 130, C.wei, { alpha: bA, r: 5.5, seed: 43, edge: 'rgba(201,211,220,0.6)', jit: t * 2 });
    text('公孙表', 800, 770, { size: 32, fam: SERIF, wt: 900, align: 'center', alpha: bA, color: C.weiE });
    tag('第二招 · 野战', 76, 560, bA, { size: 30, bar: C.red, fam: SERIF, wt: 900, align: 'left' });
    text('毛德祖', rx, 1104, { size: 32, fam: SERIF, wt: 900, align: 'center', alpha: bA * (1 - back), color: C.redL });
    // 奚斤自许昌还，合围
    const ax = bA * sstep((u - 0.4) * 8);
    curveArrow([[1000, 1330], [820, 1250], [640, 1160], [lerp(600, 500, hit), lerp(1120, 1050, hit)]], { color: C.weiM, w: 20, head: 40, frac: hit, alpha: ax });
    curveArrow([[1000, 1330], [820, 1250], [640, 1160], [lerp(600, 500, hit), lerp(1120, 1050, hit)]], { color: 'rgba(201,211,220,0.9)', w: 3, head: 0.1, frac: hit, alpha: ax });
    tag('奚斤自许昌还 · 合围', 760, 1300, ax, { size: 28, bar: C.weiE });
    // 时间：朝 → 晡
    panel(250, 600, 580, 70, bA); const tu = prog(u, 0.06, 0.62); text('朝', 284, 636, { size: 30, fam: SERIF, wt: 900, alpha: bA, stroke: 0 }); text('晡', 796, 636, { size: 30, fam: SERIF, wt: 900, alpha: bA, stroke: 0, align: 'right' });
    ctx.save(); ctx.globalAlpha = bA; ctx.fillStyle = 'rgba(241,231,210,0.2)'; ctx.fillRect(336, 632, 410, 6); ctx.fillStyle = C.gold; ctx.fillRect(336, 632, 410 * tu, 6); ctx.restore();
    text('从早晨打到下午', 540, 700, { size: 24, wt: 500, align: 'center', alpha: bA * 0.85 });
    tag('失甲士千余人 · 退还固城', W / 2, 1290, bA * sstep((u - 0.72) * 8), { size: 32, bar: C.red, fam: SERIF, wt: 900 });
  }
  // —— 反间
  if (lA > 0) {
    text('第三招 · 几封信', W / 2, 940, { size: 84, fam: SERIF, wt: 900, align: 'center', alpha: lA * fadeIO(t, k6 + 0.1, k6 + 3.0, 0.5, 0.5), ls: 6 });
    const wr = prog(t, k6 + 5.5, k8 + 1.0), fix = prog(t, k7 + 0.2, k8 + 2.6);
    const pass = eio(prog(t, k8 + 7.4, k8 + 9.6));                        // 信到了奚斤手里
    const oB = P(t, k9 + 3.4, 1.4);
    pcard(280, 660, { name: '公孙表', role: '魏 · 吴兵将军', sub: '力主先攻城；与德祖有旧', alpha: lA * P(t, k6 + 3.2, 0.5), bar: C.weiE, w: 440, h: 156, size: 50, off: oB, note: '夜，缢杀于帐中', glow: 'rgba(201,211,220,0.7)', lit: fadeIO(t, k6 + 3.2, k7, 0.4, 0.5) });
    pcard(800, 660, { name: '奚斤', role: '魏 · 主将', sub: pass > 0.6 ? '“倍疑之”' : '', alpha: lA * P(t, k8 + 3.0, 0.5), bar: C.weiE, w: 440, h: 156, size: 50, glow: 'rgba(201,211,220,0.7)', lit: pass });
    letter(lerp(300, 780, pass), lerp(1020, 1000, pass), { alpha: lA * P(t, k6 + 5.0, 0.6) * (1 - oB * 0.6), write: wr, fix, w: 400, h: 500, rot: lerp(-0.05, 0.04, pass) });
    tag('德祖的回信', lerp(300, 780, pass), 1292, lA * P(t, k6 + 5.4, 0.5) * (1 - oB), { size: 28, bar: C.red });
    tag('“辄多所治定”：处处涂改', 760, 930, lA * fadeIO(t, k7 + 0.8, k8 + 6.8, 0.5, 0.5), { size: 28, bar: C.gold });
    tag('另遣人密告奚斤：表与城中连谋', 760, 1000, lA * fadeIO(t, k8 + 3.4, k8 + 7.2, 0.5, 0.4), { size: 26 });
    tag('太史令王亮亦奏其过', 300, 930, lA * fadeIO(t, k9 + 0.2, k10, 0.5, 0.4), { size: 26, bar: C.weiE });
    note('反间事见《宋书》《通鉴》；《魏书·公孙表传》只记王亮进言', W / 2, 1344, lA * P(t, k8 + 1, 0.6), 'center');
  }
  // —— 小结
  if (rA > 0) {
    const items = [['地道', '退散复合'], ['野战', '折甲士千余'], ['反间', '除公孙表']];
    items.forEach((it, i) => { const a = rA * P(t, k10 + 0.2 + i * 0.5, 0.5), x = 200 + i * 340; panel(x - 140, 820, 280, 190, a); text(it[0], x, 885, { size: 56, fam: SERIF, wt: 900, align: 'center', alpha: a, stroke: 0 }); text(it[1], x, 960, { size: 28, wt: 500, align: 'center', alpha: a, stroke: 0, color: C.gold }); });
    text('换来的，只是时间', W / 2, 1130, { size: 64, fam: SERIF, wt: 900, align: 'center', alpha: rA * P(t, k10 + 2.2, 0.6), color: C.redL });
  }
  bands(0.6, 0.62);
}

// ---------------- 捌 · 不敢进 ----------------
function sceneS8(t) {
  const S = TL.secs.s8;
  const k0 = AT('四二三年四月'), k1 = AT('绝虎牢汲河之路'), k2 = AT('他把这条打水的路截断了'), k3 = AT('援军在哪儿'), k4 = AT('皆畏魏兵强'), k5 = AT('都怕魏军强'), k6 = AT('建康的朝廷里'), k7 = AT('刘裕在的时候'), k8 = AT('一座城守不守得住'), e = S.end;
  const cam = mapCam(kf([[k0, 113.2, 34.87, 0.6], [k1, 113.205, 34.885, 0.3], [k3 - 1.5, 113.2, 34.885, 0.3], [k3 + 1.7, 116.0, 34.3, 10.2], [k6, 116.1, 34.2, 10.2], [k6 + 2, 116.4, 33.7, 9.6], [k7, 116.2, 33.9, 9.8], [e, 115.6, 34.2, 10.6]], t));
  const near = 1 - sstep((cam.wdeg - 0.5) / 1.5), far = sstep((cam.wdeg - 5) / 3);
  drawMap(cam, 0.14); season('summer', 0.55);
  drawRivers(cam); riverNames(cam, far * 0.9, 'he huai jiang');
  const [hx, hy] = mw(cam, ...G.hulao);
  if (near > 0) {
    // 城（示意轮廓）
    const r = 110 * (0.3 / cam.wdeg);
    ctx.save(); ctx.globalAlpha = near; ctx.strokeStyle = C.red; ctx.lineWidth = 9; ctx.shadowColor = 'rgba(224,73,47,0.6)'; ctx.shadowBlur = 16; ctx.strokeRect(hx - r, hy - r * 0.8, 2 * r, 1.6 * r); ctx.restore();
    text('虎牢', hx, hy, { size: 44, fam: SERIF, wt: 900, align: 'center', alpha: near });
    // 汲河之路：从城北悬绠而下
    const rsp = smoothC(G.he).map(q => mw(cam, q[0], q[1])), rcum = pathLen(rsp); let ni = 0, nd = 1e9; rsp.forEach((q, i) => { const d = Math.hypot(q[0] - hx, q[1] - (hy - r * 0.8)); if (d < nd) { nd = d; ni = i; } });
    const rwid = clamp(cam.k / PL.macro.scale * 9, 2.5, 70) * 1.25, [rx, ry] = rsp[ni], ya = near * P(t, k0 + 4.4, 0.8), cutA = P(t, k1 + 1.2, 1.2);
    ctx.save(); ctx.globalAlpha = ya; ctx.strokeStyle = cutA > 0.6 ? 'rgba(160,150,140,0.6)' : '#9fd0e0'; ctx.lineWidth = 6; ctx.setLineDash([12, 10]); ctx.lineDashOffset = cutA > 0.6 ? 0 : -t * 24; ctx.beginPath(); ctx.moveTo(hx, hy - r * 0.8); ctx.lineTo(rx, ry); ctx.stroke(); ctx.restore();
    tag('悬绠汲河：用长绳下到河里打水', hx + r + 24, hy - r * 0.8 - 4, ya * (1 - cutA), { align: 'left', size: 26, bar: '#9fd0e0' });
    // 连舰：一条黑线截在城与河之间
    const bx = eio(prog(t, k1 + 0.4, k1 + 2.2));
    ctx.save(); ctx.globalAlpha = near * Math.min(1, bx * 4); for (let i = 0; i < 9; i++) { if ((i + 0.5) / 9 > bx) break; const q = along(rsp, rcum, rcum[ni] + (i - 4) * 66); ctx.save(); ctx.translate(q[0], q[1]); ctx.rotate(q[2]); ctx.translate(Math.cos(1.57) * 0, rwid * 0.22); ctx.fillStyle = C.wei; ctx.strokeStyle = 'rgba(201,211,220,0.9)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(-28, -11); ctx.lineTo(28, -11); ctx.lineTo(20, 11); ctx.lineTo(-20, 11); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.restore(); } ctx.restore();
    tag('连舰截河 · 绝其汲路', rx - 150, ry - rwid * 0.5 - 44, near * P(t, k1 + 2.2, 0.5), { size: 30, bar: C.weiE });
    note('城与汲路的位置为示意。“悬绠汲河”“连舰”见《魏书·太宗纪》', W / 2, 1346, near * P(t, k1 + 1, 0.6), 'center');
    weiBlock(hx + 330, hy + 60, 150, 62, near * P(t, k0 + 1, 0.6), '拓跋嗣'); weiBlock(hx - 330, hy + 130, 110, 54, near * P(t, k0 + 0.6, 0.6), '魏'); weiBlock(hx + 120, hy + 230, 110, 54, near * P(t, k0 + 0.8, 0.6), '魏');
    tag('自督攻城三日，不能下 → 赴洛阳观石经', W / 2, 1284, near * fadeIO(t, k2 + 1.8, k3 - 1.3, 0.5, 0.4), { size: 28, bar: C.weiE });
  }
  if (far > 0) {
    // 魏据之地
    fort(cam, G.huatai, '滑台', { alpha: far, fall: 1, size: 28, r: 9, dy: -30 }); fort(cam, G.luoyang, '洛阳', { alpha: far, fall: 1, size: 28, r: 9, dy: 36 });
    fort(cam, G.hulao, '虎牢', { alpha: far, size: 44, pulse: t, r: 13, dy: -50 });
    for (let i = 0; i < 3; i++) { const an = [0.3, 2.3, 4.2][i]; weiBlock(hx + Math.cos(an) * 46, hy + Math.sin(an) * 40, 34, 22, far * 0.95); }
    city(cam, ...G.jiankang, '建康', { color: C.red, alpha: far, size: 34, capital: true, dy: 46 });
    city(cam, ...G.pengcheng, '彭城', { color: C.red, alpha: far, size: 28, dy: -32, r: 7 });
    // 三路援军
    const stop = P(t, k4, 1.6), fadeC = `rgba(${Math.round(lerp(224, 128, stop))},${Math.round(lerp(73, 104, stop))},${Math.round(lerp(47, 96, stop))},1)`;
    const f1 = eio(prog(t, k3 + 1.9, k3 + 5.2)), f1b = eio(prog(t, k3 + 5.2, k3 + 7.2)), f2 = eio(prog(t, k3 + 6.8, k3 + 8.8)), f3 = eio(prog(t, k3 + 8.4, k3 + 10.4));
    const al = far * lerp(1, 0.6, stop);
    geoLine(cam, G.routeTan, { color: fadeC, w: 5, frac: f1, alpha: al * 0.6, dash: [14, 9] }); const e1 = geoLine(cam, G.routeTan2, { color: fadeC, w: 8, frac: f1b, alpha: al });
    const e2 = geoLine(cam, G.routeLiu, { color: fadeC, w: 8, frac: f2, alpha: al }), e3 = geoLine(cam, G.routeShen, { color: fadeC, w: 8, frac: f3, alpha: al });
    const head = (e, on) => { if (!e || on <= 0) return; ctx.save(); ctx.globalAlpha = al; ctx.translate(e[0], e[1]); ctx.rotate(e[2]); ctx.fillStyle = fadeC; ctx.beginPath(); ctx.moveTo(16, 0); ctx.lineTo(-10, -13); ctx.lineTo(-10, 13); ctx.closePath(); ctx.fill(); ctx.restore(); };
    head(f1b > 0 ? e1 : null, 1); head(e2, f2); head(e3, f3);
    city(cam, ...G.qingzhou, '青州', { color: C.red, alpha: far * P(t, k3 + 3.6, 0.5), size: 26, dy: -30, r: 7 });
    const st = (p, name, sub, on, dx, dy, al2) => { const [x, y] = mw(cam, p[0], p[1]); const a = far * on; if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = '#0c0b0a'; ctx.beginPath(); ctx.arc(x, y, 12, 0, 7); ctx.fill(); ctx.strokeStyle = C.cream; ctx.lineWidth = 3; ctx.stroke(); ctx.fillStyle = C.cream; ctx.fillRect(x - 5, y - 5, 4, 10); ctx.fillRect(x + 1, y - 5, 4, 10); ctx.restore(); tag(name, x + dx, y + dy, a, { size: 28, align: al2, bar: C.red }); if (sub) note(sub, x + dx + (al2 === 'left' ? 6 : -6), y + dy + 40, a, al2); return [x, y]; };
    const s1 = st(G.hulu, '湖陆 · 檀道济', '先救青州，后停于此', P(t, k3 + 7.0, 0.5), 22, -34, 'left');
    const s2 = st(G.xiangcheng, '项城 · 刘粹', '', P(t, k3 + 8.8, 0.5), -22, -32, 'right');
    const s3 = st(G.gaoqiao, '高桥 · 沈叔狸', '今地不详，位置示意', P(t, k3 + 10.2, 0.5), 22, 34, 'left');
    // 到虎牢还有多远
    const da = far * fadeIO(t, k4 + 1.2, k6 - 0.2, 0.6, 0.5);
    if (da > 0 && s1 && s2) { ctx.save(); ctx.globalAlpha = da * 0.8; ctx.strokeStyle = C.cream; ctx.lineWidth = 2; ctx.setLineDash([5, 12]); [s1, s2].forEach(s => { ctx.beginPath(); ctx.moveTo(s[0], s[1]); ctx.lineTo(hx, hy); ctx.stroke(); }); ctx.restore(); tag('湖陆距虎牢约 320 公里 · 项城约 240 公里', W / 2, 1290, da, { size: 28, bar: C.gold }); note('今地直线测距，约数', W / 2, 1344, da, 'center'); }
    // 建康
    const ja = far * fadeIO(t, k6 + 0.4, k7 - 0.1, 0.6, 0.5);
    if (ja > 0) {
      const py0 = 262; panel(110, py0, 860, 300, ja, 'rgba(14,12,10,0.92)');
      text('建康 · 朝廷', 150, py0 + 52, { size: 40, fam: SERIF, wt: 900, alpha: ja, stroke: 0, color: C.gold });
      text('少帝 刘义符（即位时年十七）', 150, py0 + 116, { size: 36, fam: SERIF, wt: 700, alpha: ja, stroke: 0 });
      text('辅政：徐羡之 · 傅亮 · 谢晦', 150, py0 + 174, { size: 36, fam: SERIF, wt: 700, alpha: ja * P(t, k6 + 2.4, 0.5), stroke: 0 });
      text('朝议：项城去魏不远，欲召守军还寿阳（未行）', 150, py0 + 232, { size: 28, wt: 500, alpha: ja * P(t, k6 + 7.2, 0.5), stroke: 0, color: C.dimtxt });
      text('次年五月，废少帝', 150, py0 + 274, { size: 28, wt: 500, alpha: ja * P(t, k6 + 11.6, 0.5), stroke: 0, color: C.dimtxt });
    }
    region(cam, '魏', 114.6, 36.7, C.weiE, far * 1.2 * (1 - fadeIO(t, k6 + 0.4, k7 - 0.1, 0.6, 0.5)), 70);
  }
  bands(0.6, 0.62);
}
