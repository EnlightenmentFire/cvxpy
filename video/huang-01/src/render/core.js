// 核心：时间、缓动、文字、字幕层、章节卡。所有画面都是 T（秒）的纯函数，逐帧确定。
const W = 1080, H = 1920;
const COL = { bg: '#0A0C0B', panel: '#111513', line: '#27302B', ink: '#E8EDE9', mute: '#8C968F',
  g: '#4BF58E', gd: '#1F7A4B', gdd: '#11301F', warn: '#FF7A59' };
let T = 0;
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, u) => a + (b - a) * u;
const eo = u => 1 - Math.pow(1 - clamp(u), 3);
const eio = u => { u = clamp(u); return u < .5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2; };
const rnd = i => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const f1 = x => (Math.round(x * 10) / 10);

const countCh = s => s.replace(/[^一-鿿A-Za-z0-9]/g, '').length || 1;
const LN = TL.lines;
const CUE = {}; LN.forEach(l => { if (l.cue) CUE[l.cue] = l; });
const SC = {}; TL.scenes.forEach(s => SC[s.name] = s);
const C = n => { if (!(n in CUE)) throw new Error('no cue ' + n); return CUE[n].start; };
const CE = n => CUE[n].end;
// 从 cue 开始淡入
const on = (n, d = .6, off = 0) => eo((T - C(n) - off) / d);
// cue a 到 cue b 之间可见
const win = (a, b, d = .5) => on(a, d) * (1 - eo((T - C(b) + .15) / .35));
// 某一行第 k 个字幕分段开始的时刻（和字幕换屏同步）
const CH = (n, k) => { const l = CUE[n], ps = l.zh.split('|'), tot = ps.reduce((s, p) => s + countCh(p), 0);
  let acc = 0; for (let i = 0; i < k; i++) acc += countCh(ps[i]); return l.start + (l.end - l.start) * acc / tot; };
const pc = (n, k, d = .5) => eo((T - CH(n, k)) / d);
// 线性进度
const prog = (n, d, off = 0) => clamp((T - C(n) - off) / d);

// SVG 小工具
const tx = (x, y, size, s, o = {}) =>
  `<text x="${x}" y="${y}" font-size="${size}" fill="${o.f || COL.ink}" font-weight="${o.w || 700}" ` +
  `font-family="${o.ff || 'Noto Sans SC'}" text-anchor="${o.a || 'start'}" ` +
  `${o.o !== undefined ? `opacity="${f1(o.o * 100) / 100}"` : ''} ${o.ls ? `letter-spacing="${o.ls}"` : ''} ${o.x || ''}>${s}</text>`;
const mono = (x, y, size, s, o = {}) => tx(x, y, size, s, Object.assign({ ff: 'Plex, Noto Sans SC', w: 500, f: COL.mute, ls: 1 }, o));
// 淡入 + 上移
const G = (u, inner, dy = 22) => u <= 0.001 ? '' :
  `<g opacity="${u.toFixed(3)}" transform="translate(0 ${((1 - u) * dy).toFixed(1)})">${inner}</g>`;
const O = (u, inner) => u <= 0.001 ? '' : `<g opacity="${u.toFixed(3)}">${inner}</g>`;
const glow = inner => `<g filter="url(#glow)">${inner}</g>`;

const DEFS = `
<defs>
  <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">
    <feGaussianBlur stdDeviation="7" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="glow2" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur stdDeviation="18" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="soft"><feGaussianBlur stdDeviation="26"/></filter>
  <linearGradient id="wall" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0c0f0d"/><stop offset="1" stop-color="#131816"/></linearGradient>
  <linearGradient id="fadeDown" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0A0C0B" stop-opacity="0"/><stop offset="1" stop-color="#0A0C0B" stop-opacity="1"/></linearGradient>
  <radialGradient id="gpool" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#4BF58E" stop-opacity=".34"/><stop offset="1" stop-color="#4BF58E" stop-opacity="0"/></radialGradient>
  <radialGradient id="lamp" cx=".5" cy="0" r="1"><stop offset="0" stop-color="#ffe9b8" stop-opacity=".30"/><stop offset=".7" stop-color="#ffe9b8" stop-opacity="0"/></radialGradient>
  <linearGradient id="night" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b1420"/><stop offset="1" stop-color="#121a1c"/></linearGradient>
  <pattern id="grid" width="36" height="36" patternUnits="userSpaceOnUse"><path d="M36 0H0V36" fill="none" stroke="#1a211d" stroke-width="1"/></pattern>
</defs>`;

