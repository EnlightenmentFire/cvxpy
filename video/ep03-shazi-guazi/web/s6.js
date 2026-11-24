/* S6 等 */
(function () {
  const sec = TL.secs.s6;
  chapter('5', '等', sec.s, sec.n + 0.25, '1982 年 12 月 31 日 ／ 1983 年 1 月 2 日');
  const HD = '五 · 等';

  /* 6a 陈云 */
  const a0 = sec.n, a1 = c('f4') - 0.15;
  ENGINE.scene({ id: 's6cy', t0: a0, t1: a1 + 0.3, cls: 'bg-dark', build(S) {
    header(S, HD);
    S.cam({ s0: 1.0, s1: 1.04 });
    const q = box(70, 330, 940, null, 'song', { fontWeight: 900, fontSize: '84px', lineHeight: '1.35', color: C.paper }, '雇工超过规定，<br>怎么办？');
    S.add(q); S.a(q, { at: a0 + 0.15, d: 0.6, from: { o: 0, y: 30 }, out: c('f2') - 0.3 });
    const tg = nameTag(S, 80, 326, '陈云', '时任中共中央政治局常委', c('f2') - 0.15);
    const occ = box(80, 520, 940, null, 'hei', { fontWeight: 600, fontSize: '34px', letterSpacing: '3px', color: C.gold }, '1982 年 12 月 31 日 · 中央政治局扩大会议');
    S.add(occ); S.fade(occ, c('f2') + 0.1);
    const qm = box(60, 560, 120, null, 'song', { fontWeight: 900, fontSize: '200px', lineHeight: '1', color: 'rgba(200,55,43,.55)' }, '“'); S.add(qm); S.fade(qm, c('f3') - 0.2);
    const sents = [['过去国务院规定最多不超过<span class="gold">七个</span>，', c('f3'), cw('f3', '现在')], ['现在实际上多了一些。', cw('f3', '现在'), cw('f3', '究竟')], ['究竟限不限，限几个合适，', cw('f3', '究竟'), cw('f3', '还要看')], ['<span class="gold">还要看一看。</span>', cw('f3', '还要看'), cw('f3', '但对')], ['但对这类问题，报纸上', cw('f3', '但对'), cw('f3', '不要大张')], ['不要大张旗鼓地宣传。', cw('f3', '不要大张'), ce('f3')]];
    const wrap = box(90, 690, 900, null, 'song', { fontWeight: 800, fontSize: '56px', lineHeight: '1.62', color: C.paper }); S.add(wrap);
    sents.forEach(([htm, s, e]) => { const d = h('div', { html: htm, style: { whiteSpace: 'nowrap' } }); wrap.append(d); S.a(d, { at: s - 0.05, d: Math.max(0.5, (e - s) * 0.9), e: 'lin', from: {}, clip: 'x' }); S.on(t => { d.style.opacity = t < s - 0.05 ? 0 : 1; }); });
    src(S, 1296, '据《陈云年谱》下卷，转引自中央党史和文献研究院网站文章', c('f3') + 0.5);
  } });

  /* 6b 一号文件 三个“不” */
  const b0 = a1, b1 = sec.e;
  ENGINE.scene({ id: 's6doc', t0: b0, t1: b1 + 0.2, cls: 'bg-dark', build(S) {
    header(S, HD);
    S.cam({ s0: 1.0, s1: 1.035 });
    const tDef = cw('f4', '一号文件', 1), t5 = c('f5'), tQ = cw('f5', '不宜提倡');
    const doc = docMock(100, 312, 880, 560, { head: '中 共 中 央 文 件', hs: 62, hls: 6, no: '中发〔1983〕1 号', title: '当前农村经济政策的若干问题', date: '一九八三年一月二日印发', ts: 46, body: bars(3, [100, 100, 62]) });
    S.add(doc); S.a(doc, { at: b0 + 0.1, d: 0.7, from: { o: 0, y: 50, r: 1.5 }, base: 'rotate(-0.6deg)', out: tQ - 0.5, od: 0.5, to: { o: 0.0, y: -40 } });
    const tw = box(110, 905, 860, null, 'hei c', { fontWeight: 600, fontSize: '40px', letterSpacing: '4px', color: C.gold }, '陈云讲话两天后 · 1983 年 1 月 2 日');
    S.add(tw); S.a(tw, { at: b0 + 0.3, d: 0.5, from: { o: 0 }, out: tQ - 0.5 });
    chip(S, 1010, '一号文件', '每年年初，中央发的第一个文件。那几年，讲的都是农村和农民。', tDef - 0.15, tQ - 0.5);
    // three 不
    const pre = box(70, 318, 940, null, 'hei', { fontWeight: 600, fontSize: '38px', lineHeight: '1.5', letterSpacing: '2px', color: C.dim }, '对超过规定、雇请较多帮工的：');
    S.add(pre); S.fade(pre, tQ - 0.4);
    const items = [['不', '宜提倡', cw('f5', '不宜提倡')], ['不', '要公开宣传', cw('f5', '不要公开宣传')], ['不', '要急于取缔', cw('f5', '也不要急于取缔')]];
    items.forEach(([b, rest, at], i) => { const y = 400 + i * 230; const e = box(70, y, 940, 210, '', { borderTop: `2px solid ${C.dim}` }, `<span class="song" style="font-weight:900;font-size:190px;line-height:210px;color:${C.red};vertical-align:middle">${b}</span><span class="song" style="font-weight:900;font-size:${i ? 92 : 104}px;color:${C.paper};vertical-align:middle;margin-left:14px;letter-spacing:4px">${i === 2 ? '<span style="font-size:60px;color:rgba(232,221,198,.6);margin-right:6px">也</span>' : ''}${rest}</span>`);
      if (i === 2) e.innerHTML = `<span class="song" style="font-weight:900;font-size:60px;color:${C.dim};vertical-align:middle;margin-right:6px">也</span>` + `<span class="song" style="font-weight:900;font-size:190px;line-height:210px;color:${C.red};vertical-align:middle">不</span><span class="song" style="font-weight:900;font-size:92px;color:${C.paper};vertical-align:middle;margin-left:14px;letter-spacing:4px">${rest}</span>`;
      S.add(e); S.a(e, { at: at - 0.15, d: 0.5, from: { o: 0, x: -40 } }); });
    const st = box(560, 1090, 440, 180, 'song c', { fontWeight: 900, fontSize: '120px', lineHeight: '166px', letterSpacing: '8px', color: C.gold, border: `8px solid ${C.gold}`, background: 'rgba(27,22,18,.94)', whiteSpace: 'nowrap' }, '先不动');
    S.add(st); S.a(st, { at: cw('f6', '先不动') - 0.15, d: 0.3, e: 'out5', from: { o: 0, s: 1.7 }, base: 'rotate(-4deg)' });
    src(S, 1296, '此句据研究文献转引；目前能查到的公开全文版本里未见此句', tQ + 0.4);
    takeaway(S, 'f8', '7 个人的规定，没改。<br>越了线的人，也没处理。<br><em>都在等。</em>');
  } });
})();
