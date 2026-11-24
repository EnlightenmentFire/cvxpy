// 场景 C：第二次认错（对内）/ 第三次认错（时间、模拟器、8 种）/ 结果 / 收尾
const pill = (x, y, w, h, label, o = {}) =>
  `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${o.r ?? 12}" fill="${o.bg || '#101512'}" stroke="${o.c || COL.line}" stroke-width="${o.sw || 2.5}"/>` +
  tx(x + w / 2, y + h / 2 + (o.fs || 34) * .36, o.fs || 34, label, { a: 'middle', w: o.w || 700, f: o.f || COL.ink });
const arrow = (x1, y1, x2, y2, c = '#5d6861', sw = 4) => {
  const a = Math.atan2(y2 - y1, x2 - x1), h = 14;
  return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${c}" stroke-width="${sw}" stroke-linecap="round"/>` +
    `<path d="M${x2} ${y2}L${f1(x2 - h * Math.cos(a - .5))} ${f1(y2 - h * Math.sin(a - .5))}M${x2} ${y2}L${f1(x2 - h * Math.cos(a + .5))} ${f1(y2 - h * Math.sin(a + .5))}" stroke="${c}" stroke-width="${sw}" stroke-linecap="round"/>`;
};
const figure = (x, y, c, o = 1) => `<g opacity="${f1(o * 100) / 100}"><circle cx="${x}" cy="${y}" r="11" fill="${c}"/><path d="M${x - 17} ${y + 46}c0 -24 7 -31 17 -31s17 7 17 31z" fill="${c}"/></g>`;

