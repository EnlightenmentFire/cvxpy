// 场景（下）：玖～收尾
'use strict';
// 四重城 + 城内兵点 + 四面魏军
function siegeView(t, o) {
  const cx = 540, cy = 980, SC = 0.88, a = o.alpha === undefined ? 1 : o.alpha; if (a <= 0) return;
  // 魏军：随城圈收缩向内压
  const press = o.press || 0, rr = lerp(470, 215, press);
  for (let i = 0; i < 8; i++) { const an = i / 8 * 6.283 + 0.35, x = cx + Math.cos(an) * rr * 1.02, y = cy + Math.sin(an) * rr * 0.95; dots(x, y, 46, 66, 46, C.wei, { alpha: a * (o.weiA === undefined ? 1 : o.weiA), r: 5, seed: 60 + i, edge: 'rgba(201,211,220,0.75)', jit: t * 1.5, keep: o.weiKeep === undefined ? 1 : o.weiKeep }); }
  walls(cx, cy, { alpha: a, broken: o.broken, shown: o.shown, core: o.core, t, sc: SC });
  if (o.men !== 0) dots(cx, cy, 120, 86 * (o.tight || 1), 76 * (o.tight || 1), C.redL, { alpha: a * (o.menA === undefined ? 1 : o.menA), r: 4, seed: 77, keep: o.men === undefined ? 1 : o.men, jit: t });
}
function dayCounter(n, a) { if (a <= 0) return; const y = 518; panel(664, y, 356, 116, a, 'rgba(14,12,10,0.94)'); text('被围 第', 688, y + 62, { size: 30, fam: SERIF, wt: 900, alpha: a, stroke: 0, color: C.gold }); text(String(n), 892, y + 56, { size: 72, fam: SERIF, wt: 900, alpha: a, stroke: 0, align: 'center', color: C.redL }); text('日', 998, y + 62, { size: 30, fam: SERIF, wt: 900, alpha: a, stroke: 0, align: 'right', color: C.gold }); }

