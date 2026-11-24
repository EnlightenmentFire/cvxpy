// 场景 B：规则（三角形 vs 四边形）/ 两难 / 第一次认错（世嘉）
// ─── 球体网格：同一个球，用三角形拼或用四边形拼
const CUBE_FACES = [
  [[1, 0, 0], [0, 1, 0], [0, 0, 1]], [[-1, 0, 0], [0, 0, 1], [0, 1, 0]],
  [[0, 1, 0], [0, 0, 1], [1, 0, 0]], [[0, -1, 0], [1, 0, 0], [0, 0, 1]],
  [[0, 0, 1], [1, 0, 0], [0, 1, 0]], [[0, 0, -1], [0, 1, 0], [1, 0, 0]],
];
function meshSphere(cx, cy, R, rot, mode, o = {}) {
  const n = 5, ex = o.explode || 0, col = o.c || [75, 245, 142], al = o.a ?? 1, tilt = 0.42;
  const cr = Math.cos(rot), sr = Math.sin(rot), ct = Math.cos(tilt), st = Math.sin(tilt);
  const P = (f, i, j) => {
    const [nn, a, b] = CUBE_FACES[f], u = Math.tan((i / n * 2 - 1) * Math.PI / 4), v = Math.tan((j / n * 2 - 1) * Math.PI / 4);
    let x = nn[0] + a[0] * u + b[0] * v, y = nn[1] + a[1] * u + b[1] * v, z = nn[2] + a[2] * u + b[2] * v;
    const l = Math.hypot(x, y, z); x /= l; y /= l; z /= l;
    const x1 = x * cr + z * sr, z1 = -x * sr + z * cr;
    return [x1, y * ct - z1 * st, y * st + z1 * ct];
  };
  let s = '';
  for (let f = 0; f < 6; f++) for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
    const q = [P(f, i, j), P(f, i + 1, j), P(f, i + 1, j + 1), P(f, i, j + 1)];
    const polys = mode === 'tri' ? ((i + j) % 2 ? [[q[0], q[1], q[2]], [q[0], q[2], q[3]]] : [[q[0], q[1], q[3]], [q[1], q[2], q[3]]]) : [q];
    polys.forEach((pl, k) => {
      const c = pl.reduce((m, p) => [m[0] + p[0] / pl.length, m[1] + p[1] / pl.length, m[2] + p[2] / pl.length], [0, 0, 0]);
      const cl = Math.hypot(...c), nz = c[2] / cl;
      if (nz < 0.02) return;
      const li = clamp(0.18 + 0.82 * Math.max(0, (-c[0] * .45 - c[1] * .55 + c[2] * .7) / cl));
      const sh = li * (mode === 'tri' && k ? .86 : 1);
      const e = ex * (0.6 + 0.8 * rnd(f * 100 + i * 10 + j + k * 7));
      const pts = pl.map(p => `${f1(cx + (p[0] + c[0] * e) * R)},${f1(cy - (p[1] + c[1] * e) * R)}`).join(' ');
      s += `<polygon points="${pts}" fill="rgb(${Math.round(col[0] * sh * .55)},${Math.round(col[1] * sh * .55)},${Math.round(col[2] * sh * .55)})" stroke="rgb(${col})" stroke-width="2" stroke-linejoin="round" stroke-opacity="${f1((0.35 + .65 * nz) * 100) / 100}"/>`;
    });
  }
  return O(al, s);
}
const mark = (x, y, r, ok) => ok
  ? `<circle cx="${x}" cy="${y}" r="${r}" fill="#0c1a12" stroke="${COL.g}" stroke-width="5"/><path d="M${x - r * .45} ${y}l${r * .32} ${r * .34}l${r * .6} -${r * .68}" fill="none" stroke="${COL.g}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>`
  : `<circle cx="${x}" cy="${y}" r="${r}" fill="#1c0f0b" stroke="${COL.warn}" stroke-width="5"/><path d="M${x - r * .4} ${y - r * .4}l${r * .8} ${r * .8}M${x + r * .4} ${y - r * .4}l-${r * .8} ${r * .8}" fill="none" stroke="${COL.warn}" stroke-width="8" stroke-linecap="round"/>`;

