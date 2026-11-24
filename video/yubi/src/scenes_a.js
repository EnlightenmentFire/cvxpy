// 场景（上）：冷启动、片名、壹 一扇门、贰 断水·土山、叁 地道与火
'use strict';

// ---------- 道具：纸、箭、墙 ----------
let _paperTex = null;
function paperTex() {
  if (_paperTex) return _paperTex;
  const c = document.createElement('canvas'); c.width = 600; c.height = 1000; const g = c.getContext('2d');
  const id = g.createImageData(600, 1000); const r = rng(11);
  for (let y = 0; y < 1000; y++) for (let x = 0; x < 600; x++) {
    const i = (y * 600 + x) * 4; const fib = Math.sin(y * 0.9 + Math.sin(x * 0.05) * 3) * 4 + (r() - 0.5) * 18;
    const edge = Math.min(x, 599 - x, y, 999 - y); const burn = clamp(1 - edge / 40);
    id.data[i] = 222 + fib - burn * 60; id.data[i + 1] = 204 + fib - burn * 66; id.data[i + 2] = 160 + fib * 0.8 - burn * 70; id.data[i + 3] = 255;
  }
  g.putImageData(id, 0, 0); _paperTex = c; return c;
}
function drawArrow(x, y, ang, len, o = {}) {      // 箭：杆、羽、镞；(x,y)=箭镞尖
  ctx.save(); ctx.translate(x, y); ctx.rotate(ang); ctx.globalAlpha *= o.alpha === undefined ? 1 : o.alpha;
  if (o.blur) { const g = ctx.createLinearGradient(-len * 2.2, 0, -len * 0.2, 0); g.addColorStop(0, 'rgba(255,240,210,0)'); g.addColorStop(1, `rgba(255,240,210,${0.35 * o.blur})`); ctx.fillStyle = g; ctx.fillRect(-len * 2.2, -6, len * 2, 12); }
  ctx.fillStyle = '#5b3c22'; ctx.fillRect(-len, -4, len - 30, 8);                       // 杆
  ctx.fillStyle = '#5d6268'; ctx.strokeStyle = '#c9ced4'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(-46, -13); ctx.lineTo(-36, 0); ctx.lineTo(-46, 13); ctx.closePath(); ctx.fill(); ctx.stroke();  // 镞
  for (const s of [-1, 1]) { ctx.fillStyle = s > 0 ? '#8a7f6e' : '#a69a86'; ctx.beginPath(); ctx.moveTo(-len + 6, s * 3); ctx.quadraticCurveTo(-len + 30, s * 22, -len + 92, s * 6); ctx.lineTo(-len + 92, s * 2); ctx.closePath(); ctx.fill(); }   // 羽
  if (o.scroll) { ctx.fillStyle = '#d8c69c'; ctx.fillRect(-len * 0.55, -15, 70, 30); ctx.fillStyle = '#7a1f12'; ctx.fillRect(-len * 0.55 + 22, -16, 6, 32); ctx.fillRect(-len * 0.55 + 44, -16, 6, 32); }
  ctx.restore();
}
function wallBG(t, warm = 1) {      // 城上：夯土墙与木栅，火把光
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#120f0c'); g.addColorStop(0.5, '#1d1611'); g.addColorStop(1, '#0d0b09'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.globalAlpha = 0.55;
  for (let i = 0; i < 9; i++) { const x = i * 128 - 20; ctx.fillStyle = i % 2 ? '#2a1f16' : '#251b13'; ctx.fillRect(x, 0, 122, H); ctx.fillStyle = 'rgba(0,0,0,0.5)'; ctx.fillRect(x + 118, 0, 6, H);
    for (let k = 0; k < 14; k++) { ctx.fillStyle = `rgba(80,60,40,${0.08 + 0.08 * hash(i, k)})`; ctx.fillRect(x + 10 + hash(i, k + 3) * 90, hash(k, i) * H, 2, 80 + 160 * hash(i + k, 2)); } }
  ctx.restore();
  const fl = 0.85 + 0.15 * Math.sin(t * 9.1) * Math.sin(t * 5.3 + 1);
  const rg = ctx.createRadialGradient(880, 420, 20, 880, 420, 900); rg.addColorStop(0, `rgba(255,150,70,${0.32 * fl * warm})`); rg.addColorStop(1, 'rgba(255,120,60,0)'); ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H);
}

