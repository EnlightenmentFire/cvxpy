// ───────── scenes s01–s06 ─────────
function nightSky(ctx, top = '#060a10', mid = '#101c28', bot = '#1c2c3a', midAt = .5) { bgGrad(ctx, top, mid, bot, midAt); }
function stars(ctx, t, n = 90, yMax = 900, alpha = 1, seed = 5) {
  const r = rng(seed); ctx.save(); ctx.fillStyle = '#cfd9df';
  for (let i = 0; i < n; i++) { const x = r() * W, y = 200 + r() * (yMax - 200), s = .6 + r() * 1.3, ph = r() * 9; ctx.globalAlpha = alpha * (.25 + .35 * r()) * (.75 + .25 * Math.sin(t * .8 + ph)); ctx.fillRect(x, y, s, s); }
  ctx.restore();
}
function moon(ctx, x, y, r, phase = 1, alpha = 1) { // phase 1 = full, <1 crescent
  glow(ctx, x, y, r * 4.2, '#a9bccb', .2 * alpha); glow(ctx, x, y, r * 1.9, '#cfdbe2', .3 * alpha);
  ctx.save(); ctx.globalAlpha *= alpha; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fillStyle = '#e4e6dc'; ctx.fill();
  ctx.clip(); ctx.globalAlpha *= .22; ctx.globalCompositeOperation = 'multiply'; ctx.drawImage(blotTex(2), x - r * .9, y - r * .7, r * 1.3, r * 1.3); ctx.drawImage(blotTex(3), x - r * .1, y - r * .1, r * .9, r * .9);
  if (phase < 1) { ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = .96; ctx.fillStyle = '#0a121b'; ctx.beginPath(); ctx.arc(x + r * (1.15 - phase) * 1.1, y - r * .12, r * 1.02, 0, 7); ctx.fill(); }
  ctx.restore();
}
function rooster(ctx, x, y, s, alpha = 1, crow = 0) { // feet at x,y
  ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(x, y); ctx.scale(s, s); ctx.fillStyle = C.ink; ctx.strokeStyle = C.ink; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.ellipse(0, -30, 24, 17, -.25, 0, 7); ctx.fill();                               // body
  ctx.save(); ctx.translate(14, -40); ctx.rotate(-crow * .35); ctx.beginPath(); ctx.moveTo(-6, 6); ctx.quadraticCurveTo(2, -22, 10, -34); ctx.lineTo(18, -30); ctx.quadraticCurveTo(14, -8, 10, 8); ctx.closePath(); ctx.fill(); // neck
  ctx.beginPath(); ctx.arc(14, -36, 7.5, 0, 7); ctx.fill(); ctx.beginPath(); ctx.moveTo(20, -38); ctx.lineTo(31, -36 - crow * 3); ctx.lineTo(20, -33 + crow * 2); ctx.fill();   // head, beak
  ctx.fillStyle = C.red; ctx.beginPath(); ctx.arc(11, -45, 3.6, 0, 7); ctx.arc(15.5, -46.5, 3.8, 0, 7); ctx.arc(19.5, -44.5, 3.2, 0, 7); ctx.fill(); ctx.restore();
  ctx.fillStyle = C.ink; for (let i = 0; i < 5; i++) { ctx.lineWidth = 5.5 - i * .5; ctx.beginPath(); ctx.moveTo(-18, -34); ctx.quadraticCurveTo(-46 - i * 4, -70 + i * 11, -52 + i * 3, -30 + i * 9); ctx.stroke(); } // tail
  ctx.lineWidth = 2.6; ctx.beginPath(); ctx.moveTo(-3, -15); ctx.lineTo(-4, 0); ctx.lineTo(4, 0); ctx.moveTo(7, -15); ctx.lineTo(8, 0); ctx.lineTo(15, 0); ctx.stroke();
  ctx.restore();
}
function soundArcs(ctx, x, y, t, t0, { n = 3, color = '#cdd8de', dir = -Math.PI / 2, spread = .9, speed = 150, life = 1.6, alpha = .5, w = 2.2 } = {}) {
  for (let i = 0; i < n; i++) { const tt = t - t0 - i * .28; if (tt < 0 || tt > life) continue; const r = 26 + tt * speed, a = alpha * (1 - tt / life) * sstep(0, .15, tt);
    ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = color; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.beginPath(); ctx.arc(x, y, r, dir - spread, dir + spread); ctx.stroke(); ctx.restore(); }
}