SCENES.rule = function (sc) {
  let s = BG();
  const sp = eio(prog('triquad', 1.3)), rot = T * 0.28;
  const only = on('onlytri', .6), fifty = on('fifty', .7), so = on('so3', .6);
  const sphA = (1 - fifty) * on('mesh', .8);
  s += G(win('rule', 'mesh', .7), tx(540, 720, 54, '更要命的是', { a: 'middle', w: 500, f: COL.mute }) + tx(540, 860, 116, '押错了规则', { a: 'middle', w: 900, f: COL.warn, ls: 6 }));
  if (sphA > 0) {
    const ex = 0.55 * (1 - eio(prog('mesh', 2.6, .3)));
    const cy = lerp(700, 610, sp), R = lerp(250, 200, sp);
    s += meshSphere(lerp(540, 285, sp), cy, R, rot, 'tri', { explode: ex, a: sphA });
    if (sp > 0) s += meshSphere(lerp(540, 795, sp), cy, R, rot, 'quad', { c: only > 0 ? [lerp(75, 150, only), lerp(245, 160, only), lerp(142, 152, only)] : [75, 245, 142], a: sphA * sp * (1 - .45 * only) });
    s += G(win('mesh', 'triquad'), tx(540, 392, 50, '拆成很多小块，再拼起来', { a: 'middle', w: 900 }), 0);
    const lb = sp * sphA;
    s += G(lb, tx(285, 892, 56, '三角形', { a: 'middle', w: 900, f: COL.g }) + tx(285, 942, 30, '同行大多用', { a: 'middle', w: 500, f: COL.mute }) +
      tx(795, 892, 56, '四边形', { a: 'middle', w: 900 }) + tx(795, 942, 30, '英伟达押的', { a: 'middle', w: 500, f: COL.mute }));
    s += O(only * sphA, mark(285, 610, 62, true) + mark(795, 610, 62, false));
  }
  // 公制 / 英制
  const mt = win('metric', 'directx');
  if (mt > 0) {
    let r = '';
    for (let i = 0; i <= 20; i++) r += `<line x1="${92 + i * 19}" y1="1020" x2="${92 + i * 19}" y2="${i % 5 ? 1040 : 1056}" stroke="${COL.g}" stroke-width="3"/>`;
    for (let i = 0; i <= 12; i++) r += `<line x1="${604 + i * 31.7}" y1="1020" x2="${f1(604 + i * 31.7)}" y2="${i % 4 ? 1040 : 1056}" stroke="#aab4ad" stroke-width="3"/>`;
    s += G(mt, `<rect x="80" y="1010" width="404" height="70" rx="8" fill="#0f1612" stroke="${COL.gd}" stroke-width="2"/><rect x="592" y="1010" width="404" height="70" rx="8" fill="#141816" stroke="#3a433d" stroke-width="2"/>` + r +
      tx(285, 1130, 34, '大家：公制', { a: 'middle', f: COL.g }) + tx(795, 1130, 34, '你：英制', { a: 'middle' }));
  }
  // 规则书：DirectX
  const dx = win('directx', 'fifty');
  if (dx > 0) {
    s += G(dx, `<rect x="72" y="990" width="936" height="190" rx="16" fill="${COL.panel}" stroke="${COL.gd}" stroke-width="2"/>` +
      `<rect x="72" y="990" width="10" height="190" rx="4" fill="${COL.g}"/>` +
      tx(112, 1058, 56, 'DirectX', { w: 900, ff: 'Inter' }) + tx(350, 1054, 32, '微软定的“画画规则”', { w: 500, f: COL.mute }) +
      O(1 - only, mono(112, 1112, 22, 'Windows 95 之后 → 1995-09 DirectX 1.0 → 1996-06 加入 3D 部分') + mono(112, 1146, 20, '日期据 Wikipedia “DirectX” 条目', { f: '#5d6861' })) +
      O(only, glow(tx(112, 1140, 60, '只认三角形', { w: 900, f: COL.g, ls: 4 })) + tx(1000 - 20, 1136, 34, '不按它来，游戏跑不了', { a: 'end', w: 500, f: COL.warn })));
  }
  // 约 50 家 vs 1 家
  if (fifty > 0 && so < 1) {
    const a = fifty * (1 - so);
    let d = `<circle cx="470" cy="720" r="330" fill="#0c1410" stroke="${COL.gd}" stroke-width="3" stroke-dasharray="10 10"/>`;
    for (let i = 0; i < 50; i++) { const ang = i * 2.39996, rr = 300 * Math.sqrt((i + .5) / 50), u = eo(prog('fifty', .4, .3 + i * .03));
      d += `<circle cx="${f1(470 + Math.cos(ang) * rr)}" cy="${f1(720 + Math.sin(ang) * rr)}" r="${f1(13 * u)}" fill="${COL.g}" opacity=".85"/>`; }
    const lone = eo(prog('fifty', .6, 3.6));
    d += tx(470, 372, 34, 'DirectX 规则之内 · 约 50 家', { a: 'middle', f: COL.g });
    d += O(lone, `<circle cx="930" cy="1030" r="16" fill="${COL.ink}" filter="url(#glow)"/>` + tx(930, 1090, 34, '英伟达', { a: 'middle', w: 900 }) + mono(930, 1126, 22, '在外面', { a: 'middle' }));
    s += O(a, d);
  }
  if (so > 0) {
    s += SO('so3');
    s += G(eo(prog('so3', .5, .9)), tx(540, 640, 76, '平台一旦定了标准', { a: 'middle', w: 900, f: COL.g }));
    s += G(eo(prog('so3', .5, 2.5)), tx(540, 800, 60, '一家小公司', { a: 'middle', w: 500, f: COL.mute }) + tx(540, 920, 84, '再聪明，也扛不住', { a: 'middle', w: 900 }));
  }
  return s;
};

