/* 场景 D：捌 督责 · 玖 如此者三 · 拾 囚安得上书 · 终 上蔡东门 */
(function () {
  const { TL, SEG, SCN, clamp, ramp, eo, eio, lerp, vis, S, E, rnd, el, svg, scene, quote, label, term, stamp, typeBlock, CITE87 } = F;
  const dur = id => E(id) - S(id);

  /* 禁中示意：皇帝在内，郎中令守门，丞相在外 */
  function palace(parent) {
    const d = el(parent, 'abs', 'left:0;top:470px;width:1080px;height:640px;opacity:0');
    d.innerHTML = `<svg viewBox="0 0 1080 640" width="1080" height="640" style="position:absolute;inset:0;overflow:visible">
      <g filter="url(#rough2)"><path d="M150 96 C 300 84, 380 50, 430 10 L 650 10 C 700 50, 780 84, 930 96 L 920 112 L 160 112 Z" fill="#12100c" stroke="#6b5f49" stroke-width="3"/>
      <rect x="210" y="112" width="660" height="200" fill="#0f0d0a" stroke="#6b5f49" stroke-width="3"/>
      <rect x="486" y="232" width="108" height="80" fill="#050505" stroke="#c9a45c" stroke-width="3"/></g>
      <path class="road" d="M540 320 V 560" stroke="#4a4132" stroke-width="3" stroke-dasharray="6 10"/></svg>`;
    d.inner = el(d, 'abs serif', 'left:210px;top:124px;width:660px;text-align:center;font-size:54px;font-weight:900;letter-spacing:.3em;text-indent:.3em;color:#f1e3c0', '二世');
    d.innerNote = el(d, 'abs serif', 'left:210px;top:196px;width:660px;text-align:center;font-size:26px;color:#8f8369;letter-spacing:.2em;text-indent:.2em', '居禁中');
    d.gate = el(d, 'abs serif', 'left:610px;top:244px;width:400px;font-size:34px;font-weight:900;color:#f0c56a;letter-spacing:.1em;white-space:nowrap;text-shadow:0 0 10px #000', '← 郎中令 赵高');
    d.li = el(d, 'abs serif', 'left:440px;top:540px;width:200px;text-align:center;font-size:44px;font-weight:900;color:#f1e3c0;letter-spacing:.14em;border:2px solid #c9a45c;padding:4px 0 8px;background:#14110c', '丞相');
    return d;
  }

  /* ================= 捌 督责 ================= */
  scene('duze', (root, add) => {
    root.style.background = '#090807';
    const a = SCN.duze.cut_in, b = SCN.duze.cut_out;
    const pal = palace(root);
    term(root, add, '郎中令', '管宫廷门户、警卫的官<br><span style="color:#9c9075">「常侍中用事」——天天在皇帝身边</span>', 96, 1140, S('d1') + dur('d1') * .42, S('d2') - .1, { size: 56, w: 640 });
    add(t => { pal.style.opacity = vis(t, S('d1') + .2, S('d2') - .1, .7, .5); });
    /* 恐惧，重爵禄 */
    label(root, add, '子李由为三川守，群盗西略地，「过去弗能禁」', 'left:0;right:0;top:500px;text-align:center;font-size:30px;color:#8f8369;letter-spacing:.08em', S('d2') + .6, S('d5') + 1.6, { cls: 'serif' });
    quote(root, add, 'd2', ['李斯{恐惧|#d2382c}，{重爵禄|#f0c56a}', '不知所出'], { y: 600, size: 84, lh: 1.5, from: S('d2') + dur('d2') * .6, dur: 2.0, until: S('d5') + 1.6, cite: CITE87, gloss: '重：看重，舍不得　｜　不知所出：不知道怎么办' });
    label(root, add, '「乃阿二世意，欲求容」', 'left:0;right:0;top:1010px;text-align:center;font-size:40px;font-weight:700;color:#b9ad93;letter-spacing:.1em', S('d5') + .2, S('d5') + 1.6, { cls: 'serif' });
    /* 督责书 */
    label(root, add, '《督责书》', 'left:0;right:0;top:486px;text-align:center;font-size:50px;font-weight:700;letter-spacing:.3em;text-indent:.3em;color:#c9a45c', S('d5') + 1.8, S('d8') - .1, { cls: 'serif' });
    label(root, add, '督责：严加督察，有过必罚', 'left:0;right:0;top:562px;text-align:center;font-size:28px;color:#8f8369;letter-spacing:.1em', S('d5') + 2.4, S('d8') - .1);
    quote(root, add, 'd6', ['主{独制|#f0c56a}于天下', '而{无所制|#f0c56a}也'], { y: 660, size: 100, lh: 1.5, until: S('d8') - .1, cite: CITE87 + ' · 李斯上二世书', gloss: '独制：独自控制　｜　无所制：不受任何约束', glossAt: S('d7') });
    /* 刑者相半于道 */
    const road = el(root, 'abs', 'left:90px;top:480px;width:900px;height:250px;opacity:0');
    let f = ''; const marked = [];
    for (let i = 0; i < 24; i++) { const r = Math.floor(i / 12), c = i % 12, m = ((i * 7 + r) % 2 === 0); marked.push(m); f += `<g transform="translate(${c * 75 + 8} ${r * 122})"><g class="fg" transform="scale(1.15)">${ART.figure('#8f8369')}</g>${m ? `<path class="sl" d="M2 96 L 50 6" stroke="#c8372d" stroke-width="7" stroke-linecap="round" opacity="0"/>` : ''}</g>`; }
    road.innerHTML = `<svg viewBox="0 0 900 250" width="900" height="250">${f}</svg>`;
    const sls = [...road.querySelectorAll('.sl')];
    const q9a = typeBlock(root, ['刑者{相半|#d2382c}于道'], { y: 742, size: 62 }), q9b = typeBlock(root, ['死人{日成积|#d2382c}于市'], { y: 1196, size: 62 });
    const heap = el(root, 'abs', 'left:90px;top:860px;width:900px;height:320px;opacity:0');
    let hs = ''; const cols = 18, maxN = 16; const strokes = [];
    for (let c = 0; c < cols; c++) { const n = Math.round(maxN * Math.exp(-Math.pow((c - 8.5) / 5.2, 2)) + 1); for (let k = 0; k < n; k++) { strokes.push({ c, k, n }); hs += `<rect class="tk" x="${c * 50 + 4 + rnd(c * 31 + k) * 6}" y="${306 - k * 19}" width="${34 + rnd(c + k * 7) * 8}" height="7" fill="#b9ad93" transform="rotate(${(rnd(c * 3 + k) - .5) * 9} ${c * 50 + 24} ${306 - k * 19})" opacity="0"/>`; } }
    heap.innerHTML = `<svg viewBox="0 0 900 320" width="900" height="320">${hs}<path d="M0 316 H900" stroke="#4a4132" stroke-width="3"/></svg>`;
    const tks = [...heap.querySelectorAll('.tk')];
    label(root, add, '相半：各占一半', 'left:0;right:0;top:826px;text-align:center;font-size:26px;color:#8f8369', S('d10') + .3, S('d11') - .2);
    label(root, add, '日成积：一天天堆积', 'left:0;right:0;top:1282px;text-align:center;font-size:26px;color:#8f8369', S('d10') + dur('d10') * .5, S('d11') - .2);
    const pl = F.pillars(root, 500, { head: '拦得住皇帝的东西' });
    label(root, add, '「若此则谓督责之诚……群臣百姓救过不给，何变之敢图？」', 'left:60px;width:960px;top:1060px;text-align:center;font-size:30px;font-weight:700;color:#8f8369;letter-spacing:.04em', S('d11') + 1.6, b + .2, { cls: 'serif' });
    add(t => {
      const s9 = S('d9'), d9 = dur('d9'), end = S('d11') - .2;
      const rv = vis(t, S('d8') - .1, end, .5, .5); road.style.opacity = rv; heap.style.opacity = vis(t, s9 + d9 * .45, end, .5, .5);
      q9a.style.opacity = t < s9 - .1 ? 0 : 1 - ramp(t, end - .4, end); q9a.reveal(ramp(t, s9 - .1, s9 + d9 * .4));
      q9b.style.opacity = t < s9 + d9 * .45 ? 0 : 1 - ramp(t, end - .4, end); q9b.reveal(ramp(t, s9 + d9 * .5, s9 + d9 * .95));
      const n = ramp(t, s9 + .2, s9 + d9 * .5) * sls.length; sls.forEach((s, i) => s.setAttribute('opacity', clamp(n - i)));
      const m = eio(ramp(t, s9 + d9 * .5, S('d10') + dur('d10'))) * maxN; tks.forEach((e, i) => e.setAttribute('opacity', clamp(m - strokes[i].k) * .9));
      const pv = vis(t, S('d11'), b + .2, .6, .5); pl.style.opacity = pv;
      if (pv > 0) { pl.set(0, 1, '不立子弟为王<br>功臣为诸侯'); pl.set(1, 1, '诗书百家语<br>蠲除去之'); pl.set(2, ramp(t, S('d11') + dur('d11') * .55, S('d11') + dur('d11') * .55 + 1), '《督责书》<br>「掩驰说之口」'); }
    });
  });

  /* ================= 玖 如此者三 ================= */
  scene('trap', (root, add) => {
    root.style.background = '#090807';
    const b = SCN.trap.cut_out; const t1 = S('t1'), d1 = dur('t1');
    const pal = palace(root); pal.innerNote.textContent = '方燕乐，妇女居前';
    const note = el(pal, 'abs', 'left:240px;top:120px;width:600px;height:70px');
    note.innerHTML = `<svg viewBox="0 0 600 70" width="600" height="70">${[0, 1, 2].map(i => `<path class="wv" d="M${20 + i * 30} 35 q 12 -22 24 0 t 24 0" stroke="#c9a45c" stroke-width="3" fill="none"/><path class="wv" d="M${490 + i * 30} 35 q 12 -22 24 0 t 24 0" stroke="#c9a45c" stroke-width="3" fill="none"/>`).join('')}</svg>`;
    label(root, add, '赵高：「上方间，可奏事」', 'left:650px;top:778px;font-size:32px;font-weight:700;color:#f0c56a;letter-spacing:.06em;white-space:nowrap', t1 + d1 * .32, S('t4') - .2, { cls: 'serif' });
    label(root, add, '间：有空', 'left:656px;top:828px;font-size:26px;color:#8f8369', t1 + d1 * .36, S('t4') - .2);
    const t3 = t1 + d1 * .56, step = d1 * .13;
    const cnt = ['一', '二', '三'].map((c, i) => label(root, add, c, `left:${150 + i * 76}px;top:860px;width:60px;text-align:center;font-size:56px;font-weight:900;color:#d2382c;border:3px solid #c8372d;padding-bottom:6px`, t3 + i * step + step * .6, S('t4') - .2, { cls: 'serif' }));
    quote(root, add, 't1', ['如此者{三|#d2382c}'], { y: 1150, size: 80, from: t3 + step * 2.3, dur: .8, until: S('t4') - .2, cite: CITE87 });
    add(t => {
      pal.style.opacity = vis(t, t1 + .2, S('t4') - .2, .7, .5);
      let y = 540; for (let i = 0; i < 3; i++) { const p = ramp(t, t3 + i * step, t3 + (i + 1) * step); const go = p < .6 ? eio(p / .6) : 1 - eio((p - .6) / .4); if (p > 0 && p < 1) y = lerp(540, 330, go); }
      pal.li.style.top = y + 'px';
      note.querySelectorAll('.wv').forEach((w, i) => w.setAttribute('transform', `translate(0 ${Math.sin(t * 5 + i) * 5})`));
    });
    quote(root, add, 't5', ['丞相岂{少|#f0c56a}我哉？', '且{固|#f0c56a}我哉？'], { y: 560, size: 96, lh: 1.5, until: S('t7') - .1, cite: '二世语 · ' + CITE87, gloss: '少：轻视　｜　固：鄙陋', glossAt: S('t6') });
    label(root, add, '赵高　→　二世', 'left:96px;top:486px;font-size:36px;font-weight:900;letter-spacing:.2em;color:#c9a45c', S('t7') + .1, b + .2, { cls: 'serif' });
    [['沙丘之谋，丞相与焉', '沙丘那件事，丞相有份', .12], ['其意亦望裂地而王', '他是想分一块地，自己称王', .5], ['丞相居外，权重于陛下', '', .82]].forEach(([q, g, k], i) => {
      label(root, add, `「${q}」${g ? `<div style="font-family:Noto Sans SC;font-weight:400;font-size:28px;color:#9c9075;margin-top:8px;letter-spacing:.04em">${g}</div>` : ''}`, `left:96px;top:${590 + i * 170}px;font-size:56px;font-weight:900;color:#e9dfc8;border-left:6px solid #c8372d;padding-left:26px;letter-spacing:.04em;white-space:nowrap;line-height:1.3`, S('t7') + dur('t7') * k, b + .2, { cls: 'serif', rise: 12 });
    });
  });

  /* ================= 拾 囚安得上书 ================= */
  scene('prison', (root, add) => {
    root.style.background = '#070605';
    const a = SCN.prison.cut_in, b = SCN.prison.cut_out;
    const bars = el(root, 'abs', 'left:0;top:455px;width:1080px;height:900px;opacity:0');
    bars.innerHTML = `<svg viewBox="0 0 1080 900" width="1080" height="900">${Array.from({ length: 9 }, (_, i) => `<rect x="${40 + i * 124}" y="0" width="16" height="900" fill="#100e0b" stroke="#2a251d" stroke-width="2"/>`).join('')}</svg>`;
    add(t => { bars.style.opacity = vis(t, a + .3, S('j11') - .2, .8, .6) * .75; });
    label(root, add, '二世：「其以李斯属郎中令！」', 'left:0;right:0;top:500px;text-align:center;font-size:38px;font-weight:700;color:#b9ad93;letter-spacing:.08em', S('j1') - .2, S('j4') - .2, { cls: 'serif' });
    label(root, add, '把李斯交给郎中令——也就是赵高——来审', 'left:0;right:0;top:562px;text-align:center;font-size:27px;color:#8f8369;letter-spacing:.06em', S('j1') + .3, S('j4') - .2);
    quote(root, add, 'j2', ['{榜掠千余|#d2382c}', '不胜痛，自诬服'], { y: 680, size: 96, lh: 1.5, until: S('j4') - .2, cite: CITE87, gloss: '榜（péng）掠：拷打　｜　自诬服：自己认下没犯的罪', glossAt: S('j3') });
    /* 七罪书 */
    const card = el(root, 'abs', 'left:150px;top:490px;width:780px;height:640px;opacity:0;background:linear-gradient(180deg,#cdbb8e,#b9a373);color:#1a140b;filter:url(#rough2);transform-origin:20% 0');
    const sins = ['兼六国，立秦为天子', '北逐胡貉，南定百越', '尊大臣，盛其爵位', '立社稷，修宗庙', '平斗斛、度量、文章', '治驰道，兴游观', '缓刑罚，薄赋敛'];
    card.innerHTML = `<div class="serif" style="font-size:38px;font-weight:900;letter-spacing:.3em;text-align:center;padding:26px 0 14px;border-bottom:3px solid #5b4a2c;margin:0 40px">狱中上书 · 自列七罪</div>` +
      sins.map((s, i) => `<div class="serif" style="display:flex;align-items:baseline;margin:0 46px;padding:13px 0;border-bottom:1.5px solid rgba(60,45,20,.4);font-size:36px;font-weight:700"><span style="color:#8a1f16;font-weight:900;width:132px;letter-spacing:.1em">罪${'一二三四五六七'[i]}矣</span><span>${s}</span></div>`).join('');
    const gong = stamp(root, add, '条条是功', 560, 760, S('j4') + dur('j4') * .44, S('j4') + dur('j4') * .74, { size: 76, rot: -10, bw: 6, pad: '0 18px 8px' });
    const shout = quote(root, add, 'j4', ['{囚安得上书！|#d2382c}'], { y: 700, size: 124, from: S('j4') + dur('j4') * .72, dur: .7, until: S('j7') - .1, cite: '赵高语 · ' + CITE87, gloss: '「使吏弃去不奏」——扔掉，不上报' });
    add(t => {
      const j4 = S('j4'), d4 = dur('j4');
      const fall = eio(ramp(t, j4 + d4 * .7, j4 + d4 * .7 + .9));
      card.style.opacity = vis(t, j4 + .1, j4 + d4 * .7 + .9, .5, .3);
      card.style.transform = `translate(${fall * 260}px, ${fall * 900}px) rotate(${fall * 38}deg) scale(${lerp(1.02, 1, ramp(t, j4, j4 + 2))})`;
    });
    /* 三张面具 */
    const j7 = S('j7'), d7 = dur('j7');
    label(root, add, '「赵高使其客十余辈，诈为御史、谒者、侍中，更往覆讯斯」', 'left:60px;width:960px;top:486px;text-align:center;font-size:30px;font-weight:700;color:#9c9075;letter-spacing:.04em', j7 + .2, S('j11') - .2, { cls: 'serif' });
    const masks = [['御史', '监察'], ['谒者', '传达'], ['侍中', '近侍']].map(([n, g], i) => {
      const d = el(root, 'abs', `left:${116 + i * 300}px;top:580px;width:250px;height:480px;opacity:0`);
      d.innerHTML = `<svg viewBox="0 0 220 300" width="250" height="340" style="position:absolute;left:0;top:0">${ART.mask('#cdbf9c')}</svg>`;
      el(d, 'abs serif', 'left:0;width:250px;top:346px;text-align:center;font-size:50px;font-weight:900;letter-spacing:.14em;color:#f1e3c0', n);
      el(d, 'abs sans', 'left:0;width:250px;top:416px;text-align:center;font-size:26px;color:#8f8369;letter-spacing:.2em', g);
      d.hit = el(d, 'abs serif', 'left:0;width:250px;top:466px;text-align:center;font-size:38px;font-weight:900;color:#d2382c;letter-spacing:.04em;opacity:0;text-shadow:0 0 10px #000,0 0 4px #000', '以实对 → 榜');
      return d;
    });
    const real = el(root, 'abs', 'left:415px;top:580px;width:250px;height:480px;opacity:0');
    real.innerHTML = `<svg viewBox="0 0 220 300" width="250" height="340" style="position:absolute;left:0;top:0">${ART.mask('#cdbf9c')}</svg>`;
    el(real, 'abs serif', 'left:-80px;width:410px;top:346px;text-align:center;font-size:46px;font-weight:900;letter-spacing:.1em;color:#f0c56a', '二世所使 · 真');
    quote(root, add, 'j8', ['斯以为如前', '{终不敢更言|#d2382c}'], { y: 1070, size: 72, lh: 1.4, from: S('j8') + dur('j8') * .4, dur: 1.6, until: S('j11') - .2, cite: CITE87 });
    add(t => {
      masks.forEach((m, i) => {
        const v = vis(t, j7 + d7 * .1 + i * .25, S('j11') - .2, .5, .5); const cyc = clamp(1 - Math.abs(((t - j7 - d7 * .45) / (d7 * .16)) - i));
        const gone = ramp(t, S('j8') - .1, S('j8') + .6);
        m.style.opacity = v * lerp(1, .16, gone); m.style.transform = `translateY(${-14 * (t > j7 + d7 * .4 ? cyc : 0)}px)`;
        m.hit.style.opacity = ramp(t, j7 + d7 * .72 + i * .3, j7 + d7 * .72 + i * .3 + .3) * (1 - gone);
      });
      real.style.opacity = vis(t, S('j8') + .2, S('j11') - .2, .6, .5);
    });
    /* 这说明什么 */
    const pl = F.pillars(root, 500, { head: '他帮着建起来的这套体制里' });
    label(root, add, '没有任何东西<br>能保护一个<span style="color:#d2382c">失宠的丞相</span>', 'left:0;right:0;top:1040px;text-align:center;font-size:62px;font-weight:900;line-height:1.5;letter-spacing:.08em;color:#f1e3c0', S('j11') + dur('j11') * .5, b + .2, { cls: 'serif', rise: 14 });
    add(t => { const v = vis(t, S('j11') - .1, b + .2, .6, .5); pl.style.opacity = v; if (v > 0) { pl.set(0, 1, '不立子弟为王<br>功臣为诸侯'); pl.set(1, 1, '诗书百家语<br>蠲除去之'); pl.set(2, 1, '《督责书》<br>「掩驰说之口」'); } });
  });

  /* ================= 终 上蔡东门 ================= */
  scene('end', (root, add) => {
    root.style.background = '#070605';
    const a = SCN.end.cut_in, b = SCN.end.cut_out;
    label(root, add, '二世二年七月', 'left:0;right:0;top:520px;text-align:center;font-size:40px;font-weight:700;letter-spacing:.3em;text-indent:.3em;color:#c9a45c', S('e1') - .2, S('e2') - .1, { cls: 'serif' });
    label(root, add, '具斯五刑，论腰斩咸阳市', 'left:0;right:0;top:640px;text-align:center;font-size:70px;font-weight:900;letter-spacing:.08em;color:#f1e3c0', S('e1') + .8, S('e2') - .1, { cls: 'serif' });
    label(root, add, '夷三族', 'left:0;right:0;top:800px;text-align:center;font-size:150px;font-weight:900;letter-spacing:.2em;text-indent:.2em;color:#d2382c', S('e1') + dur('e1') * .72, S('e2') - .1, { cls: 'serif' });
    label(root, add, CITE87, 'left:0;right:0;top:1040px;text-align:center;font-size:26px;color:#8f8369;letter-spacing:.18em', S('e1') + 1.2, S('e2') - .1, { cls: 'serif' });
    /* 黄犬 */
    const dusk = F.dusk(root, 640, 640);
    label(root, add, '牵黄犬，俱出<span style="color:#e8b84f">上蔡东门</span>，逐狡兔', 'left:0;right:0;top:500px;text-align:center;font-size:58px;font-weight:900;letter-spacing:.06em;color:#f1e3c0', S('e2') + .3, S('e4') - .2, { cls: 'serif' });
    label(root, add, '上蔡：他拼了一辈子要离开的地方', 'left:0;right:0;top:596px;text-align:center;font-size:30px;color:#9c9075;letter-spacing:.14em', S('e2') + dur('e2') * .55, S('e4') - .2);
    add(t => { const v = vis(t, S('e2') - .2, S('e4') - .1, 1.0, .8); dusk.style.opacity = v; if (v > 0) dusk.run(S('e2') - 2, t); });
    /* 太史公曰 */
    label(root, add, '太史公曰', 'left:0;right:0;top:500px;text-align:center;font-size:44px;font-weight:700;letter-spacing:.5em;text-indent:.5em;color:#c9a45c', S('e4') + .1, S('e7') - .1, { cls: 'serif' });
    quote(root, add, 'e5', ['持{爵禄|#f0c56a}之重', '{阿顺苟合|#f0c56a}'], { y: 620, size: 110, lh: 1.5, until: S('e7') - .1, cite: CITE87, gloss: '阿（ē）顺：曲意顺从　｜　苟合：无原则地附和', glossAt: S('e6') });
    /* 索隐述赞 + 两块版画回归 */
    label(root, add, '唐 · 司马贞《史记索隐》述赞', 'left:0;right:0;top:470px;text-align:center;font-size:34px;font-weight:700;letter-spacing:.2em;text-indent:.2em;color:#c9a45c', S('e7') + .1, S('e10') - .2, { cls: 'serif' });
    quote(root, add, 'e8', ['鼠在所居', '{人固择地|#f0c56a}'], { y: 640, size: 120, lh: 1.5, until: S('e10') - .2, gloss: '固：本来', glossAt: S('e9') });
    const top = F.ratPanel(root, 'ce', 72, 470), bot = F.ratPanel(root, 'cang', 72, 900);
    const doorL = el(bot, 'abs', 'left:0;top:0;width:50%;height:100%;background:#050403;border-right:3px solid #3a2c14;transform-origin:0 50%;transform:scaleX(0)');
    const doorR = el(bot, 'abs', 'right:0;top:0;width:50%;height:100%;background:#050403;border-left:3px solid #3a2c14;transform-origin:100% 50%;transform:scaleX(0)');
    const own = el(bot, 'abs serif', 'left:0;right:0;top:118px;text-align:center;font-size:84px;font-weight:900;letter-spacing:.3em;text-indent:.3em;color:#c9a45c;opacity:0', '皇帝的');
    label(root, add, '李斯 —— 一只选对了粮仓的老鼠', 'left:0;right:0;top:560px;text-align:center;font-size:44px;font-weight:700;letter-spacing:.16em;color:#c9a45c', E('e12') + 2.0, b + 1, { cls: 'serif', din: 1.0 });
    label(root, add, '引文据《史记》卷八十七、六十三、二十九、六，及司马贞《索隐》述赞', 'left:0;right:0;top:1296px;text-align:center;font-size:24px;color:#6e634e;letter-spacing:.08em', E('e12') + 1.2, b + 1);
    add(t => {
      const ghost = vis(t, S('e8') + .5, S('e10'), 1.2, .1) * .16;
      const on = ramp(t, S('e10') - .3, S('e10') + .6);
      const e11 = ramp(t, S('e11') - .1, S('e11') + .6), e12 = ramp(t, S('e12') - .1, S('e12') + .3);
      const close = eio(ramp(t, S('e12') + dur('e12') * .35, S('e12') + dur('e12') * .35 + 1.3));
      const fin = eio(ramp(t, E('e12') + .5, E('e12') + 3.2));
      top.style.opacity = Math.max(ghost, on * lerp(1, .45, e11 * (1 - e12)));
      bot.style.opacity = Math.max(ghost, on) * lerp(1, .0, fin);
      doorL.style.transform = `scaleX(${close})`; doorR.style.transform = `scaleX(${close})`;
      own.style.opacity = ramp(t, S('e12') + dur('e12') * .35 + 1.35, S('e12') + dur('e12') * .35 + 1.9);
      top.style.transform = `translateY(${fin * 220}px) scale(${1 + fin * .1})`;
      top.rat.setAttribute('transform', `translate(0 ${Math.sin(t * 2.2) * 1.5})`);
      top.intr.setAttribute('transform', 'translate(330 0)');
      bot.rat.setAttribute('transform', `translate(0 ${Math.sin(t * 1.4) * 2.2})`);
    });
  });
})();