// ---------------- 玖 · 二百日 ----------------
function sceneS9(t) {
  const S = TL.secs.s9;
  const k0 = AT('虎牢被围二百日'), k1 = AT('围了两百天'), k2 = AT('外城被撞破'), k3 = AT('将士眼皆生创'), k4 = AT('将士们的眼睛'), k5 = AT('德祖抚之以恩'), k6 = AT('毛德祖平日待人有恩'), k7 = AT('接着，就是开头那口井'), k8 = AT('孤城能做的'), e = S.end;
  ctx.fillStyle = '#0f0d0b'; ctx.fillRect(0, 0, W, H);
  const g = ctx.createRadialGradient(W / 2, 950, 80, W / 2, 950, 1050); g.addColorStop(0, 'rgba(84,60,32,0.55)'); g.addColorStop(1, 'rgba(12,10,9,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const wellA = fadeIO(t, k7 + 0.3, k8 + 0.2, 0.8, 0.8), sv = 1 - wellA;
  // 计数：1 → 200
  const dn = Math.round(lerp(1, 200, eio(prog(t, S.body, k2 + ET('外城被撞破') - k2 - 0.5))));
  // 城圈：外城破 → 内筑三重 → 又破二重
  const d2 = k2, b0 = P(t, d2 + 0.4, 1.4), s1 = P(t, d2 + 2.6, 0.7), s2 = P(t, d2 + 3.0, 0.7), s3 = P(t, d2 + 3.4, 0.7), b1 = P(t, d2 + 5.6, 1.0), b2 = P(t, d2 + 6.5, 1.0);
  const men = lerp(1, 0.42, P(t, k1 + 1.2, 6)) * lerp(1, 0.86, P(t, k4 + 4, 3));
  siegeView(t, { alpha: sv, broken: [b0, b1, b2, 0], shown: [1, s1, s2, s3], press: 0.25 * b0 + 0.3 * b1 + 0.3 * b2, men, tight: lerp(1, 0.72, P(t, k5, 3)), core: 1 });
  dayCounter(dn, sv);
  tag('外城破', 76, 576, sv * fadeIO(t, d2 + 0.6, d2 + 2.6, 0.4, 0.4), { size: 30, bar: C.weiE, align: 'left' });
  tag('于内更筑三重', 76, 576, sv * fadeIO(t, d2 + 2.6, d2 + 5.4, 0.4, 0.4), { size: 30, bar: C.red, align: 'left' });
  tag('又毁其二 · 唯保一城', 76, 576, sv * fadeIO(t, d2 + 5.6, k3 - 0.3, 0.4, 0.4), { size: 30, bar: C.weiE, align: 'left' });
  tag('《宋书》：死者太半', 76, 576, sv * fadeIO(t, k4 + 3.4, k5 - 0.2, 0.5, 0.4), { size: 30, bar: C.gold, align: 'left' });
  tag('终无离心', 76, 576, sv * fadeIO(t, k6 + 1.6, k7, 0.5, 0.4), { size: 34, bar: C.red, fam: SERIF, wt: 900, align: 'left' });
  note('四重城为示意，城的形状史书未载', W / 2, 1346, sv * 0.9 * P(t, d2 + 1, 0.6), 'center');
  // 那口井
  if (wellA > 0) {
    const tun = prog(t, k7 + 0.6, k7 + 2.4), lvl = 1 - eio(prog(t, k7 + 2.2, k7 + 4.6));
    wellDiagram(t, { alpha: wellA, tun, lvl, sc: 0.96, oy: 40 });
    tag('闰四月二十一（丁巳）· 井水被泄', 76, 520, wellA, { align: 'left', bar: C.weiE, size: 28 });
    tag('二十三（己未）· 城陷', 76, 590, wellA * P(t, k7 + 4.4, 0.5), { align: 'left', bar: C.gold, size: 30 });
    note('日期：《宋书》记日序，《通鉴》记干支，二者相合', 76, 1344, wellA, 'left');
  }
  season('summer', 0.7); dust(t, 0.7);
  bands(0.5, 0.6);
}

// ---------------- 拾 · 城亡 ----------------
function sceneS10(t) {
  const S = TL.secs.s10;
  const k0 = AT('城要破了'), k1 = AT('我誓与此城俱毙'), k2 = AT('我发过誓'), k3 = AT('拓跋嗣下令'), k4 = AT('毛德祖被俘'), k5 = AT('魏军自己，也病死'), e = S.end;
  ctx.fillStyle = '#0d0c0b'; ctx.fillRect(0, 0, W, H);
  const g = ctx.createRadialGradient(W / 2, 950, 80, W / 2, 950, 1050); g.addColorStop(0, 'rgba(70,50,30,0.5)'); g.addColorStop(1, 'rgba(12,10,9,0)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  // 最里一圈熄灭
  const out = P(t, k2 + 1.0, 4.0), core = 1 - out;
  const brk = P(t, k3 + 0.5, 2.0);
  const nameA = P(t, k0 + 0.6, 0.8) * lerp(1, 0.62, P(t, k4, 1.5));
  siegeView(t, { alpha: 1, broken: [1, 1, 1, brk], shown: [0.55, 0.55, 0.55, 1], press: lerp(0.85, 1.0, P(t, k3, 3)), men: 0.36 * (1 - P(t, k4 + 0.5, 2) * 0.99), menA: lerp(1, 0.6, out), tight: 0.72, core, weiKeep: 1 - 0.25 * P(t, k5 + 0.3, 1.6) });
  // 名字与那句话
  text('毛德祖', 546, 968, { size: 92, fam: SERIF, wt: 900, align: 'center', alpha: nameA, ls: 10, stroke: 12, strokeColor: 'rgba(9,8,7,0.9)' });
  text('“义不使城亡而身存”', 540, 1068, { size: 38, fam: SERIF, wt: 900, align: 'center', alpha: P(t, k3 + 0.2, 1.0) * lerp(1, 0.75, P(t, k4, 1.5)), color: C.gold, stroke: 8, strokeColor: 'rgba(9,8,7,0.9)' });
  note('《宋书》作：“我与此城并命，义不使此城亡而身在也。”', W / 2, 560, fadeIO(t, k1 + 1.2, k3 - 0.2, 0.6, 0.5), 'center');
  tag('魏主令：得德祖者，必生致之', 540, 540, fadeIO(t, k3 + 0.4, k4 - 0.2, 0.5, 0.4), { size: 30, bar: C.weiE });
  tag('《宋书》：“嗣重其固守之节”', 540, 604, fadeIO(t, k3 + 3.0, k4 - 0.2, 0.5, 0.4), { size: 28, bar: C.gold });
  // 二百人突围南还
  const go = eio(prog(t, k4 + 3.0, k4 + 7.5)), ga = fadeIO(t, k4 + 2.6, k5 + 0.2, 0.5, 0.8);
  if (ga > 0) { dots(lerp(560, 760, go), lerp(1090, 1330, go), 40, 34, 30, C.redL, { alpha: ga * (1 - P(t, k5 - 0.6, 0.8)), r: 4.4, seed: 91, jit: t * 3 }); tag('范道基等二百人 · 突围南还', 540, 1340, ga, { size: 28, bar: C.red }); }
  tag('执毛德祖者：魏将豆代田。将佐皆被俘', 540, 540, fadeIO(t, k4 + 0.3, k4 + 3.4, 0.5, 0.4), { size: 28, bar: C.weiE });
  tag('魏军：士卒疫死者什二三', 540, 540, fadeIO(t, k5 + 0.2, e - 0.3, 0.5, 0.4), { size: 30, bar: C.weiE });
  season('summer', 0.5 * (1 - out)); 
  bands(0.5, 0.6);
  fadeBlack(sstep((t - (e - 0.8)) / 0.8) * 0.9);
}

// ---------------- 尾声 ----------------
const MEMO = '去年逆虏纵肆，陵暴河南，司州刺史臣德祖竭诚尽力，抗对强寇，孤城独守，将涉期年，救师淹缓，举城沦没，圣怀垂悼，远近嗟伤。陛下殷忧谅闇，委政自下，臣等谋猷浅蔽，托付无成，遂令致节之臣，抱忠倾覆，将士歼辱，王略亏挫，上坠先规，下贻国耻。稽之朝典，无所辞责。……乞蒙屏固，以申国法。';
const MEMO_HI = ['孤城独守，将涉期年，救师淹缓', '遂令致节之臣，抱忠倾覆'];
function memorial(t, a, u, hiA) {
  if (a <= 0) return; const x0 = 130, y0 = 640, w = 820, h = 640, sz = 40, lh = 66;
  ctx.save(); ctx.globalAlpha = a; ctx.shadowColor = 'rgba(0,0,0,0.6)'; ctx.shadowBlur = 30; ctx.fillStyle = '#cdbb94'; ctx.fillRect(x0, y0, w, h); ctx.shadowBlur = 0;
  const gg = ctx.createLinearGradient(x0, 0, x0 + w, 0); gg.addColorStop(0, 'rgba(90,70,40,0.28)'); gg.addColorStop(0.5, 'rgba(90,70,40,0)'); gg.addColorStop(1, 'rgba(90,70,40,0.3)'); ctx.fillStyle = gg; ctx.fillRect(x0, y0, w, h);
  ctx.beginPath(); ctx.rect(x0, y0 + 8, w, h - 16); ctx.clip();
  const lines = wrap(MEMO, w - 96, sz, SERIF, 700), total = lines.length * lh, off = lerp(30, -(total - h + 60), u);
  // 高亮范围（按整段文字的下标）
  const his = MEMO_HI.map(s => [MEMO.indexOf(s), MEMO.indexOf(s) + s.length]); let idx = 0;
  for (let i = 0; i < lines.length; i++) {
    const y = y0 + 50 + off + i * lh; let x = x0 + 48;
    for (const ch of lines[i]) { const wch = measure(ch, sz, SERIF, 700); const hi = his.some((r, k) => idx >= r[0] && idx < r[1] && hiA[k] > 0);
      if (y > y0 - 40 && y < y0 + h + 40) { if (hi) { ctx.fillStyle = 'rgba(170,40,24,0.2)'; ctx.fillRect(x, y - sz * 0.62, wch, sz * 1.24); } ctx.font = font(sz, SERIF, hi ? 900 : 700); ctx.textBaseline = 'middle'; ctx.textAlign = 'left'; ctx.fillStyle = hi ? '#7a1c10' : 'rgba(30,24,18,0.9)'; ctx.fillText(ch, x, y); }
      x += wch; idx++; }
  }
  ctx.restore();
  ctx.save(); ctx.globalAlpha = a; let gr = ctx.createLinearGradient(0, y0, 0, y0 + 70); gr.addColorStop(0, 'rgba(205,187,148,1)'); gr.addColorStop(1, 'rgba(205,187,148,0)'); ctx.fillStyle = gr; ctx.fillRect(x0, y0, w, 70); gr = ctx.createLinearGradient(0, y0 + h - 70, 0, y0 + h); gr.addColorStop(0, 'rgba(205,187,148,0)'); gr.addColorStop(1, 'rgba(205,187,148,1)'); ctx.fillStyle = gr; ctx.fillRect(x0, y0 + h - 70, w, 70); ctx.restore();
}
function sceneS11(t) {
  const S = TL.secs.s11;
  const k0 = AT('滑台、洛阳、虎牢'), k1 = AT('建康那边，三位辅政大臣'), k2 = AT('孤城独守'), k3 = AT('一座孤城独自守了快一年'), k4 = AT('这年十一月，拓跋嗣死了'), k5 = AT('元嘉六年'), k6 = AT('这六年，史书没有'), e = S.end;
  const cam = mapCam(kf([[S.start, 114.6, 34.7, 8.6], [k1, 114.9, 34.4, 9.0], [k4 - 0.5, 115.2, 34.2, 9.4], [k4 + 3, 113.6, 37.6, 9.6], [e, 113.6, 37.9, 9.2]], t));
  const mA = fadeIO(t, k1 + 2.2, k4 - 0.4, 0.8, 0.8), north = P(t, k4 + 1, 2.4);
  drawMap(cam, lerp(0.16, 0.6, Math.max(mA, north * 0.5))); if (north > 0) season('night', north * 0.55);
  drawRivers(cam, 1 - north * 0.4); riverNames(cam, (1 - mA) * (1 - north), 'he huai');
  // 三镇皆陷，防线南移（示意）
  const a0 = (1 - north);
  fort(cam, G.huatai, '滑台', { alpha: a0, fall: 1, size: 32, dy: -34 }); fort(cam, G.luoyang, '洛阳', { alpha: a0, fall: 1, size: 32, dy: 40 }); fort(cam, G.hulao, '虎牢', { alpha: a0, fall: P(t, S.start + 0.6, 1.2), size: 38, dy: -36 });
  const mv = eio(prog(t, k0 + 1.4, k1 + 1.6));
  const lineOld = G.he.slice(4, 21), lineNew = [[112.2, 33.5], [113.4, 33.35], [114.6, 33.55], [115.6, 34.1], [116.3, 34.9], [116.9, 35.6], [117.8, 36.4], [118.6, 37.0]];
  geoLine(cam, lineOld, { color: C.redL, w: 5, alpha: a0 * (1 - mv) * 0.9, dash: [16, 12] });
  geoLine(cam, lineNew, { color: C.redL, w: 6, alpha: a0 * mv * 0.95, dash: [16, 12], glow: 'rgba(224,73,47,0.5)', blur: 10 });
  region(cam, '魏', 114.2, 36.2, C.weiE, a0 * 1.2, 80); region(cam, '宋', 116.4, 32.8, C.redL, a0 * 1.2, 80);
  city(cam, ...G.jiankang, '建康', { color: C.red, alpha: a0, size: 32, capital: true }); city(cam, ...G.pengcheng, '彭城', { color: C.red, alpha: a0, size: 28, r: 7, dy: 34 });
  tint(cam, [[112.3, 35.0], [113.2, 35.0], [114.6, 35.7], [116.2, 36.7], [117.6, 37.3], [117.7, 36.4], [116.9, 35.6], [116.3, 34.9], [115.6, 34.1], [114.6, 33.6], [113.4, 33.4], [112.3, 33.6]], 'rgba(20,24,30,1)', 0.42 * a0 * mv);
  tag('司、兖、豫诸郡多没于魏（防线位置为示意）', W / 2, 1290, a0 * fadeIO(t, k0 + 2.6, k1 + 2, 0.5, 0.5), { size: 26, bar: C.weiE });
  // 奏表
  if (mA > 0) {
    const u = prog(t, k1 + 2.6, k3 + 4.5);
    memorial(t, mA, eio(u), [P(t, k2 - 0.2, 0.6), P(t, AT('孤城独守') + 4.4, 0.6)]);
    text('司空徐羡之 · 尚书令傅亮 · 领军将军谢晦　上表', W / 2, 600, { size: 30, fam: SERIF, wt: 700, align: 'center', alpha: mA, color: C.gold });
    // 不许
    const na = mA * P(t, ET('一座孤城独自守了快一年') - 4.3, 0.5);
    if (na > 0) { ctx.save(); ctx.globalAlpha = na; ctx.translate(760, 1150); ctx.rotate(-0.08); ctx.strokeStyle = '#a52a18'; ctx.lineWidth = 7; ctx.strokeRect(-150, -74, 300, 148); ctx.restore(); ctx.save(); ctx.translate(760, 1150); ctx.rotate(-0.08); text('不许', 0, 4, { size: 104, fam: SERIF, wt: 900, align: 'center', alpha: na, color: '#a52a18', stroke: 0, ls: 16 }); ctx.restore(); note('《宋书》：“不许。”《通鉴》：“诏勿问。”', W / 2, 1326, na, 'center'); }
  }
  // 北方的一个点
  if (north > 0) {
    region(cam, '北 魏', 113.6, 39.3, C.weiE, north * 1.2, 70);
    city(cam, ...G.pingcheng, '平城', { color: C.weiE, alpha: north * 0.9, size: 30, capital: true, sub: '423 年十一月 拓跋嗣卒' });
    const px = 500, py = 880, fl = 0.6 + 0.4 * Math.sin(t * 2.1) * Math.sin(t * 0.7 + 1), da = north * P(t, k4 + 4.6, 1.2);
    const gl = ctx.createRadialGradient(px, py, 1, px, py, 90); gl.addColorStop(0, `rgba(255,120,80,${0.5 * da * (0.6 + 0.4 * fl)})`); gl.addColorStop(1, 'rgba(255,120,80,0)'); ctx.fillStyle = gl; ctx.fillRect(px - 90, py - 90, 180, 180);
    ctx.save(); ctx.globalAlpha = da; ctx.fillStyle = C.redL; ctx.beginPath(); ctx.arc(px, py, 8, 0, 7); ctx.fill(); ctx.restore();
    text('毛德祖', px + 30, py - 6, { size: 44, fam: SERIF, wt: 900, alpha: da });
    text('元嘉六年（429）· 死于虏中 · 时年六十五', px - 300, py + 84, { size: 34, fam: SERIF, wt: 700, alpha: north * P(t, k5 + 0.3, 0.8), color: C.gold });
    note('“虏中”所在，史书未载；此点不代表具体地点', W / 2, 1326, north * P(t, k5 + 1.2, 0.8), 'center');
  }
  bands(0.6, 0.62);
  fadeBlack(sstep((t - (e - 0.9)) / 0.9));
}

// ---------------- 收尾三句 ----------------
function sceneS12(t) {
  const S = TL.secs.s12, L3 = TL.lines.filter(l => l.sec === 's12'), e = S.end;
  ctx.fillStyle = '#0a0908'; ctx.fillRect(0, 0, W, H);
  const cam = mapCam([113.6, 34.4, 13.5]); ctx.save(); ctx.globalAlpha = 0.34 * fadeIO(t, S.start, e, 1.2, 1.0); drawPlate(cam, 'macro', 1); ctx.restore();
  ctx.fillStyle = 'rgba(10,9,8,0.45)'; ctx.fillRect(0, 0, W, H);
  // 三处回响：关中（灰）、停住的箭头、孤城
  const a1 = P(t, L3[0].start - 0.2, 0.8), a2 = P(t, L3[1].start - 0.2, 0.8), a3 = P(t, L3[2].start - 0.2, 0.8), fo = 1 - P(t, e - 1.0, 1.0);
  tint(cam, GUANZHONG, 'rgba(170,180,191,1)', 0.14 * a1 * fo);
  [G.routeTan2, G.routeLiu, G.routeShen].forEach(r => geoLine(cam, r, { color: 'rgba(150,120,110,1)', w: 5, alpha: 0.5 * a2 * fo }));
  const [hx, hy] = mw(cam, ...G.hulao); const gl = ctx.createRadialGradient(hx, hy, 1, hx, hy, 60); gl.addColorStop(0, `rgba(255,120,80,${0.6 * a3 * fo})`); gl.addColorStop(1, 'rgba(255,120,80,0)'); ctx.fillStyle = gl; ctx.fillRect(hx - 60, hy - 60, 120, 120);
  const ys = [1150, 1270, 1400], tx = [L3[0].text, L3[1].text, L3[2].text].map(s => s.replace(/。$/, ''));
  text(tx[0], W / 2, ys[0], { size: 58, fam: SERIF, wt: 900, align: 'center', alpha: a1 * fo, ls: 3 });
  text(tx[1], W / 2, ys[1], { size: 58, fam: SERIF, wt: 900, align: 'center', alpha: a2 * fo, ls: 3 });
  text(tx[2], W / 2, ys[2], { size: 58, fam: SERIF, wt: 900, align: 'center', alpha: a3 * fo, color: C.gold, ls: 3 });
}

// ---------------- 片尾 ----------------
function sceneEnd(t) {
  const s = TL.secs.end, a = fadeIO(t, s.start, s.end, 0.8, 1.0);
  ctx.fillStyle = '#090807'; ctx.fillRect(0, 0, W, H);
  walls(540, 640, { alpha: a * 0.7, broken: [1, 1, 1, 1], shown: [1, 1, 1, 1], sc: 0.62, core: 0.2 });
  text('孤城 · 壹', W / 2, 640, { size: 76, fam: SERIF, wt: 900, align: 'center', alpha: a, stroke: 10, strokeColor: 'rgba(9,8,7,0.95)', ls: 8 });
  text('下一集：韦孝宽守玉璧', W / 2, 940, { size: 50, fam: SERIF, wt: 900, align: 'center', alpha: a, color: C.gold, stroke: 0, ls: 4 });
  const ls = ['史料：《资治通鉴》卷一百一十八、一百一十九；', '《宋书》索虏传、庐陵王义真传、王镇恶传；', '《魏书》太宗纪、奚斤传、公孙表传、豆代田传', '',
    '地形据公开高程数据（Mapzen / AWS Terrain Tiles）晕渲；', '古河道、行军路线、城防、地道、水井均为示意', '旁白：Kokoro-82M v1.1-zh 语音合成　配乐：程序合成'];
  ls.forEach((x, i) => text(x, W / 2, 1090 + i * 46, { size: 26, wt: 500, align: 'center', alpha: a * 0.8, stroke: 0, color: C.dimtxt }));
}
