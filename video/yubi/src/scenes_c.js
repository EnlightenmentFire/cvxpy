// 场景（下）：柒 敕勒歌、捌 主心骨、玖 二十六年后、收尾、片尾，以及总调度
'use strict';

// ---------------- 柒 · 敕勒歌 ----------------
function tentScene(t, a, lamp = 1) {     // 穹庐：圆顶帐篷剪影，帐内灯光；帐外落雪
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#0a0d12'); g.addColorStop(1, '#101215'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.globalAlpha = a;
  const cx = 540, by = 1240, R = 360;
  const fl = 0.85 + 0.15 * Math.sin(t * 7.3) * Math.sin(t * 3.1 + 1);
  const rg = ctx.createRadialGradient(cx, by - 120, 10, cx, by - 120, 520); rg.addColorStop(0, `rgba(255,170,90,${0.55 * fl * lamp})`); rg.addColorStop(1, 'rgba(255,120,60,0)');
  ctx.fillStyle = '#1b1611'; ctx.beginPath(); ctx.moveTo(cx - R, by); ctx.lineTo(cx - R, by - 200); ctx.quadraticCurveTo(cx - R + 20, by - 520, cx, by - 560); ctx.quadraticCurveTo(cx + R - 20, by - 520, cx + R, by - 200); ctx.lineTo(cx + R, by); ctx.closePath(); ctx.fill();
  ctx.save(); ctx.clip(); ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = 'rgba(60,44,30,0.8)'; ctx.lineWidth = 3; for (let k = -6; k <= 6; k++) { ctx.beginPath(); ctx.moveTo(cx + k * 55, by); ctx.quadraticCurveTo(cx + k * 40, by - 400, cx, by - 560); ctx.stroke(); }
  ctx.restore();
  ctx.fillStyle = `rgba(255,190,120,${0.85 * fl * lamp})`; ctx.fillRect(cx - 60, by - 180, 120, 180);
  ctx.fillStyle = '#0c0b0a'; ctx.fillRect(0, by, W, H - by);
  ctx.restore();
}
function grassland(t, a) {               // 草原空镜（示意，不是玉璧当地）
  if (a <= 0) return; ctx.save(); ctx.globalAlpha = a;
  const g = ctx.createLinearGradient(0, 0, 0, 1100); g.addColorStop(0, '#2b3a4a'); g.addColorStop(0.6, '#6f7c84'); g.addColorStop(1, '#a39b84'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, 1100);
  // 穹庐般的天：一道弧
  ctx.strokeStyle = 'rgba(230,236,240,0.18)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.ellipse(540, 1100, 900, 820, 0, Math.PI, 2 * Math.PI); ctx.stroke();
  // 远山（阴山示意）
  ctx.fillStyle = '#4a5560'; ctx.beginPath(); ctx.moveTo(0, 980); for (let x = 0; x <= W; x += 30) ctx.lineTo(x, 930 - 60 * Math.sin(x * 0.006 + 1) - 30 * Math.sin(x * 0.017)); ctx.lineTo(W, 1100); ctx.lineTo(0, 1100); ctx.fill();
  ctx.fillStyle = '#5e6a52'; ctx.fillRect(0, 1060, W, H - 1060);
  // 风吹草低：成片的草，随风成波；草低处露出牛羊
  const wave = x => Math.sin(x * 0.006 - t * 1.6) * 0.5 + Math.sin(x * 0.013 - t * 2.3) * 0.5;
  const show = P(t, A('s7', 4) + 5.0, 1.0);
  for (let i = 0; i < 26; i++) { const x = 60 + i * 38 + 8 * hash(i, 2), y = 1090 + 70 * hash(i, 3); const low = clamp(-wave(x) * 1.3); if (low * show > 0.25) { ctx.globalAlpha = a * low * show; ctx.fillStyle = '#e8e2d2'; ctx.beginPath(); ctx.ellipse(x, y - 8, 12, 8, 0, 0, 7); ctx.fill(); ctx.fillRect(x - 8, y - 2, 3, 9); ctx.fillRect(x + 6, y - 2, 3, 9); ctx.globalAlpha = a; } }
  ctx.lineWidth = 2;
  for (let r = 0; r < 7; r++) {
    const y0 = 1080 + r * 95, n = 70;
    for (let i = 0; i < n; i++) {
      const x = (i + 0.5 * hash(i, r)) * (W / n); const w = wave(x + r * 40); const h = (60 + 50 * hash(i, r + 9)) * (1 + r * 0.25), bend = 22 + 40 * clamp(w);
      ctx.strokeStyle = `rgba(${150 + 30 * hash(i, r)},${150 + 20 * hash(i, r + 1)},${100 + 10 * r},${0.55 + 0.05 * r})`;
      ctx.beginPath(); ctx.moveTo(x, y0 + h * 0.2); ctx.quadraticCurveTo(x + bend * 0.4, y0 - h * 0.4, x + bend, y0 - h * (0.75 - 0.35 * clamp(w))); ctx.stroke();
    }
  }
  ctx.restore();
}
const LYRIC = ['敕勒川，阴山下。', '天似穹庐，笼盖四野。', '天苍苍，野茫茫，', '风吹草低见牛羊。'];
function sceneS7(t) {
  const s = TL.secs.s7, b = s.body; const T = k => A('s7', k), TE = k => E('s7', k);
  const tTent = T(3) - 0.4, hush = s.hush, tq = T(4), te = TE(4);
  if (t < tTent + 0.8) {      // 撤军；“定功弩”谣言
    const cam = locCam(kf([[s.start, ...kmLL(0, 0.2), 6.0], [tTent + 0.8, ...kmLL(0, 1.0), 9.0]], t));
    drawLocal(cam, { season: 0.95, dim: 0.35 });
    const go = eio(prog(t, b + 0.2, b + 3.4));
    const list = []; for (let i = 0; i < CAMP.length; i += 2) { const c = CAMP[i]; if (c[2] < 0.55) continue; list.push(lk(cam, c[0] + go * (1.5 + 3 * c[3]) * 0.6, c[1] + go * (2.5 + 2 * c[3]))); }
    dots(list, '#10151b', '#9aabbd', 3);
    drawCity(cam);
    bands(0.5, 0.55);
    label('十一月 · 高欢舆疾班师', W / 2, 640, { size: 34, bar: C.xuanL, alpha: fadeIO(t, b + 0.3, T(0) + 4.4, 0.4, 0.4) });
    const ar = fadeIO(t, CK('s7', 0, 1) - 0.1, TE(2) + 0.4, 0.4, 0.4);
    if (ar > 0) { for (let k = 0; k < 3; k++) { const u = ((t * 0.7 + k / 3) % 1); ctx.save(); ctx.globalAlpha = ar * (1 - u) * 0.8; ctx.strokeStyle = '#d7d2c4'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(540, 900, 40 + u * 260, 0, 7); ctx.stroke(); ctx.restore(); } label('军中讹言：丞相中了“定功弩”', 540, 900, { size: 32, bar: '#d7d2c4', alpha: ar }); note('西魏借题发挥 · 史书称之为讹言', 540, 960, ar, 'center'); }
  }
  if (t >= tTent) {
    const al = sstep((t - tTent) / 0.8); ctx.save(); ctx.globalAlpha = al;
    const lamp = 1 - 0.25 * P(t, TE(4) + 1.4, 1.2) + 0.15 * Math.sin(t * 1.3);
    tentScene(t, 1, lamp);
    const gl = fadeIO(t, tq + 0.8, TE(4) + 1.9, 1.6, 1.4);
    grassland(t, gl * 0.92);
    snowfall(t, 0.75 * (1 - gl * 0.5), 220, 13, 0.6);
    // 歌词：竖排，逐句随朗读显现
    const la = fadeIO(t, tq - 0.3, A('s7', 5) + 0.3, 0.5, 0.9);
    if (la > 0) {
      const dur = TE(4) - tq; const shown = (t - tq) / dur * 24 + 1.2; let idx = 0;
      LYRIC.forEach((ln, i) => { const s2 = ln.replace(/[，。]/g, ''); vtext(s2, 900 - i * 120, 300, { size: 70, lh: 84, colw: 120, color: '#fff3d6', shown: shown - idx, alpha: la, stroke: 6, strokeColor: 'rgba(6,6,8,0.7)' }); idx += s2.length; });
      text('—— 《乐府诗集》卷八十六', 990, 1180 - 60, { size: 26, fam: SERIF, wt: 700, align: 'right', alpha: la, stroke: 4, color: C.gold });
      note('其歌本鲜卑语，易为齐言（《乐府诗集》引《乐府广题》）', 90, 1250, la * 0.9, 'left', 22);
    }
    const ai = fadeIO(t, T(3) + 0.2, tq - 0.2, 0.4, 0.4);
    if (ai > 0) { label('勉坐见诸贵 · 使斛律金作《敕勒歌》', W / 2, 640, { size: 30, bar: C.xuanL, alpha: ai }); label('斛律金：敕勒人', W / 2, 1300, { size: 28, bar: C.xuanL, alpha: ai * P(t, CK('s7', 3, 1), 0.4) * (1 - P(t, CK('s7', 3, 3) - 0.3, 0.3)) }); label('高欢家累世北边 · 父居阴山白道南', W / 2, 1300, { size: 28, bar: C.gold, alpha: ai * P(t, CK('s7', 3, 3) - 0.1, 0.3) }); }
    if (gl > 0.3) note('示意：北方草原，不是玉璧当地', 90, 1318, gl * 0.85, 'left', 22);
    const a5 = fadeIO(t, T(5) - 0.2, s.end, 0.4, 0.5);
    if (a5 > 0) { label('神武自和之，哀感流涕', W / 2, 1250, { size: 34, fam: SERIF, wt: 900, bar: C.gold, alpha: a5 }); note('《北齐书·神武纪》', W / 2, 1300, a5, 'center'); }
    ctx.restore();
  }
}

