// 场景 A：冷开场 / 标题 / 餐馆 / 章鱼
// ─── 通用图形
function machine(x, y, w, h, o = {}) {           // 冰箱大小的模拟器（示意图）
  let s = `<ellipse cx="${x + w / 2}" cy="${y + h + 6}" rx="${w * 1.25}" ry="60" fill="url(#gpool)" opacity="${f1((o.pool ?? 1) * (0.8 + 0.2 * Math.sin(T * 1.7)) * 100) / 100}"/>`;
  s += `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="8" fill="#0e1210" stroke="#2c3832" stroke-width="2.5"/>`;
  s += `<rect x="${x + 14}" y="${y + 14}" width="${w - 28}" height="${h * .34}" rx="4" fill="#090c0a" stroke="#222b26" stroke-width="2"/>`;
  const cols = 9, rows = 7, gx = (w - 60) / (cols - 1), gy = (h * .34 - 44) / (rows - 1);
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const k = r * 31 + c * 7, ph = Math.floor(T * (2 + rnd(k) * 5) + rnd(k + 5) * 9);
    const lit = rnd(k * 3 + ph) > 0.55;
    s += `<circle cx="${f1(x + 30 + c * gx)}" cy="${f1(y + 36 + r * gy)}" r="4.2" fill="${lit ? COL.g : '#143122'}" ${lit ? 'filter="url(#glow)"' : ''} opacity="${lit ? 1 : .8}"/>`;
  }
  for (let i = 0; i < 9; i++) s += `<rect x="${x + 22}" y="${f1(y + h * .42 + i * (h * .05))}" width="${w - 44}" height="5" rx="2" fill="#1a221d"/>`;
  s += `<rect x="${x + 22}" y="${y + h - 64}" width="${w * .36}" height="34" rx="3" fill="#0a0d0b" stroke="#222b26" stroke-width="2"/>`;
  s += `<circle cx="${x + w - 40}" cy="${y + h - 47}" r="7" fill="${COL.g}" filter="url(#glow)" opacity="${0.6 + 0.4 * Math.sin(T * 3)}"/>`;
  s += `<rect x="${x + 6}" y="${y + h}" width="22" height="8" fill="#1c241f"/><rect x="${x + w - 28}" y="${y + h}" width="22" height="8" fill="#1c241f"/>`;
  return s;
}
function crt(x, y, w, h, p) {                     // 老式显示器，画面自上而下一行行刷出来
  const sx = x + 22, sy = y + 20, sw = w - 44, sh = h - 62, ph = sh * clamp(p);
  let s = `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="14" fill="#151a17" stroke="#2c3832" stroke-width="2.5"/>`;
  s += `<rect x="${sx}" y="${sy}" width="${sw}" height="${sh}" rx="8" fill="#050706"/>`;
  s += `<clipPath id="crtc"><rect x="${sx}" y="${sy}" width="${sw}" height="${f1(ph)}"/></clipPath><g clip-path="url(#crtc)">`;
  s += `<rect x="${sx}" y="${sy}" width="${sw}" height="${sh}" fill="#0b1a12"/>`;
  const hz = sy + sh * .56;
  for (let i = 0; i <= 10; i++) { const u = i / 10; s += `<line x1="${sx + sw * .5}" y1="${hz}" x2="${f1(sx + sw * (u * 2.2 - .6))}" y2="${sy + sh}" stroke="#1d6b41" stroke-width="1.5"/>`; }
  for (let i = 1; i <= 5; i++) { const yy = hz + (sh * .44) * Math.pow(i / 5, 1.8); s += `<line x1="${sx}" y1="${f1(yy)}" x2="${sx + sw}" y2="${f1(yy)}" stroke="#1d6b41" stroke-width="1.5"/>`; }
  s += `<circle cx="${sx + sw * .36}" cy="${sy + sh * .46}" r="${sh * .24}" fill="#2fbf71"/><circle cx="${sx + sw * .31}" cy="${sy + sh * .40}" r="${sh * .10}" fill="#8dffb9" opacity=".7"/>`;
  s += `<path d="M${sx + sw * .62} ${sy + sh * .72}L${sx + sw * .76} ${sy + sh * .30}L${sx + sw * .9} ${sy + sh * .72}Z" fill="#1f8f55"/><path d="M${sx + sw * .76} ${sy + sh * .30}L${sx + sw * .9} ${sy + sh * .72}L${sx + sw * .82} ${sy + sh * .78}Z" fill="#14603a"/>`;
  s += `</g>`;
  if (p < 1) s += `<rect x="${sx}" y="${f1(sy + ph - 3)}" width="${sw}" height="4" fill="#b8ffd3" filter="url(#glow)"/>`;
  s += `<rect x="${sx}" y="${sy}" width="${sw}" height="${sh}" rx="8" fill="none" stroke="#0b0e0c" stroke-width="3"/>`;
  s += `<circle cx="${x + w - 34}" cy="${y + h - 22}" r="5" fill="${COL.g}" filter="url(#glow)"/><rect x="${x + 30}" y="${y + h - 26}" width="60" height="6" rx="3" fill="#232b26"/>`;
  s += `<path d="M${x + w * .35} ${y + h}h${w * .3}l14 22h-${w * .3 + 28}z" fill="#101412" stroke="#2c3832" stroke-width="2"/>`;
  return s;
}
function person(cx, y, sc = 1, fill = '#0b0e0c', stroke = '#26342c') {   // 坐着的人影（上半身）
  return `<g transform="translate(${cx} ${y}) scale(${sc})"><circle cx="0" cy="0" r="46" fill="${fill}" stroke="${stroke}" stroke-width="2.5"/>` +
    `<path d="M-84 230C-84 110 -52 62 0 62C52 62 84 110 84 230Z" fill="${fill}" stroke="${stroke}" stroke-width="2.5"/></g>`;
}
function chip(cx, cy, r, label, o = {}) {         // 芯片示意
  const c = o.c || COL.g; let s = '';
  for (let i = 0; i < 6; i++) { const d = -r + 2 * r * (i + .5) / 6;
    s += `<rect x="${cx + d - 4}" y="${cy - r - 16}" width="8" height="16" fill="#39453e"/><rect x="${cx + d - 4}" y="${cy + r}" width="8" height="16" fill="#39453e"/>`;
    s += `<rect x="${cx - r - 16}" y="${cy + d - 4}" width="16" height="8" fill="#39453e"/><rect x="${cx + r}" y="${cy + d - 4}" width="16" height="8" fill="#39453e"/>`; }
  s += `<rect x="${cx - r}" y="${cy - r}" width="${2 * r}" height="${2 * r}" rx="10" fill="#0f1411" stroke="${c}" stroke-width="3"/>`;
  s += `<rect x="${cx - r + 14}" y="${cy - r + 14}" width="${2 * r - 28}" height="${2 * r - 28}" rx="6" fill="none" stroke="${c}" stroke-opacity=".25" stroke-width="2"/>`;
  if (label) s += tx(cx, cy + (o.fs || 34) * .36, o.fs || 34, label, { a: 'middle', w: 900, f: c, ff: 'Inter, Noto Sans SC', ls: 1 });
  return s;
}

