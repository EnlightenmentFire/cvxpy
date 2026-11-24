'use strict';
/* Scene definitions for 长平之战. Every visual event is keyed to narration line ids. */
const a = id => D.tl.lines[id].t0, z = id => D.tl.lines[id].t1;
const lp = (t, id) => seg(t, a(id), z(id));
const on = (t, id0, id1 = id0, fi = .4, fo = .4) => fade(t, a(id0), z(id1), fi, fo);
const onq = (t, id0, id1 = id0) => fade(t, a(id0) - .12, z(id1) + .38, .3, .3);
const PL = { xianyang: [108.71, 34.33], xinzheng: [113.74, 34.40], handan: [114.49, 36.61], daliang: [114.35, 34.80], linzi: [118.31, 36.83], chen: [114.88, 33.73], ji: [116.40, 39.90], yewang: [112.93, 35.09], cp: [112.92, 35.80], changzhi: [113.12, 36.19], jincheng: [112.85, 35.49], guguan: [113.007, 35.922], kongcang: [112.735, 35.725], luoyang: [112.45, 34.62] };
const V = { region: [111.7, 35.6, 140], shang: [113.0, 35.9, 430], battle: [112.905, 35.80, 1750], henei: [113.0, 35.47, 640], states: [113.6, 35.5, 95] };
const SHANGDANG = [[112.55, 36.80], [113.35, 36.90], [113.62, 36.3], [113.52, 35.75], [113.25, 35.40], [112.75, 35.30], [112.45, 35.60], [112.33, 36.2]];
const HENEI = [[112.40, 35.13], [112.9, 35.21], [113.5, 35.37], [114.0, 35.55], [114.08, 35.25], [113.5, 35.02], [112.9, 34.90], [112.40, 34.93]];
const HIDE = new Set(['s1.4', 's1.7', 's3.8', 's4.6', 's5.2', 's6.4', 's7.2', 's8.4', 's9.2', 's10.1', 's10.2', 's10.3']);
const NOTE_Y = 1296;

/* seventeen cities (schematic positions inside Shangdang) */
const CITIES = (() => { const r = rng(17), out = []; const inside = (x, y) => { let c = false; for (let i = 0, j = SHANGDANG.length - 1; i < SHANGDANG.length; j = i++) { const [xi, yi] = SHANGDANG[i], [xj, yj] = SHANGDANG[j]; if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) c = !c; } return c; }; let guard = 0; while (out.length < 17 && guard++ < 5000) { const x = 112.45 + r() * 1.1, y = 35.42 + r() * 1.35; if (!inside(x, y)) continue; if (out.some(q => Math.hypot(q[0] - x, (q[1] - y)) < .17)) continue; out.push([x, y, r()]); } return out; })();
function cities(t, colorF, alphaF) { CITIES.forEach((c, i) => { const al = alphaF(i, c); if (al <= 0) return; const [x, y] = P(c[0], c[1]); const col = colorF(i, c); ctx.save(); ctx.globalAlpha = al; ctx.shadowColor = col; ctx.shadowBlur = 16; ctx.fillStyle = col; ctx.fillRect(x - 6, y - 6, 12, 12); ctx.shadowBlur = 0; ctx.strokeStyle = 'rgba(0,0,0,.8)'; ctx.lineWidth = 1.5; ctx.strokeRect(x - 6, y - 6, 12, 12); ctx.restore(); }); }
function wedge(a_, color = C.gold, fill = .10) { if (a_ <= .003) return; const d = spline([...SHANGDANG, SHANGDANG[0], SHANGDANG[1]], 10).slice(0, -10); ctx.save(); ctx.globalAlpha = a_; poly(d, true); ctx.fillStyle = color; ctx.globalAlpha = a_ * fill; ctx.fill(); ctx.globalAlpha = a_; ctx.strokeStyle = color; ctx.lineWidth = 3; ctx.setLineDash([10, 7]); ctx.shadowColor = 'rgba(0,0,0,.8)'; ctx.shadowBlur = 8; ctx.stroke(); ctx.restore(); }
function stateName(ch, lon, lat, color, a_, size = 120) { const [x, y] = P(lon, lat); txt(ch, x, y, { size, w: 900, color, a: a_ * .62, shadow: 1 }); }
function states(a_, which = '秦韩赵魏', ov = {}) { const S = { '秦': [109.0, 35.0, C.qinHi, '#3d5a78'], '韩': [113.05, 34.25, C.han, C.han], '赵': [114.55, 37.35, C.zhaoHi, C.zhao], '魏': [114.75, 35.25, C.wei, C.wei], '齐': [118.3, 36.2, C.qi, C.qi], '楚': [114.6, 32.3, C.chu, C.chu], '燕': [116.5, 39.2, C.yan, C.yan] }; for (const k of which) { const s = S[k]; if (ov[k]) { s[0] = ov[k][0]; s[1] = ov[k][1]; } glow(s[0], s[1], k === '秦' ? 2.6 : 1.7, s[3], a_ * .34); stateName(k, s[0], s[1], s[2], a_, clamp(cam.ppd * .9, 84, 150)); } }
function danHi(a_) { if (a_ <= .003) return; ctx.save(); ctx.globalAlpha = a_; ctx.strokeStyle = 'rgba(150,190,215,.9)'; ctx.lineWidth = clamp(cam.ppd / 500, 1.6, 4.5); ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.shadowColor = 'rgba(90,150,200,.8)'; ctx.shadowBlur = 8; poly(D.dan); ctx.stroke(); ctx.restore(); }
function noteTag(s, a_) { tag(s, 64, NOTE_Y, a_); }
function speaker(s, y, a_) { txt(s, W / 2, y, { size: 34, w: 700, color: C.bone, a: a_, ls: 2 }); }
function grainDots(path, t, a_, n = 14, speed = .12, stopAt = 1, color = C.gold) { if (a_ <= .003) return; const d = spline(path, 12); ctx.save(); for (let i = 0; i < n; i++) { let p = ((t * speed + i / n) % 1); p = Math.min(p, stopAt - (i % 5) * .012); if (p < 0) continue; const q = along(d, p); const [x, y] = P(q[0], q[1]); ctx.globalAlpha = a_ * (p < .06 ? p / .06 : 1); ctx.fillStyle = color; ctx.fillRect(x - 3.5, y - 3.5, 7, 7); ctx.strokeStyle = 'rgba(0,0,0,.7)'; ctx.lineWidth = 1; ctx.strokeRect(x - 3.5, y - 3.5, 7, 7); } ctx.restore(); }
function cross(lon, lat, a_, size = 22, color = '#ffd9c9') { if (a_ <= .003) return; const [x, y] = P(lon, lat); ctx.save(); ctx.globalAlpha = a_; ctx.strokeStyle = 'rgba(0,0,0,.8)'; ctx.lineWidth = 9; ctx.lineCap = 'round'; for (let k = 0; k < 2; k++) { ctx.beginPath(); ctx.moveTo(x - size, y - size); ctx.lineTo(x + size, y + size); ctx.moveTo(x + size, y - size); ctx.lineTo(x - size, y + size); ctx.stroke(); ctx.strokeStyle = color; ctx.lineWidth = 5; } ctx.restore(); }

/* ---------- battlefield shared geometry (schematic over real terrain) ---------- */
const QW = [[112.775, 35.93], [112.80, 35.80], [112.83, 35.67]];           // Qin wall, west of the Dan (后世考证: 丹河以西)
const ZW = [[112.915, 35.935], [112.94, 35.82], [112.965, 35.70]];          // Zhao wall, east bank
const ZCAMP = [112.995, 35.835];
const SUPPLY = [[112.995, 35.845], [113.007, 35.922], [113.10, 36.01], [113.30, 36.13], [113.6, 36.3]];
const R25 = [[112.75, 35.71], [112.70, 35.80], [112.685, 35.90], [112.72, 35.975], [112.80, 36.01], [112.90, 36.015], [112.985, 35.985], [113.03, 35.94]];
const R5 = [[112.872, 35.672], [112.905, 35.73], [112.925, 35.80], [112.93, 35.905]];
const zAll = new Troop(330, 11), zA = new Troop(210, 12), zC = new Troop(120, 13), qMain = new Troop(230, 21), qF = new Troop(60, 22), q25 = new Troop(75, 23), q5 = new Troop(30, 24), civ = new Troop(90, 31), hn = new Troop(460, 41), qRing = new Troop(260, 25);
const fZline = F.band([[112.925, 35.93], [112.95, 35.82], [112.975, 35.71]], .014);
const fZfwd = F.blob([112.79, 35.79], .022, .06);
const fZcamp = F.blob(ZCAMP, .020, .028);
const fZatk = F.band([[112.818, 35.90], [112.838, 35.80], [112.862, 35.69]], .011);
const fZatkRing = F.blob([112.855, 35.80], .017, .034);
const fQwest = F.band([[112.66, 35.92], [112.67, 35.80], [112.69, 35.66]], .012);
const fQline = F.band([[112.755, 35.93], [112.778, 35.80], [112.81, 35.67]], .010);
const fQfront = F.blob([112.878, 35.80], .012, .04);
const fQback = F.blob([112.775, 35.80], .009, .04);
const fQ25end = F.band([[112.95, 35.945], [113.03, 35.93], [113.078, 35.89]], .008);
const fQ5end = F.band([[112.905, 35.70], [112.925, 35.80], [112.928, 35.90]], .006);
const stepChips = (t, active, a_) => { if (a_ <= .003) return; const names = ['佯败', '追至秦壁', '绝其后', '绝壁间']; const w = 228, x0 = 64, y = 352; names.forEach((n, i) => { const act = i === active, done = i < active; ctx.save(); ctx.globalAlpha = a_ * (act ? 1 : done ? .75 : .45); ctx.fillStyle = act ? 'rgba(227,201,138,.95)' : 'rgba(8,10,13,.8)'; ctx.fillRect(x0 + i * (w + 14), y - 30, w, 60); ctx.strokeStyle = C.goldDim; ctx.lineWidth = 1.5; ctx.strokeRect(x0 + i * (w + 14), y - 30, w, 60); ctx.restore(); txt('①②③④'[i] + ' ' + n, x0 + i * (w + 14) + w / 2, y + 1, { size: 30, fam: HEI, w: 700, color: act ? '#14110a' : C.bone, a: a_ * (act ? 1 : done ? .8 : .5), shadow: 0 }); }); };

/* ================= scenes ================= */
const SC = [];
const sceneStart = k => SECS[k].a - (k === 's1' ? 1.2 : .75);

