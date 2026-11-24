/* 场景 A：冷开场 · 厕鼠与仓鼠 · 地图（帝王之术 / 换仓） */
(function () {
  const { TL, SEG, SCN, clamp, ramp, eo, eio, lerp, vis, S, E, rnd, el, svg, scene, quote, label, term, stamp, typeBlock } = F;
  const CITE87 = '《史记·李斯列传》', CITE63 = '《史记·老子韩非列传》';
  F.CITE87 = CITE87; F.CITE63 = CITE63;

  /* —— 黄昏幻象：上蔡东门、黄犬逐兔（开头与结尾共用） —— */
  F.dusk = function (parent, y0 = 700, h = 580) {
    const d = el(parent, 'abs', `left:0;top:${y0}px;width:1080px;height:${h}px;opacity:0`); const u = 'k' + y0 + '_' + h;
    d.innerHTML = `<svg viewBox="0 0 1080 ${h}" width="1080" height="${h}" style="position:absolute;inset:0;overflow:visible">
      <defs><radialGradient id="duskG${u}" cx="62%" cy="74%" r="75%"><stop offset="0" stop-color="#e2a646"/><stop offset=".28" stop-color="#9a5f22"/><stop offset=".62" stop-color="#3a2210"/><stop offset="1" stop-color="#0b0a09" stop-opacity="0"/></radialGradient>
      <radialGradient id="duskMG${u}" cx="62%" cy="74%" r="60%"><stop offset="0" stop-color="#fff"/><stop offset=".7" stop-color="#555"/><stop offset="1" stop-color="#000"/></radialGradient>
      <linearGradient id="duskFade${u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b0a09"/><stop offset=".22" stop-color="#0b0a09" stop-opacity="0"/><stop offset=".8" stop-color="#0b0a09" stop-opacity="0"/><stop offset="1" stop-color="#0b0a09"/></linearGradient></defs>
      <rect width="1080" height="${h}" fill="url(#duskG${u})"/>
      <mask id="duskM${u}"><rect width="1080" height="${h}" fill="url(#duskMG${u})"/></mask>
      <rect width="1080" height="${h}" fill="url(#hatchH)" opacity=".4" mask="url(#duskM${u})"/>
      <circle cx="690" cy="${h - 150}" r="62" fill="#f3c66a" opacity=".85"/>
      <path d="M-20 ${h - 120} C 200 ${h - 136}, 420 ${h - 112}, 640 ${h - 124} C 800 ${h - 132}, 960 ${h - 116}, 1100 ${h - 126} V ${h} H -20 Z" fill="#060504" filter="url(#rough)"/>
      <g transform="translate(60 ${h - 392}) scale(.66)">${ART.gate('#060504')}</g>
      <g class="men" transform="translate(330 ${h - 208})"><g transform="scale(.42)">${ART.man('#060504')}</g><g transform="translate(46 22) scale(.34)">${ART.man('#060504')}</g></g>
      <g class="dog">${ART.dog('#0a0705')}</g>
      <g class="hare">${ART.hare('#0a0705')}</g>
      <rect width="1080" height="${h}" fill="url(#duskFade${u})"/></svg>`;
    const dog = d.querySelector('.dog'), hare = d.querySelector('.hare');
    d.run = (t0, t) => {                                 // 奔跑：从城门向右
      const p = (t - t0), gy = h - 232;
      const dx = 420 + p * 34, hx = dx + 250 + Math.sin(p * 1.3) * 26;
      dog.setAttribute('transform', `translate(${dx} ${gy + Math.sin(p * 9) * 7}) rotate(${Math.sin(p * 9 + 1) * 4}) scale(.5)`);
      hare.setAttribute('transform', `translate(${hx} ${gy + 30 - Math.abs(Math.sin(p * 7)) * 26}) rotate(${Math.cos(p * 7) * 9}) scale(.42)`);
    };
    return d;
  };

  /* —— 厕 / 仓 两块版画（开头与结尾共用） —— */
  F.ratPanel = function (parent, kind, x, y, w = 936) {
    const H = 380, s = w / 936;
    const d = el(parent, 'abs', `left:${x}px;top:${y}px;width:${w}px;height:${H * s}px;opacity:0`);
    const id = kind + Math.round(x) + '_' + Math.round(y);
    if (kind === 'ce') {
      d.innerHTML = `<svg viewBox="0 0 936 380" width="${w}" height="${H * s}" style="position:absolute;inset:0">
        <defs><radialGradient id="g${id}" cx="72%" cy="12%" r="95%"><stop offset="0" stop-color="#6b7b82"/><stop offset=".4" stop-color="#262f34"/><stop offset="1" stop-color="#06080a"/></radialGradient>
        <clipPath id="c${id}"><rect width="936" height="380"/></clipPath></defs>
        <g clip-path="url(#c${id})">
          <rect width="936" height="380" fill="url(#g${id})"/><rect width="936" height="380" fill="url(#hatchH)" opacity=".6"/>
          <path d="M-10 0 H210 V306 H-10 Z" fill="#050607" filter="url(#rough)"/>
          <path d="M210 150 H250 V306 H210 Z" fill="#0a0d0f"/>
          <path d="M-10 302 H950 V390 H-10 Z" fill="#040505" filter="url(#rough)"/>
          <ellipse cx="640" cy="322" rx="150" ry="20" fill="#000"/>
          <path d="M520 304 H760 M540 296 V312 M740 296 V312" stroke="#161b1e" stroke-width="7"/>
          ${[0, 1, 2, 3, 4, 5, 6].map(i => `<circle cx="${430 + rnd(i) * 160}" cy="${306 - rnd(i + 9) * 8}" r="${3 + rnd(i + 3) * 4}" fill="#020303"/>`).join('')}
          <g class="intr"><g transform="translate(1040 176) scale(-1.05 1.05)">${ART.dog('#020303')}</g>
            <path d="M826 -20 L 902 -20 L 884 232 L 890 290 L 772 306 L 770 286 L 826 262 L 836 170 Z" fill="#020303" filter="url(#rough2)"/></g>
          <g class="rat"><g transform="translate(350 124) scale(.74)">${ART.ratThin('#020303')}</g></g>
        </g>
        <rect width="936" height="380" fill="none" stroke="#5b6a70" stroke-width="3"/></svg>`;
    } else {
      d.innerHTML = `<svg viewBox="0 0 936 380" width="${w}" height="${H * s}" style="position:absolute;inset:0">
        <defs><radialGradient id="g${id}" cx="46%" cy="52%" r="85%"><stop offset="0" stop-color="#d9a544"/><stop offset=".42" stop-color="#7a5119"/><stop offset="1" stop-color="#150d05"/></radialGradient>
        <clipPath id="c${id}"><rect width="936" height="380"/></clipPath></defs>
        <g clip-path="url(#c${id})">
          <rect width="936" height="380" fill="url(#g${id})"/><rect width="936" height="380" fill="url(#hatchH)" opacity=".5"/>
          <path d="M-20 -10 H956 V58 L 900 92 H 36 L -20 58 Z" fill="#070503" filter="url(#rough)"/>
          ${[0, 1, 2, 3, 4, 5, 6, 7, 8].map(i => `<path d="M${60 + i * 102} 92 L ${44 + i * 102} 120 H ${76 + i * 102} Z" fill="#070503"/>`).join('')}
          <rect x="52" y="92" width="40" height="300" fill="#070503" filter="url(#rough2)"/><rect x="844" y="92" width="40" height="300" fill="#070503" filter="url(#rough2)"/>
          <path d="M60 392 C 190 310, 340 286, 478 284 C 620 286, 770 310, 890 392 Z" fill="#e0ae45" filter="url(#rough)"/>
          <path d="M60 392 C 190 310, 340 286, 478 284 C 620 286, 770 310, 890 392 Z" fill="url(#hatchD)" opacity=".5"/>
          ${Array.from({ length: 70 }, (_, i) => { const a = rnd(i) * 700 + 130, b = 300 + rnd(i + 50) * 80 + Math.abs(a - 478) * .2; return `<ellipse cx="${a}" cy="${Math.min(b, 372)}" rx="5" ry="2.6" transform="rotate(${rnd(i + 7) * 180} ${a} ${Math.min(b, 372)})" fill="#f6d98a" opacity=".8"/>`; }).join('')}
          <g class="rat"><g transform="translate(270 118) scale(.72)">${ART.ratFat('#070402')}</g></g>
        </g>
        <rect width="936" height="380" fill="none" stroke="#8a6a2e" stroke-width="3"/></svg>`;
    }
    el(d, 'abs serif', `left:${(kind === 'ce' ? 22 : 110) * s}px;top:${(kind === 'ce' ? 14 : 124) * s}px;font-size:${96 * s}px;font-weight:900;line-height:1;color:${kind === 'ce' ? '#a9bcc4' : '#ffe9ad'};opacity:${kind === 'ce' ? .5 : .62}`, kind === 'ce' ? '厕' : '仓');
    d.rat = d.querySelector('.rat'); d.intr = d.querySelector('.intr');
    return d;
  };

  /* ================= 冷开场 ================= */
  scene('cold', (root, add) => {
    root.style.background = '#070605';
    label(root, add, '秦二世二年七月 · 咸阳', 'left:0;right:0;top:232px;text-align:center;font-size:36px;font-weight:700;letter-spacing:.3em;text-indent:.3em;color:#c9a45c', S('c1') - .9, S('c5') + 3, { cls: 'serif' });
    /* 牢门的光与两个人影 */
    const door = el(root, 'abs', 'left:0;top:650px;width:1080px;height:640px;opacity:0');
    door.innerHTML = `<svg viewBox="0 0 1080 640" width="1080" height="640" style="position:absolute;inset:0;overflow:visible">
      <defs><linearGradient id="doorG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f0c57a"/><stop offset="1" stop-color="#a66a2a"/></linearGradient>
      <linearGradient id="spillG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c88a3c" stop-opacity=".75"/><stop offset="1" stop-color="#c88a3c" stop-opacity="0"/></linearGradient></defs>
      <rect x="400" y="40" width="280" height="420" fill="url(#doorG)" filter="url(#rough)"/>
      <path d="M400 460 L 680 460 L 900 660 L 180 660 Z" fill="url(#spillG)"/>
      <rect x="400" y="40" width="280" height="420" fill="url(#hatchH)" opacity=".4"/>
      ${[0, 1, 2, 3, 4].map(i => `<rect x="${418 + i * 58}" y="40" width="12" height="420" fill="#070605" opacity=".0"/>`).join('')}
      <g transform="translate(470 196) scale(1.3)">${ART.man('#060504', true)}</g>
      <g transform="translate(568 232) scale(1.08)">${ART.man('#060504')}</g>
      <path d="M520 330 C 560 350, 590 350, 612 336" stroke="#060504" stroke-width="5" fill="none"/></svg>`;
    const who = label(root, add, '李斯<span style="font-size:32px;font-weight:500;color:#a99d84;letter-spacing:.2em;margin-left:22px">秦丞相</span>', 'left:0;right:0;top:500px;text-align:center;font-size:84px;font-weight:900;letter-spacing:.2em;text-indent:.2em;color:#f1e3c0', S('c5') - .1, S('c5') + 2.6, { cls: 'serif' });
    const dusk = F.dusk(root, 690, 600);
    quote(root, add, 'c3', ['吾欲与若复牵{黄犬|#e8b84f}', '俱出{上蔡东门|#e8b84f}逐狡兔', '岂可得乎！'], { y: 316, size: 72, lh: 1.52, until: S('c5') - .1, cite: CITE87, gloss: '若：你　｜　上蔡：他的老家', glossAt: S('c4') });
    add(t => {
      const dv = vis(t, S('c3') + .9, S('c5') + .2, 1.4, .8); dusk.style.opacity = dv; if (dv > 0) dusk.run(S('c3'), t);
      door.style.opacity = Math.max(vis(t, .4, S('c3') + 1.6, 1.2, 1.0), vis(t, S('c5') - .3, E('c5') + .3, .7, .7));
      door.style.transform = `scale(${lerp(1, 1.07, ramp(t, 0, S('c3') + 2))})`;
    });
  });

  /* ================= 壹 厕鼠与仓鼠 ================= */
  scene('rats', (root, add) => {
    root.style.background = '#090807';
    const a = SCN.rats.cut_in;
    const top = F.ratPanel(root, 'ce', 72, 300), bot = F.ratPanel(root, 'cang', 72, 800);
    const q1 = quote(root, add, 'r3', ['食不絜，近人犬，{数惊恐之|#c9d6dc}'], { y: 694, size: 54, until: S('r8') - .1 });
    const q2 = quote(root, add, 'r6', ['食积粟，居大庑之下，{不见人犬之忧|#f0c56a}'], { y: 1194, size: 54, until: S('r8') - .1 });
    label(root, add, '絜＝洁　数（shuò）：屡次', 'left:0;right:0;top:770px;text-align:center;font-size:30px;color:#9c9075;letter-spacing:.08em', S('r3') + 1.6, S('r5') - .1);
    label(root, add, '庑（wǔ）：堂下四周的廊屋', 'left:0;right:0;top:1270px;text-align:center;font-size:30px;color:#9c9075;letter-spacing:.08em', S('r6') + 1.8, S('r8') - .2);
    const big = quote(root, add, 'r9', ['人之贤不肖', '譬如鼠矣', '{在所自处耳！|#f0c56a}'], { y: 520, size: 92, lh: 1.5, until: SCN.rats.cut_out + .5, cite: CITE87, gloss: '不肖：没出息　｜　自处：把自己放在哪儿', glossAt: S('r10') });
    add(t => {
      const dimmed = ramp(t, S('r8') - .2, S('r9') + .2);
      top.style.opacity = ramp(t, a, a + 1) * lerp(1, .2, dimmed);
      bot.style.opacity = ramp(t, S('r5') - .5, S('r5') + .5) * lerp(1, .2, dimmed);
      const push = lerp(1, 1.035, ramp(t, a, SCN.rats.cut_out));
      top.style.transform = `scale(${push})`; bot.style.transform = `scale(${push})`;
      /* 人犬逼近 → 厕鼠惊窜 */
      const k = eo(ramp(t, S('r3') + 1.0, S('r3') + 2.0)) - eio(ramp(t, S('r5') - .6, S('r5') + .6));
      top.intr.setAttribute('transform', `translate(${lerp(330, 0, k)} 0)`);
      const sc = eo(ramp(t, S('r3') + 1.5, S('r3') + 2.0)) - eio(ramp(t, S('r5') - .4, S('r5') + .8));
      const jit = sc > 0 && sc < 1 ? Math.sin(t * 60) * 3 : 0;
      top.rat.setAttribute('transform', `translate(${-200 * sc + jit} ${Math.sin(t * 2.2) * 1.5})`);
      bot.rat.setAttribute('transform', `translate(0 ${Math.sin(t * 1.4) * 2.2})`);   // 仓鼠只是呼吸
    });
  });

  /* ================= 地图（贯穿 贰/叁 与 肆 的开头） ================= */
  const Xa = SCN.xun.cut_in, MapEnd = S('z2') + .9;
  let MAP = null;
  scene('map', (root, add) => {
    const m = MAP = F.makeMap(root); F.MAP = m;
    const dim = el(root, 'abs', 'inset:0;background:#070605;opacity:0;z-index:5');
    const [r1a, r1b] = [S('x1') + .3, S('x1') + 3.6], [r2a, r2b] = [E('q1') - 1.6, S('q2') + 2.4];
    const zk = S('z1');
    add(t => {
      m.wrap.style.opacity = 1;
      const p1 = eio(ramp(t, r1a, r1b)), p2 = eio(ramp(t, r2a, r2b));
      m.route(p1, p2);
      /* 相机关键帧 */
      let lon, lat, z;
      const A = m.at(1, p1), B = m.at(2, p2);
      if (t < S('q1')) { lon = A[0]; lat = A[1]; z = lerp(2.7, 2.1, p1); }
      else if (t < r2a) { const k = eio(ramp(t, S('q1'), S('q1') + 1.8)); lon = lerp(118.07, 112.6, k); lat = lerp(34.86, 34.9, k); z = lerp(2.1, .98, k); }
      else if (t < zk) { const k = eio(ramp(t, r2a + .6, r2b)); lon = lerp(112.6, B[0], k); lat = lerp(34.9, B[1], k); z = lerp(.98, 2.3, k); const o = eio(ramp(t, S('q7') - .4, S('q7') + 1.6)); lon = lerp(lon, 113.0, o); lat = lerp(lat, 34.6, o); z = lerp(z, 1.02, o); }
      else { const k = eio(ramp(t, zk - .2, zk + 1.8)); lon = lerp(113.0, 109.25, k); lat = lerp(34.6, 34.72, k); z = lerp(1.02, 6.2, k); }
      m.cam(lon, lat, z, 540, 860);
      m.city('shangcai', ramp(t, Xa + .3, Xa + 1) * (1 - ramp(t, zk, zk + .8)));
      m.city('lanling', ramp(t, r1b - .5, r1b) * (1 - ramp(t, zk, zk + .8)));
      m.city('xianyang', ramp(t, r2b - .8, r2b));
      /* 列国评估：楚不足事 / 六国皆弱 / 秦欲吞天下 */
      const q1s = S('q1'), w = E('q1') - S('q1');
      const weak = ramp(t, q1s + w * .42, q1s + w * .6), qin = ramp(t, q1s + w * .72, q1s + w * .9) * (1 - ramp(t, r2a + .6, r2a + 2.2));
      ['赵', '燕', '齐', '魏', '韩'].forEach(n => m.state(n, lerp(.33, .16, weak)));
      m.state('楚', lerp(.33, .16, ramp(t, q1s + w * .22, q1s + w * .4)));
      m.state('秦', lerp(.33, .95, qin), qin > .5 ? '#f0c56a' : '#8c7a58');
      const cv = ramp(t, zk + 1.6, zk + 6.2); m.canal(cv, t > zk + 7.4 ? '#c8372d' : '#e2b659');
      dim.style.opacity = Math.max(vis(t, S('x2') - .3, E('x4') + .2, .6, .6), vis(t, S('q3') - .2, E('q5') + .2, .6, .6), ramp(t, S('z2') - .1, S('z2') + .7)) * .9;
    });
    label(root, add, '示意图 · 非精确疆界与路线', 'left:72px;top:1300px;font-size:22px;color:#6e634e;letter-spacing:.1em', Xa + 1, MapEnd - .5);
    /* 跟随地图坐标的标注 */
    const pin = (html, lon, lat, dx, dy, tin, tout, style = '') => {
      const d = el(root, 'abs sans', `font-size:28px;color:#d8ccb2;white-space:nowrap;text-shadow:0 0 8px #000,0 0 3px #000;opacity:0;${style}`, html);
      add(t => { const v = vis(t, tin, tout, .4, .4); d.style.opacity = v; if (v > 0) { const [x, y] = m.screen(lon, lat); d.style.left = (x + dx) + 'px'; d.style.top = (y + dy) + 'px'; } });
    };
    pin('郡小吏', 114.26, 33.27, -42, 22, Xa + .8, S('x1') + 2.2);
    pin('荀卿 · 兰陵令<span style="color:#8f8369;font-size:22px">　《孟子荀卿列传》</span>', 118.07, 34.86, -330, 24, S('x1') + 3.4, S('x2') - .3);
    const tag = 'font-family:Noto Serif SC;font-weight:900;font-size:34px;padding:2px 12px 5px;';
    pin('楚王不足事', 115.3, 31.6, -96, 62, S('q1') + (E('q1') - S('q1')) * .22, E('q1') + 1.2, tag + 'color:#b9ad93;border:1.5px solid #6b5f49;background:rgba(10,9,8,.6)');
    pin('六国皆弱', 116.9, 37.9, -72, 20, S('q1') + (E('q1') - S('q1')) * .42, E('q1') + 1.2, tag + 'color:#b9ad93;border:1.5px solid #6b5f49;background:rgba(10,9,8,.6)');
    pin('秦王欲吞天下', 107.2, 35.4, -120, 64, S('q1') + (E('q1') - S('q1')) * .72, E('q1') + 1.6, tag + 'color:#f0c56a;border:1.5px solid #c9a45c;background:rgba(10,9,8,.6)');
    pin('秦相文信侯吕不韦', 108.72, 34.36, -120, 30, S('q2') + 2.2, S('q3') - .3);
    /* 关中：郑国渠 */
    pin('泾水', 107.9, 35.12, -30, -52, S('z1') + 1.6, MapEnd, 'color:#7f9aa8');
    pin('洛水', 109.62, 35.42, 14, -10, S('z1') + 1.6, MapEnd, 'color:#7f9aa8');
    pin('渭水', 109.75, 34.52, -10, 18, S('z1') + 1.6, MapEnd, 'color:#7f9aa8');
    pin('瓠口', 108.62, 34.74, -34, -62, S('z1') + 2.0, MapEnd, 'color:#d8ccb2;font-size:26px');
  }, Xa, MapEnd);

  /* ================= 贰 帝王之术 ================= */
  scene('xun', (root, add) => {
    term(root, add, '帝王之术', '怎么帮君主<br>管住天下人', 96, 330, S('x1') + (E('x1') - S('x1')) * .52, S('x2') - .2, { size: 76 });
    label(root, add, '乃从荀卿学帝王之术', 'left:96px;top:480px;font-size:28px;color:#8f8369;letter-spacing:.14em', S('x1') + (E('x1') - S('x1')) * .6, S('x2') - .2, { cls: 'serif' });
    quote(root, add, 'x3', ['{诟|#f0c56a}莫大于{卑贱|#f0c56a}', '而{悲|#f0c56a}莫甚于{穷困|#f0c56a}'], { y: 560, size: 88, lh: 1.5, until: SCN.xun.cut_out + .2, cite: CITE87 + ' · 辞荀卿语', gloss: '诟（gòu）：耻辱', glossAt: S('x3') + 1.5 });
    label(root, add, '读书，是为了<span style="color:#f0c56a;font-weight:700">换一个仓</span>', 'left:0;right:0;top:1040px;text-align:center;font-size:52px;font-weight:500;letter-spacing:.12em;color:#e9dfc8', S('x5') + .2, SCN.xun.cut_out + .2, { cls: 'serif', rise: 16 });
  });

  /* ================= 叁 换仓 ================= */
  scene('qin', (root, add) => {
    term(root, add, '舍人', '大臣门下养的门客', 96, 480, S('q2') + 2.6, S('q3') - .2);
    label(root, add, '求为秦相文信侯吕不韦舍人　→　任以为郎　→　得说秦王', 'left:96px;top:600px;font-size:26px;color:#8f8369;letter-spacing:.08em', S('q2') + 3.4, S('q3') - .2, { cls: 'serif' });
    quote(root, add, 'q4', ['可下以财者，{厚遗结之|#f0c56a}', '不肯者，{利剑刺之|#d2382c}'], { y: 600, size: 76, lh: 1.6, until: S('q6') - .2, cite: CITE87, gloss: '遗（wèi）：赠送。收买不成，就刺杀', glossAt: S('q5') });
    /* 金与剑 */
    const ic = el(root, 'abs', 'left:0;top:960px;width:1080px;height:200px;opacity:0');
    ic.innerHTML = `<svg viewBox="0 0 1080 200" width="1080" height="200" style="position:absolute;inset:0;overflow:visible">
      <g class="coin" transform="translate(330 100)"><circle r="62" fill="none" stroke="#e2b659" stroke-width="14" filter="url(#rough2)"/><rect x="-20" y="-20" width="40" height="40" fill="none" stroke="#e2b659" stroke-width="8"/></g>
      <g class="sword" transform="translate(750 100) rotate(-28)"><path d="M-150 0 L 96 -9 L 150 0 L 96 9 Z" fill="#cfd4d6" filter="url(#rough2)"/><rect x="-170" y="-26" width="14" height="52" fill="#8f8369"/><rect x="-226" y="-8" width="58" height="16" fill="#5b4a2c"/></g></svg>`;
    add(t => {
      const v = vis(t, S('q4') + .3, S('q6') - .3, .5, .5); ic.style.opacity = v; if (v <= 0) return;
      const d = E('q4') - S('q4');
      ic.querySelector('.coin').setAttribute('opacity', ramp(t, S('q4') + d * .2, S('q4') + d * .35));
      ic.querySelector('.sword').setAttribute('opacity', ramp(t, S('q4') + d * .68, S('q4') + d * .8));
    });
    term(root, add, '客卿', '外国人在秦国<br>做的高官', 96, 480, S('q6') + 1.3, S('q7') - .1);
    label(root, add, '上蔡　→　兰陵　→　咸阳', 'left:0;right:0;top:1150px;text-align:center;font-size:40px;font-weight:700;letter-spacing:.2em;color:#c9a45c', S('q7') + .6, SCN.qin.cut_out + .1, { cls: 'serif' });
    label(root, add, '每一步，都离权力更近', 'left:0;right:0;top:1216px;text-align:center;font-size:34px;letter-spacing:.2em;color:#b9ad93', S('q7') + 1.0, SCN.qin.cut_out + .1);
  });
})();
