// ───────── compose: scenes + overlays + subtitles ─────────
let TL, canvas, ctx;
const NUM = ['壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖', '拾', '拾壹', '拾贰'];
const cnChars = s => (s.match(/[一-鿿]/g) || []).length;

function setup() {
  TL = window.TL; canvas = document.getElementById('c'); ctx = canvas.getContext('2d');
  TL.lines.forEach(l => { (SEGL[l.seg] = SEGL[l.seg] || []).push(l); l.pages = quotePages(l); });
  paperTex(); blotTex(1); blotTex(2); blotTex(3);
}
// group a line's chunks into pages of <=2 rows (rows <= 13 chars)
function quotePages(l) {
  if (l.kind !== 'q') return null;
  const parts = l.text.match(/[^，。；：？！、]+[，。；：？！、]*/g) || [l.text];
  const rows = []; let cur = '';
  parts.forEach(p => { if (cur && (cnChars(cur) + cnChars(p) > 12 || (/[。！？]$/.test(cur) && cnChars(cur) >= 5))) { rows.push(cur); cur = p; } else cur += p; }); if (cur) rows.push(cur);
  const pages = []; for (let i = 0; i < rows.length; i += 2) pages.push(rows.slice(i, i + 2));
  const tot = cnChars(l.text); let acc = 0;
  return pages.map(pg => { const n = cnChars(pg.join('')); const o = { rows: pg, s: l.s + (l.e - l.s) * acc / tot, e: l.s + (l.e - l.s) * (acc + n) / tot, n }; acc += n; return o; });
}