/* ---- S0 cold open + title ---- */
SC.push({ a: 0, b: sceneStart('s1'), draw(t) {
  const tPull = a('s0.6'), tTitle = z('s0.7') + .25;
  setCam(camKeys(t, [[0, [112.92, 35.80, 1500]], [tPull, [112.92, 35.80, 1650], x => x], [z('s0.7') - .2, V.region]]));
  const br = lerp(.30, .72, ease(seg(t, tPull, z('s0.7'))));
  drawMap(0, br * fade(t, 0, 1e9, 1.2, .1));
  const reveal = ease(seg(t, a('s0.7') - .2, z('s0.7')));
  if (reveal > 0) { states(reveal, '秦赵'); place(...PL.cp, '长平', { a: reveal, size: 40, color: C.gold, dot: 7 }); }
  // year
  const ya = fade(t, .25, a('s0.2') + .2, .5, .5);
  txt('公元前', W / 2, 640, { size: 46, w: 600, color: C.goldDim, a: ya, ls: 14 }); txt('260', W / 2, 790, { size: 250, w: 900, color: C.bone, a: ya, ls: 6 }); txt('年', W / 2, 950, { size: 46, w: 600, color: C.goldDim, a: ya }); txt('赵国 · 临阵换将', W / 2, 1090, { size: 56, w: 700, color: C.gold, a: ya * ease(seg(t, a('s0.1') + 1.2, a('s0.1') + 2)), ls: 4 });
  // the mother's memorial as vertical slips
  const la = fade(t, a('s0.2') + .3, a('s0.6') + .5, .6, .7);
  if (la > 0) {
    const cols = [['括不可使将', a('s0.2') + 1.6, z('s0.2')], ['王终遣之即有如不称', a('s0.4') + .6, a('s0.4') + 2.6], ['妾得无随坐乎', a('s0.4') + 2.6, z('s0.4')]];
    txt('赵括之母上书', W / 2, 360, { size: 40, w: 700, color: C.goldDim, a: la, ls: 10 });
    cols.forEach((c, i) => { const x = W / 2 + 190 - i * 190, chars = [...c[0]], top = 470; ctx.save(); ctx.globalAlpha = la * .9; ctx.fillStyle = 'rgba(196,160,96,.10)'; ctx.fillRect(x - 58, top - 40, 116, 760); ctx.strokeStyle = 'rgba(196,160,96,.35)'; ctx.lineWidth = 1.5; ctx.strokeRect(x - 58, top - 40, 116, 760); ctx.restore();
      chars.forEach((ch, k) => { const ca = clamp(seg(t, c[1], c[2]) * (chars.length + 1) - k); txt(ch, x, top + 16 + k * 79, { size: 66, w: 700, color: C.gold, a: la * ca }); }); });
    const wa = la * ease(seg(t, a('s0.5'), a('s0.5') + .5));
    txt('「王许诺。」', W / 2, 1252, { size: 60, w: 800, color: C.bone, a: wa });
    txt('——《史记·廉颇蔺相如列传》', W / 2, 1314, { size: 26, fam: HEI, w: 500, color: C.goldDim, a: la * .9 });
  }
  // title card
  const ta = fade(t, tTitle, sceneStart('s1') + .35, .5, .5);
  if (ta > 0) { shade(.8 * ta); txt('公元前260年', W / 2, 640, { size: 38, w: 600, color: C.goldDim, a: ta, ls: 10 }); txt('长平之战', W / 2, 810, { size: 196, w: 900, color: C.bone, a: ta, ls: 10 }); rule(330, 750, 950, ta); txt('赵国输给的不是秦军', W / 2, 1030, { size: 58, w: 700, color: C.gold, a: ta * ease(seg(t, tTitle + .5, tTitle + 1.1)), ls: 3 }); txt('是秦国', W / 2, 1120, { size: 76, w: 900, color: C.gold, a: ta * ease(seg(t, tTitle + 1.0, tTitle + 1.6)), ls: 12 }); }
} });

/* ---- S1 一块烫手的地 ---- */
SC.push({ a: sceneStart('s1'), b: sceneStart('s2'), draw(t) {
  setCam(camKeys(t, [[a('s1.1'), V.region], [z('s1.1') - .2, [111.9, 35.5, 150], x => x], [a('s1.2') + 2.6, V.shang], [a('s1.12'), [113.02, 35.92, 455], x => x], [z('s1.13'), [112.75, 35.75, 330]]]));
  const dimQ = Math.max(on(t, 's1.4'), on(t, 's1.7', 's1.8'), on(t, 's1.9', 's1.10'), on(t, 's1.11'));
  drawMap(0, 1 - .6 * dimQ);
  const far = 1 - sstep(230, 380, cam.ppd);
  states(1, '秦韩赵魏');
  wedge(ease(seg(t, a('s1.1') + .8, a('s1.1') + 1.8)), C.gold, .05 + .02 * Math.sin(t * 2));
  // capitals
  place(...PL.xianyang, '咸阳', { a: far, size: 30, dx: 12, dy: 34, align: 'center' }); place(...PL.handan, '邯郸', { size: 32, color: C.zhaoHi, align: 'right' }); place(...PL.xinzheng, '新郑', { a: far, size: 30, color: C.han, sub: '韩都' }); place(...PL.daliang, '大梁', { a: far, size: 30, color: C.wei });
  // Qin takes Yewang, road cut
  const p1 = lp(t, 's1.1');
  const road = [[112.92, 35.62], [112.90, 35.35], PL.yewang, [113.25, 34.80], PL.xinzheng];
  const cutA = ease(seg(p1, .55, .7));
  dashLine(road, { color: C.han, a: far * (1 - .7 * cutA) * ease(seg(p1, .05, .25)), width: 4, p: seg(p1, .05, .35) });
  arrow([[110.6, 35.25], [111.7, 35.0], [112.86, 35.07]], seg(p1, .3, .55), { color: C.qin, rim: C.qinRim, width: 22, a: 1 - sstep(300, 420, cam.ppd) * .0 });
  place(...PL.yewang, '野王', { a: ease(seg(p1, .3, .45)), size: 34, color: C.qinHi, sub: far > .5 ? '' : '今河南沁阳', ring: (t * .8) % 1, dx: 16 });
  cross(112.93, 35.22, cutA * (1 - seg(t, a('s1.3'), a('s1.3') + 1)), 18);
  txt('上党', ...((q) => [q[0], q[1]])(P(113.0, 36.05)), { size: clamp(cam.ppd * .22, 52, 96), w: 900, color: C.gold, a: ease(seg(t, a('s1.1') + 1.2, a('s1.1') + 2)) * (1 - .6 * dimQ), ls: 8 });
  // s1.2 highland
  const hA = on(t, 's1.2', 's1.2', .8, .5);
  if (hA > 0) { const pp = lp(t, 's1.2'); place(...PL.changzhi, '今长治', { a: hA, size: 28, color: C.note, fam: HEI, w: 500 }); place(...PL.jincheng, '今晋城', { a: hA, size: 28, color: C.note, fam: HEI, w: 500 });
    const k = seg(pp, .5, .95); arrow([[113.5, 36.35], [114.0, 36.5], [114.38, 36.58]], k, { color: C.gold, width: 14, a: hA * .9 }); arrow([[112.93, 35.62], [112.95, 35.38], [112.94, 35.16]], k, { color: C.gold, width: 14, a: hA * .9 }); arrow([[112.45, 35.75], [112.1, 35.55], [111.75, 35.35]], k, { color: C.gold, width: 14, a: hA * .9 });
    tag('今地形：长治盆地海拔约 900 米，邯郸约 60 米', 64, NOTE_Y, hA * seg(pp, .45, .6)); }
  // cities
  const cOn = seg(t, a('s1.3') + .5, a('s1.3') + 2.5), flip = seg(t, a('s1.12'), z('s1.12') + .4);
  cities(t, (i, c) => (flip * 19 - i > 1) ? C.zhao : C.han, (i) => clamp(cOn * 19 - i) * (1 - .55 * dimQ));
  const fl = fade(t, a('s1.12'), z('s1.12') + 1.2, .3, .6); if (fl > 0) wedge(fl, C.zhao, .07);
  const pA = on(t, 's1.3', 's1.3'); if (pA > 0) { const q = P(112.95, 36.42); plate(q[0], q[1], '上党守 冯亭', { side: 'n', a: pA, size: 32, sub: '韩' }); }
  tag('城市邑十七（位置示意）', 64, NOTE_Y, fade(t, a('s1.6'), z('s1.6'), .4, .4) + fade(t, a('s1.12'), z('s1.12') + 1, .4, .4));
  // s1.5 redirect the fire
  const f5 = on(t, 's1.5', 's1.5', .3, .5); if (f5 > 0) { const pp = lp(t, 's1.5'); arrow([[111.5, 35.2], [112.2, 35.5], [112.75, 35.75]], seg(pp, .05, .4), { color: C.qin, rim: C.qinRim, width: 24, a: f5 }); arrow([[113.2, 36.0], [113.85, 36.3], [114.36, 36.55]], seg(pp, .4, .8), { color: C.qin, rim: C.zhaoHi, width: 24, a: f5 }); }
  // quote cards
  quoteCard('「赵若受我，秦怒，必攻赵。\n赵被兵，必亲韩。\n韩赵为一，则可以当秦。」', '《史记·白起王翦列传》', onq(t, 's1.4'), { y: 440, size: 60, max: 13, p: lp(t, 's1.4') * 1.6, rows: 1 });
  const q7 = onq(t, 's1.7', 's1.8'); speaker('平阳君 赵豹', 410, q7); quoteCard('「圣人甚祸无故之利。」', '《史记·赵世家》', q7, { y: 500, size: 78, max: 11, p: lp(t, 's1.7') * 1.4, gloss: '白捡的好处，圣人看作大祸', });
  const q9 = onq(t, 's1.9', 's1.10');
  if (q9 > 0) { band(360, 1080, .93 * q9); speaker('平阳君 赵豹', 400, q9); rule(120, 960, 446, q9 * .8); const pp = seg(t, a('s1.9'), z('s1.9'));
    ['「秦以牛田之水通粮蚕食，', '上乘倍战者，裂上国之地，'].forEach((r, i) => txt(r, W / 2, 510 + i * 62, { size: 42, w: 600, color: C.goldDim, a: q9 * ease(seg(pp, .0 + i * .12, .2 + i * .12)) }));
    txt('其政行', W / 2, 720, { size: 170, w: 900, color: C.gold, a: q9 * ease(seg(pp, .45, .7)), ls: 16 }); txt('不可与为难。」', W / 2, 860, { size: 62, w: 700, color: C.gold, a: q9 * ease(seg(pp, .65, .9)) });
    txt('—— 《史记·赵世家》', W / 2, 940, { size: 30, fam: HEI, w: 500, color: C.goldDim, a: q9 }); txt('前半句历来解读不一；大意：耕战相济、步步蚕食，有功者分地', W / 2, 1000, { size: 26, fam: HEI, w: 400, color: C.note, a: q9 * .9 }); txt('政令通行，不可与之为敌', W / 2, 1040, { size: 26, fam: HEI, w: 400, color: C.note, a: q9 * .9 }); rule(120, 960, 1076, q9 * .8); }
  const q11 = onq(t, 's1.11'); speaker('平原君 赵胜', 410, q11); quoteCard('「发百万之军而攻，逾岁未得一城，\n今坐受城市邑十七，\n此大利，不可失也。」', '《史记·赵世家》', q11, { y: 500, size: 52, max: 16, p: lp(t, 's1.11') * 1.5, rows: 1 });
  // Feng Ting's tears
  const ft = fade(t, z('s1.12') + .2, a('s1.13') + 4.2, .4, .5); if (ft > 0) { band(1040, 1230, .7 * ft, 40); txt('冯亭垂涕不见使者：', W / 2, 1082, { size: 34, fam: HEI, w: 500, color: C.bone, a: ft }); txt('「卖主地而食之，不义三矣。」', W / 2, 1146, { size: 46, w: 700, color: C.gold, a: ft }); txt('——《史记·赵世家》', W / 2, 1204, { size: 26, fam: HEI, w: 500, color: C.goldDim, a: ft }); }
  // s1.13 the blade is Qin's
  const b13 = seg(t, a('s1.13') + 4.5, z('s1.13')); if (b13 > 0) arrow([[110.9, 35.15], [111.9, 35.2], [112.55, 35.55]], b13, { color: C.qin, rim: C.qinRim, width: 34, a: 1, glowC: 'rgba(90,140,190,.6)' });
  tag('形势示意 · 非精确疆界', 64, NOTE_Y, far * (1 - seg(t, a('s1.2'), a('s1.2') + .5)));
  dateTag('前262年', fade(t, a('s1.1'), this.b, .5, .4));
} });

