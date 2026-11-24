/* 时间线驱动的确定性动画内核：window.setTime(t) 把整个画面摆到 t 秒 */
(function () {
  const TL = window.TL;
  const SEG = Object.fromEntries(TL.segs.map(s => [s.id, s]));
  const SCN = Object.fromEntries(TL.scenes.map(s => [s.id, s]));
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const ramp = (t, a, b) => clamp((t - a) / (b - a));
  const eio = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
  const eo = x => 1 - Math.pow(1 - x, 3);
  const eob = x => { const c = 1.70158; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
  const lerp = (a, b, x) => a + (b - a) * x;
  const vis = (t, a, b, din = .5, dout = .5) => Math.min(ramp(t, a, a + din), 1 - ramp(t, b - dout, b));
  const S = id => SEG[id].s, E = id => SEG[id].e;
  /* 伪随机（固定种子，保证逐帧可复现） */
  const rnd = i => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };

  const stage = document.getElementById('stage');
  stage.insertAdjacentHTML('afterbegin', ART.defs);
  function el(parent, cls, style, html) {
    const d = document.createElement('div'); if (cls) d.className = cls;
    if (style) d.style.cssText = style; if (html !== undefined) d.innerHTML = html; parent.appendChild(d); return d;
  }
  const svg = (vb, inner, style = '') => `<svg viewBox="${vb}" style="position:absolute;overflow:visible;${style}">${inner}</svg>`;

  const scenes = [];   // {id, root, anim:[fn], a, b}
  function scene(id, build, a, b) {
    const sc = SCN[id] || {};
    const root = el(stage, 'scene', ''); root.id = 'sc-' + id;
    const anim = []; const obj = { id, root, anim, a: a ?? sc.cut_in, b: b ?? sc.cut_out };
    build(root, f => anim.push(f), obj); scenes.push(obj); return obj;
  }
  const overlays = [];
  function overlay(build) { const anim = []; build(stage, f => anim.push(f)); overlays.push(anim); }

  /* —— 组件 —— */
  /* 逐字显现的引文。opts: {x,y,w,size,lh,align,color,weight,ls} */
  function typeBlock(parent, lines, o = {}) {
    const d = el(parent, 'abs serif', `left:${o.x ?? 90}px;top:${o.y ?? 400}px;width:${o.w ?? 900}px;font-size:${o.size ?? 68}px;line-height:${o.lh ?? 1.5};font-weight:${o.weight ?? 900};color:${o.color ?? '#f1e3c0'};text-align:${o.align ?? 'center'};letter-spacing:${o.ls ?? '.04em'};`);
    const spans = [];
    (Array.isArray(lines) ? lines : [lines]).forEach((ln, i) => {
      const row = el(d, '', 'white-space:nowrap');
      ln.split(/(\{[^}]*\})/).forEach(part => {            // {文字|颜色} 局部着色
        let txt = part, col = null; const m = part.match(/^\{(.*)\|(.*)\}$/); if (m) { txt = m[1]; col = m[2]; }
        [...txt].forEach(ch => { const s = document.createElement('span'); s.textContent = ch; if (col) s.style.color = col; s.style.opacity = 0; row.appendChild(s); spans.push(s); });
      });
    });
    d.reveal = p => { const n = spans.length; spans.forEach((s, i) => { s.style.opacity = clamp(p * (n + 2) - i).toFixed(3); }); };
    d.spans = spans; return d;
  }
  /* 引文卡：随某句旁白逐字出现，保持到 until */
  function quote(parent, add, id, lines, o = {}) {
    const d = typeBlock(parent, lines, o); const a = (o.from ?? S(id)) - .15, dur = o.dur ?? (E(id) - S(id)) * .82;
    const until = o.until ?? E(id) + 1.2;
    let cite = null;
    if (o.cite) cite = el(d, 'serif', `font-size:26px;font-weight:500;color:#8f8369;letter-spacing:.18em;margin-top:18px;opacity:0`, o.cite);
    let gl = null;
    if (o.gloss) gl = el(d, 'sans', `font-size:30px;font-weight:400;color:#a99d84;letter-spacing:.06em;margin-top:14px;opacity:0;line-height:1.5`, o.gloss);
    add(t => {
      const v = t < a ? 0 : 1 - ramp(t, until - .45, until);
      d.style.opacity = v; if (v <= 0) return; d.reveal(ramp(t, a, a + dur));
      if (cite) cite.style.opacity = ramp(t, a + dur * .6, a + dur + .3) * .95;
      if (gl) gl.style.opacity = ramp(t, o.glossAt ?? (a + dur), (o.glossAt ?? (a + dur)) + .5);
    });
    return d;
  }
  /* 简单淡入淡出的文字 */
  function label(parent, add, html, style, tin, tout, o = {}) {
    const d = el(parent, 'abs ' + (o.cls ?? 'sans'), style + ';opacity:0', html);
    add(t => { const v = vis(t, tin, tout, o.din ?? .45, o.dout ?? .45); d.style.opacity = v * (o.max ?? 1); if (o.rise) d.style.transform = `translateY(${(1 - eo(ramp(t, tin, tin + .6))) * o.rise}px)`; });
    return d;
  }
  /* 官名释义卡 */
  function term(parent, add, name, def, x, y, tin, tout, o = {}) {
    const d = el(parent, 'abs', `left:${x}px;top:${y}px;opacity:0;display:flex;align-items:center;gap:22px`);
    el(d, 'serif', `font-size:${o.size ?? 64}px;font-weight:900;color:#e8c98a;letter-spacing:.08em;padding:6px 22px 10px;border:2px solid #c9a45c;background:rgba(10,9,8,.72)`, name);
    el(d, 'sans', `font-size:32px;color:#d8ccb2;line-height:1.45;max-width:${o.w ?? 520}px;text-shadow:0 2px 10px #000`, def);
    add(t => { const v = vis(t, tin, tout, .4, .4); d.style.opacity = v; d.style.transform = `translateX(${(1 - eo(ramp(t, tin, tin + .5))) * -24}px)`; });
    return d;
  }
  /* 朱印（盖章动画） */
  function stamp(parent, add, text, x, y, at, tout, o = {}) {
    const size = o.size ?? 58;
    const d = el(parent, 'abs serif', `left:${x}px;top:${y}px;font-size:${size}px;font-weight:900;color:#d2382c;border:${o.bw ?? 5}px solid #c8372d;padding:${o.pad ?? '0 12px 4px'};letter-spacing:.06em;line-height:1.25;transform-origin:50% 50%;opacity:0;filter:url(#inkbleed);white-space:nowrap`, text);
    add(t => {
      if (t < at || t > tout) { d.style.opacity = 0; return; }
      const p = ramp(t, at, at + .16); d.style.opacity = Math.min(p * 1.6, 1 - ramp(t, tout - .4, tout)) * .96;
      d.style.transform = `rotate(${o.rot ?? -7}deg) scale(${lerp(2.1, 1, eo(p))})`;
    });
    return d;
  }

  Object.assign(window, { F: { TL, SEG, SCN, clamp, ramp, eio, eo, eob, lerp, vis, S, E, rnd, stage, el, svg, scene, overlay, typeBlock, quote, label, term, stamp } });

  /* —— 驱动 —— */
  window.setTime = function (t) {
    for (const sc of scenes) {
      const v = vis(t, sc.a - .4, sc.b + .4, .8, .8);
      if (v <= 0) { if (sc.root.style.display !== 'none') sc.root.style.display = 'none'; continue; }
      sc.root.style.display = 'block'; sc.root.style.opacity = v;
      for (const f of sc.anim) f(t);
    }
    for (const a of overlays) for (const f of a) f(t);
  };
  F.boot = async () => {
    for (const sc of scenes) sc.root.style.display = 'block';
    const all = [...new Set(stage.innerText + TL.segs.map(s => s.text).join('') + '0123456789')].join('');
    const fams = [['Noto Serif SC', [500, 700, 900]], ['Noto Sans SC', [400, 500, 700]]];
    await Promise.all(fams.flatMap(([f, ws]) => ws.map(w => document.fonts.load(`${w} 40px "${f}"`, all))));
    await document.fonts.ready; window.setTime(0);
  };
})();
