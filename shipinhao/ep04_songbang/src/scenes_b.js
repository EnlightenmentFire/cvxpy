// 场景（下半）：半小时 → 一级一级 → 七个星期 → 收尾；以及顶部时间轴
const NS = 'http://www.w3.org/2000/svg';
const svgEl = (tag, attrs, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
const PISHI = '此信言辞恳切，使人读后有一种再不改革、再不放权，就真是不能前进了的感觉。本人认为有必要将这封信公之于众。';
const DAOYU = '情词恳切，使人读后有一种再不改革、再不放权，就真是不能前进了的感觉。本报记者认为有必要将这封来信公之于众。';

chapter('chap3', en('3.4') + .5, at('4.1') + 1.5, '三', '怎么接住的', '半小时 · 第二天 · 七个星期');

// ═════════ 4 半小时：办公室 ═════════
scene('office', at('4.1') + 1.5, en('4.3') + .35, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-lamp"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  const w = who(C, '项南', '时任中共福建省委第一书记', 372, 70); tl.in(w, t0, .5);
  // 信
  const P = h(`<div class="paper lined" style="left:70px;top:560px;width:450px;height:520px"><div class="abs pen blue c" style="left:0;right:0;top:86px;font-size:50px;line-height:78px">请给我们“松绑”</div><div class="abs greek" style="left:40px;right:40px;top:186px;height:250px;opacity:.5"></div><div class="src dark" style="left:36px;top:462px;font-size:22px">呼吁信（示意）</div></div>`, C);
  tl.set(P, { o: 0, y: 260, r: 5 }); tl.to(P, { o: 1, y: 0, r: -2.5 }, t0 + .1, .9, E.out);
  const tg = h(`<div class="abs" style="left:70px;top:1100px;font:700 34px/46px Hei;color:var(--cream)"><span class="num gold" style="font-size:44px">3月23日</span> 下午 · 直接送到办公室</div>`, C); tl.in(tg, t0 + .5, .5, 0);
  // 钟：半小时
  const K = h(`<div class="abs" style="left:570px;top:560px;width:440px;height:520px"></div>`, C);
  const sv = h(`<svg class="abs" style="left:0;top:0" width="440" height="440" viewBox="-220 -220 440 440"></svg>`, K);
  svgEl('circle', { r: 200, fill: '#ece2cc', stroke: '#1b1814', 'stroke-width': 8 }, sv);
  const sec = svgEl('path', { fill: 'rgba(176,42,31,.42)' }, sv);
  for (let i = 0; i < 60; i++) { const a = i * 6 * Math.PI / 180, r0 = i % 5 ? 184 : 168; svgEl('line', { x1: Math.sin(a) * r0, y1: -Math.cos(a) * r0, x2: Math.sin(a) * 194, y2: -Math.cos(a) * 194, stroke: '#1b1814', 'stroke-width': i % 5 ? 2 : 6 }, sv); }
  const hand = svgEl('line', { x1: 0, y1: 20, x2: 0, y2: -160, stroke: '#1b1814', 'stroke-width': 9, 'stroke-linecap': 'round' }, sv);
  svgEl('circle', { r: 12, fill: '#b02a1f' }, sv);
  tl.in(K, at('4.2') - .2, .5, 0);
  tl.fn(cl('4.2', 1) - .1, 2.0, p => { const a = p * 180; hand.setAttribute('transform', `rotate(${a})`); const r = 166, x = Math.sin(a * Math.PI / 180) * r, y = -Math.cos(a * Math.PI / 180) * r; sec.setAttribute('d', a < .5 ? '' : `M0 0L0 ${-r}A${r} ${r} 0 0 1 ${x.toFixed(2)} ${y.toFixed(2)}Z`); }, E.io);
  const kl = h(`<div class="abs c" style="left:0;right:0;top:452px;font:900 62px/72px Song;color:#fff">约<span class="gold">半小时</span></div>`, K); tl.in(kl, cl('4.2', 1) + .6, .5, 10);
  // 电话里说的三句
  const CH = h(`<div class="abs" style="left:70px;top:1175px;width:940px"></div>`, C);
  ['信看过了', '写了批示', '已转给《福建日报》'].forEach((s, i) => { const e = h(`<div style="display:inline-block;margin-right:${i < 2 ? 22 : 0}px;font:700 39px/70px Hei;color:var(--cream);background:rgba(12,10,8,.85);border-left:8px solid var(--gold);padding:0 22px">${s}</div>`, CH); tl.in(e, cl('4.2', 3 + i) - .1, .4, 14); });
  const s = src(C, '电话内容与“半个小时”：据黄文麟回忆', 1262); tl.in(s, cl('4.2', 3), .5, 0);
  tl.out(CH, at('4.3') - .35, .3); tl.out(s, at('4.3') - .35, .3); tl.out(tg, at('4.3') - .35, .3);
  const tm = term(C, '批示', '领导在文件上写的处理意见。', 1120); tl.in(tm, at('4.3') - .1, .5);
});