// ---------------- 捌 · 主心骨 ----------------
function sceneS8(t) {
  const s = TL.secs.s8, b = s.body; const T = k => A('s8', k), TE = k => E('s8', k);
  const cam = macCam(kf([[s.start, 112.6, 35.7, 7.4], [TE(1), 112.6, 35.6, 7.2], [T(2) + 1.2, 110.95, 35.6, 2.6], [TE(2), 110.95, 35.6, 2.4], [T(3) + 1.0, 110.0, 35.0, 4.8], [s.end, 110.0, 35.0, 5.0]], t));
  drawMacro(cam, 0.32); realms(cam, 1, 1, 1, 0.5); drawRivers(cam, 0.8);
  const off = P(t, CK('s8', 0, 1) + 0.4, 1.2);
  const [jx, jy] = city(cam, ...G.jinyang, '晋阳', { color: off > 0.5 ? '#6a6f75' : C.xuanL, capital: 1, dy: -44, pulse: t < CK('s8', 0, 1) + 0.4 ? t : 0 });
  const a0 = fadeIO(t, b - 0.1, T(1) + 0.4, 0.4, 0.4);
  if (a0 > 0) { label('547 年正月 · 高欢卒于晋阳 · 年五十二', W / 2, 560, { size: 30, bar: C.xuanL, alpha: a0 }); if (off > 0) { ctx.save(); ctx.globalAlpha = a0 * off; ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.beginPath(); ctx.arc(jx, jy, 30, 0, 7); ctx.fill(); ctx.restore(); } }
  // 侯景：河南
  const ah = fadeIO(t, CK('s8', 0, 2) - 0.2, TE(1) + 0.4, 0.4, 0.4);
  if (ah > 0) { const [hx, hy] = mw(cam, ...G.yingchuan); ctx.save(); ctx.globalAlpha = ah; ctx.fillStyle = 'rgba(255,200,120,0.18)'; ctx.beginPath(); ctx.arc(hx, hy, 90, 0, 7); ctx.fill(); ctx.restore(); label('侯景 · 镇守河南', hx - 120, hy - 160, { size: 30, bar: '#ffcf8a', alpha: ah }); const [ox, oy] = mw(cam, 112.7, 33.85); arrow(hx - 20, hy + 10, ox, oy, { color: '#ffcf8a', w: 8, head: 22, frac: P(t, CK('s8', 0, 2) + 0.3, 0.9), alpha: ah }); label('高欢死后五天 · 据河南叛', hx - 120, hy - 104, { size: 28, bar: '#ffcf8a', alpha: ah * P(t, CK('s8', 0, 2) + 0.8, 0.4) }); note('《资治通鉴》卷一百六十', hx - 120, hy - 60, ah, 'center'); }
  const a1 = fadeIO(t, T(1) - 0.1, TE(1) + 0.4, 0.4, 0.4); if (a1 > 0) text('东魏的主心骨', W / 2, 520, { size: 70, fam: SERIF, wt: 900, align: 'center', alpha: a1, stroke: 10, color: '#d0dae4' });
  // 西魏这边
  const [yx, yy] = mw(cam, ...G.yubi); nail(yx, yy, 1.2, 1, 0.8);
  const a2 = fadeIO(t, T(2) - 0.1, TE(2) + 0.4, 0.4, 0.4);
  if (a2 > 0) {
    ctx.save(); ctx.globalAlpha = a2; rrect(60, 262, 960, 300, 10); ctx.fillStyle = 'rgba(14,11,8,0.88)'; ctx.fill(); ctx.fillStyle = C.red; ctx.fillRect(60, 262, 8, 300); ctx.restore();
    text('韦孝宽 · 骠骑大将军 · 建忠郡公', 100, 320, { size: 38, fam: SERIF, wt: 900, alpha: a2, stroke: 0 });
    text('时人以王思政为知人', 100, 400, { size: 38, fam: SERIF, wt: 900, alpha: a2 * P(t, CK('s8', 2, 1) - 0.1, 0.4), stroke: 0, color: C.gold });
    text('—— 《资治通鉴》卷一百五十九', 990, 405, { size: 24, fam: SERIF, wt: 700, align: 'right', alpha: a2 * P(t, CK('s8', 2, 1), 0.4), stroke: 0, color: C.gold });
    text('保定初（561）· 玉璧置勋州', 100, 490, { size: 34, fam: SERIF, wt: 900, alpha: a2 * P(t, CK('s8', 2, 2) - 0.1, 0.4), stroke: 0, color: '#ff9a7c' });
    label('勋州', yx + 30, yy - 50, { size: 34, fam: SERIF, wt: 900, bar: C.gold, alpha: a2 * P(t, CK('s8', 2, 2), 0.4), align: 'left' });
  }
  // 一百二十八年前 / 这一次
  const a3 = fadeIO(t, T(3) - 0.1, s.end, 0.4, 0.4);
  if (a3 > 0) {
    city(cam, ...G.changan, '长安', { color: C.red, capital: 1, dy: 46, alpha: a3 });
    ctx.save(); ctx.globalAlpha = a3; rrect(60, 262, 960, 310, 10); ctx.fillStyle = 'rgba(14,11,8,0.9)'; ctx.fill(); ctx.restore();
    const r1 = P(t, T(3) + 0.1, 0.4), r2 = P(t, CK('s8', 3, 1) - 0.1, 0.4);
    text('418 年 · 长安', 100, 320, { size: 32, wt: 700, alpha: a3 * r1, stroke: 0, color: '#9aa0a5' });
    text('关中，被留守的人自己弄丢', 100, 378, { size: 40, fam: SERIF, wt: 900, alpha: a3 * r1, stroke: 0, color: '#b9c0c6' });
    text('546 年 · 玉璧', 100, 450, { size: 32, wt: 700, alpha: a3 * r2, stroke: 0, color: '#ff9a7c' });
    text('关中的东大门，被关中人自己守住', 100, 508, { size: 40, fam: SERIF, wt: 900, alpha: a3 * r2, stroke: 0, color: '#ffd2c2' });
  }
  bands(0.45, 0.55); compass(990, 640, 0.8);
}

