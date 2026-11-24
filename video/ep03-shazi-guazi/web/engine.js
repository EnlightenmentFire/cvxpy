/* Deterministic timeline engine: everything is a pure function of t (seconds). */
const W = 1080, H = 1920;
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, p) => a + (b - a) * p;
const EASE = {
  lin: p => p,
  out: p => 1 - Math.pow(1 - p, 3),
  out5: p => 1 - Math.pow(1 - p, 5),
  io: p => p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2,
  back: p => { const c = 1.6; return 1 + (c + 1) * Math.pow(p - 1, 3) + c * Math.pow(p - 1, 2); },
  in: p => p * p * p,
};
const pr = (t, t0, d, e = 'out') => EASE[e](clamp((t - t0) / d));
/* seeded rng for deterministic scatter */
function RNG(seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }

/* DOM helper */
function h(tag, attrs, ...kids) {
  const svgTags = ['svg', 'path', 'circle', 'rect', 'line', 'g', 'ellipse', 'polygon', 'polyline', 'text', 'defs', 'clipPath', 'tspan', 'pattern', 'mask'];
  const e = svgTags.includes(tag) ? document.createElementNS('http://www.w3.org/2000/svg', tag) : document.createElement(tag);
  if (attrs) for (const k in attrs) {
    if (k === 'style' && typeof attrs[k] === 'object') Object.assign(e.style, attrs[k]);
    else if (k === 'html') e.innerHTML = attrs[k];
    else if (k === 'cls') e.setAttribute('class', attrs[k]);
    else e.setAttribute(k, attrs[k]);
  }
  for (const k of kids.flat()) if (k != null) e.append(k.nodeType ? k : document.createTextNode(k));
  return e;
}
/* absolute-positioned div */
function box(x, y, w, hh, cls, style, html) {
  const e = h('div', { cls: 'abs ' + (cls || ''), style: Object.assign({ left: x + 'px', top: y + 'px' }, w != null ? { width: w + 'px' } : {}, hh != null ? { height: hh + 'px' } : {}, style || {}) });
  if (html != null) e.innerHTML = html;
  return e;
}

/* cue helpers (narration timeline) */
const L = id => { const l = TL.lines[id]; if (!l) throw new Error('no line ' + id); return l; };
const c = (id, f = 0) => { const l = L(id); return l.s + (l.e - l.s) * f; };
const ce = id => L(id).e;
/* time when a word is spoken inside a line (chunk-accurate, proportional inside chunk) */
function cw(id, word, nth = 0) {
  const l = L(id); let seen = 0;
  for (const ch of l.chunks) {
    let i = -1, from = 0;
    while ((i = ch.t.indexOf(word, from)) >= 0) {
      if (seen === nth) return ch.s + (ch.e - ch.s) * (i / Math.max(1, ch.t.length));
      seen++; from = i + 1;
    }
  }
  console.warn('cw miss', id, word); return l.s;
}

const ENGINE = {
  scenes: [], cur: null,
  /* def: id, t0, t1, cls, fadeIn, fadeOut, build(S) */
  scene(def) { this.scenes.push(def); },
  init() {
    const host = document.getElementById('scenes');
    for (const d of this.scenes) {
      d.root = h('div', { cls: 'scene ' + (d.cls || '') });
      d.cam = h('div', { cls: 'cam' }); d.root.append(d.cam);
      d.anims = []; d.fns = [];
      host.append(d.root);
      const S = makeS(d);
      d.build(S);
    }
    this.sub = document.getElementById('subtxt'); this.subBox = document.getElementById('subs');
    this.grain = document.getElementById('grain'); this.black = document.getElementById('black');
  },
  render(t) {
    for (const d of this.scenes) {
      const fi = d.fadeIn ?? 0.45, fo = d.fadeOut ?? 0.45;
      const vis = t >= d.t0 && t < d.t1;
      d.root.style.display = vis ? 'block' : 'none';
      if (!vis) continue;
      let o = 1;
      if (fi > 0) o = Math.min(o, clamp((t - d.t0) / fi));
      if (fo > 0) o = Math.min(o, clamp((d.t1 - t) / fo));
      d.root.style.opacity = o;
      if (d.camSpec) {
        const p = clamp((t - d.t0) / (d.t1 - d.t0)), k = d.camSpec;
        d.cam.style.transform = `translate(${lerp(k.x0 || 0, k.x1 || 0, p)}px,${lerp(k.y0 || 0, k.y1 || 0, p)}px) scale(${lerp(k.s0 || 1, k.s1 || 1, p)})`;
      }
      for (const a of d.anims) applyAnim(a, t);
      for (const f of d.fns) f(t);
    }
    // subtitles
    let txt = '';
    for (const s of TL.subs) if (t >= s.s - 0.04 && t < s.e + 0.10) { txt = s.t; break; }
    if (txt !== this._sub) { this.sub.textContent = txt; this._sub = txt; this.subBox.style.visibility = txt ? 'visible' : 'hidden'; }
    // grain offset (changes every 2 frames)
    const fr = Math.floor(t * 15), r = RNG(fr * 7919 + 13);
    this.grain.style.transform = `translate(${Math.floor(r() * 256)}px,${Math.floor(r() * 256)}px)`;
    // final black
    this.black.style.opacity = clamp((t - (TL.total - 0.9)) / 0.5);
  }
};