// ---------------- 冷启动 ----------------
const BOUNTY = '能斩城主降者，拜太尉，封开国郡公，邑万户，赏帛万疋';
const BACK = '若有斩高欢者，一依此赏';
function sceneCold(t) {
  const k0 = A('cold', 0), k1 = A('cold', 1), k2 = A('cold', 2), k3 = A('cold', 3), k4 = A('cold', 4), te = TL.secs.title.start;
  const tOut = k3 + 0.3;                     // 纸卷起、箭射出去
  if (t < k4 + 0.6) {
    wallBG(t);
    const hit = 0.9;
    // 箭自左（城外）射入，钉在木栅上；纸卷绑在箭杆上，往下展开
    const HX = 800, HY = 470, ANG = 0.2, LEN = 420;                        // 箭镞落点、角度、箭长
    const unroll = eout(prog(t, hit + 0.25, k0 + 1.4)), flip = eio(prog(t, k1 + 0.3, k1 + 1.2)), rollup = eio(prog(t, tOut, tOut + 0.55));
    const fly = eio(prog(t, tOut + 0.5, tOut + 1.25));
    if (t < hit) { const u = ein(prog(t, 0.2, hit)); drawArrow(lerp(-150, HX, u), lerp(HY - 180, HY, u), ANG, LEN, { blur: 1, scroll: 1 }); }
    else if (fly < 1) {
      const shake = t < hit + 0.35 ? Math.sin((t - hit) * 70) * 7 * (1 - (t - hit) / 0.35) : 0;
      ctx.save(); ctx.translate(0, shake);
      const ax = HX - fly * 1300, ay = HY - fly * 260;
      // 纸（挂在箭杆下）
      const ph = 720 * unroll * (1 - rollup), cxp = HX - LEN * 0.5, py = HY - Math.sin(ANG) * LEN * 0.5 + 18;
      if (ph > 6 && fly <= 0) {
        const sx = Math.cos(flip * Math.PI), pw = 440 * Math.max(0.02, Math.abs(sx));
        ctx.save(); ctx.translate(cxp, py);
        ctx.shadowColor = 'rgba(0,0,0,0.65)'; ctx.shadowBlur = 34;
        ctx.drawImage(paperTex(), 0, 0, 600, 1000 * ph / 720, -pw / 2, 0, pw, ph); ctx.shadowBlur = 0;
        if (sx < 0) { ctx.fillStyle = 'rgba(60,40,20,0.12)'; ctx.fillRect(-pw / 2, 0, pw, ph); }
        ctx.fillStyle = '#a8946a'; ctx.fillRect(-pw / 2 - 8, -8, pw + 16, 14); ctx.fillRect(-pw / 2 - 8, ph - 6, pw + 16, 14);
        ctx.strokeStyle = '#7a1f12'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(-6, -8); ctx.lineTo(-2, -30); ctx.moveTo(8, -8); ctx.lineTo(12, -28); ctx.stroke();   // 系绳
        if (pw > 40) {
          ctx.beginPath(); ctx.rect(-pw / 2, 0, pw, ph); ctx.clip(); ctx.scale(Math.abs(sx), 1);
          if (sx > 0) {   // 正面：悬赏令（竖排，自右向左）
            const shown = (t - (hit + 0.8)) / (k1 - hit - 1.2) * 22;
            vtext(BOUNTY, 150, 90, { size: 62, lh: 74, colw: 78, color: '#2a1b10', per: 8, shown, hl: ch => '尉公户疋'.includes(ch) && t > k0 + 2.5, hlColor: '#8f2014' });
          } else {         // 背面：韦孝宽手书
            const shown = (t - (k2 - 0.25)) / (E('cold', 2) - k2 + 0.1) * 11;
            vtext(BACK, 70, 110, { size: 78, lh: 90, colw: 120, color: '#1a110a', per: 6, shown });
          }
        }
        ctx.restore();
      }
      drawArrow(fly > 0 ? ax - 40 : ax, fly > 0 ? ay : ay, fly > 0 ? ANG + Math.PI : ANG, LEN, { scroll: (unroll < 0.05 || rollup > 0.95) ? 1 : 0, blur: fly > 0 ? 1 : 0 });
      ctx.restore();
    }
    const la = fadeIO(t, k0 + 0.5, k1 + 0.3, 0.5, 0.4); if (la > 0) { label('东魏射进城的悬赏令', 540, 300, { size: 32, bar: C.xuanL, alpha: la }); }
    const lb = fadeIO(t, k2 - 0.2, k3 + 0.4, 0.4, 0.4); if (lb > 0) { label('韦孝宽在背面题字，射回城外', 540, 300, { size: 32, bar: C.red, alpha: lb }); note('—— 《周书·韦孝宽传》', 540, 352, lb, 'center'); }
    bands(0.45, 0.55);
  }
  // 拉远：玉璧城
  if (t >= k4 - 0.2) {
    const al = sstep((t - k4 + 0.2) / 0.8); ctx.save(); ctx.globalAlpha = al;
    const cam = locCam(kf([[k4 - 0.2, 0.0, 0.0, 1.6], [te, 0, 0, 6.5]].map(r => [r[0], ...kmLL(r[1], r[2]), r[3]]), t));
    drawLocal(cam, { season: 0.75, dim: 0.42 });
    drawCity(cam, { alpha: 1 });
    bands(0.5, 0.55);
    const a1 = fadeIO(t, k4 + 0.1, te + 0.3, 0.5, 0.5);
    text('韦孝宽', 80, 360, { size: 92, fam: SERIF, wt: 900, alpha: a1, ls: 6 });
    text('公元 546 年冬 · 玉璧', 84, 450, { size: 40, wt: 500, alpha: a1 * P(t, k4 + 1.4, 0.5), color: C.gold, ls: 2 });
    text('今山西稷山县西南', 84, 505, { size: 30, wt: 500, alpha: a1 * P(t, k4 + 2.0, 0.5), color: 'rgba(244,234,214,0.85)' });
    const [cx, cy] = lk(cam, 0, 0); nail(cx, cy - 10, 1.1, a1 * P(t, k4 + 0.8, 0.4));
    ctx.restore();
  }
  const fo = sstep((t - (te - 0.6)) / 0.6); if (fo > 0) { ctx.fillStyle = `rgba(9,8,7,${fo})`; ctx.fillRect(0, 0, W, H); }
}