// ---------------- 玖 · 二十六年后 ----------------
function timelineBar(t, a, u) {
  if (a <= 0) return; ctx.save(); ctx.globalAlpha = a;
  const x0 = 120, x1 = 960, y = 640; ctx.strokeStyle = 'rgba(244,234,214,0.5)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(x1, y); ctx.stroke();
  ctx.strokeStyle = C.gold; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(x0, y); ctx.lineTo(lerp(x0, x1, u), y); ctx.stroke(); ctx.restore();
  text('546', x0, y - 30, { size: 34, fam: SERIF, wt: 900, align: 'center', alpha: a }); text(String(Math.round(lerp(546, 572, u))), x1, y - 30, { size: 34, fam: SERIF, wt: 900, align: 'center', alpha: a * clamp(u * 3), color: C.gold });
}
const SONG1 = '百升飞上天，明月照长安', SONG2 = '高山不推自崩，槲树不扶自竖';
function sceneS9(t) {
  const s = TL.secs.s9, b = s.body; const T = k => A('s9', k), TE = k => E('s9', k);
  const songOn = t > T(3) - 0.5 && t < TE(6) + 0.4;
  const cam = macCam(kf([[s.start, 112.4, 35.9, 6.4], [TE(1), 112.4, 35.9, 6.0], [T(2) + 1.4, 112.6, 35.8, 5.2], [TE(6), 112.6, 35.8, 5.0], [T(7) + 1.2, 112.6, 35.9, 5.4], [T(9), 112.6, 35.9, 5.6], [TE(9) - 1.0, 112.2, 35.6, 6.6], [s.end, 112.2, 35.6, 6.8]], t));
  drawMacro(cam, 0.34); realms(cam, 1, 1, 1, 0.4, ['北 周', '北 齐', '陈']); drawRivers(cam, 0.7);
  const [yx, yy] = mw(cam, ...G.yubi); nail(yx, yy, 1.1, 1);
  const [ex, ey] = city(cam, ...G.ye, '邺', { color: C.xuanL, capital: 1, sub: '北齐都城', dy: -48 });
  city(cam, ...G.changan, '长安', { color: C.red, capital: 1, sub: '北周都城', dy: 46 });
  bands(0.5, 0.55);
  timelineBar(t, fadeIO(t, b - 0.2, T(1) + 0.3, 0.4, 0.4), eio(prog(t, b, b + 2.0)));
  note('疆界示意', 64, 1318, 0.8);
  // 斛律光
  const a1 = fadeIO(t, T(1) - 0.1, T(3) - 0.2, 0.4, 0.4);
  const dead = P(t, CK('s9', 8, 1), 1.0);
  const card = (al, gray) => { if (al <= 0) return; ctx.save(); ctx.globalAlpha = al; rrect(60, 262, 960, 230, 10); ctx.fillStyle = 'rgba(14,11,8,0.9)'; ctx.fill(); ctx.fillStyle = gray ? '#555' : C.xuanL; ctx.fillRect(60, 262, 8, 230); ctx.restore(); const c = gray ? '#77797b' : C.cream; text('斛律光', 100, 330, { size: 70, fam: SERIF, wt: 900, alpha: al, stroke: 0, color: c }); text('字明月 · 北齐第一名将', 400, 336, { size: 34, wt: 700, alpha: al, stroke: 0, color: gray ? '#6c6e70' : '#b9c8d8' }); text('父 斛律金 —— 当年唱《敕勒歌》的人', 100, 430, { size: 32, fam: SERIF, wt: 700, alpha: al, stroke: 0, color: gray ? '#6c6e70' : C.gold }); };
  card(a1, false);
  // 童谣：从玉璧飘进邺城
  const a2 = fadeIO(t, CK('s9', 2, 1) - 0.2, TE(7) + 0.3, 0.4, 0.5);
  if (a2 > 0) {
    const n = 26; for (let i = 0; i < n; i++) { const u = ((t - CK('s9', 2, 1)) * 0.35 + i / n) % 1; if (t < CK('s9', 2, 1)) continue; const x = lerp(yx, ex, u), y = lerp(yy, ey, u) - Math.sin(u * Math.PI) * 160; text((SONG1 + SONG2).replace(/，/g, '')[i % 22], x, y, { size: 28, fam: SERIF, wt: 900, align: 'center', alpha: a2 * Math.sin(u * Math.PI) * 0.9, color: '#ffd2c2', stroke: 3 }); }
    label('间谍 → 邺城', (yx + ex) / 2, (yy + ey) / 2 - 220, { size: 28, bar: C.red, alpha: a2 * (songOn ? 0 : 1) });
  }
  // 两首童谣：竖排大字 + 圈出关键字
  const sA = fadeIO(t, T(3) - 0.4, TE(4) + 0.3, 0.4, 0.4), sB = fadeIO(t, T(5) - 0.4, TE(6) + 0.3, 0.4, 0.4);
  const drawSong = (str, al, t0, t1, keys, notes) => {
    if (al <= 0) return; ctx.save(); ctx.globalAlpha = al; ctx.fillStyle = 'rgba(10,9,8,0.8)'; ctx.fillRect(0, 230, W, 1080); ctx.restore();
    const shown = (t - t0) / (t1 - t0) * str.length + 1; const parts = str.split('，');
    let idx = 0; const pos = {};
    parts.forEach((p, i) => { [...p].forEach((ch, j) => { const x = 680 - i * 280, y = 340 + j * 108; const a2 = clamp(shown - idx) * al; idx++; const hl = keys.includes(ch) && t > t1 - 0.2; if (hl && !pos[ch]) pos[ch] = [x, y]; text(ch, x, y, { size: 94, fam: SERIF, wt: 900, align: 'center', alpha: a2, stroke: 0, color: hl ? '#ff9a7c' : '#fff3d6' }); }); idx++; });
    keys.forEach((k, i) => { const p = pos[k]; if (!p) return; const ka = al * P(t, t1 + 0.1 + i * 0.7, 0.4); ctx.save(); ctx.globalAlpha = ka; ctx.strokeStyle = C.red; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(p[0], p[1], 62, 0, 7); ctx.stroke(); ctx.restore();
      label(notes[i], W / 2, 1080 + i * 72, { size: 32, fam: SERIF, wt: 900, bar: C.red, alpha: ka }); });
    text('—— 《北齐书·斛律光传》', 990, 1260, { size: 26, fam: SERIF, wt: 700, align: 'right', alpha: al, stroke: 0, color: C.gold });
  };
  drawSong(SONG1, sA, T(3), TE(3), ['升', '月'], ['百升 = 一斛 → “斛”律', '明月 = 斛律光的字']);
  drawSong(SONG2, sB, T(5), TE(5), ['高', '槲'], ['高山 → 北齐皇帝的高家', '槲（hú）→ 斛']);
  // 祖珽：同一个人
  const a7 = fadeIO(t, CK('s9', 7, 2) - 0.3, TE(7) + 0.4, 0.4, 0.4);
  if (a7 > 0) {
    ctx.save(); ctx.globalAlpha = a7; rrect(60, 262, 960, 240, 10); ctx.fillStyle = 'rgba(14,11,8,0.9)'; ctx.fill(); ctx.fillStyle = C.xuanL; ctx.fillRect(60, 262, 8, 240); ctx.restore();
    text('祖珽（字孝征）', 100, 320, { size: 52, fam: SERIF, wt: 900, alpha: a7, stroke: 0 });
    text('546 · 玉璧城下劝降', 100, 400, { size: 34, wt: 700, alpha: a7, stroke: 0, color: '#b9c8d8' });
    text('572 · 邺城续谣，传到皇帝耳边', 100, 455, { size: 34, wt: 700, alpha: a7 * P(t, CK('s9', 7, 2) + 0.4, 0.4), stroke: 0, color: '#d0dae4' });
    ctx.save(); ctx.globalAlpha = a7 * 0.8; ctx.setLineDash([8, 10]); ctx.strokeStyle = C.xuanL; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(yx, yy); ctx.quadraticCurveTo((yx + ex) / 2, yy - 320, ex, ey); ctx.stroke(); ctx.restore();
  }
  // 斛律光之死：卡片熄灭
  const a8 = fadeIO(t, T(8) - 0.1, TE(8) + 0.4, 0.4, 0.5);
  if (a8 > 0) { card(a8 * (1 - 0.3 * dead), dead > 0.5); label('572 年 · 诬以谋反 · 族灭', W / 2, 560, { size: 30, bar: '#77797b', alpha: a8 * dead }); }
  // 576/577：北周武帝过玉璧、入邺
  const a9 = fadeIO(t, T(9) - 0.2, s.end, 0.4, 0.4);
  if (a9 > 0) {
    const [cx2, cy2] = mw(cam, ...G.changan), [px, py] = mw(cam, ...G.pingyang);
    const u1 = P(t, T(9) + 0.3, 1.4), u2 = P(t, CK('s9', 9, 2), 2.0);
    curveArrow([[cx2, cy2], [lerp(cx2, yx, 0.5), lerp(cy2, yy, 0.5) - 40], [yx, yy - 10]], { color: C.red, w: 8, head: 22, frac: u1, alpha: a9, glow: C.redG });
    if (u1 > 0.95) { const ag = P(t, T(9) + 1.7, 0.5); ctx.save(); ctx.globalAlpha = a9 * ag * (0.6 + 0.4 * Math.sin(t * 4)); ctx.strokeStyle = C.gold; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(yx, yy - 18, 46, 0, 7); ctx.stroke(); ctx.restore(); label('576 · 观御敌之所，深叹羡之', yx + 20, yy + 70, { size: 28, bar: C.gold, alpha: a9 * ag, align: 'left' }); }
    curveArrow([[yx + 10, yy], [px, py], [lerp(px, ex, 0.6), lerp(py, ey, 0.6) - 60], [ex, ey + 10]], { color: C.red, w: 8, head: 22, frac: u2, alpha: a9, glow: C.redG });
    if (u2 > 0.95) label('577 · 入邺', ex - 20, ey + 64, { size: 30, bar: C.red, alpha: a9, align: 'right' });
  }
}