function applyAnim(a, t) {
  const st = { o: 1, x: 0, y: 0, s: 1, r: 0, sx: 1, sy: 1 };
  const p = EASE[a.e || 'out'](clamp((t - a.at) / (a.d || 0.6)));
  for (const k in a.from) st[k] = lerp(a.from[k], st[k], p);
  if (a.out != null && t > a.out) {
    const q = EASE[a.oe || 'io'](clamp((t - a.out) / (a.od || 0.4)));
    const to = a.to || { o: 0 };
    for (const k in to) st[k] = lerp(st[k], to[k], q);
  }
  const el = a.el;
  el.style.opacity = st.o * (a.maxO ?? 1);
  if (a.clip) { // wipe reveal from left / top
    const pc = (1 - p) * 100;
    el.style.clipPath = a.clip === 'x' ? `inset(0 ${pc}% 0 0)` : a.clip === 'y' ? `inset(0 0 ${pc}% 0)` : `inset(0 0 0 ${pc}%)`;
  }
  el.style.transform = `${a.base || ''} translate(${st.x}px,${st.y}px) rotate(${st.r}deg) scale(${st.s * st.sx},${st.s * st.sy})`;
}

function makeS(d) {
  const S = {
    d, root: d.cam, t0: d.t0, t1: d.t1,
    add(...els) { for (const e of els.flat()) d.cam.append(e); return els[0]; },
    over(...els) { for (const e of els.flat()) d.root.append(e); return els[0]; }, // not affected by camera
    cam(spec) { d.camSpec = spec; },
    a(el, spec) { d.anims.push(Object.assign({ el }, spec)); return el; },
    fadeUp(el, at, out, extra) { return S.a(el, Object.assign({ at, d: 0.65, from: { o: 0, y: 36 }, out }, extra || {})); },
    fade(el, at, out, extra) { return S.a(el, Object.assign({ at, d: 0.5, from: { o: 0 }, out }, extra || {})); },
    pop(el, at, out, extra) { return S.a(el, Object.assign({ at, d: 0.5, e: 'back', from: { o: 0, s: 0.6 }, out }, extra || {})); },
    slam(el, at, out, extra) { return S.a(el, Object.assign({ at, d: 0.32, e: 'out5', from: { o: 0, s: 1.9 }, out }, extra || {})); },
    wipe(el, at, dur, out, extra) { return S.a(el, Object.assign({ at, d: dur || 0.7, e: 'io', from: {}, clip: 'x', out }, extra || {})); },
    on(fn) { d.fns.push(fn); },
    /* stroke draw for svg path/line */
    draw(el, at, dur, len) {
      const Ln = len || (el.getTotalLength ? el.getTotalLength() : 1000);
      el.style.strokeDasharray = Ln; d.fns.push(t => { el.style.strokeDashoffset = Ln * (1 - pr(t, at, dur, 'io')); });
      return el;
    },
    count(el, at, dur, a, b, fmt) { d.fns.push(t => { const v = lerp(a, b, pr(t, at, dur, 'io')); el.textContent = fmt ? fmt(v) : Math.round(v); }); return el; },
    /* typewriter: reveal characters between at..end */
    type(el, at, end) {
      const txt = el.textContent; el.textContent = '';
      const spans = [...txt].map(ch => { const s = h('span', null, ch); s.style.opacity = 0; el.append(s); return s; });
      d.fns.push(t => { const n = (t - at) / Math.max(0.01, end - at) * spans.length;
        spans.forEach((s, i) => { s.style.opacity = clamp(n - i + 0.2, 0, 1); }); });
      return el;
    },
  };
  return S;
}
