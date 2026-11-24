// ───────── scenes s05–s12 ─────────
function fadeBlack(ctx, a) { if (a > 0) { ctx.fillStyle = `rgba(4,6,9,${clamp(a)})`; ctx.fillRect(0, 0, W, H); } }
function plaque(ctx, x, y, name, sub, alpha = 1, { w = 150, h = 330, lit = 0 } = {}) {
  if (alpha <= 0) return; ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = 'rgba(20,30,38,.9)'; ctx.strokeStyle = rgba('#93a7b3', .5); ctx.lineWidth = 2;
  ctx.beginPath(); ctx.roundRect(x - w / 2, y, w, h, 4); ctx.fill(); ctx.stroke(); ctx.restore();
  if (lit) glow(ctx, x, y + h / 2, 200, '#d9c48f', .12 * lit * alpha);
  vtext(ctx, name, x + (sub ? 22 : 0), y + 64, 54, C.pale, { alpha, weight: 700, lh: 1.16 });
  if (sub) vtext(ctx, sub, x - 44, y + 48, 26, '#9fb0ba', { alpha: alpha * .95, weight: 500, lh: 1.12 });
}
function lampOnly(ctx, t, x, y, s, alpha = 1) { // oil lamp on a stand
  ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = '#05080b'; ctx.fillRect(x - s * .12, y, s * .24, s * 2.6); ctx.beginPath(); ctx.ellipse(x, y, s * .9, s * .22, 0, 0, 7); ctx.fill(); ctx.beginPath(); ctx.ellipse(x, y + s * 2.6, s * .8, s * .2, 0, 0, 7); ctx.fill(); ctx.restore();
  flame(ctx, x, y - s * .1, s * .62, t, 3, alpha);
}

// ══ s05 他的短处 ══
SC.s05 = (ctx, t, seg) => {
  const [L0, L1, L2, L3, L4, L5, L6, L7] = SEGL.s05; L6.noCard = true;
  const tB = L3.s - .4, tC = L6.s - .3, tD = L6.s + (L6.e - L6.s) * .62;
  if (t < tB + .5) { // A: gate, people in and out
    bgGrad(ctx, '#080d13', '#16232e', '#25333d', .5);
    ctx.drawImage(mountains('s5', { seed: 41, h: 1100, layers: [{ y: 820, amp: 160, col: '#1b2b37', freq: .003, fade: 260 }] }), 0, 0);
    const wy = 1000; cityWall(ctx, -20, W + 20, wy, 190, '#05080b', { crenel: 22 }); hall(ctx, 540, wy - 186, 430, 240, '#05080b', { tiers: 2 });
    ctx.fillStyle = '#d9c48f'; ctx.globalAlpha = .16; ctx.beginPath(); ctx.moveTo(488, wy + 4); ctx.lineTo(488, wy - 96); ctx.quadraticCurveTo(540, wy - 150, 592, wy - 96); ctx.lineTo(592, wy + 4); ctx.fill(); ctx.globalAlpha = 1;
    glow(ctx, 540, wy - 50, 120, C.fire, .22);
    ctx.fillStyle = '#0a1118'; ctx.fillRect(0, wy, W, H - wy);
    const r = rng(5), k = sstep(L1.s - .5, L2.s + 1, t), leave = sstep(L2.s + 1.5, L2.s + 4, t);
    for (let i = 0; i < 120; i++) { const ph = r(), sp = .09 + r() * .05, lane = r(), inn = i % 2 === 0; const u = ((t * sp + ph) % 1);
      if (inn) { const x = lerp(-40 + lane * 200, 520 + lane * 30, u), y = lerp(1260 - lane * 120, wy + 12, Math.pow(u, .8)); glow(ctx, x, y, 9, '#e6cf9c', .85 * k * sstep(0, .1, u) * (1 - sstep(.92, 1, u))); }
      else { const x = lerp(560 + lane * 30, 1120 - lane * 200, u), y = lerp(wy + 12, 1260 - lane * 120, Math.pow(u, 1.25)); glow(ctx, x, y, 9, '#9fb6c4', .8 * leave * sstep(0, .1, u) * (1 - sstep(.9, 1, u))); } }
    htext(ctx, '归者数千', 190, 1090, 40, '#e6cf9c', { alpha: win(t, L2.s + .3, tB, .6, .5), weight: 700, spacing: 4, outline: 5 });
    htext(ctx, '去者相继', 890, 1090, 40, '#a9bcc8', { alpha: win(t, L2.s + 2.2, tB, .6, .5), weight: 700, spacing: 4, outline: 5 });
    htext(ctx, '素奢豪，嗜声色', 540, 330, 36, '#b5c2c9', { alpha: win(t, L2.s + (L2.e - L2.s) * .68, tB, .6, .5), weight: 500, spacing: 5, outline: 5 });
    fadeBlack(ctx, sstep(tB - .3, tB + .4, t));
  } else if (t < tC + .5) { // B: three names
    bgGrad(ctx, '#070b10', '#101a23', '#16222b', .5);
    const a = sstep(tB + .4, tB + 1.1, t); const d = L3.e - L3.s;
    plaque(ctx, 540, 340, '刘琨', '并州刺史', a, { lit: 1 });
    plaque(ctx, 250, 720, '徐润', '晋阳令·以音律得幸', a * sstep(L3.s + .3, L3.s + 1.2, t), { h: 380 });
    plaque(ctx, 830, 720, '令狐盛', '护军·性亢直', a * sstep(L3.s + d * .28, L3.s + d * .28 + .8, t), { h: 380 });
    const a1 = sstep(L3.s + d * .38, L3.s + d * .5, t), a2 = sstep(L3.s + d * .58, L3.s + d * .7, t);
    arrow(ctx, curve([800, 720], [760, 600], [640, 560], 20), a1, '#a9bcc8', 5, .9, 16); htext(ctx, '劝除徐润', 850, 630, 30, '#a9bcc8', { alpha: a1, weight: 600, outline: 5 });
    arrow(ctx, curve([280, 720], [320, 600], [440, 560], 20), a2, '#d9c48f', 5, .9, 16); htext(ctx, '反诬：盛将劝公称帝', 240, 630, 30, '#d9c48f', { alpha: a2, weight: 600, outline: 5 });
    const cut = sstep(L3.s + d * .84, L3.s + d * .93, t);
    stroke(ctx, curve([720, 730], [840, 900], [950, 1100], 30), 26, C.red, .92, { taper: .7, u1: cut, seed: 4 });
    htext(ctx, '琨不之察，便杀之', 830, 1150, 30, '#c9837b', { alpha: sstep(L3.s + d * .9, L3.e, t) * (1 - sstep(L4.s - .2, L4.s + .4, t)), weight: 600, outline: 5 });
    const dim = sstep(L4.s - .3, L4.s + .6, t); fadeBlack(ctx, dim * .9);
    if (dim > 0) { lampOnly(ctx, t, 430, 800, 46, dim); glow(ctx, 430, 780, 420, C.fire, .12 * dim); figure(ctx, 700, 1010, 330, { sit: true, facing: -1, color: '#020304', alpha: dim }); vtext(ctx, '琨母', 850, 640, 38, '#b5c2c9', { alpha: dim, weight: 600 }); }
    fadeBlack(ctx, sstep(tC - .3, tC + .4, t));
  } else if (t < tD + .4) { // C: map — the son defects, the raid
    const cam = mkCam(112.2, 37.0, 250); drawMap(ctx, cam); enemyBlots(ctx, cam, 1, t, ENEMY_BING);
    const u = (t - tC) / (tD - tC);
    const jp = proj(cam, MAP.city.jinyang); glow(ctx, jp[0], jp[1], 240, '#d9c48f', .22 * (1 - sstep(.75, .98, u)));
    cityDot(ctx, cam, 'jinyang', '晋阳', { lit: 1 - sstep(.75, .98, u), size: 42 }); cityDot(ctx, cam, 'pingyang', '刘聪', { dx: -16, color: '#aab6bd', sub: '平阳' });
    const flee = projAll(cam, smoothPath([MAP.city.jinyang, [112.3, 37.1], [111.9, 36.5], MAP.city.pingyang], 8));
    dashed(ctx, flee, sstep(.05, .38, u), '#a9bcc8', 3.5, [8, 10], .9); const fp = pointAt(flee, .5); htext(ctx, '令狐泥奔刘聪', fp[0] - 22, fp[1] - 10, 30, '#a9bcc8', { alpha: sstep(.12, .3, u), align: 'right', weight: 600, outline: 5 });
    const raid = projAll(cam, smoothPath([MAP.city.pingyang, [111.9, 36.9], [112.4, 37.4], MAP.city.jinyang], 8).map(p => [p[0] + .12, p[1]]));
    arrow(ctx, raid, sstep(.45, .85, u), '#07090c', 13, .95, 30); arrow(ctx, raid, sstep(.45, .85, u), C.red, 4, .8, 0);
    htext(ctx, '公元 312 年 · 永嘉六年', 540, 330, 36, '#b5c2c9', { alpha: win(t, tC + .5, tD, .5, .5), weight: 500, spacing: 4, outline: 5 });
    fadeBlack(ctx, Math.max(1 - sstep(tC + .3, tC + .9, t), sstep(tD - .25, tD + .25, t)));
  } else { // D: one lamp
    ctx.fillStyle = '#04070a'; ctx.fillRect(0, 0, W, H);
    const a = sstep(tD + .3, tD + 1.6, t) * (1 - .35 * sstep(L7.s, seg.e, t));
    lampOnly(ctx, t, 430, 820, 52, a);
    vtext(ctx, '琨父母并遇害', 690, 600, 64, '#e2dccb', { fam: F.brush, weight: 400, alpha: a, reveal: sstep(tD + .8, tD + 2.6, t), lh: 1.2 });
    const b = win(t, tD + 2.2, L7.s + .5, .8, .8);
    htext(ctx, '《晋书》：琨父母并遇害', 540, 1170, 30, '#9fb0ba', { alpha: b, weight: 500, outline: 4 });
    htext(ctx, '《资治通鉴》卷八十八：壬子，令狐泥杀琨父母', 540, 1222, 30, '#9fb0ba', { alpha: b * sstep(tD + 2.8, tD + 3.6, t), weight: 500, outline: 4 });
  }
};