SCENES.inner = function (sc) {
  let s = BG();
  const lay = on('layoff', .7), chk = on('check', .6), so = on('so6', .6);
  s += G(win('inner', 'priem', .7), tx(540, 700, 76, '对外认错，难', { a: 'middle', w: 900, f: '#77827a' }) + tx(540, 880, 124, '对内，更难', { a: 'middle', w: 900, ls: 6 }));
  // 蓝图：NV2 架构
  const bp = on('priem', .8) * (1 - lay);
  if (bp > 0) {
    const sh = eio(prog('shelve', 1.2, .2));
    let d = `<rect x="110" y="440" width="860" height="470" rx="10" fill="#0c1512" stroke="#2d6b49" stroke-width="2.5"/>`;
    for (let i = 1; i < 12; i++) d += `<line x1="${110 + i * 71.6}" y1="440" x2="${f1(110 + i * 71.6)}" y2="910" stroke="#143024" stroke-width="1.5"/>`;
    for (let i = 1; i < 7; i++) d += `<line x1="110" y1="${f1(440 + i * 67)}" x2="970" y2="${f1(440 + i * 67)}" stroke="#143024" stroke-width="1.5"/>`;
    d += `<path d="M200 540h200v110h-200zM470 520h160v150h-160zM700 540h190v110h-190zM250 740h230v100h-230zM560 740h260v100h-260z" fill="none" stroke="${COL.g}" stroke-width="3" stroke-opacity=".8"/>` +
      `<path d="M400 595h70M630 595h70M365 650v90M690 650v90M480 790h80" stroke="${COL.g}" stroke-width="3" stroke-opacity=".6"/>`;
    d += mono(140, 486, 24, 'NV2 架构 · 四边形 / 正向纹理映射', { f: COL.g });
    d += mono(940, 890, 20, '设计：联合创始人、技术负责人 Curtis Priem', { a: 'end' });
    s += `<g opacity="${f1(bp * (1 - .7 * sh) * 100) / 100}" transform="translate(0 ${f1(sh * 120)}) rotate(${f1(-3 * sh)} 540 700)">${d}</g>`;
    s += G(eo(prog('shelve', .35, .9)) * bp, `<g transform="rotate(-10 540 700)"><rect x="350" y="690" width="380" height="130" rx="12" fill="none" stroke="${COL.warn}" stroke-width="8"/>` + tx(540, 790, 92, '放弃', { a: 'middle', w: 900, f: COL.warn, ls: 16 }) + `</g>`, 0);
    const sp = win('split', 'shelve');
    s += G(sp * eo(prog('split', .4, 1.6)), pill(72, 330, 440, 84, '普里姆：沿着它继续做', { fs: 32 }));
    s += G(sp * eo(prog('split', .4, 3.6)), pill(568, 330, 440, 84, '黄仁勋：顾客别再退货', { fs: 32, c: COL.gd, f: COL.g }));
    const st = win('shout', 'shelve');
    s += G(st, pill(110, 960, 330, 80, '关着门的争论', { fs: 32, f: COL.mute }) + arrow(460, 1000, 610, 1000, COL.warn, 5) + pill(630, 960, 340, 80, '当着员工的面', { fs: 32, c: COL.warn, f: COL.warn }));
    s += G(on('shelve', .6, 2.4) * bp, pill(120, 330, 840, 90, '掉头：做一块按微软规则来的芯片', { fs: 36, c: COL.g, f: COL.g }));
  }
  // 裁员：一百多个人影 → 四十个左右
  if (lay > 0 && so < 1) {
    const a = lay * (1 - so) * (1 - chk);
    const cols = 13, rows = 8, cut = eio(prog('layoff', 4.5, 1.2));
    let d = '';
    for (let i = 0; i < cols * rows; i++) {
      const c = i % cols, r = Math.floor(i / cols), order = rnd(i * 3.3 + 1);
      const keep = rnd(i * 7.7 + 2) < 0.395;       // 约 41 个留下（示意，不代表任何一个确切数字）
      const gone = !keep && order < cut * 1.02;
      d += figure(108 + c * 72, 432 + r * 66, gone ? '#1c241f' : (keep && cut > .98 ? COL.g : '#aab4ad'), gone ? .55 : 1);
    }
    s += O(a, d + tx(72, 372, 44, '一百多人', { w: 900 }) + O(cut, tx(1008, 372, 44, '剩下多少？', { a: 'end', w: 900, f: COL.g })));
    const n1 = on('n40', .5), n2 = on('n42', .5);
    const num = (x, n, unit, src, u, c) => G(u * (1 - so) * (1 - chk), tx(x, 1066, 84, n, { a: 'middle', w: 900, ff: 'Inter', f: c }) + tx(x, 1110, 28, unit, { a: 'middle', w: 500 }) + mono(x, 1146, 20, src, { a: 'middle' }));
    s += num(200, '≈40', '人', '《英伟达之道》· 转述', n1, COL.ink) + num(540, '35', '名工程师', 'Witt《The Thinking Machine》', eo(prog('n40', .5, 2.4)), COL.ink) + num(880, '42', '人 · 1996 年底', '英伟达上市文件（S-1）', n2, COL.g);
  }
  // 每周一张纸质支票
  if (chk > 0 && so < 1) {
    const a = chk * (1 - so);
    s += G(a, `<g transform="rotate(-4 540 700)"><rect x="150" y="520" width="780" height="340" rx="10" fill="#e9ede6" stroke="#aab4ad" stroke-width="3"/>` +
      `<rect x="150" y="520" width="780" height="54" fill="#cfd8cd"/>` + tx(186, 558, 26, 'PAYCHECK · 周薪支票（示意）', { f: '#31403a', ff: 'Plex, Noto Sans SC', w: 500 }) +
      `<path d="M190 650h420M190 720h600M190 800h260" stroke="#7c877f" stroke-width="3"/>` + tx(700, 812, 40, '本周', { f: '#1f7a4b', w: 900 }) +
      `<path d="M560 800q30 -40 60 0t60 0t60 0" fill="none" stroke="#31403a" stroke-width="3"/></g>` +
      tx(540, 400, 44, '每个工作周结束 · 当面 · 一张纸质支票', { a: 'middle', w: 900 }) +
      mono(540, 960, 22, '图形专家 David Kirk，1996 年到公司 · 据 Witt 的书', { a: 'middle' }));
  }
  if (so > 0) {
    s += G(eo(prog('so6', .5, .8)), tx(540, 600, 66, '认错，不是说一句话', { a: 'middle', w: 900, f: '#9aa49d' }));
    s += G(eo(prog('so6', .5, 2.6)), tx(540, 800, 84, '是放下自己人的心血', { a: 'middle', w: 900 }));
    s += G(eo(prog('so6', .5, 4.2)), tx(540, 950, 84, '送走一大半同事', { a: 'middle', w: 900, f: COL.g }));
  }
  return s;
};

