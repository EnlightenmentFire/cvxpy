/* S7 放两年再看 + S8 收尾 */
(function () {
  const sec = TL.secs.s7;
  chapter('6', '放两年再看', sec.s, sec.n + 0.25, '1984 年 10 月 22 日');

  const a0 = sec.n, a1 = TL.secs.s8.s + 0.1;
  ENGINE.scene({ id: 's7q', t0: a0, t1: a1 + 0.3, cls: 'bg-dark', fadeOut: 0.6, build(S) {
    header(S, '六 · 放两年再看');
    S.cam({ s0: 1.0, s1: 1.03 });
    const occ = box(80, 318, 940, null, 'hei', { fontWeight: 600, fontSize: '36px', lineHeight: '1.5', letterSpacing: '3px', color: C.gold }, '1984 年 10 月 22 日<br>中央顾问委员会第三次全体会议');
    S.add(occ); S.fadeUp(occ, a0 + 0.15);
    const tg = nameTag(S, 80, 450, '邓小平', '时任中央顾问委员会主任', cw('g1', '邓小平') - 0.2);
    S.on(t => { const p = pr(t, c('g2') - 0.7, 0.6, 'io'); tg.style.transform += ` translate(0px,${-0 * p}px)`; });
    const ids = ['g2', 'g3', 'g4', 'g5', 'g6', 'g7', 'g8'];
    const txt = { g2: '前些时候那个雇工问题，相当震动呀，大家担心得不得了。', g3: '我的意见是放两年再看。', g4: '那个能影响到我们的大局吗？', g5: '如果你一动，群众就说政策变了，人心就不安了。', g6: '你解决了一个“傻子瓜子”，会牵动人心不安，没有益处。', g7: '让“傻子瓜子”经营一段，怕什么？', g8: '伤害了社会主义吗？' };
    const wrap = box(84, 690, 912, null, 'song', { fontWeight: 800, fontSize: '50px', lineHeight: '1.5', color: C.paper, textAlign: 'justify' }); S.add(wrap);
    const qm = box(64, 610, 120, null, 'song', { fontWeight: 900, fontSize: '170px', lineHeight: '1', color: 'rgba(200,55,43,.6)' }, '“'); S.add(qm); S.fade(qm, c('g2') - 0.3);
    ids.forEach((id, i) => { const sp = h('span', null, txt[id]); wrap.append(sp); S.type(sp, c(id), ce(id) - 0.15);
      S.on(t => { const cur = t >= c(id) - 0.1 && (i === ids.length - 1 || t < c(ids[i + 1]) - 0.1); const done = t >= ce('g8') + 0.4; sp.style.color = (id === 'g3' || id === 'g7') ? C.gold : C.paper; sp.style.filter = `opacity(${cur || done ? 1 : 0.5})`; }); });
    const cite = box(84, 1258, 912, null, 'hei', { fontWeight: 500, fontSize: '28px', letterSpacing: '2px', color: C.dim, textAlign: 'right' }, '——《邓小平文选》第三卷，第 91 页');
    S.add(cite); S.fade(cite, ce('g8') + 0.3);
    const note = box(84, 1306, 912, null, 'hei', { fontWeight: 400, fontSize: '23px', lineHeight: '1.45', color: 'rgba(232,221,198,.5)' }, '书中注释：这里指安徽省芜湖市的一家个体户，他雇工经营，制作和销售瓜子，称为“傻子瓜子”，得以致富。');
    S.add(note); S.fade(note, ce('g8') + 0.8);
  } });

  /* S8 收尾三句 */
  const s8 = TL.secs.s8, e1 = TL.total;
  ENGINE.scene({ id: 's8', t0: s8.s + 0.1, t1: e1, cls: 'bg-dark', fadeIn: 0.6, fadeOut: 0, build(S) {
    const rows = [['h1', '1981', '规定说：<br>最多 <span class="red">7</span> 个人。', C.paper], ['h2', '1984', '有人说：<br>让他经营一段，怕什么。', C.paper], ['h3', '1988 <span style="font-size:.5em">年 4 月</span>', '宪法里加了一句：<br><span style="font-size:42px;line-height:1.5;display:inline-block;margin-top:8px">“国家允许私营经济在法律规定的范围内存在和发展。”</span>', C.paper]];
    rows.forEach(([id, yr, html, col], i) => { const y = 320 + i * 320; const at = c(id) - 0.15;
      const yb = box(80, y, 920, null, 'song', { fontWeight: 900, fontSize: '110px', lineHeight: '1', color: i === 2 ? C.gold : C.dim, letterSpacing: '4px' }, yr);
      const tx = box(80, y + 122, 920, null, 'song', { fontWeight: 800, fontSize: '54px', lineHeight: '1.4', color: col }, html);
      const ln = box(80, y - 26, 920, 3, '', { background: C.dim, transformOrigin: 'left center', opacity: .5 });
      S.add(ln, yb, tx); S.a(ln, { at, d: 0.7, e: 'io', from: { sx: 0 }, maxO: .5 }); S.fadeUp(yb, at); S.fadeUp(tx, at + 0.25);
    });
  } });
})();