// ══ s06 借来的兵 ══
SC.s06 = (ctx, t, seg) => {
  const [L0, L1, L2, L3, L4, L5, L6, L7] = SEGL.s06;
  const tB = L3.s - .5, tC = L5.s - .5;
  if (t < tB + .4) { // A: Tuoba comes & goes; then two capitals
    const camA = mkCam(112.6, 38.6, 190, 540, 800); const cam = t < L2.s - .5 ? camA : camLerp(camA, CAM_ALL, (t - L2.s + .5) / 2.5);
    drawMap(ctx, cam); enemyBlots(ctx, cam, 1, t, ENEMY_BING.slice(0, 2).concat([ENEMY_BING[4]]));
    const d = L0.e - L0.s, come = sstep(L0.s + d * .35, L0.s + d * .62, t), go = sstep(L0.s + d * .8, L0.e + .6, t), oldMap = 1 - sstep(L2.s - .5, L2.s + 1, t);
    regionLabel(ctx, cam, [112.9, 40.55], '拓跋部', 44, sstep(L0.s + .5, L0.s + 1.4, t) * oldMap, '#b9c7cf'); regionLabel(ctx, cam, [112.9, 40.2], '代地 · 鲜卑', 26, sstep(L0.s + 1.4, L0.s + 2.2, t) * oldMap, '#8fa0aa');
    const path = projAll(cam, smoothPath([[113.2, 40.0], [112.9, 39.3], [112.7, 38.6], [112.57, 37.95]], 8));
    arrow(ctx, path, come, '#b9c7cf', 12, .9 * (1 - go) * oldMap, 28);
    dashed(ctx, path.slice().reverse(), go, '#b9c7cf', 3.5, [8, 12], .8 * oldMap * (1 - sstep(L1.e, L2.s, t)));
    cityDot(ctx, cam, 'jinyang', '晋阳', { lit: .3 + .7 * come, size: 40 });
    cityDot(ctx, cam, 'pingyang', '刘聪', { dx: -16, color: '#aab6bd', sub: '平阳', alpha: oldMap });
    // borrowed bar
    const ba = win(t, L1.s - .2, L2.s - .6, .6, .6); if (ba > 0) { const x0 = 190, y0 = 1090, w = 700, k = easeOut((t - L1.s) / 1.6);
      ctx.save(); ctx.globalAlpha = ba; ctx.fillStyle = '#d9c48f'; ctx.fillRect(x0, y0, w * .3, 26); ctx.fillStyle = '#8fa9b8'; ctx.fillRect(x0 + w * .3 + 4, y0, (w * .7 - 4) * k, 26); ctx.restore();
      htext(ctx, '自己的', x0, y0 - 34, 30, '#d9c48f', { align: 'left', alpha: ba, weight: 600, outline: 5 }); htext(ctx, '借来的', x0 + w, y0 - 34, 30, '#a9c0cd', { align: 'right', alpha: ba * k, weight: 600, outline: 5 });
      htext(ctx, '示意', x0 + w + 16, y0 + 13, 22, '#7f8e97', { align: 'left', alpha: ba, weight: 500 }); }
    // two capitals
    const cap = sstep(L2.s + .3, L2.s + 1.5, t); if (cap > 0) { cityDot(ctx, cam, 'luoyang', '洛阳', { alpha: cap, dx: 16, sq: true, dim: 1, sub: '311 年陷落' }); cityDot(ctx, cam, 'changan', '长安', { alpha: sstep(L2.s + 1.6, L2.s + 2.6, t), dx: -16, sq: true, lit: .8, sub: '愍帝' });
      const ln_ = projAll(cam, [MAP.city.jinyang, [111.2, 36.4], [109.8, 35.2], MAP.city.changan]); dashed(ctx, smoothPath(ln_, 8), sstep(L2.s + 3, L2.e + .3, t), '#d9c48f', 3, [5, 12], .8); htext(ctx, '上表', lerp(ln_[1][0], ln_[2][0], .5) - 20, lerp(ln_[1][1], ln_[2][1], .5), 30, '#d9c48f', { align: 'right', alpha: sstep(L2.s + 3.6, L2.e, t), weight: 600, outline: 5 }); }
    fadeBlack(ctx, sstep(tB - .3, tB + .4, t));
  } else if (t < tC + .4) { // B: eight provinces
    bgGrad(ctx, '#070b10', '#0f1922', '#15212a', .5);
    const a = sstep(tB + .4, tB + 1.1, t); htext(ctx, '东北八州', 540, 400, 76, '#e2dccb', { fam: F.brush, weight: 400, alpha: a, spacing: 26 });
    const d = L3.e - L3.s, order = [0, 3, 5, 1, 7, 2, 4]; const r = rng(9);
    for (let i = 0; i < 8; i++) { const cx = 177 + (i % 4) * 242, cy = 640 + Math.floor(i / 4) * 250, me = i === 6; const oi = order.indexOf(i);
      const off = me ? 0 : sstep(L3.s + d * (.22 + oi * .045), L3.s + d * (.22 + oi * .045) + .5, t);
      ctx.save(); ctx.globalAlpha = a; blot(ctx, cx, cy, 128, '#d9c48f', .5 * (1 - off) + (me ? .25 * sstep(L3.s + d * .6, L3.e, t) : 0), 1 + i % 3, i); blot(ctx, cx, cy, 128, '#03050700'.slice(0, 7), .9 * off, 1 + (i + 1) % 3, i * 2);
      ctx.strokeStyle = rgba('#93a7b3', .35); ctx.lineWidth = 1.5; ctx.strokeRect(cx - 104, cy - 104, 208, 208); ctx.restore();
      if (!me && off > 0) { stroke(ctx, [[cx - 60, cy - 60], [cx + 60, cy + 60]], 9, '#020304', .9 * a, { taper: .6, u1: off }); stroke(ctx, [[cx + 60, cy - 60], [cx - 60, cy + 60]], 9, '#020304', .9 * a, { taper: .6, u1: sstep(.4, 1, off) }); }
      if (me) { htext(ctx, '并州', cx, cy - 8, 60, '#1a1408', { fam: F.brush, weight: 400, alpha: a }); } }
    const only = sstep(L3.s + d * .62, L3.e, t); htext(ctx, '存者唯臣', 540, 1150, 84, '#ecd9a4', { fam: F.brush, weight: 400, alpha: a * only, reveal: only, spacing: 22 });
    htext(ctx, '勒灭其七', 540, 1048, 40, '#9fb0ba', { alpha: a * sstep(L3.s + d * .3, L3.s + d * .5, t) * (1 - only * .4), weight: 600, spacing: 10, outline: 5 });
    fadeBlack(ctx, sstep(tC - .3, tC + .4, t));
  } else { // C: the vice
    const cam = mkCam(113.0, 37.0, 215, 540, 760); drawMap(ctx, cam); enemyBlots(ctx, cam, 1, t, ENEMY_BING);
    const d = L5.e - L5.s, end = sstep(L7.s - .3, L7.s + 1.5, t);
    const jp = cityDot(ctx, cam, 'jinyang', '晋阳', { lit: 1, size: 42 }); cityDot(ctx, cam, 'pingyang', '刘聪', { dx: -16, color: '#aab6bd', sub: '平阳' }); cityDot(ctx, cam, 'xiangguo', '石勒', { dx: 16, dy: 26, color: '#aab6bd', sub: '襄国' });
    htext(ctx, '孑然', jp[0], jp[1] - 64, 40, '#d9c48f', { alpha: win(t, L5.s + .2, L5.s + d * .3, .4, .5), weight: 600, spacing: 8, outline: 5 });
    const atk = projAll(cam, smoothPath([[112.45, 37.7], [112.1, 37.1], [111.75, 36.5], [111.55, 36.2]], 8)), rear = projAll(cam, smoothPath([[114.4, 37.1], [113.8, 37.5], [113.2, 37.75], [112.7, 37.85]], 8));
    const a1 = sstep(L5.s + d * .5, L5.s + d * .66, t), a2 = sstep(L5.s + d * .66, L5.s + d * .82, t), hold = 1 - end;
    arrow(ctx, atk, a1 * (1 - .45 * a2), '#d9c48f', 10, .92 * hold, 26); htext(ctx, '进讨', atk[12][0] - 26, atk[12][1], 34, '#d9c48f', { align: 'right', alpha: a1 * hold, weight: 700, outline: 5 });
    arrow(ctx, rear, a2, '#07090c', 14, .95 * hold, 30); arrow(ctx, rear, a2, C.red, 4, .75 * hold, 0); htext(ctx, '袭其后', rear[10][0], rear[10][1] - 44, 34, '#c9837b', { alpha: a2 * hold, weight: 700, outline: 5 });
    const st = win(t, L5.s + d * .3, L5.s + d * .52, .4, .4); ctx.save(); ctx.globalAlpha = st * .8; ctx.strokeStyle = '#d9c48f'; ctx.lineWidth = 3; ctx.setLineDash([6, 8]); ctx.beginPath(); ctx.arc(jp[0], jp[1], 60, 0, 7); ctx.stroke(); ctx.restore(); htext(ctx, '自守', jp[0] - 80, jp[1] + 6, 34, '#d9c48f', { align: 'right', alpha: st, weight: 700, outline: 5 });
    if (end > 0) { const al = projAll(cam, [[112.6, 38.05], [112.8, 39.2], [113.0, 40.3]]), ho = projAll(cam, [[112.6, 37.6], [112.9, 36.2], [112.5, 34.9]]);
      dashed(ctx, smoothPath(al, 6), end, '#b9c7cf', 3.5, [8, 10], .9); htext(ctx, '盟友', al[1][0] + 24, al[1][1], 40, '#b9c7cf', { align: 'left', alpha: end, weight: 700, outline: 6 });
      dashed(ctx, smoothPath(ho, 6), sstep(.3, 1, end), '#6c7880', 3, [3, 14], .7); const hp = ho[1]; htext(ctx, '后援', hp[0] + 26, hp[1], 40, '#7c8890', { align: 'left', alpha: sstep(.4, 1, end), weight: 700, outline: 6 });
      const x = sstep(L7.s + 2.0, L7.s + 2.6, t); stroke(ctx, [[hp[0] + 16, hp[1] + 4], [hp[0] + 122, hp[1] - 2]], 7, C.red, .9, { taper: .5, u1: x }); }
    fadeBlack(ctx, 1 - sstep(tC + .3, tC + 1, t));
  }
};