// 批示（钢笔书写，只留写字声）
scene('pishi', en('4.3') + .35, at('4.6') - LEAD, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-lamp"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  const P = h(`<div class="paper" style="left:60px;top:372px;width:960px;height:980px"></div>`, C);
  h(`<div class="abs" style="left:56px;top:40px;right:56px;height:150px;border-bottom:2px solid rgba(176,42,31,.5)"><div class="pen blue" style="font-size:40px;line-height:60px;opacity:.55">请给我们“松绑” —— 五十五名厂长、经理</div><div class="greek" style="height:60px;margin-top:8px;opacity:.3"></div></div>`, P);
  const tx = h(`<div class="abs pen blue" style="left:66px;top:225px;width:830px;font-size:71px;line-height:110px;letter-spacing:1px"></div>`, P);
  // 分句：与 4.4 的分句一一对应（0:据记载 1:批示写的是 2..6:正文）
  const parts = ['此信言辞恳切，', '使人读后有一种再不改革、', '再不放权，', '就真是不能前进了的感觉。', '本人认为有必要将这封信公之于众。'];
  const spans = parts.map(p => h(`<span>${p}</span>`, tx)); const all = [];
  spans.forEach(sp => all.push(...chars(sp)));
  const W0 = t0 + .25, W1 = cl('4.4', 2) - .15;         // 书写时段：静场 + “据记载，批示写的是”
  tl.type(all, W0, W1, .16);
  // 笔尖
  const pen = h(`<svg class="abs" style="left:0;top:0;overflow:visible" width="10" height="10"><g transform="rotate(138)"><path d="M0 0 L9 -30 L22 -150 L-22 -150 L-9 -30 Z" fill="#14110d" stroke="#3a332a" stroke-width="2"/><path d="M0 0 L7 -26 L-7 -26 Z" fill="#c9a45c"/><rect x="-22" y="-420" width="44" height="270" rx="8" fill="#1d1813" stroke="#3a332a" stroke-width="2"/><rect x="-22" y="-176" width="44" height="12" fill="#c9a45c"/></g></svg>`, P);
  let pos = null;
  tl.fn(W0, W1 - W0, p => {
    if (!pos) { const pr = P.getBoundingClientRect(), sc = pr.width / 960; pos = all.map(c => { const r = c.getBoundingClientRect(); return [(r.left - pr.left) / sc + r.width / sc * .6, (r.top - pr.top) / sc + r.height / sc * .72]; }); }
    const f = p * (all.length - 1), i = Math.floor(f), q = f - i, a = pos[i], b = pos[Math.min(all.length - 1, i + 1)];
    const wob = Math.sin(p * 380) * 5;
    pen.style.transform = `translate(${(a[0] + (b[0] - a[0]) * q + 6).toFixed(1)}px,${(a[1] + (b[1] - a[1]) * q + wob).toFixed(1)}px)`;
    pen.style.opacity = p <= 0 ? 0 : (p >= 1 ? 0 : 1);
  });
  tl.set(pen, { o: 1 });
  // 朗读时逐句加重
  spans.forEach((sp, i) => { tl.fn(cl('4.4', 2 + i) - .1, .3, p => { sp.style.color = `rgb(${Math.round(lerp(34, 16, p))},${Math.round(lerp(52, 24, p))},${Math.round(lerp(109, 70, p))})`; sp.style.textShadow = p > 0 ? `0 0 ${(.8 * p).toFixed(2)}px #101846` : 'none'; }); });
  h(`<div class="src dark" style="left:66px;top:804px">批示文字：据人民网党史频道2015年文章 · 手迹为示意</div>`, P);
  // 标题、导语、版面
  const row = h(`<div class="abs" style="left:66px;top:850px;width:830px"></div>`, P);
  [['标题', '自己拟'], ['导语', '自己拟'], ['版面', '他指定']].forEach(([a, b], i) => { const e = h(`<div style="display:inline-block;width:256px;margin-right:${i < 2 ? 30 : 0}px;height:86px;border:3px solid #22346d;color:#22346d;text-align:center;font:900 40px/80px Song"><span>${a}</span><span style="font:700 30px Hei;margin-left:14px;color:#b02a1f">${b}</span></div>`, row); tl.in(e, cl('4.5', 1) - .1 + i * .55, .4, 14); });
  const s2 = h(`<div class="src dark" style="left:66px;top:938px;top:${0}px"></div>`, P); s2.remove();
  const s3 = src(C, '拟标题、导语，指定版面：据报社方面回忆', 1360, 60); tl.in(s3, at('4.5'), .4, 0);
}, { zoom: 1.035 });

// 报纸版面（示意）
function newsPage(C, o) {
  const P = h(`<div class="news" style="left:60px;top:${o.top}px;width:960px;height:${o.h}px;overflow:hidden"></div>`, C);
  if (o.cap) h(`<div class="abs" style="left:40px;right:40px;top:${o.h - 46}px;font:400 22px/32px Hei;color:rgba(34,32,27,.7);border-top:1.5px solid rgba(34,32,27,.35);padding-top:2px;white-space:nowrap">${o.cap}</div>`, P);
  h(`<div class="abs" style="left:40px;right:40px;top:26px;height:136px;border-bottom:5px double #22201b"><div class="abs song" style="left:0;top:0;font:900 104px/128px Song;letter-spacing:10px">${o.name}</div><div class="abs" style="right:0;top:34px;text-align:right;font:700 28px/40px Hei">${o.date}<br><span style="font-weight:400;font-size:24px">${o.no}</span></div></div>`, P);
  return P;
}
scene('paper', at('4.6') - LEAD, at('4.7') - LEAD, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-desk"></div><div class="cam" style="transform-origin:540px 700px"></div>`;
  const C = R.querySelector('.cam');
  const P = newsPage(C, { top: 372, h: 990, name: '福建日报', date: '1984年3月24日　星期六', no: '第 12477 号　·　第一版', cap: '版式示意 · 报头、标题、导语据1984年3月24日《福建日报》一版' });
  tl.set(P, { o: 0, y: 50 }); tl.to(P, { o: 1, y: 0 }, t0, .6);
  const k = h(`<div class="abs c" style="left:40px;right:40px;top:186px;height:74px;background:#2a2620;color:#eee4cc;font:700 46px/74px Hei;letter-spacing:12px">五十五名厂长、经理呼吁</div>`, P);
  const hd = h(`<div class="abs c" style="left:40px;right:40px;top:260px;height:170px;background:repeating-linear-gradient(45deg,#3a352c 0 6px,#4a443a 6px 12px);color:#f4ecd6;font:900 104px/170px Song;letter-spacing:2px;white-space:nowrap">请给我们“松绑”</div>`, P);
  tl.set(k, { clipx: 0 }); tl.to(k, { clipx: 1 }, cl('4.6', 2) - .2, .7, E.io); tl.set(hd, { clipx: 0 }); tl.to(hd, { clipx: 1 }, cl('4.6', 4) - .25, .7, E.io);
  const lead = h(`<div class="abs" style="left:40px;top:456px;width:420px;font:600 27px/41px Song;text-align:justify"><b style="font-family:Hei">本报讯</b>　在福州参加省厂长（经理）研究会成立大会的五十五名厂长、经理，三月二十二日写信给省委领导同志，题目是“请给我们‘松绑’。”情词恳切，使人读后有一种再不改革、再不放权，就真是不能前进了的感觉。本报记者认为有必要将这封来信公之于众。以下是该信全文：</div>`, P);
  h(`<div class="abs greek" style="left:40px;top:848px;width:420px;height:82px;opacity:.6"></div>`, P);
  h(`<div class="abs greek" style="left:490px;top:456px;width:205px;height:474px;opacity:.6"></div>`, P);
  h(`<div class="abs greek" style="left:715px;top:456px;width:205px;height:474px;opacity:.6"></div>`, P);
  tl.in(lead, t0 + .4, .5, 0);
}, { zoom: 1.06 });

