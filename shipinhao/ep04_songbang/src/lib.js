// 迷你时间轴动画库：所有状态都是 t 的纯函数，可任意 seek。
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const E = {
  lin: x => x,
  out: x => 1 - Math.pow(1 - x, 3),
  in: x => x * x * x,
  io: x => (x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
  back: x => { const c = 1.70158; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); },
};
const lerp = (a, b, p) => a + (b - a) * p;

const D = window.TL_DATA;
const LN = {}; D.lines.forEach(l => (LN[l.id] = l));
const at = id => LN[id].start;           // 一句开始
const en = id => LN[id].end;             // 一句结束
const cl = (id, k) => LN[id].clauses[k].start;   // 第 k 个分句开始
const ce = (id, k) => LN[id].clauses[k].end;

function h(html, parent) {
  const t = document.createElement('template'); t.innerHTML = html.trim();
  const el = t.content.firstElementChild; if (parent) parent.appendChild(t.content); return el;   // 多个并列节点会一并挂上，返回第一个
}
function chars(el) {           // 把文字拆成逐字 span（保留内部标签）
  const out = [];
  const walk = n => {
    if (n.nodeType === 3) {
      const f = document.createDocumentFragment();
      for (const ch of n.textContent) { const s = document.createElement('span'); s.textContent = ch; s.style.display = 'inline-block'; if (ch === ' ') s.style.width = '.3em'; f.appendChild(s); out.push(s); }
      n.parentNode.replaceChild(f, n);
    } else if (n.nodeType === 1 && n.tagName !== 'BR') Array.from(n.childNodes).forEach(walk);
  };
  Array.from(el.childNodes).forEach(walk); return out;
}

class TLn {
  constructor() { this.tr = []; this.init = new Map(); this.fns = []; }
  set(el, props) { const s = this.init.get(el) || {}; Object.assign(s, props); this.init.set(el, s); return this; }
  to(el, props, t0, d = .6, e = E.out) {
    if (Array.isArray(el) || el instanceof NodeList) { el.forEach(x => this.to(x, props, t0, d, e)); return this; }
    if (!this.init.has(el)) this.init.set(el, {});
    for (const k in props) this.tr.push({ el, k, t0, d, v: props[k], e });
    return this;
  }
  stagger(els, props, t0, each = .05, d = .4, e = E.out) { els.forEach((el, i) => this.to(el, props, t0 + i * each, d, e)); return this; }
  // 逐字出现：在 [t0,t1] 内均匀显现
  type(els, t0, t1, d = .22) { const n = els.length; els.forEach((el, i) => { this.set(el, { o: 0 }); this.to(el, { o: 1 }, t0 + (t1 - t0) * i / Math.max(1, n), d, E.lin); }); return this; }
  fn(t0, d, f, e = E.lin) { this.fns.push({ t0, d, f, e }); return this; }
  // 快捷：淡入上移
  in(el, t0, d = .6, dy = 36) { if (Array.isArray(el)) { el.forEach(x => this.in(x, t0, d, dy)); return this; } const s = this.init.get(el) || {}; this.set(el, { o: 0, y: (s.y || 0) + dy }); return this.to(el, { o: 1, y: (s.y || 0) }, t0, d); }
  out(el, t0, d = .4) { return this.to(el, { o: 0 }, t0, d, E.in); }
  build() { this.tr.sort((a, b) => a.t0 - b.t0); this.by = new Map(); for (const r of this.tr) { if (!this.by.has(r.el)) this.by.set(r.el, []); this.by.get(r.el).push(r); } }
  apply(t) {
    for (const [el, init] of this.init) {
      const s = Object.assign({ o: 1, x: 0, y: 0, s: 1, r: 0 }, init);
      const trs = this.by.get(el) || [];
      for (const r of trs) { if (t < r.t0) break; const p = r.e(clamp((t - r.t0) / Math.max(1e-6, r.d))); s[r.k] = lerp(s[r.k] === undefined ? 0 : s[r.k], r.v, p); }
      const st = el.style;
      st.opacity = s.o.toFixed(4);
      st.transform = `translate(${s.x.toFixed(2)}px,${s.y.toFixed(2)}px) rotate(${s.r.toFixed(3)}deg) scale(${(s.sx !== undefined ? s.sx : s.s).toFixed(4)},${(s.sy !== undefined ? s.sy : s.s).toFixed(4)})`;
      if (s.dash !== undefined) { const L = el._len || (el._len = el.getTotalLength()); st.strokeDasharray = L; st.strokeDashoffset = (L * (1 - s.dash)).toFixed(2); }
      if (s.clipx !== undefined) st.clipPath = `inset(-20px ${(100 * (1 - s.clipx)).toFixed(3)}% -20px -20px)`;
      if (s.clipy !== undefined) st.clipPath = `inset(-20px -20px ${(100 * (1 - s.clipy)).toFixed(3)}% -20px)`;
      if (s.w !== undefined) st.width = s.w.toFixed(2) + 'px';
      if (s.hgt !== undefined) st.height = s.hgt.toFixed(2) + 'px';
      if (s.num !== undefined) el.textContent = Math.round(s.num);
      if (s.blur !== undefined) st.filter = s.blur > .05 ? `blur(${s.blur.toFixed(2)}px)` : 'none';
    }
    for (const f of this.fns) { const p = clamp((t - f.t0) / Math.max(1e-6, f.d)); f.f(f.e(p), t); }
  }
}