// ══ s07 等不起 ══
SC.s07 = (ctx, t, seg) => {
  const [L0, L1, L2, L3, L4, L5, L6] = SEGL.s07;
  const camA = mkCam(113.2, 38.5, 205, 540, 780), camB = mkCam(113.3, 37.8, 240, 540, 760);
  let cam = t < L1.s ? camA : camLerp(camA, camB, (t - L1.s) / 4); if (t > L6.s - .8) cam = camLerp(camB, CAM_ALL, (t - L6.s + .8) / 3);
  const shake = win(t, L3.s, L4.e, .2, 1.2); ctx.save(); ctx.translate(shake * 5 * Math.sin(t * 31), shake * 4 * Math.sin(t * 27 + 1));
  drawMap(ctx, cam); enemyBlots(ctx, cam, 1, t, [ENEMY_BING[0], ENEMY_BING[1], ENEMY_BING[4]]);
  const late = sstep(L6.s - .8, L6.s + 1, t);
  // herd/people particles
  const d0 = L0.e - L0.s, flow = sstep(L0.s + d0 * .3, L0.e + .5, t), march = sstep(L2.s - .2, L2.e + .3, t), die = sstep(L2.s + (L2.e - L2.s) * .6, L3.s + .8, t);
  const A = proj(cam, [113.3, 40.1]), B = proj(cam, [112.75, 38.15]), Cc = proj(cam, [113.75, 37.55]); const r = rng(21);
  for (let i = 0; i < 260; i++) { const ph = r(), ox = (r() - .5), oy = (r() - .5), big = i % 4 === 0; const u = clamp(flow * 1.5 - ph * .5), m = clamp(march * 1.4 - ph * .4);
    let x = lerp(A[0], B[0], easeIO(u)) + ox * cam.scale * (.5 + .4 * Math.sin(ph * 9)), y = lerp(A[1], B[1], easeIO(u)) + oy * cam.scale * .45;
    x = lerp(x, Cc[0] + ox * cam.scale * .22, easeIO(m)); y = lerp(y, Cc[1] + oy * cam.scale * .2, easeIO(m));
    const a = sstep(0, .08, u) * (1 - clamp(die * 1.6 - ph * .6)) * (1 - late); if (a > 0) glow(ctx, x, y, big ? 9 : 6, big ? '#e6cf9c' : '#b9c7cf', .8 * a); }
  htext(ctx, '部众三万 · 马牛羊十万', 540, 330, 38, '#d9c48f', { alpha: win(t, L0.s + d0 * .35, L1.s, .6, .6), weight: 600, spacing: 4, outline: 5 });
  htext(ctx, '公元 316 年 · 建兴四年', 540, 384, 30, '#9fb0ba', { alpha: win(t, L0.s + .2, L1.s, .6, .6), weight: 500, spacing: 4, outline: 5 });
  regionLabel(ctx, cam, [114.4, 39.75], '拓跋部内乱', 32, win(t, L0.s + .6, L1.s + 1, .6, 1), '#b9c7cf');
  cityDot(ctx, cam, 'jinyang', '晋阳', { lit: (.5 + .5 * flow) * (1 - .8 * die), size: 40 });
  cityDot(ctx, cam, 'xiangguo', '石勒', { dx: 16, color: '#aab6bd', sub: '襄国', alpha: sstep(L1.s, L1.s + 1, t) });
  cityDot(ctx, cam, 'leping', '乐平', { dx: 14, dy: -26, size: 30, alpha: sstep(L1.s + .5, L1.s + 1.5, t) * (1 - late) });
  const sl = projAll(cam, smoothPath([[114.45, 37.1], [114.2, 37.35], [113.95, 37.5]], 8)); arrow(ctx, sl, sstep(L1.s + .3, L1.s + 1.8, t), '#07090c', 12, .95 * (1 - late), 26);
  // ambush closes
  const amb = sstep(L2.s + (L2.e - L2.s) * .45, L3.s + .3, t) * (1 - late);
  if (amb > 0) { blot(ctx, Cc[0] - 20, Cc[1] - cam.scale * .5 * (1 - amb), cam.scale * .5, '#020304', .9 * amb, 2, 1); blot(ctx, Cc[0] + 20, Cc[1] + cam.scale * .5 * (1 - amb), cam.scale * .5, '#020304', .9 * amb, 3, 2); glow(ctx, Cc[0], Cc[1], cam.scale * .45, C.red, .5 * win(t, L2.e - .3, L4.e, .5, 2)); htext(ctx, '设伏', Cc[0] + cam.scale * .5, Cc[1] + 12, 34, '#c9837b', { align: 'left', alpha: win(t, L2.s + (L2.e - L2.s) * .5, L4.e, .4, 1), weight: 700, outline: 5 }); }
  regionLabel(ctx, cam, [112.2, 38.7], '并州', 54, (1 - late) * (1 - .6 * die), '#c8bfa6');
  // two capitals go dark
  if (late > 0) { const off = sstep(L6.s + 1.6, L6.s + 3.2, t);
    cityDot(ctx, cam, 'luoyang', '洛阳', { alpha: late, dx: 16, sq: true, dim: 1, sub: '311 年陷落' });
    cityDot(ctx, cam, 'changan', '长安', { alpha: late, dx: -16, sq: true, lit: .9 * (1 - off), dim: off > .6 ? 1 : 0, sub: off > .5 ? '316 年冬陷落' : '愍帝' });
    const jp = proj(cam, MAP.city.jinyang); const bk = sstep(L6.s + 4, L6.e, t); blot(ctx, jp[0], jp[1] + 150, 300 * bk, '#020304', .8 * bk, 1, .5); }
  ctx.restore();
};