// 批示 / 导语 并排
scene('compare', at('4.7') - LEAD, at('4.8') - LEAD, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-desk"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  const A = h(`<div class="paper" style="left:60px;top:372px;width:960px;height:440px;padding:30px 44px"><div>${tab('批示', 'var(--blue)')} <span style="font:400 25px Hei;color:#5a5244;margin-left:14px">据记载 · 3月23日下午</span></div><div class="pen blue" style="font-size:55px;line-height:84px;margin-top:10px">此信言辞恳切，使人读后有一种再不改革、再不放权，就真是不能前进了的感觉。<span class="m">本人</span>认为有必要将这封信公之于众。</div></div>`, C);
  const B = h(`<div class="news" style="left:60px;top:880px;width:960px;height:440px;padding:30px 44px"><div>${tab('报纸导语', '#2a2620')} <span style="font:400 25px Hei;color:#4a4338;margin-left:14px">《福建日报》1984年3月24日一版 · 导语：新闻开头的一段</span></div><div class="song" style="font:600 45px/78px Song;margin-top:12px;text-align:justify">……情词恳切，使人读后有一种再不改革、再不放权，就真是不能前进了的感觉。<span class="m">本报记者</span>认为有必要将这封来信公之于众。</div></div>`, C);
  tl.in(A, t0, .5); tl.in(B, t0 + .25, .5);
  const ma = A.querySelector('.m'), mb = B.querySelector('.m');
  [[ma, cl('4.7', 1) + .5], [mb, cl('4.7', 2) + .4]].forEach(([m, t]) => { m.style.padding = '0 8px'; m.style.borderRadius = '6px'; m.style.whiteSpace = 'nowrap'; m.style.display = 'inline-block'; m.style.lineHeight = '1.25'; tl.fn(t, .35, p => { m.style.boxShadow = `0 0 0 ${(4 * p).toFixed(1)}px rgba(176,42,31,${p})`; m.style.background = `rgba(176,42,31,${(.16 * p).toFixed(3)})`; }); });
  const ar = h(`<div class="abs c" style="left:340px;top:806px;width:400px;height:80px;font:900 44px/80px Song;color:#fff;background:var(--red);box-shadow:0 10px 24px rgba(0,0,0,.5)">本人 <span style="font-family:Hei;font-weight:700;margin:0 6px">→</span> 本报记者</div>`, C);
  tl.set(ar, { o: 0, s: .8 }); tl.to(ar, { o: 1, s: 1 }, cl('4.7', 2) + .7, .4, E.back);
  const s = src(C, '见报的这句话，没有署成省委书记的话', 1340, 60); tl.in(s, cl('4.7', 3), .5, 0);
});

// 大时间轴：不到一天
scene('timeline1', at('4.8') - LEAD, en('4.9') + .5, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-desk"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  const rows = [['3月22日', '写信', '55位厂长、经理联名'], ['3月23日 下午', '送到省委', '直接送进第一书记办公室'], ['约半小时', '批示', '“有必要将这封信公之于众”'], ['3月24日', '头版头条', '第一版最显眼的位置 · 刊出全文']];
  const ys = [372, 548, 724, 900];
  const line = h(`<div class="abs" style="left:137px;top:${ys[0] + 30}px;width:6px;height:${ys[3] - ys[0]}px;background:var(--gold);transform-origin:50% 0"></div>`, C);
  tl.set(line, { sy: 0 }); tl.to(line, { sy: 1 }, t0 + .1, 1.6, E.io);
  rows.forEach((r, i) => {
    const e = h(`<div class="abs" style="left:100px;top:${ys[i]}px;width:900px;height:150px"><i class="abs" style="left:14px;top:6px;width:52px;height:52px;border-radius:50%;background:${i === 2 ? 'var(--red)' : 'var(--gold)'};border:8px solid #15110d"></i><div class="abs num gold" style="left:110px;top:0;font-size:58px;line-height:64px;white-space:nowrap">${r[0]}</div><div class="abs" style="left:110px;top:70px;font:900 50px/60px Song;color:#fff;white-space:nowrap">${r[1]} <span style="font:400 29px Hei;color:var(--dim);margin-left:10px">${r[2]}</span></div></div>`, C);
    tl.in(e, t0 + .15 + i * .4, .45, 0);
  });
  // 括号：送到 → 见报
  const br = h(`<div class="abs" style="left:790px;top:${ys[1] + 16}px;width:40px;height:${ys[3] - ys[1] + 40}px;border:6px solid #fff;border-left:none;transform-origin:50% 0"></div>`, C);
  tl.set(br, { o: 0, sy: 0 }); tl.to(br, { o: 1, sy: 1 }, cl('4.8', 1), .6, E.io);
  const bl = h(`<div class="abs" style="left:822px;top:${ys[2] - 40}px;width:240px;font:900 64px/84px Song;color:#fff;text-align:center;transform-origin:0 50%">不到<br>一天</div>`, C);
  tl.set(bl, { o: 0, x: -20 }); tl.to(bl, { o: 1, x: 0 }, cl('4.8', 2) - .1, .5);
  const S = so(C, '省委书记做的事很小，<br>也很快。', 1090); tl.in(S, at('4.9') - .1, .5, 20);
});

