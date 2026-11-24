/* Shared visual components */
const C = { ink: '#1a1410', paper: '#e8ddc6', kraft: '#ba9460', red: '#c8372b', red2: '#a8281f', gold: '#d2a03c', dim: 'rgba(232,221,198,.62)', blue: '#5a6f7a' };

function person(size, color, extra) {
  const s = h('svg', { viewBox: '0 0 40 52', width: size * 40 / 52, height: size, style: Object.assign({ position: 'absolute' }, extra || {}) },
    h('circle', { cx: 20, cy: 10, r: 9, fill: color }),
    h('path', { d: 'M4,52 C4,32 8,23 20,23 C32,23 36,32 36,52 Z', fill: color }));
  return s;
}
function coin(size, frac, color) { // frac: 1 = full, .5 = half coin
  const col = color || C.gold;
  const s = h('svg', { viewBox: '0 0 100 100', width: size, height: size, style: { position: 'absolute' } });
  const g = h('g', frac < 1 ? { 'clip-path': 'inset(0 50% 0 0)' } : null,
    h('circle', { cx: 50, cy: 50, r: 47, fill: col, stroke: 'rgba(0,0,0,.35)', 'stroke-width': 2 }),
    h('circle', { cx: 50, cy: 50, r: 37, fill: 'none', stroke: 'rgba(0,0,0,.28)', 'stroke-width': 2 }),
    h('rect', { x: 39, y: 39, width: 22, height: 22, fill: 'none', stroke: 'rgba(0,0,0,.4)', 'stroke-width': 3 }));
  s.append(g);
  if (frac < 1) s.append(h('circle', { cx: 50, cy: 50, r: 47, fill: 'none', stroke: 'rgba(0,0,0,.25)', 'stroke-width': 1.5, 'stroke-dasharray': '4 5' }));
  return s;
}
function header(S, right, dark) {
  const e = h('div', { cls: 'hdr', html: `<span>改革开放系列 · 03 · 企业家线</span><span>${right || ''}</span>` });
  if (dark === false) e.style.color = C.ink;
  S.over(e); S.fade(e, S.t0 + 0.2);
  return e;
}
function nameTag(S, x, y, name, role, at, out, color) {
  const e = box(x, y, null, null, 'ntag', color ? { color } : null, `<div class="nm">${name}</div><div class="bar"></div><div class="rl">${role}</div>`);
  S.add(e); S.a(e, { at, d: 0.6, from: { o: 0, x: -30 }, out });
  return e;
}
function chip(S, y, term, def, at, out) {
  const e = h('div', { cls: 'chip', style: { top: y + 'px' }, html: `<div class="tm">${term}</div><div class="df">${def}</div>` });
  S.add(e); S.a(e, { at, d: 0.55, from: { o: 0, y: 40 }, out, od: 0.35 });
  return e;
}
function src(S, y, text, at, out, color) {
  const e = h('div', { cls: 'src', style: { top: y + 'px', color: color || 'inherit' }, html: text });
  S.add(e); S.fade(e, at, out);
  return e;
}
/* "这说明什么" overlay; line id gives timing */
function takeaway(S, id, html) {
  const l = L(id), at = l.s - 0.25;
  const t = h('div', { cls: 'tk' }, h('div', { cls: 'lab' }, '这说明什么'), h('div', { cls: 'rule' }), h('div', { cls: 'tx', html }));
  S.over(t); S.a(t, { at, d: 0.45, from: { o: 0 } });
  S.a(t.children[1], { at: at + 0.15, d: 0.7, e: 'io', from: { sx: 0 } });
  S.a(t.children[2], { at: Math.min(l.chunks[1] ? l.chunks[1].s - 0.15 : at + 0.5, at + 1.6), d: 0.7, from: { o: 0, y: 30 } });
  return t;
}
/* chapter card scene */
function chapter(no, title, t0, t1, sub) {
  ENGINE.scene({ id: 'chap' + no, t0, t1, cls: 'bg-dark chap', fadeIn: 0.35, fadeOut: 0.35, build(S) {
    S.cam({ s0: 1.0, s1: 1.04 });
    const n = h('div', { cls: 'no' }, no), ln = h('div', { cls: 'ln' }), ti = h('div', { cls: 'ti' }, title), yr = h('div', { cls: 'yr' }, sub || '');
    S.add(n, ln, ti, yr);
    S.a(n, { at: t0 + 0.1, d: 0.6, from: { o: 0, y: 40 } });
    S.a(ln, { at: t0 + 0.25, d: 0.7, e: 'io', from: { sx: 0 } });
    S.a(ti, { at: t0 + 0.35, d: 0.7, from: { o: 0, y: 30 } });
    S.a(yr, { at: t0 + 0.6, d: 0.6, from: { o: 0 } });
  } });
}
/* paper document mock (示意) */
function docMock(x, y, w, hh, o) {
  const d = box(x, y, w, hh, 'doc');
  d.innerHTML = `<div class="rh" style="font-size:${o.hs || 64}px;padding-top:${o.pt || 46}px;${o.hls ? 'letter-spacing:' + o.hls + 'px;' : ''}">${o.head}</div>
    <div style="text-align:center;font-family:Song;font-weight:600;font-size:27px;margin:14px 0 16px;letter-spacing:2px">${o.no}</div>
    <div class="rr"></div>
    <div style="font-family:Song;font-weight:900;font-size:${o.ts || 40}px;line-height:1.35;text-align:center;padding:26px 56px 6px">${o.title}</div>
    <div style="text-align:center;font-family:Song;font-weight:500;font-size:26px;opacity:.8">${o.date || ''}</div>
    <div class="body" style="padding:18px 62px 0;font-family:Song;font-weight:600;font-size:${o.bs || 37}px;line-height:1.62;text-align:justify">${o.body}</div>
    <div class="demo" style="right:20px;bottom:16px">示意图</div>`;
  return d;
}
const bars = (n, ws) => Array.from({ length: n }, (_, i) => `<div class="bar" style="width:${(ws && ws[i]) || 100}%"></div>`).join('');
/* newspaper mock (版面示意) */
function paperMock(x, y, w, hh, o) {
  const d = box(x, y, w, hh, 'doc bg-news');
  d.style.background = 'url("../assets/newsprint.jpg")';
  d.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:flex-end;padding:30px 40px 10px">
      <div style="font-family:Song;font-weight:900;font-size:${o.ms || 84}px;letter-spacing:10px;color:${o.mc || C.red2}">${o.mast}</div>
      <div style="font-family:Hei;font-weight:500;font-size:26px;text-align:right;line-height:1.4">${o.date}</div></div>
    <div style="height:6px;background:${C.ink};margin:0 40px"></div><div style="height:2px;background:${C.ink};margin:5px 40px 0"></div>
    <div class="body" style="padding:22px 40px 0">${o.body}</div>
    <div class="demo" style="right:20px;bottom:16px">版面示意</div>`;
  return d;
}
const cols = (n, lines, hgt) => `<div style="display:flex;gap:22px">${Array.from({ length: n }, () => `<div style="flex:1">${bars(lines)}</div>`).join('')}</div>`;