// ══ s08 投奔 ══
SC.s08 = (ctx, t, seg) => {
  const [L0, L1, L2, L3, L4, L5] = SEGL.s08;
  const camA = mkCam(114.7, 38.9, 178, 540, 760), camY = mkCam(116.9, 39.6, 300, 540, 760);
  let cam = t < L1.s - .5 ? camA : t < L4.s - .8 ? camLerp(camA, mkCam(115.6, 35.9, 86, 540, 760), (t - L1.s + .5) / 3.5) : camLerp(mkCam(115.6, 35.9, 86, 540, 760), camY, (t - L4.s + .8) / 3);
  drawMap(ctx, cam); enemyBlots(ctx, cam, 1, t, [[112.5, 37.6, 1.5, 1, 0], [114.5, 37.0, 1.2, 2, 0], [111.2, 36.2, 1.1, 3, 0]]);
  const d0 = L0.e - L0.s, go = sstep(L0.s + d0 * .45, L0.s + d0 * .8, t), inA = t < L1.s + 2;
  const route = projAll(cam, smoothPath([MAP.city.jinyang, [113.3, 38.6], [114.2, 39.3], MAP.city.feihu, [115.6, 39.6], MAP.city.ji], 8));
  dashed(ctx, route, go, '#d9c48f', 3.5, [9, 11], .9 * (inA ? 1 : .5)); const rp = pointAt(route, go); glow(ctx, rp[0], rp[1], 26, '#e6cf9c', .9 * (go > 0 && go < 1 ? 1 : 0));
  cityDot(ctx, cam, 'jinyang', '晋阳', { dim: 1, alpha: 1 - sstep(L4.s - .8, L4.s, t), sub: inA ? '并州已失' : '' });
  regionLabel(ctx, cam, [116.0, 40.5], '幽州 · 段部', 36, sstep(L0.s + d0 * .12, L0.s + d0 * .25, t) * (t < L4.s ? 1 : .0), '#b9c7cf');
  cityDot(ctx, cam, 'ji', '蓟', { lit: sstep(.7, 1, go), size: 42, dx: 16, sub: inA ? '今北京一带' : '', alpha: sstep(L0.s + d0 * .3, L0.s + d0 * .45, t) });
  const bro = win(t, L0.s + d0 * .85, L1.s + 1, .5, .8); if (bro > 0) { const jp = proj(cam, MAP.city.ji); htext(ctx, '刘琨 ═ 段匹磾', jp[0] - 30, jp[1] - 70, 34, '#e6cf9c', { alpha: bro, weight: 700, outline: 6 }); htext(ctx, '结婚，约为兄弟', jp[0] - 30, jp[1] - 116, 26, '#9fb0ba', { alpha: bro, weight: 500, outline: 5 }); }
  // Jiankang + Wen Jiao's line
  const jk = sstep(L1.s + 1.5, L1.s + 2.8, t) * (1 - sstep(L4.s - .8, L4.s, t));
  if (jk > 0) { cityDot(ctx, cam, 'jiankang', '建康', { alpha: jk, lit: .9, size: 42, dx: 16, sub: '今南京 · 江东朝廷' }); cityDot(ctx, cam, 'luoyang', '洛阳', { alpha: jk * .8, dim: 1, sq: true, dx: -16 }); cityDot(ctx, cam, 'changan', '长安', { alpha: jk * .8, dim: 1, sq: true, dx: -16 });
    const d1 = L1.e - L1.s; const wj = projAll(cam, smoothPath([MAP.city.ji, [117.4, 38.2], [118.0, 36.3], [118.2, 34.3], MAP.city.jiankang], 10)); const u = sstep(L1.s + d1 * .6, L3.s + 1.5, t);
    dashed(ctx, wj, u, '#e6cf9c', 3, [4, 9], .95 * jk); const wp = pointAt(wj, u); glow(ctx, wp[0], wp[1], 20, '#f0dba8', .9 * jk);
    htext(ctx, '温峤', wp[0] + 22, wp[1] - 6, 32, '#e6cf9c', { align: 'left', alpha: jk * sstep(L1.s + d1 * .65, L1.s + d1 * .8, t), weight: 700, outline: 5 });
    // tries to return — refused
    const d3 = L3.e - L3.s, back = sstep(L3.s + d3 * .55, L3.s + d3 * .8, t); if (back > 0) { const rb = projAll(cam, smoothPath([[118.65, 32.25], [118.5, 33.0], [118.4, 33.6]], 6)); dashed(ctx, rb, back, '#a9bcc8', 3, [4, 8], .9 * jk); const e = rb[rb.length - 1]; const bar = sstep(L3.s + d3 * .78, L3.s + d3 * .9, t);
      stroke(ctx, [[e[0] - 46, e[1] - 6], [e[0] + 46, e[1] - 10]], 9, C.red, .9 * jk, { taper: .5, u1: bar }); htext(ctx, '屡求返命，朝廷不许', e[0] - 60, e[1] - 12, 28, '#c9a39c', { align: 'right', alpha: bar * jk, weight: 600, outline: 5 }); } }
  // Duan clans gather & scatter
  const g = sstep(L4.s, L4.s + 1, t);
  if (g > 0) { const d4 = L4.e - L4.s, G = [116.3, 39.35]; const come = sstep(L4.s + .6, L4.s + d4 * .4, t), leave = sstep(L4.s + d4 * .5, L4.s + d4 * .75, t);
    cityDot(ctx, cam, 'ji', '', { lit: 1 }); const gp = proj(cam, G); ctx.save(); ctx.globalAlpha = g * .9; ctx.strokeStyle = '#d9c48f'; ctx.lineWidth = 2.5; ctx.setLineDash([5, 7]); ctx.beginPath(); ctx.arc(gp[0], gp[1], 40, 0, 7); ctx.stroke(); ctx.restore(); htext(ctx, '固安 · 会师', gp[0], gp[1] + 70, 30, '#d9c48f', { alpha: g, weight: 600, outline: 5 });
    const mine = projAll(cam, [MAP.city.ji, [116.33, 39.6], [116.31, 39.47]]); arrow(ctx, smoothPath(mine, 6), come, '#e6cf9c', 9, .95 * g, 22); htext(ctx, '刘琨 · 段匹磾', proj(cam, MAP.city.ji)[0] - 26, proj(cam, MAP.city.ji)[1] - 8, 32, '#e6cf9c', { align: 'right', alpha: g, weight: 700, outline: 6 });
    [['疾陆眷（兄）', [118.6, 40.0], [117.3, 39.9]], ['涉复辰（叔）', [118.5, 39.5], [117.3, 39.45]], ['末柸（从弟）', [118.3, 39.0], [117.2, 39.0]]].forEach(([nm, from, mid], i) => {
      const pth = projAll(cam, smoothPath([from, mid, [116.5 + i * .02, 39.42 - i * .05]], 8)); const u = clamp(come - leave * .85); arrow(ctx, pth, .15 + .85 * u, '#9fb6c4', 9, .95 * g, 22);
      htext(ctx, nm, pth[0][0] - 6, pth[0][1] - 30, 30, '#b9c7cf', { align: 'center', alpha: g, weight: 600, outline: 5 }); });
    { const sa = win(t, L4.s + d4 * .72, L5.s + 1.5, .6, .6); htext(ctx, '《资治通鉴》：以父兄而从子弟，耻也', 540, 1010, 28, '#9fb0ba', { alpha: sa, weight: 500, outline: 4 }); htext(ctx, '《晋书》：末波纳勒厚赂，独不进', 540, 1056, 28, '#9fb0ba', { alpha: sa * sstep(L4.s + d4 * .82, L4.s + d4 * .95, t), weight: 500, outline: 4 }); }
    htext(ctx, '各引兵还', proj(cam, [117.7, 38.55])[0], proj(cam, [117.7, 38.55])[1], 36, '#c9a39c', { alpha: sstep(L4.s + d4 * .7, L4.s + d4 * .85, t), weight: 700, spacing: 6, outline: 6 });
    const fam = sstep(L5.s + (L5.e - L5.s) * .35, L5.s + (L5.e - L5.s) * .6, t); if (fam > 0) { htext(ctx, '不是一个国家，是一个家族', 540, 330, 40, '#e2dccb', { alpha: fam, weight: 700, spacing: 4, outline: 6 }); } }
};

