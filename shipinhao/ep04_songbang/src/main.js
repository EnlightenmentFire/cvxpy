// 装配：场景 + 顶部时间轴 + 字幕
const stage = document.getElementById('stage');
mountScenes(stage);
const SUBS = buildSubs();
const subEl = h(`<div id="sub" style="z-index:50"></div>`, stage);
const strip = (typeof buildStrip === 'function') ? buildStrip(stage) : null;
window.TOTAL = D.total;
window.seek = function (t) {
  seekScenes(t);
  let s = null; for (const x of SUBS) { if (t >= x.start && t < x.end) { s = x; break; } }
  subEl.textContent = s ? s.text : '';
  if (s) { const n = s.text.length; subEl.style.fontSize = (n > 19 ? Math.floor(46 * 19 / n) : 46) + 'px'; }
  if (strip) strip(t);
};
window.ready = document.fonts.ready.then(() => { seek(0); return true; });