// ---------------- 片名 ----------------
function sceneTitle(t) {
  const s = TL.secs.title, u = (t - s.start) / (s.end - s.start);
  ctx.fillStyle = '#090807'; ctx.fillRect(0, 0, W, H);
  const a = fadeIO(t, s.start, s.end, 0.7, 0.6);
  // 一座城：方框 + 三面深沟（细线）
  ctx.save(); ctx.globalAlpha = a; const cx = W / 2, cy = 1060, au = eout(prog(u, 0.05, 0.55));
  ctx.strokeStyle = C.red; ctx.lineWidth = 10; ctx.shadowColor = 'rgba(226,69,46,0.6)'; ctx.shadowBlur = 26;
  ctx.beginPath(); ctx.rect(cx - 150 * au, cy - 110 * au, 300 * au, 220 * au); ctx.stroke(); ctx.shadowBlur = 0;
  ctx.strokeStyle = 'rgba(201,180,122,0.6)'; ctx.lineWidth = 3;
  const v = eout(prog(u, 0.2, 0.7));
  ctx.beginPath(); ctx.moveTo(cx - 260 * v, cy - 190); ctx.lineTo(cx + 260 * v, cy - 190); ctx.stroke();       // 北：陡坎
  ctx.beginPath(); ctx.moveTo(cx - 230, cy - 170); ctx.lineTo(cx - 230, cy - 170 + 330 * v); ctx.stroke();      // 西沟
  ctx.beginPath(); ctx.moveTo(cx + 230, cy - 170); ctx.lineTo(cx + 230, cy - 170 + 330 * v); ctx.stroke();      // 东沟
  ctx.restore();
  text('孤城 · 第二集', W / 2, 470, { size: 34, wt: 700, align: 'center', alpha: a * 0.85, stroke: 0, ls: 12 });
  ctx.fillStyle = `rgba(226,69,46,${a})`; ctx.fillRect(W / 2 - 30, 515, 60, 4);
  text('玉 璧', W / 2, 700 + 12 * (1 - eout(u * 2)), { size: 200, fam: SERIF, wt: 900, align: 'center', alpha: a, stroke: 0, ls: 20 });
  text('攻者自劳　守者常逸', W / 2, 1320, { size: 50, fam: SERIF, wt: 900, align: 'center', alpha: a * sstep((u - 0.25) * 4), color: C.gold, stroke: 0, ls: 6 });
  text('韦孝宽守玉璧（546）· 细节与胜负手', W / 2, 1405, { size: 30, wt: 500, align: 'center', alpha: a * sstep((u - 0.35) * 4) * 0.85, stroke: 0, ls: 2 });
}

// ---------------- 壹 · 一扇门 ----------------
function sceneS1(t) {
  const s = TL.secs.s1, b = s.body; const T = k => A('s1', k), TE = k => E('s1', k);
  const wide = [111.2, 35.9, 10.6], hedong = [110.9, 35.55, 3.4], gz = [109.2, 34.7, 4.2];
  const cam = macCam(kf([[s.start, ...wide], [TE(0), ...wide], [T(1) + 1.6, ...hedong], [TE(1), 110.9, 35.5, 3.2], [T(2) + 1.2, 111.5, 36.4, 5.6], [TE(2), 111.4, 36.3, 5.8], [T(3) + 1.5, 109.6, 34.9, 4.6], [T(5) - 0.2, ...gz], [TE(5), 109.1, 34.55, 3.0], [T(6) + 1.2, 110.0, 35.0, 4.6], [s.end, 110.0, 35.05, 4.9]], t));
  drawMacro(cam, 0.3);
  const ra = P(t, b - 0.3, 1.2);
  realms(cam, 1, P(t, T(0) + 3.6, 1.2), P(t, T(0) + 0.6, 1.2), P(t, T(0) + 5, 1), ['西 魏', '东 魏', '梁']);
  drawRivers(cam, ra, t > T(1) ? '汾水' : '');
  // 关中
  const ag = fadeIO(t, T(0) + 4.6, TE(0) + 0.6, 0.6, 0.6);
  if (ag > 0) { geoPoly(cam, G.guanzhong, 'rgba(255,140,100,0.18)', '#ffb08f', { alpha: ag, w: 3, dash: [10, 8] }); const [x, y] = mw(cam, 108.7, 35.2); label('关中（关西）：潼关以西，长安一带', x, y - 70, { size: 28, bar: C.red, alpha: ag }); }
  const ca = P(t, b, 0.8);
  city(cam, ...G.jinyang, '晋阳', { alpha: ca, color: C.xuanL, capital: 1, sub: '今太原 · 高欢大本营', dy: -44 });
  city(cam, ...G.changan, '长安', { alpha: ca, color: C.red, capital: 1, sub: '西魏都城 · 宇文泰', dy: 46 });
  city(cam, ...G.ye, '邺', { alpha: ca, color: C.xuanL, capital: 1, sub: '东魏都城', dy: -44 });
  city(cam, ...G.luoyang, '洛阳', { alpha: ca * 0.9, color: C.xuanL, r: 7, size: 28, dy: 40 });
  city(cam, ...G.tongguan, '潼关', { alpha: ca * 0.9, color: C.red, r: 6, size: 26, dy: 38 });
  // 河东 / 汾水 标注
  const ah = fadeIO(t, T(1) + 0.4, TE(2) + 0.6, 0.5, 0.5);
  if (ah > 0) {
    const [hx, hy] = mw(cam, 110.95, 35.15); label('河东：黄河以东的山西南部', hx, hy + 40, { size: 28, bar: C.gold, alpha: ah });
    const [fx, fy] = mw(cam, 111.45, 36.0); label('汾水：山西最大的河，西流入黄河', fx + 10, fy - 40, { size: 26, bar: C.water, alpha: ah * P(t, T(1) + 3.6, 0.5) });
  }
  // 玉璧：钉子
  const ya = P(t, T(1) + 1.0, 0.6);
  if (ya > 0) { const [x, y] = mw(cam, ...G.yubi); nail(x, y, 1.0 + 0.2 * Math.sin(t * 2), ya); text('玉璧', x + 30, y - 34, { size: 40, fam: SERIF, wt: 900, alpha: ya }); }
  // 一扇门：东魏沿汾水南下被挡住；542 年那次（淡化 + 雪）
  const ad = fadeIO(t, T(2) - 0.1, T(3) + 0.5, 0.4, 0.5);
  if (ad > 0) {
    const pts = [[112.4, 37.6], [112.0, 37.2], [111.7, 36.7], [111.5, 36.15], [111.25, 35.75], [111.05, 35.62]];
    const sp = smooth(pts.map(p => mw(cam, ...p)), 10);
    const e = strokePts(sp, { color: C.xuanL, w: 12, frac: P(t, T(2) + 0.2, 1.4), alpha: ad, glow: C.xuanG });
    if (e && t > T(2) + 1.5) { const [x, y] = mw(cam, ...G.yubi); cross(x + 28, y - 8, 18, '#fff1d0', 7, ad * P(t, T(2) + 1.5, 0.3)); }
    const a542 = P(t, T(2) + 2.2, 0.6);
    label('542 年 · 高欢围玉璧九日 · 遇大雪而退', W / 2, 640, { size: 30, bar: C.xuanL, alpha: ad * a542 });
    note('《资治通鉴》卷一百五十八', W / 2, 690, ad * a542, 'center');
    snowfall(t, ad * a542 * 0.8, 220, 9, 1.2);
  }
  // 王思政 → 荆州；举荐韦孝宽
  const aw = fadeIO(t, T(3) - 0.1, TE(3) + 0.3, 0.4, 0.5);
  if (aw > 0) {
    const y0 = mw(cam, ...G.yubi), r0 = mw(cam, ...G.rangcheng);
    curveArrow([[y0[0] - 10, y0[1] + 20], [lerp(y0[0], r0[0], 0.5) + 80, lerp(y0[1], r0[1], 0.5)], [r0[0], r0[1] - 20]], { color: C.redL, w: 6, head: 18, frac: P(t, T(3) + 0.2, 1.2), alpha: aw, dash: [12, 9] });
    label('王思政 调任荆州 ↘', clamp(r0[0], 200, W - 200), clamp(r0[1] + 50, 700, 1240), { size: 28, bar: C.red, alpha: aw * P(t, T(3) + 0.8, 0.4) });
    label('举荐：韦孝宽 接守玉璧', y0[0] - 20, y0[1] - 92, { size: 30, bar: C.red, alpha: aw * P(t, T(3) + 1.7, 0.4), align: 'right' });
    const d = mw(cam, ...G.duling); const ad2 = P(t, T(3) + 3.0, 0.4);
    city(cam, ...G.duling, '', { alpha: aw * ad2, color: C.redL, r: 7 }); label('京兆杜陵 · 今西安东南', d[0], d[1] + 52, { size: 28, bar: C.redL, alpha: aw * ad2 });
  }
  // 三辅
  const a3 = fadeIO(t, T(4) - 0.2, TE(5) + 0.4, 0.5, 0.5);
  if (a3 > 0) {
    const pts = [[[108.05, 34.55], '右扶风'], [[109.25, 34.02], '京兆'], [[109.95, 34.95], '左冯翊']];
    pts.forEach(([p, nm], i) => { const [x, y] = mw(cam, ...p); const al = a3 * P(t, T(5) + 0.2 + i * 0.4, 0.4); ctx.save(); ctx.globalAlpha = al; ctx.fillStyle = 'rgba(255,130,100,0.22)'; ctx.beginPath(); ctx.arc(x, y, 58, 0, 7); ctx.fill(); ctx.strokeStyle = '#ffb08f'; ctx.lineWidth = 3; ctx.stroke(); ctx.restore(); text(nm, x, y, { size: 34, fam: SERIF, wt: 900, align: 'center', alpha: al }); });
    label('三辅：汉代长安周边三郡，后泛指关中', W / 2, 1290, { size: 28, bar: C.gold, alpha: a3 * P(t, T(5) - 0.1, 0.4) });
  }
  // 结论：关中人守关中的门
  const a6 = fadeIO(t, T(6) - 0.1, s.end, 0.4, 0.4);
  if (a6 > 0) {
    const p0 = mw(cam, ...G.changan), p1 = mw(cam, ...G.yubi);
    ctx.save(); ctx.globalAlpha = a6; ctx.strokeStyle = C.red; ctx.lineWidth = 5; ctx.setLineDash([14, 10]); ctx.shadowColor = C.redG; ctx.shadowBlur = 16; ctx.beginPath(); ctx.moveTo(p0[0], p0[1]); const u = P(t, T(6) + 0.3, 1.0); ctx.lineTo(lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u)); ctx.stroke(); ctx.restore();
    nail(p1[0], p1[1], 1.25, a6);
    label('关中人 · 守关中的门', W / 2, 640, { size: 40, fam: SERIF, wt: 900, bar: C.red, alpha: a6 * P(t, T(6) + 1.4, 0.4) });
  }
  bands(0.5, 0.55); compass(990, 250, ca);
  note('疆界、城址为示意', 64, 1318, ca * 0.8);
}