// ══ s09 一封信 ══
function letterIcon(ctx, x, y, s, rot = 0, alpha = 1, open = 0) {
  ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(x, y); ctx.rotate(rot); const w = s * (1 + open * 1.6), h = s * 1.5;
  ctx.fillStyle = '#d6cfba'; ctx.shadowColor = 'rgba(0,0,0,.6)'; ctx.shadowBlur = 18; ctx.fillRect(-w / 2, -h / 2, w, h); ctx.shadowBlur = 0;
  ctx.strokeStyle = 'rgba(30,26,20,.75)'; ctx.lineWidth = Math.max(1.5, s * .035); const n = Math.round(3 + open * 5); for (let i = 0; i < n; i++) { const lx = w / 2 - (i + .7) * (w / (n + .4)); ctx.beginPath(); ctx.moveTo(lx, -h * .38); ctx.lineTo(lx, h * (.1 + .28 * hash(i + 3))); ctx.stroke(); }
  ctx.restore();
}
function interior(ctx, t, { lampA = 1, third = 0, dark = 0 } = {}) {
  bgGrad(ctx, '#06090d', '#0e161d', '#151d22', .55);
  ctx.fillStyle = '#0a0f14'; ctx.fillRect(0, 1040, W, H - 1040);
  // lattice window hints
  ctx.save(); ctx.globalAlpha = .22; ctx.strokeStyle = '#6c8291'; ctx.lineWidth = 3; for (let k = 0; k < 2; k++) { const x0 = k ? 760 : 100; for (let i = 0; i <= 4; i++) { ctx.beginPath(); ctx.moveTo(x0 + i * 55, 380); ctx.lineTo(x0 + i * 55, 700); ctx.stroke(); } for (let j = 0; j <= 4; j++) { ctx.beginPath(); ctx.moveTo(x0, 380 + j * 80); ctx.lineTo(x0 + 220, 380 + j * 80); ctx.stroke(); } } ctx.restore();
  glow(ctx, 540, 900, 520, C.fire, .2 * lampA * (.9 + .1 * noise1(t * 5, 1)));
  // table
  ctx.fillStyle = '#05080b'; ctx.fillRect(330, 1010, 420, 22); ctx.fillRect(350, 1032, 16, 70); ctx.fillRect(714, 1032, 16, 70);
  figure(ctx, 205, 1108, 400, { sit: true, facing: 1, color: '#030506', robeW: 1.05 }); figure(ctx, 875, 1108, 400, { sit: true, facing: -1, color: '#030506', robeW: 1.05 });
  if (third > 0) figure(ctx, 1000, 1100, 460, { facing: -1, color: '#020304', alpha: third });
  lampOnly(ctx, t, 665, 920, 30, lampA);
}
SC.s09 = (ctx, t, seg) => {
  const [L0, L1, L2, L3, L4, L5, L6, L7, L8] = SEGL.s09; const tB = L2.s - .5;
  if (t < tB + .4) { // A: the letter travels and is intercepted
    bgGrad(ctx, '#06090e', '#0e1820', '#16222b', .5);
    ctx.drawImage(mountains('s9', { seed: 51, h: 1100, layers: [{ y: 640, amp: 170, col: '#182733', freq: .003, fade: 300 }, { y: 1000, amp: 130, col: '#0d161d', freq: .0045, fade: 240 }] }), 0, 0);
    const path = smoothPath([[900, 470], [760, 560], [640, 700], [520, 820], [380, 930], [230, 1040]], 10);
    const d0 = L0.e - L0.s, u = sstep(L0.s + d0 * .55, L1.s + .4, t) * .56;
    htext(ctx, '段末柸营', 900, 400, 36, '#b9c7cf', { alpha: sstep(L0.s + .5, L0.s + 1.3, t), weight: 700, outline: 5 }); glow(ctx, 900, 470, 70, C.fire, .35);
    htext(ctx, '刘琨 · 征北小城', 240, 1110, 34, '#d9c48f', { alpha: sstep(L0.s + 1.2, L0.s + 2, t), weight: 700, outline: 5 }); glow(ctx, 230, 1040, 60, '#d9c48f', .3);
    htext(ctx, '俘刘群，使作书，请琨为内应', 540, 300, 32, '#9fb0ba', { alpha: win(t, L0.s + d0 * .4, L1.s, .6, .5), weight: 500, spacing: 3, outline: 5 });
    dashed(ctx, path, 1, '#6c7880', 2.5, [4, 12], .5); dashed(ctx, path, u, '#e6cf9c', 3.5, [8, 9], .9);
    const p = pointAt(path, u), cut = sstep(L1.s + .3, L1.s + .9, t);
    // patrol slash
    stroke(ctx, curve([420, 640], [600, 760], [760, 900], 24), 22, '#05080b', .95, { taper: .6, u1: cut }); stroke(ctx, curve([420, 640], [600, 760], [760, 900], 24), 5, C.red, .7, { taper: .6, u1: cut });
    htext(ctx, '匹磾逻骑', 800, 930, 34, '#c9a39c', { alpha: cut, weight: 700, outline: 5 });
    letterIcon(ctx, p[0], p[1] - 10, 46 + 30 * cut, -.25 + .1 * Math.sin(t * 2), sstep(L0.s + d0 * .5, L0.s + d0 * .6, t));
    fadeBlack(ctx, sstep(tB - .3, tB + .4, t));
  } else { // B: the room
    const dk = sstep(L6.s - .5, L6.s + 1.5, t), third = sstep(L5.s + (L5.e - L5.s) * .5, L6.s, t), bars = sstep(L8.s + (L8.e - L8.s) * .32, L8.s + (L8.e - L8.s) * .55, t);
    const push = 1 + .04 * easeIO((t - tB) / (seg.e - tB)); ctx.save(); ctx.translate(540, 900); ctx.scale(push, push); ctx.translate(-540, -900);
    interior(ctx, t, { lampA: 1 - .55 * dk, third });
    letterIcon(ctx, 520, 1000, 60, .04, 1, 1); glow(ctx, 520, 995, 120, '#e6dcc0', .12 + .12 * dk);
    ctx.restore();
    vtext(ctx, '刘琨', 110, 560, 40, '#d9c48f', { alpha: win(t, tB + .8, L6.s, .6, .8), weight: 700, outline: 5 }); vtext(ctx, '段匹磾', 800, 520, 40, '#b9c7cf', { alpha: win(t, tB + 1.4, L6.s, .6, .8), weight: 700, outline: 5 });
    vtext(ctx, '叔军', 1010, 470, 40, '#b9c7cf', { alpha: win(t, L5.s + (L5.e - L5.s) * .6, L8.s, .6, .8), weight: 700, outline: 5 });
    htext(ctx, '匹磾雅重琨，初无害琨志，将听还屯', 540, 320, 32, '#9fb0ba', { alpha: win(t, L5.s + .2, L5.s + (L5.e - L5.s) * .6, .5, .5), weight: 500, spacing: 2, outline: 5 });
    fadeBlack(ctx, dk * .42);
    if (bars > 0) { ctx.save(); ctx.fillStyle = '#020304'; for (let i = 0; i < 5; i++) { const x = 40 + i * 78; ctx.globalAlpha = sstep(i * .12, i * .12 + .5, bars); ctx.fillRect(x, 0, 20, H); } ctx.restore(); htext(ctx, '匹磾遂留琨', 720, 330, 44, '#e2dccb', { alpha: sstep(.5, 1, bars), weight: 700, spacing: 8, outline: 6 }); }
    fadeBlack(ctx, 1 - sstep(tB + .3, tB + 1, t));
  }
};