// ─── 冷开场：夜里的休息室
SCENES.cold = function (sc) {
  const lt = T - sc.start, z = 1 + 0.08 * eio(lt / 27);
  let s = `<g transform="translate(600 900) scale(${z.toFixed(4)}) translate(-600 -900)">`;
  s += `<rect x="-100" y="-100" width="1280" height="1230" fill="url(#wall)"/><rect x="-100" y="1130" width="1280" height="700" fill="#060807"/>`;
  s += `<line x1="-100" y1="1130" x2="1180" y2="1130" stroke="#1d2520" stroke-width="2"/>`;
  // 墙上的窗（夜）
  s += `<rect x="120" y="500" width="250" height="270" fill="url(#night)" stroke="#1c2420" stroke-width="6"/>`;
  for (let i = 0; i < 8; i++) s += `<rect x="120" y="${512 + i * 33}" width="250" height="5" fill="#161d19"/>`;
  // 乒乓球台，被推到左边墙角
  s += `<g opacity=".95"><rect x="-70" y="930" width="400" height="16" rx="3" fill="#1b3226" stroke="#3b6650" stroke-width="2.5"/>` +
    `<rect x="124" y="896" width="6" height="34" fill="#3a4a41"/><rect x="100" y="896" width="54" height="3" fill="#56695e"/>` +
    `<path d="M-30 946L-50 1130M290 946L310 1130M40 946L30 1130" stroke="#2c3a32" stroke-width="7"/>` +
    `<ellipse cx="236" cy="922" rx="26" ry="7" fill="#3a2a22"/><rect x="258" y="919" width="30" height="6" rx="3" fill="#2b332e"/><circle cx="196" cy="920" r="8" fill="#c9d1cb" opacity=".8"/></g>`;
  // 机器、电缆、显示器
  const mOn = on('machine', 1.2);
  s += `<path d="M640 1126C560 1160 520 1150 470 1128M660 1128C600 1190 470 1180 420 1126" fill="none" stroke="#1a231e" stroke-width="7"/>`;
  s += machine(640, 590, 270, 540, { pool: 0.5 + 0.5 * mOn });
  s += `<rect x="330" y="968" width="270" height="14" fill="#1a211d"/><path d="M350 982v148M580 982v148" stroke="#1a211d" stroke-width="10"/>`;
  s += crt(352, 760, 226, 196, 0.06 + lt / 62);
  s += `<ellipse cx="465" cy="1136" rx="170" ry="30" fill="url(#gpool)" opacity=".5"/>`;
  s += `</g>`;
  s += `<rect x="0" y="1100" width="${W}" height="400" fill="url(#fadeDown)"/><rect x="0" y="1499" width="${W}" height="500" fill="#0A0C0B"/>`;
  // 文字
  s += G(win('cold', 'cash', .9), tx(72, 420, 150, '1996', { w: 900, ls: -2, ff: 'Inter' }), 0);
  // 现金 → 机器
  const ca = win('cash', 'name');
  if (ca > 0) {
    const p = eio(prog('cash', 1.6, .6));
    s += O(ca, tx(72, 330, 34, '公司剩下的现金', { w: 700, f: COL.mute }) +
      `<rect x="72" y="356" width="936" height="46" rx="6" fill="#141a17" stroke="#27302B" stroke-width="2"/>` +
      `<rect x="72" y="356" width="${f1(936 * (1 - .42 * p))}" height="46" rx="6" fill="#2b352f"/>` +
      `<rect x="${f1(72 + 936 * .58)}" y="356" width="${f1(936 * .42)}" height="46" rx="6" fill="${COL.g}" opacity="${f1((.25 + .75 * p) * 100) / 100}" filter="url(#glow)"/>` +
      O(p, tx(1008, 452, 34, '一大块 → 这台机器', { a: 'end', f: COL.g }) +
        mono(1008, 492, 21, '占多少，说法不一：三分之一 / “最后的钱”', { a: 'end' })));
  }
  const na = win('name', 'thesis');
  s += G(na, tx(72, 400, 120, '英伟达', { w: 900, ls: 6 }) + O(prog('name', .6, 1.4), tx(76, 470, 36, '今天：全世界最值钱的公司之一', { w: 500, f: COL.mute })));
  // 论点
  const th = on('thesis', .7);
  if (th > 0) {
    const u2 = eo(prog('thesis', .5, 1.75)), st = eo(prog('thesis', .45, 1.2));
    s += DIM(th * .82);
    s += G(th, tx(540, 700, 96, '不是坚持', { a: 'middle', w: 900, f: '#77827a', ls: 8 }) +
      `<rect x="${330}" y="664" width="${f1(420 * st)}" height="7" fill="#77827a"/>`);
    s += G(u2, glow(tx(540, 880, 170, '是认错', { a: 'middle', w: 900, f: COL.g, ls: 10 })), 30);
  }
  return s;
};