/* ---- S2 一个夏天 ---- */
SC.push({ a: sceneStart('s2'), b: sceneStart('s3'), draw(t) {
  setCam(camKeys(t, [[a('s2.1'), [112.9, 35.72, 470]], [z('s2.1'), [112.9, 35.75, 520], x => x], [a('s2.2') + 2.8, V.battle], [z('s2.8'), [112.93, 35.82, 1620], x => x]]));
  const dimT = on(t, 's2.6', 's2.6', .5, .5);
  drawMap(.12, 1 - .6 * dimT);
  const near = sstep(900, 1500, cam.ppd);
  // s2.1 Qin takes Shangdang, people flee
  const p1 = lp(t, 's2.1'); const farA = 1 - near;
  if (farA > 0) { wedge(farA * .9, C.qinRim, .08); cities(t, (i) => (p1 * 26 - i > 1) ? '#1a2330' : C.zhao, () => farA); arrow([[112.25, 35.22], [112.55, 35.42], [112.8, 35.58]], seg(p1, .05, .45), { color: C.qin, rim: C.qinRim, width: 26, a: farA }); arrow([[112.05, 36.2], [112.45, 36.25], [112.8, 36.22]], seg(p1, .15, .55), { color: C.qin, rim: C.qinRim, width: 22, a: farA });
    const fc0 = F.blob([113.0, 36.15], .25, .3), fc1 = F.blob([113.25, 35.95], .12, .12); const pc = seg(p1, .5, 1.2);
    ctx.save(); for (let i = 0; i < civ.n; i++) { const g = civ.g[i]; const q0 = fc0(g), q1 = fc1(g); const e = eio(clamp(pc * 1.4 - g[3] * .4)); const [x, y] = P(lerp(q0[0], q1[0], e) + e * .25, lerp(q0[1], q1[1], e) + e * .08); ctx.globalAlpha = farA * .8 * seg(p1, .35, .5); ctx.fillStyle = '#d8d2c0'; ctx.beginPath(); ctx.arc(x, y, 2.2, 0, 7); ctx.fill(); } ctx.restore();
    tag('上党民走赵', 64, NOTE_Y, farA * seg(p1, .5, .65)); }
  // battlefield
  danHi(near * .9);
  const lineA = near * fade(t, a('s2.3'), z('s2.5'), .8, .8);
  dashLine([[112.735, 35.60], [112.735, 35.725], [112.74, 35.86]], { a: lineA * .7, color: C.note, width: 2.5 }); dashLine([[112.85, 35.985], [113.02, 36.0], [113.15, 35.975]], { a: lineA * .7, color: C.note, width: 2.5 });
  if (lineA > 0) { let q = P(112.735, 35.60); txt('空仓岭', q[0], q[1] + 26, { size: 26, fam: HEI, w: 500, color: C.note, a: lineA, stroke: 3 }); q = P(113.0, 36.0); txt('百里石长城', q[0], q[1] - 24, { size: 26, fam: HEI, w: 500, color: C.note, a: lineA, stroke: 3 }); }
  noteTag('防线位置据后世考证，说法不一', lineA);
  const zIn = seg(t, a('s2.2') + 1.6, a('s2.2') + 3.6), p3 = lp(t, 's2.3');
  const back = seg(p3, .4, .95);
  const fz = (g, i) => (g[2] < .32 ? mixF(fZfwd, fZline, back, .5)(g, i) : fZline(g, i));
  const wallA = near * seg(t, a('s2.4') + 1.5, a('s2.4') + 3.2);
  wall(ZW, { color: '#4a1a12', rim: C.zhaoHi, a: wallA, p: seg(t, a('s2.4') + 1.5, a('s2.4') + 3.4) });
  const zc = drawTroop(zAll, fz, { side: 'zhao', a: near * zIn, alive: 1 - .1 * back, t });
  const qIn = seg(t, a('s2.3'), a('s2.3') + 1.2);
  const qc = drawTroop(qMain, mixF(fQwest, fQline, seg(p3, .05, .9), .4), { side: 'qin', a: near * qIn });
  wall(QW, { a: near * seg(t, a('s2.4'), a('s2.4') + 1.5) * .9 });
  plate(zc[0] + 120, zc[1] - 30, '赵军 · 廉颇', { side: 'zhao', a: near * zIn }); plate(qc[0] - 60, qc[1] - 300, '秦军', { side: 'qin', a: near * qIn });
  place(...PL.cp, '长平', { a: near, size: 40, color: C.gold, dot: 7, sub: on(t, 's2.2') > 0 ? '今山西高平市一带' : '', dx: 16, dy: 60, align: 'center' });
  if (near > 0) { const q = P(112.975, 35.585); txt('丹河', q[0] + 34, q[1], { size: 30, w: 600, color: '#a9c8dc', a: near, stroke: 4 }); }
  // probes bounce off
  const pr = on(t, 's2.5', 's2.5', .3, .3); if (pr > 0) { const k = .5 - .5 * Math.cos(lp(t, 's2.5') * Math.PI * 6); [[35.88, 0], [35.80, .2], [35.72, .4]].forEach(([la, ph], i) => arrow([[112.80 + i * .008, la], [112.86 + i * .008, la], [112.918 + i * .012, la]], .35 + .65 * (.5 - .5 * Math.cos((lp(t, 's2.5') * 3 + ph) * Math.PI * 2)), { color: C.qin, rim: C.qinRim, width: 13, a: pr })); }
  termCard('壁 · 垒', '军营外面的土墙工事', on(t, 's2.4', 's2.4', .4, .4), { y: 1060 });
  // months
  const mo = t < a('s2.3') ? '' : p3 < .33 ? '四月' : p3 < .52 ? '六月' : '七月';
  dateTag('前260年' + (mo ? ' · ' + mo : ''), fade(t, a('s2.1'), this.b, .5, .4));
  // timeline graphic
  if (dimT > 0) { const x0 = 120, x1 = 960, y = 640; band(390, 1010, .9 * dimT); txt('时间', W / 2, 440, { size: 34, w: 700, color: C.goldDim, a: dimT, ls: 16 });
    const xs = [x0, x0 + 300, x0 + 600]; ctx.save(); ctx.globalAlpha = dimT; ctx.strokeStyle = C.bone; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x1, y); ctx.stroke(); ctx.restore();
    ['前262', '前261', '前260'].forEach((s, i) => { ctx.save(); ctx.globalAlpha = dimT; ctx.fillStyle = C.bone; ctx.fillRect(xs[i] - 1.5, y - 14, 3, 28); ctx.restore(); txt(s, xs[i] + (i === 0 ? 0 : 0), y + 50, { size: 34, w: 700, color: C.bone, a: dimT, align: i === 0 ? 'left' : 'center' }); });
    txt('赵受上党', x0, y - 44, { size: 30, fam: HEI, w: 500, color: C.han, a: dimT, align: 'left' });
    const pp = lp(t, 's2.6'); const sA = dimT * ease(seg(pp, .12, .3)); const sx0 = xs[2] + 60, sx1 = xs[2] + 185; ctx.save(); ctx.globalAlpha = sA; ctx.fillStyle = C.zhao; ctx.shadowColor = C.zhao; ctx.shadowBlur = 18; ctx.fillRect(sx0, y - 9, sx1 - sx0, 18); ctx.restore();
    txt('四月', sx0, y - 40, { size: 26, fam: HEI, w: 500, color: C.zhaoHi, a: sA }); txt('九月', sx1, y - 40, { size: 26, fam: HEI, w: 500, color: C.zhaoHi, a: sA });
    txt('长平对峙：一个夏天', W / 2, 800, { size: 54, w: 800, color: C.gold, a: sA });
    const bA = dimT * ease(seg(pp, .55, .72)); ctx.save(); ctx.globalAlpha = bA; ctx.strokeStyle = C.note; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(x0, y + 96); ctx.lineTo(x0, y + 112); ctx.lineTo(sx1, y + 112); ctx.lineTo(sx1, y + 96); ctx.stroke(); ctx.restore();
    txt('所谓“三年”：从接下上党算起', W / 2, 900, { size: 38, fam: HEI, w: 500, color: C.bone, a: bA });
    txt('月份据《史记·白起王翦列传》', W / 2, 962, { size: 26, fam: HEI, w: 400, color: C.note, a: dimT * .9 }); }
  // king's impatience + supply
  const k7 = on(t, 's2.7', 's2.7', .4, .4); if (k7 > 0) { band(400, 620, .7 * k7, 40); txt('「赵王数以为让」', W / 2, 470, { size: 62, w: 700, color: C.gold, a: k7 }); txt('多次责备廉颇 ——《史记·白起王翦列传》', W / 2, 556, { size: 28, fam: HEI, w: 500, color: C.goldDim, a: k7 }); }
  const s8 = near * fade(t, a('s2.8') + .8, this.b, .6, .3); dashLine(SUPPLY, { color: C.gold, a: s8 * .8, width: 3, dash: [4, 9] }); grainDots([...SUPPLY].reverse(), t, s8, 16, .09);
  if (s8 > 0) { const q = P(113.14, 36.03); txt('粮道（示意）', q[0] + 20, q[1] + 34, { size: 28, fam: HEI, w: 500, color: C.gold, a: s8, stroke: 3, align: 'left' }); band(400, 560, .6 * s8, 40); txt('数十万人 · 日日耗粮', W / 2, 480, { size: 56, w: 800, color: C.bone, a: s8 }); }
} });