// ══ s10 狱中 ══
const POEM = ['功业未及建', '夕阳忽西流', '何意百炼刚', '化为绕指柔'];
SC.s10 = (ctx, t, seg) => {
  const [L0, L2, L3, L4, L5, L6] = SEGL.s10; const death = sstep(L6.s + (L6.e - L6.s) * .55, L6.e + 1.2, t); const d0 = L0.e - L0.s;
  ctx.fillStyle = '#05080b'; ctx.fillRect(0, 0, W, H);
  // window + light shaft
  const wx = 700, wy = 330, ww = 210, wh = 250, la = (1 - death) * (.85 + .15 * noise1(t * .8, 4));
  ctx.save(); ctx.globalAlpha = .34 * la; const g = ctx.createLinearGradient(wx, wy, 300, 1300); g.addColorStop(0, '#b9cbd6'); g.addColorStop(1, 'rgba(185,203,214,0)'); ctx.fillStyle = g;
  ctx.beginPath(); ctx.moveTo(wx, wy); ctx.lineTo(wx + ww, wy); ctx.lineTo(760, 1320); ctx.lineTo(80, 1320); ctx.closePath(); ctx.fill(); ctx.restore();
  ctx.fillStyle = rgba('#aebfca', .9 * la + .05); ctx.fillRect(wx, wy, ww, wh); ctx.fillStyle = '#05080b'; for (let i = 1; i < 5; i++) ctx.fillRect(wx + i * ww / 5 - 7, wy, 14, wh); ctx.fillRect(wx, wy + wh / 2 - 6, ww, 12);
  ctx.strokeStyle = '#0d151b'; ctx.lineWidth = 16; ctx.strokeRect(wx - 8, wy - 8, ww + 16, wh + 16);
  // paper with poem
  const px = 150, py = 640, pw = 470, ph = 520; ctx.save(); ctx.translate(px + pw / 2, py + ph / 2); ctx.rotate(-.035); ctx.globalAlpha = .5 + .5 * (1 - death * .8);
  ctx.fillStyle = '#b9b29c'; ctx.shadowColor = 'rgba(0,0,0,.7)'; ctx.shadowBlur = 30; ctx.fillRect(-pw / 2, -ph / 2, pw, ph); ctx.shadowBlur = 0;
  ctx.globalCompositeOperation = 'multiply'; ctx.globalAlpha *= .5; ctx.drawImage(paperTex(), 0, 0, 300, 330, -pw / 2, -ph / 2, pw, ph); ctx.globalCompositeOperation = 'source-over'; ctx.restore();
  const rv = [sstep(L0.s + d0 * .35, L0.s + d0 * .7, t), sstep(L0.s + d0 * .7, L0.e + .5, t), sstep(L4.s, L4.e, t), sstep(L4.e, L5.e, t)];
  ctx.save(); ctx.translate(px + pw / 2, py + ph / 2); ctx.rotate(-.035);
  POEM.forEach((c, i) => { const x = 165 - i * 108; if (rv[i] > 0) { vtext(ctx, c, x, -180, 74, '#14110c', { fam: F.brush, weight: 400, reveal: rv[i], lh: 1.2, alpha: .96 }); } });
  if (rv[3] > .95) blot(ctx, 165 - 3 * 108 + 6, -180 + 74 * 1.2 * 4 + 44, 30 * sstep(L5.e, L5.e + 3, t), '#14110c', .55, 2, 1);
  ctx.restore();
  htext(ctx, '狱中赠别驾卢谌 · 谌以常词酬和，殊乖琨心', px + pw / 2 + 60, py + ph + 44, 26, '#8fa0aa', { alpha: win(t, L2.s - .5, L3.s, .6, .6), weight: 500, spacing: 2 });
  // seated figure, back view, in the shaft
  figure(ctx, 800, 1260, 330, { sit: true, back: true, color: '#020304', robeW: 1.1 });
  // two sources on Wang Dun
  const d2 = L2.e - L2.s, s1 = win(t, L2.s + .3, L3.s + .2, .5, .5), s2 = win(t, L2.s + d2 * .68, L3.s + .2, .5, .5);
  if (s1 > 0) { ctx.save(); ctx.globalAlpha = s1 * .82; ctx.fillStyle = '#060a0e'; ctx.fillRect(60, 300, 560, 190); ctx.restore();
    htext(ctx, '《晋书·刘琨传》', 90, 342, 30, '#d9c48f', { align: 'left', alpha: s1, weight: 700 }); htext(ctx, '会王敦密使匹磾杀琨', 90, 390, 34, '#e2dccb', { align: 'left', alpha: s1, weight: 600 });
    htext(ctx, '《资治通鉴》卷九十', 90, 442, 30, '#9fb0ba', { align: 'left', alpha: s2, weight: 700 }); htext(ctx, '未载此事', 380, 442, 32, '#b9c7cf', { align: 'left', alpha: s2, weight: 600 }); }
  const da = sstep(L6.s + (L6.e - L6.s) * .7, L6.e + .6, t); htext(ctx, '太兴元年（318）五月癸丑', 540, 300, 38, '#b5c2c9', { alpha: da, weight: 600, spacing: 4, outline: 5 }); htext(ctx, '年四十八', 540, 362, 44, '#e2dccb', { alpha: da * sstep(L6.e - .3, L6.e + .8, t), weight: 700, spacing: 12, outline: 5 });
};