// ─── 两难
function roads(pA, pB, hot) {
  const A = 'M540 1160C540 1000 520 960 440 900C330 820 200 820 205 700C210 620 290 600 290 530';
  const B = 'M540 1160C540 1000 560 960 650 920C740 880 800 860 830 790';
  const dash = p => `pathLength="1" stroke-dasharray="1" stroke-dashoffset="${f1((1 - p) * 1000) / 1000}"`;
  let s = `<path d="M540 1190V1160" stroke="#2a332d" stroke-width="56" stroke-linecap="round"/>`;
  s += `<path d="${A}" fill="none" stroke="#1b221e" stroke-width="56" stroke-linecap="round"/><path d="${B}" fill="none" stroke="#1b221e" stroke-width="56" stroke-linecap="round"/>`;
  s += `<path d="${A}" fill="none" stroke="#e8ede9" stroke-width="4" stroke-dasharray="0.02 0.02" pathLength="1" opacity=".18"/><path d="${B}" fill="none" stroke="#e8ede9" stroke-width="4" stroke-dasharray="0.03 0.03" pathLength="1" opacity=".18"/>`;
  s += `<path d="${A}" fill="none" stroke="${COL.warn}" stroke-width="8" stroke-linecap="round" ${dash(pA)} opacity=".9"/>`;
  s += `<path d="${B}" fill="none" stroke="${COL.warn}" stroke-width="8" stroke-linecap="round" ${dash(pB)} opacity=".9"/>`;
  const end = (x, y, u, t1, t2, when, anchor) => O(u,
    `<circle cx="${x}" cy="${y}" r="${46 + 8 * hot * Math.sin(T * 3)}" fill="#1c0f0b" stroke="${COL.warn}" stroke-width="5" ${hot ? 'filter="url(#glow)"' : ''}/>` +
    tx(x, y + 14, 38, '倒闭', { a: 'middle', w: 900, f: COL.warn }) +
    tx(anchor === 'start' ? x + 70 : x - 70, y - 12, 38, t1, { a: anchor, w: 900 }) + tx(anchor === 'start' ? x + 70 : x - 70, y + 34, 30, t2, { a: anchor, w: 500, f: COL.mute }) +
    `<rect x="${x - 70}" y="${y - 132}" width="140" height="50" rx="25" fill="${COL.warn}"/>` + tx(x, y - 96, 30, when, { a: 'middle', w: 900, f: '#170a06' }));
  s += end(290, 530, eo((pA - .92) / .08), '做完它', '越走越远，追不上', '晚一点', 'start');
  s += end(830, 790, eo((pB - .9) / .1), '', '', '马上', 'end');
  s += O(eo((pB - .9) / .1), tx(1008, 900, 38, '不做完', { a: 'end', w: 900 }) + tx(1008, 946, 30, '马上没钱', { a: 'end', w: 500, f: COL.mute }));
  return s;
}
SCENES.dilemma = function (sc) {
  let s = BG('#080a09', .4);
  const hush = on('hush', .9, .9) * (1 - on('both', .7));
  const pA = eio(prog('pathA', 3.2, .2)), pB = eio(prog('pathB', 1.4, .1));
  s += roads(pA, pB, on('both', .5));
  // 合同
  const ct = win('contract', 'pathA');
  s += G(ct, `<rect x="72" y="330" width="936" height="210" rx="16" fill="${COL.panel}" stroke="${COL.line}" stroke-width="2"/>` +
    mono(108, 386, 24, '手里的合同', { f: COL.g }) + tx(108, 452, 48, '给世嘉的下一代游戏机做芯片', { w: 900 }) +
    tx(108, 508, 32, 'NV2 · 用的还是四边形那一套', { w: 500, f: COL.mute }));
    if (hush > 0) {
    s += DIM(hush * .95);
    const l = CUE.q_die, u = (T - l.start) / (l.end - l.start);
    s += G(eo((T - l.start) / .5) * hush, tx(540, 700, 88, '做完这个项目，', { a: 'middle', w: 900 }) + tx(540, 820, 108, '会死。', { a: 'middle', w: 900, f: COL.warn }), 16);
    s += G(eo((u - .5) / .14) * hush, tx(540, 990, 88, '不做完，', { a: 'middle', w: 900 }) + glow(tx(540, 1110, 108, '马上就死。', { a: 'middle', w: 900, f: COL.warn })), 16);
  }
  s += G(on('both', .6, .5), tx(1008, 400, 52, '两条路', { a: 'end', w: 500, f: COL.mute }) + tx(1008, 480, 64, '尽头都是倒闭', { a: 'end', w: 900 }) + tx(1008, 540, 34, '区别只是早一点，晚一点', { a: 'end', w: 500, f: COL.mute }), 0);
  return s;
};

