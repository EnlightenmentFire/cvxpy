/* S5 吵 */
(function () {
  const sec = TL.secs.s5;
  chapter('4', '吵', sec.s, sec.n + 0.25, '大字报 ／ 《光明日报》');
  const HD = '四 · 吵';

  /* 5a 大字报 */
  const a0 = sec.n, a1 = c('e4') - 0.15;
  ENGINE.scene({ id: 's5wall', t0: a0, t1: a1 + 0.3, cls: '', build(S) {
    // brick wall
    const wall = box(-40, -40, 1160, 2000, '', { background: `linear-gradient(rgba(20,14,10,.38),rgba(20,14,10,.62)), repeating-linear-gradient(0deg, transparent 0 70px, #2a211b 70px 78px), repeating-linear-gradient(90deg, #6d3b2c 0 164px, #2a211b 164px 172px)` });
    const wall2 = box(-40, -40, 1160, 2000, '', { background: `repeating-linear-gradient(0deg, transparent 0 78px, rgba(0,0,0,0) 78px 156px)`, opacity: 1 });
    S.add(wall);
    // offset alternate brick rows using stripes
    for (let r = 0; r < 26; r += 2) { const row = box(-126, -40 + r * 78, 1300, 70, '', { background: `repeating-linear-gradient(90deg, #73402f 0 164px, #2a211b 164px 172px)`, opacity: .92 }); S.add(row); }
    const shade = box(0, 0, 1080, 1920, '', { background: 'radial-gradient(ellipse 80% 55% at 50% 42%, rgba(0,0,0,0) 40%, rgba(0,0,0,.6) 100%), linear-gradient(rgba(25,18,12,.35),rgba(25,18,12,.35))' }); S.add(shade);
    header(S, HD);
    S.cam({ s0: 1.0, s1: 1.06 });
    const poster = box(110, 330, 860, 940, 'bg-paper', { background: 'url("../assets/paper.jpg")', boxShadow: '0 20px 50px rgba(0,0,0,.6)', padding: '46px 30px 0' });
    const lines = ['傻子瓜子呆子报', '呆子报道傻子笑', '四项原则全不要', '如此报纸实胡闹'];
    const ts = [c('e2'), cw('e2', '呆子报道'), c('e3'), cw('e3', '如此')], te = [cw('e2', '呆子报道') - 0.1, ce('e2'), cw('e3', '如此') - 0.1, ce('e3')];
    lines.forEach((ln, i) => { const e = h('div', { cls: 'brush c', style: { fontSize: '106px', lineHeight: '196px', color: '#17110c', whiteSpace: 'nowrap' } }, ln); poster.append(e); S.a(e, { at: ts[i] - 0.05, d: Math.max(0.8, te[i] - ts[i]), e: 'lin', from: {}, clip: 'x' }); });
    poster.append(h('div', { cls: 'demo', style: { right: '20px', bottom: '16px' } }, '大字报示意'));
    for (const [x, y] of [[20, 14], [800, 10], [16, 898], [806, 900]]) poster.append(box(x, y, 40, 26, '', { background: 'rgba(120,100,70,.5)', transform: `rotate(${(x + y) % 9 - 4}deg)` }));
    S.add(poster); S.a(poster, { at: cw('e1', '贴了') - 0.3, d: 0.45, e: 'out5', from: { o: 0, s: 1.25, r: 3 }, base: 'rotate(-1.2deg)' });
    src(S, 1296, '字句据《光明日报》记者回忆文章；张贴者、时间各篇说法不一', c('e2') + 0.5, null, C.paper);
  } });

  /* 5b 光明日报两次报道 */
  const b0 = a1, b1 = c('e6') - 0.15;
  ENGINE.scene({ id: 's5gmrb', t0: b0, t1: b1 + 0.3, cls: 'bg-dark', build(S) {
    header(S, HD);
    S.cam({ s0: 1.0, s1: 1.04 });
    const t1 = cw('e4', '1982年'), tP = cw('e4', '短评'), t2 = cw('e4', '1983年');
    const lab = box(70, 312, 940, null, 'song', { fontWeight: 900, fontSize: '60px', color: C.paper }, '另一种声音');
    S.add(lab); S.fadeUp(lab, b0 + 0.15);
    const p1 = paperMock(70, 410, 880, 600, { mast: '光明日报', date: '1982 年 12 月 20 日<br>第 1 版',
      body: `<div style="display:flex;gap:22px"><div style="flex:1.5"><div class="song" style="font-weight:900;font-size:35px;line-height:1.3">个体经营的“傻子瓜子”价廉物美信誉高，国营企业的“迎春瓜子”面临挑战赶上去</div>${bars(4)}</div>
        <div id="dp" style="flex:1;border:4px solid ${C.ink};padding:12px 14px;align-self:flex-start"><div class="hei" style="font-weight:700;font-size:26px;letter-spacing:8px;color:${C.red2}">短评</div><div class="song" style="font-weight:900;font-size:56px;line-height:1.25">有点<br>竞争好</div>${bars(2)}</div></div>` });
    S.add(p1); S.a(p1, { at: cw('e4', '登在') - 0.2, d: 0.7, from: { o: 0, y: 50, r: 2 }, base: 'rotate(-1deg)' });
    const dp = p1.querySelector('#dp'); S.on(t => { const p = pr(t, tP - 0.1, 0.5); dp.style.background = `rgba(210,160,60,${0.45 * p})`; });
    const p2 = paperMock(150, 800, 860, 440, { mast: '光明日报', ms: 66, date: '1983 年 1 月 4 日<br>第 2 版',
      body: `<div class="song" style="font-weight:900;font-size:68px;line-height:1.3;text-align:center;padding:6px 0 10px;white-space:nowrap">“傻子”和他的瓜子</div>${cols(3, 3)}` });
    S.add(p2); S.a(p2, { at: t2 - 0.3, d: 0.7, from: { o: 0, y: 80, r: -3 }, base: 'rotate(1.2deg)' });
    src(S, 1296, '标题、版次据当年采访记者的回忆文章；原版未见', t1 + 0.5);
  } });

  /* 5c 三方说法 */
  const c0 = b1, c1 = c('e9') - 0.15;
  ENGINE.scene({ id: 's5say', t0: c0, t1: c1 + 0.3, cls: 'bg-dark', build(S) {
    header(S, HD);
    S.cam({ s0: 1.0, s1: 1.035 });
    const card = (y, hgt, who, html, at) => { const e = box(70, y, 940, hgt, 'bg-paper', { background: 'url("../assets/paper.jpg")', boxShadow: '0 12px 30px rgba(0,0,0,.45)', padding: '24px 34px', color: C.ink },
      `<div style="display:inline-block;background:${C.ink};color:${C.paper};font-family:Hei;font-weight:700;font-size:34px;letter-spacing:6px;padding:4px 18px 6px">${who}</div><div class="song" style="font-weight:800;font-size:50px;line-height:1.42;margin-top:14px">${html}</div>`); S.add(e); S.a(e, { at, d: 0.6, from: { o: 0, x: -40 } }); return e; };
    card(312, 290, '税务部门说', '他按时交税，<br>是这一片的<span class="red">纳税大户</span>。', cw('e6', '税务部门') - 0.2);
    card(630, 290, '派出所说', '无业青年进了他的作坊，<br>有了收入，<span class="red">不再打架斗殴</span>。', c('e7') - 0.1);
    const k = card(948, 320, '国营“迎春瓜子”', '也跟着降价，每斤比他<br>还低 <span class="red" style="font-size:86px;line-height:1">0.24</span> 元 <span class="hei" style="font-size:34px;font-weight:600">（便宜一成多）</span>', c('e8') - 0.1);
    src(S, 1296, '以上据《光明日报》记者 1999 年的回忆文章', cw('e6', '税务部门') + 0.4);
  } });

  /* 5d 一块钱怎么分 */
  const d0 = c1, d1 = c('e12') - 0.15;
  ENGINE.scene({ id: 's5coin', t0: d0, t1: d1 + 0.3, cls: 'bg-paper', build(S) {
    header(S, HD, false);
    S.cam({ s0: 1.0, s1: 1.035 });
    const ink = C.ink;
    const ti = box(70, 306, 940, null, 'song', { fontWeight: 900, fontSize: '58px', color: ink }, '1982 年 · 每 1 块钱收入怎么分');
    S.add(ti); S.fadeUp(ti, cw('e9', '1982年') - 0.3);
    const cx = 540, cy = 690, R = 270;
    const sv = h('svg', { width: W, height: H, style: { position: 'absolute', left: 0, top: 0 } }); S.add(sv);
    const parts = [
      { v: 44.6, col: ink, lab: '年广久个人', money: '4 毛 4 分 6', at: cw('e10', '年广久') - 0.15 },
      { v: 12.0, col: C.gold, lab: '雇工工资', money: '1 毛 2', at: cw('e10', '工人工资') - 0.15 },
      { v: 43.33, col: C.red2, lab: '上交国家税费', money: '4 毛 3', at: cw('e10', '交给国家') - 0.15 },
    ];
    const tot = 100; let a = -90 - 44.6 / 100 * 360 / 2 + 44.6 / 100 * 360 / 2; a = -90;
    const P = (ang, r) => [cx + r * Math.cos(ang * Math.PI / 180), cy + r * Math.sin(ang * Math.PI / 180)];
    // whole coin first
    const whole = h('g', {}); whole.append(h('circle', { cx, cy, r: R, fill: C.gold, stroke: 'rgba(0,0,0,.4)', 'stroke-width': 4 }), h('circle', { cx, cy, r: R - 34, fill: 'none', stroke: 'rgba(0,0,0,.3)', 'stroke-width': 4 }));
    whole.append(h('text', { x: cx, y: cy + 60, 'text-anchor': 'middle', 'font-family': 'Song', 'font-weight': 900, 'font-size': 190, fill: 'rgba(26,20,16,.85)' }, '1元'));
    sv.append(whole);
    const tCut = cw('e10', '年广久') - 0.5;
    S.on(t => { whole.style.opacity = pr(t, d0 + 0.3, 0.5) * (1 - pr(t, tCut, 0.35)); whole.setAttribute('transform', `translate(${cx},${cy}) scale(${lerp(.7, 1, pr(t, d0 + 0.3, 0.5, 'back'))}) translate(${-cx},${-cy})`); });
    parts.forEach((p, i) => {
      const sweep = p.v / tot * 360, a0 = a, a1 = a + sweep, mid = (a0 + a1) / 2; a = a1;
      const [x0, y0] = P(a0, R), [x1, y1] = P(a1, R);
      const g = h('g', {});
      g.append(h('path', { d: `M${cx},${cy} L${x0},${y0} A${R},${R} 0 ${sweep > 180 ? 1 : 0} 1 ${x1},${y1} Z`, fill: p.col, stroke: C.paper, 'stroke-width': 5 }));
      const [tx, ty] = P(mid, R * (i === 1 ? 0.66 : 0.52));
      g.append(h('text', { x: tx, y: ty + (i === 1 ? 16 : 20), 'text-anchor': 'middle', 'font-family': 'Song', 'font-weight': 900, 'font-size': i === 1 ? 44 : 60, fill: i === 1 ? ink : C.paper }, p.v + '%'));
      sv.append(g);
      const [ex, ey] = P(mid, 26);
      S.on(t => { const q = pr(t, tCut, 0.4), e = pr(t, p.at, 0.5, 'back'); g.style.opacity = q * lerp(.35, 1, pr(t, p.at, 0.3)); g.setAttribute('transform', `translate(${(ex - cx) * e},${(ey - cy) * e})`); });
    });
    // legend rows
    parts.forEach((p, i) => { const y = 1010 + i * 92; const e = box(70, y, 940, 80, '', { borderTop: `2px solid rgba(26,20,16,.3)`, color: ink },
      `<div style="position:absolute;left:0;top:18px;width:44px;height:44px;background:${p.col}"></div><div class="hei" style="position:absolute;left:66px;top:12px;font-weight:700;font-size:42px">${p.lab}</div><div class="song" style="position:absolute;right:0;top:4px;font-weight:900;font-size:54px;color:${p.col === C.gold ? '#8a6414' : p.col}">${p.money}</div>`); S.add(e); S.a(e, { at: p.at, d: 0.5, from: { o: 0, x: -30 } }); });
    // comparison (e11)
    const cmp = box(0, 300, 1080, 1010, 'bg-paper', { background: 'url("../assets/paper.jpg")' }); S.add(cmp); S.fade(cmp, c('e11') - 0.25);
    const bar = (y, lab, v, col, at) => { const l = box(70, y, 400, null, 'hei', { fontWeight: 700, fontSize: '40px', color: ink }, lab); const b = box(70, y + 60, v * 15, 84, '', { background: col }); const n = box(70 + v * 15 + 18, y + 62, 300, null, 'song', { fontWeight: 900, fontSize: '62px', color: col === C.gold ? '#8a6414' : col, whiteSpace: 'nowrap' }, v + '%'); cmp.append(l, b, n); S.a(b, { at, d: 0.7, e: 'io', from: {}, clip: 'x' }); S.fade(l, at - 0.1); S.fade(n, at + 0.4); };
    const tG = c('e11'), tZ = cw('e11', '他自己拿的'), tW = cw('e11', '工人拿的');
    bar(60, '交给国家', 43.33, C.red2, tG); bar(230, '他自己拿', 44.6, ink, tZ - 0.1); bar(520, '工人工资', 12.0, C.gold, tW - 0.1);
    const eq = box(70, 396, 940, null, 'song', { fontWeight: 900, fontSize: '60px', color: ink }, '↑ 差不多一样多'); cmp.append(eq); S.fadeUp(eq, cw('e11', '差不多') - 0.1);
    const th = box(70, 690, 940, null, 'song', { fontWeight: 900, fontSize: '60px', color: ink }, '↑ 不到他的<span class="red">三分之一</span>'); cmp.append(th); S.fadeUp(th, cw('e11', '不到') - 0.1);
    src(S, 1296, '转引自人民网 2018 年文章所引的一份调查；原件未见，仅供参考', cw('e9', '原件') - 0.2, null, ink);
  } });

  /* 5e 近60家 + takeaway */
  const e0 = d1, e1 = sec.e;
  ENGINE.scene({ id: 's5sixty', t0: e0, t1: e1 + 0.2, cls: 'bg-dark', build(S) {
    header(S, HD);
    S.cam({ s0: 1.0, s1: 1.05 });
    const n = box(70, 300, 940, null, 'song', { fontWeight: 900, fontSize: '250px', lineHeight: '1', color: C.red }, '<span style="font-size:90px;color:#e8ddc6">近</span>60<span style="font-size:90px;color:#e8ddc6"> 家</span>');
    S.add(n); S.a(n, { at: e0 + 0.15, d: 0.6, from: { o: 0, y: 30 } });
    const sub = box(80, 566, 900, null, 'hei', { fontWeight: 600, fontSize: '40px', letterSpacing: '4px', color: C.paper }, '芜湖 · 做瓜子的（据报道）');
    S.add(sub); S.fade(sub, e0 + 0.4);
    const t0 = cw('e12', '冒出') - 0.2, rr = RNG(21);
    for (let i = 0; i < 60; i++) { const col = i % 10, row = Math.floor(i / 10);
      const w = h('svg', { width: 84, height: 70, viewBox: '0 0 84 70', style: { position: 'absolute', left: (78 + col * 93) + 'px', top: (680 + row * 100) + 'px' } });
      w.append(h('path', { d: 'M6,26 C10,58 28,64 42,64 C56,64 74,58 78,26 Z', fill: i === 0 ? C.red : C.kraft }), h('ellipse', { cx: 42, cy: 26, rx: 36, ry: 8, fill: '#17130f', stroke: i === 0 ? C.red : C.kraft, 'stroke-width': 3 }));
      for (let k = 0; k < 3; k++) w.append(h('ellipse', { cx: 30 + k * 12, cy: 16 - (k % 2) * 6, rx: 5, ry: 2.6, fill: C.paper, transform: `rotate(${k * 50} ${30 + k * 12} ${16 - (k % 2) * 6})` }));
      S.add(w); S.a(w, { at: i === 0 ? e0 + 0.3 : t0 + rr() * 1.3, d: 0.35, e: 'back', from: { o: 0, s: .3 } }); }
    takeaway(S, 'e13', '同一个作坊，<br>一边看他<em>有没有越线</em>，<br>一边看<em>税、就业和价钱</em>。<br>两种说法，同时摆着。');
  } });
})();