// ---------------- 贰 · 断水 · 土山 ----------------
let CAMP = null;
function campDots() {      // 东魏营盘：城外三面的一块块营区（台塬南面、东西两侧、北面谷地），营内兵点成行
  if (CAMP) return CAMP; const r = rng(46); CAMP = [];
  const zones = [[-2.6, 2.6, -3.4, -1.0, 26], [-3.2, -0.85, -1.0, 1.0, 9], [0.85, 3.2, -1.0, 1.0, 9], [-3.0, 3.0, 1.05, 2.1, 14]];
  let id = 0;
  for (const [x0, x1, y0, y1, n] of zones) for (let k = 0; k < n; k++) {
    const cx = lerp(x0, x1, r()), cy = lerp(y0, y1, r()), w = 0.18 + 0.22 * r(), h = 0.1 + 0.12 * r(), an = (r() - 0.5) * 0.6, d = 0.034;
    const order = r();
    for (let u = -w / 2; u <= w / 2; u += d) for (let v = -h / 2; v <= h / 2; v += d) {
      const x = cx + u * Math.cos(an) - v * Math.sin(an), y = cy + u * Math.sin(an) + v * Math.cos(an);
      CAMP.push([x + (r() - 0.5) * 0.008, y + (r() - 0.5) * 0.008, r(), order, id++]);
    }
  }
  CAMP.sort((p, q) => p[3] - q[3]);      // 按营区先后出现
  return CAMP;
}
function drawCamp(cam, t, a = 1, frac = 1, dim = 0) {
  if (a <= 0) return; const list = []; const n = Math.floor(campDots().length * frac);
  for (let i = 0; i < n; i++) { const c = CAMP[i]; if (dim > 0 && c[2] < dim) continue; list.push(lk(cam, c[0], c[1])); }
  ctx.save(); ctx.globalAlpha *= a; dots(list, '#0c1015', '#a9b9ca', clamp(4.6 / Math.sqrt(cam.km / 3), 2.2, 5)); ctx.restore();
}
function sceneS2(t) {
  const s = TL.secs.s2, b = s.body; const T = k => A('s2', k), TE = k => E('s2', k);
  const tl = T(2) - 0.3;          // 切到局部地形
  if (t < tl + 0.8) {
    const cam = macCam(kf([[s.start, 112.3, 36.6, 6.6], [T(1), 112.2, 36.4, 7.6], [tl + 0.8, 111.2, 35.7, 3.0]], t));
    drawMacro(cam, 0.3); realms(cam, 1, 1, 1, 0.6); drawRivers(cam, 1, '汾水');
    const ca = 1;
    city(cam, ...G.jinyang, '晋阳', { alpha: ca, color: C.xuanL, capital: 1, dy: -44 });
    city(cam, ...G.ye, '邺', { alpha: ca, color: C.xuanL, capital: 1, dy: -44 });
    const [jx, jy] = mw(cam, ...G.jinyang);
    const a0 = fadeIO(t, b + 0.2, T(1) + 0.4, 0.5, 0.5);
    if (a0 > 0) {
      unitBox(jx - 150, jy + 30, { type: 'hq', color: C.xuanL, name: '高欢', sub: '东魏真正的主人', alpha: a0 });
      label('边镇出身，家贫 → 一手扶起东魏', W / 2, 640, { size: 30, bar: C.xuanL, alpha: a0 * P(t, b + 1.0, 0.5) });
      note('《北齐书·神武纪》', W / 2, 690, a0 * P(t, b + 1.0, 0.5), 'center');
    }
    // 倾山东之众：各路汇向晋阳，再沿汾水南下
    const a1 = P(t, T(1) - 0.3, 0.5);
    if (a1 > 0) {
      const srcs = [[114.4, 36.4], [115.6, 37.6], [113.6, 35.2], [116.2, 35.3], [114.8, 38.6]];
      srcs.forEach((p, i) => { const q = mw(cam, ...p); arrow(q[0], q[1], jx + 10, jy + 10, { color: C.xuanL, w: 7, head: 20, frac: P(t, T(1) - 0.2 + i * 0.15, 0.9), alpha: a1 * 0.9, glow: C.xuanG }); });
      const pts = [[112.4, 37.6], [112.0, 37.2], [111.7, 36.7], [111.5, 36.15], [111.25, 35.75], [111.05, 35.62]];
      strokePts(smooth(pts.map(p => mw(cam, ...p)), 10), { color: C.xuanL, w: 16, frac: P(t, T(1) + 0.8, 1.6), alpha: a1, glow: C.xuanG });
      label('546 年九月 · 倾山东之众', W / 2, 640, { size: 34, bar: C.xuanL, alpha: a1 * fadeIO(t, T(1), tl + 0.5, 0.4, 0.4) });
    }
    const [yx, yy] = mw(cam, ...G.yubi); nail(yx, yy, 1.1, 1); text('玉璧', yx + 30, yy - 34, { size: 38, fam: SERIF, wt: 900 });
    bands(0.5, 0.55); compass(990, 250, 1);
  }
  if (t >= tl) {
    const al = sstep((t - tl) / 0.8); ctx.save(); ctx.globalAlpha = al;
    const K = (tt, dx, dy, km) => [tt, ...kmLL(dx, dy), km];
    const cam = locCam(kf([K(tl, 0, 0.6, 9.5), K(T(3), 0, 0.9, 8.0), K(TE(3), 0, 0.9, 7.6), K(T(4) + 1.0, 0, -0.25, 2.6), K(TE(4), 0, -0.3, 2.4), K(T(6), 0, -0.2, 2.8), K(s.end, 0, -0.1, 3.2)], t));
    const season = lerp(0.05, 0.25, prog(t, s.start, s.end));
    drawLocal(cam, { season, dim: 0.3 });
    // 汾水：原河道 → 一夜改道（离城更远）
    const div = eio(prog(t, CK('s2', 3, 2) - 0.2, CK('s2', 3, 2) + 1.6));
    const shift = div * 1.35;      // 公里，示意
    const river = FEN.map(p => [p[0], p[1] + shift / 110.57 * clamp(1 - Math.abs(p[0] - YB[0]) / 0.22) ** 0.7]);
    geoLine(cam, FEN, { color: C.water, w: 6, alpha: 0.9 * (1 - div * 0.75), glow: 'rgba(120,190,220,0.6)', n: 2 });
    if (div > 0) {
      geoLine(cam, river, { color: C.water, w: 7, alpha: div, glow: 'rgba(120,190,220,0.7)', n: 2 });
      const [x0, y0] = lk(cam, -1.6, 2.2), [x1, y1] = lk(cam, 1.6, 2.2);
      ctx.save(); ctx.globalAlpha = div; ctx.strokeStyle = C.xuan; ctx.lineWidth = 12; ctx.beginPath(); ctx.moveTo(x0, y0 + 40); ctx.quadraticCurveTo((x0 + x1) / 2, y0 - 120 * div, x1, y1 + 40); ctx.stroke(); ctx.strokeStyle = C.xuanL; ctx.lineWidth = 2; ctx.stroke(); ctx.restore();
    }
    // 取水路线
    const aw = fadeIO(t, T(3) + 0.3, TE(3) + 0.8, 0.4, 0.6);
    if (aw > 0) { const p0 = lk(cam, 0.02, 0.45), p1 = lk(cam, 0.08, 2.35 + shift * 0.9); ctx.save(); ctx.globalAlpha = aw; ctx.setLineDash([6, 10]); ctx.strokeStyle = '#cfe6ee'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(p0[0], p0[1]); ctx.lineTo(p1[0], p1[1]); ctx.stroke(); ctx.restore(); label(div > 0.5 ? '一夜改道 · 离城更远' : '城中无水 · 汲于汾', p1[0] + 20, (p0[1] + p1[1]) / 2, { size: 30, bar: div > 0.5 ? C.xuanL : C.water, alpha: aw, align: 'left' }); }
    const an = fadeIO(t, TE(3) - 0.6, T(4) + 1.0, 0.4, 0.4); if (an > 0) note('城中后来如何取水，史书未载', W / 2, 1300, an, 'center', 26);
    // 营盘
    drawCamp(cam, t, P(t, tl + 0.5, 1.2), Math.min(1, 0.35 + prog(t, tl, T(4)) * 0.65));
    drawCity(cam, { alpha: 1 });
    // 土山 + 两座楼
    const mh = prog(t, T(4) + 0.6, TE(4) - 0.4);
    if (t > T(4)) {
      const [mx, my] = lk(cam, ...MOUND); const rr = 0.16 / LKM() * cam.s;
      ctx.save(); ctx.globalAlpha = P(t, T(4), 0.5);
      for (let k = 0; k < 6; k++) { const f = clamp(mh * 6 - k); if (f <= 0) continue; ctx.fillStyle = `rgba(${20 + k * 8},${26 + k * 8},${34 + k * 8},0.75)`; ctx.beginPath(); ctx.ellipse(mx, my, rr * (1 - k * 0.13) * (0.6 + 0.4 * f), rr * 0.75 * (1 - k * 0.13) * (0.6 + 0.4 * f), -0.1, 0, 7); ctx.fill(); }
      ctx.strokeStyle = C.xuanL; ctx.lineWidth = 3; ctx.beginPath(); ctx.ellipse(mx, my, rr, rr * 0.75, -0.1, 0, 7); ctx.stroke(); ctx.restore();
      label('土山', mx, my + rr * 0.75 + 34, { size: 32, fam: SERIF, wt: 900, bar: C.xuanL, alpha: P(t, T(4) + 0.4, 0.4) });
      TOWERS.forEach(p => { const [x, y] = lk(cam, ...p); ctx.save(); ctx.globalAlpha = P(t, T(4) + 1.6, 0.4); ctx.fillStyle = C.red; ctx.fillRect(x - 9, y - 9, 18, 18); ctx.strokeStyle = '#ffd2c2'; ctx.lineWidth = 2; ctx.strokeRect(x - 9, y - 9, 18, 18); ctx.restore(); });
      const [tx, ty] = lk(cam, 0.02, -0.5); label('城南两座楼', tx + 150, ty - 40, { size: 28, bar: C.red, alpha: fadeIO(t, T(4) + 1.8, TE(4), 0.4, 0.4) });
    }
    bands(0.5, 0.55); compass(990, 250, 1);
    // 侧视：土山 vs 楼
    const ap = fadeIO(t, CK('s2', 4, 2) - 0.3, s.end, 0.5, 0.5);
    if (ap > 0) drawTowerRace(t, ap, mh, T(6));
    // 结论
    const a8 = fadeIO(t, T(8) - 0.1, s.end, 0.4, 0.4);
    if (a8 > 0) {
      ctx.save(); ctx.globalAlpha = a8; rrect(60, 262, 960, 200, 10); ctx.fillStyle = 'rgba(14,11,8,0.88)'; ctx.fill(); ctx.restore();
      text('攻方：改一条河，堆一座山', 100, 320, { size: 40, fam: SERIF, wt: 900, alpha: a8, stroke: 0, color: '#b9c8d8' });
      text('守方：再绑一截木头', 100, 400, { size: 40, fam: SERIF, wt: 900, alpha: a8 * P(t, CK('s2', 8, 1) - 0.1, 0.4), stroke: 0, color: '#ff9a7c' });
    }
    ctx.restore();
  }
}
// 侧视图：土山一层层加高，楼一节节往上接，始终高出一截
function drawTowerRace(t, a, mh, tTaunt) {
  const y0 = 760, y1 = 1300, gy = 1230;
  ctx.save(); ctx.globalAlpha = a;
  ctx.fillStyle = 'rgba(14,12,10,0.985)'; ctx.fillRect(40, y0, 1000, y1 - y0); ctx.fillStyle = C.gold; ctx.fillRect(40, y0, 1000, 3);
  text('侧视示意（高度、比例为推测）', 70, y0 + 36, { size: 24, wt: 500, stroke: 0, color: 'rgba(244,234,214,0.7)' });
  ctx.strokeStyle = 'rgba(244,234,214,0.5)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(60, gy); ctx.lineTo(1020, gy); ctx.stroke();
  // 城墙（右）
  ctx.fillStyle = '#5a3a26'; ctx.fillRect(700, gy - 150, 320, 150); ctx.fillStyle = '#7a5236'; for (let x = 700; x < 1020; x += 32) ctx.fillRect(x, gy - 168, 20, 18);
  // 土山（左）：分层
  const mhh = 40 + 300 * mh;
  ctx.fillStyle = '#1c232b'; ctx.beginPath(); ctx.moveTo(80, gy); ctx.quadraticCurveTo(330, gy - mhh * 1.25, 640, gy); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = C.xuanL; ctx.lineWidth = 3; ctx.stroke();
  for (let k = 1; k < 6; k++) { const yy = gy - mhh * k / 6 * 0.62; ctx.strokeStyle = 'rgba(159,176,195,0.25)'; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(110 + k * 30, yy); ctx.lineTo(610 - k * 30, yy); ctx.stroke(); }
  text('土山', 330, gy - mhh * 0.62 - 40, { size: 32, fam: SERIF, wt: 900, align: 'center', color: '#b9c8d8' });
  // 楼：一节一节往上接，比土山顶高一截
  const top = gy - Math.max(260, mhh * 0.62 + 70) - (t > tTaunt ? 20 * Math.sin((t - tTaunt) * 2) : 0);
  for (const tx of [760, 930]) {
    ctx.fillStyle = '#6b4a30'; ctx.fillRect(tx, top, 56, gy - 150 - top);
    ctx.strokeStyle = '#d8b48a'; ctx.lineWidth = 2; for (let y = gy - 150; y > top; y -= 26) { ctx.beginPath(); ctx.moveTo(tx, y); ctx.lineTo(tx + 56, y); ctx.stroke(); ctx.beginPath(); ctx.moveTo(tx, y); ctx.lineTo(tx + 56, y - 26); ctx.stroke(); }
    ctx.fillStyle = C.red; ctx.fillRect(tx - 6, top - 14, 68, 14);
  }
  text('楼 · 缚木接之', 873, top - 40, { size: 30, fam: SERIF, wt: 900, align: 'center', color: '#ff9a7c' });
  // 高差
  const ty = gy - mhh * 0.62;
  ctx.setLineDash([8, 8]); ctx.strokeStyle = 'rgba(255,240,210,0.6)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(330, ty); ctx.lineTo(1000, ty); ctx.stroke(); ctx.beginPath(); ctx.moveTo(700, top); ctx.lineTo(1000, top); ctx.stroke(); ctx.setLineDash([]);
  text('始终高出一截', 660, (ty + top) / 2, { size: 26, wt: 700, align: 'right', color: C.gold, stroke: 0 });
  ctx.restore();
}

