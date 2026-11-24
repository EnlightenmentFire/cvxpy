/* S2 一道算术题 */
(function () {
  const sec = TL.secs.s2;
  chapter('1', '一道算术题', sec.s, sec.n + 0.25, '1981 · 国务院规定 ／ 1867 ·《资本论》');

  /* 2b 文件：帮手 + 学徒 = 7 */
  const b0 = sec.n, b1 = c('a5') - 0.15;
  ENGINE.scene({ id: 's2doc', t0: b0, t1: b1 + 0.3, cls: 'bg-dark', build(S) {
    header(S, '一 · 一道算术题');
    S.cam({ s0: 1.0, s1: 1.035 });
    const doc = docMock(100, 312, 880, 700, {
      head: '国 务 院', hs: 70, no: '国发〔1981〕108号', title: '关于城镇非农业个体经济<br>若干政策性规定', date: '一九八一年七月七日', ts: 42, bs: 36,
      body: `${bars(1, [70])}<div id="cl5">（五）个体经营户，一般是一人经营或家庭经营；必要时，经过工商行政管理部门批准，<span class="hl" id="hlA">可以请一至两个帮手</span>；技术性较强或者有特殊技艺的，<span class="hl" id="hlB">可以带两三个最多不超过五个学徒</span>。</div>${bars(1, [55])}`
    });
    S.add(doc); S.a(doc, { at: b0 + 0.1, d: 0.8, from: { o: 0, y: 60, r: 1.5 }, base: 'rotate(-0.6deg)' });
    const hlA = doc.querySelector('#hlA'), hlB = doc.querySelector('#hlB');
    const tA = cw('a3', '可以请'), tB = cw('a3', '可以带');
    S.on(t => { for (const [e, at, dur] of [[hlA, tA, 1.0], [hlB, tB, 1.6]]) { const p = pr(t, at, dur, 'io'); e.style.background = `linear-gradient(90deg, rgba(210,160,60,.8) ${p * 100}%, transparent ${p * 100}%)`; e.style.boxDecorationBreak = 'clone'; e.style.webkitBoxDecorationBreak = 'clone'; } });
    chip(S, 1060, '个体户', '自己给自己干的小买卖。当时允许，但人数有限。', cw('a1', '个体户') - 0.1, c('a4') - 0.25);
    // 2 + 5 = 7
    const y = 1070, g = h('div', { cls: 'abs', style: { left: '70px', top: y + 'px', width: '940px', height: '260px' } });
    S.add(g);
    const tH = cw('a4', '2'), tX = cw('a4', '5'), t7 = cw('a4', '7');
    const mk = (x, n, col, lab, at) => { const w = h('div', { cls: 'abs', style: { left: x + 'px', top: '0px' } });
      for (let i = 0; i < n; i++) { const pz = person(104, col, { left: i * 72 + 'px', top: '0px' }); w.append(pz); S.a(pz, { at: at + i * 0.08, d: 0.4, e: 'back', from: { o: 0, s: .4, y: 16 } }); }
      const lb = box(0, 116, n * 72 + 8, null, 'hei c', { fontWeight: 600, fontSize: '32px', letterSpacing: '4px', color: C.paper, borderTop: `3px solid ${col}`, paddingTop: '8px' }, lab);
      w.append(lb); S.fade(lb, at + 0.2); g.append(w); return w; };
    mk(0, 2, C.gold, '帮手 2', tH - 0.15);
    const plus = box(160, 6, 60, null, 'song c', { fontWeight: 900, fontSize: '80px', color: C.paper }, '+'); g.append(plus); S.fade(plus, tX - 0.3);
    mk(238, 5, C.kraft, '学徒 5', tX - 0.15);
    const eq = box(618, 6, 60, null, 'song c', { fontWeight: 900, fontSize: '80px', color: C.paper }, '='); g.append(eq); S.fade(eq, t7 - 0.45);
    const seven = box(690, -62, 250, null, 'song c', { fontWeight: 900, fontSize: '250px', lineHeight: '1', color: C.red }, '7'); g.append(seven); S.slam(seven, t7 - 0.2);
    src(S, 1296, '国发〔1981〕108号第（五）项原文', c('a3') + 0.3);
  } });

  /* 2c 林子力 · 《资本论》 */
  const c0 = b1, c1 = c('a7') - 0.15;
  ENGINE.scene({ id: 's2book', t0: c0, t1: c1 + 0.3, cls: 'bg-dark', build(S) {
    header(S, '一 · 一道算术题');
    S.cam({ s0: 1.0, s1: 1.05 });
    const q = box(70, 310, 940, null, 'song', { fontWeight: 900, fontSize: '120px', color: C.paper, letterSpacing: '4px' }, '为什么是 <span class="red" style="font-size:170px">7</span>？');
    S.add(q); S.a(q, { at: c0 + 0.15, d: 0.6, from: { o: 0, y: 30 }, out: cw('a5', '中央书记处') - 0.5, od: 0.4 });
    nameTag(S, 80, 326, '林子力', '时在中央书记处研究室', cw('a5', '中央书记处') - 0.15);
    // book
    const bk = box(270, 530, 540, 640, '', { background: 'linear-gradient(100deg,#3b1512 0%,#5a1f18 9%,#4a1a14 11%,#55201a 100%)', boxShadow: '0 30px 60px rgba(0,0,0,.6), inset 0 0 0 3px rgba(0,0,0,.4)', borderRadius: '4px 10px 10px 4px' });
    bk.innerHTML = `<div style="position:absolute;inset:36px 36px 36px 84px;border:3px solid ${C.gold};opacity:.85"></div><div style="position:absolute;inset:46px 46px 46px 94px;border:1.5px solid ${C.gold};opacity:.6"></div>
      <div class="song" style="position:absolute;left:84px;right:36px;top:110px;text-align:center;font-weight:900;font-size:116px;letter-spacing:12px;color:${C.gold}">资本论</div>
      <div class="song" style="position:absolute;left:84px;right:36px;top:280px;text-align:center;font-weight:700;font-size:44px;letter-spacing:12px;color:${C.gold}">第 一 卷</div>
      <div style="position:absolute;left:220px;right:172px;top:366px;height:3px;background:${C.gold};opacity:.7"></div>
      <div class="song" style="position:absolute;left:84px;right:36px;top:404px;text-align:center;font-weight:600;font-size:34px;letter-spacing:6px;color:${C.gold};opacity:.9">卡尔 · 马克思</div>
      <div class="hei" style="position:absolute;left:84px;right:36px;bottom:70px;text-align:center;font-weight:500;font-size:26px;letter-spacing:4px;color:${C.gold};opacity:.7">1867 年初版</div>`;
    S.add(bk); S.a(bk, { at: cw('a5', '《资本论》') - 0.5, d: 0.8, from: { o: 0, y: 70, r: 4 }, base: 'rotate(-2deg)' });
    const ch9 = box(70, 1205, 940, null, 'song c', { fontWeight: 700, fontSize: '40px', letterSpacing: '2px', color: C.paper }, '第三篇 第九章《剩余价值率和剩余价值量》');
    S.add(ch9); S.fadeUp(ch9, cw('a5', '算例') - 0.5);
    src(S, 1292, '林子力引用一事，据后来的回顾文章；当年原文未见', cw('a5', '据后来') , null, C.paper).style.textAlign = 'center';
  } });

  /* 2d 算账 */
  const d0 = c1, d1 = c('a14') - 0.15;
  ENGINE.scene({ id: 's2calc', t0: d0, t1: d1 + 0.3, cls: 'bg-paper', build(S) {
    header(S, '一 · 一道算术题', false);
    const ink = C.ink;
    const ti = box(70, 300, 940, null, 'song', { fontWeight: 900, fontSize: '54px', color: ink, letterSpacing: '2px' }, '书里的比方：<span style="font-weight:600;font-size:38px">一个工人的一天</span>');
    S.add(ti); S.fadeUp(ti, d0 + 0.15);
    // time bar: 8h + 4h  (75px per hour)
    const bx = 90, by = 400, hw = 75;
    const seg8 = box(bx, by, hw * 8, 96, '', { background: ink }), seg4 = box(bx + hw * 8, by, hw * 4, 96, '', { background: C.red2 });
    seg8.innerHTML = `<div class="song" style="color:${C.paper};font-weight:900;font-size:54px;line-height:96px;padding-left:24px">8 小时</div>`;
    seg4.innerHTML = `<div class="song" style="color:${C.paper};font-weight:900;font-size:54px;line-height:96px;text-align:center">4 小时</div>`;
    S.add(seg8, seg4);
    const t8 = cw('a7', '8'), t4 = cw('a7', '4');
    S.a(seg8, { at: t8 - 0.3, d: 0.9, e: 'io', from: {}, clip: 'x' }); S.a(seg4, { at: t4 - 0.3, d: 0.7, e: 'io', from: {}, clip: 'x' });
    for (let i = 1; i < 12; i++) { const tk = box(bx + hw * i - 1, by + 96, 2, 12, '', { background: ink, opacity: .5 }); S.add(tk); S.fade(tk, t8 - 0.2 + i * 0.05); }
    const l8 = box(bx, by + 118, hw * 8, null, 'hei', { fontWeight: 600, fontSize: '32px', color: ink }, '挣回自己的生活（工资）');
    const l4 = box(bx + hw * 8, by + 118, hw * 4, null, 'hei c', { fontWeight: 700, fontSize: '32px', color: C.red2 }, '归雇主');
    S.add(l8, l4); S.fade(l8, cw('a7', '挣回')); S.fade(l4, cw('a7', '归雇主') - 0.1);
    chip(S, 800, '剩余价值', '马克思的说法：工人干活创造的价值，扣掉工资，剩下的那部分。', cw('a8', '剩余价值') - 0.2, c('a9') - 0.1);
    // 4 / 8 = 1/2
    const eq = box(70, 600, 940, 120, '', { color: ink });
    eq.innerHTML = `<div class="song" style="font-weight:900;font-size:62px;display:flex;align-items:center;gap:16px;white-space:nowrap"><span class="red">4</span> ÷ 8 = <span class="red">½</span><span class="hei" style="font-weight:600;font-size:33px;margin-left:14px;line-height:1.3">雇 1 个工人，雇主一天到手<br><b class="red">半份</b>工人的生活费</span></div>`;
    S.add(eq); S.fadeUp(eq, c('a10') - 0.45);
    const hc = coin(104, .5); hc.style.left = '890px'; hc.style.top = '606px'; S.add(hc); S.pop(hc, c('a10') - 0.4);
    const big = box(70, 690, 940, 600, '', { color: ink });
    big.innerHTML = `<div class="song c" style="font-weight:900;font-size:190px;line-height:1.1;white-space:nowrap"><span class="red">4</span> ÷ 8 = <span class="red">½</span></div><div class="hei c" style="font-weight:700;font-size:52px;line-height:1.5;margin-top:26px">雇 1 个工人<br>雇主一天到手 <span class="red">半份</span> 工人的生活费</div>`;
    S.add(big); S.a(big, { at: c('a9') - 0.05, d: 0.6, from: { o: 0, y: 40 }, out: c('a10') - 0.5, od: 0.35, to: { o: 0, y: -60, s: .8 } });
    const bc = coin(170, .5); bc.style.left = '455px'; bc.style.top = '1130px'; S.add(bc); S.a(bc, { at: cw('a9', '半份') - 0.1, d: 0.45, e: 'back', from: { o: 0, s: .4 }, out: c('a10') - 0.5, od: 0.3 });
    // rows
    const rows = [
      { id: 'a10', n: 1, coins: .5, w: '1', txt: '半份 · 不够，自己还要干活', key: '1' },
      { id: 'a11', n: 2, coins: 1, w: '2', txt: '一份 · 普通工人的日子', key: '2' },
      { id: 'a12', n: 4, coins: 2, w: '4', txt: '两份 · 比工人好一倍', key: '4' },
      { id: 'a13', n: 8, coins: 4, w: '8', txt: '两份自己花 + 两份扩大生产', key: '8' },
    ];
    const ry0 = 752, rh = 146;
    rows.forEach((r, i) => {
      const y = ry0 + i * rh, at = c(r.id) - 0.1, last = i === 3;
      const row = box(70, y, 940, rh - 12, '', { borderTop: `2px solid rgba(26,20,16,.35)`, background: last ? 'rgba(168,40,31,.12)' : 'transparent', outline: last ? `4px solid ${C.red2}` : 'none' });
      S.add(row); S.a(row, { at, d: 0.5, from: { o: 0, x: -24 } });
      const num = box(14, 6, 150, null, 'song', { fontWeight: 900, fontSize: '50px', color: last ? C.red2 : ink, whiteSpace: 'nowrap' }, `雇 <span style="font-size:${last ? 96 : 76}px;line-height:1">${r.w}</span> 个`);
      row.append(num);
      for (let k = 0; k < r.n; k++) { const pz = person(64, last ? C.red2 : ink, { left: (250 + k * 43) + 'px', top: '8px' }); row.append(pz); S.a(pz, { at: at + 0.15 + k * 0.05, d: 0.3, e: 'back', from: { o: 0, s: .4 } }); }
      const nc = Math.ceil(r.coins), cx0 = 940 - 14 - nc * 66;
      const tc = last ? cw('a13', '8', 0) - 0.5 : at + 0.5;
      for (let k = 0; k < nc; k++) { const cc = coin(60, r.coins < 1 ? .5 : 1, last && k >= 2 ? '#c8372b' : null); cc.style.left = (cx0 + k * 66) + 'px'; cc.style.top = '10px'; row.append(cc); S.a(cc, { at: (last && k >= 2 ? cw('a13', '扩大生产') - 0.4 : last ? at + 0.2 : at + 0.45) + k * 0.07, d: 0.35, e: 'back', from: { o: 0, s: .3 } }); }
      const tx = box(250, 80, 680, null, 'hei', { fontWeight: 700, fontSize: '36px', color: last ? C.red2 : ink, letterSpacing: '1px' }, r.txt);
      row.append(tx); S.fade(tx, at + 0.55);
    });
    src(S, 1338 - 6, '《资本论》第一卷第九章：必要劳动“比如说每天8小时”，剩余劳动“比如说4小时”', d0 + 1.0).style.fontSize = '23px';
  } });

  /* 2e 七上八下 + takeaway */
  const e0 = d1, e1 = TL.secs.s2.e;
  ENGINE.scene({ id: 's2line', t0: e0, t1: e1 + 0.2, cls: 'bg-dark', build(S) {
    header(S, '一 · 一道算术题');
    S.cam({ s0: 1.0, s1: 1.05 });
    const tS = cw('a14', '不到'), tC = cw('a14', '到了'), tQ = cw('a14', '七上八下');
    const d7 = box(0, 330, 540, null, 'song c', { fontWeight: 900, fontSize: '470px', lineHeight: '1', color: C.paper }, '7');
    const d8 = box(540, 330, 540, null, 'song c', { fontWeight: 900, fontSize: '470px', lineHeight: '1', color: C.red }, '8');
    S.add(d7, d8); S.a(d7, { at: e0 + 0.2, d: 0.6, from: { o: 0, y: 30 } }); S.a(d8, { at: e0 + 0.35, d: 0.6, from: { o: 0, y: 30 } });
    const ln = box(537, 320, 6, 900, '', { background: `repeating-linear-gradient(${C.red} 0 18px, transparent 18px 30px)`, transformOrigin: 'top center' });
    S.add(ln); S.a(ln, { at: e0 + 0.5, d: 0.9, e: 'io', from: { sy: 0 } });
    const mkL = (x, title, sub, col, at) => { const e = box(x, 850, 540, null, 'c', { color: col }, `<div class="hei" style="font-weight:500;font-size:34px;letter-spacing:4px;opacity:.8">${sub}</div><div class="song" style="font-weight:900;font-size:104px;letter-spacing:6px;margin-top:8px">${title}</div>`); S.add(e); S.fadeUp(e, at); return e; };
    mkL(0, '小业主', '不到 8 个 · 自己还要干活', C.paper, tS - 0.1);
    mkL(540, '资本家', '到了 8 个', C.red, tC - 0.1);
    const st = box(290, 1090, 500, 170, 'brush c', { fontSize: '128px', lineHeight: '170px', color: C.gold, border: `6px solid ${C.gold}`, borderRadius: '10px', letterSpacing: '6px', whiteSpace: 'nowrap', background: 'rgba(27,22,18,.9)' }, '七上八下');
    S.add(st); S.a(st, { at: tQ - 0.15, d: 0.3, e: 'out5', from: { o: 0, s: 1.7 }, base: 'rotate(-4deg)' });
    src(S, 1296, '“8”不是书里的原话，是后人照这个算例推出来的', tQ + 0.5).style.textAlign = 'center';
    takeaway(S, 'a15', '那时候，<br>能不能多请一个帮工，<br>要<em>翻书</em>来定。');
  } });
})();
