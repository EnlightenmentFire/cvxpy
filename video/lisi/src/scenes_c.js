/* 场景 C：柒 沙丘（全片高潮） */
(function () {
  const { TL, SEG, SCN, clamp, ramp, eo, eio, lerp, vis, S, E, rnd, el, svg, scene, quote, label, term, stamp, typeBlock, CITE87 } = F;
  const dur = id => E(id) - S(id);

  scene('shaqiu', (root, add) => {
    const a = SCN.shaqiu.cut_in, b = SCN.shaqiu.cut_out;
    root.style.background = 'linear-gradient(180deg,#04060a 0%,#0a1018 46%,#0d141c 60%,#050506 60.2%,#030303 100%)';
    /* 夜空 */
    const sky = el(root, 'abs', 'inset:0');
    sky.innerHTML = `<svg viewBox="0 0 1080 1920" width="1080" height="1920" style="position:absolute;inset:0">
      <defs><radialGradient id="moonG"><stop offset="0" stop-color="#cfd8dc" stop-opacity=".5"/><stop offset="1" stop-color="#cfd8dc" stop-opacity="0"/></radialGradient></defs>
      ${Array.from({ length: 46 }, (_, i) => `<circle cx="${rnd(i) * 1080}" cy="${460 + rnd(i + 60) * 620}" r="${.8 + rnd(i + 5) * 1.5}" fill="#c9d3d8" opacity="${.18 + rnd(i + 8) * .5}"/>`).join('')}
      <circle cx="150" cy="540" r="130" fill="url(#moonG)"/><circle cx="150" cy="540" r="30" fill="#dfe6e8" opacity=".9"/><circle cx="163" cy="533" r="29" fill="#070b11"/>
      <path d="M-20 1152 C 160 1138, 300 1160, 520 1150 C 760 1140, 900 1158, 1100 1146 V 1400 H -20 Z" fill="#030303" filter="url(#rough)"/>
      <path d="M-20 1152 C 160 1138, 300 1160, 520 1150 C 760 1140, 900 1158, 1100 1146" fill="none" stroke="#1c2730" stroke-width="2"/></svg>`;
    /* 辒辌车与侍者 */
    const car = el(root, 'abs', 'left:260px;top:850px;width:560px;height:304px');
    car.innerHTML = `<svg viewBox="-50 0 700 380" width="560" height="304" style="overflow:visible"><ellipse cx="300" cy="200" rx="330" ry="200" fill="#e9b45a" opacity=".1" filter="url(#glowBig)"/>${ART.carriage('#020202')}</svg>`;
    const win = car.querySelector('.carWin');
    const men = el(root, 'abs', 'left:0;top:1010px;width:260px;height:150px;opacity:0');
    men.innerHTML = `<svg viewBox="0 0 260 150" width="260" height="150" style="overflow:visible"><g transform="translate(60 0) scale(.68)">${ART.man('#020202', true)}<rect x="62" y="70" width="46" height="8" fill="#020202"/></g><g transform="translate(140 8) scale(.64)">${ART.man('#020202', true)}<rect x="62" y="70" width="46" height="8" fill="#020202"/></g></svg>`;
    const veil = el(root, 'abs', 'inset:0;background:#040506;opacity:0');

    label(root, add, '始皇三十七年七月 · 沙丘', 'left:0;right:0;top:490px;text-align:center;font-size:40px;font-weight:700;letter-spacing:.3em;text-indent:.3em;color:#c9a45c', S('s1') - .5, S('s2') - .1, { cls: 'serif' });
    label(root, add, '「始皇帝至沙丘，病甚」', 'left:0;right:0;top:570px;text-align:center;font-size:32px;color:#8f8369;letter-spacing:.16em', S('s1') + 1.2, S('s2') - .1, { cls: 'serif' });

    /* 封好的诏书与玺 */
    const desk = el(root, 'abs', 'left:0;top:480px;width:1080px;height:240px;opacity:0');
    desk.innerHTML = `<svg viewBox="0 0 1080 240" width="1080" height="240" style="overflow:visible">
      <g transform="translate(250 22) scale(.92)">${ART.letter()}</g><g transform="translate(680 30) scale(1.02)">${ART.seal()}</g></svg>`;
    label(root, add, '赐扶苏书<br><span style="color:#d8ccb2">已封，未授使者</span>', 'left:228px;top:706px;width:320px;text-align:center;font-size:27px;line-height:1.5;color:#8f8369;letter-spacing:.08em', S('s2') + .6, S('s5') - .2, { cls: 'serif' });
    label(root, add, '皇帝之玺', 'left:640px;top:706px;width:240px;text-align:center;font-size:27px;color:#8f8369;letter-spacing:.08em', S('s2') + 1.2, S('s5') - .2, { cls: 'serif' });
    quote(root, add, 's3', ['书及玺{皆在赵高所|#f0c56a}'], { y: 1180, size: 66, until: S('s4') + dur('s4') * .45, cite: CITE87 });
    term(root, add, '赵高', '中车府令，兼行符玺令事<br><span style="color:#9c9075">管皇帝的车马，兼管印玺</span>', 96, 1196, S('s4') + dur('s4') * .5, S('s5') - .2, { size: 58, w: 620 });
    /* 秘不发丧 */
    quote(root, add, 's5', ['置始皇居{辒辌车|#f0c56a}中', '百官奏事、上食{如故|#f0c56a}'], { y: 520, size: 62, lh: 1.55, from: S('s5') + .2, dur: 2.6, until: S('s6') - .2, cite: CITE87, gloss: '辒辌（wēn liáng）车：可卧、有窗的车' });

    /* 对话开始 */
    const hi = S('s6'), d6 = dur('s6');
    const spk = (name, x, right, t0, t1) => label(root, add, name, `${right ? 'right' : 'left'}:${x}px;top:486px;font-size:40px;font-weight:900;letter-spacing:.2em;color:#c9a45c;border-bottom:2px solid #c9a45c;padding-bottom:6px`, t0, t1, { cls: 'serif' });
    spk('赵高', 96, false, hi + .2, S('s7') - .1); spk('李斯', 96, true, hi + d6 * .7, S('s7') - .1);
    label(root, add, '欲改立少子<span style="color:#f0c56a;font-weight:900">胡亥</span>', 'left:214px;top:490px;font-size:34px;font-weight:700;color:#d8ccb2;letter-spacing:.08em', hi + .5, S('s7') - .1, { cls: 'serif' });
    quote(root, add, 's6', ['定太子', '在{君侯|#b9ad93}与高之{口|#f0c56a}耳'], { x: 96, w: 888, y: 580, size: 62, lh: 1.45, align: 'left', from: hi + d6 * .34, dur: 2.0, until: S('s7') - .1, color: '#e9dfc8' });
    quote(root, add, 's6', ['{安得亡国之言！|#f0c56a}', '此非人臣所当议也'], { x: 96, w: 888, y: 820, size: 62, lh: 1.45, align: 'right', from: hi + d6 * .74, dur: 1.4, until: S('s7') - .1, color: '#e9dfc8' });
    label(root, add, '君侯：对丞相李斯的尊称', 'left:96px;top:770px;font-size:26px;color:#8f8369', hi + d6 * .5, S('s7') - .1);

    /* —— 五问 —— */
    const Q = [['s8', '君侯自料能', '论才能，你比得上蒙恬吗'], ['s9', '功高', '论功劳'], ['s10', '谋远不失', '论谋略：想得远、不失算'], ['s11', '无怨于天下', '论人缘：天下没人怨你'], ['s12', '长子旧而信之', '论扶苏的信任：与他有旧交、被他信得过']];
    const num = ['一', '二', '三', '四', '五'];
    const qEnd = E('s18') + 1.4;
    label(root, add, '赵高五问', 'left:96px;top:476px;font-size:34px;font-weight:700;letter-spacing:.4em;color:#c9a45c', S('s7') + .2, qEnd, { cls: 'serif' });
    const rows = Q.map(([id, q, g], i) => {
      const y = 556 + i * 128;
      const row = el(root, 'abs', `left:96px;top:${y}px;width:900px;height:120px;opacity:0`);
      el(row, 'abs serif', 'left:0;top:14px;font-size:34px;font-weight:700;color:#c9a45c', num[i]);
      const tb = typeBlock(row, [`${q}{孰与蒙恬？|#b9ad93}`], { x: 58, y: 0, w: 760, size: 58, lh: 1.25, align: 'left', ls: '.02em' });
      const gl = el(row, 'abs sans', 'left:60px;top:78px;font-size:27px;color:#9c9075;letter-spacing:.04em;white-space:nowrap', g);
      const st = stamp(root, add, '不及', 818, y + 2, S('s15') + .25 + i * .34, qEnd, { size: 52, rot: -6 + (i % 2) * 4, bw: 4 });
      add(t => {
        const v = t < S(id) - .1 ? 0 : (1 - ramp(t, qEnd - .5, qEnd)); const dimmed = ramp(t, S('s16') + 2.2, S('s16') + 3.0);
        row.style.opacity = v * lerp(1, .13, dimmed); st.style.filter = `url(#inkbleed) opacity(${lerp(1, .22, dimmed)})`;
        if (v > 0) { tb.reveal(ramp(t, S(id) - .1, S(id) + dur(id) * .75)); tb.style.opacity = 1; gl.style.opacity = ramp(t, S(id) + dur(id) * .7, S(id) + dur(id) + .2); }
      });
      return row;
    });
    term(root, add, '蒙恬', '扶苏身边的大将<br><span style="color:#9c9075">将兵三十万，屯守上郡</span>', 96, 1212, S('s7') + dur('s7') * .4, S('s9') - .1, { size: 54, w: 560 });
    /* 没有一个传到第二代 */
    quote(root, add, 's16', ['未尝见秦免罢丞相功臣', '有{封及二世|#f0c56a}者也', '{卒皆以诛亡|#d2382c}'], { y: 600, size: 70, lh: 1.6, from: S('s16') + 2.6, dur: 4.2, until: qEnd, cite: CITE87, gloss: '免罢：罢免　｜　封及二世：爵位传到下一代　｜　卒：最终', glossAt: S('s16') + 5.5 });
    label(root, add, '「长子……即位必用<span style="color:#f0c56a">蒙恬为丞相</span>」', 'left:0;right:0;top:1130px;text-align:center;font-size:42px;font-weight:700;color:#d8ccb2;letter-spacing:.06em', S('s18') + .2, qEnd, { cls: 'serif' });

    /* —— 静默之后：三次推辞 —— */
    const r0 = S('s19'), dr = dur('s19');
    label(root, add, '李斯', 'right:96px;top:486px;font-size:40px;font-weight:900;letter-spacing:.2em;color:#c9a45c;border-bottom:2px solid #c9a45c;padding-bottom:6px', r0 - .2, S('s20') - .2, { cls: 'serif' });
    [['斯奉主之诏，听天之命', '讲天命'], ['忠臣不避死……孝子不勤劳而见危', '讲忠孝'], ['三者逆天，宗庙不血食', '讲前车之鉴']].forEach(([q, g], i) => {
      const t0 = r0 + .3 + i * (dr * .11);
      const d = label(root, add, `「${q}」<span style="font-family:Noto Sans SC;font-weight:400;font-size:26px;color:#8f8369;margin-left:14px">${g}</span>`, `right:96px;top:${580 + i * 74}px;font-size:${i === 1 ? 37 : 40}px;font-weight:700;color:#d8ccb2;white-space:nowrap`, t0, S('s20') - .2, { cls: 'serif' });
      add(t => { if (t > r0 + dr * .42) d.style.opacity = Math.min(+d.style.opacity, lerp(1, .3, ramp(t, r0 + dr * .42, r0 + dr * .52))); });
    });
    label(root, add, '赵高', 'left:96px;top:830px;font-size:40px;font-weight:900;letter-spacing:.2em;color:#c9a45c;border-bottom:2px solid #c9a45c;padding-bottom:6px', r0 + dr * .42, S('s20') - .2, { cls: 'serif' });
    label(root, add, '听　<span style="color:#f0c56a">长有封侯，世世称孤</span>', 'left:96px;top:930px;font-size:60px;font-weight:900;color:#e9dfc8;letter-spacing:.04em', r0 + dr * .66, S('s20') - .2, { cls: 'serif', rise: 12 });
    label(root, add, '不听　<span style="color:#d2382c">祸及子孙</span>', 'left:96px;top:1040px;font-size:60px;font-weight:900;color:#e9dfc8;letter-spacing:.04em', r0 + dr * .84, S('s20') - .2, { cls: 'serif', rise: 12 });
    label(root, add, '称孤：封侯者自称', 'left:96px;top:1150px;font-size:26px;color:#8f8369', r0 + dr * .74, S('s20') - .2);
    /* 垂泪 */
    quote(root, add, 's20', ['斯乃仰天而叹', '{垂泪太息|#f0c56a}'], { y: 600, size: 96, lh: 1.5, until: S('s22') - .2, cite: CITE87 });
    label(root, add, '于是斯乃<span style="color:#d2382c">听高</span>', 'left:0;right:0;top:1010px;text-align:center;font-size:66px;font-weight:900;letter-spacing:.2em;text-indent:.2em;color:#e9dfc8', S('s21') + .1, S('s22') - .2, { cls: 'serif', rise: 12 });
    /* 这说明什么 */
    const z = S('s22'), dz = dur('s22');
    const no = label(root, add, '该不该？', 'left:0;right:0;top:600px;text-align:center;font-size:96px;font-weight:900;letter-spacing:.14em;text-indent:.14em;color:#6e634e', z + .2, b + .3, { cls: 'serif' });
    const strike = el(root, 'abs', 'left:310px;top:668px;width:460px;height:6px;background:#8f8369;transform-origin:0 50%;transform:scaleX(0)');
    label(root, add, '失了势的丞相，<span style="color:#d2382c">没有任何东西</span>能保他', 'left:0;right:0;top:1120px;text-align:center;font-size:48px;font-weight:900;letter-spacing:.06em;color:#e9dfc8', z + dz * .64, b + .3, { cls: 'serif', rise: 12 });
    label(root, add, '待不待得住？', 'left:0;right:0;top:800px;text-align:center;font-size:124px;font-weight:900;letter-spacing:.1em;text-indent:.1em;color:#f0c56a', z + dz * .36, b + .3, { cls: 'serif', rise: 18 });
    label(root, add, '赵高问的，从头到尾只有后一个', 'left:0;right:0;top:1010px;text-align:center;font-size:34px;letter-spacing:.2em;color:#9c9075', z + dz * .46, b + .3);

    add(t => {
      /* 车窗灯火微微闪烁；静默时推近 */
      win.setAttribute('opacity', .78 + .14 * Math.sin(t * 5.3) * Math.sin(t * 1.7) + .06 * Math.sin(t * 13));
      const sil = vis(t, E('s18') + 1.2, S('s19') + .2, 1.0, .8);
      const v = Math.max(ramp(t, hi - .2, hi + .8) * (1 - sil), 0);
      veil.style.opacity = v * .9;
      const push = lerp(1, 1.06, ramp(t, a, hi)) + .05 * eio(ramp(t, E('s18') + 1, S('s19')));
      car.style.transform = `scale(${push})`;
      desk.style.opacity = vis(t, S('s2') + .1, S('s5') - .2, .7, .5);
      const mv = vis(t, S('s5') + .3, hi, .8, .6); men.style.opacity = mv; men.style.left = lerp(-120, 30, eo(ramp(t, S('s5') + .3, S('s5') + 3.2))) + 'px';
      strike.style.transform = `scaleX(${eo(ramp(t, z + dz * .14, z + dz * .14 + .5))})`; strike.style.opacity = vis(t, z + dz * .14, b + .3, .1, .4);
    });
  });
})();