// ─── 标题卡
SCENES.title = function (sc) {
  const lt = T - sc.start, a = eo(lt / .8), w = eo((lt - .2) / 1.2) * 936;
  let s = BG('#070908', .5);
  s += G(a, mono(72, 520, 30, '黄仁勋的商业决断', { f: COL.g, ls: 8 }));
  s += G(eo((lt - .15) / .8), tx(64, 760, 260, '01', { w: 900, ff: 'Inter', f: '#1f2a24', ls: -6 }), 0);
  s += `<rect x="72" y="800" width="${f1(w)}" height="4" fill="${COL.g}" filter="url(#glow)"/>`;
  s += G(eo((lt - .5) / .8), tx(72, 950, 128, '先认错，', { w: 900, ls: 4 }));
  s += G(eo((lt - .9) / .8), tx(72, 1105, 128, '再活下来', { w: 900, ls: 4 }));
  s += O(eo((lt - 1.6) / .8), mono(72, 1180, 24, '1993 — 1997 · 一家差点倒闭的芯片公司'));
  return s;
};

// ─── 餐馆
SCENES.diner = function (sc) {
  const lt = T - sc.start, z = 1 + 0.05 * eio(lt / 50);
  const toAn = on('chip', .8);                       // 切到“管家/画师”比方时，餐馆压暗
  let s = `<g transform="translate(540 820) scale(${z.toFixed(4)}) translate(-540 -820)" opacity="${f1((1 - .88 * toAn) * 100) / 100}">`;
  s += `<rect x="-60" y="-100" width="1200" height="1260" fill="url(#wall)"/>`;
  // 窗外夜色
  s += `<rect x="110" y="420" width="860" height="400" fill="url(#night)" stroke="#1d2622" stroke-width="8"/>`;
  for (let i = 0; i < 16; i++) { const bx = 140 + rnd(i) * 800, by = 600 + rnd(i + 40) * 170, r = 5 + rnd(i + 9) * 12;
    s += `<circle cx="${f1(bx)}" cy="${f1(by)}" r="${f1(r)}" fill="${i % 4 === 0 ? '#ffd9a0' : '#9fc8ff'}" opacity="${f1((0.06 + rnd(i + 3) * .12) * 100) / 100}"/>`; }
  for (let i = 0; i < 12; i++) s += `<rect x="110" y="${428 + i * 33}" width="860" height="4" fill="#0e1311" opacity=".9"/>`;
  s += `<rect x="536" y="420" width="8" height="400" fill="#1d2622"/>`;
  // 吊灯
  s += `<line x1="540" y1="-100" x2="540" y2="470" stroke="#262f2a" stroke-width="4"/><path d="M470 520L500 470H580L610 520Z" fill="#1c2420" stroke="#33413a" stroke-width="2"/>`;
  s += `<path d="M476 520L250 1100H830L604 520Z" fill="url(#lamp)" opacity="${f1((0.85 + .08 * Math.sin(T * 2.3)) * 100) / 100}"/>`;
  // 人影（在卡座靠背前）
  s += person(250, 800, 1.0) + person(850, 800, 1.0) + person(730, 822, .94);
  // 卡座
  s += `<rect x="100" y="800" width="64" height="300" rx="14" fill="#161c19" stroke="#2a352f" stroke-width="2.5"/><rect x="100" y="1010" width="290" height="90" rx="12" fill="#131815" stroke="#2a352f" stroke-width="2.5"/>`;
  s += `<rect x="916" y="800" width="64" height="300" rx="14" fill="#161c19" stroke="#2a352f" stroke-width="2.5"/><rect x="690" y="1010" width="290" height="90" rx="12" fill="#131815" stroke="#2a352f" stroke-width="2.5"/>`;
  // 桌子、咖啡杯
  s += `<rect x="330" y="960" width="420" height="22" rx="6" fill="#222b26" stroke="#3a4840" stroke-width="2"/><rect x="524" y="982" width="32" height="118" fill="#151a17"/><rect x="470" y="1092" width="140" height="10" rx="5" fill="#1b221e"/>`;
  [410, 560, 660].forEach((cx, i) => {
    s += `<path d="M${cx - 18} 930h36l-4 30h-28z" fill="#cfd6d0" opacity=".85"/><path d="M${cx + 18} 936q14 2 0 16" fill="none" stroke="#cfd6d0" stroke-width="3" opacity=".8"/>`;
    for (let k = 0; k < 2; k++) { const ph = T * 0.9 + i * 1.7 + k * 2.1, dx = Math.sin(ph) * 7;
      s += `<path d="M${cx - 6 + k * 12} 922q${f1(dx)} -18 0 -34q${f1(-dx)} -16 0 -32" fill="none" stroke="#dfe6e0" stroke-width="2.5" opacity="${f1((0.16 + .08 * Math.sin(ph * 1.3)) * 100) / 100}" stroke-linecap="round"/>`; }
  });
  s += `<rect x="-60" y="1100" width="1200" height="80" fill="#070908"/></g>`;
  s += `<rect x="0" y="1060" width="${W}" height="320" fill="url(#fadeDown)"/><rect x="0" y="1379" width="${W}" height="600" fill="#0A0C0B"/>`;
  // 文字层
  s += G(win('diner', 'thirty', .8), tx(72, 400, 120, '1993', { w: 900, ff: 'Inter', ls: -2 }) + tx(380, 396, 40, '圣何塞 · 一家连锁餐馆', { w: 500, f: COL.mute }), 0);
  const tg = win('thirty', 'busboy');
  ['30 岁', '已婚', '两个孩子'].forEach((w, i) => {
    const u = tg * eo(prog('thirty', .35, .1 + i * .5));
    s += G(u, `<rect x="${72 + i * 250}" y="330" width="226" height="74" rx="10" fill="#101512" stroke="${COL.gd}" stroke-width="2"/>` + tx(72 + i * 250 + 113, 381, 38, w, { a: 'middle' }));
  });
  s += G(tg, mono(72, 448, 22, 'CBS《60 Minutes》2024 旁白'), 0);
  const bb = win('busboy', 'q_noidea');
  s += G(bb, tx(72, 372, 76, '15 岁', { w: 900 }) + tx(300, 368, 36, '同一个牌子，另一家分店', { w: 500, f: COL.mute }) +
    tx(72, 440, 40, '洗盘子 · 收桌子', { f: COL.g }) + mono(72, 484, 22, '英伟达官方博客 2023-09-26'));
  const k4 = win('40k', 'bet3d');
  s += G(k4, glow(tx(72, 410, 150, '$40,000', { w: 900, ff: 'Inter', f: COL.g, ls: -3 })) + tx(76, 474, 36, '公司成立时账上的钱', { w: 500 }) + mono(76, 514, 22, '《财富》杂志 2017-11'));
  s += G(win('bet3d', 'chip'), tx(72, 372, 44, '他们押对了：', { w: 500, f: COL.mute }) + tx(72, 458, 84, '3D 游戏，会火', { w: 900 }));
  // 比方：管家 / 画师
  if (toAn > 0) {
    const out = 1 - on('so1', .5);
    const a1 = toAn * out, a2 = on('painter', .6) * out;
    s += G(a1 * (1 - on('painter', .5)), tx(540, 420, 44, '电脑里专门“画画面”的那块芯片', { a: 'middle', w: 700 }) + mono(540, 470, 24, '显卡 / 3D 图形芯片', { a: 'middle', f: COL.g }));
    // CPU 管家
    s += G(a2, `<rect x="72" y="360" width="450" height="700" rx="18" fill="${COL.panel}" stroke="${COL.line}" stroke-width="2"/>` +
      chip(297, 520, 78, 'CPU', { c: '#aab4ad' }) + tx(297, 690, 60, '管家', { a: 'middle', w: 900 }) + tx(297, 742, 32, '什么都管', { a: 'middle', w: 500, f: COL.mute }) +
      ['算账', '开文件', '联网', '管键盘鼠标', '……'].map((w, i) => O(eo(prog('painter', .3, .5 + i * .28)),
        `<rect x="132" y="${790 + i * 52}" width="330" height="40" rx="8" fill="#161c19"/>` + tx(297, 819 + i * 52, 26, w, { a: 'middle', w: 500, f: '#b7c0ba' }))).join(''));
    // 画师
    const pu = prog('painter', 3.2, 2.4);
    let pic = `<rect x="618" y="800" width="330" height="210" rx="6" fill="#070a08" stroke="#2c3832" stroke-width="2"/><clipPath id="pc"><rect x="618" y="800" width="330" height="${f1(210 * pu)}"/></clipPath><g clip-path="url(#pc)">` +
      `<rect x="618" y="800" width="330" height="210" fill="#0b1a12"/><path d="M618 1010L700 880L760 950L840 850L948 1010Z" fill="#1f8f55"/><circle cx="880" cy="850" r="22" fill="#8dffb9"/></g>` +
      (pu < 1 ? `<rect x="618" y="${f1(800 + 210 * pu - 2)}" width="330" height="3" fill="#b8ffd3" filter="url(#glow)"/>` : '');
    s += G(eo(prog('painter', .6, 2.0)) * out, `<rect x="558" y="360" width="450" height="700" rx="18" fill="${COL.panel}" stroke="${COL.gd}" stroke-width="2"/>` +
      chip(783, 520, 78, '图形芯片', { fs: 26 }) + tx(783, 690, 60, '画师', { a: 'middle', w: 900, f: COL.g }) + tx(783, 742, 32, '只管画', { a: 'middle', w: 500, f: COL.mute }) + pic);
  }
  // 小结
  const so = on('so1', .6);
  if (so > 0) {
    s += DIM(so * .55) + SO('so1');
    s += G(eo(prog('so1', .5, 1.0)), tx(540, 640, 54, '方向', { a: 'middle', w: 500, f: COL.mute }) + glow(tx(540, 760, 112, '对的', { a: 'middle', w: 900, f: COL.g, ls: 8 })));
    s += G(eo(prog('so1', .5, 3.1)), tx(540, 900, 54, '下一步', { a: 'middle', w: 500, f: COL.mute }) + tx(540, 1020, 112, '错的', { a: 'middle', w: 900, f: COL.warn, ls: 8 }));
  }
  return s;
};

