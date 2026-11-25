// 入口：加载资源、分发场景、全局叠加层
'use strict';
const SCN = { s1: sc1, s2: sc2, s3: sc3, s4: sc4, s5: sc5, s6: sc6, s7: sc7 };
const ORDER = ['s1', 's2', 's3', 's4', 's5', 's6', 's7'];
let OFF, offx;
function loadImg(src) { return new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = src; }); }
async function boot() {
  try {
    for (const [f, fam, w] of [['NotoSerifSC', 'Noto Serif SC', '200 900'], ['NotoSansSC', 'Noto Sans SC', '100 900']]) {
      const ff = new FontFace(fam, `url(../fonts/${f}.ttf)`, { weight: w });
      await ff.load(); document.fonts.add(ff);
    }
    TL = await (await fetch('timeline.json?' + Date.now())).json();
    for (const l of TL.lines) LINE[l.id] = l;
    GEO = await (await fetch('../assets/geo.json')).json();
    IMG.macro = await loadImg('../assets/macro.jpg'); IMG.region = await loadImg('../assets/region.jpg'); IMG.land = await loadImg('../assets/macro_land.png');
    cv = document.getElementById('c'); ctx = cv.getContext('2d');
    OFF = document.createElement('canvas'); OFF.width = W; OFF.height = H; offx = OFF.getContext('2d');
    buildTerritory(); initTorches(); initCamp(); initArmy();
    // 预先测量一次字体
    ctx.font = `800 40px ${SERIF}`; ctx.fillText('淝水', -100, -100); ctx.font = `700 40px ${SANS}`; ctx.fillText('淝水', -100, -100);
    window.READY = true;
  } catch (e) { window.BOOTERR = String(e && e.stack || e); }
}
function drawScene(sid, t) { ctx.save(); const r = SCN[sid](t) || {}; ctx.restore(); return r; }
function render(t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  // 当前段落与转场（段落起点前后 0.45 s 交叉淡化）
  let idx = 0; for (let i = 0; i < ORDER.length; i++) if (t >= TL.secs[ORDER[i]].start - 0.45) idx = i;
  const sid = ORDER[idx];
  const st = TL.secs[sid].start - 0.45, xf = idx > 0 ? clamp((t - st) / 0.9) : 1;
  let flags;
  if (xf < 1) {
    const main = ctx; drawScene(ORDER[idx - 1], t);
    ctx = offx; ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
    flags = drawScene(sid, t); ctx = main;
    ctx.save(); ctx.globalAlpha = sstep(xf); ctx.drawImage(OFF, 0, 0); ctx.restore();
  } else flags = drawScene(sid, t);
  vignette(0.5);
  quoteCard(t);
  chapterCard(t);
  subtitle(t);
  badges(t, flags || {});
  grain(t, 0.05);
}
window.frameJPEG = (t, q = 0.93) => { render(t); return cv.toDataURL('image/jpeg', q).split(',')[1]; };
window.renderAt = t => render(t);
boot();
// 封面：火把长龙 + 倒下的大旗 + 标题
window.coverJPEG = () => {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1;
  torchLine(3.0, 0.55);
  banner(520, 1080, 620, C.qinD, '秦', 2.0, { rot: -0.55 });
  const g = ctx.createLinearGradient(0, 1150, 0, H); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(0.35, 'rgba(0,0,0,0.75)'); g.addColorStop(1, 'rgba(0,0,0,0.92)');
  ctx.fillStyle = g; ctx.fillRect(0, 1150, W, H - 1150);
  txt('淝水之战', W / 2, 300, { size: 150, weight: 900, color: C.cream, glow: 'rgba(0,0,0,1)', blur: 40, ls: 16 });
  txt('公元 383 年', W / 2, 440, { size: 52, weight: 700, color: C.gold, glow: 'rgba(0,0,0,1)', ls: 10 });
  txt('几十万大军', W / 2, 1420, { size: 120, weight: 900, color: C.cream, glow: 'rgba(0,0,0,1)', blur: 30 });
  txt('为什么一句话就散了？', W / 2, 1570, { size: 96, weight: 900, color: C.jin, glow: 'rgba(0,0,0,1)', blur: 30 });
  txt('历史的关键一局', W / 2, 1720, { size: 44, weight: 700, color: rgba(C.gold, 0.95), ls: 12 });
  vignette(0.4);
  return cv.toDataURL('image/png').split(',')[1];
};
