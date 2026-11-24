/* S4 撞线 */
(function () {
  const sec = TL.secs.s4;
  chapter('3', '撞线', sec.s, sec.n + 0.25, '芜湖 ／ 广东高要 · 1981');
  const HD = '三 · 撞线';

  /* 4a 降价 */
  const a0 = sec.n, a1 = c('d2') - 0.15;
  ENGINE.scene({ id: 's4price', t0: a0, t1: a1 + 0.3, cls: 'bg-kraft', build(S) {
    header(S, HD, false);
    S.cam({ s0: 1.0, s1: 1.04 });
    const ink = C.ink;
    const d = box(80, 312, 900, null, 'hei', { fontWeight: 600, fontSize: '40px', letterSpacing: '4px', color: ink }, '1981 年 8 月 · 瓜子每斤');
    S.add(d); S.fadeUp(d, a0 + 0.15);
    const tA = cw('d1', '2.4'), tB = cw('d1', '1.76'), tC = cw('d1', '一斤便宜'), tD = cw('d1', '降了');
    const tag = (x, y, txt, col, at, big) => { const e = box(x, y, 430, 300, 'bg-paper', { boxShadow: '0 14px 34px rgba(0,0,0,.35)', borderTop: `14px solid ${col}` }, `<div class="song c" style="font-weight:900;font-size:${big ? 170 : 150}px;line-height:1.2;color:${col};padding-top:26px">${txt}</div><div class="hei c" style="font-weight:600;font-size:36px;letter-spacing:6px;color:${ink}">元 / 斤</div>`); S.add(e); S.a(e, { at, d: 0.5, e: 'back', from: { o: 0, s: .8 } }); return e; };
    const oldT = tag(70, 400, '2.40', ink, tA - 0.2);
    const strike = box(40, 150, 350, 10, '', { background: C.red2, transform: 'rotate(-12deg)', transformOrigin: 'left center' }); oldT.append(strike);
    S.a(strike, { at: tB - 0.35, d: 0.3, e: 'io', from: { sx: 0 }, base: 'rotate(-12deg)' });
    S.on(t => { oldT.style.filter = `saturate(${lerp(1, .4, pr(t, tB - 0.2, 0.4))})`; });
    tag(580, 400, '1.76', C.red2, tB - 0.15, true);
    const arr = box(505, 498, 70, null, 'song c', { fontWeight: 900, fontSize: '80px', color: ink }, '→'); S.add(arr); S.fade(arr, tB - 0.3);
    // bars
    const by = 800, full = 860;
    const b1 = box(90, by, full, 70, '', { background: ink }), b2 = box(90, by + 100, full * 1.76 / 2.4, 70, '', { background: C.red2 });
    const gap = box(90 + full * 1.76 / 2.4, by + 100, full * 0.64 / 2.4, 70, '', { border: `4px dashed ${C.red2}`, background: 'rgba(168,40,31,.12)' });
    gap.innerHTML = `<div class="song c" style="font-weight:900;font-size:40px;line-height:62px;color:${C.red2};white-space:nowrap">−0.64</div>`;
    S.add(b1, b2, gap); S.wipe(b1, tA, 0.7); S.wipe(b2, tB, 0.7); S.fade(gap, tC - 0.15);
    const r1 = box(70, 1030, 940, null, 'song', { fontWeight: 900, fontSize: '64px', lineHeight: '1.4', color: ink }, '一斤便宜 <span class="red">六毛四</span>');
    const r2 = box(70, 1130, 940, null, 'song', { fontWeight: 900, fontSize: '64px', lineHeight: '1.4', color: ink }, '降了 <span class="red">四分之一还多</span>');
    S.add(r1, r2); S.fadeUp(r1, tC - 0.1); S.fadeUp(r2, tD - 0.1);
    src(S, 1296, '价格与时间据《光明日报》1983年1月4日通讯', tB + 0.4, null, ink);
  } });

  /* 4b 雇工越过线 */
  const b0 = a1, b1 = c('d6') - 0.15;
  ENGINE.scene({ id: 's4hire', t0: b0, t1: b1 + 0.3, cls: 'bg-dark', build(S) {
    header(S, HD);
    S.cam({ s0: 1.0, s1: 1.04 });
    const tRep = c('d2'), tFew = cw('d4', '几个'), tTen = cw('d4', '十来个'), tHun = cw('d4', '超过'), tRule = cw('d4', '规定最多'), tMul = cw('d4', '十几倍');
    // small clipping
    const clip = box(70, 312, 940, 170, 'bg-news', { boxShadow: '0 12px 30px rgba(0,0,0,.5)', padding: '18px 28px', color: C.ink, background: 'url("../assets/newsprint.jpg")' }, `<div class="hei" style="font-weight:600;font-size:28px;letter-spacing:4px;opacity:.75">1981 年 9 月 · 芜湖当地报纸</div><div class="song" style="font-weight:900;font-size:52px;margin-top:10px;white-space:nowrap">货真价实的“傻子瓜子”</div><div class="demo" style="right:14px;bottom:10px;font-size:20px">标题据回忆 · 示意</div>`);
    S.add(clip); S.a(clip, { at: tRep - 0.1, d: 0.6, from: { o: 0, y: -30, r: -3 }, base: 'rotate(-1deg)', out: tFew - 0.5, od: 0.4 });
    chip(S, 1090, '雇工', '花钱请别人给你干活。', cw('d2', '雇工') - 0.15, tFew - 0.45);
    const wok = box(70, 560, 940, null, 'song c', { fontWeight: 900, fontSize: '76px', lineHeight: '1.5', color: C.paper }, '生意更旺<br><span class="gold">炒不过来，只能请人</span>');
    S.add(wok); S.a(wok, { at: cw('d2', '生意') - 0.1, d: 0.6, from: { o: 0, y: 30 }, out: tFew - 0.5, od: 0.4 });
    // counter + grid
    const cnt = box(70, 300, 600, null, 'song', { fontWeight: 900, fontSize: '230px', lineHeight: '1', color: C.red }, '0');
    const cl = box(80, 540, 800, null, 'hei', { fontWeight: 600, fontSize: '38px', letterSpacing: '4px', color: C.paper }, '雇工人数（据报道）');
    S.add(cnt, cl); S.fade(cnt, tFew - 0.3); S.fade(cl, tFew - 0.2);
    S.on(t => { let v; if (t < tTen - 0.2) v = lerp(0, 4, pr(t, tFew - 0.2, 0.5)); else if (t < tHun - 0.2) v = lerp(4, 12, pr(t, tTen - 0.2, 0.6)); else v = lerp(12, 104, pr(t, tHun - 0.2, 1.3, 'io'));
      const n = Math.round(v); cnt.innerHTML = n >= 104 ? '100<span style="font-size:120px">多</span>' : n; });
    const cols = 13, gx = 70, gy = 640, dx = 72, dy = 82, N = 104, ps = [];
    for (let i = 0; i < N; i++) { const pz = person(64, i < 7 ? C.paper : C.red, { left: (gx + (i % cols) * dx + 8) + 'px', top: (gy + Math.floor(i / cols) * dy) + 'px' }); pz.style.opacity = 0; S.add(pz); ps.push(pz); }
    S.on(t => { let v; if (t < tTen - 0.2) v = lerp(0, 4, pr(t, tFew - 0.2, 0.5)); else if (t < tHun - 0.2) v = lerp(4, 12, pr(t, tTen - 0.2, 0.6)); else v = lerp(12, 104, pr(t, tHun - 0.2, 1.3, 'io'));
      ps.forEach((p, i) => { const o = clamp(v - i); p.style.opacity = o; p.style.transform = `scale(${lerp(.5, 1, o)})`; }); });
    // rule line after 7th
    const rl = box(gx + 7 * dx - 2, gy - 22, 5, 108, '', { background: C.gold });
    const rlab = box(gx + 7 * dx + 12, gy - 34, null, null, 'hei', { fontWeight: 700, fontSize: '28px', letterSpacing: '2px', color: C.gold, whiteSpace: 'nowrap', background: 'rgba(27,22,18,.92)', padding: '2px 10px' }, '← 规定：最多 7 个');
    S.add(rl, rlab); S.a(rl, { at: tFew - 0.2, d: 0.4, from: { o: 0, sy: 0 } }); S.fade(rlab, tRule - 0.2); S.on(t => { rlab.style.zIndex = 5; });
    const mul = box(600, 330, 420, null, 'song', { fontWeight: 900, fontSize: '70px', lineHeight: '1.25', color: C.gold, textAlign: 'right' }, '7 的<br>十几倍');
    S.add(mul); S.fadeUp(mul, tMul - 0.2);
    src(S, 1310, '人数、年份各篇说法不一；此处只取量级', tHun + 0.6);
  } });

  /* 4c 陈志雄的鱼塘 */
  const c0 = b1, c1 = c('d8') - 0.15;
  ENGINE.scene({ id: 's4pond', t0: c0, t1: c1 + 0.3, cls: 'bg-dark', build(S) {
    header(S, HD);
    S.cam({ s0: 1.0, s1: 1.04 });
    // two province outlines
    const sv = h('svg', { width: W, height: H, style: { position: 'absolute', left: 0, top: 0 } }); S.add(sv);
    const mk = (G, ox, oy, sc, place, col, lab, at, lx, ly, pname) => {
      const g = h('g', { transform: `translate(${ox},${oy}) scale(${sc})` }); const p = h('path', { d: G.d, fill: 'rgba(232,221,198,.05)', stroke: C.paper, 'stroke-width': 3 / sc * 0.8, 'stroke-linejoin': 'round', opacity: .8 }); g.append(p); sv.append(g);
      S.on(t => { g.style.opacity = pr(t, at, 0.7); });
      const x = ox + G.places[place][0] * sc, y = oy + G.places[place][1] * sc;
      const d = box(x - 11, y - 11, 22, 22, '', { borderRadius: '50%', background: col, boxShadow: `0 0 0 7px ${col}33` }); S.add(d); S.pop(d, at + 0.3);
      const l = box(x + lx, y + ly, null, null, 'song', { fontWeight: 900, fontSize: '44px', color: col, whiteSpace: 'nowrap' }, lab); S.add(l); S.fade(l, at + 0.35);
      const pn = box(ox, oy + G.h * sc + 6, G.w * sc, null, 'hei c', { fontWeight: 500, fontSize: '26px', letterSpacing: '8px', color: C.dim }, pname); S.add(pn); S.fade(pn, at + 0.2);
    };
    mk(GEO.anhui, 110, 312, 0.29, '芜湖', C.red, '芜湖', c0 + 0.1, 18, -30, '安徽');
    mk(GEO.guangdong, 560, 345, 0.40, '高要', C.gold, '高要', cw('d6', '广东') - 0.2, -4, -68, '广东');
    nameTag(S, 80, 690, '陈志雄', '广东高要农民，承包鱼塘', cw('d6', '陈志雄') - 0.2).querySelector('.nm').style.fontSize = '66px';
    // ponds, area-proportional squares
    const k = 18, base = 1212, items = [[8, '头一年', cw('d6', '头一年')], [151, '第二年', cw('d6', '第三年') - 0.75], [355, '第三年', cw('d6', '第三年') - 0.1]];
    let x = 84;
    items.forEach(([mu, lab, at], i) => { const s = Math.sqrt(mu) * k; const e = box(x, base - s, s, s, '', { background: 'linear-gradient(160deg,#39606b,#27444d)', border: `3px solid ${C.paper}`, transformOrigin: 'left bottom', overflow: 'hidden' });
      e.innerHTML = Array.from({ length: Math.floor(s / 46) }, (_, j) => `<div style="position:absolute;left:0;right:0;top:${20 + j * 46}px;height:2px;background:rgba(232,221,198,.18)"></div>`).join('');
      S.add(e); S.a(e, { at: at - 0.1, d: 0.6, e: 'out5', from: { o: 0, s: 0.2 } });
      const l = box(x - 20, base + 10, s + 40, null, 'hei c', { fontWeight: 500, fontSize: '26px', color: C.dim, whiteSpace: 'nowrap' }, lab); S.add(l); S.fade(l, at);
      const n = box(x - 40, base - s - (i === 0 ? 78 : 0) + (i === 0 ? 0 : s / 2 - 50), s + 80, null, 'song c', { fontWeight: 900, fontSize: i === 0 ? '50px' : i === 1 ? '70px' : '96px', color: C.paper, whiteSpace: 'nowrap' }, `${mu}<span style="font-size:.5em"> 亩</span>`); S.add(n); S.fade(n, at + 0.1);
      x += s + (i === 0 ? 70 : 60); });
    const mul = box(600, 700, 420, null, 'song', { fontWeight: 900, fontSize: '62px', lineHeight: '1.25', color: C.gold, textAlign: 'right' }, '三年<br>大了四十多倍');
    S.add(mul); S.fadeUp(mul, cw('d6', '大了') - 0.15);
    const wk = box(70, 1258, 940, null, 'hei', { fontWeight: 600, fontSize: '32px', letterSpacing: '2px', color: C.paper }, '长年工（干满一年的）<b class="red" style="font-size:42px">5</b> 个，零工另算');
    S.add(wk); S.fade(wk, cw('d6', '长年工') - 0.1);
    src(S, 1316, '数字据《人民日报》1981年5月29日原文', cw('d6', '头一年') + 0.3);
  } });

  /* 4d 人民日报讨论三个月 + takeaway */
  const e0 = c1, e1 = sec.e;
  ENGINE.scene({ id: 's4rmrb', t0: e0, t1: e1 + 0.2, cls: 'bg-dark', build(S) {
    header(S, HD);
    S.cam({ s0: 1.0, s1: 1.04 });
    const np = paperMock(80, 312, 920, 640, { mast: '人民日报', date: '1981 年 5 月 29 日<br>第 2 版',
      body: `<div class="song" style="font-weight:900;font-size:62px;line-height:1.3;text-align:center;padding:10px 0 14px">一场关于承包鱼塘的争论</div>${cols(3, 4)}
        <div style="margin-top:14px;border:3px solid ${C.ink};padding:12px 18px"><div class="hei" style="font-weight:700;font-size:26px;letter-spacing:4px;color:${C.red2}">问题讨论 · 6 月起连续刊登读者来信</div><div class="song" style="font-weight:900;font-size:42px;line-height:1.3;white-space:nowrap">怎样看待陈志雄承包鱼塘问题？</div></div>` });
    S.add(np); S.a(np, { at: e0 + 0.1, d: 0.7, from: { o: 0, y: 50, r: 2 }, base: 'rotate(-0.8deg)' });
    // 3-month timeline
    const y = 1070, x0 = 110, x1 = 970, tS = cw('d8', '1981年5月29日'), tE = cw('d8', '8月30日');
    const line = box(x0, y, x1 - x0, 6, '', { background: C.paper, transformOrigin: 'left center' }); S.add(line); S.a(line, { at: tS, d: Math.max(0.8, tE - tS), e: 'io', from: { sx: 0 } });
    const mark = (x, lab, at, col) => { const d = box(x - 12, y - 9, 24, 24, '', { borderRadius: '50%', background: col || C.paper }); S.add(d); S.pop(d, at); const l = box(x - 130, y + 30, 260, null, 'hei c', { fontWeight: 600, fontSize: '32px', color: col || C.paper, whiteSpace: 'nowrap' }, lab); S.add(l); S.fade(l, at); };
    mark(x0, '5 月 29 日', tS, C.gold); mark(x1, '8 月 30 日', tE, C.gold);
    ['6 月', '7 月', '8 月'].forEach((m, i) => { const x = x0 + (x1 - x0) * [0.035, 0.36, 0.69][i]; const tk = box(x, y - 12, 3, 30, '', { background: C.dim }); S.add(tk); S.fade(tk, tS + 0.4 + i * 0.3); const l = box(x - 50, y - 60, 100, null, 'hei c', { fontWeight: 500, fontSize: '26px', color: C.dim }, m); S.add(l); S.fade(l, tS + 0.4 + i * 0.3); });
    const three = box(70, 1180, 940, null, 'song c', { fontWeight: 900, fontSize: '88px', color: C.paper, letterSpacing: '6px' }, '讨论了 <span class="red">三个月</span>');
    S.add(three); S.fadeUp(three, cw('d8', '前后') - 0.15);
    takeaway(S, 'd9', '两个人都没想<br>去碰那条线。<br>生意大了要人手，<br><em>人数自己越过了线。</em>');
  } });
})();