/* ---- S3 换将 ---- */
SC.push({ a: sceneStart('s3'), b: sceneStart('s4'), draw(t) {
  setCam(camKeys(t, [[a('s3.1'), [111.6, 35.5, 160]], [z('s3.3'), [111.65, 35.52, 166], x => x], [a('s3.4') + 2.2, [112.95, 35.815, 1900]], [z('s3.6'), [112.95, 35.815, 1960], x => x], [a('s3.7') + 2, [112.80, 35.80, 2100]], [z('s3.9'), [112.80, 35.80, 2140], x => x], [a('s3.10') + 2, [112.89, 35.80, 1850]]]));
  const dimQ = Math.max(on(t, 's3.2'), on(t, 's3.5', 's3.6'), on(t, 's3.8'));
  drawMap(.15, 1 - .5 * dimQ);
  const near = sstep(900, 1500, cam.ppd), far = 1 - sstep(230, 400, cam.ppd);
  if (far > 0) { states(far, '秦赵'); place(...PL.xianyang, '咸阳', { a: far, size: 34, color: C.qinHi, align: 'center', dx: 0, dy: -40 }); place(...PL.handan, '邯郸', { a: far, size: 34, color: C.zhaoHi, align: 'center', dx: 0, dy: -40 }); place(...PL.cp, '长平', { a: far, size: 30, color: C.gold, dot: 6 });
    const path = [PL.xianyang, [110.6, 35.6], [112.6, 36.6], PL.handan]; const p1 = seg(t, a('s3.1') + .8, z('s3.1') + 1); dashLine(path, { color: C.gold, a: far * .7, width: 2.5, dash: [3, 9], p: p1 }); grainDots(path, t, far * seg(t, a('s3.1') + 1, a('s3.1') + 2), 12, .16, 1, C.gold);
    const q = P(110.7, 36.0); txt('千金 · 反间', q[0], q[1] - 40, { size: 40, w: 800, color: C.gold, a: far * p1, stroke: 4 }); const q2 = P(...PL.xianyang); plate(q2[0] + 40, q2[1] + 62, '应侯 范雎', { side: 'qin', a: far * seg(t, a('s3.1'), a('s3.1') + .6), size: 28, sub: '秦相' }); }
  quoteCard('「秦之所恶，独畏马服子赵括将耳，\n廉颇易与，且降矣。」', '《史记·白起王翦列传》', onq(t, 's3.2'), { y: 470, size: 54, max: 16, p: lp(t, 's3.2') * 1.5, rows: 1 });
  termCard('马服君', '赵括之父、名将赵奢的封号', on(t, 's3.3', 's3.3', .3, .4), { y: 1040 });
  // battlefield
  danHi(near * .9); wall(ZW, { color: '#4a1a12', rim: C.zhaoHi, a: near }); wall(QW, { a: near });
  const jit = 0;
  const zc = drawTroop(zAll, fZline, { side: 'zhao', a: near, alive: .9, t: t * 6, jit }); drawTroop(qMain, fQline, { side: 'qin', a: near });
  if (near > 0) { const sw = ease(seg(t, a('s3.4') + 2.2, a('s3.4') + 3.4)); const q = P(112.99, 35.80);
    plate(q[0] + 60 + sw * 60, q[1] - 40, '廉颇', { side: 'n', a: near * (1 - sw), size: 36 }); plate(q[0] + 60, q[1] - 40 + (1 - sw) * 30, '赵括', { side: 'zhao', a: near * sw * (1 - seg(t, a('s3.7'), a('s3.7') + 1)), size: 40, sub: '马服子' });
    const nA = near * fade(t, a('s3.4') + 3, z('s3.4') + 1.2, .4, .4); if (nA > 0) { band(1040, 1230, .72 * nA, 40); txt('「七月，廉颇免而赵括代将。」', W / 2, 1090, { size: 46, w: 700, color: C.gold, a: nA }); txt('——《史记·赵世家》', W / 2, 1150, { size: 26, fam: HEI, w: 500, color: C.goldDim, a: nA }); txt('通行本作“七年”，此据校勘本作“七月”', W / 2, 1200, { size: 26, fam: HEI, w: 400, color: C.note, a: nA }); }
    // Qin side
    const q8 = seg(t, a('s3.7') + 1.6, a('s3.7') + 3), qo = fade(t, a('s3.7') + 1, a('s3.10') + 1.5, .5, .6); const qq = P(112.74, 35.80);
    plate(qq[0] + 10, qq[1] + 120, '王龁', { side: 'qin', a: near * qo * (1 - .55 * q8), size: 30, sub: q8 > .5 ? '改任裨将' : '左庶长' });
    plate(qq[0] + 10, qq[1] - 40, q8 < .5 ? '上将军 ？' : '白起', { side: 'qin', a: near * qo * (q8 < .5 ? 1 - q8 * 2 : q8 * 2 - 1), size: 44, sub: q8 < .5 ? '' : '武安君 · 上将军' });
    const dA = near * fade(t, a('s3.7') + .5, z('s3.9'), .8, .5); if (dA > 0) { const g = ctx.createLinearGradient(0, 0, W, 0); g.addColorStop(0, `rgba(3,4,6,${.0})`); g.addColorStop(1, `rgba(3,4,6,${.0})`); }
    const e11 = on(t, 's3.10', 's3.10', .5, .4); if (e11 > 0) { const g = ctx.createLinearGradient(0, 0, W, 0); g.addColorStop(0, `rgba(2,3,5,${.62 * e11})`); g.addColorStop(.48, `rgba(2,3,5,${.5 * e11})`); g.addColorStop(.62, 'rgba(2,3,5,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); const qa = P(112.79, 35.80), za = P(112.975, 35.80); txt('严令保密', qa[0], qa[1] - 250, { size: 54, w: 800, color: C.qinHi, a: e11 }); txt('大张旗鼓', za[0] + 20, za[1] - 250, { size: 54, w: 800, color: C.zhaoHi, a: e11 }); plate(qa[0], qa[1] - 170, '白起', { side: 'qin', a: e11, size: 34 }); plate(za[0] + 20, za[1] - 170, '赵括', { side: 'zhao', a: e11, size: 34 }); }
  }
  // father and son
  const c5 = on(t, 's3.5', 's3.6', .4, .4);
  if (c5 > 0) { band(350, 1250, .8 * c5, 40); txt('赵括之母上书', W / 2, 398, { size: 36, w: 700, color: C.goldDim, a: c5, ls: 10 }); rule(120, 960, 440, c5 * .8);
    const pa = c5 * ease(seg(t, a('s3.5') + 1.8, a('s3.5') + 2.6)); txt('父 · 赵奢', 150, 510, { size: 44, w: 800, color: C.bone, align: 'left', a: pa }); ['「大王及宗室所赏赐者，', '尽以予军吏士大夫；', '受命之日，不问家事。」'].forEach((r, i) => txt(r, 150, 590 + i * 70, { size: 50, w: 700, color: C.gold, align: 'left', a: pa }));
    const pb = c5 * ease(seg(t, a('s3.6'), a('s3.6') + .8)); rule(150, 930, 800, pb * .5, C.goldDim, 1); txt('子 · 赵括', 150, 860, { size: 44, w: 800, color: C.zhaoHi, align: 'left', a: pb }); ['「王所赐金帛，归藏于家，', '而日视便利田宅', '可买者买之。」'].forEach((r, i) => txt(r, 150, 940 + i * 70, { size: 50, w: 700, color: C.gold, align: 'left', a: pb }));
    txt('——《史记·廉颇蔺相如列传》', W / 2, 1180, { size: 28, fam: HEI, w: 500, color: C.goldDim, a: c5 }); rule(120, 960, 1226, c5 * .8); }
  quoteCard('「军中有敢泄\n武安君将者斩。」', '《史记·白起王翦列传》', onq(t, 's3.8', 's3.9'), { y: 880, size: 76, max: 11, p: lp(t, 's3.8') * 1.4, rows: 1 });
  dateTag('前260年 · 七月', fade(t, a('s3.4') + 2, this.b, .5, .4));
} });

/* ---- S4 截成两段 ---- */
function battleS4(t, o = {}) { // returns state; shared with later scenes
  const p2 = lp(t, 's4.2'), p3 = lp(t, 's4.3'), p4 = lp(t, 's4.4'), p5 = lp(t, 's4.5'), p8 = lp(t, 's4.8');
  const surge = seg(t, a('s4.1') + (z('s4.1') - a('s4.1')) * .35, a('s4.1') + (z('s4.1') - a('s4.1')) * .35 + 2.2);
  const adv = seg(p3, .0, .55);
  // attackers: line -> cross river -> at Qin wall ; camp group: line -> camp
  const fA = mixF(mixF(fZline, F.band([[112.895, 35.92], [112.915, 35.81], [112.94, 35.70]], .012), surge, .3), fZatk, adv, .5);
  const fAr = mixF(fA, fZatkRing, seg(p8, .2, .8), .3);
  const fCg = mixF(fZline, fZcamp, seg(t, a('s4.1') + .5, a('s4.3')), .4);
  return { p2, p3, p4, p5, p8, fAr, fCg, adv };
}
SC.push({ a: sceneStart('s4'), b: sceneStart('s5'), draw(t) {
  setCam(camKeys(t, [[a('s4.1'), [112.89, 35.80, 1850]], [a('s4.2'), [112.875, 35.81, 2000]], [z('s4.8'), [112.88, 35.815, 2050], x => x], [z('s4.9') - .5, [112.93, 35.76, 1150]]]));
  const dimQ = onq(t, 's4.6');
  drawMap(.2, 1 - .5 * dimQ);
  const S = battleS4(t); danHi(.9); const pl = 1 - dimQ;
  // supply line
  const cut = seg(S.p4, .85, 1);
  dashLine(SUPPLY, { color: cut > .5 ? '#5a5346' : C.gold, a: .8 * (1 - .4 * cut), width: 3, dash: [4, 9] }); grainDots([...SUPPLY].reverse(), t, 1 - cut, 16, .09);
  { const q = P(113.10, 36.01); txt(cut > .5 ? '粮道 · 绝' : '粮道', Math.min(q[0] + 26, 1040), q[1] + 34, { size: 30, fam: HEI, w: 600, color: cut > .5 ? '#ffb39c' : C.gold, a: 1, stroke: 4, align: q[0] + 26 > 900 ? 'right' : 'left' }); cross(113.045, 35.955, cut * (.6 + .4 * Math.sin(t * 5) ** 2), 18); }
  // walls
  const flash = on(t, 's4.3') * seg(S.p3, .5, .6) * (.5 + .5 * Math.sin(t * 9));
  wall(QW, { rim: flash > .3 ? '#ffffff' : C.qinRim, width: 11 + 4 * flash });
  wall(ZW, { color: '#4a1a12', rim: C.zhaoHi, a: 1 - seg(t, a('s4.3'), z('s4.3')) * .6 });
  // Zhao wall around the forward group (s4.8)
  if (S.p8 > .15) { const k = seg(S.p8, .25, .9); const ring = []; for (let i = 0; i <= 24; i++) { const an = i / 24 * 6.2832 * k - 1.57; ring.push([112.855 + Math.cos(an) * .047, 35.80 + Math.sin(an) * .074]); } if (ring.length > 3) wall(ring, { color: '#4a1a12', rim: C.zhaoHi, width: 8 }); }
  { const ring = []; for (let i = 0; i <= 20; i++) { const an = i / 20 * 6.2832; ring.push([ZCAMP[0] + Math.cos(an) * .048, ZCAMP[1] + Math.sin(an) * .055]); } wall(ring, { color: '#4a1a12', rim: C.zhaoHi, width: 7, a: seg(t, a('s4.2'), a('s4.3')) * .9 }); }
  // Qin feint
  drawTroop(qMain, fQline, { side: 'qin' });
  const fb = mixF(fQfront, fQback, seg(S.p2, .25, .9), .4);
  const qfIn = seg(t, a('s4.1') + .3, a('s4.1') + 1.4);
  drawTroop(qF, t < a('s4.2') ? mixF(fQback, fQfront, qfIn, .4) : fb, { side: 'qin' });
  const f2 = on(t, 's4.2', 's4.2', .2, .5) * seg(S.p2, .2, .35); arrow([[112.875, 35.775], [112.84, 35.772], [112.80, 35.775]], seg(S.p2, .25, .8), { color: C.qin, rim: C.qinRim, width: 18, a: f2 }); if (f2 > 0) { const q = P(112.845, 35.752); txt('佯败', q[0], q[1], { size: 40, w: 800, color: C.qinHi, a: f2, stroke: 5 }); }
  // Zhao
  const ac = drawTroop(zA, S.fAr, { side: 'zhao', t }); const cc = drawTroop(zC, S.fCg, { side: 'zhao' });
  const f3 = on(t, 's4.3', 's4.3', .2, .5); arrow([[112.93, 35.84], [112.89, 35.835], [112.855, 35.835]], S.adv, { color: C.zhao, rim: C.zhaoHi, width: 20, a: f3 * (1 - seg(S.p3, .7, .9)) });
  if (flash > 0) { const q = P(112.80, 35.80); txt('壁坚拒不得入', q[0] - 4, q[1] - 268, { size: 38, w: 800, color: C.qinHi, a: on(t, 's4.3') * seg(S.p3, .5, .6), stroke: 5 }); }
  // 25,000
  const a25 = seg(t, a('s4.4'), a('s4.4') + .4); const d25 = spline(R25, 14);
  const m25 = seg(S.p4, .08, .9);
  const hd = arrow(R25, m25, { color: C.qin, rim: C.qinRim, width: 24, a: a25 * (1 - .65 * seg(t, z('s4.5'), z('s4.5') + 1)), glowC: 'rgba(120,170,220,.5)' });
  drawTroop(q25, (g, i) => { const hp = clamp(m25 * 1.18 - g[2] * .18); const q = along(d25, hp); const e = fQ25end(g); const k = seg(m25, .9, 1) * 1; return [lerp(q[0] + g[0] * .004, e[0], eio(clamp(k * 1.5 - g[3] * .5))), lerp(q[1] + g[1] * .004, e[1], eio(clamp(k * 1.5 - g[3] * .5)))]; }, { side: 'qin', a: a25 });
  if (a25 > 0) { const q = m25 < 1 && hd ? hd : P(113.05, 35.94); plate(clamp(q[0] + (m25 < .98 ? 0 : 70), 170, 900), q[1] - 56, '奇兵 二万五千', { side: 'qin', a: a25 * pl, size: 30 }); }
  // 5,000 cavalry
  const a5 = seg(t, a('s4.5'), a('s4.5') + .4); const d5 = spline(R5, 14); const m5 = seg(S.p5, .08, .85);
  const hd5 = arrow(R5, m5, { color: C.qin, rim: C.qinRim, width: 20, a: a5 * (1 - .65 * seg(t, z('s4.5'), z('s4.5') + 1)), glowC: 'rgba(120,170,220,.5)' });
  drawTroop(q5, (g) => { const hp = clamp(m5 * 1.15 - g[2] * .15); const q = along(d5, hp); const e = fQ5end(g); const k = eio(clamp(seg(m5, .9, 1) * 1.5 - g[3] * .5)); return [lerp(q[0] + g[0] * .003, e[0], k), lerp(q[1] + g[1] * .003, e[1], k)]; }, { side: 'qin', a: a5 });
  if (a5 > 0) { const q = m5 < 1 && hd5 ? hd5 : P(112.93, 35.90); plate(q[0] + 96, q[1] + (m5 < .98 ? 40 : -30), '骑兵 五千', { side: 'qin', a: a5 * pl, size: 30 }); }
  // the cut
  const cA = seg(t, z('s4.5') - .5, a('s4.6') + .5);
  if (cA > 0) { ctx.save(); ctx.globalAlpha = cA * (.6 + .2 * Math.sin(t * 4)) * (1 - .6 * seg(t, a('s4.8'), a('s4.8') + 1)); ctx.strokeStyle = '#eaf4ff'; ctx.lineWidth = 3; ctx.shadowColor = '#8fc0ff'; ctx.shadowBlur = 18; poly(spline([[112.908, 35.70], [112.925, 35.80], [112.928, 35.90]], 12)); ctx.stroke(); ctx.restore();
    plate(ac[0] - 6, ac[1] - 236 * cam.ppd / 2000, '赵军主力', { side: 'zhao', a: cA * pl, size: 30 }); plate(cc[0] + 30, cc[1] + 150 * cam.ppd / 2000, '赵壁', { side: 'zhao', a: cA * pl, size: 30 }); }
  else { plate(cc[0] + 40, cc[1] - 130, '赵括', { side: 'zhao', a: 1 - seg(t, a('s4.3'), a('s4.3') + 1), size: 34 }); }
  plate(P(112.73, 35.80)[0], P(112.73, 35.80)[1] - 60, '秦壁', { side: 'qin', a: seg(t, a('s4.2'), a('s4.2') + 1) * pl, size: 30 });
  // harass
  const h8 = on(t, 's4.8', 's4.8', .4, .4) * seg(S.p8, .0, .2); if (h8 > 0) { const k = .5 - .5 * Math.cos(lp(t, 's4.8') * Math.PI * 4); arrow([[112.80, 35.86], [112.82, 35.855], [112.835, 35.85]], k, { color: C.qin, rim: C.qinRim, width: 10, a: h8 }); arrow([[112.90, 35.74], [112.885, 35.75], [112.87, 35.76]], k, { color: C.qin, rim: C.qinRim, width: 10, a: h8 }); band(1050, 1210, .7 * h8, 40); txt('「筑壁坚守，以待救至」', W / 2, 1100, { size: 56, w: 700, color: C.gold, a: h8 }); txt('——《史记·白起王翦列传》', W / 2, 1168, { size: 26, fam: HEI, w: 500, color: C.goldDim, a: h8 }); }
  quoteCard('「赵军分而为二，\n粮道绝。」', '《史记·白起王翦列传》', dimQ, { y: 420, size: 84, max: 11, p: lp(t, 's4.6') * 1.4, rows: 1 });
  const c7 = fade(t, a('s4.1') + .3, a('s4.1') + (z('s4.1') - a('s4.1')) * .5, .3, .4); if (c7 > 0) { band(1050, 1210, .8 * c7, 40); txt('「悉更约束，易置军吏」', W / 2, 1100, { size: 56, w: 700, color: C.gold, a: c7 }); txt('——《史记·廉颇蔺相如列传》', W / 2, 1170, { size: 26, fam: HEI, w: 500, color: C.goldDim, a: c7 }); }
  // steps
  const step = t < a('s4.3') ? 0 : t < a('s4.4') ? 1 : t < a('s4.5') ? 2 : 3;
  stepChips(t, step, fade(t, a('s4.2') - .3, z('s4.5') + .3, .4, .4));
  // closing question
  const q9 = on(t, 's4.9', 's4.9', .6, .3) * seg(lp(t, 's4.9'), .35, .5);
  if (q9 > 0) { arrow([[113.34, 36.17], [113.24, 36.11], [113.15, 36.05]], 1, { color: C.zhao, rim: C.zhaoHi, width: 22, a: q9 * (.55 + .45 * Math.sin(t * 3) ** 2) }); arrow([[112.87, 35.50], [112.87, 35.56], [112.875, 35.625]], 1, { color: C.qin, rim: C.qinRim, width: 22, a: q9 * (.55 + .45 * Math.cos(t * 3) ** 2) }); let q = P(113.20, 36.17); txt('赵：援兵和粮？', q[0], q[1] - 30, { size: 40, w: 800, color: C.zhaoHi, a: q9, stroke: 6 }); q = P(112.87, 35.53); txt('秦：人和粮？', q[0] + 180, q[1], { size: 40, w: 800, color: C.qinHi, a: q9, stroke: 6 }); }
  noteTag('行军路线为示意；地点据后世考证，说法不一', fade(t, a('s4.2'), a('s4.9'), .5, .4) * (1 - on(t, 's4.8')));
  dateTag('前260年 · 七月以后', fade(t, a('s4.1'), this.b, .5, .4));
} });

/* trapped state reused by S5/S7/S8 */
function trapped(t, o = {}) { const { dim = 0, alive = 1, a_ = 1, side = 'zhao' } = o; const A1 = drawTroop(zA, fZatkRing, { side, t, dim, alive, a: a_ }); const C1 = drawTroop(zC, fZcamp, { side, dim, alive, a: a_ }); return [A1, C1]; }
function qinRings(t, a_ = 1, extra = 0) { drawTroop(qMain, fQline, { side: 'qin', a: a_ }); drawTroop(qF, fQback, { side: 'qin', a: a_ }); drawTroop(q25, fQ25end, { side: 'qin', a: a_ }); drawTroop(q5, fQ5end, { side: 'qin', a: a_ }); if (extra > 0) drawTroop(qRing, F.ell([112.925, 35.815], .168, .128, .14), { side: 'qin', a: a_ * extra, r: 2.6 }); }
function rings(a_ = 1) { const mk = (c, rx, ry) => { const r = []; for (let i = 0; i <= 24; i++) { const an = i / 24 * 6.2832; r.push([c[0] + Math.cos(an) * rx, c[1] + Math.sin(an) * ry]); } return r; }; wall(mk([112.855, 35.80], .047, .074), { color: '#4a1a12', rim: C.zhaoHi, width: 8, a: a_ }); wall(mk(ZCAMP, .048, .055), { color: '#4a1a12', rim: C.zhaoHi, width: 7, a: a_ }); wall(QW, { a: a_ }); }

/* ---- S5 秦国的那一个动作 ---- */
const ROUTE = [[112.93, 35.10], [112.87, 35.30], [112.85, 35.50], [112.89, 35.66]];
const ARC = [[112.60, 35.96], [112.82, 36.12], [113.10, 36.10], [113.30, 35.94], [113.36, 35.72]];
SC.push({ a: sceneStart('s5'), b: sceneStart('s6'), draw(t) {
  setCam(camKeys(t, [[a('s5.1') - .7, [112.93, 35.86, 1250]], [z('s5.1') + .8, V.henei], [z('s5.6'), [113.0, 35.49, 660], x => x]]));
  const diag = fade(t, a('s5.7') + .8, this.b + .5, .7, .1);
  const dimQ = Math.max(on(t, 's5.2', 's5.2', .4, .5) * .35, diag * .82);
  drawMap(.28, 1 - Math.max(dimQ, on(t, 's5.2') * .55));
  const mid = 1 - sstep(900, 1200, cam.ppd);
  // trapped Zhao + Qin lines (small at this scale)
  drawTroop(qMain, fQline, { side: 'qin', r: 2.4 }); drawTroop(q25, fQ25end, { side: 'qin', r: 2.4 }); drawTroop(q5, fQ5end, { side: 'qin', r: 2.4 }); drawTroop(zA, fZatkRing, { side: 'zhao', r: 2.6 }); drawTroop(zC, fZcamp, { side: 'zhao', r: 2.6 });
  place(...PL.cp, '长平', { a: mid, size: 36, color: C.gold, dot: 0, dx: 0, dy: -78, align: 'center' });
  // Henei
  const hA = mid * seg(t, z('s5.1'), z('s5.1') + 1.2);
  if (hA > 0) { const d = spline([...HENEI, HENEI[0], HENEI[1]], 10).slice(0, -10); ctx.save(); poly(d, true); ctx.globalAlpha = hA * (.16 + .08 * on(t, 's5.3')); ctx.fillStyle = C.qinRim; ctx.fill(); ctx.globalAlpha = hA * .8; ctx.strokeStyle = C.qinRim; ctx.lineWidth = 2.5; ctx.setLineDash([9, 7]); ctx.stroke(); ctx.restore();
    const q = P(113.55, 35.22); txt('河内', q[0], q[1] + 6, { size: 74, w: 900, color: C.qinHi, a: hA, ls: 10, stroke: 5 }); place(...PL.yewang, '野王', { a: hA, size: 30, color: C.bone, sub: '今沁阳', align: 'right', dx: 14 });
    const y = P(112.25, 34.93); txt('黄河', y[0] + 10, y[1] + 44, { size: 30, w: 600, color: '#a9c8dc', a: hA, stroke: 4 }); const th = P(113.42, 35.62); txt('太 行', th[0], th[1], { size: 34, w: 600, color: C.note, a: hA * .9, stroke: 4, ls: 8 });
    const dA = on(t, 's5.3', 's5.3', .5, .4); if (dA > 0) { dashLine([PL.yewang, [112.90, 35.45], PL.cp], { color: C.bone, a: dA * .8, width: 2, dash: [5, 8], smooth: false }); const m = P(112.915, 35.45); tag('直线约 80 公里（今沁阳—高平）', m[0] + 22, m[1], dA); } }
  // the king arrives; people; ranks; march
  const p5 = lp(t, 's5.5'), p6 = lp(t, 's5.6');
  const kingA = mid * fade(t, a('s5.5') + 1, z('s5.6'), .5, .6); if (kingA > 0) { const k = eout(seg(p5, .1, .3)); const q = P(lerp(111.9, 112.72, k), lerp(34.72, 35.03, k)); plate(q[0], q[1] + 44, '秦昭王', { side: 'qin', a: kingA, size: 34, sub: '王自之河内' }); }
  const pop = seg(t, a('s5.5') + 2.2, a('s5.5') + 4.2); const fH = F.blob([113.18, 35.14], .30, .055, .26);
  const mTot = seg(t, a('s5.5') + lerp(0, z('s5.5') - a('s5.5'), .62), z('s5.6') - .6);
  const dR = spline(ROUTE, 12), dArc = spline(ARC, 14);
  const fMarch = (g, i) => { const h = fH(g); const lag = g[3] * .35; const m = clamp((mTot * 1.35 - lag)); if (m <= 0) return h; const k1 = clamp(m / .12), k2 = clamp((m - .12) / .5), k3 = clamp((m - .62) / .38); const r0 = along(dR, 0), r = along(dR, k2); const e = along(dArc, g[2]); const ex = e[0] + g[0] * .012, ey = e[1] + g[1] * .010; let x = lerp(h[0], r0[0] + g[0] * .015, eio(k1)), y = lerp(h[1], r0[1] + g[1] * .008, eio(k1)); if (k2 > 0) { x = r[0] + g[0] * .014; y = r[1] + g[1] * .010; } if (k3 > 0) { x = lerp(x, ex, eio(k3)); y = lerp(y, ey, eio(k3)); } return [x, y]; };
  if (pop > 0 && mid > 0) { ctx.save(); for (let i = 0; i < hn.n; i++) { const g = hn.g[i]; const ap = clamp(pop * 1.6 - (g[2] * .6)); if (ap <= 0) continue; const [lo, la] = fMarch(g, i); const [x, y] = P(lo, la); ctx.globalAlpha = mid * ap; ctx.fillStyle = C.qinRim; ctx.beginPath(); ctx.arc(x, y, 3.3, 0, 7); ctx.fill(); ctx.fillStyle = C.qin; ctx.beginPath(); ctx.arc(x, y, 2.1, 0, 7); ctx.fill();
      // rank mark sweep (赐民爵各一级)
      const sweep = seg(p5, .34, .58) * 1.3 - g[2] * .9; if (sweep > 0 && sweep < .5 && mTot < .05) { ctx.globalAlpha = mid * (1 - sweep * 2); ctx.strokeStyle = C.gold; ctx.lineWidth = 2.2; ctx.beginPath(); ctx.moveTo(x - 5, y - 8 - sweep * 14); ctx.lineTo(x, y - 14 - sweep * 14); ctx.lineTo(x + 5, y - 8 - sweep * 14); ctx.stroke(); } } ctx.restore(); }
  const rk = mid * fade(t, a('s5.5') + lerp(0, z('s5.5') - a('s5.5'), .34), a('s5.5') + lerp(0, z('s5.5') - a('s5.5'), .66), .3, .4); if (rk > 0) { const q = P(113.2, 35.02); txt('爵 +一级', q[0], q[1] + 40, { size: 44, w: 800, color: C.gold, a: rk, stroke: 5 }); }
  const mk = mid * fade(t, a('s5.5') + lerp(0, z('s5.5') - a('s5.5'), .66), z('s5.6') + 1.5, .4, .6); if (mk > 0) { const q = P(112.62, 35.40); txt('年十五以上', q[0] - 10, q[1], { size: 38, w: 800, color: C.qinHi, a: mk, stroke: 5 }); txt('悉诣长平', q[0] - 10, q[1] + 50, { size: 38, w: 800, color: C.qinHi, a: mk, stroke: 5 }); }
  // blocked relief
  const bl = mid * fade(t, a('s5.6') - .2, a('s5.7') + 1.2, .5, .6); if (bl > 0) { const k = lp(t, 's5.6'); arrow([[114.25, 36.52], [113.9, 36.38], [113.42, 36.12]], seg(k, .0, .55) * .93, { color: C.zhao, rim: C.zhaoHi, width: 22, a: bl }); grainDots([[114.3, 36.3], [113.9, 36.12], [113.45, 35.92]], t, bl, 9, .12, .9, C.gold); const q = P(113.95, 36.5); txt('赵救 · 粮食', q[0] - 30, q[1] - 46, { size: 34, w: 800, color: C.zhaoHi, a: bl, stroke: 5 }); const q2 = P(113.33, 36.18); txt('遮绝', q2[0] - 96, q2[1] - 22, { size: 54, w: 900, color: C.qinHi, a: bl * seg(k, .5, .7), stroke: 6 }); }
  // the sentence
  const qa = onq(t, 's5.2');
  if (qa > 0) { const rows = ['「秦王闻赵食道绝，', '王自之河内，', '赐民爵各一级，', '发年十五以上悉诣长平，', '遮绝赵救及粮食。」']; const pp = lp(t, 's5.2'); band(330, 830, .8 * qa); rule(120, 960, 372, qa * .8); const cuts = [0, .2, .36, .52, .78, 1];
    rows.forEach((r, i) => txt(r, W / 2, 440 + i * 78, { size: 58, w: 700, color: C.gold, a: qa * ease(seg(pp, cuts[i] - .03, cuts[i] + .07)) })); txt('——《史记·白起王翦列传》', W / 2, 840 - 20, { size: 28, fam: HEI, w: 500, color: C.goldDim, a: qa }); rule(120, 960, 862, qa * .8); }
  termCard('河内', '黄河以北，今河南焦作、沁阳一带；秦国离长平最近的后方', on(t, 's5.3', 's5.3', .4, .4), { y: 330 });
  const jA = on(t, 's5.4', 's5.4', .4, .4);
  if (jA > 0) { shade(.55 * jA); termCard('爵', '秦国的军功等级\n有爵，就有田宅和身份', jA, { y: 330, sub: '赐爵见《史记》；《资治通鉴》卷五记同一事，未载赐爵' });
    const names = ['公士', '上造', '簪袅', '不更']; const base = 960; names.forEach((n, i) => { const x = 130 + i * 210, h = 120 + i * 62, ka = jA * ease(seg(lp(t, 's5.4'), .06 + i * .07, .16 + i * .07)); ctx.save(); ctx.globalAlpha = ka; ctx.fillStyle = 'rgba(14,17,21,.96)'; ctx.fillRect(x, base - h, 196, h); ctx.fillStyle = C.gold; ctx.fillRect(x, base - h, 196, 6); ctx.restore(); txt('一二三四'[i] + '级', x + 98, base - h + 40, { size: 28, fam: HEI, w: 500, color: C.note, a: ka, shadow: 0 }); txt(n, x + 98, base - h + 88, { size: 46, w: 800, color: C.bone, a: ka, shadow: 0 }); });
    txt('…… 共二十级', 130, base + 44, { size: 32, fam: HEI, w: 500, color: C.bone, a: jA, align: 'left', shadow: 0 }); txt('爵名据《汉书·百官公卿表》', 950, base + 44, { size: 24, fam: HEI, w: 400, color: C.note, a: jA, align: 'right', shadow: 0 }); }
  // four questions diagram
  if (diag > 0) { shade(.9 * diag); const B = [['户籍', '人人登记在册', 's5.8'], ['县', '官府直接管到每一户', 's5.11'], ['爵', '军功换田宅、身份', 's5.9'], ['兵', '年十五以上，悉诣长平', 's5.12']]; const y0 = 520, dy = 178, x = 150, bw = 250, bh = 126;
    txt('一道命令，靠什么落地', W / 2, 400, { size: 44, w: 800, color: C.goldDim, a: diag * (1 - on(t, 's5.12', 's5.13', .5, .3)), ls: 4 });
    const lit = id => ease(seg(t, a(id) + (id === 's5.12' ? 3.2 : (z(id) - a(id)) * .52), a(id) + (id === 's5.12' ? 4 : (z(id) - a(id)) * .52 + .6)));
    const chain = ease(seg(t, a('s5.12'), a('s5.12') + 3));
    ctx.save(); ctx.globalAlpha = diag; ctx.strokeStyle = C.goldDim; ctx.lineWidth = 2; ctx.setLineDash([4, 6]); ctx.beginPath(); ctx.moveTo(x + bw / 2, y0 + bh); ctx.lineTo(x + bw / 2, y0 + 3 * dy); ctx.stroke(); ctx.setLineDash([]); ctx.strokeStyle = C.gold; ctx.lineWidth = 6; ctx.shadowColor = C.gold; ctx.shadowBlur = 16; ctx.beginPath(); ctx.moveTo(x + bw / 2, y0 + bh / 2); ctx.lineTo(x + bw / 2, y0 + bh / 2 + chain * 3 * dy); ctx.stroke(); ctx.restore();
    B.forEach((b, i) => { const L = Math.max(lit(b[2]), i < 3 ? seg(chain * 3, i, i + .4) : 0); const y = y0 + i * dy; ctx.save(); ctx.globalAlpha = diag; ctx.fillStyle = L > .5 ? 'rgba(227,201,138,.96)' : 'rgba(10,12,15,.95)'; ctx.shadowColor = L > .5 ? C.gold : 'transparent'; ctx.shadowBlur = 24 * L; ctx.fillRect(x, y, bw, bh); ctx.shadowBlur = 0; ctx.strokeStyle = C.goldDim; ctx.lineWidth = 2; ctx.strokeRect(x, y, bw, bh); ctx.restore();
      txt(b[0], x + bw / 2, y + bh / 2 + 2, { size: 76, w: 900, color: L > .5 ? '#14110a' : C.goldDim, a: diag, shadow: 0, ls: b[0].length > 1 ? 6 : 0 }); txt(b[1], x + bw + 40, y + bh / 2 - (i === 2 ? 22 : 0), { size: 38, fam: HEI, w: 500, color: C.bone, a: diag * (.25 + .75 * L), align: 'left', shadow: 0 });
      if (i === 2) { const la = ease(seg(t, a('s5.10') + (z('s5.10') - a('s5.10')) * .7, z('s5.10'))); txt('不去，有法', x + bw + 40, y + bh / 2 + 30, { size: 38, fam: HEI, w: 500, color: '#ffb39c', a: diag * la, align: 'left', shadow: 0 }); } });
    const zx = on(t, 's5.12', 's5.12', .4, .4) * seg(lp(t, 's5.12'), .62, .78); txt('其政行', W / 2, 400, { size: 110, w: 900, color: C.gold, a: diag * zx, ls: 16 });
    txt('户籍、县制、军功爵为战国秦制通识；此处是解读，非本条原文', 64, NOTE_Y, { size: 24, fam: HEI, w: 400, color: C.note, a: diag * (1 - on(t, 's5.13', 's5.13', .4, .1)), align: 'left', shadow: 0 });
    const e13 = on(t, 's5.13', 's5.13', .4, .3); if (e13 > 0) { const k = lp(t, 's5.13'); shade(.97 * e13, 280, 1340); const a1 = e13 * ease(seg(k, 0, .15)), a2 = e13 * ease(seg(k, .45, .62)); txt('赵国有', W / 2, 520, { size: 56, w: 600, color: C.bone, a: a1, ls: 8 }); txt('名将', W / 2, 670, { size: 190, w: 900, color: C.zhaoHi, a: a1, ls: 20 }); rule(300, 780, 810, e13 * .7); txt('秦国有', W / 2, 900, { size: 56, w: 600, color: C.bone, a: a2, ls: 8 }); txt('一部机器', W / 2, 1050, { size: 190, w: 900, color: C.qinHi, a: a2, ls: 8 }); } }
  dateTag('前260年 · 秋', fade(t, a('s5.1'), a('s5.7'), .5, .4));
} });

/* ---- S6 门关上了 ---- */
SC.push({ a: sceneStart('s6'), b: sceneStart('s7'), draw(t) {
  setCam(camKeys(t, [[a('s6.1'), [113.8, 35.6, 98]], [z('s6.5'), [113.5, 35.6, 106], x => x]]));
  const dimQ = Math.max(on(t, 's6.2', 's6.4', .4, .4)) * .35; drawMap(.45, 1 - dimQ);
  states(1, '秦韩赵魏齐楚燕', { '魏': [115.75, 34.55], '韩': [112.55, 33.75], '楚': [113.6, 32.3] });
  glow(...PL.cp, .9 + .15 * Math.sin(t * 2.2), C.zhao, .55); place(...PL.cp, '长平', { size: 34, color: C.gold, dot: 7, align: 'right', dx: 16 });
  place(...PL.linzi, '临淄', { size: 28, color: C.qi, dy: 34, align: 'center', dx: 0 }); place(...PL.chen, '陈', { size: 28, color: C.chu, dy: 34, align: 'center', dx: 0 }); place(...PL.daliang, '大梁', { size: 28, color: C.wei, dy: 34, align: 'center', dx: 0 }); place(...PL.handan, '邯郸', { size: 28, color: C.zhaoHi, dy: -34, align: 'center', dx: 0 }); place(...PL.xianyang, '咸阳', { size: 28, color: C.qinHi, dy: 34, align: 'center', dx: 0 });
  // Zhao asks Qi for grain
  const p1 = lp(t, 's6.1'); dashLine([PL.handan, [116.3, 37.1], PL.linzi], { color: C.zhaoHi, a: fade(t, a('s6.1') + 1, z('s6.4'), .4, .6), width: 3, p: seg(p1, .3, .6) });
  { const q = P(116.3, 37.2); txt('请粟', q[0], q[1] - 34, { size: 36, w: 800, color: C.zhaoHi, a: fade(t, a('s6.1') + 1.5, z('s6.4'), .4, .6) * seg(p1, .4, .55), stroke: 5 }); }
  const dead = seg(t, a('s6.4'), z('s6.4') + .6);
  const AR = [['qi', [[117.9, 36.7], [116.6, 36.4], [115.3, 36.15]], C.qi, .52, a('s6.1') + (z('s6.1') - a('s6.1')) * .62, a('s6.4')], ['chu', [[114.8, 33.8], [114.5, 34.15], [114.2, 34.45], [113.7, 34.95]], C.chu, .78, a('s6.5'), a('s6.5') + 6.5, [-10, 56]], ['wei', [[114.5, 35.0], [114.2, 35.15], [113.9, 35.3], [113.45, 35.55]], C.wei, .78, a('s6.5') + .4, a('s6.5') + 7, [40, -44]]];
  AR.forEach(([k, pts, col, stop, t0, tOff, qo = [-44, -34]]) => { const grow = ease(seg(t, t0, t0 + 1.6)) * stop; const off = seg(t, tOff, tOff + 1.2); if (grow <= 0) return; const hd = arrow(pts, grow, { color: col, width: 20, a: 1 - .85 * off, rim: 'rgba(0,0,0,.6)' }); if (hd) txt('？', hd[0] + qo[0], hd[1] + qo[1], { size: 64, w: 900, color: C.bone, a: seg(t, t0 + 1.4, t0 + 2) * (1 - off), stroke: 6 }); });
  const st = seg(t, a('s6.1') + (z('s6.1') - a('s6.1')) * .72, a('s6.1') + (z('s6.1') - a('s6.1')) * .8) * (1 - seg(t, a('s6.2') - .3, a('s6.2'))); if (st > 0) { const q = P(117.2, 36.0); txt('齐王弗许', q[0], q[1] + 60, { size: 60, w: 900, color: C.gold, a: st, stroke: 6 }); }
  const q2 = on(t, 's6.2', 's6.3', .3, .4); if (q2 > 0) { speaker('齐 · 周子', 372, q2); const two = t >= a('s6.3') - .2; const k = ease(seg(t, a('s6.3') - .4, a('s6.3') + .2));
    quoteCard('「夫赵之于齐、楚，扞蔽也，\n犹齿之有唇也，唇亡则齿寒；\n今日亡赵，明日患及齐、楚矣。」', '', q2 * (1 - k), { y: 460, size: 50, max: 16, p: lp(t, 's6.2') * 1.4, rows: 1, note: '扞蔽：屏障 ——《资治通鉴》卷五' });
    quoteCard('「救赵之务，\n宜若奉漏瓮沃焦釜然。」', '《资治通鉴》卷五', q2 * k, { y: 460, size: 64, max: 14, p: lp(t, 's6.3') * 1.6, rows: 1 }); }
  quoteCard('「齐王弗听。」', '《资治通鉴》卷五', onq(t, 's6.4'), { y: 480, size: 110, max: 10, p: lp(t, 's6.4') * 2 });
  const n5 = on(t, 's6.5', 's6.5', .6, .4); if (n5 > 0) { const k = lp(t, 's6.5'); band(330, 600, .74 * n5, 40); txt('魏国诸大夫「皆以为秦伐赵，于魏便」', W / 2, 392, { size: 42, w: 700, color: C.gold, a: n5 * ease(seg(k, .05, .15)) }); txt('《通鉴》另记“齐人、楚人救赵”，其后无下文', W / 2, 470, { size: 32, fam: HEI, w: 500, color: C.bone, a: n5 * ease(seg(k, .2, .3)) }); txt('——《资治通鉴》卷五', W / 2, 536, { size: 26, fam: HEI, w: 500, color: C.goldDim, a: n5 });
    glow(109.6, 35.0, 3.2 + 1.2 * ease(seg(k, .5, 1)), '#3d5a78', n5 * .35); }
  tag('形势示意 · 非精确疆界', 64, NOTE_Y, fade(t, this.a + 1, this.b, .5, .4));
  dateTag('前260年 · 秋', fade(t, a('s6.1'), this.b, .5, .4));
} });

/* ---- S7 四十六天 ---- */
SC.push({ a: sceneStart('s7'), b: sceneStart('s8'), draw(t) {
  setCam(camKeys(t, [[a('s7.1'), [112.88, 35.81, 1950]], [z('s7.6'), [112.87, 35.805, 2250], x => x]]));
  const days = seg(t, a('s7.1') + .6, z('s7.3')); const dimQ = onq(t, 's7.2');
  drawMap(lerp(.45, 1, days), (1 - .3 * days) * (1 - .4 * dimQ));
  danHi(.6); rings(1); qinRings(t, 1, 1);
  const dim = .72 * days, alive = 1 - .16 * days;
  const [ac] = trapped(t, { dim, alive });
  // day counter
  const N = Math.max(1, Math.round(1 + 45 * days)); const ca = fade(t, a('s7.1') + .3, this.b, .5, .4) * (1 - .0);
  band(330, 520, .55 * ca, 30); txt('第', 70, 440, { size: 46, w: 700, color: C.goldDim, align: 'left', a: ca }); txt(String(N), 250, 428, { size: 190, w: 900, color: N >= 46 ? '#ffb39c' : C.bone, align: 'center', a: ca }); txt('日', 388, 440, { size: 46, w: 700, color: C.goldDim, align: 'left', a: ca }); txt('不得食', 480, 440, { size: 46, w: 700, color: C.bone, align: 'left', a: ca * .9 });
  quoteCard('「赵卒不得食四十六日，\n皆内阴相杀食。」', '《史记·白起王翦列传》', dimQ, { y: 640, size: 70, max: 12, p: lp(t, 's7.2') * 1.4, rows: 1 });
  // four columns, four or five rounds
  const f4 = on(t, 's7.4', 's7.4', .3, .5); if (f4 > 0) { const k = seg(lp(t, 's7.4'), .28, .86); const rounds = 4.5, ph = k * rounds, cyc = ph % 1, rn = Math.floor(ph); const ext = k > 0 && k < 1 ? Math.sin(Math.min(1, cyc * 1.5) * Math.PI * .5) * (cyc > .7 ? 1 - (cyc - .7) / .3 : 1) : 0; const str = 1 - rn * .14;
    const dirs = [[[112.845, 35.84], [112.825, 35.85], [112.80, 35.855]], [[112.845, 35.77], [112.825, 35.755], [112.805, 35.745]], [[112.87, 35.85], [112.885, 35.875], [112.90, 35.895]], [[112.872, 35.76], [112.89, 35.74], [112.905, 35.725]]];
    dirs.forEach((d, i) => arrow(d, ext * .96, { color: C.zhao, rim: C.zhaoHi, width: 15, a: f4 * str * (k > 0 && k < 1 ? 1 : 0) }));
    if (cyc > .55 && cyc < .8 && k < 1) { ctx.save(); ctx.globalAlpha = f4 * (1 - Math.abs(cyc - .67) / .13) * .8; ctx.strokeStyle = '#fff'; ctx.lineWidth = 3; dirs.forEach(d => { const [x, y] = P(d[2][0], d[2][1]); ctx.beginPath(); ctx.arc(x, y, 12 + (cyc - .55) * 60, 0, 7); ctx.stroke(); }); ctx.restore(); }
    tag('为四队 · 四五复之 · 不能出', 64, NOTE_Y, f4 * seg(k, .02, .1)); if (k > 0 && k < 1) txt('第 ' + '一二三四五'[Math.min(4, rn)] + ' 轮', 1016, 440, { size: 40, w: 700, color: C.bone, align: 'right', a: f4 }); }
  // Zhao Kuo's last charge
  const f5 = on(t, 's7.5', 's7.5', .3, 1.2); if (f5 > 0) { const k = lp(t, 's7.5'); const path = [[112.862, 35.80], [112.89, 35.795], [112.915, 35.80]]; const g = seg(k, .2, .6); const hit = seg(k, .68, .8);
    const hd = arrow(path, g * .95, { color: C.zhao, rim: C.zhaoHi, width: 22, a: f5 * (1 - hit) }); const q = hd || P(112.862, 35.80); plate(q[0] + 10, q[1] - 60, '赵括', { side: hit > .5 ? 'n' : 'zhao', a: f5 * (1 - .75 * hit), size: 34 });
    if (k > .5 && k < .9) { const r = rng(77); ctx.save(); ctx.strokeStyle = C.qinHi; ctx.lineWidth = 2; const tip = P(112.912, 35.80); for (let i = 0; i < 26; i++) { const an = -1.2 + r() * 2.4, len = 150 + r() * 120, pr = clamp((k - .5) / .22 - r() * .35); if (pr <= 0 || pr >= 1) continue; const sx = tip[0] + Math.cos(an) * len * (1 - pr), sy = tip[1] + Math.sin(an) * len * (1 - pr); ctx.globalAlpha = f5 * .9; ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(sx + Math.cos(an) * 26, sy + Math.sin(an) * 26); ctx.stroke(); } ctx.restore(); }
    tag('「秦军射杀赵括」——《史记·白起王翦列传》', 64, NOTE_Y, f5 * hit); }
  dateTag('前260年 · 九月', fade(t, a('s7.1'), this.b, .5, .4));
} });

/* ---- S8 结局 ---- */
function grid(x0, y0, cols, rows, gap, r, fn) { for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) fn(x0 + i * gap, y0 + j * gap, i + j * cols, r); }
SC.push({ a: sceneStart('s8'), b: sceneStart('s9'), draw(t) {
  setCam(camKeys(t, [[a('s8.1'), [112.87, 35.805, 2250]], [z('s8.3'), [112.90, 35.82, 1500]]]));
  const gone = seg(t, a('s8.3') + 1.2, z('s8.3') - 1.2); const black = Math.max(.25 * on(t, 's8.2'), ease(seg(t, a('s8.3') + 1, z('s8.3'))));
  drawMap(1, .68 * (1 - black));
  if (black < 1) { danHi(.5 * (1 - black)); rings(1 - black); qinRings(t, 1 - black, 1); trapped(t, { dim: .72 + .2 * seg(t, a('s8.1'), z('s8.1')), alive: .84 * (1 - gone), a_: 1 - black * .5 });
    const s1 = on(t, 's8.1', 's8.1', .4, .4); if (s1 > 0) { band(400, 560, .7 * s1, 40); txt('「卒四十万人降武安君」', W / 2, 470, { size: 60, w: 700, color: C.gold, a: s1 }); txt('——《史记·白起王翦列传》', W / 2, 540, { size: 26, fam: HEI, w: 500, color: C.goldDim, a: s1 }); }
    const k3 = seg(t, a('s8.3') + (z('s8.3') - a('s8.3')) * .55, z('s8.3')); if (k3 > 0) { const d = spline([[113.0, 35.85], [113.12, 36.0], [113.3, 36.12]], 10); ctx.save(); for (let i = 0; i < 6; i++) { const q = along(d, clamp(k3 * 1.1 - i * .04)); const [x, y] = P(q[0], q[1]); ctx.globalAlpha = 1; ctx.fillStyle = C.zhaoHi; ctx.beginPath(); ctx.arc(x, y, 3, 0, 7); ctx.fill(); } ctx.restore(); const q = P(113.14, 36.02); txt('二百四十人 归赵', q[0] + 20, q[1] + 44, { size: 32, w: 700, color: C.zhaoHi, a: seg(k3, .1, .3) * (1 - seg(k3, .85, 1)), stroke: 5 }); } }
  const q2 = onq(t, 's8.2'); speaker('武安君 白起', 420, q2); quoteCard('「非尽杀之，恐为乱。」', '《史记·白起王翦列传》', q2, { y: 510, size: 80, max: 11, p: seg(lp(t, 's8.2'), .55, 1) * 1.6 });
  const s3 = on(t, 's8.3', 's8.3', .5, .5) * (1 - seg(lp(t, 's8.3'), .5, .62)); if (s3 > 0) { band(400, 520, .7 * s3, 40); txt('「挟诈而尽坑杀之」', W / 2, 462, { size: 60, w: 700, color: C.gold, a: s3 }); }
  // the number
  const n4 = fade(t, a('s8.4') - .2, z('s8.5') + .3, .6, .5); if (n4 > 0) { txt('史载', W / 2, 520, { size: 44, w: 600, color: C.goldDim, a: n4, ls: 16 }); txt('四十五万', W / 2, 730, { size: 220, w: 900, color: C.bone, a: n4, ls: 4 }); const tg = ease(seg(t, a('s8.5'), a('s8.5') + .6)); ctx.save(); ctx.globalAlpha = n4 * (.55 + .45 * tg); ctx.strokeStyle = '#ffb39c'; ctx.lineWidth = 2.5; ctx.strokeRect(700, 858, 290, 62); ctx.restore(); txt('数字有争议', 845, 890, { size: 38, fam: HEI, w: 600, color: '#ffb39c', a: n4 * (.55 + .45 * tg), shadow: 0 });
    txt('「前后斩首虏四十五万人。赵人大震。」', W / 2, 1010, { size: 46, w: 700, color: C.gold, a: n4 * (1 - tg) }); txt('——《史记·白起王翦列传》', W / 2, 1076, { size: 26, fam: HEI, w: 500, color: C.goldDim, a: n4 }); txt('《史记》所记；后世对总数一直有争议', W / 2, 1010, { size: 38, fam: HEI, w: 500, color: C.bone, a: n4 * tg }); }
  // excavation schematic
  const e6 = on(t, 's8.6', 's8.6', .5, .5); if (e6 > 0) { const k = lp(t, 's8.6'); const x0 = 110, x1 = 970, top = 520; txt('高平 · 永录1号尸骨坑', W / 2, 400, { size: 54, w: 800, color: C.bone, a: e6 }); txt('1995年发掘', W / 2, 462, { size: 30, fam: HEI, w: 500, color: C.goldDim, a: e6 });
    const layers = [['#3a3122', 70, '耕土'], ['#51432c', 150, '黄土'], ['#43371f', 150, '']]; let y = top; ctx.save(); ctx.globalAlpha = e6; layers.forEach(([c, h, n]) => { ctx.fillStyle = c; ctx.fillRect(x0, y, x1 - x0, h); ctx.strokeStyle = 'rgba(0,0,0,.35)'; ctx.lineWidth = 1; for (let i = 0; i < 60; i++) { const r = Math.sin(i * 91.7 + y) * .5 + .5; ctx.beginPath(); ctx.moveTo(x0 + r * (x1 - x0), y + (Math.sin(i * 17.3) * .5 + .5) * h); ctx.lineTo(x0 + r * (x1 - x0) + 14, y + (Math.sin(i * 17.3) * .5 + .5) * h); ctx.stroke(); } y += h; });
    ctx.beginPath(); ctx.moveTo(300, top + 70); ctx.lineTo(340, top + 190); ctx.lineTo(740, top + 190); ctx.lineTo(780, top + 70); ctx.closePath(); ctx.fillStyle = '#231c12'; ctx.fill(); ctx.strokeStyle = C.gold; ctx.lineWidth = 3; ctx.setLineDash([10, 6]); ctx.stroke(); ctx.setLineDash([]); ctx.save(); ctx.clip(); ctx.strokeStyle = 'rgba(227,201,138,.28)'; ctx.lineWidth = 2; for (let i = -10; i < 40; i++) { ctx.beginPath(); ctx.moveTo(280 + i * 22, top + 60); ctx.lineTo(280 + i * 22 - 130, top + 200); ctx.stroke(); } ctx.restore(); ctx.strokeStyle = C.bone; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x0, top); ctx.lineTo(x1, top); ctx.stroke(); ctx.restore();
    txt('地表', x1 - 10, top - 22, { size: 24, fam: HEI, w: 400, color: C.note, a: e6, align: 'right' }); txt('坑（示意）', W / 2, top + 132, { size: 34, fam: HEI, w: 600, color: C.gold, a: e6, shadow: 0 });
    txt('✓ 能证实：这里有过大规模杀戮', 130, 960, { size: 44, w: 700, color: C.bone, a: e6 * ease(seg(k, .45, .6)), align: 'left' }); txt('✗ 证实不了：总数', 130, 1040, { size: 44, w: 700, color: '#ffb39c', a: e6 * ease(seg(k, .72, .85)), align: 'left' });
    txt('剖面为示意图，非实测；发掘简报见《文物》1996年第6期', 64, NOTE_Y, { size: 24, fam: HEI, w: 400, color: C.note, a: e6, align: 'left', shadow: 0 }); }
  // the winner's cost / a generation
  const w7 = fade(t, a('s8.7'), z('s8.11') + .4, .6, .6); if (w7 > 0) {
    const h7 = ease(seg(t, a('s8.7') + (z('s8.7') - a('s8.7')) * .55, z('s8.8'))); const s9 = seg(t, a('s8.9'), a('s8.9') + .8); const d9 = ease(seg(t, a('s8.9') + (z('s8.9') - a('s8.9')) * .5, z('s8.10')));
    txt('秦', 110, 420, { size: 72, w: 900, color: C.qinHi, a: w7, align: 'left' }); txt('赢的一方', 210, 426, { size: 32, fam: HEI, w: 500, color: C.note, a: w7, align: 'left' });
    ctx.save(); grid(124, 500, 26, 7, 32.5, 10, (x, y, i, r) => { const dead = (i * 7919 % 100) < 54; const al = w7 * (dead ? 1 - .86 * h7 : 1); ctx.globalAlpha = al; ctx.fillStyle = C.qinRim; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); if (dead && h7 > .02) { ctx.globalAlpha = w7 * h7 * .5; ctx.strokeStyle = '#3d4d5e'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.stroke(); } }); ctx.restore();
    txt('「秦卒死者过半，国内空。」', 110, 760, { size: 48, w: 700, color: C.gold, a: w7 * seg(h7, .1, .4), align: 'left' }); txt('—— 白起自述 ·《史记·白起王翦列传》', 110, 818, { size: 26, fam: HEI, w: 500, color: C.goldDim, a: w7 * seg(h7, .1, .4), align: 'left' });
    rule(110, 970, 866, w7 * s9 * .6, C.goldDim, 1);
    txt('赵', 110, 930, { size: 72, w: 900, color: C.zhaoHi, a: w7 * s9, align: 'left' }); txt('九年以后 · 前251年', 210, 936, { size: 32, fam: HEI, w: 500, color: C.note, a: w7 * s9, align: 'left' });
    ctx.save(); grid(124, 1004, 26, 4, 32.5, 10, (x, y, i, r) => { ctx.globalAlpha = w7 * s9 * (1 - .88 * d9); ctx.fillStyle = C.zhao; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); ctx.globalAlpha = w7 * s9 * d9 * .7; ctx.strokeStyle = C.zhaoDim; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.stroke(); }); grid(124, 1142, 26, 1, 32.5, 5, (x, y, i, r) => { ctx.globalAlpha = w7 * s9 * d9; ctx.fillStyle = C.zhaoHi; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); }); ctx.restore();
    txt('壮者', 1016, 1050, { size: 26, fam: HEI, w: 500, color: C.note, a: w7 * s9 * d9, align: 'right', stroke: 4 }); txt('其孤', 1016, 1142, { size: 26, fam: HEI, w: 500, color: C.note, a: w7 * s9 * d9, align: 'right', stroke: 4 });
    txt('「赵氏壮者皆死长平，其孤未壮。」', 110, 1216, { size: 46, w: 700, color: C.gold, a: w7 * seg(d9, .0, .3), align: 'left' }); txt('—— 燕相栗腹 ·《史记·赵世家》   圆点为示意，不按比例', 110, 1270, { size: 24, fam: HEI, w: 500, color: C.goldDim, a: w7 * seg(d9, .0, .3), align: 'left' }); }
  dateTag('前260年 · 九月', fade(t, a('s8.1'), a('s8.6'), .5, .4));
} });