SCENES.time = function (sc) {
  let s = BG();
  s += G(win('speed', 'tapeout', .6), tx(540, 560, 50, '规则是微软定的', { a: 'middle', w: 500, f: COL.mute }) + O(pc('speed', 1), tx(540, 720, 70, '在别人的规则里', { a: 'middle', w: 900 }) + tx(540, 820, 70, '能比的只剩一样', { a: 'middle', w: 900 })) +
    G(pc('speed', 2), glow(tx(540, 1040, 190, '谁快', { a: 'middle', w: 900, f: COL.g, ls: 24 })), 20));
  s += G(win('time', 'speed', .7), tx(540, 720, 54, '剩下的问题', { a: 'middle', w: 500, f: COL.mute }) + glow(tx(540, 900, 180, '时间', { a: 'middle', w: 900, f: COL.g, ls: 20 })));
  // ① 平常的流程：设计 → 流片 → 打样 → 找错 → 改 → 再流片…
  const fl = on('tapeout', .7) * (1 - on('emu', .5));
  if (fl > 0) {
    const N = [[540, 400, '设计'], [270, 600, '流片 · 送工厂'], [810, 600, '打样 · 等样片回来'], [810, 860, '装上试 · 找错'], [270, 860, '改']];
    const lp = on('loop', .5), lt = Math.max(0, T - C('loop') - 2.2), dead = on('toolate', .5, 1.6);
    const lap = lt / 2.6, k = lap % 1, seg = Math.floor(k * 4), su = (k * 4) % 1, laps = Math.min(3, Math.floor(lap));
    let d = arrow(470, 446, 330, 552) + O(lp, arrow(450, 600, 610, 600) + arrow(810, 650, 810, 806) + arrow(620, 860, 400, 860) + arrow(270, 810, 270, 654));
    N.forEach(([x, y, lab], i) => {
      const u = i < 2 ? on('tapeout', .4, i * 1.9) : lp * eo(prog('loop', .4, (i - 2) * 1.1));
      const hot = lp > .5 && dead < .5 && i >= 1 && ((seg + 1 - 1) % 4) + 1 === i;
      d += O(u, pill(x - 190, y - 46, 380, 92, lab, { fs: 34, c: hot ? COL.g : COL.line, f: hot ? COL.g : COL.ink, bg: hot ? '#0c1a12' : '#101512' }));
    });
    d += O(lp, tx(540, 742, 40, laps ? `已经 ${laps} 轮` : '一来一回', { a: 'middle', w: 900 }) + tx(540, 786, 28, '每一轮，按月算', { a: 'middle', w: 500, f: COL.mute }));
    // 现金条
    const cash = clamp(1 - lt / 9.5) * (1 - dead);
    d += O(lp, tx(72, 1010, 30, '公司的钱', { w: 500, f: COL.mute }) + `<rect x="72" y="1030" width="936" height="34" rx="8" fill="#141a17" stroke="${COL.line}" stroke-width="2"/>` +
      `<rect x="72" y="1030" width="${f1(936 * cash)}" height="34" rx="8" fill="${cash > .3 ? '#aab4ad' : COL.warn}"/>`);
    d += G(dead, `<g transform="rotate(-6 540 730)">` + pill(300, 650, 480, 150, '倒闭', { fs: 100, w: 900, c: COL.warn, f: COL.warn, bg: '#1c0f0b', sw: 6 }) + `</g>` + tx(540, 1130, 34, '错还没改完，钱先没了', { a: 'middle', f: COL.warn }), 0);
    s += O(fl, d);
  }
  // ② 模拟器
  const em = on('emu', .8) * (1 - on('queue', .5));
  if (em > 0) {
    let d = machine(110, 470, 290, 600, { pool: 1 });
    // 机器“肚子里”：那块还没造出来的芯片（虚线）
    const pr = on('pretend', .6);
    d += O(pr, `<rect x="180" y="760" width="150" height="150" rx="12" fill="#0c1a12" stroke="${COL.g}" stroke-width="3" stroke-dasharray="12 9"/>` + tx(255, 828, 26, '还没造', { a: 'middle', f: COL.g }) + tx(255, 862, 26, '出来的芯片', { a: 'middle', f: COL.g }));
    // 软件窗口，先在它上面跑
    const pu = clamp(0.05 + (T - C('pretend')) / 60);
    d += O(pr, `<path d="M400 800C470 800 470 700 540 700" fill="none" stroke="${COL.gd}" stroke-width="6" stroke-dasharray="4 10" stroke-dashoffset="${f1(-T * 30)}"/>` +
      `<rect x="540" y="520" width="440" height="360" rx="12" fill="#0d110f" stroke="#33413a" stroke-width="2.5"/><rect x="540" y="520" width="440" height="50" rx="12" fill="#18201b"/>` +
      mono(566, 554, 22, '软件 · 驱动程序', { f: '#b7c0ba' }) +
      `<clipPath id="swc"><rect x="560" y="590" width="400" height="${f1(270 * pu)}"/></clipPath><g clip-path="url(#swc)"><rect x="560" y="590" width="400" height="270" fill="#0b1a12"/>` +
      `<path d="M560 860L660 720L740 800L840 680L960 860Z" fill="#1f8f55"/><circle cx="880" cy="660" r="26" fill="#8dffb9"/></g>` +
      `<rect x="560" y="${f1(590 + 270 * pu - 2)}" width="400" height="3" fill="#b8ffd3" filter="url(#glow)"/>`);
    s += O(em, d);
    s += G(win('emu', 'pretend'), tx(540, 400, 84, '模拟器', { a: 'middle', w: 900 }), 0);
    s += G(win('pretend', '1m'), tx(540, 392, 46, '假装自己就是那块芯片', { a: 'middle', w: 900 }) + tx(540, 446, 30, '软件不用等，先在它上面跑', { a: 'middle', w: 500, f: COL.mute }), 0);
    const m1 = win('1m', 'room');
    s += G(m1, glow(tx(72, 420, 96, '约 $1,000,000', { w: 900, ff: 'Inter, Noto Sans SC', f: COL.g, ls: -2 })), 0);
    s += G(m1 * eo(prog('1m', .5, 2.0)), `<rect x="540" y="900" width="440" height="190" rx="12" fill="${COL.panel}" stroke="${COL.line}" stroke-width="2"/>` +
      mono(566, 942, 21, '占剩下现金的多少，说法不一') + tx(566, 996, 34, '三分之一', { w: 900 }) + mono(960, 994, 20, '《福布斯》2007', { a: 'end' }) +
      tx(566, 1054, 34, '“最后的钱”', { w: 900 }) + mono(960, 1052, 20, 'Witt 的书', { a: 'end' }));
    const rm = win('room', 'slow');
    s += G(rm, tx(540, 400, 46, '机房放不下，摆进休息室', { a: 'middle', w: 900 }), 0);
    s += G(rm * eo(prog('room', .4, 1.6)), pill(540, 920, 210, 84, '☀ 白天一班', { fs: 30 }) + pill(770, 920, 210, 84, '☾ 晚上一班', { fs: 30, c: COL.gd, f: COL.g }));
    const sl = win('slow', 'queue');
    s += G(sl, tx(540, 400, 76, '非常、非常慢', { a: 'middle', w: 900 }), 0);
    s += G(sl * eo(prog('slow', .5, 1.6)), `<rect x="540" y="900" width="440" height="190" rx="12" fill="${COL.panel}" stroke="${COL.line}" stroke-width="2"/>` +
      mono(566, 942, 21, '一帧画面要多久，说法不一') + tx(566, 996, 32, '约 30 秒', { w: 900 }) + mono(960, 994, 19, 'Acquired 2022 · 主持人', { a: 'end' }) +
      tx(566, 1054, 32, '约一小时', { w: 900 }) + mono(960, 1052, 19, '黄仁勋 2023 · 他本人', { a: 'end' }));
  }
  // ③ 排队干 vs 同时干
  const qp = on('queue', .7) * (1 - on('noproto', .5));
  if (qp > 0) {
    const par = on('parallel', .8), u = i => eo(prog('queue', .45, .7 + i * 1.5));
    const names = ['等芯片', '写软件', '找错'];
    let d = tx(72, 392, 44, '排队干', { w: 900, f: '#aab4ad' }) + mono(1008, 388, 22, '一件做完，才能做下一件', { a: 'end' });
    names.forEach((nm, i) => d += O(u(i), pill(72 + i * 312, 430, 300, 96, nm, { fs: 36, bg: '#141a17', c: '#3a433d' })));
    d += `<line x1="72" y1="560" x2="1008" y2="560" stroke="#3a433d" stroke-width="3"/>` + arrow(980, 560, 1008, 560, '#3a433d', 3) + mono(1008, 596, 22, '时间 →', { a: 'end' });
    d += O(par, tx(72, 740, 44, '同时干', { w: 900, f: COL.g }) + mono(1008, 736, 22, '芯片和软件，一起跑在模拟器上', { a: 'end', f: COL.g }) +
      names.map((nm, i) => pill(72, 778 + i * 104, 340, 90, i === 0 ? '芯片（在模拟器里）' : nm, { fs: i === 0 ? 30 : 36, bg: '#0c1a12', c: COL.g, f: COL.g })).join('') +
      `<line x1="412" y1="778" x2="412" y2="1076" stroke="${COL.g}" stroke-width="3" stroke-dasharray="8 8"/>` +
      O(on('buytime', .6), `<rect x="430" y="778" width="578" height="298" rx="12" fill="${COL.g}" opacity=".07"/>` +
        `<path d="M440 1100h558" stroke="${COL.g}" stroke-width="3"/><path d="M440 1088v24M998 1088v24" stroke="${COL.g}" stroke-width="3"/>` +
        glow(tx(719, 950, 76, '省下的时间', { a: 'middle', w: 900, f: COL.g })) + tx(719, 1166, 40, '拿钱，买时间', { a: 'middle', w: 900 })));
    s += O(qp, d);
  }
  // ④ 不打样，直接量产
  const np = on('noproto', .7) * (1 - on('back', .5));
  if (np > 0) {
    const x = eo(prog('noproto', .4, 1.5));
    let d = pill(72, 520, 250, 110, '设计', { fs: 44 }) + arrow(332, 575, 400, 575) + pill(410, 520, 260, 110, '样片', { fs: 44, f: '#77827a' }) + arrow(680, 575, 748, 575) + pill(758, 520, 250, 110, '量产', { fs: 44, c: COL.g, f: COL.g, bg: '#0c1a12' });
    d += O(x, `<path d="M420 530L660 620M660 530L420 620" stroke="${COL.warn}" stroke-width="9" stroke-linecap="round"/>` +
      `<path d="M197 640C300 800 780 800 883 640" fill="none" stroke="${COL.g}" stroke-width="5" stroke-dasharray="1" pathLength="1" stroke-dashoffset="${f1(1 - eio(prog('noproto', 1.0, 2.0)))}"/>`);
    d += tx(540, 410, 64, '不打样，直接量产', { a: 'middle', w: 900 });
    d += G(pc('q_perfect', 2, .6), glow(tx(540, 990, 110, '只有一次机会', { a: 'middle', w: 900, f: COL.g, ls: 6 })) + mono(540, 1050, 24, 'We get one shot.', { a: 'middle' }));
    d += G(win('ask2', 'q_perfect'), tx(540, 960, 52, '“你怎么知道它会是完美的？”', { a: 'middle', w: 700, f: '#b7c0ba' }));
    s += O(np, d);
  }
  // ⑤ 32 种，只支持 8 种
  const gr = on('back', .7), so = on('so7', .6);
  if (gr > 0 && so < 1) {
    const g32 = on('g32', .6), g8 = on('g8', .5), q24 = on('q_24', .5) * (1 - on('honest', .5)), hon = on('honest', .5);
    const LIT = [1, 4, 10, 13, 18, 23, 27, 30];
    let d = '';
    s += G(win('back', 'g32'), chip(540, 640, 130, '') + tx(540, 900, 64, '芯片做出来了', { a: 'middle', w: 900 }) + O(prog('back', .5, 1.4), tx(540, 980, 48, '它并不完美', { a: 'middle', w: 700, f: COL.warn })));
    for (let i = 0; i < 32; i++) {
      const c = i % 8, r = Math.floor(i / 8), u = eo(prog('g32', .3, .5 + i * .07)), lit = LIT.includes(i);
      const col = lit && g8 > 0 ? COL.g : '#27302B', dimmed = !lit && g8 > 0;
      d += O(u * (dimmed ? lerp(1, .45, g8) : 1), `<rect x="${92 + c * 114}" y="${470 + r * 114}" width="98" height="98" rx="12" fill="${lit && g8 > 0 ? '#12301f' : '#111513'}" stroke="${col}" stroke-width="3" ${lit && g8 > .5 ? 'filter="url(#glow)"' : ''}/>` +
        mono(92 + c * 114 + 49, 470 + r * 114 + 60, 28, String(i + 1).padStart(2, '0'), { a: 'middle', f: lit && g8 > 0 ? COL.g : '#5d6861' }));
    }
    s += O(g32 * (1 - so) * (1 - .88 * q24), d);
    s += G(g32 * (1 - g8) , tx(72, 400, 50, '混合模式：32 种', { w: 900 }) + mono(1008, 396, 22, '= 32 种“叠颜色”的办法', { a: 'end' }), 0);
    s += G(g8 * (1 - q24) * (1 - hon), tx(72, 400, 50, '这块芯片只支持', { w: 900 }) + glow(tx(1008, 410, 100, '8 种', { a: 'end', w: 900, f: COL.g })), 0);
    s += G(g8 * (1 - q24) * (1 - hon), mono(540, 990, 22, '32 和 8 这两个数出自 Acquired 主持人的提问，黄仁勋当场没有否认', { a: 'middle' }), 0);
    if (q24 > 0) s += G(q24, tx(540, 640, 110, '另外 24 种，', { a: 'middle', w: 900 }) + glow(tx(540, 810, 124, '没那么重要。', { a: 'middle', w: 900, f: COL.g })), 14);
    s += G(hon * (1 - so), tx(540, 392, 50, '不是计划好的', { a: 'middle', w: 900 }) + tx(540, 446, 32, '他知道得太晚了', { a: 'middle', w: 500, f: COL.mute }), 0);
    s += G(on('q_best', .5, 0.2) * (1 - so), tx(540, 1010, 44, '本该 32 种全做', { a: 'middle', w: 900, f: '#b7c0ba' }) + O(prog('q_best', .5, 3.2), tx(540, 1076, 44, '做出来这样，就把它用到最好', { a: 'middle', w: 900, f: COL.g })), 0);
  }
  if (so > 0) {
    s += G(eo(prog('so7', .5, .8)), tx(540, 560, 48, '第三次认错', { a: 'middle', w: 500, f: COL.mute }) + tx(540, 660, 72, '认自己做不到完美', { a: 'middle', w: 900 }));
    ['先到', '够用', '活下来'].forEach((w, i) => s += G(eo(prog('so7', .4, 3.6 + i * .62)), pill(100 + i * 300, 800, 280, 150, w, { fs: 70, w: 900, c: COL.g, f: COL.g, bg: '#0c1a12', sw: 4 })));
  }
  return s;
};