// ══ s01 鸡鸣 ══
const S1 = { ground: 1150, h: 205 };
function courtyard(ctx, t, { lamp = 0, crowTs = [], roosterOn = true } = {}) {
  nightSky(ctx, '#070c13', '#13212e', '#22343f'); stars(ctx, t, 110, 950); moon(ctx, 820, 450, 62, .42);
  ctx.drawImage(mountains('s1', { seed: 4, h: 1200, layers: [{ y: 990, amp: 150, col: '#1e303d', freq: .0032, fade: 240 }, { y: 1040, amp: 90, col: '#122029', freq: .006, fade: 200 }] }), 0, 0);
  ctx.fillStyle = '#0b131a'; ctx.fillRect(0, 1075, W, 900);
  const g = ctx.createLinearGradient(0, 1080, 0, 1500); g.addColorStop(0, 'rgba(130,155,170,.22)'); g.addColorStop(1, 'rgba(130,155,170,0)'); ctx.fillStyle = g; ctx.fillRect(0, 1080, W, 420);
  tree(ctx, 120, 1080, 640, 21, '#070c11');
  ctx.fillStyle = '#070c11'; ctx.fillRect(-20, 1012, 600, 70); ctx.fillRect(-20, 1002, 612, 13);
  hall(ctx, 830, 1090, 500, 320, '#070c11');
  ctx.save(); ctx.globalAlpha = lamp * (.85 + .15 * noise1(t * 6, 2)); ctx.fillStyle = '#e2a95a'; ctx.fillRect(772, 972, 46, 60); ctx.fillRect(842, 972, 46, 60); ctx.fillStyle = '#070c11'; ctx.fillRect(793, 972, 4, 60); ctx.fillRect(863, 972, 4, 60); ctx.fillRect(772, 1000, 116, 4); ctx.restore();
  glow(ctx, 830, 1004, 240, C.fire, .22 * lamp);
  if (roosterOn) { let crow = 0; crowTs.forEach(c => { crow = Math.max(crow, win(t, c, c + 1.9, .2, .5)); }); rooster(ctx, 215, 1003, 1.25, 1, crow); crowTs.forEach(c => soundArcs(ctx, 255, 932, t, c, { dir: -.6, spread: .7, n: 4, speed: 130, life: 1.9 })); }
}
function s1pose(t, who) {
  const ph = who ? 1.9 : 0, w = 1.55;
  const a = t * w + ph;
  return { x: (who ? 690 : 450) + 46 * Math.sin(a * .5 + ph) * (who ? -1 : 1), y: S1.ground + 6, facing: who ? -1 : 1,
    lean: .16 * Math.sin(a + .6), arm: .55 + 1.05 * Math.sin(a), swordA: .15 + .55 * Math.sin(a * 1.0 + 1.2) };
}
function s1tip(p, h) { const sy = -.78, lean = p.lean; const s0x = .1 + lean * (sy + .04), s0y = sy + .04, hx = s0x + Math.cos(p.arm) * .34, hy = s0y - Math.sin(p.arm) * .34, a = p.arm + p.swordA; return [p.x + p.facing * h * (hx + Math.cos(a) * .72), p.y + h * (hy - Math.sin(a) * .72)]; }
SC.s01 = (ctx, t, seg) => {
  const L0 = ln('s01', 0), L1 = ln('s01', 1), L2 = ln('s01', 2), L3 = ln('s01', 3), L4 = ln('s01', 4), L5 = ln('s01', 5);
  const tSplit = L5.s - .15, tTitle = L5.e + .5; L4.showY = 1240;
  const zoom = 1 + .05 * easeIO((t) / (tSplit));
  if (t < tSplit + .7) {
    ctx.save(); ctx.translate(540, 900); ctx.scale(zoom, zoom); ctx.translate(-540, -900);
    const lamp = sstep(L0.s - 1.5, L0.s + .5, t) * (1 - .9 * sstep(L3.s + 1, L3.s + 3, t));
    courtyard(ctx, t, { lamp, crowTs: [1.6, L1.s + .2] });
    // figures
    const out = sstep(L2.s + .2, L3.s + .4, t); const dance = sstep(L3.s + .5, L3.s + 1.6, t);
    for (let who = 0; who < 2; who++) {
      const p = s1pose(t, who), rest = { x: who ? 760 : 680, lean: 0, arm: -1.25, swordA: .1 };
      const q = { x: lerp(rest.x, p.x, dance), y: p.y, facing: p.facing, lean: p.lean * dance, arm: lerp(rest.arm, p.arm, dance), swordA: lerp(rest.swordA, p.swordA, dance) };
      // sword trail
      if (dance > .3) { ctx.save(); ctx.lineCap = 'round'; let prev = null; for (let k = 0; k <= 14; k++) { const pk = s1pose(t - k * .022, who); pk.x = lerp(rest.x, pk.x, dance); const tp = s1tip(pk, S1.h); if (prev) { ctx.strokeStyle = rgba('#dfe9ee', .38 * dance * (1 - k / 14)); ctx.lineWidth = 5 * (1 - k / 14) + .5; ctx.beginPath(); ctx.moveTo(prev[0], prev[1]); ctx.lineTo(tp[0], tp[1]); ctx.stroke(); } prev = tp; } ctx.restore(); }
      ctx.save(); ctx.globalAlpha = out * .5; ctx.fillStyle = '#04070a'; ctx.beginPath(); ctx.ellipse(q.x, q.y + 6, 70, 9, 0, 0, 7); ctx.fill(); ctx.restore();
      const glint = Math.pow(Math.max(0, Math.sin(t * 1.55 + (who ? 1.9 : 0) + 1.2)), 12);
      figure(ctx, q.x, q.y, S1.h, { facing: q.facing, lean: q.lean, arm: q.arm, sword: .72, swordA: q.swordA, alpha: out, glint: glint * dance, color: '#05080b' });
      // names
      const na = win(t, L4.s + (who ? 1.4 : .3), L5.s - .3, .5, .4);
      if (na > 0) { const nx = (who ? 800 : 340); vtext(ctx, who ? '刘琨' : '祖逖', nx, 760, 46, C.pale, { alpha: na, weight: 700, outline: 5 }); ctx.save(); ctx.globalAlpha = na * .6; ctx.fillStyle = C.yellowDim; ctx.fillRect(nx - 1, 846, 2, 44); ctx.restore(); }
    }
    ctx.restore();
    // sword flash → split
    const fl = win(t, tSplit - .12, tSplit + .55, .1, .45);
    if (fl > 0) { ctx.save(); ctx.globalAlpha = fl; ctx.translate(540, 860); ctx.rotate(-.42); const gg = ctx.createLinearGradient(0, -40, 0, 40); gg.addColorStop(0, 'rgba(255,255,255,0)'); gg.addColorStop(.5, 'rgba(240,248,252,1)'); gg.addColorStop(1, 'rgba(255,255,255,0)'); ctx.fillStyle = gg; ctx.fillRect(-900, -40 * (1.2 - fl * .5), 1800, 80 * (1.2 - fl * .5)); ctx.restore(); ctx.fillStyle = `rgba(230,240,245,${fl * .14})`; ctx.fillRect(0, 0, W, H); }
  }
  // split view: north (up) / south (down)
  const sp = sstep(tSplit + .25, tSplit + 1.1, t);
  if (sp > 0) {
    ctx.save(); ctx.globalAlpha = sp; nightSky(ctx, '#070b11', '#0e1822', '#131f2a');
    const mid = 800, focusN = sstep(L5.e - 2.6, L5.e - 1.2, t), toTitle = sstep(tTitle - .3, tTitle + 1.0, t);
    // north half: mountains + walker
    ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W, mid + 300 * toTitle); ctx.clip();
    stars(ctx, t, 60, 600, 1, 9);
    ctx.drawImage(mountains('s1n', { seed: 12, h: 900, layers: [{ y: 560, amp: 170, col: '#22323f', freq: .003, fade: 260 }, { y: 650, amp: 150, col: '#172631', freq: .0045, fade: 220 }, { y: 760, amp: 110, col: '#0c151d', freq: .007, fade: 200 }] }), 0, 0);
    const wn = clamp((t - tSplit - .4) / 9); const fx = 470 + wn * 40, fy = 778 - wn * 40, fh = 96 - wn * 26;
    figure(ctx, fx, fy, fh, { back: true, arm: -1.3, sword: .6, swordA: .05, color: '#04070a', alpha: 1 - toTitle * .2 });
    vtext(ctx, '刘琨', fx + 86, fy - 150, 38, C.pale, { alpha: sstep(tSplit + 1.2, tSplit + 2, t) * (1 - toTitle), weight: 700, outline: 5 });
    htext(ctx, '北', 930, 330, 96, rgba('#aebcc5', .9), { fam: F.brush, weight: 400, alpha: .55 * (1 - toTitle) });
    ctx.restore();
    // south half: river + boat
    const sa = (1 - .78 * focusN) * (1 - toTitle);
    if (sa > 0.01) {
      ctx.save(); ctx.globalAlpha = sp * sa; ctx.beginPath(); ctx.rect(0, mid, W, 520); ctx.clip();
      ctx.fillStyle = '#0a121a'; ctx.fillRect(0, mid, W, 520);
      ctx.drawImage(mountains('s1s', { seed: 31, h: 300, layers: [{ y: 150, amp: 60, col: '#1a2934', freq: .004, fade: 120 }] }), 0, mid - 20);
      for (let i = 0; i < 9; i++) { const y = mid + 150 + i * 36; const pts = []; for (let x = -20; x <= W + 20; x += 30) pts.push([x, y + 5 * Math.sin(x * .012 + i * 1.7 + t * .7)]); stroke(ctx, pts, 1.6 + i * .22, '#7f9db0', .16 + .025 * i, { taper: .3, seed: i }); }
      const bx = 560 + 30 * Math.sin(t * .3), by = mid + 300 + 4 * Math.sin(t * 1.3);
      ctx.fillStyle = '#04070a'; ctx.beginPath(); ctx.moveTo(bx - 130, by - 14); ctx.quadraticCurveTo(bx, by + 30, bx + 140, by - 20); ctx.quadraticCurveTo(bx, by + 8, bx - 130, by - 14); ctx.fill();
      figure(ctx, bx - 10, by + 2, 104, { arm: .5 + .25 * Math.sin(t * 2.2), color: '#04070a' });
      const ax = bx + 26, ay = by - 62; ctx.strokeStyle = '#04070a'; ctx.lineWidth = 4; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(ax - 10, ay - 4); ctx.lineTo(ax + 70, by + 26); ctx.stroke();
      vtext(ctx, '祖逖', bx - 130, by - 190, 38, C.pale, { alpha: sstep(tSplit + 1.0, tSplit + 1.8, t), weight: 700, outline: 5 });
      htext(ctx, '中流击楫', bx + 210, by - 110, 30, '#9fb0ba', { alpha: sstep(tSplit + 2.2, tSplit + 3.0, t) * .95, weight: 500, spacing: 5, outline: 4 });
      htext(ctx, '南', 930, mid + 110, 96, rgba('#aebcc5', .9), { fam: F.brush, weight: 400, alpha: .55 });
      ctx.restore();
      ctx.save(); ctx.globalAlpha = sp * (1 - toTitle) * .7; ctx.fillStyle = '#93a7b3'; ctx.fillRect(0, mid - 1, W, 2); ctx.restore();
    }
    ctx.restore();
    // title
    const ta = sstep(tTitle, tTitle + 1.2, t);
    if (ta > 0) {
      ctx.fillStyle = `rgba(5,8,11,${ta * .35})`; ctx.fillRect(0, 0, W, H);
      htext(ctx, '刘琨', 540, 1000, 250, '#e9e4d4', { fam: F.brush, weight: 400, alpha: ta, reveal: sstep(tTitle, tTitle + 1.0, t), spacing: 30 });
      ctx.save(); ctx.globalAlpha = ta * sstep(tTitle + .8, tTitle + 1.4, t); ctx.fillStyle = C.red; ctx.fillRect(540 - 230, 1162, 460 * sstep(tTitle + .8, tTitle + 1.6, t), 3); ctx.restore();
      htext(ctx, '一座没有后方的孤城', 540, 1232, 62, '#d9d4c4', { weight: 700, alpha: ta, reveal: sstep(tTitle + 1.0, tTitle + 2.2, t), spacing: 8, outline: 6 });
    }
  }
};

