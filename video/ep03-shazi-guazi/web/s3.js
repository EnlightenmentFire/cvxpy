/* S3 一个讨饭来的孩子 */
(function () {
  const sec = TL.secs.s3;
  chapter('2', '一个讨饭来的孩子', sec.s, sec.n + 0.25, '怀远 → 芜湖');
  const HD = '二 · 一个讨饭来的孩子';

  /* 3a 地图：怀远 → 芜湖 */
  const a0 = sec.n, a1 = c('b3') - 0.15;
  ENGINE.scene({ id: 's3map', t0: a0, t1: a1 + 0.3, cls: 'bg-dark', build(S) {
    header(S, HD);
    S.cam({ s0: 1.0, s1: 1.07, y0: 0, y1: -20 });
    const G = GEO.anhui, sc = 0.71, ox = 270, oy = 512;
    const sv = h('svg', { width: W, height: H, style: { position: 'absolute', left: 0, top: 0 } });
    const g = h('g', { transform: `translate(${ox},${oy}) scale(${sc})` });
    const out = h('path', { d: G.d, fill: 'rgba(232,221,198,.06)', stroke: C.paper, 'stroke-width': 3.2, 'stroke-linejoin': 'round' });
    g.append(out); sv.append(g); S.add(sv);
    S.draw(out, a0 + 0.1, 2.2, 5200);
    const P = n => [ox + G.places[n][0] * sc, oy + G.places[n][1] * sc];
    const [hx, hy] = P('怀远'), [wx, wy] = P('芜湖');
    const prov = box(ox + 150, oy + 560, 300, null, 'song', { fontWeight: 900, fontSize: '80px', letterSpacing: '30px', color: 'rgba(232,221,198,.13)' }, '安徽');
    S.add(prov); S.fade(prov, a0 + 1.0);
    const dot = (x, y, col, at, lab, lx, ly) => {
      const d = box(x - 13, y - 13, 26, 26, '', { borderRadius: '50%', background: col, boxShadow: `0 0 0 8px ${col}33` }); S.add(d); S.pop(d, at);
      const l = box(x + lx, y + ly, null, null, 'song', { fontWeight: 900, fontSize: '56px', color: col, whiteSpace: 'nowrap', letterSpacing: '4px' }, lab); S.add(l); S.fadeUp(l, at + 0.1);
      return d; };
    const tW = cw('b1', '芜湖') - 0.2, tH = cw('b2', '安徽怀远') - 0.1, tGo = cw('b2', '逃荒');
    dot(wx, wy, C.red, tW, '芜湖', 26, -40);
    dot(hx, hy, C.paper, tH, '怀远', -150, -44);
    const pth = h('path', { d: `M${hx},${hy} C${hx + 120},${hy + 90} ${wx - 150},${wy - 140} ${wx - 16},${wy - 14}`, fill: 'none', stroke: C.gold, 'stroke-width': 6, 'stroke-dasharray': '4 16', 'stroke-linecap': 'round' });
    sv.append(pth);
    S.on(t => { const p = pr(t, tGo - 0.1, 2.2, 'io'); pth.style.clipPath = `inset(0 0 ${(1 - p) * 100}% 0)`; });
    const cap = box(hx - 150, (hy + wy) / 2 + 20, null, null, 'hei', { fontWeight: 600, fontSize: '34px', letterSpacing: '6px', color: C.gold, whiteSpace: 'nowrap' }, '逃荒 · 讨饭');
    S.add(cap); S.fade(cap, tGo + 0.8);
    // b1 caption
    const b1c = box(70, 310, 940, null, 'song', { fontWeight: 900, fontSize: '70px', lineHeight: '1.35', color: C.paper }, '芜湖，一个炒瓜子的<br><span style="font-size:48px;font-weight:700;color:rgba(232,221,198,.7)">没读过《资本论》</span>');
    S.add(b1c); S.a(b1c, { at: a0 + 0.2, d: 0.6, from: { o: 0, y: 30 }, out: c('b2') - 0.3 });
    nameTag(S, 80, 326, '年广久', '芜湖个体户，“傻子瓜子”老板', c('b2') - 0.05);
    const born = box(80, 1246, 940, null, 'hei', { fontWeight: 500, fontSize: '36px', letterSpacing: '3px', color: C.dim }, '1937 年生 · 安徽怀远人');
    S.add(born); S.fade(born, cw('b2', '1937') - 0.1);
    src(S, 1304, '生年、籍贯据多篇报道；生年另有 1940 年一说', cw('b2', '1937') + 0.5);
  } });

  /* 3b 水果摊 → 割尾巴 */
  const b0 = a1, b1 = c('b4') - 0.15;
  ENGINE.scene({ id: 's3stall', t0: b0, t1: b1 + 0.3, cls: 'bg-kraft', build(S) {
    header(S, HD, false);
    S.cam({ s0: 1.0, s1: 1.05 });
    const ink = C.ink;
    const nine = box(70, 300, 500, null, 'song', { fontWeight: 900, fontSize: '330px', lineHeight: '1', color: ink }, '9<span style="font-size:110px;margin-left:10px">岁</span>');
    S.add(nine); S.a(nine, { at: b0 + 0.15, d: 0.6, from: { o: 0, y: 40 } });
    const sub = box(80, 650, 900, null, 'hei', { fontWeight: 600, fontSize: '42px', letterSpacing: '3px', color: ink }, '跟着父亲，在街头卖水果');
    S.add(sub); S.fadeUp(sub, cw('b3', '跟着') - 0.1);
    // stall silhouette
    const sv = h('svg', { width: 940, height: 520, viewBox: '0 0 940 520', style: { position: 'absolute', left: '70px', top: '760px' } });
    const st = h('g', {});
    // awning
    st.append(h('path', { d: 'M150,150 L640,150 L690,230 L100,230 Z', fill: ink }));
    for (let i = 0; i < 6; i++) st.append(h('path', { d: `M${100 + i * 98.3},230 q49,56 98.3,0 Z`, fill: i % 2 ? ink : C.red2 }));
    st.append(h('rect', { x: 150, y: 230, width: 12, height: 250, fill: ink }), h('rect', { x: 628, y: 230, width: 12, height: 250, fill: ink }));
    st.append(h('rect', { x: 120, y: 400, width: 550, height: 100, fill: ink }));
    const rr = RNG(5);
    for (let i = 0; i < 22; i++) st.append(h('circle', { cx: 150 + (i % 11) * 49, cy: 385 - Math.floor(i / 11) * 38 + rr() * 6, r: 22, fill: i % 3 === 0 ? C.red2 : i % 3 === 1 ? '#c98b2b' : '#6e7a3a', stroke: ink, 'stroke-width': 3 }));
    // adult + child silhouettes
    st.append(h('circle', { cx: 770, cy: 245, r: 30, fill: ink }), h('path', { d: 'M725,500 C722,360 735,290 770,290 C805,290 818,360 815,500 Z', fill: ink }));
    st.append(h('circle', { cx: 868, cy: 352, r: 23, fill: ink }), h('path', { d: 'M836,500 C834,420 842,384 868,384 C894,384 902,420 900,500 Z', fill: ink }));
    st.append(h('rect', { x: 60, y: 500, width: 860, height: 6, fill: ink }));
    sv.append(st); S.add(sv); S.a(sv, { at: b0 + 0.3, d: 0.8, from: { o: 0, y: 40 } });
    // cut
    const tCut = cw('b3', '资本主义尾巴'), tOff = cw('b3', '割掉');
    const cut = h('line', { x1: 40, y1: 500, x2: 720, y2: 120, stroke: C.red2, 'stroke-width': 14, 'stroke-linecap': 'round' });
    sv.append(cut); S.draw(cut, tOff - 0.15, 0.35, 800);
    S.on(t => { const p = pr(t, tOff + 0.1, 0.8, 'io'); st.style.opacity = lerp(1, 0.22, p); });
    const lab = box(250, 900, 620, 124, 'song c', { fontWeight: 900, fontSize: '78px', lineHeight: '112px', letterSpacing: '4px', color: C.red2, border: `7px solid ${C.red2}`, background: 'rgba(232,221,198,.9)', whiteSpace: 'nowrap' }, '资本主义尾巴');
    S.add(lab); S.a(lab, { at: tCut - 0.1, d: 0.3, e: 'out5', from: { o: 0, s: 1.6 }, base: 'rotate(-5deg)' });
    const gl = box(70, 1226, 940, null, 'hei', { fontWeight: 600, fontSize: '32px', lineHeight: '1.45', color: ink }, '当时的说法：私人做的小买卖，被看作要“割掉”的尾巴。'); S.add(gl); S.fade(gl, tCut + 0.5);
    src(S, 1304, '据 2008 年《环球人物》等报道，回忆性质', tCut, null, ink);
  } });

  /* 3c 1963 投机倒把 */
  const c0 = b1, c1 = c('b6') - 0.15;
  ENGINE.scene({ id: 's3jail', t0: c0, t1: c1 + 0.3, cls: 'bg-dark', build(S) {
    header(S, HD);
    S.cam({ s0: 1.0, s1: 1.05 });
    const yr = box(0, 330, 1080, null, 'song c', { fontWeight: 900, fontSize: '330px', lineHeight: '1', color: C.paper, letterSpacing: '6px' }, '1963');
    S.add(yr); S.a(yr, { at: c0 + 0.15, d: 0.7, from: { o: 0, s: 1.08 } });
    // bars
    for (let i = 0; i < 9; i++) { const b = box(110 + i * 105, 290, 22, 470, '', { background: 'linear-gradient(90deg,#0c0a08,#3a322b 45%,#0c0a08)', transformOrigin: 'top center', boxShadow: '4px 0 10px rgba(0,0,0,.5)' }); S.add(b); S.a(b, { at: cw('b4', '坐了') - 0.5 + i * 0.04, d: 0.45, e: 'out5', from: { sy: 0 } }); }
    const st = box(210, 800, 660, 150, 'song c', { fontWeight: 900, fontSize: '110px', lineHeight: '136px', letterSpacing: '12px', color: C.red, border: `7px solid ${C.red}`, whiteSpace: 'nowrap' }, '投机倒把');
    S.add(st); S.a(st, { at: cw('b4', '投机倒把') - 0.15, d: 0.3, e: 'out5', from: { o: 0, s: 1.7 }, base: 'rotate(-3deg)' });
    const one = box(0, 985, 1080, null, 'hei c', { fontWeight: 600, fontSize: '44px', letterSpacing: '8px', color: C.paper }, '坐牢一年');
    S.add(one); S.fadeUp(one, cw('b4', '坐了') - 0.05);
    chip(S, 1080, '投机倒把', '当时的罪名。低价买进高价卖出、长途贩运，都可能算。', cw('b4', '这是') - 0.1);
    src(S, 1304, '据多篇报道；未见判决原件', cw('b4', '坐了') + 0.4);
  } });

  /* 3d 炒瓜子 */
  const d0 = c1, d1 = c('b7') - 0.15;
  ENGINE.scene({ id: 's3wok', t0: d0, t1: d1 + 0.3, cls: 'bg-dark', build(S) {
    header(S, HD);
    S.cam({ s0: 1.02, s1: 1.1, y0: 0, y1: -24 });
    const glow = box(140, 760, 800, 620, '', { background: 'radial-gradient(ellipse at 50% 60%, rgba(230,120,30,.5), rgba(200,60,20,.18) 45%, transparent 70%)' });
    S.add(glow); S.on(t => { glow.style.opacity = 0.75 + 0.25 * Math.sin(t * 9.1) * Math.sin(t * 3.7); });
    const sv = h('svg', { width: W, height: H, style: { position: 'absolute', left: 0, top: 0 } }); S.add(sv);
    // flames
    const flames = [];
    for (let i = 0; i < 9; i++) { const x = 300 + i * 60; const f = h('path', { d: `M${x},1290 C${x - 46},1230 ${x - 12},1190 ${x},1120 C${x + 16},1190 ${x + 46},1230 ${x},1290 Z`, fill: i % 2 ? '#e2762a' : '#d2a03c', opacity: .92 }); sv.append(f); flames.push([f, x, i]); }
    S.on(t => flames.forEach(([f, x, i]) => { const k = 0.75 + 0.35 * Math.sin(t * (7 + i * 0.9) + i * 1.7) + 0.12 * Math.sin(t * 17 + i); f.setAttribute('transform', `translate(${x},1290) scale(${0.9 + 0.1 * Math.sin(t * 5 + i)},${k}) translate(${-x},-1290)`); }));
    // wok
    sv.append(h('path', { d: 'M170,900 C200,1160 380,1210 540,1210 C700,1210 880,1160 910,900 Z', fill: '#0d0b09', stroke: '#3a322b', 'stroke-width': 6 }));
    sv.append(h('ellipse', { cx: 540, cy: 900, rx: 370, ry: 58, fill: '#17130f', stroke: '#4a4037', 'stroke-width': 6 }));
    sv.append(h('rect', { x: 120, y: 884, width: 70, height: 26, rx: 10, fill: '#0d0b09', stroke: '#3a322b', 'stroke-width': 4 }), h('rect', { x: 890, y: 884, width: 70, height: 26, rx: 10, fill: '#0d0b09', stroke: '#3a322b', 'stroke-width': 4 }));
    // seeds
    const rr = RNG(11), seeds = [];
    for (let i = 0; i < 70; i++) { const s = h('ellipse', { rx: 15, ry: 7.5, fill: i % 5 === 0 ? '#e8ddc6' : '#2a231d', stroke: '#e8ddc6', 'stroke-width': 2 }); sv.append(s); seeds.push({ s, x: 260 + rr() * 560, ph: rr() * 6.28, sp: 1.8 + rr() * 1.6, amp: 20 + rr() * 150, rot: rr() * 360, dx: (rr() - .5) * 60 }); }
    S.on(t => seeds.forEach(o => { const u = (t * o.sp * 0.5 + o.ph) % 1, yj = Math.sin(u * Math.PI); const sw = Math.sin(t * 2.6) * 50; o.s.setAttribute('transform', `translate(${o.x + sw * yj + o.dx * u},${905 - yj * o.amp}) rotate(${o.rot + u * 300})`); }));
    // spatula
    const sp = h('g', {}); sp.append(h('rect', { x: -10, y: -470, width: 20, height: 400, rx: 8, fill: '#6b4a2a' }), h('path', { d: 'M-70,-80 L70,-80 L58,40 L-58,40 Z', fill: '#8d8478', stroke: '#2a231d', 'stroke-width': 4 }));
    sv.append(sp); S.on(t => { const a = Math.sin(t * 2.6); sp.setAttribute('transform', `translate(${560 + a * 150},${880 - Math.abs(Math.cos(t * 2.6)) * 30}) rotate(${28 + a * 16})`); });
    const ti = box(70, 310, 940, null, 'song', { fontWeight: 900, fontSize: '84px', lineHeight: '1.3', color: C.paper }, '学会了炒瓜子');
    const t2 = box(74, 440, 940, null, 'hei', { fontWeight: 600, fontSize: '44px', lineHeight: '1.5', color: C.gold, letterSpacing: '4px' }, '偷偷地卖');
    const t3 = box(74, 530, 940, null, 'hei', { fontWeight: 500, fontSize: '38px', lineHeight: '1.6', color: C.dim, letterSpacing: '2px' }, '管的人来了，他走<br>人走了，他再来');
    S.add(ti, t2, t3); S.fadeUp(ti, cw('b6', '学会') - 0.2); S.fadeUp(t2, cw('b6', '偷偷') - 0.1); S.fadeUp(t3, ce('b6') + 0.1);
    src(S, 1304, '据当年及后来的报道，回忆性质；学艺的年份说法不一', d0 + 1.2);
  } });

  /* 3e “傻子”的来历 + takeaway */
  const e0 = d1, e1 = sec.e;
  ENGINE.scene({ id: 's3name', t0: e0, t1: e1 + 0.2, cls: 'bg-kraft', build(S) {
    header(S, HD, false);
    S.cam({ s0: 1.0, s1: 1.04 });
    const ink = C.ink;
    const sign = box(150, 310, 780, 250, '', { background: 'linear-gradient(#7c2218,#63190f)', boxShadow: '0 16px 40px rgba(0,0,0,.45), inset 0 0 0 10px rgba(0,0,0,.18), inset 0 0 0 14px rgba(232,221,198,.35)' });
    sign.innerHTML = `<div class="brush c" style="font-size:210px;line-height:250px;color:#f1e6cd;letter-spacing:40px;padding-left:40px;white-space:nowrap">傻子</div>`;
    S.add(sign); S.a(sign, { at: e0 + 0.15, d: 0.5, e: 'back', from: { o: 0, s: .8 }, base: 'rotate(-1.5deg)' });
    const q = box(0, 590, 1080, null, 'hei c', { fontWeight: 600, fontSize: '40px', letterSpacing: '6px', color: ink }, '这个名字怎么来的？两种说法');
    S.add(q); S.fade(q, cw('b7', '名字') - 0.1);
    const card = (y, no, html, at) => { const e = box(70, y, 940, 270, 'bg-paper', { boxShadow: '0 12px 30px rgba(0,0,0,.3)', borderLeft: `12px solid ${C.red2}`, padding: '26px 34px' }, `<div class="hei" style="font-weight:700;font-size:30px;letter-spacing:8px;color:${C.red2}">说法${no}</div><div class="song" style="font-weight:800;font-size:50px;line-height:1.45;margin-top:8px;color:${ink}">${html}</div>`); S.add(e); S.a(e, { at, d: 0.6, from: { o: 0, x: -40 } }); return e; };
    card(680, '一', '父亲被街坊叫“傻子”，<br>他是“小傻子”。', cw('b7', '一说', 0) - 0.15);
    const c2 = card(980, '二', '你买一包，<br>他再<span class="red">抓一把</span>送你。', cw('b7', '一说', 1) - 0.15);
    // kraft bag + seeds
    const bag = h('svg', { width: 200, height: 230, viewBox: '0 0 200 230', style: { position: 'absolute', left: '700px', top: '10px' } });
    bag.append(h('path', { d: 'M30,40 L42,28 L54,40 L66,28 L78,40 L90,28 L102,40 L114,28 L126,40 L138,28 L150,40 L162,28 L170,40 L186,222 L14,222 Z', fill: C.kraft, stroke: ink, 'stroke-width': 5, 'stroke-linejoin': 'round' }), h('rect', { x: 52, y: 100, width: 96, height: 76, fill: '#7c2218' }));
    bag.append(h('text', { x: 100, y: 152, 'text-anchor': 'middle', 'font-family': 'Brush', 'font-size': 44, fill: '#f1e6cd' }, '瓜子'));
    c2.append(bag);
    const rr = RNG(3);
    for (let i = 0; i < 16; i++) { const s = box(640 + rr() * 60, 20 + rr() * 30, 26, 13, '', { borderRadius: '50%', background: '#2a231d', border: '2px solid #e8ddc6' }); c2.append(s); const tx = 110 + rr() * 60, at = cw('b7', '抓一把') + i * 0.05; const r0 = rr() * 180;
      S.on(t => { const p = pr(t, at, 0.6, 'io'); s.style.opacity = p > 0 && p < 1 ? 1 : p >= 1 ? 0 : 0; s.style.transform = `translate(${tx * p}px,${-90 * Math.sin(p * Math.PI) + 40 * p}px) rotate(${r0 + p * 300}deg)`; }); }
    src(S, 1296, '两种说法均见于报道与回忆；本人另说过因“多送一点”得名', cw('b7', '一说', 1) + 0.6, null, ink);
    takeaway(S, 'b9', '碰到“7 个人”这条线之前，<br>他已经因为做买卖，<br><em>丢过摊子，坐过牢。</em>');
  } });
})();