// ---------------- 收尾 ----------------
function sceneS10(t) {
  const s = TL.secs.s10; const T = k => A('s10', k);
  const cam = locCam(kf([[s.start, ...kmLL(0, 0.0), 3.0], [s.end, ...kmLL(0, 0.4), 9.0]], t));
  drawLocal(cam, { season: 1, snow: 0.35, dim: 0.45 }); drawCity(cam, { alpha: 0.9 });
  snowfall(t, 0.5, 160, 21, 0.5);
  ctx.fillStyle = 'rgba(8,7,6,0.35)'; ctx.fillRect(0, 0, W, H);
  const big = (str, a, y, col) => text(str, W / 2, y, { size: 70, fam: SERIF, wt: 900, align: 'center', alpha: a, ls: 4, stroke: 12, color: col || C.cream });
  const fade = k => (t > T(2) + 2.2 ? 1 - P(t, T(2) + 2.2, 0.8) * 0.0 : 1);
  big('高欢，输在城下', P(t, T(0) - 0.15, 0.5) * (t > T(1) - 0.2 ? 0.6 : 1), 560, '#b9c8d8');
  big('斛律光，输在自己人手里', P(t, T(1) - 0.15, 0.5) * (t > T(2) - 0.2 ? 0.6 : 1), 700, '#b9c8d8');
  big('韦孝宽两次，都没有出城', P(t, T(2) - 0.15, 0.5), 860, '#ff9a7c');
  const fo = sstep((t - (s.end - 0.8)) / 0.8); if (fo > 0) { ctx.fillStyle = `rgba(9,8,7,${fo})`; ctx.fillRect(0, 0, W, H); }
}
function sceneEnd(t) {
  const s = TL.secs.end; ctx.fillStyle = '#090807'; ctx.fillRect(0, 0, W, H);
  const a = fadeIO(t, s.start, s.end, 0.8, 1.0);
  text('玉 璧', W / 2, 400, { size: 110, fam: SERIF, wt: 900, align: 'center', alpha: a, stroke: 0, ls: 12 });
  text('孤城 · 第二集', W / 2, 500, { size: 30, wt: 700, align: 'center', alpha: a * 0.85, stroke: 0, ls: 10 });
  ctx.fillStyle = `rgba(226,69,46,${a})`; ctx.fillRect(W / 2 - 40, 545, 80, 4);
  const L = [['史料', 1], ['《周书》卷三十一 韦孝宽传、卷十八 王思政传', 0], ['《北齐书》卷一、二 神武纪，卷十七 斛律金、斛律光传', 0], ['卷三十九 祖珽传', 0], ['《资治通鉴》卷一百五十八至一百六十、一百七十一', 0], ['《乐府诗集》卷八十六《敕勒歌》', 0], ['', 0],
    ['说明', 1], ['引文、日期、人数据上列原文；各书数字不一处已注出处', 0], ['城形、楼位、地道走向、器械与人物剪影均为示意', 0], ['疆界为示意；地形据公开高程数据（SRTM）晕渲，河道为今貌', 0], ['旁白为开源语音合成（Qwen3-TTS，按文字描述设计的声音）', 0], ['配乐为开源模型生成（MusicGen）', 0]];
  let y = 640; for (const [s2, h] of L) { if (s2) text(s2, W / 2, y, { size: h ? 34 : 28, fam: h ? SANS : SERIF, wt: 700, align: 'center', alpha: a * (h ? 1 : 0.88), stroke: 0, color: h ? C.gold : C.cream, ls: h ? 10 : 0 }); y += (h ? 34 : 28) + 24; }
}