// ─── 章鱼：NV1
SCENES.octo = function (sc) {
  const lt = T - sc.start, z = 1 + 0.04 * eio(lt / 40);
  const ret = on('returns', .7), so = on('so2', .6);
  let s = BG();
  s += `<g transform="translate(540 760) scale(${z.toFixed(4)}) translate(-540 -760)" opacity="${f1((1 - .86 * Math.max(ret, so)) * 100) / 100}">`;
  // 触手一样的线和接口
  const arms = [
    ['3D 图形', 150, 470, -1], ['2D 显示', 110, 720, -1], ['声音', 160, 1010, -1],
    ['手柄接口', 930, 470, 1], ['手柄接口', 970, 720, 1], ['摇杆口', 920, 1010, 1],
  ];
  const grow = eio(prog('stuff', 2.6, .1)), oct = on('octopus', 1.0);
  arms.forEach(([lab, ex, ey, dir], i) => {
    const sx = 540 + dir * 170, sy = 700 + (i % 3 - 1) * 60;
    const wob = Math.sin(T * 1.3 + i * 1.9) * (10 + 26 * oct), wob2 = Math.cos(T * 1.1 + i) * (8 + 22 * oct);
    const c1x = sx + dir * 120, c1y = sy + (ey - sy) * .1 + wob, c2x = ex - dir * 130, c2y = ey - (ey - sy) * .5 + wob2;
    const u = clamp(grow * 1.5 - i * .08);
    s += `<path d="M${sx} ${sy}C${f1(c1x)} ${f1(c1y)} ${f1(c2x)} ${f1(c2y)} ${ex} ${ey}" fill="none" stroke="#1d5c3b" stroke-width="${18 + 6 * oct}" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="${f1((1 - u) * 1000) / 1000}"/>`;
    s += `<path d="M${sx} ${sy}C${f1(c1x)} ${f1(c1y)} ${f1(c2x)} ${f1(c2y)} ${ex} ${ey}" fill="none" stroke="${COL.g}" stroke-width="4" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="${f1((1 - u) * 1000) / 1000}" opacity=".9"/>`;
    const eu = eo((u - .85) / .15);
    s += O(eu, `<rect x="${ex - 34}" y="${ey - 22}" width="68" height="44" rx="8" fill="#101512" stroke="${COL.g}" stroke-width="3"/>` +
      [0, 1, 2, 3].map(k => `<circle cx="${ex - 21 + k * 14}" cy="${ey}" r="3.5" fill="${COL.g}"/>`).join('') +
      tx(ex, ey + 68, 32, lab, { a: 'middle', w: 700 }));
  });
  // 显卡本体
  s += `<rect x="340" y="560" width="400" height="290" rx="14" fill="#0f1a14" stroke="#2d6b49" stroke-width="3"/>`;
  for (let i = 0; i < 14; i++) s += `<rect x="${372 + i * 24}" y="850" width="14" height="30" fill="#b99a3a" opacity=".8"/>`;
  s += `<path d="M360 600h80v40h60M720 620h-70v60h-40M360 800h120v-40" fill="none" stroke="#1f4a34" stroke-width="3"/>`;
  s += chip(540, 705, 74, 'NV1');
  if (oct > 0) { // 一点章鱼的意思：两只眼睛
    const bl = (T % 3.1) < .12 ? .15 : 1;
    s += O(oct, `<ellipse cx="512" cy="664" rx="9" ry="${f1(11 * bl)}" fill="${COL.g}"/><ellipse cx="568" cy="664" rx="9" ry="${f1(11 * bl)}" fill="${COL.g}"/>`);
  }
  s += `</g>`;
  s += G(win('nv1', 'stuff', .8), tx(72, 400, 120, '1995', { w: 900, ff: 'Inter', ls: -2 }) + tx(380, 396, 40, '第一颗芯片 · NV1', { w: 500, f: COL.mute }), 0);
  s += G(win('stuff', 'q_terrible') , tx(540, 392, 56, '一块卡，想全包', { a: 'middle', w: 900 }), 0);
  s += G(win('q_terrible', 'octopus'), tx(540, 372, 44, '技术成就：了不起', { a: 'middle', f: COL.g }) + tx(540, 436, 44, '产品：糟糕', { a: 'middle', f: COL.warn }), 0);
  s += G(win('octopus', 'knife'), tx(540, 400, 64, '“像一只章鱼”', { a: 'middle', w: 900 }), 0);
  s += G(win('knife', 'returns'), tx(540, 372, 40, '市场只想要一样东西：', { a: 'middle', w: 500, f: COL.mute }) + tx(540, 440, 54, '又快又便宜的 3D 芯片', { a: 'middle', w: 900, f: COL.g }), 0);
  // 退货
  if (ret > 0 && so < 1) {
    const a = ret * (1 - so), p1 = eio(prog('returns', 1.6, 1.3)), p2 = eio(prog('returns', 2.0, 3.6));
    const n1 = Math.round(250000 * p1), n2 = Math.round(249000 * p2);
    s += O(a, tx(72, 520, 36, '卖出去', { w: 500, f: COL.mute }) + tx(72, 640, 124, n1.toLocaleString('en-US'), { w: 900, ff: 'Inter', ls: -3 }) + tx(1008, 640, 40, '片', { a: 'end', w: 500, f: COL.mute }) +
      `<rect x="72" y="676" width="936" height="10" rx="5" fill="#1a211d"/><rect x="72" y="676" width="${f1(936 * p1)}" height="10" rx="5" fill="#aab4ad"/>` +
      tx(72, 820, 36, '被退回来', { w: 500, f: COL.mute }) + tx(72, 940, 124, '≈ ' + n2.toLocaleString('en-US'), { w: 900, ff: 'Inter', f: COL.warn, ls: -3 }) + tx(1008, 940, 40, '片', { a: 'end', w: 500, f: COL.mute }) +
      `<rect x="72" y="976" width="936" height="10" rx="5" fill="#1a211d"/><rect x="${f1(72 + 936 * (1 - p2 * .996))}" y="976" width="${f1(936 * p2 * .996)}" height="10" rx="5" fill="${COL.warn}"/>` +
      mono(72, 1040, 22, '他本人的说法，带夸张口吻；买方是显卡厂商 Diamond'));
  }
  if (so > 0) {
    s += SO('so2');
    s += G(eo(prog('so2', .5, .9)), tx(540, 640, 50, '产品好不好', { a: 'middle', w: 500, f: COL.mute }) + tx(540, 760, 80, '工程师说了不算', { a: 'middle', w: 900, f: '#77827a' }));
    s += G(eo(prog('so2', .5, 3.0)), glow(tx(540, 920, 96, '掏钱的人说了算', { a: 'middle', w: 900, f: COL.g })));
  }
  return s;
};