// ══ s11 那笔账 ══
SC.s11 = (ctx, t, seg) => {
  const [L0, L1, L2, L3, L4] = SEGL.s11; const tM = L4.s - .5;
  if (t < tM + .4) {
    bgGrad(ctx, '#06090d', '#0d151c', '#141c22', .55); glow(ctx, 540, 640, 620, '#7d95a3', .1);
    // altar
    const ay = 1030; ctx.fillStyle = '#05080b'; ctx.fillRect(210, ay, 660, 26); ctx.fillRect(240, ay + 26, 22, 220); ctx.fillRect(818, ay + 26, 22, 220); ctx.fillRect(230, ay + 90, 620, 12);
    // blank tablet
    const tx = 540, ty = ay - 380; ctx.fillStyle = '#10181e'; ctx.strokeStyle = rgba('#93a7b3', .55); ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(tx - 78, ay - 30); ctx.lineTo(tx - 78, ty + 40); ctx.quadraticCurveTo(tx, ty - 30, tx + 78, ty + 40); ctx.lineTo(tx + 78, ay - 30); ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#05080b'; ctx.fillRect(tx - 110, ay - 34, 220, 34);
    // incense burner (cold), candles unlit
    ctx.fillStyle = '#05080b'; ctx.beginPath(); ctx.ellipse(540, ay - 2, 70, 16, 0, 0, 7); ctx.fill(); ctx.fillRect(500, ay - 62, 80, 60); ctx.beginPath(); ctx.ellipse(540, ay - 62, 52, 12, 0, 0, 7); ctx.fill();
    [320, 760].forEach(x => { ctx.fillStyle = '#05080b'; ctx.fillRect(x - 20, ay - 12, 40, 12); ctx.fillStyle = '#39434a'; ctx.fillRect(x - 9, ay - 122, 18, 110); ctx.fillStyle = '#05080b'; ctx.fillRect(x - 1.5, ay - 134, 3, 12); });
    const late = sstep(L3.s, L3.e + .5, t); if (late > 0) { const pts = []; for (let q = 0; q <= 20; q++) pts.push([540 + 14 * Math.sin(q * .45 + t * .8) * q / 20, ay - 70 - q * 17]); stroke(ctx, pts, 5, '#9fb0b8', .3 * late, { taper: .8, seed: 2 });
      vtext(ctx, '愍', tx, ty + 150, 84, '#b9b29c', { fam: F.brush, weight: 400, alpha: late * .9 }); htext(ctx, '后数岁，乃赠琨太尉、侍中，谥曰愍', 540, 1170, 30, '#9fb0ba', { alpha: late, weight: 500, outline: 4 }); htext(ctx, '——《资治通鉴》卷九十', 800, 1216, 24, '#7f8e97', { alpha: late, align: 'right', weight: 500 }); }
    // ledger
    const d1 = L1.e - L1.s, la = win(t, L0.s + .8, L3.s - .2, .6, .6); if (la > 0) { const y = 370;
      htext(ctx, '段匹磾', 300, y, 46, '#e2dccb', { alpha: la, weight: 700, outline: 5 }); htext(ctx, '尚强 · 可讨石勒', 300, y + 56, 30, '#9fb0ba', { alpha: la * sstep(L1.s + d1 * .1, L1.s + d1 * .4, t), weight: 500, outline: 5 });
      htext(ctx, '刘琨', 780, y, 46, '#e2dccb', { alpha: la, weight: 700, outline: 5 }); htext(ctx, '已死', 780, y + 56, 30, '#9fb0ba', { alpha: la * sstep(L0.s + 1.4, L0.s + 2, t), weight: 500, outline: 5 });
      const c = sstep(L1.s + d1 * .45, L1.s + d1 * .7, t); ctx.save(); ctx.globalAlpha = la * .9; ctx.strokeStyle = C.red; ctx.lineWidth = 5; ctx.beginPath(); ctx.ellipse(300, y + 22, 170, 76, -.04, -1.6, -1.6 + 6.5 * c); ctx.stroke(); ctx.restore();
      stroke(ctx, [[690, y + 4], [870, y - 2]], 8, '#05080b', la, { taper: .5, u1: sstep(L1.s + d1 * .78, L1.e, t) }); stroke(ctx, [[690, y + 4], [870, y - 2]], 3, '#93a7b3', la * .8, { taper: .5, u1: sstep(L1.s + d1 * .78, L1.e, t) }); }
    vtext(ctx, '不举琨哀', 930, 600, 58, '#e2dccb', { fam: F.brush, weight: 400, alpha: win(t, L1.e - .4, L3.s, .8, .6), reveal: sstep(L1.e - .4, L2.s + 1, t), lh: 1.25 });
    fadeBlack(ctx, sstep(tM - .3, tM + .4, t));
  } else {
    const cam = mkCam(116.6, 38.9, 190, 540, 760); drawMap(ctx, cam); const d = L4.e - L4.s, off = sstep(L4.s + d * .3, L4.s + d * .7, t), lost = sstep(L4.s + d * .78, L4.e, t);
    enemyBlots(ctx, cam, .4 + .6 * lost, t, [[114.5, 37.2, 1.6, 2, 0], [115.6, 38.6, 1.3, 1, .3], [116.4, 39.6, 1.2, 3, .55]]);
    regionLabel(ctx, cam, [117.4, 40.4], '幽州 · 段匹磾', 38, 1 - .5 * lost, '#b9c7cf'); cityDot(ctx, cam, 'ji', '蓟', { lit: 1 - off, dim: lost > .5 ? 1 : 0, size: 42 });
    const r = rng(4); for (let i = 0; i < 26; i++) { const a = r() * 6.28, rr = 40 + r() * 150, jp = proj(cam, MAP.city.ji); const x = jp[0] + Math.cos(a) * rr * (1 + off * 2.2), y = jp[1] + Math.sin(a) * rr * .7 * (1 + off * 2.2); glow(ctx, x, y, 7, i % 2 ? '#e6cf9c' : '#b9c7cf', .8 * (1 - off)); }
    htext(ctx, '晋人与各部，皆不附', 540, 330, 40, '#e2dccb', { alpha: win(t, L4.s + d * .32, L4.e + 1, .6, .6), weight: 700, spacing: 6, outline: 6 });
    htext(ctx, '公元 319 年 · 段匹磾失幽州，奔乐陵', 540, 388, 30, '#9fb0ba', { alpha: lost, weight: 500, spacing: 2, outline: 5 });
    const esc = projAll(cam, smoothPath([MAP.city.ji, [116.9, 38.9], [117.3, 37.9]], 8)); dashed(ctx, esc, lost, '#9fb6c4', 3.5, [8, 10], .9);
    fadeBlack(ctx, 1 - sstep(tM + .3, tM + 1, t));
  }
};