// ══ s02 洛阳公子 ══
SC.s02 = (ctx, t, seg) => {
  const L0 = ln('s02', 0), L1 = ln('s02', 1) || { s: seg.e + 99 }; const u = (t - seg.s) / (seg.e - seg.s);
  const cold = sstep(L1.s - .6, L1.s + .8, t);
  bgGrad(ctx, '#0a0f15', lerpCol('#1d2a33', '#101a23', cold), lerpCol('#2b3438', '#16222c', cold), .5);
  ctx.save(); ctx.translate(-30 * u, 0);
  ctx.drawImage(mountains('s2', { seed: 8, h: 1000, w: 1200, layers: [{ y: 760, amp: 120, col: '#24333d', freq: .003, fade: 240 }] }), 0, 0);
  // garden: water, pavilion, willow, lanterns
  const gy = 1010; ctx.fillStyle = '#0a1118'; ctx.fillRect(0, gy, 1200, 600);
  hall(ctx, 620, gy, 520, 360, '#060a0f', { tiers: 2 });
  hall(ctx, 190, gy + 6, 300, 200, '#080d13'); hall(ctx, 1010, gy + 4, 260, 180, '#080d13');
  // reflection
  ctx.save(); ctx.globalAlpha = .28; ctx.translate(0, 2 * gy + 16); ctx.scale(1, -1); hall(ctx, 620, gy, 520, 360, '#060a0f', { tiers: 2 }); ctx.restore();
  const warm = 1 - cold; const r = rng(3);
  for (let i = 0; i < 16; i++) { const lx = 300 + r() * 660, ly = gy - 40 - r() * 230, ph = r() * 9, a = warm * (.6 + .4 * noise1(t * 3 + ph, i));
    glow(ctx, lx, ly, 46, C.fire, .42 * a); ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = '#f0c57c'; ctx.beginPath(); ctx.ellipse(lx, ly, 6.5, 9, 0, 0, 7); ctx.fill(); ctx.restore();
    glow(ctx, lx + 3 * Math.sin(t + ph), 2 * gy + 16 - ly, 30, C.fire, .14 * a); }
  // willow strokes
  for (let k = 0; k < 2; k++) { const bx = k ? 1080 : 70; tree(ctx, bx, gy + 10, 560, 40 + k, '#05090d'); const rr = rng(60 + k);
    for (let i = 0; i < 26; i++) { const x0 = bx - 150 + rr() * 300, y0 = gy - 380 + rr() * 140, len = 150 + rr() * 170, sw = 16 * Math.sin(t * .6 + i); stroke(ctx, curve([x0, y0], [x0 + sw * .4, y0 + len * .5], [x0 + sw, y0 + len], 10), 2.2, '#0a1016', .8, { taper: .7, seed: i }); } }
  ctx.restore();
  // labels
  const a0 = win(t, L0.s + 2.2, Math.min(L1.s - .3, seg.e), .7, .6);
  vtext(ctx, '金谷园', 900, 420, 64, '#e2dccb', { fam: F.brush, weight: 400, alpha: a0, reveal: sstep(L0.s + 2.2, L0.s + 3.4, t) });
  seal(ctx, 836, 640, 24, '二十四友', a0 * sstep(L0.s + 4, L0.s + 4.8, t));
  // cold turn: a sword laid on a pillow (枕戈待旦), lamps out
  if (cold > 0) { ctx.save(); ctx.globalAlpha = cold * .55; ctx.fillStyle = '#05080b'; ctx.fillRect(0, 0, W, H); ctx.restore();
    const y = 860; ctx.save(); ctx.globalAlpha = cold; ctx.translate(540, y); ctx.rotate(-.1);
    ctx.fillStyle = '#1a242c'; ctx.beginPath(); ctx.roundRect(-310, 26, 240, 74, 30); ctx.fill();          // pillow
    const sg = ctx.createLinearGradient(-330, 0, 360, 0); sg.addColorStop(0, '#6f8088'); sg.addColorStop(.5, '#cfdade'); sg.addColorStop(1, '#8d9ca4'); ctx.fillStyle = sg;
    ctx.beginPath(); ctx.moveTo(-250, 2); ctx.lineTo(330, -4); ctx.lineTo(372, 8); ctx.lineTo(330, 18); ctx.lineTo(-250, 16); ctx.closePath(); ctx.fill();
    ctx.fillStyle = '#2a2420'; ctx.fillRect(-268, -16, 18, 50); ctx.fillStyle = '#3a312a'; ctx.fillRect(-380, -2, 112, 22); ctx.restore();
    glow(ctx, 760, y - 40, 160, '#cfe0e8', .12 * cold * (.6 + .4 * Math.sin(t * 1.3)));
    htext(ctx, '枕戈待旦', 540, 640, 84, '#dcd7c6', { fam: F.brush, weight: 400, alpha: cold, reveal: sstep(L1.s + .2, L1.s + 1.6, t), spacing: 22 }); }
};
function lerpCol(a, b, u) { const A = parseInt(a.slice(1), 16), B = parseInt(b.slice(1), 16); const f = s => Math.round(lerp((A >> s) & 255, (B >> s) & 255, clamp(u))); return `rgb(${f(16)},${f(8)},${f(0)})`; }

