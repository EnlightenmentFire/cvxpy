/* S1 冷启动 + 片名 */
(function () {
  const t0 = 0, tEnd = ce('c3') + 0.9;
  ENGINE.scene({ id: 's1', t0, t1: tEnd + 0.3, cls: 'bg-dark', fadeIn: 0.5, build(S) {
    S.cam({ s0: 1.0, s1: 1.06 });
    const t7 = cw('c1', '7'), t8 = cw('c2', '8'), tLine = c('c3'), tAb = cw('c3', '一百多年前');
    const yr = box(90, 300, null, null, 'song', { fontWeight: 900, fontSize: '64px', letterSpacing: '6px', color: C.dim }, '1981');
    S.add(yr); S.fadeUp(yr, 0.5);
    // giant digits
    const d7 = box(0, 270, 1080, null, 'song c', { fontWeight: 900, fontSize: '700px', lineHeight: '1', color: C.paper }, '7');
    const d8 = box(0, 270, 1080, null, 'song c', { fontWeight: 900, fontSize: '700px', lineHeight: '1', color: C.red }, '8');
    S.add(d7, d8);
    S.a(d7, { at: 0.25, d: 1.1, from: { o: 0, s: 1.12 } });
    S.on(t => { const p = pr(t, t8 - 0.45, 0.6, 'io'); d7.style.transform = `translate(${-250 * p}px,${-40 * p}px) scale(${lerp(1, .68, p)})`; d7.style.opacity = Math.min(parseFloat(d7.style.opacity || 1), 1) * 1; });
    S.on(t => { const p = pr(t, t8 - 0.05, 0.34, 'out5'); d8.style.opacity = p; d8.style.transform = `translate(${250}px,${-40}px) scale(${lerp(1.6, .68, p)})`; });
    // people row
    const rowY = 985, n = 8, gap = 112, x0 = 540 - (n * gap) / 2 + 12;
    for (let i = 0; i < n; i++) {
      const pz = person(96, i < 7 ? C.paper : C.red, { left: (x0 + i * gap + (i === 7 ? 26 : 0)) + 'px', top: rowY + 'px' });
      S.add(pz);
      if (i < 7) S.a(pz, { at: t7 - 0.25 + i * 0.09, d: 0.4, e: 'back', from: { o: 0, s: .4, y: 20 } });
      else S.a(pz, { at: t8 + 0.1, d: 0.4, e: 'back', from: { o: 0, s: .4, y: 20 } });
    }
    const cap7 = box(x0, rowY + 118, 7 * gap - 30, null, 'hei c', { fontWeight: 500, fontSize: '34px', letterSpacing: '6px', color: C.dim, borderTop: '2px solid ' + C.dim, paddingTop: '10px' }, '最多 7 个人');
    S.add(cap7); S.fade(cap7, t7 + 0.6);
    // the line
    const lx = x0 + 7 * gap - 4;
    const sv = h('svg', { width: W, height: H, style: { position: 'absolute', left: 0, top: 0 } });
    const ln = h('path', { d: `M540,330 L540,950 L${lx},950 L${lx},1130`, fill: 'none', stroke: C.red, 'stroke-width': 5, 'stroke-dasharray': '18 12' });
    sv.append(ln); S.add(sv);
    const LN = 620 + (lx - 540) + 180;
    S.on(t => { const p = pr(t, t8 + 0.35, 1.1, 'io'); ln.style.strokeDasharray = '18 12'; ln.style.clipPath = `inset(${(1 - p) * 100}% 0 0 0)`; ln.style.opacity = pr(t, t8 + 0.3, 0.3); ln.setAttribute('stroke-width', lerp(5, 8, pr(t, tLine - 0.1, 0.5))); });
    // abacus
    const ab = h('svg', { width: 472, height: 160, viewBox: '0 0 560 190', style: { position: 'absolute', left: '80px', top: '1176px' } });
    ab.append(h('rect', { x: 4, y: 4, width: 552, height: 182, fill: 'none', stroke: C.kraft, 'stroke-width': 8, rx: 6 }), h('line', { x1: 4, y1: 62, x2: 556, y2: 62, stroke: C.kraft, 'stroke-width': 7 }));
    const beads = [];
    for (let i = 0; i < 9; i++) {
      const x = 40 + i * 60;
      ab.append(h('line', { x1: x, y1: 8, x2: x, y2: 182, stroke: 'rgba(186,148,96,.55)', 'stroke-width': 3 }));
      const top = h('ellipse', { cx: x, cy: 26, rx: 22, ry: 11, fill: C.paper }); ab.append(top); beads.push({ el: top, y0: 26, y1: 45, k: i });
      for (let j = 0; j < 4; j++) { const b = h('ellipse', { cx: x, cy: 104 + j * 23, rx: 22, ry: 11, fill: j === 0 && i % 3 === 1 ? C.red : C.paper }); ab.append(b); if (j === 0) beads.push({ el: b, y0: 104, y1: 80, k: i + 3 }); }
    }
    S.add(ab); S.fadeUp(ab, tAb - 0.2);
    S.on(t => beads.forEach(b => { const on = [1, 4, 6, 8, 11].includes(b.k); const p = on ? pr(t, tAb + 0.3 + (b.k % 5) * 0.16, 0.28, 'io') : 0; b.el.setAttribute('cy', lerp(b.y0, b.y1, p)); }));
    const capA = box(600, 1186, 420, null, 'song', { fontWeight: 800, fontSize: '50px', lineHeight: '1.4', color: C.paper }, '一百多年前<br><span class="gold">一道算术题</span>');
    S.add(capA); S.fadeUp(capA, tAb + 0.1);
  } });

  /* title card */
  const tt0 = tEnd, tt1 = TL.secs.s2.s + 0.1;
  ENGINE.scene({ id: 'title', t0: tt0, t1: tt1, cls: 'bg-kraft', fadeIn: 0.4, fadeOut: 0.4, build(S) {
    S.cam({ s0: 1.0, s1: 1.05 });
    const top = box(0, 330, 1080, null, 'hei c', { fontWeight: 700, fontSize: '36px', letterSpacing: '12px', color: C.ink }, '改革开放系列 · 第 3 期');
    const sub = box(0, 392, 1080, null, 'hei c', { fontWeight: 500, fontSize: '30px', letterSpacing: '10px', color: 'rgba(26,20,16,.7)' }, '企 业 家 线');
    const l1 = box(0, 520, 1080, null, 'song c', { fontWeight: 900, fontSize: '178px', lineHeight: '1.15', letterSpacing: '8px', color: C.ink }, '雇<span style="color:#a8281f">八</span>个人');
    const l2 = box(0, 740, 1080, null, 'song c', { fontWeight: 900, fontSize: '128px', lineHeight: '1.15', letterSpacing: '4px', color: C.ink }, '算不算资本家');
    const rule = box(340, 930, 400, 6, '', { background: C.ink });
    // hand-painted sign
    const sign = box(190, 1010, 700, 250, '', { background: 'linear-gradient(#7c2218,#63190f)', boxShadow: '0 16px 40px rgba(0,0,0,.45), inset 0 0 0 10px rgba(0,0,0,.18), inset 0 0 0 14px rgba(232,221,198,.35)', transformOrigin: 'center' });
    sign.innerHTML = `<div class="brush c" style="font-size:150px;line-height:250px;white-space:nowrap;color:#f1e6cd;letter-spacing:4px;text-shadow:0 3px 0 rgba(0,0,0,.35)">傻子瓜子</div>`;
    S.add(top, sub, l1, l2, rule, sign);
    S.fade(top, tt0 + 0.2); S.fade(sub, tt0 + 0.3);
    S.a(l1, { at: tt0 + 0.35, d: 0.7, from: { o: 0, y: 40 } });
    S.a(l2, { at: tt0 + 0.6, d: 0.7, from: { o: 0, y: 40 } });
    S.a(rule, { at: tt0 + 0.9, d: 0.6, e: 'io', from: { sx: 0 } });
    S.a(sign, { at: tt0 + 1.15, d: 0.5, e: 'back', from: { o: 0, s: .8, r: -6 }, base: 'rotate(-2.5deg)' });
  } });
})();