/* ---- S9 尾声 ---- */
SC.push({ a: sceneStart('s9'), b: sceneStart('s10'), draw(t) {
  ctx.fillStyle = '#050607'; ctx.fillRect(0, 0, W, H);
  const al = fade(t, a('s9.1'), z('s9.3') + .6, .6, .8);
  txt('秦昭王五十年十一月', W / 2, 470, { size: 40, w: 600, color: C.goldDim, a: al, ls: 6 }); txt('杜邮', W / 2, 560, { size: 84, w: 900, color: C.bone, a: al, ls: 20 });
  speaker('武安君 白起', 700, al * seg(t, a('s9.1') + 2, a('s9.1') + 2.8));
  quoteCard('「长平之战，\n赵卒降者数十万人，\n我诈而尽坑之，\n是足以死。」', '《史记·白起王翦列传》', onq(t, 's9.2', 's9.3'), { y: 790, size: 68, max: 12, p: lp(t, 's9.2') * 1.3, rows: 1, bg: 0 });
} });

/* ---- S10 收尾 ---- */
SC.push({ a: sceneStart('s10'), b: TOTAL, draw(t) {
  setCam(camKeys(t, [[a('s10.1'), [112.6, 35.7, 300]], [TOTAL, [112.3, 35.65, 215], x => x]]));
  const end = fade(t, this.a, TOTAL - .2, 1, 1.4); drawMap(.6, .5 * end);
  const cr = seg(t, z('s10.3') + 2.6, z('s10.3') + 3.4);
  wedge(ease(seg(t, a('s10.3') + 1, z('s10.3'))) * end * (1 - cr), C.zhao, .08); place(...PL.cp, '', { a: end * .8 * (1 - cr), dot: 6, color: C.gold });
  const L = [['赵括，输在战场上。', 's10.1', 640], ['赵国，输在河内那一道命令上。', 's10.2', 800], ['而这一仗，', 's10.3', 960], ['从接下上党的那一天，', 's10.3', 1050], ['就已经开始了。', 's10.3', 1140]];
  const sub = [0, 0, 0, .28, .68];
  L.forEach(([s, id, y], i) => txt(s, W / 2, y, { size: i < 2 ? 62 : 66, w: 800, color: i < 2 ? C.bone : C.gold, a: end * (1 - cr) * ease(seg(t, a(id) + (z(id) - a(id)) * sub[i], a(id) + (z(id) - a(id)) * sub[i] + .6)) }));
  const fin = fade(t, z('s10.3') + .5, z('s10.3') + 2.9, .6, .5); band(1210, 1330, .6 * fin, 30); txt('「王悔不听赵豹之计，故有长平之祸焉。」', W / 2, 1250, { size: 40, w: 700, color: C.gold, a: fin }); txt('——《史记·赵世家》', W / 2, 1306, { size: 26, fam: HEI, w: 500, color: C.goldDim, a: fin });
  if (cr > 0) { const c = cr * fade(t, 0, TOTAL - .1, .1, .8); txt('史料', W / 2, 560, { size: 34, w: 700, color: C.goldDim, a: c, ls: 14 }); ['《史记·白起王翦列传》', '《史记·赵世家》', '《史记·廉颇蔺相如列传》', '《资治通鉴》卷五'].forEach((s, i) => txt(s, W / 2, 640 + i * 64, { size: 40, w: 600, color: C.bone, a: c })); ['行军路线、防线与城邑位置为示意；', '战场地点据后世考证，说法不一。', '地形：SRTM 等公开高程数据（AWS Terrain Tiles）', '河流：据高程推算 / Natural Earth'].forEach((s, i) => txt(s, W / 2, 960 + i * 50, { size: 28, fam: HEI, w: 400, color: C.note, a: c })); }
} });

/* ================= master ================= */
function renderFrame(t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.fillStyle = '#050607'; ctx.fillRect(0, 0, W, H);
  let sc = SC[0]; for (const s of SC) if (t >= s.a) sc = s;
  sc.draw.call(sc, t);
  // dip between scenes
  for (const s of SC) { if (s.a <= 0) continue; const d = 1 - Math.min(1, Math.abs(t - s.a) / .55); if (d > 0) shade(.9 * ease(d)); }
  vignette(); grain(t); header(t);
  const hid = LINES.some(l => HIDE.has(l.id) && t >= l.t0 - .1 && t <= l.t1 + .25);
  if (!hid) subtitles(t);
  if (t < .8) shade(1 - t / .8); if (t > TOTAL - 1) shade(clamp((t - (TOTAL - 1)) / .9));
}
window.ready = loadAll().then(() => true);
window.renderFrame = renderFrame; window.TOTAL = TOTAL; window.A_ = a; window.Z_ = z;