// ══ s03 进州 ══
function enemyBlots(ctx, cam, k, t, list) { // list: [lon,lat,r(deg),seed,delay]
  list.forEach(([lo, la, rd, sd, dl]) => { const kk = clamp((k - dl) / (1 - dl)); if (kk <= 0) return; const p = proj(cam, [lo, la]); blot(ctx, p[0], p[1], rd * cam.scale * (.35 + .65 * easeOut(kk)) * (1 + .03 * Math.sin(t * .7 + sd)), '#020406', .78 * sstep(0, .35, kk), sd, sd * 1.3); });
}
const ENEMY_BING = [[110.9, 36.3, 1.25, 1, 0], [114.6, 37.0, 1.2, 2, .1], [111.2, 38.9, .95, 3, .2], [113.9, 39.0, .9, 1, .3], [112.6, 36.0, .8, 2, .35], [110.9, 37.7, .85, 3, .15], [114.3, 38.2, .8, 1, .4]];
function ruins(ctx, t, k, seed = 7) { // k = rebuild progress 0..1
  const gy = 1085; const r = rng(seed);
  bgGrad(ctx, '#080d13', lerpCol('#18242e', '#202d35', k), lerpCol('#27323a', '#3a3f3c', k), .52);
  ctx.drawImage(mountains('s3r', { seed: 17, h: 1100, layers: [{ y: 800, amp: 190, col: '#1f2e3a', freq: .0028, fade: 300 }, { y: 930, amp: 120, col: '#131f29', freq: .005, fade: 220 }] }), 0, 0);
  ctx.fillStyle = '#080d12'; ctx.fillRect(0, gy, W, 900);
  const gg = ctx.createLinearGradient(0, gy, 0, gy + 300); gg.addColorStop(0, 'rgba(130,150,160,.16)'); gg.addColorStop(1, 'rgba(130,150,160,0)'); ctx.fillStyle = gg; ctx.fillRect(0, gy, W, 300);
  // broken walls / charred posts
  ctx.fillStyle = '#05080b';
  for (let i = 0; i < 9; i++) { const x = 40 + i * 120 + r() * 60, w = 22 + r() * 60, h = 60 + r() * 210, a = (r() - .5) * .25; ctx.save(); ctx.translate(x, gy + 6); ctx.rotate(a * (1 - k * .3)); ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, -h); ctx.lineTo(w * .4, -h - 14 * r()); ctx.lineTo(w * .7, -h + 20 * r()); ctx.lineTo(w, -h * (.5 + .4 * r())); ctx.lineTo(w, 0); ctx.fill(); ctx.restore(); }
  for (let i = 0; i < 5; i++) { const x = 100 + r() * 880, len = 160 + r() * 200, a = -.5 + r() * 1.0; ctx.save(); ctx.translate(x, gy - 10 - r() * 40); ctx.rotate(a); ctx.fillRect(0, 0, len, 9); ctx.restore(); }
  // rebuilt huts with lights + smoke
  const huts = [[210, 1.0], [470, .8], [720, 1.1], [930, .85], [345, .6], [600, .65], [845, .55]];
  huts.forEach(([hx, s], i) => { const a = sstep(i / 9, i / 9 + .28, k); if (a <= 0) return; const y = gy + 8 + (i > 3 ? -42 : 12); hall(ctx, hx, y, 190 * s, 120 * s, '#05080b', { alpha: a });
    const la = sstep(i / 9 + .1, i / 9 + .4, k) * (.8 + .2 * noise1(t * 5 + i, i)); ctx.save(); ctx.globalAlpha = la; ctx.fillStyle = '#e6b468'; ctx.fillRect(hx - 12 * s, y - 44 * s, 24 * s, 26 * s); ctx.restore(); glow(ctx, hx, y - 32 * s, 110 * s, C.fire, .3 * la);
    if (la > .2) { for (let j = 0; j < 2; j++) { const pts = []; for (let q = 0; q <= 16; q++) { const yy = y - 120 * s - q * 22; pts.push([hx + 40 * s + j * 10 + 16 * Math.sin(q * .5 + t * .9 + i + j) * (q / 16) + q * 3, yy]); } stroke(ctx, pts, 7 * s, '#9fb0b8', .16 * la, { taper: .8, seed: i + j }); } } });
  // thorns (fade as k grows)
  const ta = 1 - .85 * sstep(.1, .7, k); const rr = rng(seed + 9);
  ctx.save(); ctx.strokeStyle = '#04070a'; ctx.lineCap = 'round';
  for (let i = 0; i < 150; i++) { const x = rr() * W, y = gy + 20 + rr() * 150 - Math.abs(rr() - .5) * 60, len = 30 + rr() * 110, a = -Math.PI / 2 + (rr() - .5) * 1.9, bend = (rr() - .5) * 80; ctx.globalAlpha = ta * (.5 + .5 * rr()); ctx.lineWidth = 1 + rr() * 2.4;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.quadraticCurveTo(x + Math.cos(a) * len * .5 + bend, y + Math.sin(a) * len * .5, x + Math.cos(a) * len, y + Math.sin(a) * len); ctx.stroke(); }
  ctx.restore();
}
SC.s03 = (ctx, t, seg) => {
  const Ls = SEGL.s03, [L0, L1, L2, L3, L4, L5, L6, L7] = Ls;
  const inRuins = t >= L4.s - .2 && t < L7.s - .2;
  if (!inRuins) {
    const back = t >= L7.s - .2;
    let cam = back ? camLerp(CAM_BING, CAM_NORTH, (t - L7.s + .5) / 5) : t < L1.s ? camLerp(CAM_ALL, mkCam(113.4, 36.6, 96), (t - seg.s) / (L1.s - seg.s)) : camLerp(mkCam(113.4, 36.6, 96), CAM_BING, (t - L1.s) / (L3.s - L1.s));
    drawMap(ctx, cam);
    const k = back ? 1 : sstep(L2.s - .5, L3.e, t);
    enemyBlots(ctx, cam, k, t, ENEMY_BING);
    // Bingzhou light
    const jp = proj(cam, MAP.city.jinyang); const la = back ? 1 : sstep(L0.s + 3.5, L0.s + 5, t);
    glow(ctx, jp[0], jp[1], cam.scale * 1.15 * (1 - .35 * k), '#d9c48f', .2 * la);
    regionLabel(ctx, cam, [112.3, 38.75], '并州', Math.min(64, 30 * cam.scale / 74), sstep(L0.s + 2.5, L0.s + 3.5, t) * (1 - .5 * k), '#c8bfa6');
    cityDot(ctx, cam, 'luoyang', '洛阳', { alpha: sstep(seg.s + .5, seg.s + 1.5, t), dx: 16, sq: true, sub: back ? '' : '朝廷' });
    cityDot(ctx, cam, 'changan', '长安', { alpha: sstep(seg.s + .8, seg.s + 1.8, t) * (back ? 1 : 1 - sstep(L1.s, L1.s + 2, t)), dx: -16, sq: true });
    cityDot(ctx, cam, 'jinyang', '晋阳', { alpha: la, lit: la, sub: (t < L1.s + 1.5) ? '今太原' : '', size: 40 });
    // route to post
    if (!back) { const route = projAll(cam, smoothPath([MAP.city.luoyang, [112.9, 35.4], MAP.city.huguan, [113.0, 37.0], MAP.city.jinyang], 8)); const ru = sstep(L1.s - .3, L2.s + 1.2, t);
      dashed(ctx, route, ru, '#d9c48f', 3.5, [9, 11], .85 * (1 - sstep(L3.s, L3.s + 2, t)));
      cityDot(ctx, cam, 'huguan', '壶关', { alpha: win(t, L1.s + .6, L3.s + 1, .6, .8), dx: 16, sub: '今山西长治一带', size: 32 });
      // request to court
      const ra = win(t, L3.s + 2.2, L4.s - .6, .6, .5); if (ra > 0) { htext(ctx, '请谷五百万斛 · 绢五百万匹 · 绵五百万斤', 540, 1196, 34, '#d9c48f', { alpha: ra, weight: 600, outline: 5 }); htext(ctx, '朝廷许之', 540, 1246, 30, '#9fb0ba', { alpha: ra * sstep(L3.s + 3, L3.s + 3.8, t), weight: 500, spacing: 6, outline: 4 }); }
      const ya = win(t, L0.s + .2, L1.s, .6, .6); htext(ctx, '公元 307 年 · 永嘉元年', 540, 330, 36, '#b5c2c9', { alpha: ya, weight: 500, spacing: 4, outline: 5 }); }
    else { const k2 = sstep(L7.s + 1, L7.s + 4, t);
      cityDot(ctx, cam, 'pingyang', '刘聪', { alpha: k2, dx: -16, color: '#aab6bd', sub: '平阳' }); cityDot(ctx, cam, 'xiangguo', '石勒', { alpha: sstep(L7.s + 2.6, L7.s + 3.6, t), dx: 16, color: '#aab6bd', sub: '襄国' });
      const cline = projAll(cam, smoothPath([MAP.city.jinyang, [113.0, 37.0], MAP.city.huguan, [112.9, 35.4], MAP.city.luoyang], 8));
      const ca = sstep(L7.s + 4.5, L7.s + 5.5, t), fade = 1 - .8 * sstep(L7.e - 2.2, L7.e, t);
      dashed(ctx, cline, ca, '#d9c48f', 3, [6, 14], .8 * fade * (.7 + .3 * Math.sin(t * 5)));
      const lp = proj(cam, MAP.city.luoyang); glow(ctx, lp[0], lp[1], 60, '#d9c48f', .35 * ca * fade);
      htext(ctx, '粮，只能向朝廷讨', lp[0] + 20, lp[1] + 78, 30, '#d9c48f', { alpha: ca * fade, align: 'left', weight: 600, outline: 5 }); }
  } else {
    const k = sstep(L4.s + 3.5, L6.e, t); ruins(ctx, t, k);
    htext(ctx, '晋阳', 540, 360, 120, '#e2dccb', { fam: F.brush, weight: 400, alpha: win(t, L4.s, L4.s + 4.5, .8, 1) * .9, spacing: 24 });
    const f = Math.max(1 - sstep(L4.s - .2, L4.s + .5, t), sstep(L7.s - .6, L7.s - .2, t)); if (f > 0) { ctx.fillStyle = `rgba(4,6,9,${f})`; ctx.fillRect(0, 0, W, H); }
  }
  if (!inRuins) { const f = t < L4.s ? sstep(L4.s - .6, L4.s - .2, t) : 1 - sstep(L7.s - .2, L7.s + .5, t); if (f > 0) { ctx.fillStyle = `rgba(4,6,9,${f})`; ctx.fillRect(0, 0, W, H); } }
};