// ─── 第一次认错：世嘉
function chair(x, dir) {    // 侧面的椅子
  return `<g transform="translate(${x} 0) scale(${dir} 1)"><rect x="-70" y="700" width="18" height="250" rx="8" fill="#1a211d" stroke="#33413a" stroke-width="2.5"/>` +
    `<rect x="-70" y="930" width="170" height="20" rx="8" fill="#1a211d" stroke="#33413a" stroke-width="2.5"/>` +
    `<path d="M-60 950L-74 1100M90 950L104 1100" stroke="#2a342e" stroke-width="12" stroke-linecap="round"/></g>`;
}
const VERS = [
  ['v1', '黄仁勋 · 2025', ['他请对方把最后这 500 万，', '改成对英伟达的投资'], '2025-12 播客访谈 · GameSpot 2025-12-05 转述'],
  ['v2', '入交昭一郎 · 2026', ['他说服总部：用剩下的开发费', '买英伟达股票，当作“分手礼物”'], '时事通讯社 ·《日本时报》2026-09-12 刊'],
  ['v3', '世嘉公司 · 2026', ['批过约 500 万美元（1995 或 96 年）；', '确切记录已不可得，未说明性质'], 'Inc. 2026-07-21'],
  ['v4', '英伟达招股书 · 1999', ['1995-07 合作方以 500 万美元买入优先股；', '开发款另付：95 年 200 万，96 年 300 万'], 'SEC 424B4 · 文件只写“第三方”，未点名'],
];
SCENES.sega = function (sc) {
  let s = BG('#090b0a', .4);
  const ver = on('versions', .7), so = on('so5', .6);
  s += G(win('third', 'table', .7), tx(540, 720, 54, '他选了第三条路', { a: 'middle', w: 500, f: COL.mute }) + glow(tx(540, 880, 150, '去认错', { a: 'middle', w: 900, f: COL.g, ls: 8 })));
  // 两把椅子、一张桌子、一份合同
  const ta = on('table', .9) * (1 - ver);
  if (ta > 0) {
    let d = `<path d="M400 520L250 1100H830L680 520Z" fill="url(#lamp)" opacity=".8"/>`;
    d += `<line x1="540" y1="-100" x2="540" y2="476" stroke="#262f2a" stroke-width="4"/><path d="M480 520L506 476H574L600 520Z" fill="#1c2420" stroke="#33413a" stroke-width="2"/>`;
    d += chair(250, 1) + chair(830, -1);
    d += `<rect x="360" y="900" width="360" height="22" rx="6" fill="#222b26" stroke="#3a4840" stroke-width="2"/><path d="M400 922L384 1100M680 922L696 1100" stroke="#232c27" stroke-width="12" stroke-linecap="round"/>`;
    d += `<g transform="translate(540 886) skewX(-24)"><rect x="-62" y="-12" width="124" height="16" fill="#dfe6e0"/><path d="M-48 -6h60M-48 -1h84" stroke="#7c877f" stroke-width="2"/></g>`;
    d += `<line x1="-40" y1="1100" x2="1120" y2="1100" stroke="#1d2520" stroke-width="2"/>`;
    d += mono(250, 1150, 24, '黄仁勋 · 英伟达', { a: 'middle', f: '#9aa49d' }) + mono(830, 1150, 24, '入交昭一郎 · 世嘉', { a: 'middle', f: '#9aa49d' });
    s += O(ta, d);
    // 坦白的三句话
    const cf = win('confess', 'ask');
    ['英伟达的路线错了', '这块芯片做不完', '世嘉应该另找伙伴'].forEach((w, i) => {
      s += G(cf * eo(prog('confess', .4, .5 + i * 1.5)), `<rect x="210" y="${334 + i * 78}" width="660" height="62" rx="10" fill="#101512" stroke="${COL.line}" stroke-width="2"/>` + tx(540, 378 + i * 78, 36, w, { a: 'middle', w: 700 }));
    });
    // 解约 / 照付
    const ak = win('ask', 'agree');
    s += G(ak * eo(prog('ask', .4, 2.6)), `<rect x="150" y="350" width="350" height="150" rx="14" fill="#0f1411" stroke="#aab4ad" stroke-width="3"/>` + tx(325, 452, 84, '解约', { a: 'middle', w: 900 }));
    s += G(ak * eo(prog('ask', .4, 3.7)), `<rect x="580" y="350" width="350" height="150" rx="14" fill="#0c1a12" stroke="${COL.g}" stroke-width="3" filter="url(#glow)"/>` + tx(755, 452, 84, '照付', { a: 'middle', w: 900, f: COL.g }));
    s += G(win('agree', '5m'), tx(540, 392, 44, '考虑了两天', { a: 'middle', w: 500, f: COL.mute }) + tx(540, 478, 68, '“我愿意帮你”', { a: 'middle', w: 900 }), 0);
    const m5 = win('5m', 'versions');
    s += G(m5, glow(tx(540, 430, 110, '约 500 万美元', { a: 'middle', w: 900, f: COL.g })) + O(prog('5m', .5, 1.8), tx(540, 506, 40, '“六个月的命”', { a: 'middle', w: 700 })), 0);
  }
  // 几方说法并列
  if (ver > 0 && so < 1) {
    const a = ver * (1 - so);
    s += O(a, tx(72, 372, 40, '这笔钱算什么？', { w: 900 }) + mono(1008, 368, 22, '几方说法并列，不替他们统一', { a: 'end' }));
    VERS.forEach(([cue, who, lines, src], i) => {
      const y = 410 + i * 196, u = on(cue, .5), act = clamp(u) * (i < 3 ? 1 - on(VERS[i + 1][0], .5) * .55 : 1);
      s += G(a * u, `<rect x="72" y="${y}" width="936" height="180" rx="14" fill="${COL.panel}" stroke="${act > .6 ? COL.gd : COL.line}" stroke-width="2"/>` +
        `<rect x="72" y="${y}" width="8" height="180" rx="4" fill="${COL.g}" opacity="${f1((.3 + .7 * act) * 100) / 100}"/>` +
        tx(108, y + 50, 32, who, { w: 900, f: COL.g }) + tx(108, y + 96, 31, lines[0], { w: 500 }) + tx(108, y + 136, 31, lines[1], { w: 500 }) +
        mono(1000 - 16, y + 50, 19, src, { a: 'end', f: '#6f7a73' }));
    });
  }
  if (so > 0) {
    s += SO('so5');
    s += G(pc('so5', 1), tx(540, 600, 60, '对方押的', { a: 'middle', w: 500, f: COL.mute }) + tx(540, 730, 100, '不是芯片，是人', { a: 'middle', w: 900 }));
    s += G(pc('so5', 2), tx(540, 900, 54, '坦白', { a: 'middle', w: 500, f: COL.mute }) + glow(tx(540, 1030, 96, '成了唯一的筹码', { a: 'middle', w: 900, f: COL.g })));
  }
  return s;
};