SCENES.result = function (sc) {
  let s = BG();
  const mil = on('million', .6), pf = on('profit', .6), yr = on('years', .7), so = on('so8', .6);
  const top = (1 - yr);
  s += G(win('riva', 'million', .7), chip(540, 640, 150, 'RIVA 128', { fs: 46 }) + tx(72, 400, 120, '1997', { w: 900, ff: 'Inter', ls: -2 }) +
    mono(540, 900, 24, '4 月发布 · 8 月开始出货', { a: 'middle', f: '#b7c0ba' }) + mono(540, 936, 20, '英伟达官方时间线 / 1999 年招股书', { a: 'middle' }));
  if (mil > 0 && top > 0) {
    const p = eio(prog('million', 3.2, .3)), n = Math.round(1000000 * p);
    let d = tx(72, 400, 40, 'RIVA 128 · 出货量', { w: 500, f: COL.mute });
    d += glow(tx(540, 640, 176, n.toLocaleString('en-US'), { a: 'middle', w: 900, ff: 'Inter', f: COL.g, ls: -5 }));
    d += tx(540, 720, 40, p >= 1 ? '片以上' : '片', { a: 'middle', w: 500 });
    for (let i = 0; i < 4; i++) { const u = clamp(p * 4 - i);
      d += `<rect x="${72 + i * 238}" y="790" width="222" height="26" rx="6" fill="#141a17" stroke="${COL.line}" stroke-width="2"/><rect x="${72 + i * 238}" y="790" width="${f1(222 * u)}" height="26" rx="6" fill="${COL.g}"/>` +
        mono(72 + i * 238 + 111, 852, 22, `第 ${i + 1} 个月`, { a: 'middle' }); }
    d += mono(540, 910, 20, '英伟达新闻稿 1998-01-12：出货四个月超过一百万片（发给板卡厂商的数量）', { a: 'middle' });
    d += G(pf, `<rect x="72" y="960" width="936" height="190" rx="16" fill="${COL.panel}" stroke="${COL.gd}" stroke-width="2"/><rect x="72" y="960" width="10" height="190" rx="4" fill="${COL.g}"/>` +
      mono(112, 1012, 24, '1997 年第四季度', { f: COL.g }) + tx(112, 1078, 52, '成立以来第一次单季盈利', { w: 900 }) + mono(112, 1122, 20, '净利约 142 万美元 · 1999 年招股书'));
    s += O(mil * top, d);
  }
  if (yr > 0 && so < 1) {
    const a = yr * (1 - so), q = on('q_30', .5);
    let d = '';
    for (let i = 0; i < 30; i++) { const c = i % 6, r = Math.floor(i / 6), u = eo(prog('years', .25, .4 + i * .08));
      d += O(u, `<rect x="${222 + c * 108}" y="${420 + r * 108}" width="92" height="92" rx="10" fill="#111513" stroke="${q > 0 ? COL.warn : COL.line}" stroke-width="2.5" stroke-opacity="${q > 0 ? .7 : 1}"/>` +
        mono(222 + c * 108 + 46, 420 + r * 108 + 58, 30, String(30 - i), { a: 'middle', f: q > 0 ? COL.warn : '#6f7a73' })); }
    s += O(a * (1 - .8 * q), d);
    s += G(q * (1 - so), tx(540, 660, 76, '我们公司，离倒闭', { a: 'middle', w: 900 }) + glow(tx(540, 860, 180, '只有 30 天', { a: 'middle', w: 900, f: COL.warn, ls: 4 })), 14);
  }
  if (so > 0) {
    s += G(eo(prog('so8', .5, 1.4)), tx(540, 680, 70, '活下来之后，他没讲胜利', { a: 'middle', w: 900, f: '#9aa49d' }));
    s += G(pc('so8', 1), tx(540, 800, 56, '他讲的，还是', { a: 'middle', w: 500, f: COL.mute }) + glow(tx(540, 930, 100, '公司随时会倒闭', { a: 'middle', w: 900, f: COL.g })));
  }
  return s;
};