// ══ s04 胡笳 ══
function siegeCity(ctx, t, { wallY = 935 } = {}) {
  const yT = wallY - 120; cityWall(ctx, -20, W + 20, wallY, 120, '#05080b', { crenel: 20 });
  ctx.fillStyle = '#05080b'; ctx.fillRect(120, yT - 74, 400, 80); for (let x = 120; x < 520; x += 40) ctx.fillRect(x, yT - 86, 20, 13);
  hall(ctx, 320, yT - 70, 430, 250, '#05080b', { tiers: 2 });
  ctx.fillStyle = '#0c141b'; ctx.beginPath(); ctx.moveTo(282, wallY + 10); ctx.lineTo(282, wallY - 58); ctx.quadraticCurveTo(320, wallY - 96, 358, wallY - 58); ctx.lineTo(358, wallY + 10); ctx.fill();
}
SC.s04 = (ctx, t, seg) => {
  const [L0, L1, L2, L3] = SEGL.s04; const dawn = sstep(L2.s - 1.5, L3.s + 2, t);
  bgGrad(ctx, lerpCol('#060a10', '#1b2833', dawn), lerpCol('#12202d', '#40505a', dawn), lerpCol('#1f3040', '#8f8a74', dawn), .47);
  stars(ctx, t, 120, 900, 1 - dawn);
  const wallY = 935, fx = 730, fy = wallY - 126;
  moon(ctx, fx, fy - 150 + 40 * dawn, 170, 1, 1 - .7 * dawn);
  ctx.drawImage(mountains('s4', { seed: 23, h: 1100, layers: [{ y: 830, amp: 150, col: '#1a2a36', freq: .003, fade: 260 }] }), 0, 0);
  siegeCity(ctx, t, { wallY });
  figure(ctx, fx, fy, 128, { back: true, color: '#05080b', robeW: 1.1 });
  // sound: whistle (L0 late) then hujia (L1 → solo) then again (L2)
  const whistle = L0.s + (L0.e - L0.s) * .62, hj0 = L1.s + .6, hj1 = L1.e + L1.gap - .6, hj2 = L2.s + .2;
  soundArcs(ctx, fx, fy - 105, t, whistle, { n: 5, spread: Math.PI, speed: 230, life: 3.2, alpha: .42, w: 2 });
  for (let k = 0; hj0 + k * 1.5 < hj1; k++) soundArcs(ctx, fx, fy - 105, t, hj0 + k * 1.5, { n: 2, spread: Math.PI, speed: 170, life: 4.2, alpha: .36, w: 1.8, color: '#d9c48f' });
  for (let k = 0; k < 3; k++) soundArcs(ctx, fx, fy - 105, t, hj2 + k * 1.5, { n: 2, spread: Math.PI, speed: 170, life: 4.2, alpha: .3, w: 1.8, color: '#d9c48f' });
  // plain + campfires in arcs (the besiegers)
  const pg = ctx.createLinearGradient(0, wallY, 0, 1500); pg.addColorStop(0, lerpCol('#070c12', '#1a2129', dawn)); pg.addColorStop(1, lerpCol('#0b1219', '#272b2c', dawn)); ctx.fillStyle = pg; ctx.fillRect(0, wallY, W, H - wallY);
  const r = rng(77); const tOff0 = L1.s + (L1.e - L1.s) * .55, tOff1 = L2.e - .3; const fires = [];
  for (let ring = 0; ring < 3; ring++) { const n = 9 + ring * 4; for (let i = 0; i < n; i++) { const u = (i + .5 + (r() - .5) * .5) / n; const x = 60 + u * 960, y = wallY + 52 + ring * 62 + 26 * Math.sin(u * Math.PI) + r() * 14; fires.push([x, y, 6.5 + ring * 2.2, r(), r()]); } }
  fires.forEach(([x, y, s, ph, o], i) => { const off = lerp(tOff0, tOff1, o); const a = sstep(seg.s + ph * 1.5, seg.s + ph * 1.5 + 1, t) * (1 - sstep(off, off + 1.2, t));
    if (a > 0) flame(ctx, x, y, s, t, i, a);
    // smoke wisp after going out
    const sm = win(t, off + .6, off + 6, 1, 3); if (sm > 0) { const pts = []; for (let q = 0; q <= 8; q++) pts.push([x + 9 * Math.sin(q * .7 + t + i) * q / 8 + q * 1.5, y - 8 - q * 13 * (1 + (t - off) * .12)]); stroke(ctx, pts, s * .7, '#9fb0b8', .18 * sm, { taper: .8, seed: i }); } });
  htext(ctx, '《晋书》所载', 1010, 268, 28, '#9aa9b2', { align: 'right', alpha: .9 * win(t, seg.s + 1, seg.e - 1, 1, 1), weight: 500, spacing: 3, outline: 4 });
};
