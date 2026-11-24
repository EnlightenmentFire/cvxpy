// 场景（上半）：冷启动 → 片名 → 诉苦会 → 婆婆 → 写信 → 五样权力 → 承诺
const LEAD = .25;

// ── 绳结 ──
function knotD(x0, x1, y, amp, kw) {
  // 直绳 + 中段一个反手结（开口三叶结）。amp: 结的尺度；amp→0 拉直。kw: 结所占的绳长
  kw = kw || (x1 - x0); const cx = (x0 + x1) / 2, a = cx - kw / 2, b = cx + kw / 2, T = 2.72;
  const k = Math.min(1, amp / 12);                       // 小于 12 时整体向直线收拢
  const sm = (e0, e1, x) => { const t = Math.min(1, Math.max(0, (x - e0) / (e1 - e0))); return t * t * (3 - 2 * t); };
  const N = 120; let d = `M${x0.toFixed(1)} ${y.toFixed(1)}`;
  if (a > x0 + 1) d += `L${a.toFixed(1)} ${y.toFixed(1)}`;
  for (let i = 0; i <= N; i++) {
    const u = i / N, t = T * (1 - 2 * u), w = sm(0, .2, u) * sm(1, .8, u) * k;
    const kx = cx + amp * (Math.sin(t) + 2 * Math.sin(2 * t)) * .5, ky = y - amp * (Math.cos(t) - 2 * Math.cos(2 * t) + .75) * .5;
    const lx = a + kw * u;
    d += 'L' + (lx + (kx - lx) * w).toFixed(1) + ' ' + (y + (ky - y) * w).toFixed(1);
  }
  if (b < x1 - 1) d += `L${x1.toFixed(1)} ${y.toFixed(1)}`;
  return d;
}
function rope(svg, x0, x1, y, wd = 18, kw = 0) {
  const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  g.innerHTML = `<path fill="none" stroke="#1c140b" stroke-width="${wd + 7}" stroke-linecap="round" stroke-linejoin="round"/>
  <path fill="none" stroke="#b9945c" stroke-width="${wd}" stroke-linecap="round" stroke-linejoin="round"/>
  <path fill="none" stroke="rgba(70,46,20,.6)" stroke-width="${wd}" stroke-dasharray="3 ${Math.round(wd * .45)}" stroke-linejoin="round"/>
  <path fill="none" stroke="rgba(255,236,190,.28)" stroke-width="${Math.max(2, wd * .22)}" stroke-linecap="round" stroke-linejoin="round" transform="translate(0,-${(wd * .22).toFixed(1)})"/>`;
  svg.appendChild(g);
  const ps = g.querySelectorAll('path');
  g._set = amp => { const d = knotD(x0, x1, y, amp, kw); ps.forEach(p => p.setAttribute('d', d)); };
  g._set(0);
  return g;
}
// 解结：tight(amp a0) → 松开(amp a1) → 拉直(0)
function untie(tl, g, t0, d, a0, a1) {
  tl.fn(t0, d, p => { const amp = p < .45 ? lerp(a0, a1, E.io(p / .45)) : lerp(a1, 0, E.io((p - .45) / .55)); g._set(amp); });
}

// 标签小片
const tab = (txt, bg = 'var(--red)', col = '#fff') => `<span style="display:inline-block;font:700 27px/44px Hei;color:${col};background:${bg};padding:0 18px;letter-spacing:5px">${txt}</span>`;

