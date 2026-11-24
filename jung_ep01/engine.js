// 逐帧确定性渲染引擎：window.seek(t) 把整页状态设到第 t 秒。
// 时间线 window.TL 由 build/timeline.js 提供（tts.py 生成）。
(function () {
  const W = 1080, H = 1920;
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const ease = x => { x = clamp(x); return 1 - Math.pow(1 - x, 3); };
  const smooth = x => { x = clamp(x); return x * x * (3 - 2 * x); };
  window.clamp = clamp; window.ease = ease; window.smooth = smooth;

  // ---- 时间表达式："L05" 行起点，"L05e" 行终点，可带 +0.4 / -0.2，也可是纯数字 ----
  function T(expr) {
    if (expr == null) return null;
    if (typeof expr === 'number') return expr;
    const m = /^([A-Za-z]\w*?)(e?)([+-]\d+(\.\d+)?)?$/.exec(expr.trim());
    if (!m) { const v = parseFloat(expr); if (isNaN(v)) throw new Error('bad time ' + expr); return v; }
    let L = TL.lines[m[1]], end = m[2] === 'e';
    if (!L && m[2] === 'e') { L = TL.lines[m[1] + 'e']; end = false; }
    if (!L) throw new Error('unknown line ' + m[1] + ' in ' + expr);
    return (end ? L.e : L.s) + (m[3] ? parseFloat(m[3]) : 0);
  }
  window.T = T;

  // ---- 星空 ----
  function rng(seed) { let s = seed >>> 0; return () => { s = (s + 0x6D2B79F5) | 0; let t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  const R = rng(19210);
  const stars = [];
  for (let i = 0; i < 520; i++) {
    const depth = Math.pow(R(), 2.2);               // 0 远 … 1 近
    stars.push({ x: R() * W, y: R() * (H + 200), d: depth, r: 0.55 + depth * 1.5 + (R() < 0.03 ? 0.9 : 0),
      a: 0.22 + R() * 0.5 + depth * 0.2, ph: R() * 6.283, tw: 0.25 + R() * 0.7, warm: R() });
  }
  const nebulae = [
    { x: 250, y: 420, r: 760, c: [46, 62, 118], a: 0.30, vx: 1.2, vy: -0.5 },
    { x: 900, y: 1250, r: 820, c: [70, 48, 104], a: 0.22, vx: -0.9, vy: -0.7 },
    { x: 480, y: 1780, r: 700, c: [28, 66, 92], a: 0.24, vx: 0.6, vy: -0.9 },
  ];
  function drawSky(t) {
    const c = document.getElementById('sky'), x = c.getContext('2d');
    const g = x.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, '#05070f'); g.addColorStop(0.55, '#080b17'); g.addColorStop(1, '#0a0c18');
    x.globalCompositeOperation = 'source-over'; x.fillStyle = g; x.fillRect(0, 0, W, H);
    x.globalCompositeOperation = 'lighter';
    for (const n of nebulae) {
      const nx = n.x + n.vx * t, ny = n.y + n.vy * t;
      const rg = x.createRadialGradient(nx, ny, 0, nx, ny, n.r);
      const breathe = 1 + 0.08 * Math.sin(t * 0.05 + n.x);
      rg.addColorStop(0, `rgba(${n.c[0]},${n.c[1]},${n.c[2]},${n.a * breathe})`);
      rg.addColorStop(0.5, `rgba(${n.c[0]},${n.c[1]},${n.c[2]},${n.a * 0.35 * breathe})`);
      rg.addColorStop(1, 'rgba(0,0,0,0)');
      x.fillStyle = rg; x.fillRect(0, 0, W, H);
    }
    // 慢速推移：整体向左下漂，近处的星稍快一点（视差）
    for (const s of stars) {
      const sp = 1.6 + s.d * 5.2;                    // px/s
      let px = (s.x - t * sp * 0.42) % W; if (px < 0) px += W;
      let py = (s.y + t * sp * 0.9) % (H + 200) - 100;
      const tw = 1 - 0.22 * s.tw * (0.5 + 0.5 * Math.sin(t * (0.35 + s.tw) + s.ph));
      const a = s.a * tw;
      const col = s.warm > 0.82 ? `rgba(255,232,200,${a})` : (s.warm < 0.2 ? `rgba(196,214,255,${a})` : `rgba(236,238,246,${a})`);
      x.fillStyle = col; x.beginPath(); x.arc(px, py, s.r, 0, 6.283); x.fill();
      if (s.r > 2.1) { const hg = x.createRadialGradient(px, py, 0, px, py, s.r * 5); hg.addColorStop(0, `rgba(210,222,255,${a * 0.28})`); hg.addColorStop(1, 'rgba(0,0,0,0)'); x.fillStyle = hg; x.fillRect(px - 12, py - 12, 24, 24); }
    }
    x.globalCompositeOperation = 'source-over';
  }

  // ---- 场景与元素 ----
  let scenes = [], hooks = {};
  window.registerAnim = (id, fn) => { hooks[id] = fn; };
  function init() {
    scenes = [...document.querySelectorAll('.scene')].map(sc => {
      const s = T(sc.dataset.in), e = T(sc.dataset.out);
      const els = [...sc.querySelectorAll('.el')].map(el => ({
        el, s: T(el.dataset.in ?? sc.dataset.in), e: el.dataset.out ? T(el.dataset.out) : null,
        fx: el.dataset.fx || 'rise', dur: parseFloat(el.dataset.dur || '0.7'), max: parseFloat(el.dataset.max || '1'),
        dimAt: el.dataset.dim ? T(el.dataset.dim) : null, dimTo: parseFloat(el.dataset.dimto || '0.38'),
      }));
      return { sc, s, e, els, id: sc.id };
    });
  }
  const FIN = 0.55, FOUT = 0.40;
  window.seek = function (t) {
    drawSky(t);
    for (const S of scenes) {
      const vis = t >= S.s - 0.001 && t < S.e;
      if (!vis) { S.sc.style.opacity = 0; S.sc.style.display = 'none'; continue; }
      S.sc.style.display = 'block';
      const o = Math.min(smooth((t - S.s) / FIN), smooth((S.e - t) / FOUT));
      S.sc.style.opacity = o.toFixed(4);
      for (const E of S.els) {
        let p = ease((t - E.s) / E.dur), op = p * E.max;
        if (E.e != null) op *= smooth((E.e - t) / 0.4);
        if (E.dimAt != null) op *= 1 - (1 - E.dimTo) * smooth((t - E.dimAt) / 0.6);
        E.el.style.opacity = op.toFixed(4);
        if (E.fx === 'rise') E.el.style.transform = `translateY(${((1 - p) * 26).toFixed(2)}px)`;
        else if (E.fx === 'left') E.el.style.transform = `translateX(${((1 - p) * -30).toFixed(2)}px)`;
        else if (E.fx === 'scale') E.el.style.transform = `scale(${(0.94 + 0.06 * p).toFixed(4)})`;
      }
      if (hooks[S.id]) hooks[S.id](t, t - S.s, S);
    }
    // 字幕
    const sub = document.getElementById('sub');
    let cur = null;
    for (const s of TL.subs) if (t >= s.s && t < s.e) { cur = s; break; }
    if (cur) { sub.textContent = cur.text; sub.style.opacity = Math.min(clamp((t - cur.s) / 0.10), clamp((cur.e - t) / 0.10)).toFixed(3); }
    else sub.style.opacity = 0;
    // 片头片尾整体黑场淡入淡出
    const fade = document.getElementById('fade');
    fade.style.opacity = Math.max(1 - smooth(t / 1.0), smooth((t - (TL.duration - 1.2)) / 1.2)).toFixed(4);
  };
  window.initEngine = async function () { await document.fonts.ready; init(); return true; };
})();