const SCENES = [];
// scene(name, t0, t1, build(root, tl, t0, t1))  root 为 .scene 容器；fade: 入/出淡变时长
function scene(name, t0, t1, build, opt = {}) {
  SCENES.push({ name, t0, t1, build, opt });
}
function mountScenes(stage) {
  for (const sc of SCENES) {
    const root = h(`<div class="scene" data-name="${sc.name}"></div>`, stage);
    const tl = new TLn();
    sc.root = root; sc.tl = tl;
    const cam = sc.build(root, tl, sc.t0, sc.t1) || root.querySelector('.cam');
    if (cam && !sc.opt.nocam) { tl.set(cam, { s: 1 }); tl.to(cam, { s: sc.opt.zoom || 1.045 }, sc.t0, sc.t1 - sc.t0 + .5, E.lin); }
    tl.build();
  }
}
const FADE = .32;
function seekScenes(t) {
  for (const sc of SCENES) {
    const fi = sc.opt.fi === undefined ? FADE : sc.opt.fi, fo = sc.opt.fo === undefined ? FADE : sc.opt.fo;
    const vis = t >= sc.t0 - 1e-6 && t < sc.t1 + fo;
    sc.root.style.display = vis ? 'block' : 'none';
    if (!vis) continue;
    let o = 1;
    if (fi > 0) o = Math.min(o, clamp((t - sc.t0) / fi));
    if (fo > 0 && t > sc.t1) o = Math.min(o, 1 - clamp((t - sc.t1) / fo));
    sc.root.style.opacity = o.toFixed(4);
    sc.root.style.zIndex = t > sc.t1 ? 2 : 1;
    sc.tl.apply(t);
  }
}

// ── 通用小部件 ──
const bust = (c = '#c9a45c', size = 96) => `<svg width="${size}" height="${size}" viewBox="0 0 96 96"><circle cx="48" cy="48" r="46" fill="none" stroke="${c}" stroke-width="2.5"/><clipPath id="bc"><circle cx="48" cy="48" r="44"/></clipPath><g clip-path="url(#bc)" fill="${c}"><circle cx="48" cy="38" r="15"/><path d="M14 98c0-24 15-38 34-38s34 14 34 38z"/></g></svg>`;
function who(parent, name, title, top, left = 90) {
  return h(`<div class="who" style="top:${top}px;left:${left}px">${bust()}<div class="bar"></div><div class="nm">${name}</div><div class="ti">${title}</div></div>`, parent);
}
function term(parent, word, def, top) {
  return h(`<div class="term" style="top:${top}px"><span class="k">名词</span><span class="t">${word}</span><div class="d">${def}</div></div>`, parent);
}
function so(parent, text, top) {
  return h(`<div class="so" style="top:${top}px"><div class="k">这说明什么</div><div class="t">${text}</div></div>`, parent);
}
function src(parent, text, top, left = 90, dark = false) {
  return h(`<div class="src${dark ? ' dark' : ''}" style="top:${top}px;left:${left}px">${text}</div>`, parent);
}

// 字幕：把分句合并成 ≤ max 字的行
function buildSubs(max = 19) {
  const subs = [];
  const strip = s => s.replace(/[，。；：、]+$/g, '').replace(/^[，。；：、]+/g, '');
  for (const l of D.lines) {
    let cur = null;
    for (const c of l.clauses) {
      const txt = c.text;
      const hard = /[。？！；：]$/.test(cur ? cur.text : '');
      if (cur && !hard && (cur.text + txt).replace(/[「」《》]/g, '').length <= max) { cur.text += txt; cur.end = c.end; }
      else { if (cur) subs.push(cur); cur = { text: txt, start: c.start, end: c.end }; }
    }
    if (cur) subs.push(cur);
  }
  for (let i = 0; i < subs.length; i++) {
    subs[i].text = strip(subs[i].text);
    const nx = subs[i + 1];
    subs[i].end = nx ? Math.min(subs[i].end + .28, nx.start - .02) : subs[i].end + .5;
    subs[i].start -= .04;
  }
  return subs;
}