// ═════════ 0 冷启动 ═════════
scene('cold', 0, at('0.5') - LEAD, (R, tl) => {
  R.innerHTML = `<div class="bg-black"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  const q = h(`<div class="abs big c" style="left:0;right:0;top:600px;transform-origin:540px 170px">企业建个厕所<br>都要层层报批。</div>`, C);
  const cs = chars(q);
  tl.type(cs.slice(0, 6), at('0.1') - .1, ce('0.1', 0) - .25, .3);
  tl.type(cs.slice(6), cl('0.1', 1) - .05, en('0.1') - .3, .3);
  tl.set(q, { s: 1, y: 0 });
  tl.to(q, { s: .56, y: -365 }, at('0.2') - .45, .9, E.io);
  const d1 = h(`<div class="abs c num gold" style="left:0;right:0;top:600px;font-size:150px;line-height:170px;letter-spacing:2px">1984<span style="font:900 76px Song;margin:0 10px">年</span>3<span style="font:900 76px Song;margin-left:10px">月</span></div>`, C);
  const d2 = h(`<div class="abs c song" style="left:0;right:0;top:780px;font:900 120px/150px Song;letter-spacing:40px;padding-left:40px">福州</div>`, C);
  tl.in(d1, at('0.2'), .6); tl.in(d2, cl('0.2', 1) - .1, .6);
  const s1 = src(C, '据当时在场的人回忆 · 说话的是一位国营厂厂长', 518); s1.style.left = '0'; s1.style.right = '0'; s1.style.textAlign = 'center';
  tl.in(s1, at('0.3') + .2, .6, 0);
  const tm = term(C, '国营厂', '国家开的厂，厂长由上级任命。', 1040);
  tl.in(tm, at('0.4') - .1, .6);
}, { fi: .5 });

// 55
scene('n55', at('0.5') - LEAD, en('0.5') + .55, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-desk"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  const n = h(`<div class="abs c num" style="left:0;right:0;top:330px;font-size:400px;line-height:420px;color:var(--cream);letter-spacing:-6px">55</div>`, C);
  tl.set(n, { num: 0 }); tl.to(n, { num: 55 }, t0 + .2, 2.3, E.out);
  const lb = h(`<div class="abs c" style="left:0;right:0;top:760px;font:900 78px/100px Song;letter-spacing:8px">位厂长、经理</div>`, C);
  tl.in(lb, cl('0.5', 0) + .2, .6);
  const grid = h(`<div class="abs" style="left:117px;top:930px;width:860px"></div>`, C);
  for (let i = 0; i < 55; i++) {
    const c = h(`<div class="abs" style="left:${(i % 11) * 78}px;top:${Math.floor(i / 11) * 78}px;width:64px;height:64px">${bust('#c9a45c', 64)}</div>`, grid);
    tl.set(c, { o: .0, s: .6 }); tl.to(c, { o: 1, s: 1 }, t0 + .25 + i * 2.2 / 55, .3);
  }
  const s = src(C, '福建省厂长（经理）研究会成立大会 · 1984年3月 · 福州', 1340); s.style.left = '0'; s.style.right = '0'; s.style.textAlign = 'center';
  tl.in(s, cl('0.5', 2), .5, 0);
});

// 片名
scene('title', en('0.5') + .55, at('1.1') - .3, (R, tl, t0, t1) => {
  R.innerHTML = `<div class="bg-black"></div><div class="cam"><svg class="abs" style="left:0;top:0" width="1080" height="1920"></svg></div>`;
  const C = R.querySelector('.cam'), svg = R.querySelector('svg');
  const g = rope(svg, -40, 1120, 520, 24, 420); g._set(64);
  tl.fn(t0, t1 - t0, p => g._set(lerp(62, 68, p)));
  const s0 = h(`<div class="abs c" style="left:0;right:0;top:300px;font:700 34px/50px Hei;color:var(--gold);letter-spacing:14px">改革开放系列 · 第 4 期</div>`, C);
  const tt = h(`<div class="abs c" style="left:0;right:0;top:720px;font:900 148px/200px Song;letter-spacing:6px">请给我们松绑</div>`, C);
  const rl = h(`<div class="abs" style="left:340px;top:950px;width:400px;height:3px;background:var(--gold);transform-origin:50% 50%"></div>`, C);
  const sb = h(`<div class="abs c" style="left:0;right:0;top:990px;font:700 60px/90px Hei;letter-spacing:10px;color:var(--cream)">五十五个厂长的一封信</div>`, C);
  const yr = h(`<div class="abs c num gold" style="left:0;right:0;top:1130px;font-size:44px;letter-spacing:10px">1984 · 福建</div>`, C);
  tl.in(s0, t0 + .1, .5, 0); tl.type(chars(tt), t0 + .15, t0 + .9, .35); tl.set(rl, { sx: 0 }); tl.to(rl, { sx: 1 }, t0 + .8, .6);
  tl.in(sb, t0 + .95, .6, 20); tl.in(yr, t0 + 1.3, .6, 0);
}, { fi: .3, fo: .3 });

// 章节卡
function chapter(name, t0, t1, no, tt, sb) {
  scene(name, t0, t1, (R, tl) => {
    R.innerHTML = `<div class="bg-black"></div><div class="cam chap"><div class="no">${no}</div><div class="tt">${tt}</div><div class="rule"></div><div class="sb">${sb}</div></div>`;
    const [a, b, c, d] = R.querySelector('.cam').children;
    tl.in(a, t0 + .05, .4, 0); tl.type(chars(b), t0 + .1, t0 + .55, .3); tl.set(c, { sx: 0 }); tl.to(c, { sx: 1 }, t0 + .4, .5); tl.in(d, t0 + .55, .5, 14);
  }, { fi: .25, fo: .3, zoom: 1.03 });
}
chapter('chap1', at('1.1') - .3, at('1.1') + 1.75, '一', '卡在哪', '建个厕所，都要层层报批');

// ═════════ 1 诉苦会 ═════════
scene('meeting', at('1.1') + 1.75, at('1.5') - LEAD, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-desk"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  const ban = h(`<div class="abs c" style="left:70px;width:940px;top:262px;height:96px;background:linear-gradient(180deg,#b12c20,#8f2018);font:900 47px/96px Song;color:#f6e7c8;letter-spacing:3px;box-shadow:0 14px 30px rgba(0,0,0,.5)">福建省厂长（经理）研究会成立大会</div>`, C);
  tl.in(ban, t0, .5, -20);
  const sub = src(C, '1984年3月 · 福州 · 55位厂长、经理', 372); sub.style.left = '0'; sub.style.right = '0'; sub.style.textAlign = 'center'; tl.in(sub, t0 + .3, .5, 0);
  // 座位
  const seats = h(`<div class="abs" style="left:139px;top:440px;width:802px;height:300px"></div>`, C); const dots = [];
  for (let i = 0; i < 55; i++) { const d = h(`<div class="abs" style="left:${(i % 11) * 73 + 8}px;top:${Math.floor(i / 11) * 60}px;width:42px;height:42px;border-radius:50%;background:#8b7c63"></div>`, seats); dots.push(d); tl.set(d, { o: 0 }); tl.to(d, { o: .85 }, t0 + .2 + (i % 11) * .03 + Math.floor(i / 11) * .08, .3); }
  const f1 = h(`<div class="abs c" style="left:0;right:0;top:820px"><div style="font:700 36px/50px Hei;color:var(--gold);letter-spacing:10px">本来的议程</div><div style="font:900 124px/170px Song;color:#fff;margin-top:10px">交流经验</div></div>`, C);
  tl.in(f1, t0 + .3, .5, 20); tl.out(f1, at('1.2') - .1, .35);
  const A = dots[2], B = dots[8];
  [A, B].forEach(d => { d.style.background = '#c9a45c'; d.style.boxShadow = '0 0 0 0 rgba(201,164,92,.5)'; });
  tl.fn(at('1.2'), .6, p => { [A, B].forEach(d => { d.style.boxShadow = `0 0 0 ${(p * 9).toFixed(1)}px rgba(201,164,92,.35)`; d.style.background = p > 0 ? '#e8c273' : '#8b7c63'; }); });
  // 两家厂
  const P = h(`<div class="abs" style="left:0;top:0;width:1080px;height:1400px"></div>`, C);
  const mk = (l, name, kind) => h(`<div class="abs" style="left:${l}px;top:800px;width:450px;height:230px;background:linear-gradient(176deg,#f1e8d3,#e4d9be);color:var(--ink);border-top:8px solid var(--gold);padding:24px 30px;box-shadow:0 18px 40px rgba(0,0,0,.5)"><div style="font:900 50px/66px Song;white-space:nowrap;letter-spacing:-1px">${name}</div><div style="margin-top:22px">${tab(kind, '#3b352b')}</div></div>`, P);
  const c1 = mk(80, '福日电视机公司', '中日合资'), c2 = mk(550, '福州铅笔厂', '承包试点');
  tl.in(c1, cl('1.2', 1) - .15, .55); tl.in(c2, cl('1.2', 2) - .15, .55);
  const bars = h(`<div class="abs" style="left:80px;top:1085px;width:920px;height:240px"><div style="font:700 32px/40px Hei;color:var(--gold);letter-spacing:8px">手里的自主权 <span style="font-weight:400;color:var(--dim);letter-spacing:2px">（示意）</span></div>
   <div class="abs" style="top:66px;left:0;font:500 36px/56px Hei">这两家</div><div class="abs b1" style="top:72px;left:180px;height:44px;width:700px;background:linear-gradient(90deg,#c9a45c,#e3c27e);transform-origin:0 50%"></div>
   <div class="abs" style="top:146px;left:0;font:500 36px/56px Hei">一般的厂</div><div class="abs b2" style="top:152px;left:180px;height:44px;width:210px;background:#6f6657;transform-origin:0 50%"></div></div>`, P);
  tl.in(bars, cl('1.2', 3) - .1, .5, 0); tl.set(bars.querySelector('.b1'), { sx: 0 }); tl.to(bars.querySelector('.b1'), { sx: 1 }, cl('1.2', 3), .9); tl.set(bars.querySelector('.b2'), { sx: 0 }); tl.to(bars.querySelector('.b2'), { sx: 1 }, cl('1.2', 3) + .15, .7);
  tl.out(P, at('1.3') - .35, .35);
  // 引语
  const Q = h(`<div class="abs" style="left:80px;top:810px;width:920px"><div class="q" style="font-size:86px;line-height:128px;color:#fff">「有你们那样的权力，<br>我们也可以搞好。」</div></div>`, C);
  const qc = chars(Q.firstChild); tl.type(qc, cl('1.3', 1) - .1, en('1.3') - .3, .3);
  const qs = src(C, '别的厂长听完说 —— 据《福建日报》2024年回顾文章，回忆性质', 1090); tl.in(qs, at('1.3'), .5, 0);
  tl.out(Q, at('1.4') - .35, .3); tl.out(qs, at('1.4') - .35, .3);
  // 交流会 → 诉苦会
  const X = h(`<div class="abs c" style="left:0;right:0;top:830px"><div class="x1" style="display:inline-block;position:relative;font:900 104px/140px Song;color:#b9ad97">经验交流会<i style="position:absolute;left:-14px;right:-14px;top:68px;height:9px;background:var(--red);transform-origin:0 50%"></i></div><div class="x2" style="font:900 170px/220px Song;color:#fff;margin-top:26px;letter-spacing:12px">诉苦会</div></div>`, C);
  const x1 = X.querySelector('.x1'), x2 = X.querySelector('.x2'), xi = X.querySelector('i');
  tl.in(x1, at('1.4') - .05, .4, 0); tl.set(xi, { sx: 0 }); tl.to(xi, { sx: 1 }, cl('1.4', 1) - .25, .35, E.io);
  tl.set(x2, { o: 0, s: 1.25 }); tl.to(x2, { o: 1, s: 1 }, cl('1.4', 1) + .1, .4, E.out);
});

// 婆婆
scene('popo', at('1.5') - LEAD, en('1.8') + .5, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-desk"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  const Q = h(`<div class="abs q c" style="left:40px;right:40px;top:262px;font-size:68px;line-height:104px;color:#fff">「婆婆太多，媳妇这也不能干，<br>那也干不成。」</div>`, C);
  tl.type(chars(Q), cl('1.5', 1) - .1, en('1.5') - .2, .3);
  const qs = src(C, '据《福建日报》2024年回顾文章，回忆性质', 482); qs.style.left = '0'; qs.style.right = '0'; qs.style.textAlign = 'center'; tl.in(qs, at('1.5') + .3, .5, 0);
  // 中心厂长 + 一圈图章
  const cx = 540, cy = 830, G = h(`<div class="abs" style="left:0;top:0;width:1080px;height:1400px"></div>`, C);
  const svg = h(`<svg class="abs" style="left:0;top:0" width="1080" height="1400"></svg>`, G);
  const me = h(`<div class="abs c" style="left:${cx - 85}px;top:${cy - 100}px;width:170px">${bust('#f1e9d8', 150)}<div style="font:900 44px/56px Song;margin-top:4px">厂长</div></div>`, G);
  tl.in(me, at('1.5') - .1, .5, 0);
  const names = ['计划', '原材料', '销售', '工资', '人事'];
  const pos = [[540, 590], [860, 720], [790, 1010], [290, 1010], [220, 720]], rot = [-4, 6, -5, 5, -7];
  names.forEach((nm, i) => {
    const [x, y] = pos[i], t = cl('1.7', i) - .08;
    const ln = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    const ex = cx + (x - cx) * .3, ey = cy + (y - cy) * .3 - 10;
    ln.setAttribute('x1', x); ln.setAttribute('y1', y); ln.setAttribute('x2', ex); ln.setAttribute('y2', ey);
    ln.setAttribute('stroke', '#b02a1f'); ln.setAttribute('stroke-width', 4); ln.setAttribute('stroke-dasharray', '10 8'); svg.appendChild(ln);
    tl.set(ln, { o: 0 }); tl.to(ln, { o: .75 }, t + .15, .3);
    const st = h(`<div class="stamp" style="left:${x - 105}px;top:${y - 62}px;width:210px;background:#eadfc6">${nm}<small>上面统一定</small></div>`, G);
    tl.set(st, { o: 0, s: 1.7, r: rot[i] }); tl.to(st, { o: 1, s: 1 }, t, .22, E.in);
  });
  const sy = h(`<div class="shiyi" style="left:880px;top:1150px">示意</div>`, G); tl.in(sy, cl('1.7', 0), .4, 0);
  const tm = term(C, '婆婆', '厂长们对上级主管部门的叫法：<br>管厂子的部门多，个个都能管你。', 1120);
  tl.in(tm, at('1.6') - .1, .5); tl.out(tm, at('1.7') - .3, .3);
  // 这说明什么
  tl.to(G, { o: .22 }, at('1.8') - .3, .4); tl.to(Q, { o: .25 }, at('1.8') - .3, .4); tl.out(qs, at('1.8') - .3, .3);
  const S = so(C, '他们不缺办法，<br>缺的是能自己拿主意的<br>那几样权力。', 660); tl.in(S, at('1.8') - .1, .5, 20);
});

chapter('chap2', en('1.8') + .5, at('2.1') + 1.5, '二', '要什么', '不是钱，是五样权力');

// ═════════ 2 连夜写信 ═════════
scene('draft', at('2.1') + 1.5, at('2.3') - LEAD, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-lamp"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  const w1 = who(C, '黄文麟', '时任福建省经委副主任、省企业管理协会副会长 · 50岁', 262, 70); tl.in(w1, t0, .5);
  const w2 = who(C, '滕能香', '时任福建省企业管理协会秘书长', 412, 70); tl.in(w2, cl('2.2', 1) - .2, .5);
  const gl = src(C, '省经委：省经济委员会，企业的上级主管部门之一', 540, 70); tl.in(gl, t0 + .6, .5, 0);
  const P = h(`<div class="paper lined" style="left:110px;top:590px;width:860px;height:700px;transform-origin:50% 50%"></div>`, C);
  tl.set(P, { o: 0, y: 60, r: -1.6 }); tl.to(P, { o: 1, y: 0 }, t0 + .2, .7);
  const tt = h(`<div class="abs pen blue c" style="left:0;right:0;top:92px;font-size:92px;line-height:150px;letter-spacing:6px">请给我们“松绑”</div>`, P);
  tl.type(chars(tt), cl('2.1', 4) - .2, en('2.1') + .2, .25);
  // 潦草的行（示意）
  const sv = h(`<svg class="abs" style="left:0;top:0" width="860" height="700"></svg>`, P);
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  for (let r = 0; r < 4; r++) {
    let d = `M70 ${288 + r * 78}`; let x = 70; const end = r === 3 ? 520 : 790;
    while (x < end) { const dx = 14 + rnd() * 22; d += ` q${(dx / 2).toFixed(1)} ${(-(8 + rnd() * 22)).toFixed(1)} ${dx.toFixed(1)} ${(rnd() * 6 - 3).toFixed(1)}`; x += dx; if (rnd() < .16) { d += ` m${14 + rnd() * 10} 0`; x += 20; } }
    const p = document.createElementNS('http://www.w3.org/2000/svg', 'path'); p.setAttribute('d', d); p.setAttribute('fill', 'none'); p.setAttribute('stroke', '#22346d'); p.setAttribute('stroke-width', 3.2); p.setAttribute('stroke-linecap', 'round'); p.setAttribute('opacity', .8); sv.appendChild(p);
    tl.set(p, { dash: 0, o: 0 }); tl.to(p, { o: 1 }, at('2.2') + r * 1.1, .05, E.lin); tl.to(p, { dash: 1 }, at('2.2') + r * 1.1, 1.3, E.lin);
  }
  h(`<div class="src dark" style="left:60px;top:640px">信纸与笔迹为示意</div>`, P);
  const dt = h(`<div class="abs" style="left:520px;top:1010px;width:480px;height:250px;background:rgba(12,10,8,.9);border-left:10px solid var(--gold);padding:22px 30px"><div style="font:700 30px/40px Hei;color:var(--gold);letter-spacing:6px">信上的日期</div><div class="num" style="font-size:112px;line-height:130px;color:var(--cream);white-space:nowrap">3<span style="font:900 56px Song">月</span>22<span style="font:900 56px Song">日</span></div><div style="font:400 24px/30px Hei;color:var(--dim)">据《人民日报》1984年3月30日</div></div>`, C);
  tl.in(dt, cl('2.2', 2) - .1, .5);
  const s = src(C, '提议联名、当晚起草：据当事人回忆与回顾文章', 1340); tl.in(s, at('2.2'), .5, 0);
});

// ═════════ 五样权力 ═════════
const POW = [
  { k: '一', n: '用人', id: ['2.4', '2.5'], q: '「副职应由厂长提名……其余干部通通由企业自行任免，上面不要干预。」', bt: '在这之前', b: '连一个车间主任，<br>都要主管部门来任命。', bs: '副职：副厂长一级 · “在这之前”据黄文麟回忆' },
  { k: '二', n: '提拔', id: ['2.6', '2.7'], q: '「破除“终身制”和“铁交椅”……真正做到能上能下，能“干”能“工”……」', bt: '名词 · 铁交椅', b: '干部只能上、不能下，<br>坐上去就是一辈子。<br>能干的工人，也上不去。', bs: '能“干”能“工”：干部可以回去当工人' },
  { k: '三', n: '发奖金', id: ['2.8', '2.9'], q: '「奖金随税利增减而浮动，不封顶，不保底。」可以实行「浮动工资」。', bt: '名词 · 大锅饭 / 浮动工资', b: '大锅饭：干多干少一个样。<br>浮动工资：工资跟着干得好坏上下浮动。', bs: '税利：上交国家的税和利润 · 发加班费要先报批：据黄文麟回忆' },
  { k: '四', n: '卖多出来的产品', id: ['2.10', '2.11'], q: '「在完成国家计划指标的情况下，企业自己组织原材料所增产的产品，允许企业自销……」', bt: '在这之前', b: '生产多少，按计划来；<br>生产出来的东西，统购包销。', bs: '统购包销：产品由国家统一收购、统一销售 · 据黄文麟回忆' },
  { k: '五', n: '厂长说了算', id: ['2.12', '2.12'], q: '「改革企业领导制度，试行厂长（经理）负责制，扩大厂长权力……」', bt: '名词 · 厂长负责制', b: '厂里的事厂长说了算，<br>不用层层请示。', bs: '信里只建议：先选几个厂进行试点' },
];
scene('five', at('2.3') - LEAD, en('2.14') + .5, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-desk"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  // 开场大字
  const O = h(`<div class="abs c" style="left:0;right:0;top:560px"><div style="font:900 110px/160px Song;color:#b9ad97">信里要的<span style="position:relative;display:inline-block">不是钱<i style="position:absolute;left:-10px;right:-10px;top:74px;height:9px;background:var(--red);transform-origin:0 50%"></i></span></div><div style="font:900 150px/220px Song;color:#fff;margin-top:20px">是<span class="gold">五样</span>权力</div></div>`, C);
  tl.in(O.children[0], at('2.3') - .1, .4, 0); const oi = O.querySelector('i'); tl.set(oi, { sx: 0 }); tl.to(oi, { sx: 1 }, cl('2.3', 1) - .3, .3, E.io);
  tl.in(O.children[1], cl('2.3', 1) - .05, .45, 20); tl.out(O, at('2.4') - .4, .35);
  // 顶部绳结行
  const head = h(`<div class="abs" style="left:0;top:0;width:1080px;height:560px"></div>`, C);
  tl.in(head, at('2.4') - .3, .5, 0);
  h(`<div class="abs c" style="left:0;right:0;top:250px;font:700 34px/48px Hei;color:var(--gold);letter-spacing:12px">信里要的五样权力</div>`, head);
  const svg = h(`<svg class="abs" style="left:0;top:0" width="1080" height="560"></svg>`, head);
  const xs = [164, 352, 540, 728, 916], short = ['用人', '提拔', '奖金', '自销', '厂长负责'];
  const knots = [], labs = [];
  xs.forEach((x, i) => {
    const g = rope(svg, x - 86, x + 86, 392, 9, 150); g._set(21); knots.push(g);
    const lb = h(`<div class="abs c" style="left:${x - 94}px;width:188px;top:455px"><div class="num" style="font:900 30px/36px Song;color:var(--gold)">${POW[i].k}</div><div class="nm" style="font:700 36px/50px Hei;color:#8f8471;white-space:nowrap">${short[i]}</div></div>`, head); labs.push(lb);
  });
  // 逐样
  POW.forEach((p, i) => {
    const ta = at(p.id[0]) - .2, tb = (i < 4 ? at(POW[i + 1].id[0]) : at('2.14')) - .45;
    const nm = labs[i].querySelector('.nm');
    tl.fn(ta, .3, q => { nm.style.color = q > 0 ? (q < 1 ? '#e3c27e' : '#e3c27e') : '#8f8471'; });
    // 解结：在"在这之前/名词"说完后
    const tu = i < 4 ? en(p.id[1]) - 1.5 : en('2.12') - 1.3;
    untie(tl, knots[i], tu, 1.5, 21, 30);
    tl.fn(tu + 1.4, .2, q => { if (q > 0) nm.style.color = '#f1e9d8'; });
    const P = h(`<div class="abs" style="left:0;top:0;width:1080px;height:1400px"></div>`, C);
    tl.in(P, ta, .45, 24); tl.out(P, tb, .35);
    h(`<div class="abs" style="left:80px;top:575px;font:700 38px/50px Hei;color:var(--gold);letter-spacing:8px">第${p.k}样</div>`, P);
    h(`<div class="abs" style="left:76px;top:625px;font:900 ${p.n.length > 5 ? 96 : 124}px/160px Song;color:#fff;white-space:nowrap">${p.n}</div>`, P);
    const qc = h(`<div class="abs paper" style="left:70px;top:785px;width:940px;padding:22px 38px 18px 38px"><div>${tab('信里写')}</div><div style="font:600 43px/68px Song;margin-top:14px;text-align:justify">${p.q}</div><div style="font:400 23px/30px Hei;color:#6b6252;margin-top:8px;text-align:right">《人民日报》1984年3月30日二版转载</div></div>`, P);
    tl.in(qc, cl(p.id[0], 2) - .3, .5, 20);
    const isTerm = p.bt.startsWith('名词');
    const tB = i === 4 ? cl('2.12', 2) - .2 : at(p.id[1]) - .2;
    const bc = h(`<div class="abs" style="left:70px;top:1085px;width:940px;padding:20px 38px 20px 38px;background:rgba(12,10,8,.88);border-left:10px solid ${isTerm ? 'var(--red)' : 'var(--gold)'}"><div>${tab(p.bt, isTerm ? 'var(--red)' : '#3b352b', isTerm ? '#fff' : '#e3c27e')}</div><div style="font:700 ${p.b.length > 44 ? 38 : 44}px/${p.b.length > 44 ? 58 : 64}px Hei;color:var(--cream);margin-top:12px">${p.b}</div><div style="font:400 25px/36px Hei;color:var(--dim);margin-top:8px">${p.bs}</div></div>`, P);
    tl.in(bc, tB, .5, 20);
  });
  // 收束
  const S = so(C, '五样里，没有一样是钱。<br>要的都是：厂里的事，<br>能在厂里定。', 700); tl.in(S, at('2.14') - .1, .5, 20);
}, { zoom: 1.02 });

// ═════════ 3 一句承诺 ═════════
scene('pledge', at('3.1') - LEAD, en('3.4') + .5, (R, tl, t0) => {
  R.innerHTML = `<div class="bg-lamp"></div><div class="cam"></div>`;
  const C = R.querySelector('.cam');
  const P = h(`<div class="paper lined" style="left:70px;top:262px;width:940px;height:740px"></div>`, C);
  tl.set(P, { o: 0, y: 50 }); tl.to(P, { o: 1, y: 0 }, t0, .6);
  const tx = h(`<div class="abs" style="left:52px;top:80px;width:840px;font:600 51px/78px Song;color:#1b1814;letter-spacing:1px">
  <span class="a">我们要这些权力，</span><span class="b"><u>绝不是为了以权谋私</u>，</span><span class="c">只是想在目前条件下，</span><span class="d">给企业松松绑</span><span class="d2">……</span><span class="e">如果有人滥用职权，</span><span class="f">谋取私利，</span><span class="g">搞违法乱纪，</span><span class="hh"><u>当受党纪、</u></span><span class="i"><u>政纪直至国法惩处</u>。</span></div>`, P);
  tx.querySelectorAll('u').forEach(u => { u.style.textDecoration = 'none'; u.style.backgroundImage = 'linear-gradient(#b02a1f,#b02a1f)'; u.style.backgroundRepeat = 'no-repeat'; u.style.backgroundPosition = '0 92%'; u.style.backgroundSize = '0% 7px'; });
  const sp = k => tx.querySelector('.' + k);
  const seq = [['a', cl('3.2', 0)], ['b', cl('3.2', 1)], ['c', cl('3.2', 2)], ['d', cl('3.2', 3)], ['d2', en('3.2')], ['e', cl('3.3', 0)], ['f', cl('3.3', 1)], ['g', cl('3.3', 2)], ['hh', cl('3.3', 3)], ['i', cl('3.3', 4)]];
  seq.forEach(([k, t], j) => { const e = sp(k); const cs = chars(e); const nx = j < seq.length - 1 ? seq[j + 1][1] : en('3.3'); tl.type(cs, t - .12, Math.min(nx, t + cs.length * .16) - .1, .22); });
  const ul = (el, t, d) => tl.fn(t, d, p => { el.style.backgroundSize = (p * 100).toFixed(1) + '% 7px'; }, E.io);
  const us = tx.querySelectorAll('u'); ul(us[0], ce('3.2', 1) - .5, .7); ul(us[1], ce('3.3', 3) - .3, .5); ul(us[2], en('3.3') - .7, .9);
  h(`<div class="src dark" style="left:52px;top:682px">据《人民日报》1984年3月30日二版转载 · 信纸为示意</div>`, P);
  // 55 个签名（示意）
  const L = h(`<div class="paper" style="left:70px;top:1030px;width:940px;height:330px"></div>`, C); tl.set(L, { o: 0, y: 40 }); tl.to(L, { o: 1, y: 0 }, at('3.2'), .6);
  h(`<div class="abs" style="left:34px;top:14px;font:700 26px/40px Hei;color:#5a5244;letter-spacing:4px">联名 · 55人 <span style="font-weight:400;letter-spacing:1px">（签名为示意，非真实笔迹）</span></div>`, L);
  const sv = h(`<svg class="abs" style="left:0;top:0" width="940" height="330"></svg>`, L);
  let seed = 11; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const T0 = at('3.2') + .6, T1 = en('3.3') + .3;
  for (let i = 0; i < 55; i++) {
    const x0 = 38 + (i % 11) * 79.5, y0 = 96 + Math.floor(i / 11) * 50; let d = `M${x0} ${y0}`; let x = 0;
    const n = 4 + Math.floor(rnd() * 3);
    for (let k = 0; k < n; k++) { const dx = 7 + rnd() * 9; d += ` q${(dx * .4).toFixed(1)} ${(-(8 + rnd() * 16)).toFixed(1)} ${dx.toFixed(1)} ${(rnd() * 10 - 5).toFixed(1)}`; if (rnd() < .5) d += ` q${(-3 - rnd() * 4).toFixed(1)} ${(8 + rnd() * 10).toFixed(1)} ${(4 + rnd() * 5).toFixed(1)} ${(rnd() * 4 - 2).toFixed(1)}`; x += dx; }
    const p = document.createElementNS('http://www.w3.org/2000/svg', 'path'); p.setAttribute('d', d); p.setAttribute('fill', 'none'); p.setAttribute('stroke', '#22346d'); p.setAttribute('stroke-width', 2.6); p.setAttribute('stroke-linecap', 'round'); sv.appendChild(p);
    tl.set(p, { dash: 0 }); tl.to(p, { dash: 1 }, T0 + (T1 - T0) * i / 55, .35, E.lin);
  }
  const cnt = h(`<div class="abs num" style="right:36px;top:8px;font-size:44px;line-height:52px;color:var(--red)">0</div>`, L); tl.set(cnt, { num: 0 }); tl.to(cnt, { num: 55 }, T0, T1 - T0, E.lin);
  tl.to(P, { o: .22 }, at('3.4') - .3, .4); tl.to(L, { o: .5 }, at('3.4') - .3, .4);
  const S = so(C, '他们要权，同时把自己的<br>后路，先交了出去。', 520); tl.in(S, at('3.4') - .1, .5, 20);
});