// ═════════ 5 一级一级 ═════════
scene('depts', at('5.1') - LEAD, at('5.4') - LEAD, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-desk"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  const hd = h(`<div class="abs" style="left:70px;top:366px;font:700 36px/50px Hei;color:var(--gold);letter-spacing:6px">见报当天 · 记者去问省里的部门</div>`, C); tl.in(hd, t0, .5, 0);
  const A = h(`<div class="paper" style="left:60px;top:440px;width:960px;height:440px;padding:30px 44px"><div>${tab('省经委')} <span style="font:900 40px Song;margin-left:18px;vertical-align:middle">黄文麟</span><span style="font:400 26px Hei;color:#5a5244;margin-left:14px">省经委副主任</span></div>
    <div class="q" style="font-size:57px;line-height:90px;margin-top:22px">“老婆婆”换“新婆婆”，<br>“小媳妇”照样动弹不得。</div>
    <div class="ten abs" style="right:40px;bottom:26px;font:700 34px/60px Hei;color:#fff;background:var(--red);padding:0 24px"><span class="num" style="font-size:46px">十</span> 条措施</div>
    <div class="abs" style="left:44px;bottom:30px;font:400 25px/36px Hei;color:#5a5244;width:560px">意思是：权只放到地、市或主管局，<br>厂子头上只是换了一个上级。</div></div>`, C);
  tl.in(A, t0 + .35, .5); const ten = A.querySelector('.ten'); const ga = A.lastElementChild; tl.set(ga, { o: 0 }); tl.to(ga, { o: 1 }, en('5.2') - 1.2, .5); tl.set(ten, { o: 0, s: 1.3 }); tl.to(ten, { o: 1, s: 1 }, at('5.3') - .05, .35);
  const qq = A.querySelector('.q'); tl.type(chars(qq), cl('5.2', 2), en('5.2') - .2, .25);
  const B = h(`<div class="paper" style="left:60px;top:910px;width:960px;height:410px;padding:30px 44px"><div>${tab('省委组织部')} <span style="font:900 40px Song;margin-left:18px;vertical-align:middle">傅大文</span><span style="font:400 26px Hei;color:#5a5244;margin-left:14px">时任福建省委组织部副部长</span></div>
    <div style="font:600 39px/64px Song;margin-top:22px;text-align:justify">第一条：「……副职由厂长提名、由上级主管部门考核任命，其余干部包括中层干部均由企业自行任免。」</div>
    <div class="three abs" style="right:40px;bottom:26px;font:700 34px/60px Hei;color:#fff;background:var(--red);padding:0 24px"><span class="num" style="font-size:46px">三</span> 条办法</div></div>`, C);
  tl.in(B, t0 + .7, .5); const th = B.querySelector('.three'); const gb = B.children[1]; tl.set(gb, { o: 0 }); tl.to(gb, { o: 1 }, cl('5.3', 1) + .1, .6); tl.set(th, { o: 0, s: 1.3 }); tl.to(th, { o: 1, s: 1 }, cl('5.3', 2), .35);
  const s = src(C, '两个部门的表态：据《人民日报》1984年3月30日二版', 1340, 60); tl.in(s, at('5.2'), .5, 0);
});

scene('rmrb', at('5.4') - LEAD, at('5.6') - LEAD, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-desk"></div><div class="cam" style="transform-origin:540px 900px"></div>`;
  const C = R.querySelector('.cam');
  const P = newsPage(C, { top: 372, h: 990, name: '人民日报', date: '1984年3月30日　星期五', no: '第二版　·　头条', cap: '版式示意 · 标题与编者按文字据《人民日报》1984年3月30日二版' });
  tl.set(P, { o: 0, y: 50 }); tl.to(P, { o: 1, y: 0 }, t0, .6);
  const k = h(`<div class="abs" style="left:40px;right:40px;top:182px;font:700 37px/56px Hei;letter-spacing:1px">福建省五十五名厂长、经理给省委领导写信：</div>`, P);
  const hd = h(`<div class="abs" style="left:40px;right:40px;top:240px;font:900 104px/150px Song;letter-spacing:0;white-space:nowrap">请给我们“松绑”</div>`, P);
  tl.in(k, cl('5.4', 1) - .2, .5, 0); tl.set(hd, { clipx: 0 }); tl.to(hd, { clipx: 1 }, cl('5.4', 1) + .2, .8, E.io);
  const box = h(`<div class="abs" style="left:40px;right:40px;top:412px;height:400px;border:4px solid #22201b;padding:22px 30px"><span style="font:900 34px Hei">编者按</span><span style="font:400 24px Hei;color:#4a4338;margin-left:14px">编辑部加在文章前面的话</span><div style="font:600 38px/62px Song;margin-top:6px;text-align:justify">……这些象绳索一样捆绑着企业的手脚，前进一步，困难得很！<span class="m1">这种状况的确到了非解决不可的时候了！</span>福建省有关部门对55位厂长、经理的信，很快作出反应，<span class="m2">值得赞赏</span>。</div></div>`, P);
  tl.in(box, cl('5.4', 2) - .2, .5, 0);
  const m1 = box.querySelector('.m1'), m2 = box.querySelector('.m2');
  [m1, m2].forEach(m => { m.style.backgroundImage = 'linear-gradient(rgba(176,42,31,.42),rgba(176,42,31,.42))'; m.style.backgroundRepeat = 'no-repeat'; m.style.backgroundSize = '0% 100%'; m.style.fontWeight = 900; });
  tl.fn(cl('5.5', 1) - .1, en('5.5') - cl('5.5', 1), p => { m1.style.backgroundSize = (p * 100).toFixed(1) + '% 100%'; }, E.io);
  tl.fn(en('5.5') + .25, .6, p => { m2.style.backgroundSize = (p * 100).toFixed(1) + '% 100%'; }, E.io);
  h(`<div class="abs greek" style="left:40px;top:836px;width:270px;height:96px;opacity:.6"></div><div class="abs greek" style="left:345px;top:836px;width:270px;height:96px;opacity:.6"></div><div class="abs greek" style="left:650px;top:836px;width:270px;height:96px;opacity:.6"></div>`, P);
}, { zoom: 1.05 });