// ---------------- 叁 · 地道与火：南北剖面（真实高程，垂直夸大） ----------------
// 剖面取遗址点南北一线（公里，北为正）的高程（米），来自 SRTM
const PROF = [[1.49, 378], [1.31, 379], [1.12, 377], [0.93, 390], [0.84, 394], [0.75, 395], [0.65, 388], [0.56, 403], [0.47, 449], [0.37, 455], [0.28, 459], [0.19, 459], [0.09, 462], [0.0, 456], [-0.19, 457], [-0.37, 457], [-0.56, 460], [-0.75, 462], [-0.93, 464], [-1.12, 463], [-1.31, 463], [-1.49, 463]];
function sceneS3(t) {
  const s = TL.secs.s3, b = s.body; const T = k => A('s3', k), TE = k => E('s3', k);
  // 背景：局部地形（北面陡坎高亮）
  const cam = locCam(kf([[s.start, ...kmLL(0, 0.3), 3.2], [TE(0), ...kmLL(0, 0.45), 2.6], [s.end, ...kmLL(0, 0.4), 2.8]], t));
  drawLocal(cam, { season: 0.3, dim: 0.5 });
  drawCamp(cam, t, 0.6, 1); drawCity(cam, { alpha: 0.8 });
  bands(0.55, 0.6);
  // 孤虚法：干支盘指向北
  const ag = fadeIO(t, b + 0.6, TE(0) + 0.3, 0.5, 0.5);
  if (ag > 0) {
    const cx = 830, cy = 560, R = 120; const rot = lerp(2.4, 0, eout(prog(t, b + 0.8, b + 3.2)));
    ctx.save(); ctx.globalAlpha = ag; ctx.fillStyle = 'rgba(14,12,10,0.86)'; ctx.beginPath(); ctx.arc(cx, cy, R + 34, 0, 7); ctx.fill();
    ctx.strokeStyle = C.gold; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(cx, cy, R + 34, 0, 7); ctx.stroke(); ctx.beginPath(); ctx.arc(cx, cy, R - 30, 0, 7); ctx.stroke();
    const br = '子丑寅卯辰巳午未申酉戌亥';
    for (let i = 0; i < 12; i++) { const an = rot + i * Math.PI / 6 - Math.PI / 2; text(br[i], cx + Math.cos(an) * R, cy + Math.sin(an) * R, { size: 28, fam: SERIF, wt: 900, align: 'center', stroke: 0, color: i === 0 && rot < 0.05 ? C.redL : C.cream }); }
    ctx.restore();
    text('孤虚法', cx, cy - 6, { size: 30, fam: SERIF, wt: 900, align: 'center', alpha: ag, stroke: 0, color: C.gold });
    text('推算方位吉凶', cx, cy + 30, { size: 20, wt: 500, align: 'center', alpha: ag, stroke: 0 });
    label('术士李业兴 · 算定主攻北面', cx - 20, cy + R + 76, { size: 28, bar: C.xuanL, alpha: ag * P(t, b + 3.0, 0.4) });
  }
  const an = fadeIO(t, CK('s3', 0, 3) - 0.3, A('s3', 1) - 0.35, 0.4, 0.3);
  if (an > 0) { const [x, y] = lk(cam, 0, 0.6); leader(x, y, 300, 1000, 'rgba(220,183,108,0.85)', 3); label('北，天险也：悬崖深沟', 300, 1040, { size: 34, fam: SERIF, wt: 900, bar: C.gold, alpha: an }); note('《资治通鉴》卷一百五十九 ·《北齐书·神武纪》', 300, 1092, an, 'center'); }
  // 剖面图
  const ap = fadeIO(t, T(1) - 0.4, s.end, 0.5, 0.5);
  if (ap > 0) drawSection(t, ap);
  const a4 = fadeIO(t, T(4) - 0.1, s.end, 0.4, 0.4);
  if (a4 > 0) {
    ctx.save(); ctx.globalAlpha = a4; rrect(60, 262, 960, 200, 10); ctx.fillStyle = 'rgba(14,11,8,0.88)'; ctx.fill(); ctx.restore();
    text('攻：主攻方向，靠算', 100, 320, { size: 42, fam: SERIF, wt: 900, alpha: a4, stroke: 0, color: '#b9c8d8' });
    text('守：一条沟', 100, 400, { size: 42, fam: SERIF, wt: 900, alpha: a4 * P(t, CK('s3', 4, 1) - 0.1, 0.4), stroke: 0, color: '#ff9a7c' });
  }
}
function drawSection(t, a) {
  const T = k => A('s3', k); const x0 = 60, x1 = 1020, y0 = 640, y1 = 1300;
  const X = km => lerp(x0 + 20, x1 - 20, (1.45 - km) / 2.9), Y = m => lerp(1215, 840, (m - 370) / 100);   // 垂直夸大
  ctx.save(); ctx.globalAlpha = a;
  ctx.fillStyle = 'rgba(12,11,10,0.985)'; ctx.fillRect(x0, y0, x1 - x0, y1 - y0); ctx.fillStyle = C.gold; ctx.fillRect(x0, y0, x1 - x0, 3); ctx.fillRect(x0, y1 - 3, x1 - x0, 3);
  text('南北剖面 · 真实高程（垂直方向夸大约 4 倍）', x0 + 26, y0 + 34, { size: 24, wt: 500, stroke: 0, color: 'rgba(244,234,214,0.75)' });
  text('北', x0 + 30, y0 + 80, { size: 30, fam: SERIF, wt: 900, stroke: 0 }); text('南', x1 - 30, y0 + 80, { size: 30, fam: SERIF, wt: 900, stroke: 0, align: 'right' });
  // 地面
  const pts = PROF.map(p => [X(p[0]), Y(p[1])]); const sp = smooth(pts, 6);
  ctx.beginPath(); ctx.moveTo(sp[0][0], y1 - 4); sp.forEach(p => ctx.lineTo(p[0], p[1])); ctx.lineTo(sp[sp.length - 1][0], y1 - 4); ctx.closePath();
  const g = ctx.createLinearGradient(0, 840, 0, y1); g.addColorStop(0, '#7b6545'); g.addColorStop(1, '#3b2f22'); ctx.fillStyle = g; ctx.fill();
  ctx.strokeStyle = '#d9c39a'; ctx.lineWidth = 3; ctx.beginPath(); sp.forEach((p, i) => i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])); ctx.stroke();
  text('汾河谷地', X(1.15), Y(378) - 30, { size: 26, wt: 700, align: 'center', stroke: 0, color: '#cfe6ee' });
  text('陡坎（天险）', X(0.52), Y(430) - 10, { size: 26, wt: 700, align: 'right', stroke: 4, color: C.gold });
  // 城墙（北墙在坎顶，南墙在台塬）
  const wall = (km, m) => { const x = X(km), y = Y(m); ctx.fillStyle = C.red; ctx.fillRect(x - 10, y - 46, 20, 46); ctx.fillStyle = '#ffb3a0'; ctx.fillRect(x - 12, y - 52, 24, 6); };
  wall(0.43, 452); wall(-0.55, 460);
  text('玉璧城', X(-0.06), Y(462) - 70, { size: 32, fam: SERIF, wt: 900, align: 'center', stroke: 5, color: '#ff9a7c' });
  // 地道：自北面坎下挖向城墙
  const dig = prog(t, T(1) - 0.2, T(1) + 2.0), fire = prog(t, CK('s3', 1, 2) + 0.2, A('s3', 2) + 0.6), out = prog(t, A('s3', 3) + 0.4, A('s3', 4) + 0.6);
  const trenchX = X(0.3); const tunnels = [[442, 0.484], [432, 0.503], [424, 0.519]];      // 起点在陡坎坎面上
  // 长沟（红）
  const tr = P(t, T(1) + 0.4, 0.8);
  ctx.fillStyle = '#120e0b'; ctx.fillRect(trenchX - 14, Y(458), 28, (Y(415) - Y(458)) * tr);
  ctx.strokeStyle = C.red; ctx.lineWidth = 4; ctx.strokeRect(trenchX - 14, Y(458), 28, (Y(415) - Y(458)) * tr);
  if (tr > 0.5) text('长沟 · 横截地道', trenchX + 26, Y(410) + 16, { size: 26, wt: 700, stroke: 4, color: '#ff9a7c', alpha: tr });
  tunnels.forEach(([m, startKm], i) => {
    const xs = X(startKm), xe = lerp(xs, trenchX - 14, clamp(dig * 1.15 - i * 0.08)); const y = Y(m);
    ctx.strokeStyle = '#06080a'; ctx.lineWidth = 12; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(xs, y); ctx.lineTo(xe, y); ctx.stroke();
    ctx.strokeStyle = C.xuanL; ctx.lineWidth = 2; ctx.stroke();
    if (fire > 0) {     // 火光：从沟口灌进地道，然后熄灭
      const f = clamp(fire * 1.3 - i * 0.1) * (1 - out); const xf = lerp(trenchX - 14, xs, clamp(fire * 1.2));
      const gg = ctx.createLinearGradient(trenchX, 0, xf, 0); gg.addColorStop(0, `rgba(255,200,90,${0.95 * f})`); gg.addColorStop(1, `rgba(255,90,20,${0.15 * f})`);
      ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.strokeStyle = gg; ctx.lineWidth = 10 + 4 * Math.sin(t * 20 + i); ctx.beginPath(); ctx.moveTo(trenchX - 14, y); ctx.lineTo(xf, y); ctx.stroke(); ctx.restore();
    }
  });
  if (dig > 0.1) text('地道', X(0.52) - 6, Y(446) - 22, { size: 26, wt: 700, stroke: 4, color: '#b9c8d8', align: 'right' });
  // 皮风箱示意
  const ab = fadeIO(t, CK('s3', 1, 2), A('s3', 4), 0.3, 0.5);
  if (ab > 0) { const x = trenchX + 50, y = Y(462) - 40; ctx.save(); ctx.globalAlpha *= ab; ctx.fillStyle = '#8a6a45'; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + 70, y - 22 - 8 * Math.sin(t * 6)); ctx.lineTo(x + 70, y + 22 + 8 * Math.sin(t * 6)); ctx.closePath(); ctx.fill(); ctx.restore(); text('皮风箱鼓风', x + 84, y, { size: 26, wt: 700, stroke: 4, color: '#ffcf8a', alpha: ab }); }
  note('示意：地道条数、走向、深度史书未载', x0 + 26, y1 - 30, 1, 'left', 22);
  ctx.restore();
}