// ══ s12 中原 ══
SC.s12 = (ctx, t, seg) => {
  const [L0, L1, L2, L3, L4, L5, L6, L7] = SEGL.s12; const tB = L3.s - .4, tC = L4.s - .5, tD = L5.s - .6, tE = L6.s - .5, tF = L7.s - .6;
  if (t < tC + .4) { // A: the couplet; B: what held him up
    bgGrad(ctx, '#06090d', '#0d151c', '#131b21', .5); glow(ctx, 540, 720, 640, '#7d95a3', .09);
    const fadeA = 1 - sstep(tB - .4, tB + .5, t), d1 = L1.e - L1.s;
    vtext(ctx, '何意百炼刚', 660, 370, 150, '#e6e1d0', { fam: F.brush, weight: 400, alpha: fadeA, reveal: sstep(L1.s, L1.s + d1 * .5, t) * 1.02, lh: 1.16 });
    vtext(ctx, '化为绕指柔', 420, 370, 150, '#e6e1d0', { fam: F.brush, weight: 400, alpha: fadeA, reveal: sstep(L1.s + d1 * .5, L1.e, t) * 1.02, lh: 1.16 });
    seal(ctx, 290, 1010, 24, '刘琨', fadeA * sstep(L1.e, L1.e + .8, t));
    if (t > tB) { const d3 = L3.e - L3.s, ws = ['粮', '兵', '朝廷', '盟友'], xs = [200, 420, 650, 880]; const inn = sstep(tB + .3, tB + 1.2, t);
      // sword upright
      ctx.save(); ctx.globalAlpha = inn; const sg = ctx.createLinearGradient(520, 0, 560, 0); sg.addColorStop(0, '#7b8a92'); sg.addColorStop(.5, '#d6e0e4'); sg.addColorStop(1, '#8796a0'); ctx.fillStyle = sg; ctx.beginPath(); ctx.moveTo(540, 300); ctx.lineTo(556, 340); ctx.lineTo(552, 980); ctx.lineTo(528, 980); ctx.lineTo(524, 340); ctx.closePath(); ctx.fill(); ctx.fillStyle = '#2a2420'; ctx.fillRect(482, 980, 116, 18); ctx.fillStyle = '#3a312a'; ctx.fillRect(526, 998, 28, 130); ctx.restore();
      ws.forEach((w_, i) => { const off = sstep(L3.s + d3 * (.42 + i * .12), L3.s + d3 * (.42 + i * .12) + .7, t); const y = 560 + (i % 2) * 220; vtext(ctx, w_, xs[i] + (i < 2 ? -30 : 30), y, 76, '#e2dccb', { fam: F.brush, weight: 400, alpha: inn * (1 - off), lh: 1.15 });
        if (off > 0 && off < 1) blot(ctx, xs[i] + (i < 2 ? -30 : 30), y + 40, 90 * off, '#05080b', .5 * (1 - off), 1 + i % 3, i); }); }
    fadeBlack(ctx, sstep(tC - .3, tC + .4, t));
  } else if (t < tD + .4) { // C: Zu Ti
    const cam = mkCam(115.2, 34.6, 150, 540, 760); drawMap(ctx, cam); const d = L4.e - L4.s, lit = sstep(L4.s + .3, L4.s + d * .3, t), off = sstep(L4.s + d * .75, L4.e + .8, t);
    enemyBlots(ctx, cam, 1, t, [[114.5, 37.0, 1.5, 2, 0], [112.0, 36.6, 1.4, 1, 0], [116.5, 38.2, 1.2, 3, 0]]);
    [[114.8, 34.4, 1.5, 1], [116.2, 33.9, 1.3, 2], [113.6, 34.1, 1.1, 3]].forEach(([lo, la, rd, sd]) => { const p = proj(cam, [lo, la]); blot(ctx, p[0], p[1], rd * cam.scale, '#d9c48f', .2 * lit * (1 - off), sd, sd); });
    regionLabel(ctx, cam, [115.2, 33.45], '祖逖收复河南地', 36, lit * (1 - off), '#d9c48f');
    cityDot(ctx, cam, 'yongqiu', '雍丘', { lit: lit * (1 - off), dim: off > .6 ? 1 : 0, size: 40, sub: off > .5 ? '321 年 · 祖逖卒，年五十六' : '祖逖' }); cityDot(ctx, cam, 'luoyang', '洛阳', { dim: 1, sq: true, dx: -16 }); cityDot(ctx, cam, 'jiankang', '建康', { dx: 16, lit: .5, sub: '朝廷' });
    const ctl = projAll(cam, smoothPath([MAP.city.jiankang, [117.6, 32.6], [116.4, 33.6], [115.1, 34.4]], 8)); arrow(ctx, ctl, sstep(L4.s + d * .35, L4.s + d * .6, t), '#8fa9b8', 6, .9 * (1 - off), 18); const cp = pointAt(ctl, .45); htext(ctx, '遣戴渊来统', cp[0] + 24, cp[1] + 30, 28, '#a9bcc8', { align: 'left', alpha: sstep(L4.s + d * .45, L4.s + d * .6, t) * (1 - off), weight: 600, outline: 5 });
    fadeBlack(ctx, Math.max(1 - sstep(tC + .3, tC + 1, t), sstep(tD - .3, tD + .4, t)));
  } else if (t < tE + .4 || t >= tF + .4) { // D / F: the courtyard, one sword
    const z = 1 + .07 * easeIO((t - tD) / (seg.e - tD)); ctx.save(); ctx.translate(560, 1050); ctx.scale(z, z); ctx.translate(-560, -1050);
    courtyard(ctx, t, { lamp: 0, roosterOn: false });
    // a sword stuck in the ground
    ctx.save(); ctx.translate(560, 1168); ctx.rotate(.09); ctx.fillStyle = 'rgba(3,5,8,.5)'; ctx.beginPath(); ctx.ellipse(40, 4, 90, 8, 0, 0, 7); ctx.fill();
    const sg = ctx.createLinearGradient(-6, 0, 6, 0); sg.addColorStop(0, '#6f8088'); sg.addColorStop(.5, '#dbe5e9'); sg.addColorStop(1, '#7d8c95'); ctx.fillStyle = sg; ctx.fillRect(-5, -170, 10, 170); ctx.fillStyle = '#1d1814'; ctx.fillRect(-26, -180, 52, 10); ctx.fillRect(-6, -236, 12, 58); ctx.restore();
    glow(ctx, 566, 1060, 120, '#cfe0e8', .1 + .05 * Math.sin(t * .9));
    ctx.restore();
    const cr = sstep(seg.e - 4.2, seg.e - 3.2, t); htext(ctx, '史料：《晋书》卷六十二 · 《资治通鉴》卷八十八至九十一', 540, 1262, 26, '#8fa0aa', { alpha: cr, weight: 500, outline: 4 });
    fadeBlack(ctx, Math.max(t < tE + .4 ? Math.max(1 - sstep(tD + .3, tD + 1.1, t), sstep(tE - .3, tE + .4, t)) : 1 - sstep(tF + .3, tF + 1.1, t), 0));
  } else { // E: two lights gone
    const cam = CAM_ALL; drawMap(ctx, cam); enemyBlots(ctx, cam, 1, t, [[112.6, 37.4, 2.2, 1, 0], [115.5, 38.6, 2.4, 2, 0], [114.2, 35.6, 2.0, 3, 0], [110.0, 35.2, 1.8, 2, 0], [117.2, 36.2, 1.8, 1, 0]]);
    const d = L6.e - L6.s; cityDot(ctx, cam, 'ji', '蓟', { dim: 1, dx: 16, sub: '318 年 · 刘琨' , alpha: sstep(tE + .5, tE + 1.2, t) }); cityDot(ctx, cam, 'yongqiu', '雍丘', { dim: 1, dx: 16, sub: '321 年 · 祖逖', alpha: sstep(L6.s + d * .5, L6.s + d * .7, t) });
    cityDot(ctx, cam, 'luoyang', '洛阳', { dim: 1, sq: true, dx: -16 }); cityDot(ctx, cam, 'changan', '长安', { dim: 1, sq: true, dx: -16 }); cityDot(ctx, cam, 'jiankang', '建康', { dx: 16, lit: .5 });
    regionLabel(ctx, cam, [113.6, 36.3], '中原', 80, .5, '#6c7880');
    fadeBlack(ctx, Math.max(1 - sstep(tE + .3, tE + 1, t), sstep(tF - .3, tF + .4, t)));
  }
};