SCENES.end = function (sc) {
  let s = BG('#070908', .45);
  const fin = on('not', .6), nx = on('next', .6);
  s += G(win('end', 'q_enemy', .6), tx(540, 760, 60, '很多年后，他这样回看', { a: 'middle', w: 500, f: COL.mute }));
  const qe = win('q_enemy', 'q_confront');
  s += G(qe, `<rect x="72" y="520" width="8" height="420" fill="${COL.g}"/>` + tx(120, 600, 64, '年轻时，很多事', { w: 900, f: '#9aa49d' }) + tx(120, 690, 64, '都做得很烂', { w: 900, f: '#9aa49d' }) +
    O(prog('q_enemy', .5, 2.6), tx(120, 810, 76, '我们熬过了自己', { w: 900 })) + O(prog('q_enemy', .5, 4.2), glow(tx(120, 920, 76, '我们是自己最大的敌人', { w: 900, f: COL.g }))));
  const qc = win('q_confront', 'not');
  s += G(qc, `<rect x="72" y="560" width="8" height="340" fill="${COL.g}"/>` + tx(120, 650, 84, '直面错误', { w: 900 }) + O(prog('q_confront', .5, 1.9), tx(120, 760, 84, '带着谦卑去求助', { w: 900 })) +
    O(prog('q_confront', .5, 3.3), glow(tx(120, 880, 84, '救了英伟达', { w: 900, f: COL.g }))));
  if (fin > 0 && nx < 1) {
    const a = fin * (1 - nx), st = eo(prog('not', .5, 1.5)), up = on('l1', .6), th3 = on('three', .5);
    s += G(a * (1 - up) * th3, tx(540, 520, 76, '是三次认错', { a: 'middle', w: 900 }) + ['对客户', '对自己人', '对完美'].map((w, i) => O(eo((T - CH('three', 1) - i * .75) / .4), pill(190, 600 + i * 170, 700, 130, w, { fs: 66, w: 900, c: COL.g, f: COL.g, bg: '#0c1a12', sw: 4 }))).join(''));
    s += G(a * (1 - th3), tx(540, 720, 60, '这不是一个', { a: 'middle', w: 500, f: COL.mute }) + tx(540, 860, 104, '咬牙坚持', { a: 'middle', w: 900, f: '#9aa49d' }) + tx(540, 980, 60, '的故事', { a: 'middle', w: 500, f: COL.mute }) +
      `<rect x="322" y="820" width="${f1(436 * st)}" height="8" fill="${COL.warn}"/>`);
    const rows = [['l1', '押对了方向，', '却押错了规则', COL.ink], ['l2', '认了错，', '把剩下的钱换成了时间', COL.ink], ['l3', '这一次，', '他向别人的标准低头', COL.ink], ['l4', '后来，', '他要让别人，向他的标准低头', COL.g]];
    rows.forEach(([cue, a1, a2, c], i) => {
      const u = on(cue, .6), y = 400 + i * 200, last = i === 3;
      s += G(a * u, mono(72, y, 24, String(i + 1).padStart(2, '0'), { f: last ? COL.g : '#5d6861' }) + `<rect x="120" y="${y - 10}" width="${f1(888 * u)}" height="2" fill="${last ? COL.g : COL.line}"/>` +
        tx(72, y + 70, 44, a1, { w: 500, f: last ? COL.g : COL.mute }) + (last ? glow(tx(72, y + 140, 62, a2, { w: 900, f: c })) : tx(72, y + 140, 62, a2, { w: 900, f: c })));
    });
  }
  if (nx > 0) {
    s += G(nx, mono(540, 640, 30, '黄仁勋的商业决断', { a: 'middle', f: COL.g, ls: 8 }) + tx(540, 860, 220, '02', { a: 'middle', w: 900, ff: 'Inter', f: '#1f2a24', ls: -6 }) +
      `<rect x="390" y="900" width="300" height="4" fill="${COL.g}" filter="url(#glow)"/>` + tx(540, 1010, 76, '下一期', { a: 'middle', w: 900, ls: 10 }) +
      tx(540, 1080, 34, '把自己变成别人得低头的那个标准', { a: 'middle', w: 500, f: COL.mute }));
  }
  return s;
};