// ─── 字幕层（中文译文 + 英文原话 + 出处），放在安全区内
// 一行放不下时，在最靠近中间的标点后面折行
const zhW = s => [...s].reduce((w, ch) => w + (ch.charCodeAt(0) > 0x2e80 || '，。：；？！、“”「」《》'.includes(ch) ? 1 : 0.55), 0);
function breakZh(s) {
  if (s.includes('¦')) return s.replace('¦', '<br>');
  if (zhW(s) <= 16.6) return s;
  let best = -1, bd = 1e9; const half = zhW(s) / 2; let w = 0;
  [...s].forEach((ch, i) => { w += zhW(ch); if ('，。：；？！、'.includes(ch) && i < s.length - 1) { const d = Math.abs(w - half); if (d < bd) { bd = d; best = i; } } });
  if (best < 0 || bd > half * 0.55) return s;   // 没有合适的标点，就交给浏览器均衡折行
  return s.slice(0, best + 1) + '<br>' + s.slice(best + 1);
}
function subtitle() {
  const l = LN.find(l => T >= l.start - 0.08 && T < l.end + 0.22);
  if (!l) return '';
  const a = clamp((T - (l.start - 0.08)) / 0.18) * clamp((l.end + 0.22 - T) / 0.18);
  const parts = l.zh.split('|'); const tot = parts.reduce((s, p) => s + countCh(p), 0);
  let acc = 0, cur = parts[parts.length - 1]; const u = (T - l.start) / (l.end - l.start);
  for (const p of parts) { acc += countCh(p) / tot; if (u < acc) { cur = p; break; } }
  let zh = breakZh(cur);
  if (l.q) { // 引语：整句加引号
    const i = parts.indexOf(cur);
    zh = (i === 0 ? '「' : '') + breakZh(cur) + (i === parts.length - 1 ? '」' : '');
  }
  let h = `<div class="sub" style="opacity:${a.toFixed(3)}">`;
  if (!l.big && l.scene !== 'title') h += `<div class="zh${l.q ? ' q' : ''}">${zh}</div>`;
  if (l.en) h += `<div class="en"${l.big ? ' style="margin-top:40px;font-size:30px;line-height:40px"' : ''}>“${l.en}”</div>`;
  if (l.src) h += `<div class="src">${l.src}</div>`;
  return h + '</div>';
}

// ─── 页眉：系列名 + 章节 + 进度
const CHAP = {
  diner: ['一', '方向', '他们押对了什么'], octo: ['二', '章鱼', '第一颗芯片为什么卖不动'],
  rule: ['三', '规则', '微软定了标准'], dilemma: ['四', '两难', '做完会死，不做马上死'],
  sega: ['五', '第一次认错', '对客户'], inner: ['六', '第二次认错', '对自己人'],
  time: ['七', '第三次认错', '对“完美”'], result: ['八', '结果', '四个月，一百万片'], end: ['', '', ''],
};
function header(sc) {
  if (sc.name === 'cold' || sc.name === 'title') return '';
  const ch = CHAP[sc.name] || ['', '', ''];
  const a = clamp((T - sc.start - 1.3) / .5) * clamp((sc.end - T) / .4);
  const p = T / TL.duration;
  return O(a, mono(70, 262, 22, '黄仁勋的商业决断 · 01', { f: '#6f7a73' }) +
    (ch[0] ? tx(1010, 263, 24, `第${ch[0]}章 · ${ch[1]}`, { a: 'end', f: COL.g, w: 700, ls: 2 }) : '') +
    `<rect x="70" y="282" width="940" height="2" fill="#1b221e"/><rect x="70" y="282" width="${f1(940 * p)}" height="2" fill="${COL.gd}"/>`);
}
// 章节卡：每场开头 1.4 秒
function chapterCard(sc) {
  const ch = CHAP[sc.name]; if (!ch || !ch[0]) return '';
  const lt = T - sc.start; if (lt > 1.7) return '';
  const a = clamp(lt / .3) * clamp((1.55 - lt) / .35);
  const w = eo(lt / .9) * 300;
  return `<rect width="${W}" height="${H}" fill="#070908" opacity="${clamp((1.7 - lt) / .4).toFixed(3)}"/>` + O(a,
    mono(540, 770, 40, `第${ch[0]}章`, { a: 'middle', f: COL.g, ls: 14 }) +
    `<rect x="${540 - w / 2}" y="820" width="${w}" height="3" fill="${COL.g}"/>` +
    tx(540, 950, 104, ch[1], { a: 'middle', w: 900, ls: 6 }) +
    tx(540, 1036, 36, ch[2], { a: 'middle', w: 500, f: COL.mute, ls: 3 }));
}

const SCENES = {};
// 每段小结开头的提示语，和旁白“这说明什么？”同步
const SO = n => G(on(n, .35), mono(540, 452, 30, '这说明什么？', { a: 'middle', f: COL.g, ls: 6 }) + `<rect x="500" y="478" width="80" height="3" fill="${COL.gd}"/>`, 10);
const SHIFT = 60;   // 画面整体下移，给视频号顶部遮挡区让位
// 全屏底色（含网格），向上多画一截，配合整体下移
const BG = (c = '#090b0a', grid = .55) => `<rect x="0" y="-120" width="${W}" height="${H + 120}" fill="${c}"/>` +
  (grid ? `<rect x="0" y="-120" width="${W}" height="${H + 120}" fill="url(#grid)" opacity="${grid}"/>` : '');
const DIM = a => a <= 0 ? '' : `<rect x="0" y="-120" width="${W}" height="${H + 120}" fill="#060807" opacity="${(Math.round(a * 100) / 100)}"/>`;
window.renderFrame = function (t) {
  T = t;
  const sc = TL.scenes.find(s => t >= s.start && t < s.end) || TL.scenes[TL.scenes.length - 1];
  const body = SCENES[sc.name] ? SCENES[sc.name](sc) : '';
  // 场间淡入淡出
  const fin = clamp((t - sc.start) / .35), fout = sc.name === 'end' ? clamp((TL.duration - t) / 1.2) : clamp((sc.end - t) / .3);
  const dim = 1 - Math.min(fin, fout);
  document.getElementById('stage').innerHTML =
    `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${DEFS}<g transform="translate(0 ${SHIFT})">${body}</g>` +
    `<rect width="${W}" height="${H}" fill="#060807" opacity="${dim.toFixed(3)}"/>` +
    `${chapterCard(sc)}<g transform="translate(0 ${SHIFT})">${header(sc)}</g></svg><div class="vig"></div>${subtitle()}`;
};