function overlay(ctx) {
  ctx.save(); ctx.globalCompositeOperation = 'soft-light'; ctx.globalAlpha = .38; ctx.drawImage(paperTex(), 0, 0, W, H); ctx.restore();
  const g = ctx.createRadialGradient(W / 2, H * .46, H * .28, W / 2, H * .5, H * .72);
  g.addColorStop(0, 'rgba(3,5,8,0)'); g.addColorStop(1, 'rgba(3,5,8,.5)'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  // keep platform UI zones quiet
  let b = ctx.createLinearGradient(0, 1500, 0, H); b.addColorStop(0, 'rgba(4,6,9,0)'); b.addColorStop(.5, 'rgba(4,6,9,.7)'); b.addColorStop(1, 'rgba(4,6,9,.92)'); ctx.fillStyle = b; ctx.fillRect(0, 1500, W, H - 1500);
  b = ctx.createLinearGradient(0, 0, 0, 230); b.addColorStop(0, 'rgba(4,6,9,.8)'); b.addColorStop(1, 'rgba(4,6,9,0)'); ctx.fillStyle = b; ctx.fillRect(0, 0, W, 230);
}
function chapter(ctx, t, seg) {
  const i = TL.segs.indexOf(seg); if (i === 0 && t < ln('s01', 0).s) return;
  const a = win(t, seg.s + .5, seg.e - .2, .8, .5) * .9; if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = C.red; ctx.fillRect(64, 246, 5, 44); ctx.restore();
  htext(ctx, NUM[i], 84, 269, 34, C.pale, { align: 'left', alpha: a, weight: 700, outline: 4 });
  htext(ctx, seg.name, 84 + NUM[i].length * 36 + 16, 269, 30, '#9aabb5', { align: 'left', alpha: a * .95, weight: 500, spacing: 4, outline: 4 });
}
function showCard(ctx, t) {
  TL.lines.forEach(l => {
    if (!l.show || l.noCard) return; const a = win(t, l.s + .25, l.e + Math.min(l.gap, 1.2), .6, .5); if (a <= 0) return;
    const y = l.showY || 1196; const str = '「' + l.show + '」'; let size = 40; const n = [...str].length; if (n * size > 900) size = Math.floor(900 / n);
    ctx.save(); ctx.globalAlpha = a * .5; ctx.fillStyle = '#04070a'; const bw = Math.min(980, n * size + 90); ctx.beginPath(); ctx.roundRect(540 - bw / 2, y - 44, bw, 118, 6); ctx.fill(); ctx.restore();
    htext(ctx, str, 540, y, size, '#d9c48f', { alpha: a, weight: 600, reveal: sstep(l.s + .25, l.s + 1.6, t), outline: 5 });
    htext(ctx, '—— ' + l.show_src, 540 + Math.min(450, n * size / 2), y + 46, 25, '#8fa0aa', { alpha: a * .95, align: 'right', weight: 500, outline: 4 });
  });
}
function subtitles(ctx, t) {
  const l = TL.lines.find(l => t >= l.s - .05 && t < l.e + Math.min(.45, l.gap * .6)); if (!l) return;
  if (l.kind === 'q') {
    const pg = l.pages.find((p, i) => t < p.e || i === l.pages.length - 1); const first = pg === l.pages[0], last = pg === l.pages[l.pages.length - 1];
    const a = Math.min(first ? sstep(l.s - .05, l.s + .25, t) : sstep(pg.s - .05, pg.s + .15, t), last ? 1 - sstep(l.e + Math.min(.45, l.gap * .6) - .25, l.e + Math.min(.45, l.gap * .6), t) : 1);
    const size = 62, lh = 88, y0 = 1348 - (pg.rows.length - 1) * lh / 2; let acc = 0;
    ctx.save(); ctx.globalAlpha = a * .55; ctx.fillStyle = '#04070a'; ctx.beginPath(); ctx.roundRect(60, y0 - 62, 960, pg.rows.length * lh + 82, 8); ctx.fill();
    ctx.globalAlpha = a; ctx.fillStyle = C.yellowDim; ctx.fillRect(60, y0 - 62, 4, pg.rows.length * lh + 82); ctx.restore();
    pg.rows.forEach((r, i) => { const n = cnChars(r); const rv = clamp(((t - pg.s) / Math.max(.2, pg.e - pg.s) * pg.n - acc + 1.5) / n);
      htext(ctx, r, 540, y0 + i * lh, size, '#ecd9a4', { alpha: a, weight: 700, reveal: rv * 1.02, spacing: 3, outline: 6 }); acc += n; });
    htext(ctx, l.src, 1006, y0 + pg.rows.length * lh - 8, 26, '#9aa9b2', { alpha: a * .95, align: 'right', weight: 500, outline: 4 });
  } else {
    const ch = l.chunks.find((c, i) => t < c.e || i === l.chunks.length - 1);
    const a = Math.min(sstep(ch.s - .06, ch.s + .1, t), ch === l.chunks[l.chunks.length - 1] ? 1 - sstep(l.e + Math.min(.45, l.gap * .6) - .2, l.e + Math.min(.45, l.gap * .6), t) : 1);
    htext(ctx, ch.t, 540, 1385, 56, '#f1ede2', { alpha: a, weight: 600, spacing: 2, outline: 8, outlineColor: 'rgba(3,5,8,.92)' });
  }
}
function renderAt(t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.filter = 'none';
  ctx.fillStyle = C.night0; ctx.fillRect(0, 0, W, H);
  const seg = TL.segs.find(s => t >= s.s && t < s.e) || TL.segs[TL.segs.length - 1], i = TL.segs.indexOf(seg);
  ctx.save(); SC[seg.id](ctx, t, seg); ctx.restore();
  let f = Math.max(i === 0 ? 1 - sstep(0, 2.5, t) : 1 - sstep(seg.s, seg.s + .7, t), i === TL.segs.length - 1 ? sstep(seg.e - 1.6, seg.e - .2, t) : sstep(seg.e - .7, seg.e, t));
  if (f > 0) { ctx.fillStyle = `rgba(4,6,9,${f})`; ctx.fillRect(0, 0, W, H); }
  overlay(ctx); chapter(ctx, t, seg); showCard(ctx, t); subtitles(ctx, t);
}
window.setup = setup; window.renderAt = renderAt;
