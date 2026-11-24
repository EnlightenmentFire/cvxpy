// 场景（上）：冷开场、片名、壹～肆
'use strict';
const fadeBlack = a => { if (a > 0) { ctx.fillStyle = `rgba(9,8,7,${clamp(a)})`; ctx.fillRect(0, 0, W, H); } };
const tag = (s, x, y, a = 1, o = {}) => label(s, x, y, Object.assign({ size: 28, alpha: a }, o));
// 沿路线移动的部队牌
function unitOn(cam, pts, frac, o = {}) {
  const sp = smoothC(pts).map(q => mw(cam, q[0], q[1])), cum = pathLen(sp), e = along(sp, cum, clamp(frac) * cum[cum.length - 1]);
  unitBox(e[0], e[1], Object.assign({ w: 70, h: 46 }, o)); return e;
}

// ---------------- 冷开场 ----------------
function sceneCold(t) {
  const t0 = AT('公元四二三年'), t1 = AT('围城的魏军从地下挖过来'), t2 = AT('两天以后'), t3 = AT('人马渴乏'), t4 = AT('人和马又渴'), t5 = AT('守这座城的人'), te = TL.secs.title.start;
  ctx.fillStyle = '#0d0c0b'; ctx.fillRect(0, 0, W, H);
  const g = ctx.createRadialGradient(W / 2, 900, 100, W / 2, 900, 1100); g.addColorStop(0, 'rgba(70,52,30,0.5)'); g.addColorStop(1, 'rgba(10,9,8,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const da = fadeIO(t, t0 + 0.6, t5 + 0.6, 1.4, 1.0);
  const tun = prog(t, t1 + 0.2, t1 + 3.6), lvl = 1 - eio(prog(t, t1 + 3.4, t2 + 0.6));
  const sc = lerp(0.92, 1.03, prog(t, t0, t5));
  wellDiagram(t, { alpha: da, tun, lvl, sc, oy: 40, depth: P(t, t1 + 3.0, 0.8) });
  season('summer', da * 0.8); dust(t, da * 0.8);
  // 年月
  const a0 = fadeIO(t, t0 - 0.5, t3 - 0.2, 0.7, 0.6);
  text('景平元年 · 闰四月', 76, 330, { size: 84, fam: SERIF, wt: 900, alpha: a0, ls: 4 });
  text('公元 423 年 · 虎牢被围近二百日', 80, 416, { size: 38, wt: 500, alpha: a0, color: C.gold, ls: 2 });
  tag('二十一日　魏军穴地，泄城中井水', 76, 520, fadeIO(t, t1 + 0.4, t2 - 0.1, 0.5, 0.4), { align: 'left', bar: C.weiE });
  tag('二十三日', 76, 640, fadeIO(t, t2, t5, 0.5, 0.5), { align: 'left', bar: C.gold, size: 30 });
  note('井与地道的位置，史书无图，此为示意', 76, 1338, da * P(t, t1 + 1, 0.8));
  // 毛德祖
  const a5 = fadeIO(t, t5 + 0.1, te - 0.2, 0.7, 0.6);
  if (a5 > 0) {
    fadeBlack(a5 * 0.82);
    text('毛德祖', W / 2, 860, { size: 190, fam: SERIF, wt: 900, align: 'center', alpha: a5, ls: 18, stroke: 0, glow: 'rgba(224,73,47,0.35)', blur: 40 });
    text('宋 · 司州刺史　守虎牢', W / 2, 1010, { size: 40, wt: 500, align: 'center', alpha: a5 * P(t, t5 + 0.8, 0.6), color: C.gold, stroke: 0, ls: 6 });
    const a6 = a5 * P(t, t5 + 3.6, 0.8); ctx.save(); ctx.globalAlpha = a6; ctx.fillStyle = C.red; ctx.fillRect(W / 2 - 40, 1108, 80, 4); ctx.restore();
    text('六年前 · 长安', W / 2, 1170, { size: 52, fam: SERIF, wt: 900, align: 'center', alpha: a6, stroke: 0, ls: 8 });
  }
  fadeBlack(sstep((t - (te - 0.7)) / 0.7));
}

// ---------------- 片名 ----------------
function sceneTitle(t) {
  const s = TL.secs.title, u = (t - s.start) / (s.end - s.start);
  ctx.fillStyle = '#090807'; ctx.fillRect(0, 0, W, H);
  const a = fadeIO(t, s.start, s.end, 0.8, 0.7);
  const cx = W / 2, cy = 930;
  walls(cx, cy, { alpha: a * 0.85, broken: [1, 1, 1, 0], shown: [eout(u * 3), eout(u * 3 - 0.2), eout(u * 3 - 0.4), eout(u * 3 - 0.6)], sc: 2.0, core: 0.9 });
  text('孤城', cx + 14, cy - 8 + 12 * (1 - eout(u * 2)), { size: 196, fam: SERIF, wt: 900, align: 'center', alpha: a, stroke: 0, ls: 28 });
  text('壹 · 毛德祖守虎牢', cx, cy + 352, { size: 60, fam: SERIF, wt: 900, align: 'center', alpha: a * sstep((u - 0.2) * 4), color: C.gold, stroke: 12, strokeColor: 'rgba(9,8,7,0.95)', ls: 6 });
  text('公元 417 — 423 年', cx, cy + 432, { size: 34, wt: 500, align: 'center', alpha: a * sstep((u - 0.3) * 4) * 0.9, stroke: 10, strokeColor: 'rgba(9,8,7,0.95)', ls: 4 });
  text('细节与胜负手', cx, cy - 372, { size: 34, wt: 700, align: 'center', alpha: a * 0.85, stroke: 10, strokeColor: 'rgba(9,8,7,0.95)', ls: 14 });
}

// ---------------- 壹 · 东还 ----------------
function sceneS1(t) {
  const S = TL.secs.s1, b = S.body;
  const k0 = AT('公元四一七年'), k1 = AT('长安，就是今天的西安'), k2 = AT('这年十一月'), k3 = AT('刘裕本想留下'), k6 = AT('关中的父老找上门来'), k7 = AT('残民不沾王化'), k8 = AT('我们这些剩下来的百姓'), k9 = AT('刘裕也难过'), k10 = AT('关中人留不住他'), e = S.end;
  const cam = mapCam(kf([[k0, 113.4, 34.6, 13.8], [k1 - 0.6, 113.0, 34.6, 12.6], [k1 + 2.2, 109.3, 34.55, 4.6], [k2 - 0.3, 109.3, 34.55, 4.4], [k2 + 2.2, 113.6, 33.7, 13.8], [k6 - 0.5, 113.6, 33.7, 13.4], [k6 + 2.4, 108.86, 34.36, 1.5], [k9 - 0.3, 108.86, 34.37, 1.42], [k9 + 2.6, 113.5, 33.9, 13.4], [e, 113.7, 33.8, 13.8]], t));
  const far = cam.wdeg > 7 ? 1 : sstep((cam.wdeg - 3) / 4), near = 1 - sstep((cam.wdeg - 1.6) / 2);
  drawMap(cam, 0.12);
  const win = P(t, k9 - 0.5, 2); season('winter', win * 0.7);
  tint(cam, GUANZHONG, 'rgba(224,73,47,1)', 0.17 * fadeIO(t, k1 + 0.6, k6 + 1, 1, 1.2));
  drawRivers(cam); riverNames(cam, far * 0.9, 'he jiang huai'); riverNames(cam, (1 - far) * (1 - near), 'wei');
  region(cam, '北 魏', 114.6, 38.2, C.weiE, far * 0.8, 50); region(cam, '夏', 108.6, 37.6, C.xia, far * 0.9, 50);
  region(cam, '东 晋', 115.4, 31.2, C.redL, far * 0.7, 50);
  region(cam, '后 秦', 108.3, 35.25, C.gold, far * (1 - P(t, k0 + 3.2, 1.6)), 44);
  region(cam, '关 中', 108.4, 34.86, C.cream, fadeIO(t, k1 + 1.4, k2 - 0.1, 0.8, 0.6) * 1.5, 70);
  // 北伐红线
  const f1 = eio(prog(t, k0 + 0.3, k0 + 5.2)), back = eio(prog(t, k9 + 1.2, k10 + 0.4)), home = eio(prog(t, k10 + 0.2, e - 0.8));
  geoLine(cam, G.routeNorth, { color: C.red, w: 7, frac: f1, alpha: 0.95 * (1 - P(t, k9 + 0.6, 1.5) * 0.75), glow: 'rgba(224,73,47,0.7)', blur: 16 });
  if (f1 > 0.02 && f1 < 1) { const u = unitOn(cam, G.routeNorth, f1, { color: C.red, type: 'navy' }); tag('太尉 刘裕 · 北伐', u[0], u[1] - 58, sstep((f1 - 0.1) * 8) * (1 - sstep((f1 - 0.86) * 10)), { size: 28, bar: C.red }); }
  // 城
  const ca = far;
  city(cam, ...G.pengcheng, '彭城', { color: C.red, alpha: ca, size: 30, dy: 38 });
  city(cam, ...G.luoyang, '洛阳', { color: C.red, alpha: ca * f1, size: 28, dy: 36 });
  city(cam, ...G.tongguan, '潼关', { color: C.red, alpha: (1 - near) * P(t, k0 + 3.6, 0.6) * (1 - far * 0.999 > 0.5 ? 1 : 0.0), size: 26, dy: 36, r: 6 });
  const lampOn = P(t, k9 + 1.4, 1.0), flick = 0.55 + 0.45 * Math.sin(t * 5.3) * Math.sin(t * 1.7);
  const [cx, cy] = mw(cam, ...G.changan);
  if (lampOn > 0 && near < 0.5) { const r = 70 + 14 * flick; const gl = ctx.createRadialGradient(cx, cy, 2, cx, cy, r); gl.addColorStop(0, `rgba(255,120,70,${0.5 * lampOn})`); gl.addColorStop(1, 'rgba(255,120,70,0)'); ctx.fillStyle = gl; ctx.fillRect(cx - r, cy - r, 2 * r, 2 * r); }
  city(cam, ...G.changan, '长安', { color: f1 >= 0.999 ? C.red : C.gold, alpha: 1 - near * 0.0, size: near > 0.5 ? 44 : 36, capital: true, sub: (t > k1 - 0.3 && t < k6) || t > k9 ? '今西安' : '', pulse: t > k0 + 5 && t < k1 + 1 ? t : 0 });
  city(cam, ...G.jiankang, '建康', { color: C.red, alpha: ca, size: 36, capital: true, sub: t > k2 - 0.5 ? '今南京 · 都城' : '', pulse: (t > k2 + 1.6 && t < k6 - 1) || t > k10 ? t : 0 });
  // 太尉注
  tag('太尉：当时刘裕的官职，实际上的最高统帅', W / 2, 1290, fadeIO(t, k0 + 3.9, k1 - 0.1, 0.4, 0.4), { size: 28, bar: C.red });
  tag('关中：今陕西中部，渭河平原', W / 2, 1290, fadeIO(t, k1 + 1.6, k2 - 0.1, 0.4, 0.4), { size: 28, bar: C.gold });
  // 刘穆之
  const am = fadeIO(t, k2 + 2.4, k6 - 0.4, 0.5, 0.6);
  if (am > 0) {
    const [jx, jy] = mw(cam, ...G.jiankang);
    tag('十一月 · 刘穆之卒', jx - 20, jy - 120, am, { align: 'right', bar: C.gold, size: 30 });
    note('留守建康，总管后方', jx - 34, jy - 76, am, 'right');
    // 根本 —— 长安与建康之间的虚线
    ctx.save(); ctx.globalAlpha = am * P(t, k3 + 0.5, 1.2) * 0.8; ctx.strokeStyle = C.gold; ctx.lineWidth = 2.5; ctx.setLineDash([12, 12]); ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(jx, jy); ctx.stroke(); ctx.restore();
    const mx_ = (cx + jx) / 2, my_ = (cy + jy) / 2;
    tag('将佐久役思归', cx + 30, cy - 86, am * fadeIO(t, k3 + 0.3, k3 + 4.5, 0.4, 0.5), { align: 'left', size: 26 });
    text('根本', mx_, my_ - 34, { size: 46, fam: SERIF, wt: 900, color: C.gold, align: 'center', alpha: am * P(t, AT('裕以根本无托') + 0.6, 0.6) });
  }
  // 三秦父老：长安近景
  const af = fadeIO(t, k6 + 1.6, k9 + 0.5, 0.8, 0.8);
  if (af > 0) {
    const ling = [[108.47, 34.4], [108.56, 34.41], [108.63, 34.425], [108.7, 34.43], [108.76, 34.44], [108.82, 34.445], [108.88, 34.45], [108.94, 34.445], [109.0, 34.44], [108.66, 34.38]];
    ling.forEach((p, i) => { const [x, y] = mw(cam, p[0], p[1]); const u = af * P(t, k7 + 3.4 + i * 0.12, 0.5); if (u <= 0) return; ctx.save(); ctx.globalAlpha = u; ctx.fillStyle = '#d8b46a'; ctx.beginPath(); ctx.moveTo(x - 16, y + 9); ctx.lineTo(x - 7, y - 9); ctx.lineTo(x + 7, y - 9); ctx.lineTo(x + 16, y + 9); ctx.closePath(); ctx.fill(); ctx.strokeStyle = 'rgba(10,9,8,0.8)'; ctx.lineWidth = 2; ctx.stroke(); ctx.restore(); });
    const [lx, ly] = mw(cam, 108.72, 34.5); tag('长安十陵（西汉帝陵，示意）', lx, ly - 30, af * P(t, k7 + 3.6, 0.6), { size: 26, bar: C.gold });
    const [xx, xy] = mw(cam, ...G.xianyang); ctx.save(); ctx.globalAlpha = af * P(t, k7 + 5.4, 0.6); ctx.fillStyle = C.gold; ctx.fillRect(xx - 9, xy - 9, 18, 18); ctx.restore();
    tag('咸阳宫殿', xx - 20, xy + 4, af * P(t, k7 + 5.4, 0.6), { size: 26, align: 'right' });
    // 父老：聚在城门外的暖色小点
    dots(cx - 6, cy + 58, 70, 62, 26, '#f0cfa0', { alpha: af * 0.95, r: 3.2, seed: 5, jit: t });
    tag('三秦父老', cx, cy + 122, af, { size: 28, bar: '#f0cfa0' });
    note('刘裕自称汉楚元王之后，故称汉陵为“公家坟墓”（《宋书·武帝纪》）', W / 2, 1326, af * P(t, k8 + 2.6, 0.6), 'center');
  }
  // 东还
  if (back > 0) {
    geoLine(cam, G.routeBack, { color: C.redL, w: 5, frac: back, alpha: 0.9, dash: [16, 10] });
    if (back < 1) { const u = unitOn(cam, G.routeBack, back, { color: C.red, type: 'navy' }); tag('刘裕东还 · 十二月', u[0], u[1] - 58, 1, { size: 28, bar: C.red }); }
    geoLine(cam, G.routeHome, { color: C.redL, w: 5, frac: home, alpha: 0.9, dash: [16, 10] });
  }
  const al = P(t, k9 + 3.0, 0.8);
  if (al > 0) { tag('留守：次子刘义真，年十二', cx - 10, cy + 112, al, { align: 'left', bar: C.red, size: 28 }); }
  snow(t, win * 0.5, 160, 0.8);
  bands(0.55, 0.6);
}

// ---------------- 贰、叁 共用：长安的四张卡 ----------------
const RING = { yz: [540, 708], wx: [282, 936], zh: [798, 936], st: [540, 1164] };   // 义真 / 王修 / 镇恶 / 沈田子
function ringCards(t, o) {
  const a = o.alpha === undefined ? 1 : o.alpha, off = o.off || {}, lit = o.lit || {}, sub = o.sub || {};
  // 虚线：互相提防
  const wa = a * (o.wary || 0);
  wary(RING.st[0] + 60, RING.st[1] - 84, RING.zh[0] - 30, RING.zh[1] + 84, wa * (1 - (off.zh || 0)) * (1 - (off.st || 0)), t, 'rgba(224,73,47,0.95)', o.hot ? 5 : 3);
  wary(RING.wx[0] + 200, RING.wx[1], RING.zh[0] - 200, RING.zh[1], wa * 0.7 * (1 - (off.zh || 0)) * (1 - (off.wx || 0)), t, 'rgba(216,180,106,0.8)');
  wary(RING.st[0] - 60, RING.st[1] - 84, RING.wx[0] + 30, RING.wx[1] + 84, wa * 0.7 * (1 - (off.wx || 0)) * (1 - (off.st || 0)), t, 'rgba(216,180,106,0.8)');
  wary(RING.yz[0] - 60, RING.yz[1] + 84, RING.wx[0] + 30, RING.wx[1] - 84, wa * 0.6 * (1 - (off.wx || 0)), t, 'rgba(216,180,106,0.8)');
  wary(RING.yz[0] + 60, RING.yz[1] + 84, RING.zh[0] - 30, RING.zh[1] - 84, wa * 0.6 * (1 - (off.zh || 0)), t, 'rgba(216,180,106,0.8)');
  pcard(...RING.yz, { name: '刘义真', role: '安西将军 · 留守', sub: sub.yz || '刘裕次子，年十二', alpha: a * (o.aYz === undefined ? 1 : o.aYz), bar: C.red, lit: lit.yz, tag: '主' });
  pcard(...RING.wx, { name: '王修', role: '长史 · 管行政', sub: sub.wx || '京兆人', alpha: a * (o.aWx === undefined ? 1 : o.aWx), bar: C.gold, off: off.wx, note: o.nWx, lit: lit.wx, tag: '副' });
  pcard(...RING.zh, { name: '王镇恶', role: '司马 · 管军事', sub: sub.zh || '家在关中', alpha: a * (o.aZh === undefined ? 1 : o.aZh), bar: C.gold, off: off.zh, note: o.nZh, lit: lit.zh, tag: '副' });
  pcard(...RING.st, { name: '沈田子', role: '中兵参军 · 带兵', sub: sub.st || '南来诸将之一', alpha: a * (o.aSt === undefined ? 1 : o.aSt), bar: C.red, off: off.st, note: o.nSt, lit: lit.st });
}

// ---------------- 贰 · 猛兽与群狐 ----------------
function sceneS2(t) {
  const S = TL.secs.s2;
  const k0 = AT('留下来守关中的'), k1 = AT('孩子身边有两个副手'), k2 = AT('王镇恶家在关中'), k3 = AT('刘裕私下回了'), k4 = AT('钟会不得遂其乱'), k5 = AT('当年钟会在蜀地'), k6 = AT('这话狠在哪儿'), k7 = AT('《通鉴》的作者司马光'), k9 = AT('不放心就别用'), k10 = AT('敌人也看在眼里'), k11 = AT('此天以关中赐我'), k13 = AT('人还没走远'), e = S.end;
  const cam = mapCam(kf([[k0, 108.93, 34.4, 3.4], [k10 - 0.4, 108.93, 34.45, 3.0], [k10 + 2.6, 108.9, 36.25, 6.4], [k13 - 0.2, 108.9, 36.1, 6.2], [k13 + 2.2, 108.93, 34.5, 3.4], [e, 108.93, 34.5, 3.3]], t));
  const xiaA = fadeIO(t, k10 + 0.6, k13 + 0.6, 1, 1);
  drawMap(cam, lerp(0.46, 0.2, xiaA)); season('winter', 0.6);
  drawRivers(cam, lerp(0.5, 0.9, xiaA));
  city(cam, ...G.changan, '长安', { color: C.red, alpha: 0.9, size: 34, capital: true });
  // 夏
  if (xiaA > 0) {
    region(cam, '夏', 108.2, 37.3, C.xia, xiaA * 1.4, 84);
    city(cam, ...G.tongwan, '统万城', { color: C.xia, alpha: xiaA, size: 32, sub: '夏都 · 今陕北靖边', sq: true });
    const fx = 0.1 + eio(prog(t, k10 + 3, e)) * 0.32;
    geoLine(cam, G.routeXia, { color: C.xia, w: 9, frac: fx, alpha: xiaA * 0.95, glow: 'rgba(170,180,191,0.5)', blur: 12 });
    const ee = unitOn(cam, G.routeXia, fx, { color: C.xia, type: 'cav', alpha: xiaA });
    tag('夏：赫连勃勃所建，今陕北、宁夏一带', W / 2, 452, xiaA * fadeIO(t, k10 + 2.6, k11 - 0.6, 0.5, 0.4), { bar: C.xia });
    pcard(540, 1180, { name: '王买德', role: '夏 · 赫连勃勃的谋士', sub: '以下是敌方的看法', alpha: xiaA * P(t, k10 + 6.5, 0.6), bar: C.xia, w: 470, h: 150, size: 50 });
  }
  // 卡片
  const ca = (1 - xiaA) * P(t, k0 + 0.1, 0.8);
  const aWx = P(t, k1 + 0.6, 0.5), aZh = P(t, k1 + 3.4, 0.5), aSt = P(t, k1 + 6.2, 0.5);
  const wr = P(t, k2 + 3.2, 1.0);
  const hot = t > k4 && t < k10;
  ringCards(t, { alpha: ca, aWx, aZh, aSt, wary: wr, hot, lit: { zh: fadeIO(t, k2, k2 + 4.4, 0.5, 0.8) + fadeIO(t, k5 + 2.4, k6, 0.4, 0.5), st: fadeIO(t, k5 + 5.6, k7, 0.4, 0.6), wx: fadeIO(t, k1 + 0.6, k1 + 3.2, 0.3, 0.5), yz: fadeIO(t, k0, k1, 0.4, 0.5) }, sub: { zh: t > k2 ? '家在关中 · 克长安首功' : undefined } });
  if (ca > 0) {
    note('毛德祖、傅弘之等，亦在留守诸将之列', W / 2, 1310, ca * fadeIO(t, k1 + 7.4, k3, 0.5, 0.5), 'center');
    tag('南人皆忌之', (RING.st[0] + RING.zh[0]) / 2 + 96, (RING.st[1] + RING.zh[1]) / 2 + 26, ca * fadeIO(t, k2 + 3.6, k4, 0.5, 0.4), { size: 26, bar: C.red });
    // 猛兽 / 群狐
    const am = ca * fadeIO(t, k5 + 4.4, k7 - 0.2, 0.5, 0.5);
    tag('猛兽', RING.zh[0] + 120, RING.zh[1] - 118, am, { size: 34, fam: SERIF, wt: 900, color: C.gold });
    tag('群狐 · 卿等十余人', RING.st[0], RING.st[1] + 122, am, { size: 34, fam: SERIF, wt: 900, color: C.redL });
    if (am > 0) dots(RING.st[0], RING.st[1] + 176, 12, 150, 14, C.redL, { alpha: am, r: 5.5, seed: 3 });
    // 刘裕的话，从远处递到沈田子手里
    const aq = ca * fadeIO(t, k3, k7 - 0.2, 0.5, 0.5);
    tag('刘裕 · 私谓田子', 908, 1206, aq, { size: 28, bar: C.red });
    arrow(800, 1206, 748, 1190, { color: C.redL, w: 4, head: 16, frac: P(t, k3 + 0.6, 0.8), alpha: aq });
    // 司马光
    const ag = ca * fadeIO(t, k9 + 2.2, k10 - 0.2, 0.5, 0.4);
    panel(120, 1262, 840, 84, ag); text('“是斗之使为乱也”', 152, 1305, { size: 38, fam: SERIF, wt: 900, color: C.gold, alpha: ag, stroke: 0 }); text('—— 臣光曰', 928, 1307, { size: 26, fam: SERIF, wt: 700, color: C.gold, alpha: ag, stroke: 0, align: 'right' });
  }
  bands(0.6, 0.62);
}

// ---------------- 叁 · 三条人命 ----------------
function sceneS3(t) {
  const S = TL.secs.s3;
  const k0 = AT('第二年正月'), k3 = AT('沈田子把王镇恶请到'), k4 = AT('长史王修随即'), k5 = AT('到这年冬天'), k7 = AT('王镇恶要反，所以'), k8 = AT('人情离骇'), k9 = AT('人心又散又怕'), k10 = AT('夏军其实被打退过'), e = S.end;
  const cam = mapCam(kf([[k0, 108.93, 34.9, 4.2], [k8, 108.93, 34.75, 3.9], [k9 + 2, 108.75, 34.7, 4.4], [e, 108.7, 34.7, 4.5]], t));
  const fall = P(t, k8 + 0.4, 3.2);           // 关中褪色
  drawMap(cam, lerp(0.44, 0.22, fall)); season('winter', 0.7);
  tint(cam, GUANZHONG, 'rgba(170,180,191,1)', 0.22 * fall);
  drawRivers(cam, lerp(0.5, 0.85, fall));
  // 夏军逼近：正月进至渭阳，被傅弘之击退；冬，再至
  const adv = t < k4 ? lerp(0.42, 0.86, eio(prog(t, k0, k3))) : t < k5 ? lerp(0.86, 0.6, eio(prog(t, k4 + 1, k5))) : lerp(0.6, 0.93, eio(prog(t, k5, k9 + 2)));
  geoLine(cam, G.routeXia, { color: C.xia, w: 9, frac: adv, alpha: 0.9, glow: 'rgba(170,180,191,0.5)', blur: 12 });
  { const gy = lerp(360, 900, adv), gg = ctx.createLinearGradient(0, 0, 0, gy); gg.addColorStop(0, 'rgba(170,180,191,0.34)'); gg.addColorStop(1, 'rgba(170,180,191,0)'); ctx.fillStyle = gg; ctx.fillRect(0, 0, W, gy); text('夏军', 930, lerp(300, 560, adv), { size: 40, fam: SERIF, wt: 900, align: 'center', color: C.xiaL, alpha: 0.9 * (1 - fall) }); }
  city(cam, ...G.changan, '长安', { color: fall > 0.9 ? C.redL : C.red, alpha: 0.95, size: 34, capital: true, dy: 44 });
  // 郡县易帜：红点翻灰
  if (fall > 0) for (let i = 0; i < 26; i++) { const lon = 107.2 + 3.0 * hash(i, 21), lat = 34.2 + 0.85 * hash(i, 22); if (Math.hypot(lon - 108.93, lat - 34.33) < 0.14) continue; const [x, y] = mw(cam, lon, lat); const u = clamp(fall * 1.6 - hash(i, 23) * 0.6); ctx.save(); ctx.globalAlpha = 0.9 * P(t, k8, 0.6); ctx.fillStyle = u > 0.5 ? C.xia : C.red; ctx.beginPath(); ctx.arc(x, y, 6, 0, 7); ctx.fill(); ctx.strokeStyle = 'rgba(8,8,8,0.8)'; ctx.lineWidth = 2; ctx.stroke(); ctx.restore(); }
  // 卡片依次熄灭
  const oZh = P(t, k3 + 3.2, 1.4), oSt = P(t, k4 + 1.9, 1.4), oWx = P(t, ET('王镇恶要反，所以') - 1.6, 1.4);
  const ca = 1 - fall * 0.92;
  const calm = t > k10 ? 0 : 1;
  ringCards(t, { alpha: ca, aYz: (1 - fall * 0.15) / Math.max(0.05, ca), wary: (1 - oWx) * (0.6 + 0.4 * Math.sin(t * 3) ** 2), hot: t < k4,
    off: { zh: oZh, st: oSt, wx: oWx }, nZh: '正月 · 为沈田子所杀', nSt: '同日 · 为王修所斩', nWx: '是年冬 · 为义真左右所杀',
    lit: { st: fadeIO(t, k3, k3 + 3.2, 0.4, 0.3) * (1 - oSt), wx: fadeIO(t, k4, k4 + 1.9, 0.3, 0.3) * (1 - oWx), yz: fadeIO(t, k5 + 1, e, 0.6, 0.5) }, sub: { zh: '家在关中 · 克长安首功', yz: oWx > 0.5 ? '只剩一个孩子' : '刘裕次子' } });
  tag('矫称受太尉令', RING.st[0], RING.st[1] + 120, ca * fadeIO(t, k3 + 4.6, k4 + 1.2, 0.4, 0.3), { size: 26, bar: C.red });
  tag('讹言：镇恶欲尽杀南人', RING.zh[0] - 30, RING.zh[1] - 116, ca * fadeIO(t, k0 + 2.4, k3 + 2.6, 0.4, 0.4), { size: 26, bar: C.gold });
  tag('其间：傅弘之破夏军于池阳、寡妇渡', W / 2, 566, fadeIO(t, k4 + 1.2, k5 + 0.4, 0.5, 0.5), { size: 26, bar: C.red });
  tag('关中郡县，悉降于夏', W / 2, 640, fadeIO(t, k9 + 2.2, k10 + 0.4, 0.5, 0.5), { size: 30, bar: C.xia });
  // 结：把那句话再亮一次
  const ar = fadeIO(t, k10 + 2.6, e - 0.4, 0.6, 0.5);
  panel(120, 1150, 840, 150, ar); text('“猛兽不如群狐，卿等十余人，', 152, 1200, { size: 38, fam: SERIF, wt: 900, color: C.gold, alpha: ar, stroke: 0 }); text('何惧王镇恶！”', 152, 1258, { size: 38, fam: SERIF, wt: 900, color: C.gold, alpha: ar, stroke: 0 }); text('—— 刘裕，前一年冬', 928, 1262, { size: 26, fam: SERIF, wt: 700, color: C.gold, alpha: ar, stroke: 0, align: 'right' });
  snow(t, 0.35, 140, 0.7);
  bands(0.6, 0.62);
}

// ---------------- 肆 · 青泥 ----------------
function sceneS4(t) {
  const S = TL.secs.s4;
  const k0 = AT('刘裕派朱龄石去接替'), k1 = AT('多载宝货'), k2 = AT('车上装满抢来的'), k3 = AT('夏军三万追上来'), k4 = AT('刘义真一个人躲进草丛'), k5 = AT('可刎身头以南'), k6 = AT('把我的头砍下来'), k7 = AT('断后的傅弘之被俘'), k8 = AT('弘之不屈'), k9 = AT('他不肯。天很冷'), k10 = AT('长安的百姓，把朱龄石'), k11 = AT('消息传到彭城'), k12 = AT('登城北望'), k13 = AT('登上城楼往北看'), k14 = AT('北伐拿下的关中'), e = S.end;
  const cam = mapCam(kf([[k0, 109.05, 34.3, 1.5], [k3, 109.2, 34.22, 1.15], [k4 + 1, 109.36, 34.12, 0.8], [k7 - 0.3, 109.4, 34.1, 0.8], [k7 + 2.5, 109.32, 34.15, 0.62], [k10 - 0.4, 109.32, 34.15, 0.58], [k10 + 2.2, 109.6, 34.42, 3.2], [k11 - 0.3, 109.7, 34.42, 3.3], [k11 + 3, 112.6, 34.6, 12.2], [e, 112.7, 34.7, 12.6]], t));
  const far = sstep((cam.wdeg - 4) / 4);
  drawMap(cam, 0.12); season('winter', 0.68);
  const gray = P(t, k10 + 0.6, 2.5);
  tint(cam, GUANZHONG, 'rgba(150,160,172,1)', 0.2 * gray);
  drawRivers(cam);
  riverNames(cam, far * 0.9, 'he');
  // —— 傅弘之一段：画面几乎收掉，只留地名
  const hush = fadeIO(t, k7 + 0.6, k10 - 0.2, 1.6, 1.2);
  // 撤退车队：又慢又粗的红线
  const conv = t < k3 ? lerp(0.0, 0.34, prog(t, k0 + 1.2, k3)) : lerp(0.34, 0.47, prog(t, k3, k3 + 4));
  const cut = P(t, k3 + 3.2, 1.2), lineA = (1 - P(t, k4 + 0.4, 2.0)) * (1 - hush);
  if (lineA > 0) {
    geoLine(cam, G.routeRetreat, { color: C.redD, w: 30, frac: conv, from: Math.max(0, conv - 0.36), alpha: lineA * 0.85 });
    geoLine(cam, G.routeRetreat, { color: C.red, w: 20, frac: conv, from: Math.max(0, conv - 0.36), alpha: lineA * (1 - cut * 0.7), dash: cut > 0.3 ? [24, 16 + 40 * cut] : null });
    const hd = along(...(() => { const sp = smoothC(G.routeRetreat).map(q => mw(cam, q[0], q[1])); const cum = pathLen(sp); return [sp, cum, conv * cum[cum.length - 1]]; })());
    tag('义真军 · 多载宝货、子女', hd[0] + 40, hd[1] - 70, lineA * fadeIO(t, k1 - 0.4, k3 + 0.5, 0.5, 0.4), { align: 'left', bar: C.red, size: 28 });
    tag('“一日行不过十里”—— 傅弘之', hd[0] + 40, hd[1] - 16, lineA * fadeIO(t, k2 + 3.2, k3 + 0.5, 0.5, 0.4), { align: 'left', size: 26 });
  }
  // 夏军追及，切断车队
  const ch = eio(prog(t, k3 + 0.2, k3 + 3.4)), chA = fadeIO(t, k3, k7 + 0.4, 0.4, 1.4);
  if (chA > 0) { geoLine(cam, G.routeChase, { color: C.xia, w: 13, frac: ch, alpha: chA, glow: 'rgba(190,200,211,0.6)', blur: 14 }); const u = unitOn(cam, G.routeChase, ch, { color: C.xia, type: 'cav', alpha: chA }); tag('夏军 · 三万', u[0] - 46, u[1] - 62, chA, { align: 'right', bar: C.xia, size: 30 }); }
  // 地名
  const [qx, qy] = mw(cam, ...G.qingni);
  city(cam, ...G.changan, '长安', { color: gray > 0.5 ? C.xia : C.red, alpha: 1 - hush, size: 36, capital: true });
  const qa = P(t, k3 - 0.2, 0.6);
  ctx.save(); ctx.globalAlpha = qa * 0.9 * (1 - far); ctx.strokeStyle = C.cream; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.arc(qx, qy, 11, 0, 7); ctx.stroke(); ctx.restore();
  text('青泥', qx, qy + 54, { size: lerp(44, 64, hush), fam: SERIF, wt: 900, align: 'center', alpha: qa * (1 - far), ls: 8 });
  text('今陕西蓝田一带', qx, qy + 108, { size: 26, wt: 500, align: 'center', alpha: qa * (1 - hush) * 0.9 * (1 - far), color: C.dimtxt });
  // 草中：义真与段宏
  const ag = fadeIO(t, k4 + 0.6, k7 + 0.2, 0.6, 0.8);
  if (ag > 0) {
    const [gx, gy] = mw(cam, 109.47, 34.09), go = eio(prog(t, k6 + 3.2, k7 + 0.2));
    const dx = lerp(qx + 30, gx, eio(prog(t, k4 + 1.6, k5 - 0.2))), dy = lerp(qy + 10, gy - 22, eio(prog(t, k4 + 1.6, k5 - 0.2)));
    const ox = go * 150, oy = go * 70;
    ctx.save(); ctx.globalAlpha = ag; ctx.fillStyle = C.redL; ctx.beginPath(); ctx.arc(gx + ox, gy + oy, 9, 0, 7); ctx.fill(); ctx.fillStyle = C.cream; ctx.beginPath(); ctx.arc(dx + ox, dy + oy, 8, 0, 7); ctx.fill(); ctx.restore();
    tag('刘义真 · 独逃草中', gx + ox + 22, gy + oy + 34, ag, { align: 'left', bar: C.red, size: 26 });
    tag('段宏 · 单骑追寻', dx + ox + 22, dy + oy - 34, ag * P(t, k4 + 1.6, 0.5), { align: 'left', size: 26 });
  }
  if (hush > 0) { ctx.fillStyle = `rgba(9,11,15,${hush * 0.8})`; ctx.fillRect(0, 0, W, H); text('青泥', qx, qy + 54, { size: 64, fam: SERIF, wt: 900, align: 'center', alpha: hush * 0.9, ls: 8 }); }
  // 长安易手、朱龄石
  const az = fadeIO(t, k10 + 0.7, k11 + 1.8, 0.6, 0.8);
  if (az > 0) {
    const [cx, cy] = mw(cam, ...G.changan), [tx, ty] = mw(cam, ...G.tongguan), go = eio(prog(t, k10 + 2.0, k11 - 0.6));
    arrow(cx + 20, cy - 6, tx, ty, { color: C.redL, w: 5, frac: go, alpha: az, dash: [12, 10] });
    tag('长安百姓逐朱龄石', cx + 16, cy - 164, az, { align: 'left', bar: C.gold, size: 28 });
    tag('龄石焚宫殿东走 · 后与弟超石同被杀', cx + 16, cy - 108, az * P(t, k10 + 2.6, 0.5), { align: 'left', size: 26 });
    region(cam, '关 中', 108.4, 34.86, C.xiaL, az * 1.3, 60);
  }
  // 彭城：登城北望
  const ap = P(t, k11 + 2.2, 1.0);
  if (ap > 0) {
    city(cam, ...G.pengcheng, '彭城', { color: C.red, alpha: ap, size: 38, capital: true, sub: '今徐州', pulse: t });
    region(cam, '关 中', 108.9, 35.05, C.xiaL, ap * 1.4, 54);
    const [px, py] = mw(cam, ...G.pengcheng), [cx, cy] = mw(cam, ...G.changan);
    ctx.save(); ctx.globalAlpha = ap * fadeIO(t, k12 - 0.4, e, 0.8, 0.6) * 0.75; ctx.strokeStyle = C.cream; ctx.lineWidth = 2.5; ctx.setLineDash([6, 14]); ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(cx, cy); ctx.stroke(); ctx.restore();
    tag('怒甚，刻日北伐 → 知义真得免，乃止', W / 2, 660, ap * fadeIO(t, k11 + 3, k12 + 0.3, 0.5, 0.4), { size: 28, bar: C.red });
    panel(150, 1236, 780, 96, fadeIO(t, k14, e - 0.3, 0.5, 0.4));
    const aa = fadeIO(t, k14, e - 0.3, 0.5, 0.4); text('417 年八月 克长安', 190, 1284, { size: 34, fam: SERIF, wt: 900, alpha: aa, stroke: 0, color: C.redL }); text('→', 540, 1284, { size: 34, wt: 700, alpha: aa, stroke: 0, align: 'center' }); text('418 年十一月 失长安', 890, 1284, { size: 34, fam: SERIF, wt: 900, alpha: aa, stroke: 0, color: C.xiaL, align: 'right' });
  }
  snow(t, lerp(0.75, 0.3, far) * (1 + hush * 0.5), 300, 1.4 + hush * 0.8);
  towerSilhouette(fadeIO(t, k12 - 1.2, e - 0.2, 1.4, 0.8), 1640);
  bands(0.6, 0.62);
}