// 福州 → 北京：8 天
scene('map', at('5.6') - LEAD, at('5.7') - LEAD, (R, tl, t0, t1) => {
  R.innerHTML = `<div class="bg-desk"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  const sv = h(`<svg class="abs" style="left:0;top:0" width="1080" height="1400"></svg>`, C);
  for (let i = 0; i < 9; i++) svgEl('line', { x1: 60, x2: 1020, y1: 400 + i * 115, y2: 400 + i * 115, stroke: 'rgba(201,164,92,.13)', 'stroke-width': 2 }, sv);
  for (let i = 0; i < 9; i++) svgEl('line', { y1: 380, y2: 1340, x1: 80 + i * 115, x2: 80 + i * 115, stroke: 'rgba(201,164,92,.13)', 'stroke-width': 2 }, sv);
  const F = [430, 1215], B = [318, 580];      // 相对方位按经纬度：北京在福州的北偏西
  const path = svgEl('path', { d: `M${F[0]} ${F[1]} Q${F[0] - 240} ${(F[1] + B[1]) / 2} ${B[0]} ${B[1]}`, fill: 'none', stroke: '#c9a45c', 'stroke-width': 6, 'stroke-linecap': 'round' }, sv);
  tl.set(path, { dash: 0 }); tl.to(path, { dash: 1 }, cl('5.6', 1), ce('5.6', 2) - cl('5.6', 1), E.io);
  const dot = (p, big) => { svgEl('circle', { cx: p[0], cy: p[1], r: big ? 26 : 22, fill: 'none', stroke: '#c9a45c', 'stroke-width': 3, opacity: .6 }, sv); return svgEl('circle', { cx: p[0], cy: p[1], r: 12, fill: '#f1e9d8' }, sv); };
  dot(F); dot(B, 1);
  const lf = h(`<div class="abs" style="left:${F[0] + 44}px;top:${F[1] - 56}px"><div style="font:900 76px/90px Song;color:#fff">福州</div><div style="font:500 30px/42px Hei;color:var(--gold);white-space:nowrap">3月22日 · 一个省的会议室</div></div>`, C);
  const lb = h(`<div class="abs" style="left:${B[0] + 44}px;top:${B[1] - 56}px"><div style="font:900 76px/90px Song;color:#fff">北京</div><div style="font:500 30px/42px Hei;color:var(--gold);white-space:nowrap">3月30日 · 《人民日报》二版头条</div></div>`, C);
  tl.in(lf, t0 + .1, .5, 0); tl.in(lb, cl('5.6', 2) + .3, .5, 0);
  const n = h(`<div class="abs" style="left:560px;top:760px;width:460px;text-align:center"><span class="num gold nn" style="font-size:330px;line-height:330px">0</span><span style="font:900 110px Song;color:#fff;margin-left:10px">天</span></div>`, C);
  const nn = n.querySelector('.nn'); tl.in(n, cl('5.6', 1), .4, 0); tl.set(nn, { num: 0 }); tl.to(nn, { num: 8 }, cl('5.6', 1), cl('5.6', 3) - cl('5.6', 1) + .3, E.lin);
  const sy = h(`<div class="shiyi" style="left:70px;top:372px">方位示意 · 非地图</div>`, C); tl.in(sy, t0, .4, 0);
});

// 4 月：一批文件 + 一级接着一级
scene('april', at('5.7') - LEAD, en('5.8') + .5, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-desk"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  const G = h(`<div class="abs" style="left:0;top:0;width:1080px;height:1400px"></div>`, C);
  const hd = h(`<div class="abs" style="left:70px;top:372px"><span class="num gold" style="font-size:110px;line-height:120px">4<span style="font:900 60px Song">月</span></span><span style="font:900 60px/120px Song;color:#fff;margin-left:24px">福建省里</span></div>`, G); tl.in(hd, t0, .5, 0);
  // 一摞文件（不示具体份数）
  for (let i = 0; i < 14; i++) {
    const last = i === 13;
    const d = h(`<div class="doc" style="left:${250 - i * 3}px;top:${700 - i * 13}px;width:600px;height:${last ? 500 : 500}px;transform-origin:50% 50%">${last ? `<div class="abs c" style="left:0;right:0;top:54px;font:900 64px/80px Song;color:var(--red);letter-spacing:22px">文　件</div><div class="abs" style="left:50px;right:50px;top:160px;height:4px;background:var(--red)"></div><div class="abs greek" style="left:70px;right:70px;top:210px;height:210px;opacity:.5"></div><div class="src dark" style="left:70px;top:440px">示意</div>` : ''}</div>`, G);
    tl.set(d, { o: 0, y: -120, r: (i % 3 - 1) * 1.2 }); tl.to(d, { o: 1, y: 0 }, t0 + .2 + i * .13, .4, E.out);
  }
  const cap = h(`<div class="abs c" style="left:0;right:0;top:1180px;font:900 62px/80px Song;color:#fff">一批落实放权的文件</div>`, G); tl.in(cap, cl('5.7', 1) + .3, .5);
  tl.out(G, at('5.8') - .4, .35);
  // 阶梯
  const steps = [['省委书记', '半小时 · 批示'], ['福建日报', '第二天 · 头版头条'], ['省经委、省委组织部', '表态 · 十条、三条'], ['人民日报', '8天后 · 二版头条转载'], ['福建省里', '4月 · 一批文件']];
  const ST = h(`<div class="abs" style="left:0;top:0;width:1080px;height:1400px"></div>`, C);
  steps.forEach((s, i) => { const e = h(`<div class="abs" style="left:${70 + i * 46}px;top:${372 + i * 132}px;width:${756}px;height:114px;background:linear-gradient(90deg,rgba(236,226,204,.96),rgba(226,214,187,.92));color:var(--ink);border-left:12px solid var(--red);padding:12px 26px"><div style="font:900 44px/52px Song;white-space:nowrap">${s[0]}</div><div style="font:500 28px/38px Hei;color:#5a5244;white-space:nowrap">${s[1]}</div></div>`, ST); tl.in(e, at('5.8') - .3 + i * .28, .4, 0); tl.set(e, { o: 0, x: -40 }); tl.to(e, { x: 0 }, at('5.8') - .3 + i * .28, .4); });
  const S = so(C, '接这封信的，不止一个人、<br>一个部门，是一级接着一级。', 1070); tl.in(S, cl('5.8', 1) - .2, .5, 20);
});

// ═════════ 6 七个星期 ═════════
scene('guowuyuan', at('6.1') - LEAD, at('6.2') - LEAD, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-desk"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  const P = h(`<div class="doc" style="left:90px;top:372px;width:900px;height:980px"></div>`, C);
  tl.set(P, { o: 0, y: 60 }); tl.to(P, { o: 1, y: 0 }, t0, .6);
  h(`<div class="abs c" style="left:0;right:0;top:44px;font:900 96px/120px Song;color:var(--red);letter-spacing:18px;padding-left:18px">国务院文件</div>
     <div class="abs c" style="left:0;right:0;top:186px;font:500 34px/44px Song;color:#2a2620">国发〔1984〕67号</div>
     <div class="abs" style="left:56px;right:56px;top:246px;height:5px;background:var(--red)"></div>`, P);
  const tt = h(`<div class="abs c" style="left:60px;right:60px;top:278px;font:900 49px/72px Song">国务院关于进一步扩大国营工业<br>企业自主权的暂行规定</div>`, P);
  const dd = h(`<div class="abs c" style="left:0;right:0;top:428px;font:500 31px/44px Song;color:#3a342a">（一九八四年五月十日）</div>`, P);
  tl.in(tt, cl('6.1', 1) + .2, .6, 0); tl.in(dd, cl('6.1', 1) + .9, .5, 0);
  const items = ['生产经营计划', '产品销售', '产品价格', '物资选购', '资金使用', '资产处置', '机构设置', '人事劳动管理', '工资奖金', '联合经营'], nums = '一二三四五六七八九十';
  const T = cl('6.1', 2) - 2.2;
  items.forEach((s, i) => { const e = h(`<div class="abs" style="left:${i < 5 ? 70 : 470}px;top:${500 + (i % 5) * 84}px;width:370px;height:70px;border-bottom:2px solid rgba(40,34,24,.25);font:700 36px/70px Hei;white-space:nowrap"><span class="song" style="font:900 38px Song;color:var(--red);display:inline-block;width:56px">${nums[i]}</span>${s}</div>`, P); tl.in(e, T + i * .2, .35, 10); });
  h(`<div class="src dark" style="left:60px;top:932px">文件版式为示意，不含印章 · 条文据国发〔1984〕67号</div>`, P);
});

scene('weeks', at('6.2') - LEAD, at('6.3') - LEAD, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-desk"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  const hd = h(`<div class="abs" style="left:70px;top:366px;width:940px"><span class="num gold nn" style="font-size:170px;line-height:170px">0</span><span style="font:900 80px Song;color:#fff;margin-left:8px">天</span><span class="eq" style="font:900 64px Song;color:#fff;margin-left:40px">＝ 整整 <span class="gold">7</span> 个星期</span></div>`, C);
  tl.in(hd, t0, .4, 0); const nn = hd.querySelector('.nn'), eq = hd.querySelector('.eq');
  const TA = cl('6.2', 0) + .3, TB = ce('6.2', 1) + .2;
  tl.set(nn, { num: 0 }); tl.to(nn, { num: 49 }, TA, TB - TA, E.lin); tl.in(eq, cl('6.2', 2) - .1, .4, 0);
  const days = []; for (let d = 22; d <= 31; d++) days.push([3, d]); for (let d = 1; d <= 30; d++) days.push([4, d]); for (let d = 1; d <= 10; d++) days.push([5, d]);
  const G = h(`<div class="abs" style="left:150px;top:640px;width:860px"></div>`, C), cw = 110, chh = 80;
  ['四', '五', '六', '日', '一', '二', '三'].forEach((w, i) => h(`<div class="abs c" style="left:${i * cw}px;top:-46px;width:${cw - 8}px;font:500 26px/36px Hei;color:var(--dim)">周${w}</div>`, G));
  days.forEach(([m, d], i) => {
    const r = Math.floor(i / 7), c = i % 7, first = i === 0, last = i === 49;
    const e = h(`<div class="abs c" style="left:${c * cw}px;top:${r * chh}px;width:${cw - 8}px;height:${chh - 8}px;background:${first || last ? 'var(--red)' : 'rgba(236,226,204,.92)'};color:${first || last ? '#fff' : '#2a2620'};font:700 ${first || last ? 27 : 30}px/${chh - 8}px Hei;white-space:nowrap">${first ? '3·22' : last ? '5·10' : (d === 1 ? m + '·1' : d)}</div>`, G);
    tl.set(e, { o: .0, s: .7 }); tl.to(e, { o: 1, s: 1 }, TA + (TB - TA) * i / 49, .25);
    if (c === 0 && r < 7) { const wk = h(`<div class="abs" style="left:-84px;top:${r * chh}px;width:70px;font:500 24px/${chh - 8}px Hei;color:var(--gold);text-align:right">第${r + 1}周</div>`, G); tl.in(wk, TA + (TB - TA) * i / 49, .3, 0); }
  });
  const a = h(`<div class="abs" style="left:${cw + 14}px;top:${7 * chh + 6}px;font:700 34px/66px Hei;color:#fff;white-space:nowrap">← 国务院的规定发出</div>`, G); tl.in(a, TB, .4, 0);
  const b = h(`<div class="abs" style="left:150px;top:548px;font:500 27px/36px Hei;color:var(--gold)">↓ 3月22日 写信</div>`, C); tl.in(b, TA, .4, 0);
  const cap = h(`<div class="abs c" style="left:0;right:0;top:1300px;font:900 48px/70px Song;color:#fff">一封省里的信 <span class="gold" style="font-family:Hei">→</span> 一份全国的规定</div>`, C); tl.in(cap, cl('6.2', 3), .5, 10);
});

// 并排：第一样
scene('side', at('6.3') - LEAD, at('6.5') - LEAD, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-desk"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  const A = h(`<div class="paper lined" style="left:60px;top:372px;width:960px;height:400px;padding:22px 44px"><div style="height:56px">${tab('信')} <span style="font:400 26px Hei;color:#5a5244;margin-left:14px">3月22日 · 第一条</span></div><div style="font:600 43px/78px Song;margin-top:0">企业干部管理除工厂正职由上级任命外，<span class="m" style="font-weight:900;font-size:50px;white-space:nowrap">副职应由厂长提名</span>，然后由上级主管部门考核任命，其余干部通通由企业自行任免……</div></div>`, C);
  const B = h(`<div class="doc" style="left:60px;top:860px;width:960px;height:470px;padding:26px 44px;border-top:10px solid var(--red)"><div>${tab('规定')} <span style="font:400 26px Hei;color:#5a5244;margin-left:14px">5月10日 · 第八条 人事劳动管理</span></div><div style="font:600 43px/78px Song;text-align:justify;margin-top:14px">厂长（经理）、党委书记分别由上级主管部门任命；<span class="m" style="font-weight:900;font-size:50px">厂级行政副职由厂长提名</span>，报主管部门批准；<span class="m2" style="font-weight:900">厂内中层行政干部由厂长任免</span>。</div></div>`, C);
  tl.in(A, t0, .5); tl.in(B, cl('6.3', 1) - .3, .5);
  const mark = (m, t, d = .7) => { m.style.backgroundImage = 'linear-gradient(rgba(176,42,31,.40),rgba(176,42,31,.40))'; m.style.backgroundRepeat = 'no-repeat'; m.style.backgroundSize = '0% 100%'; tl.fn(t, d, p => { m.style.backgroundSize = (p * 100).toFixed(1) + '% 100%'; }, E.io); };
  mark(A.querySelector('.m'), cl('6.3', 2) + .1); mark(B.querySelector('.m'), cl('6.4', 1) - .1, 1.2); mark(B.querySelector('.m2'), cl('6.4', 3) - .1, 1.2);
  const mid = h(`<div class="abs c" style="left:330px;top:780px;width:420px;height:72px;font:700 32px/72px Hei;color:#fff;background:#2a2620;border:2px solid var(--gold);letter-spacing:4px">相隔 <span class="num gold" style="font-size:44px">49</span> 天</div>`, C); tl.in(mid, cl('6.4', 0), .4, 0);
  const s = src(C, '信：《人民日报》1984年3月30日二版 · 规定：国发〔1984〕67号', 1345, 60); tl.in(s, t0 + .3, .5, 0);
});

// 并排：五样逐一对照
scene('side2', at('6.5') - LEAD, en('6.7') + .5, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-desk"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  const G = h(`<div class="abs" style="left:0;top:0;width:1080px;height:1400px"></div>`, C);
  h(`<div class="abs" style="left:60px;top:366px;width:300px;height:60px;background:#ece2cc;color:#1b1814;font:900 34px/60px Song;text-align:center">信 · 3月22日</div><div class="abs" style="left:370px;top:366px;width:650px;height:60px;background:var(--red);color:#fff;font:900 34px/60px Song;text-align:center">规定 · 5月10日</div>`, G);
  const rows = [
    ['一', '用人', '第八条', '「厂级行政副职由厂长提名……厂内中层行政干部由厂长任免。」'],
    ['二', '提拔', '第八条', '「从工人中选拔干部……不担任干部时仍当工人……」'],
    ['三', '奖金', '第九条', '「企业对提取的奖励基金有权自主分配。」'],
    ['四', '自销', '第二条', '可以自销的产品，包括「国家计划外超产的产品」。'],
    ['五', '厂长负责制', '这五个字，规定里没有', '第八条：厂长「有权对职工进行奖惩」，中层干部「由厂长任免」。'],
  ];
  const ts = [t0, cl('6.5', 0) - .1, cl('6.5', 1) - .1, cl('6.5', 2) - .1, at('6.6') - .15];
  rows.forEach((r, i) => {
    const y = 438 + i * 178;
    const e = h(`<div class="abs" style="left:60px;top:${y}px;width:960px;height:166px"><div class="abs" style="left:0;top:0;width:300px;height:166px;background:linear-gradient(176deg,#f0e7d2,#e2d6bb);color:#1b1814;padding:14px 22px"><div style="font:900 30px/38px Song;color:var(--red)">第${r[0]}样</div><div style="font:900 ${r[1].length > 3 ? 44 : 60}px/84px Song;white-space:nowrap">${r[1]}</div></div>
      <div class="abs" style="left:310px;top:0;width:650px;height:166px;background:linear-gradient(176deg,#f6f1e4,#ebe4d2);color:#1b1814;padding:14px 26px;border-left:8px solid ${i === 4 ? '#3b352b' : 'var(--red)'}"><div style="font:700 27px/36px Hei;color:${i === 4 ? '#1b1814' : 'var(--red)'};letter-spacing:2px">${r[2]}</div><div style="font:600 ${i === 4 ? 31 : 33}px/49px Song;margin-top:4px">${r[3]}</div></div></div>`, G);
    tl.in(e, ts[i], .45, 18);
  });
  const s = src(G, '条文据国发〔1984〕67号', 1338, 60); tl.in(s, t0 + .3, .5, 0);
  tl.to(G, { o: .2 }, at('6.7') - .35, .4);
  const S = so(C, '七个星期前写在信里的话，<br>这时写进了国务院的规定。', 680); tl.in(S, at('6.7') - .1, .5, 20);
});

scene('october', at('6.8') - LEAD, en('6.8') + .7, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-black"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  const a = h(`<div class="abs c num gold" style="left:0;right:0;top:470px;font-size:120px;line-height:140px">1984<span style="font:900 64px Song;margin:0 8px">年</span>10<span style="font:900 64px Song;margin-left:8px">月</span></div>`, C);
  const b = h(`<div class="abs c" style="left:0;right:0;top:640px;font:900 92px/120px Song;color:#fff;letter-spacing:6px">十二届三中全会</div>`, C);
  const c = h(`<div class="abs c" style="left:0;right:0;top:776px;font:500 38px/56px Hei;color:var(--dim)">《中共中央关于经济体制改革的决定》</div>`, C);
  const d = h(`<div class="abs paper c" style="left:70px;top:900px;width:940px;padding:40px 30px;border-top:8px solid var(--red)"><div style="font:900 60px/92px Song">增强企业活力是<br>经济体制改革的中心环节</div><div style="font:400 25px/36px Hei;color:#5a5244;margin-top:10px">《决定》第三部分标题</div></div>`, C);
  tl.in(a, t0, .5, 0); tl.in(b, cl('6.8', 1) - .1, .5, 14); tl.in(c, cl('6.8', 1) + .5, .5, 0); tl.in(d, cl('6.8', 2) - .1, .6);
});

// ═════════ 7 收尾三句 ═════════
scene('end', en('6.8') + .7, en('7.3') + .9, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-black"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  const mk = (y, date, txt) => h(`<div class="abs c" style="left:0;right:0;top:${y}px"><div class="num gold" style="font-size:66px;line-height:84px;letter-spacing:2px">${date}</div><div style="font:900 70px/104px Song;color:#fff;margin-top:6px">${txt}</div></div>`, C);
  const a = mk(470, '1984年3月22日', '55个厂长，<br>在一封信上签了名。'), b = mk(830, '3月23日下午', '半个小时。'), c = mk(1090, '5月10日', '一份文件，发到了全国。');
  tl.in(a, at('7.1') - .1, .7, 0); tl.in(b, at('7.2') - .1, .7, 0); tl.in(c, at('7.3') - .1, .7, 0);
}, { fo: 0, zoom: 1.03 });

// ── 顶部时间轴（后半段贯穿） ──
function buildStrip(stage) {
  const el = h(`<div id="strip" style="z-index:40"><div class="line"></div><div class="fill"></div></div>`, stage);
  const N = [['3月22日', '写信', at('4.1') + 1.5], ['23日下午', '送到', at('4.1') + 1.9], ['约半小时', '批示', cl('4.2', 1) + .6], ['24日', '见报', at('4.6')], ['30日', '人民日报', at('5.4')], ['5月10日', '国务院', at('6.1')]];
  const xs = N.map((_, i) => 30 + (940 - 60) * i / 5);
  const ns = N.map((n, i) => h(`<div class="n off" style="left:${xs[i]}px"><i></i><b>${n[0]}</b><s>${n[1]}</s></div>`, el));
  const fill = el.querySelector('.fill');
  const T0 = at('4.1') + 1.5, T1 = en('6.8') + .7;
  return t => {
    const vis = t >= T0 - .01 && t < T1 + .4;
    el.style.display = vis ? 'block' : 'none'; if (!vis) return;
    el.style.opacity = Math.min(clamp((t - T0) / .5), 1 - clamp((t - T1) / .4)).toFixed(3);
    let w = 0;
    N.forEach((n, i) => { const on = t >= n[2]; ns[i].className = 'n ' + (on ? 'on' : 'off'); if (on) { const nx = N[i + 1]; w = xs[i] - 30; if (nx) w += (xs[i + 1] - xs[i]) * E.io(clamp((t - nx[2] + .8) / .8)) * 1; } });
    fill.style.width = Math.min(w, 880).toFixed(1) + 'px';
  };
}