// ---------------- 总调度 ----------------
function render(t) {
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.shadowBlur = 0; ctx.setLineDash([]);
  const S = TL.secs;
  if (t < S.title.start) sceneCold(t);
  else if (t < S.title.end) sceneTitle(t);
  else if (t < S.s2.start) sceneS1(t);
  else if (t < S.s3.start) sceneS2(t);
  else if (t < S.s4.start) sceneS3(t);
  else if (t < S.s5.start) sceneS4(t);
  else if (t < S.s6.start) sceneS5(t);
  else if (t < S.s7.start) sceneS6(t);
  else if (t < S.s8.start) sceneS7(t);
  else if (t < S.s9.start) sceneS8(t);
  else if (t < S.s10.start) sceneS9(t);
  else if (t < S.end.start) sceneS10(t);
  else sceneEnd(t);
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.shadowBlur = 0;
  chip(t); quotes(t); subtitles(t); chapterCard(t); post(t);
  if (t < 0.25) { ctx.fillStyle = `rgba(9,8,7,${1 - t / 0.25})`; ctx.fillRect(0, 0, W, H); }
}
async function boot() {
  const cv = document.getElementById('c'); ctx = cv.getContext('2d', { alpha: false, willReadFrequently: location.search.includes('sw=1') });
  const j = async u => (await fetch(u)).json();
  [TL, MACRO, LOCAL, RIV, FEN] = await Promise.all([j('timeline.json?' + Date.now()), j('../assets/macro.json'), j('../assets/local.json'), j('../assets/rivers_macro.json'), j('../assets/fen_local.json')]);
  const load = (k, u) => new Promise((res, rej) => { const im = new Image(); im.onload = () => { IMG[k] = im; res(); }; im.onerror = rej; im.src = u; });
  await Promise.all([load('macro', '../assets/macro.jpg'), load('local', '../assets/local.jpg'), load('snow', '../assets/snow_rgba.png')]);
  for (const w of ['900', '700', '500']) { await document.fonts.load(`${w} 40px "Noto Serif SC"`, '玉璧韦孝宽'); await document.fonts.load(`${w} 40px "Noto Sans SC"`, '玉璧韦孝宽'); }
  await document.fonts.ready;
  // 由场景自己呈现的原文（不再弹通用原文卡）
  QUOTE_SKIP = l => (l.sec === 'cold') || (l.sec === 's5' && l.k === 4) || (l.sec === 's7' && l.k === 4) || (l.sec === 's9' && (l.k === 3 || l.k === 5));
  SUB_HIDE = l => l.sec === 's10';
  campDots();
  window.READY = true;
}
window.renderAt = t => { render(t); return true; };
window.frameJPEG = (t, q) => { render(t); return document.getElementById('c').toDataURL('image/jpeg', q || 0.93).slice(23); };
