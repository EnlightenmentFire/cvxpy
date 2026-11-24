/* 场景 B：肆 逐客 · 伍 韩非 · 陆 物禁大盛 */
(function () {
  const { TL, SEG, SCN, clamp, ramp, eo, eio, lerp, vis, S, E, rnd, el, svg, scene, quote, label, term, stamp, typeBlock, CITE87, CITE63 } = F;
  const dur = id => E(id) - S(id);

  /* 竖排名牌 */
  function tablet(parent, name, x, y, o = {}) {
    const w = o.w ?? 190, h = o.h ?? 380;
    const d = el(parent, 'abs', `left:${x}px;top:${y}px;width:${w}px;height:${h}px;opacity:0`);
    d.box = el(d, 'abs', `inset:0;border:3px solid ${o.col ?? '#c9a45c'};background:linear-gradient(180deg,#1d1811,#0f0d0a);filter:url(#rough2)`);
    d.tx = el(d, 'abs serif', `inset:0;display:flex;align-items:center;justify-content:center;writing-mode:vertical-rl;font-size:${o.size ?? 104}px;font-weight:900;letter-spacing:.14em;color:${o.col ?? '#f1e3c0'}`, name);
    return d;
  }

  /* 「能对皇帝说不」的三样东西：封国 / 诗书 / 谏臣（陆、捌、拾 三处复用） */
  F.pillars = function (parent, y, o = {}) {
    const wrap = el(parent, 'abs', `left:0;top:${y}px;width:1080px;height:520px;opacity:0`);
    const head = el(wrap, 'abs serif', 'left:0;right:0;top:0;text-align:center;font-size:36px;font-weight:700;letter-spacing:.16em;color:#b9ad93', o.head ?? '能对皇帝说「不」的东西');
    const items = [['封国', '分封的子弟功臣'], ['诗书', '可以引古非今的书'], ['谏臣', '敢当面反对的人']].map(([n, sub], i) => {
      const x = 150 + i * 300;
      const t = tablet(wrap, n, x, 80, { w: 180, h: 300, size: 92 }); t.style.opacity = 1;
      const subEl = el(wrap, 'abs sans', `left:${x - 60}px;width:300px;top:396px;text-align:center;font-size:26px;color:#9c9075;letter-spacing:.04em`, sub);
      const x1 = el(t, 'abs', 'left:-18px;right:-18px;top:50%;height:9px;background:#c8372d;transform:rotate(-58deg) scaleX(0);filter:url(#inkbleed)');
      const note = el(wrap, 'abs serif', `left:${x - 80}px;width:340px;top:440px;text-align:center;font-size:25px;font-weight:700;color:#d2382c;letter-spacing:.04em;opacity:0;line-height:1.35`, '');
      return { t, subEl, x1, note };
    });
    wrap.set = (i, k, noteHtml) => {                   // k: 0 完好 → 1 被拆
      const it = items[i]; it.x1.style.transform = `rotate(-58deg) scaleX(${eo(clamp(k * 2))})`;
      it.t.tx.style.opacity = lerp(1, .22, clamp(k * 1.5 - .3)); it.t.box.style.opacity = lerp(1, .4, clamp(k * 1.5 - .3));
      if (noteHtml !== undefined) { if (it.note.innerHTML !== noteHtml) it.note.innerHTML = noteHtml; it.note.style.opacity = clamp(k * 2 - .8); }
    };
    wrap.items = items; return wrap;
  };

  /* ================= 肆 逐客 ================= */
  scene('zhuke', (root, add) => {
    const z1 = S('z1'), d1 = dur('z1');
    const tagS = 'font-size:30px;font-weight:900;padding:2px 14px 6px;background:rgba(10,9,8,.7);letter-spacing:.08em;';
    label(root, add, '郑国渠<span style="font-weight:500;font-size:24px;color:#b9ad93">　凿泾水，东注洛，三百余里</span>', `left:300px;top:650px;${tagS}color:#f0c56a;border:1.5px solid #c9a45c`, z1 + 3.0, S('z2') + .3, { cls: 'serif' });
    label(root, add, '《史记·河渠书》', 'left:306px;top:716px;font-size:24px;color:#8f8369;letter-spacing:.16em', z1 + 3.4, S('z2') + .3, { cls: 'serif' });
    label(root, add, '韩 → 水工郑国', `left:700px;top:940px;${tagS}color:#d8ccb2;border:1.5px solid #6b5f49`, z1 + 1.4, S('z2') + .3, { cls: 'serif' });
    label(root, add, '「欲罢之，毋令东伐」', 'left:560px;top:1010px;width:440px;text-align:right;font-size:30px;font-weight:700;color:#b9ad93;letter-spacing:.06em', z1 + d1 * .7, S('z2') + .3, { cls: 'serif' });
    label(root, add, '罢：使之疲敝', 'left:560px;top:1060px;width:440px;text-align:right;font-size:26px;color:#8f8369', z1 + d1 * .74, S('z2') + .3);
    stamp(root, add, '间', 520, 760, z1 + d1 * .56, S('z2') + .3, { size: 120, rot: -9, bw: 7, pad: '0 20px 10px' });

    /* 逐客令 */
    const zk = S('z2'), d2 = dur('z2');
    label(root, add, '请一切<span style="color:#d2382c">逐客</span>', 'left:0;right:0;top:500px;text-align:center;font-size:104px;font-weight:900;letter-spacing:.16em;text-indent:.16em;color:#f1e3c0', zk + .3, S('z5') - .1, { cls: 'serif', rise: 14 });
    label(root, add, '秦宗室大臣皆言秦王', 'left:0;right:0;top:450px;text-align:center;font-size:28px;color:#8f8369;letter-spacing:.2em', zk + .3, S('z5') - .1, { cls: 'serif' });
    const tabs = ['客', '客', '客', '李斯', '客'].map((n, i) => {
      const t = tablet(root, n, 96 + i * 184, 720, { w: 152, h: 270, size: n === '李斯' ? 82 : 92, col: n === '李斯' ? '#f0c56a' : '#8f8369' });
      add(tt => {
        const v = vis(tt, zk + .8 + i * .12, S('z5') - .1, .4, .4); t.style.opacity = v; if (v <= 0) return;
        const out = eio(ramp(tt, zk + d2 * .45 + i * .22, zk + d2 * .45 + i * .22 + 1.0));
        t.style.transform = `translateX(${out * (n === '李斯' ? 26 : 60)}px) rotate(${out * (n === '李斯' ? 3 : 7)}deg)`;
        if (n !== '李斯') t.style.opacity = v * lerp(1, .18, out);
      });
      return t;
    });
    quote(root, add, 'z2', ['李斯议亦在{逐|#d2382c}中'], { y: 1040, size: 72, from: zk + d2 * .58, dur: 1.2, until: S('z5') - .1, cite: CITE87, gloss: '他自己，也在被赶走的名单上' });

    /* 谏逐客书 */
    label(root, add, '《谏逐客书》', 'left:0;right:0;top:470px;text-align:center;font-size:50px;font-weight:700;letter-spacing:.3em;text-indent:.3em;color:#c9a45c', S('z5') + .1, S('z8') - .1, { cls: 'serif' });
    quote(root, add, 'z6', ['{太山|#f0c56a}不让土壤', '故能成其{大|#f0c56a}', '{河海|#f0c56a}不择细流', '故能就其{深|#f0c56a}'], { y: 580, size: 86, lh: 1.5, until: S('z8') - .1, cite: CITE87, gloss: '太山＝泰山　｜　不让：不拒绝　｜　不择：不挑拣', glossAt: S('z7') });
    /* 撤令、复官、廷尉 */
    stamp(root, add, '除逐客之令', 250, 560, S('z8') + .5, S('z9') - .1, { size: 96, rot: -6, bw: 7, pad: '2px 22px 10px' });
    label(root, add, '复李斯官　·　官至廷尉', 'left:0;right:0;top:770px;text-align:center;font-size:40px;font-weight:700;letter-spacing:.2em;color:#d8ccb2', S('z8') + 1.4, S('z9') - .1, { cls: 'serif' });
    term(root, add, '廷尉', '最高司法官', 300, 880, S('z8') + 2.4, S('z9') - .1);
    /* 这说明什么 */
    const z9 = S('z9'), d9 = dur('z9');
    label(root, add, '《谏逐客书》', 'left:0;right:0;top:520px;text-align:center;font-size:76px;font-weight:900;letter-spacing:.14em;text-indent:.14em;color:#f1e3c0', z9 + .1, SCN.zhuke.cut_out + .2, { cls: 'serif' });
    label(root, add, '写于他自己要被赶走之时', 'left:0;right:0;top:640px;text-align:center;font-size:34px;letter-spacing:.2em;color:#9c9075', z9 + .4, SCN.zhuke.cut_out + .2);
    const two = (html, x, t0) => label(root, add, html, `left:${x}px;top:760px;width:420px;text-align:center;font-size:44px;font-weight:700;line-height:1.5;color:#e9dfc8;padding:26px 0 30px;border-top:3px solid #c9a45c;background:rgba(20,17,12,.7)`, t0, SCN.zhuke.cut_out + .2, { cls: 'serif', rise: 14 });
    two('为自己<br><span style="font-size:30px;font-weight:500;color:#b9ad93">保住在秦国的位置</span>', 96, z9 + d9 * .5);
    two('为秦国<br><span style="font-size:30px;font-weight:500;color:#b9ad93">「客何负于秦哉」</span>', 564, z9 + d9 * .66);
    label(root, add, '后话：那条渠照样修成，溉田四万余顷，「秦以富强，卒并诸侯」——《河渠书》', 'left:96px;width:888px;top:1040px;text-align:center;font-size:27px;line-height:1.6;color:#8f8369;letter-spacing:.04em', z9 + d9 * .72, SCN.zhuke.cut_out + .2);
  });

  /* ================= 伍 韩非 ================= */
  scene('hanfei', (root, add) => {
    root.style.background = '#090807';
    const a = SCN.hanfei.cut_in, b = SCN.hanfei.cut_out;
    const xun = label(root, add, '荀 卿', 'left:0;right:0;top:540px;text-align:center;font-size:54px;font-weight:900;letter-spacing:.3em;text-indent:.3em;color:#c9a45c', S('h1') + .8, S('h4') - .2, { cls: 'serif' });
    const lines = el(root, 'abs', 'left:0;top:630px;width:1080px;height:120px;opacity:0');
    lines.innerHTML = `<svg viewBox="0 0 1080 120" width="1080" height="120"><path d="M540 6 V 44 M300 44 H780 M300 44 V 110 M780 44 V 110" stroke="#6b5f49" stroke-width="3" fill="none"/></svg>`;
    const li = tablet(root, '李斯', 205, 760), hf = tablet(root, '韩非', 685, 760);
    const lt = label(root, add, '＜', 'left:0;right:0;top:870px;text-align:center;font-size:120px;font-weight:900;color:#f0c56a', S('h2') + .3, S('h4') - .2, { cls: 'serif' });
    label(root, add, '俱事荀卿', 'left:0;right:0;top:700px;text-align:center;font-size:28px;color:#8f8369;letter-spacing:.3em;text-indent:.3em', S('h1') + 1.6, S('h4') - .2, { cls: 'serif' });
    quote(root, add, 'h2', ['斯自以为{不如非|#f0c56a}'], { y: 1170, size: 76, until: S('h4') - .2, cite: CITE63 });
    /* 秦王读书 */
    quote(root, add, 'h4', ['寡人得见此人与之游', '{死不恨矣！|#f0c56a}'], { y: 480, size: 68, lh: 1.45, from: S('h4') + .5, dur: 2.2, until: S('h7') - .2, cite: '秦王见《孤愤》《五蠹》之书 · ' + CITE63, gloss: '恨：遗憾' });
    /* 害之 */
    quote(root, add, 'h7', ['李斯、姚贾{害|#d2382c}之'], { y: 480, size: 80, from: S('h7') + .9, dur: 1.2, until: S('h10') - .1, cite: CITE63, gloss: '害：忌恨。<br>「非终为韩不为秦……不如以过法诛之」' });
    /* 狱栏 + 药 */
    const bars = el(root, 'abs', 'left:655px;top:730px;width:250px;height:440px;opacity:0');
    bars.innerHTML = `<svg viewBox="0 0 250 440" width="250" height="440">${[0, 1, 2, 3, 4, 5].map(i => `<rect x="${14 + i * 42}" y="0" width="12" height="440" fill="#050505" stroke="#3a342a" stroke-width="2"/>`).join('')}<rect x="0" y="30" width="250" height="12" fill="#050505" stroke="#3a342a" stroke-width="2"/><rect x="0" y="398" width="250" height="12" fill="#050505" stroke="#3a342a" stroke-width="2"/></svg>`;
    const vial = el(root, 'abs', 'left:0;top:900px;width:90px;height:110px;opacity:0');
    vial.innerHTML = `<svg viewBox="0 0 90 110" width="90" height="110"><g filter="url(#rough2)"><path d="M32 8 H58 V30 C 80 44, 84 76, 70 96 H 20 C 6 76, 10 44, 32 30 Z" fill="#b9ad93"/><rect x="28" y="2" width="34" height="10" fill="#7a2f22"/></g><text x="45" y="76" text-anchor="middle" font-size="34" font-weight="900" fill="#0b0a09">药</text></svg>`;
    quote(root, add, 'h11', ['李斯使人{遗非药|#d2382c}', '使自杀'], { y: 480, size: 76, lh: 1.4, until: S('h13') - .2, cite: CITE63, gloss: '遗（wèi）：送给', glossAt: S('h12') });
    label(root, add, '「秦王后悔之，使人赦之，非已死矣」', 'left:0;right:0;top:1190px;text-align:center;font-size:38px;font-weight:700;color:#b9ad93;letter-spacing:.06em', S('h12') + dur('h12') * .4, S('h13') - .2, { cls: 'serif' });
    /* 这说明什么 */
    label(root, add, '史书没有写他怎么想', 'left:0;right:0;top:500px;text-align:center;font-size:54px;font-weight:700;letter-spacing:.14em;color:#e9dfc8', S('h13') + .1, b + .2, { cls: 'serif' });
    label(root, add, '只写了两件事', 'left:0;right:0;top:590px;text-align:center;font-size:32px;letter-spacing:.3em;color:#8f8369', S('h13') + .5, b + .2);
    label(root, add, '斯自以为不如非<span style="display:inline-block;width:150px"></span>李斯使人遗非药', 'left:0;right:0;top:1190px;text-align:center;font-size:36px;font-weight:700;color:#c9a45c;letter-spacing:.04em', S('h13') + 1.4, b + .2, { cls: 'serif' });
    add(t => {
      const tv = vis(t, S('h1') + 1.2, b + .2, .7, .5);
      lines.style.opacity = vis(t, S('h1') + 1.2, S('h4') - .2, .6, .4);
      li.style.opacity = tv; hf.style.opacity = tv;
      const dead = ramp(t, S('h12') + dur('h12') * .35, S('h12') + dur('h12') * .35 + 1.6);
      hf.tx.style.opacity = lerp(1, .12, dead); hf.box.style.opacity = lerp(1, .45, dead);
      const lift = eio(ramp(t, S('h4') - .2, S('h4') + .6)) - eio(ramp(t, S('h13') - .3, S('h13') + .5));
      hf.style.transform = `translateY(${-10 * lift}px) scale(${1 + .06 * lift})`;
      bars.style.opacity = ramp(t, S('h10'), S('h10') + .5) * (1 - ramp(t, b - .3, b + .2));
      const vp = eio(ramp(t, S('h11') + .3, S('h11') + dur('h11') * .9));
      vial.style.opacity = ramp(t, S('h11'), S('h11') + .4) * (1 - ramp(t, S('h12') + .4, S('h12') + 1.2));
      vial.style.left = lerp(410, 600, vp) + 'px';
    });
  });

  /* ================= 陆 物禁大盛 ================= */
  scene('peak', (root, add) => {
    root.style.background = '#090807';
    const a = SCN.peak.cut_in, b = SCN.peak.cut_out;
    label(root, add, '丞相', 'left:0;right:0;top:500px;text-align:center;font-size:230px;font-weight:900;letter-spacing:.2em;text-indent:.2em;color:#f1e3c0;line-height:1.1', S('p1') + .5, S('p2') - .1, { cls: 'serif', rise: 20 });
    label(root, add, '百官之首', 'left:0;right:0;top:800px;text-align:center;font-size:48px;letter-spacing:.5em;text-indent:.5em;color:#c9a45c', S('p1') + 1.3, S('p2') - .1);
    label(root, add, '二十余年，竟并天下，尊主为皇帝，以斯为丞相', 'left:0;right:0;top:900px;text-align:center;font-size:28px;color:#8f8369;letter-spacing:.1em', S('p1') + 1.5, S('p2') - .1, { cls: 'serif' });
    /* 三样东西 */
    const pl = F.pillars(root, 480); const p2 = S('p2'), d2 = dur('p2');
    quote(root, add, 'p3', ['若有欲学者，{以吏为师|#f0c56a}'], { y: 1060, size: 66, until: S('p6') - .2, cite: CITE87 + ' · 始皇三十四年', gloss: '吏：官吏。想学，只能跟官府学' });
    /* 余烬 */
    const emb = el(root, 'abs', 'left:360px;top:420px;width:360px;height:460px;opacity:0;pointer-events:none');
    emb.innerHTML = `<svg viewBox="0 0 360 460" width="360" height="460">${Array.from({ length: 26 }, (_, i) => `<circle class="e" r="${2 + rnd(i) * 3}" fill="#f0a94a"/>`).join('')}</svg>`;
    const es = [...emb.querySelectorAll('.e')];
    add(t => {
      pl.style.opacity = vis(t, p2 - .2, S('p6') - .2, .6, .5);
      const k0 = ramp(t, p2 + d2 * .28, p2 + d2 * .28 + .9), k1 = ramp(t, p2 + d2 * .72, p2 + d2 * .72 + 1.2);
      pl.set(0, k0, '不立子弟为王<br>功臣为诸侯'); pl.set(1, k1, '诗书百家语<br>蠲除去之'); pl.set(2, 0);
      const ev = vis(t, p2 + d2 * .72, S('p4'), .3, 1.2); emb.style.opacity = ev;
      if (ev > 0) es.forEach((c, i) => { const ph = ((t - p2) * (.35 + rnd(i + 3) * .5) + rnd(i + 9)) % 1; c.setAttribute('cx', 90 + rnd(i + 20) * 180 + Math.sin(ph * 6 + i) * 14); c.setAttribute('cy', 400 - ph * 400); c.setAttribute('opacity', (1 - ph) * .9); });
    });
    /* 车骑以千数 */
    const grid = el(root, 'abs', 'left:60px;top:500px;width:960px;height:560px;opacity:0');
    const COLS = 12, ROWS = 9; let g = '';
    for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++) g += `<g class="c" transform="translate(${c * 80} ${r * 60}) scale(.74)">${ART.cart(r % 2 ? '#b08f4e' : '#c9a45c')}</g>`;
    grid.innerHTML = `<svg viewBox="0 0 960 560" width="960" height="560">${g}</svg>`;
    const cs = [...grid.querySelectorAll('.c')];
    quote(root, add, 'p6', ['门廷车骑{以千数|#f0c56a}'], { y: 1080, size: 70, from: S('p6') + 1.2, dur: 1.2, until: S('p9') - .1, cite: CITE87, gloss: '儿子都娶秦公主，女儿都嫁秦公子' });
    quote(root, add, 'p9', ['物禁大盛', '吾未知所{税驾|#f0c56a}也！'], { y: 560, size: 100, lh: 1.5, until: b + .3, cite: CITE87, gloss: '大＝太　｜　税驾：解马停车，指归宿', glossAt: S('p10') });
    const lone = el(root, 'abs', 'left:0;top:1090px;width:140px;height:70px;opacity:0'); lone.innerHTML = `<svg viewBox="0 0 100 50" width="140" height="70">${ART.cart('#c9a45c')}</svg>`;
    add(t => {
      const gv = vis(t, S('p6') + .1, S('p9') + .3, .5, .9); grid.style.opacity = gv * lerp(1, .0, ramp(t, S('p9') - .2, S('p9') + .5));
      if (gv > 0) { const n = eo(ramp(t, S('p6') + .2, S('p6') + dur('p6') * .8)) * cs.length; cs.forEach((c, i) => c.setAttribute('opacity', clamp(n - ((i * 37) % cs.length)))); grid.style.transform = `scale(${lerp(1.08, 1, ramp(t, S('p6'), S('p9')))})`; }
      const lv = vis(t, S('p10') + .3, b + .4, .8, .8); lone.style.opacity = lv * .9; lone.style.left = lerp(760, 240, ramp(t, S('p10'), b + .4)) + 'px';
    });
    label(root, add, '车，停在哪儿？', 'left:0;right:0;top:1180px;text-align:center;font-size:30px;letter-spacing:.3em;color:#8f8369', S('p10') + 1.6, b + .3);
  });
})();
