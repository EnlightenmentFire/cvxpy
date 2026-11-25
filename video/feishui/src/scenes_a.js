// 第 1–4 段场景
'use strict';

// ================= S1 开场 =================
const TORCH = [];
function initTorches() {
  const r = rng(11);
  for (let i = 0; i < 1100; i++) {
    const u = r();                       // 沿队列的位置 0=远端 1=近端
    TORCH.push({ u, off: (r() - 0.5), ph: r() * 6.28, f: 2 + r() * 5 });
  }
}
function torchLine(t, push, alpha = 1) {
  // 远景：夜空、北岸长龙般的火把、淮河水面倒影
  const hz = lerp(720, 640, push);
  const sky = ctx.createLinearGradient(0, 0, 0, hz + 60);
  sky.addColorStop(0, '#04060c'); sky.addColorStop(0.7, '#0c1424'); sky.addColorStop(1, '#231a18');
  ctx.fillStyle = sky; ctx.fillRect(0, 0, W, hz + 60);
  // 月
  const mg = ctx.createRadialGradient(820, 260, 0, 820, 260, 160); mg.addColorStop(0, 'rgba(230,226,210,0.9)'); mg.addColorStop(0.18, 'rgba(230,226,210,0.85)'); mg.addColorStop(0.2, 'rgba(200,200,190,0.18)'); mg.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = mg; ctx.fillRect(600, 60, 440, 420);
  // 远山
  ctx.fillStyle = '#0a0d14'; ctx.beginPath(); ctx.moveTo(0, hz);
  for (let x = 0; x <= W; x += 20) ctx.lineTo(x, hz - 40 - 50 * Math.sin(x * 0.006 + 1) - 25 * Math.sin(x * 0.021));
  ctx.lineTo(W, hz + 40); ctx.lineTo(0, hz + 40); ctx.fill();
  // 北岸地面
  ctx.fillStyle = '#0d0f12'; ctx.fillRect(0, hz, W, 120);
  // 水面
  const wy = hz + 110, wg = ctx.createLinearGradient(0, wy, 0, H);
  wg.addColorStop(0, '#141d2a'); wg.addColorStop(1, '#05070b'); ctx.fillStyle = wg; ctx.fillRect(0, wy, W, H - wy);
  // 火把长龙：透视曲线，远端在左上，近端在右
  const zoom = 1 + push * 1.4;
  ctx.save(); ctx.translate(W / 2, hz + 40); ctx.scale(zoom, zoom); ctx.translate(-W / 2, -(hz + 40));
  ctx.globalCompositeOperation = 'lighter';
  for (const q of TORCH) {
    const u = q.u, d = Math.pow(u, 1.8);
    // 蜿蜒的行军队列：远端在左侧地平线，近端向右下展开
    const x = lerp(-120, 1250, u) + Math.sin(u * 9 + 0.5) * 90 * (1 - u * 0.6);
    const y = hz + 6 + d * 120 + Math.sin(u * 13) * 10 * (1 - u) + q.off * lerp(3, 46, d);
    const fl = 0.65 + 0.35 * Math.sin(t * q.f + q.ph);
    const rr = lerp(2.2, 9, d) * (0.85 + 0.25 * fl);
    torchGlow(x, y, rr * 4.5, 0.16 * fl * alpha);
    ctx.fillStyle = `rgba(255,${210 + 40 * fl | 0},150,${0.95 * alpha})`; ctx.fillRect(x - rr * 0.35, y - rr * 0.6, rr * 0.7, rr * 1.1);
    const ry = wy + (y - hz) * 2.0 + 20;
    ctx.fillStyle = `rgba(255,150,70,${0.07 * fl * alpha * (0.3 + d)})`; ctx.fillRect(x - rr * 0.25, ry, rr * 0.5, lerp(16, 120, d) * (0.7 + 0.3 * Math.sin(t * 2 + q.ph)));
  }
  ctx.restore();
  // 水面波光
  ctx.save(); ctx.globalAlpha = 0.18;
  for (let i = 0; i < 90; i++) { const y = wy + 20 + hash(i, 1) * (H - wy); const x = (hash(i, 2) * W + t * (10 + 20 * hash(i, 3))) % (W + 200) - 100; ctx.fillStyle = '#9fb4cc'; ctx.fillRect(x, y, 30 + 60 * hash(i, 4), 2); }
  ctx.restore();
}

function sc1(t) {
  const s = 's1';
  let map = 0;
  // --- 1. 火把长龙 + 倒下的大旗（第一帧即钩子）
  const tA = A('s1_03');
  if (t < tA + 0.8) {
    const push = eio(clamp(t / (E('s1_01') + 0.3)));
    torchLine(t, push);
    // 大旗：在推镜末段倒下
    const tf = E('s1_01') - 1.6;
    const rot = -1.35 * ein(clamp((t - tf) / 1.4));
    const sc = lerp(0.55, 1.25, push);
    banner(lerp(600, 430, push), lerp(780, 1150, push), 560 * sc, C.qinD, '秦', t, { rot, alpha: 1 });
    // 尘
    if (t > tf + 1.2) { const u = clamp((t - tf - 1.2) / 2.5); ctx.save(); ctx.globalAlpha = 0.35 * (1 - u); ctx.fillStyle = '#8a7c66'; ctx.beginPath(); ctx.ellipse(200, 1150, 280 * u + 40, 50 * u + 10, 0, 0, Math.PI * 2); ctx.fill(); ctx.restore(); }
    // 地点时间
    const a2 = fadeIO(t, A('s1_02') - 0.2, tA + 0.3, 0.6, 0.5);
    if (a2 > 0) {
      txt('公元 383 年', W / 2, 360, { size: 96, weight: 900, color: C.cream, alpha: a2, glow: 'rgba(0,0,0,1)', blur: 30, ls: 6 });
      txt('淮河南岸 · 淝水', W / 2, 480, { size: 56, weight: 700, color: C.gold, alpha: a2, glow: 'rgba(0,0,0,1)', blur: 20, ls: 10 });
    }
    if (t > tA - 0.2) { ctx.fillStyle = `rgba(6,7,10,${sstep((t - tA + 0.2) / 0.9)})`; ctx.fillRect(0, 0, W, H); }
  }
  // --- 2. 数字：87 万 vs 8 万
  if (t > tA - 0.2 && t < A('s1_06') + 0.6) {
    const a = fadeIO(t, tA - 0.2, A('s1_06') + 0.6, 0.5, 0.6);
    ctx.save(); ctx.globalAlpha = a;
    ctx.fillStyle = '#07080b'; ctx.fillRect(0, 0, W, H);
    const nQ = 2600, grow = eout((t - tA) / 3.2), scatter = ein(clamp((t - A('s1_05') - 0.3) / 3));
    const cols = 52;
    for (let i = 0; i < nQ * grow; i++) {
      const cx = i % cols, cy = Math.floor(i / cols);
      let x = 70 + cx * 15.6 + (hash(i, 1) - 0.5) * 4, y = 560 + cy * 15 + (hash(i, 2) - 0.5) * 4;
      if (scatter > 0) { const ang = -Math.PI / 2 + (hash(i, 3) - 0.5) * 2.6; const d = scatter * (300 + 900 * hash(i, 4)); x += Math.cos(ang) * d * 0.5; y += Math.abs(Math.sin(ang)) * d; }
      ctx.fillStyle = i < 600 * 26 / 87 * 3.04 && false ? C.qinL : (cy < 34 ? C.qin : C.qinL);
      ctx.globalAlpha = a * (1 - scatter * 0.7 * hash(i, 5));
      ctx.fillRect(x, y, 9, 9);
    }
    const aL = a * (1 - P(t, A('s1_05'), 0.4));
    ctx.globalAlpha = aL;
    const n = Math.round(870000 * eout((t - tA - 0.2) / 3.5));
    txt('前秦（史书记载）', 70, 330, { size: 40, align: 'left', color: C.qinL, weight: 700, alpha: aL });
    txt(fmtWan(Math.max(0, n)), 70, 430, { size: 120, align: 'left', color: C.qin, weight: 900, glow: rgba(C.qin, 0.6), alpha: aL });
    txt('步兵六十余万 · 骑兵二十七万 · 前后千里', 70, 515, { size: 34, align: 'left', color: '#c8d3df', weight: 600, alpha: aL * P(t, tA + 2, 0.8) });
    // 东晋
    const a4 = P(t, A('s1_04'), 0.6);
    if (a4 > 0) {
      ctx.globalAlpha = a * a4;
      ctx.fillStyle = C.jin; ctx.shadowColor = C.jin; ctx.shadowBlur = 25;
      const nJ = 240; for (let i = 0; i < nJ; i++) ctx.fillRect(820 + (i % 12) * 15.6, 1180 + Math.floor(i / 12) * 15, 9, 9);
      ctx.shadowBlur = 0;
      txt('东晋', 800, 1290, { size: 44, align: 'right', color: C.jinL, weight: 800, alpha: a * a4 * (1 - P(t, A('s1_05'), 0.4)) });
      txt('8万', 800, 1400, { size: 110, align: 'right', color: C.jin, weight: 900, alpha: a * a4 * (1 - P(t, A('s1_05'), 0.4)), glow: rgba(C.jin, 0.6) });
    }
    // 结局
    const a5 = fadeIO(t, A('s1_05') + 0.2, A('s1_06') + 0.5, 0.4, 0.5);
    if (a5 > 0) {
      ctx.globalAlpha = 1;
      bigArrow([[1000, 1150], [700, 900], [380, 700]], eout((t - A('s1_05') - 0.2) / 1.2), C.jin, 46, { alpha: a5 });
      txt('前秦大败', W / 2, 330, { size: 92, weight: 900, color: C.cream, alpha: a5, glow: 'rgba(0,0,0,1)', blur: 30 });
    }
    ctx.restore();
  }
  // --- 3. 成语
  const t6 = A('s1_06');
  if (t > t6 - 0.3 && t < A('s1_08') + 0.5) {
    const a = fadeIO(t, t6 - 0.3, A('s1_08') + 0.5, 0.5, 0.5);
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = '#0a0908'; ctx.fillRect(0, 0, W, H); ctx.restore();
    // 夜色芦苇
    reeds(t, 1420, 70, 360, `rgba(20,24,30,${a})`, 3, 1.4);
    const crack = P(t, A('s1_07') + 1.2, 1.0);
    const sh = (hash(Math.floor(t * 25), 1) - 0.5) * 8 * crack * (1 - P(t, A('s1_07') + 2.5, 1));
    ['风', '声', '鹤', '唳'].forEach((c, i) => txt(c, 330 + sh, 470 + i * 150, { size: 140, weight: 900, color: C.cream, alpha: a * P(t, t6 + 1.0 + i * 0.12, 0.5) * (1 - 0.55 * crack) }));
    ['草', '木', '皆', '兵'].forEach((c, i) => txt(c, 750 - sh, 470 + i * 150, { size: 140, weight: 900, color: C.cream, alpha: a * P(t, t6 + 2.0 + i * 0.12, 0.5) * (1 - 0.55 * crack) }));
    if (crack > 0) {
      ctx.save(); ctx.globalAlpha = a * crack; ctx.strokeStyle = C.jin; ctx.lineWidth = 5; ctx.shadowColor = C.jin; ctx.shadowBlur = 18;
      ctx.beginPath(); let x = 540, y = 360; ctx.moveTo(x, y);
      for (let i = 0; i < 14; i++) { x += (hash(i, 9) - 0.5) * 80; y += 60; ctx.lineTo(x, y); } ctx.stroke(); ctx.restore();
      txt('结果', 330, 1130, { size: 44, color: C.gold, alpha: a * crack, weight: 700 });
      txt('机制？', 750, 1130, { size: 44, color: C.jinL, alpha: a * crack, weight: 800 });
    }
  }
  // --- 4. 命令：稍微往后退一点
  const t8 = A('s1_08');
  if (t > t8 - 0.4 && t < A('s1_09') + 0.4) {
    const a = fadeIO(t, t8 - 0.4, A('s1_09') + 0.4, 0.5, 0.4);
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = '#08090c'; ctx.fillRect(0, 0, W, H); ctx.restore();
    // 河 + 一排兵
    ctx.save(); ctx.globalAlpha = a;
    ctx.fillStyle = '#132232'; ctx.fillRect(0, 520, W, 170);
    const back = ein(clamp((t - t8 - 3.5) / 4)) * 260;
    for (let r = 0; r < 6; r++) for (let c = 0; c < 9; c++) figure(130 + c * 103, 860 + r * 95 + back * (1 + r * 0.15) + (r > 3 ? back * hash(c, r) * 0.6 : 0), 0.8, r < 2 ? C.qin : mix(C.qin, '#203550', r / 8), { alpha: a, run: clamp(back / 200) * 0.6, phase: t * 9 + c });
    ctx.restore();
    caption('「稍微往后退一点」', 360, t, t8 + 2.6, A('s1_09') + 0.4, { size: 70, color: C.cream });
    bigArrow([[540, 760], [540, 1000], [540, 1180]], eout((t - t8 - 3.3) / 1.2), C.qin, 60, { alpha: a });
  }
  // --- 5. 四步预告
  const t9 = A('s1_09');
  if (t > t9 - 0.3) {
    const a = fadeIO(t, t9 - 0.3, S1(s) + 0.6, 0.4, 0.6);
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = '#09090b'; ctx.fillRect(0, 0, W, H); ctx.restore();
    const items = [['人数', '怎么打了折'], ['前锋', '怎么先倒'], ['一嗓子', '是谁喊的'], ['几十万人', '为何停不下来']];
    const dur = E('s1_09') - t9;
    items.forEach((it, i) => {
      const ti = t9 + dur * (0.18 + 0.2 * i), ai = a * P(t, ti, 0.4);
      const y = 470 + i * 230;
      panel(110, y - 90, W - 220, 180, ai * 0.9, i === 3 ? C.jin : C.goldD);
      txt(String(i + 1), 190, y, { size: 90, weight: 900, color: i === 3 ? C.jin : C.gold, alpha: ai });
      txt(it[0], 290, y - 30, { size: 58, weight: 800, align: 'left', color: C.cream, alpha: ai });
      txt(it[1], 290, y + 40, { size: 42, weight: 600, align: 'left', color: '#c9c2b2', alpha: ai });
    });
  }
  return { map };
}

// ================= S2 人数不等于兵力（东亚大图） =================
let TERR;
function buildTerritory() {
  const g = GEO.macro;
  const c = document.createElement('canvas'); c.width = g.w; c.height = g.h; const x = c.getContext('2d');
  const toP = (lon, lat) => { const [X, Y] = merc(lon, lat); return [(X - g.mx0) * g.scale, (Y - g.my0) * g.scale]; };
  const poly = (pts, col) => { x.beginPath(); pts.forEach((p, i) => { const q = toP(p[0], p[1]); i ? x.lineTo(q[0], q[1]) : x.moveTo(q[0], q[1]); }); x.closePath(); x.fillStyle = col; x.fill(); };
  poly(QIN_POLY, 'rgba(70,140,220,0.34)'); poly(JIN_POLY, 'rgba(220,70,45,0.30)');
  x.globalCompositeOperation = 'destination-in'; x.drawImage(IMG.land, 0, 0, g.w, g.h);
  x.globalCompositeOperation = 'source-over';
  // 边界线
  x.setLineDash([22, 14]); x.lineWidth = 7; x.strokeStyle = 'rgba(240,220,170,0.75)';
  x.beginPath(); BORDER.forEach((p, i) => { const q = toP(p[0], p[1]); i ? x.lineTo(q[0], q[1]) : x.moveTo(q[0], q[1]); }); x.stroke();
  TERR = c;
}
function drawTerr(cam, a) {
  if (a <= 0) return; const sw = W / cam.s, sh = H / cam.s;
  ctx.save(); ctx.globalAlpha = a; ctx.drawImage(TERR, cam.px - sw / 2, cam.py - sh / 2, sw, sh, 0, 0, W, H); ctx.restore();
}
function plabel(cam, key, a, o = {}) { const p = PL[key]; const [x, y] = mw(cam, p[0], p[1]); placeLabel(x, y, o.name || p[2], Object.assign({ alpha: a }, o)); return [x, y]; }

function sc2(t) {
  const s = 's2';
  const t0 = S0(s);
  // 镜头：全景 → 中原 → 淮河
  const cam = plateCam('macro', kf([
    [t0, 110.5, 33.2, 17], [A('s2_03'), 110.5, 33.2, 17], [A('s2_12'), 110.2, 33.6, 16.5], [A('s2_15') + 2, 110.2, 33.6, 16.5],
    [A('s2_16'), 115.3, 33.2, 6.5], [A('s2_21'), 115.3, 33.2, 6.5], [A('s2_22'), 112.0, 33.6, 14], [S1(s) + 1, 112.0, 33.6, 14]], t));
  drawPlate(cam, 0.2);
  drawTerr(cam, P(t, t0 + 0.4, 1.2));
  // 势力名称
  const aT = P(t, t0 + 0.8, 0.8);
  { const [x, y] = mw(cam, 109.5, 37.4); txt('前秦', x, y, { size: 84, weight: 900, color: C.qinL, alpha: aT * 0.9, stroke: 'rgba(0,0,0,0.7)', sw: 10, ls: 20 }); }
  { const [x, y] = mw(cam, 114.0, 28.7); txt('东晋', x, y, { size: 84, weight: 900, color: C.jinL, alpha: aT * 0.9, stroke: 'rgba(0,0,0,0.7)', sw: 10, ls: 20 }); }
  // 灭国年表
  const conq = [[115.3, 37.6, '灭前燕 370'], [104.6, 31.4, '取巴蜀 373'], [103.2, 37.0, '灭前凉 376'], [112.0, 40.3, '灭代 376']];
  const dC = E('s2_02') - A('s2_02');
  conq.forEach((c, i) => {
    const ti = A('s2_02') + dC * (0.2 + 0.17 * i), a = fadeIO(t, ti, A('s2_04') - 0.2, 0.4, 0.5);
    if (a <= 0) return; const [x, y] = mw(cam, c[0], c[1]);
    ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = C.qinL; ctx.lineWidth = 4; const r = 40 + 30 * eout((t - ti) / 0.8); ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
    txt(c[2], x, y + 70, { size: 38, weight: 800, color: C.cream, alpha: a, stroke: 'rgba(0,0,0,0.85)', sw: 8 });
  });
  plabel(cam, 'changan', P(t, t0 + 1, 0.6) * (1 - P(t, A('s2_16') - 1, 0.6)), { dot: C.gold });
  plabel(cam, 'jiankang', P(t, t0 + 1, 0.6) * (1 - P(t, A('s2_16') - 1, 0.6)), { dot: C.jin });

  // --- 投鞭断流
  const tc = A('s2_03');
  if (t > tc - 0.4 && t < A('s2_08') + 0.3) {
    const a = fadeIO(t, tc - 0.4, A('s2_08') + 0.3, 0.5, 0.5);
    ctx.save(); ctx.globalAlpha = a * 0.88; ctx.fillStyle = '#08090b'; ctx.fillRect(0, 0, W, H); ctx.restore();
    // 江
    ctx.save(); ctx.globalAlpha = a; const ry = 1180;
    const rg = ctx.createLinearGradient(0, ry - 80, 0, ry + 120); rg.addColorStop(0, '#1b3043'); rg.addColorStop(1, '#0c1620'); ctx.fillStyle = rg; ctx.fillRect(0, ry - 80, W, 200);
    for (let i = 0; i < 60; i++) { const x = (hash(i, 1) * W + t * 60) % W; ctx.fillStyle = 'rgba(170,200,230,0.25)'; ctx.fillRect(x, ry - 70 + hash(i, 2) * 180, 40, 2); }
    // 马鞭雨
    const tw = A('s2_05');
    for (let i = 0; i < 160; i++) {
      const st = tw + hash(i, 3) * (E('s2_05') - tw) * 0.9, u = (t - st) / 0.9;
      if (u < 0) continue;
      const x = 60 + hash(i, 4) * (W - 120), y = lerp(200, ry - 40 + hash(i, 5) * 150, clamp(u));
      const rot = u * 6 + hash(i, 6) * 6;
      ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.strokeStyle = u < 1 ? '#8a6a40' : 'rgba(138,106,64,0.6)'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(-22, 0); ctx.lineTo(22, 0); ctx.stroke(); ctx.restore();
    }
    // 江面堵塞示意：鞭子堆积
    const pile = P(t, tw + 1.5, 3);
    ctx.fillStyle = `rgba(110,84,50,${0.55 * pile})`; ctx.fillRect(0, ry - 30, W * pile, 60);
    ctx.restore();
    // 苻融之谏
    miniQuote(t, A('s2_06') - 0.2, A('s2_07') + 0.2, '我數戰，兵疲將倦，有憚敵之意。', '苻融語 · 《晉書·苻堅載記下》', 560);
    caption('人多 ≠ 好管', 520, t, A('s2_07') + 1.0, A('s2_08') + 0.3, { size: 84, color: C.gold });
  }
  // --- 拼起来的大军
  const tp = A('s2_08');
  if (t > tp - 0.4 && t < A('s2_12') + 0.2) {
    const a = fadeIO(t, tp - 0.4, A('s2_12') + 0.2, 0.5, 0.5);
    ctx.save(); ctx.globalAlpha = a * 0.92; ctx.fillStyle = '#08090b'; ctx.fillRect(0, 0, W, H); ctx.restore();
    if (t < A('s2_10') + 0.3) {
      const labs = ['氐', '羌', '鲜卑', '汉', '降部', '新征', '羯', '旧部', '良家子'];
      const shades = ['#5ea6ea', '#4a86c0', '#7bb4e6', '#3d73a8', '#8cc0ef', '#5590c8', '#6aa0d4', '#2f5f90', '#9ccbf2'];
      const ab = a * (1 - P(t, A('s2_10') - 0.3, 0.5));
      for (let k = 0; k < 9; k++) {
        const cx = 210 + (k % 3) * 330, cy = 620 + Math.floor(k / 3) * 330;
        const ti = tp + 0.3 + k * 0.25, u = eout((t - ti) / 0.8);
        const ox = (hash(k, 1) - 0.5) * 500 * (1 - u), oy = (hash(k, 2) - 0.5) * 500 * (1 - u);
        ctx.save(); ctx.globalAlpha = ab * clamp(u * 1.5); ctx.translate(cx + ox, cy + oy); ctx.rotate((hash(k, 3) - 0.5) * 0.3 * (1 - u));
        ctx.fillStyle = shades[k]; ctx.beginPath();
        for (let j = 0; j < 6; j++) { const ang = j / 6 * Math.PI * 2 + hash(k, j) * 0.4; const rr = 140 + 25 * hash(k, j + 7); ctx.lineTo(Math.cos(ang) * rr, Math.sin(ang) * rr); }
        ctx.closePath(); ctx.fill(); ctx.strokeStyle = '#0a0d12'; ctx.lineWidth = 10; ctx.stroke(); ctx.restore();
        if (t > A('s2_09') - 0.2) txt(labs[k], cx + ox, cy + oy, { size: 52, weight: 900, color: '#0b1522', alpha: ab * P(t, A('s2_09') + k * 0.3, 0.4) });
      }
      // 接缝发光
      const seam = P(t, A('s2_09') + 2.5, 1);
      if (seam > 0) { ctx.save(); ctx.globalAlpha = ab * seam * (0.6 + 0.4 * Math.sin(t * 6)); ctx.strokeStyle = C.jinL; ctx.lineWidth = 3; ctx.shadowColor = C.jin; ctx.shadowBlur = 20; for (let i = 0; i < 2; i++) { ctx.beginPath(); ctx.moveTo(45 + 330 * (i + 1) - 120, 430); ctx.lineTo(45 + 330 * (i + 1) - 120, 1340); ctx.stroke(); ctx.beginPath(); ctx.moveTo(60, 450 + 330 * (i + 1)); ctx.lineTo(1020, 450 + 330 * (i + 1)); ctx.stroke(); } ctx.restore(); }
      caption('一块一块拼起来的大军', 330, t, tp + 0.3, A('s2_10') - 0.2, { size: 64 });
    }
    // 十丁遣一兵
    const t10 = A('s2_10');
    if (t > t10 - 0.3 && t < A('s2_11') + 0.3) {
      const a2 = a * fadeIO(t, t10 - 0.3, A('s2_11') + 0.3, 0.4, 0.4);
      for (let i = 0; i < 10; i++) { const hi = i === 6 && t > t10 + 1.8; figure(98 + i * 98, 1150, 2.0, hi ? C.qin : '#4a4f58', { alpha: a2, noSpear: !hi }); }
      txt('十丁遣一兵', W / 2, 640, { size: 96, weight: 900, color: C.cream, alpha: a2 });
      txt('每十个成年男子，抽一个当兵', W / 2, 760, { size: 40, weight: 600, color: '#c8c0ae', alpha: a2 });
    }
    // 旗鼓传令
    const t11 = A('s2_11');
    if (t > t11 - 0.3) {
      const a3 = a * P(t, t11 - 0.3, 0.4);
      const nn = 7;
      for (let i = 0; i < nn; i++) {
        const x = 150 + i * 130, y = 1180 - i * 70;
        const pulse = Math.exp(-Math.pow((t - t11 - 0.8 - i * 0.7) / 0.25, 2));
        banner(x, y, 170, mix(C.qinD, C.gold, pulse), '', t + i, { alpha: a3 * (1 - i * 0.08) });
        if (pulse > 0.05) torchGlow(x + 40, y - 150, 90, pulse * a3 * 0.8);
      }
      txt('号令 → 一层一层往下传', W / 2, 640, { size: 56, weight: 800, color: C.cream, alpha: a3 });
      txt('越往后越慢，越往后越走样', W / 2, 1380, { size: 40, weight: 600, color: C.jinL, alpha: a3 * P(t, t11 + 4, 0.6) });
    }
  }
  // --- 没有到齐：各路箭头
  const t12 = A('s2_12');
  if (t > t12 - 0.3) {
    const aR = P(t, t12, 0.5) * (1 - P(t, A('s2_22') - 0.5, 0.6));
    const p = id => eout((t - A(id)) / 2.2);
    const d13 = E('s2_13') - A('s2_13');
    const sp = (pts) => geoPts(cam, pts);
    if (aR > 0) {
      bigArrow(sp(ROUTES.main), eout((t - t12 - 0.3) / 2.0), C.qin, 46, { alpha: aR });
      bigArrow(sp(ROUTES.liang), eout((t - A('s2_13') - d13 * 0.15) / 1.6) * 1.0, C.qinL, 30, { alpha: aR });
      bigArrow(sp(ROUTES.shu), eout((t - A('s2_13') - d13 * 0.42) / 1.6) * 0.62, C.qinL, 30, { alpha: aR });
      bigArrow(sp(ROUTES.youji), eout((t - A('s2_13') - d13 * 0.7) / 1.6), C.qinL, 30, { alpha: aR });
      const lab = (key, ti, name) => plabel(cam, key, aR * P(t, ti, 0.4), { name, dot: C.qinL, size: 36 });
      lab('xiangcheng', t12 + 1.6, '项城（苻坚）');
      lab('xianyang', A('s2_13') + d13 * 0.25, '咸阳：凉州兵才到');
      { const [x, y] = mw(cam, 109.6, 30.2); txt('蜀兵：还在顺江而下', x, y + 60, { size: 34, weight: 700, color: C.cream, alpha: aR * P(t, A('s2_13') + d13 * 0.5, 0.4), stroke: 'rgba(0,0,0,0.85)', sw: 8 }); }
      lab('pengcheng', A('s2_13') + d13 * 0.8, '彭城：幽冀兵到此');
      // 拉开上万里
      const a15 = fadeIO(t, A('s2_15') + 1.5, A('s2_16') + 0.2, 0.5, 0.5);
      if (a15 > 0) {
        const [x1, y1] = mw(cam, 102.64, 37.93), [x2, y2] = mw(cam, 117.18, 34.26);
        strokePath([[x1, y1 - 120], [x2, y2 - 120]], C.gold, 5, { alpha: a15, dash: [18, 12] });
        txt('东西拉开上万里（史书语）', (x1 + x2) / 2, (y1 + y2) / 2 - 170, { size: 44, weight: 800, color: C.gold, alpha: a15, stroke: 'rgba(0,0,0,0.85)', sw: 8 });
      }
    }
    // 前锋到颍口
    const t16 = A('s2_16');
    if (t > t16 - 0.3) {
      const aF = P(t, t16, 0.5) * (1 - P(t, A('s2_22') - 0.5, 0.6));
      bigArrow(sp(ROUTES.front), eout((t - t16 - 0.8) / 1.5), C.qin, 48, { alpha: aF });
      plabel(cam, 'xiangcheng', aF, { name: '项城：主力留此', dot: C.qinL, size: 36 });
      plabel(cam, 'yingkou', aF * P(t, t16 + 2, 0.4), { name: '颍口：前锋（史载三十万）', dot: C.qin, size: 34, dy: 46, dx: -30, align: 'right' });
      plabel(cam, 'shouyang', aF * P(t, t16 + 2.5, 0.4), { name: '寿阳', dot: C.cream, size: 38, dy: 40 });
      // 截获的求援信
      const t17 = A('s2_17');
      if (t > t17 - 0.2 && t < A('s2_19') + 0.5) {
        const al = fadeIO(t, t17 - 0.2, A('s2_19') + 0.5, 0.4, 0.4);
        const [hx, hy] = mw(cam, 116.72, 32.705), [ex, ey] = mw(cam, 117.6, 32.4);
        const u = eio((t - t17 - 0.5) / 2.5);
        const lx = lerp(hx, ex, u * 0.55), ly = lerp(hy, ey, u * 0.55);
        letterIcon(lx, ly, 0.7, C.paper, -0.1, al);
        if (t > t17 + 2.8) { ctx.save(); ctx.globalAlpha = al; ctx.strokeStyle = C.qin; ctx.lineWidth = 9; ctx.beginPath(); ctx.moveTo(lx - 50, ly - 50); ctx.lineTo(lx + 50, ly + 50); ctx.moveTo(lx + 50, ly - 50); ctx.lineTo(lx - 50, ly + 50); ctx.stroke(); ctx.restore(); }
        miniQuote(t, A('s2_18') - 0.1, A('s2_19') + 0.4, '賊少易擒，但恐逃去，宜速赴之。', '苻融語 · 《資治通鑑》卷一百五', 560);
      }
      // 八千轻骑
      const t19 = A('s2_19');
      if (t > t19) {
        const pts = sp(ROUTES.dash), u = eout((t - t19 - 1.5) / 1.6);
        strokePath(subPath(smooth(pts, 10), cumLen(smooth(pts, 10)), 0, cumLen(smooth(pts, 10)).slice(-1)[0] * u), C.gold, 12, { alpha: aF, dash: [26, 14], dashOff: -t * 80, glow: C.gold });
        const [x, y] = mw(cam, 115.9, 33.15);
        txt('苻坚 · 轻骑八千', x, y - 70, { size: 40, weight: 800, color: C.gold, alpha: aF * P(t, t19 + 2, 0.4), stroke: 'rgba(0,0,0,0.85)', sw: 8 });
      }
      miniQuote(t, A('s2_20') + 0.3, A('s2_21') + 0.2, '敢言吾至壽春者拔舌。', '《晉書·苻堅載記下》', 1240);
      // 前锋 vs 路上
      const t21 = A('s2_21');
      if (t > t21) {
        const a21 = fadeIO(t, t21, A('s2_22') - 0.2, 0.4, 0.5);
        const [x, y] = mw(cam, 116.78, 32.58);
        ctx.save(); ctx.globalAlpha = a21; ctx.strokeStyle = C.cream; ctx.lineWidth = 4; ctx.setLineDash([10, 8]); ctx.beginPath(); ctx.arc(x, y, 120, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
        txt('淝水前线', x, y + 165, { size: 42, weight: 800, color: C.cream, alpha: a21, stroke: 'rgba(0,0,0,0.9)', sw: 8 });
        // 路上的长队列小点
        for (let i = 0; i < 160; i++) { const route = ROUTES.main; const sm = smooth(geoPts(cam, route), 8), c = cumLen(sm); const q = along(sm, c, ((hash(i, 1) + t * 0.02) % 1) * c[c.length - 1]); ctx.fillStyle = rgba(C.qinL, a21 * 0.9); ctx.fillRect(q[0] - 4 + (hash(i, 2) - 0.5) * 20, q[1] - 4 + (hash(i, 3) - 0.5) * 20, 8, 8); }
        txt('后面几十万人：还在路上', W / 2, 360, { size: 52, weight: 800, color: C.qinL, alpha: a21 * P(t, t21 + 3, 0.5), glow: 'rgba(0,0,0,1)' });
      }
    }
  }
  // --- 账面 vs 前线
  const t22 = A('s2_22');
  if (t > t22 - 0.4) {
    const a = P(t, t22 - 0.4, 0.5);
    ctx.save(); ctx.globalAlpha = a * 0.88; ctx.fillStyle = '#07080a'; ctx.fillRect(0, 0, W, H); ctx.restore();
    const bar = (y, label, q, j, qText, ti) => {
      const u = eout((t - ti) / 1.2);
      txt(label, 90, y - 70, { size: 44, align: 'left', weight: 800, color: C.cream, alpha: a });
      ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = C.qin; ctx.fillRect(90, y - 30, 820 * q * u, 70); ctx.fillStyle = C.jin; ctx.fillRect(90, y + 60, 820 * j * u, 70); ctx.restore();
      txt(qText, 100 + 820 * q * u + 20, y + 5, { size: 44, align: 'left', weight: 900, color: C.qinL, alpha: a * u });
      txt('8万', 100 + 820 * j * u + 20, y + 95, { size: 44, align: 'left', weight: 900, color: C.jinL, alpha: a * u });
    };
    bar(560, '账面上（出发时，史书记载）', 1.0 * 0.92, 0.085, '87万', t22 + 0.3);
    const fq = 0.32 + 0.06 * Math.sin(t * 2.5);
    if (t > t22 + 3.5) bar(1000, '同一时刻、淝水边上', fq * P(t, t22 + 3.5, 1), 0.085, '？', t22 + 3.5);
    const t23 = A('s2_23');
    caption('到了多少？史书没写清', 1330, t, t23 + 0.2, A('s2_24') + 0.3, { size: 54, color: C.gold });
    caption('后世也有学者怀疑记载有夸张', 1410, t, t23 + 3.5, A('s2_24') + 0.3, { size: 40, color: '#cfc6b4', weight: 600 });
    const t24 = A('s2_24');
    if (t > t24) {
      const a24 = P(t, t24, 0.5);
      ctx.save(); ctx.globalAlpha = a24 * 0.92; ctx.fillStyle = '#07080a'; ctx.fillRect(0, 0, W, H); ctx.restore();
      txt('不比谁的人多', W / 2, 640, { size: 64, weight: 800, color: '#a9a294', alpha: a24 });
      txt('一支大军', W / 2, 820, { size: 96, weight: 900, color: C.cream, alpha: a24 * P(t, t24 + 2.5, 0.6) });
      txt('在什么条件下', W / 2, 960, { size: 96, weight: 900, color: C.cream, alpha: a24 * P(t, t24 + 3.2, 0.6) });
      txt('会自己散掉？', W / 2, 1100, { size: 110, weight: 900, color: C.jin, alpha: a24 * P(t, t24 + 4.0, 0.6), glow: rgba(C.jin, 0.5) });
    }
  }
  return { map: t < A('s2_03') - 0.2 || (t > A('s2_12') && t < A('s2_22')) ? 1 : 0 };
}

// ================= S3 第一块骨牌（淮河—淝水局部） =================
let CAMP;
function initCamp() { CAMP = []; const r = rng(23); for (let i = 0; i < 420; i++) { const a = r() * Math.PI * 2, d = Math.sqrt(r()); CAMP.push({ dx: Math.cos(a) * d * 0.045, dy: Math.sin(a) * d * 0.028 - 0.012, k: r(), fire: r() < 0.14, ph: r() * 6 }); } }
function regionRivers(cam, a = 1, hiFei = 0) {
  const draw = (pts, w, col) => { geoStroke(cam, pts, '#0d1a26', w + 10, { alpha: a * 0.8 }); geoStroke(cam, pts, col, w, { alpha: a }); };
  draw(RIV.ying, 14, C.waterL); draw(RIV.huai, 30, '#3f6688'); draw(RIV.luo, 12, C.waterL);
  draw(RIV.fei, 16 + 8 * hiFei, mix('#4a7090', '#8fd0ff', hiFei));
  const lab = (lon, lat, s, rot = 0) => { const [x, y] = mw(cam, lon, lat); ctx.save(); ctx.translate(x, y); ctx.rotate(rot); txt(s, 0, 0, { size: 38, weight: 700, color: '#9ec4e2', alpha: a, stroke: 'rgba(0,0,0,0.8)', sw: 7, ls: 8 }); ctx.restore(); };
  lab(116.43, 32.50, '淮 水', 0.35); lab(116.97, 32.44, '淝水', 0.0); lab(117.26, 32.47, '洛涧', 0);
}
function sc3(t) {
  const s = 's3', t0 = S0(s);
  const cam = plateCam('region', kf([[t0, 116.98, 32.63, 0.72], [A('s3_03'), 117.02, 32.64, 0.62], [A('s3_05'), 117.10, 32.65, 0.42], [A('s3_09'), 117.10, 32.65, 0.42],
  [A('s3_12'), 116.98, 32.63, 0.62], [A('s3_13'), 116.86, 32.63, 0.4], [S1(s) + 1, 116.86, 32.63, 0.4]], t));
  const night = fadeIO(t, A('s3_06') - 0.5, A('s3_09'), 1.0, 1.5);
  drawPlate(cam, 0.18 + 0.45 * night);
  regionRivers(cam, 1, P(t, A('s3_12') + 1, 1) * (1 - P(t, A('s3_13') + 2, 1)));
  // 地名
  plabel(cam, 'shouyang', P(t, t0 + 0.6, 0.5), { name: '寿阳（寿春）', dot: t > A('s3_02') + 1 ? C.qin : C.jin, square: true, size: 40, dx: -24, align: 'right' });
  plabel(cam, 'bagong', P(t, t0 + 1.0, 0.5), { name: '八公山', dot: '#b8a888', size: 34, dy: -40 });
  plabel(cam, 'xiashi', P(t, t0 + 1.2, 0.5), { name: '硖石', dot: '#b8a888', size: 34, dy: -40, dx: -20, align: 'right' });
  // 胡彬退守硖石
  const t2 = A('s3_02');
  if (t > t2) {
    const [x1, y1] = mw(cam, 116.80, 32.55), [x2, y2] = mw(cam, 116.73, 32.69);
    bigArrow([[x1 + 40, y1 + 40], [x1, y1 - 40], [x2, y2 + 20]], eout((t - t2 - 2.5) / 1.4), C.jin, 22, { alpha: 1 - P(t, A('s3_05'), 1) });
    const [sx, sy] = mw(cam, 116.785, 32.575);
    if (t < A('s3_05')) banner(sx + 10, sy, 120, C.qinD, '秦', t, { alpha: P(t, t2 + 1, 0.5) * (1 - P(t, A('s3_04'), 1)) });
    const [hx, hy] = mw(cam, 116.72, 32.705);
    txt('胡彬 · 粮尽', hx - 30, hy + 70, { size: 36, align: 'right', weight: 800, color: C.jinL, alpha: P(t, t2 + 4, 0.4) * (1 - P(t, A('s3_05'), 1)), stroke: 'rgba(0,0,0,0.85)', sw: 7 });
  }
  // 梁成五万
  const t3 = A('s3_03'), tStrike = A('s3_07') + 0.8, tFlee = A('s3_07') + 2.5;
  const [cx, cy] = mw(cam, 117.12, 32.64);
  const sc = cam.s * GEO.region.scale / 360;  // px per degree
  if (t > t3 - 0.2) {
    const aC = P(t, t3, 0.8) * (1 - P(t, A('s3_11'), 1.0));
    for (let i = 0; i < CAMP.length; i++) {
      const q = CAMP[i];
      let x = cx + q.dx * sc, y = cy + q.dy * sc;
      let al = aC;
      if (t > tFlee) { // 争赴淮水
        const u = clamp((t - tFlee - q.k * 2.5) / 3.5);
        const [hx, hy] = mw(cam, 117.12 + q.dx * 0.6, 32.705);
        x = lerp(x, hx, ein(u)); y = lerp(y, hy, ein(u));
        if (u > 0.85) al *= (1 - u) / 0.15;
      }
      ctx.fillStyle = rgba(C.qin, al); ctx.fillRect(x - 4, y - 4, 8, 8);
      if (q.fire && night > 0) {
        const out = clamp((t - tStrike - q.k * 3) / 0.5);
        if (out < 1) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; torchGlow(x, y, 26 + 8 * Math.sin(t * 7 + q.ph), night * (1 - out) * aC * 0.9); ctx.restore(); }
      }
    }
    // 木栅
    const [px1, py1] = mw(cam, 117.06, 32.695), [px2, py2] = mw(cam, 117.08, 32.722);
    ctx.save(); ctx.globalAlpha = aC; ctx.strokeStyle = '#c8a46a'; ctx.lineWidth = 8; ctx.setLineDash([6, 6]); ctx.beginPath(); ctx.moveTo(px1, py1); ctx.lineTo(px2, py2); ctx.stroke(); ctx.restore();
    txt('梁成 · 五万', cx, cy + 0.04 * sc, { size: 44, weight: 900, color: C.qinL, alpha: aC * (1 - P(t, tFlee, 1)), stroke: 'rgba(0,0,0,0.85)', sw: 8 });
    txt('立栅遏淮', (px1 + px2) / 2 + 60, (py1 + py2) / 2 - 30, { size: 32, weight: 700, color: '#e0c890', alpha: aC * P(t, t3 + 2.5, 0.5) * (1 - P(t, A('s3_05'), 0.5)), stroke: 'rgba(0,0,0,0.85)', sw: 6, align: 'left' });
  }
  // 晋军主力停在 25 里外
  const t4 = A('s3_04');
  if (t > t4 - 0.2) {
    const aJ = P(t, t4, 0.6) * (1 - P(t, A('s3_11'), 1));
    const [jx, jy] = mw(cam, 117.30, 32.585);
    ctx.save(); ctx.globalAlpha = aJ; ctx.fillStyle = C.jin; ctx.shadowColor = C.jin; ctx.shadowBlur = 20; ctx.fillRect(jx - 60, jy - 30, 120, 60); ctx.restore();
    txt('晋军主力', jx, jy + 70, { size: 38, weight: 800, color: C.jinL, alpha: aJ, stroke: 'rgba(0,0,0,0.85)', sw: 7 });
    strokePath([[jx - 70, jy - 10], [cx + 0.03 * sc, cy]], C.cream, 4, { alpha: aJ * (1 - P(t, A('s3_05'), 0.5)), dash: [12, 10] });
    txt('二十五里 · 不敢进', (jx + cx) / 2 + 40, (jy + cy) / 2 - 50, { size: 34, weight: 800, color: C.cream, alpha: aJ * (1 - P(t, A('s3_05'), 0.5)), stroke: 'rgba(0,0,0,0.85)', sw: 7 });
  }
  // 刘牢之五千：红色大箭头切入
  const t5 = A('s3_05');
  if (t > t5) {
    const [ax, ay] = mw(cam, 117.30, 32.60);
    const aA = 1 - P(t, A('s3_09'), 0.8);
    bigArrow([[ax - 40, ay], [cx + 0.07 * sc, cy + 0.005 * sc], [cx - 0.005 * sc, cy - 0.004 * sc]], eout((t - t5 - 1.5) / 1.6) * (t < tStrike ? 0.82 : 1), C.jin, 58, { alpha: aA });
    txt('刘牢之 · 精兵五千', ax - 20, ay + 85, { size: 40, weight: 900, color: C.jinL, alpha: aA * P(t, t5 + 1.8, 0.4), stroke: 'rgba(0,0,0,0.85)', sw: 8 });
    caption('夜 袭', 470, t, A('s3_06') + 0.5, A('s3_07') + 1, { size: 110, color: C.jinL, ls: 30 });
    // 截断归津
    if (t > A('s3_07') + 1.2) {
      const [fx, fy] = mw(cam, 117.10, 32.70);
      bigArrow([[cx + 0.04 * sc, cy - 0.01 * sc], [fx + 0.02 * sc, fy + 0.01 * sc], [fx - 0.01 * sc, fy]], eout((t - A('s3_07') - 1.2) / 1.0), C.jin, 34, { alpha: aA });
      txt('截断归路', fx + 0.02 * sc, fy - 70, { size: 38, weight: 900, color: C.jinL, alpha: aA * P(t, A('s3_07') + 2, 0.4), stroke: 'rgba(0,0,0,0.85)', sw: 8 });
    }
    // 计数
    const k = clamp((t - tFlee) / 5);
    if (k > 0) txt('死者 ' + fmtWan(15000 * eout(k)), W / 2, 380, { size: 72, weight: 900, color: C.cream, alpha: 1 - P(t, A('s3_08') - 0.4, 0.4), glow: 'rgba(0,0,0,1)' });
  }
  // 预演三步
  const t9 = A('s3_09');
  if (t > t9 - 0.3 && t < A('s3_12')) {
    const a = fadeIO(t, t9 - 0.3, A('s3_12'), 0.4, 0.5);
    ctx.save(); ctx.globalAlpha = a * 0.85; ctx.fillStyle = '#07080a'; ctx.fillRect(0, 0, W, H); ctx.restore();
    const st = ['被打乱', '退路断', '争着逃'], d9 = E('s3_09') - t9;
    st.forEach((s0, i) => {
      const ai = a * P(t, t9 + d9 * (0.25 + 0.22 * i), 0.4);
      panel(240, 470 + i * 260, 600, 170, ai, i === 2 ? C.jin : C.goldD);
      txt(s0, W / 2, 555 + i * 260, { size: 72, weight: 900, color: i === 2 ? C.jinL : C.cream, alpha: ai });
      if (i < 2) txt('↓', W / 2, 685 + i * 260, { size: 60, color: C.gold, alpha: ai });
    });
    caption('淝水的预演', 1330, t, A('s3_10'), A('s3_12'), { size: 80, color: C.gold });
    // 我们赢定了 → 裂
    const t11 = A('s3_11');
    if (t > t11 - 0.2) {
      const a2 = P(t, t11 - 0.2, 0.4);
      ctx.save(); ctx.globalAlpha = a2 * 0.95; ctx.fillStyle = '#07080a'; ctx.fillRect(0, 0, W, H); ctx.restore();
      const cr = P(t, t11 + 2.0, 0.6);
      const sh = cr * (1 - P(t, t11 + 2.8, 0.6));
      txt('「我们赢定了」', W / 2 + (hash(Math.floor(t * 25), 2) - 0.5) * 20 * sh, 860, { size: 100, weight: 900, color: mix('#f4ead6', '#7a7570', cr), alpha: a2 });
      if (cr > 0) { ctx.save(); ctx.globalAlpha = a2 * cr; ctx.strokeStyle = '#fff'; ctx.lineWidth = 4; ctx.beginPath(); let x = 160, y = 840; ctx.moveTo(x, y); for (let i = 0; i < 12; i++) { x += 65; y += (hash(i, 4) - 0.5) * 70; ctx.lineTo(x, y); } ctx.stroke(); ctx.restore(); }
      txt('全军的信心', W / 2, 1010, { size: 48, weight: 700, color: C.gold, alpha: a2 * cr });
    }
  }
  // 晋军水陆并进到淝水东岸
  const t12 = A('s3_12');
  if (t > t12 - 0.2 && t < A('s3_13') + 1.5) {
    const a = fadeIO(t, t12 - 0.2, A('s3_13') + 1.5, 0.4, 0.8);
    const r1 = geoPts(cam, [[117.25, 32.62], [117.10, 32.62], [116.98, 32.61], [116.87, 32.60]]);
    const r2 = geoPts(cam, [[117.25, 32.74], [117.05, 32.715], [116.92, 32.70], [116.83, 32.67]]);
    bigArrow(r1, eout((t - t12 - 0.4) / 2.2), C.jin, 50, { alpha: a });
    bigArrow(r2, eout((t - t12 - 0.9) / 2.2), C.jinL, 34, { alpha: a });
    const [x, y] = mw(cam, 116.88, 32.585);
    txt('晋军 → 淝水东岸', x + 40, y + 80, { size: 40, weight: 900, color: C.jinL, alpha: a * P(t, t12 + 2.5, 0.4), stroke: 'rgba(0,0,0,0.85)', sw: 8, align: 'left' });
  }
  // 八公山草木 → 人形
  const t13 = A('s3_13');
  if (t > t13 + 2.5) {
    const a = fadeIO(t, t13 + 2.5, A('s3_15') + 0.4, 0.8, 0.6);
    drawGrassHill(t, a, P(t, t13 + 5.5, 2.5), true);
    caption('苻坚「憮然始有懼色」', 380, t, A('s3_14') + 2.0, A('s3_15'), { size: 56, color: C.gold });
  }
  // 文本对照
  const t15 = A('s3_15');
  if (t > t15) {
    const a = P(t, t15, 0.5);
    ctx.save(); ctx.globalAlpha = a * 0.93; ctx.fillStyle = '#08090b'; ctx.fillRect(0, 0, W, H); ctx.restore();
    const d = E('s3_15') - t15;
    panel(70, 480, 450, 330, a * P(t, t15 + d * 0.2, 0.4)); panel(560, 480, 450, 330, a * P(t, t15 + d * 0.45, 0.4));
    txt('《晉書》', 295, 550, { size: 40, color: C.gold, alpha: a * P(t, t15 + d * 0.2, 0.4) });
    txt('草木皆類人形', 295, 680, { size: 56, weight: 900, color: C.cream, alpha: a * P(t, t15 + d * 0.2, 0.4) });
    txt('《資治通鑑》', 785, 550, { size: 40, color: C.gold, alpha: a * P(t, t15 + d * 0.45, 0.4) });
    txt('皆以為晉兵', 785, 680, { size: 56, weight: 900, color: C.cream, alpha: a * P(t, t15 + d * 0.45, 0.4) });
    txt('↓ 后世凝固成成语', W / 2, 930, { size: 44, color: '#bdb4a2', alpha: a * P(t, t15 + d * 0.75, 0.4) });
    txt('草木皆兵', W / 2, 1110, { size: 140, weight: 900, color: C.cream, alpha: a * P(t, t15 + d * 0.8, 0.5), glow: rgba(C.gold, 0.4) });
  }
  return { map: t < t13 + 2.5 ? 1 : (t < t15 ? 1 : 0) };
}
function drawGrassHill(t, a, morph, withCity) {
  ctx.save(); ctx.globalAlpha = a;
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#0d121a'); g.addColorStop(0.55, '#1c2430'); g.addColorStop(1, '#0a0c10');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  // 山
  ctx.fillStyle = '#121820'; ctx.beginPath(); ctx.moveTo(0, 1100);
  for (let x = 0; x <= W; x += 10) ctx.lineTo(x, 760 + 160 * Math.pow(Math.sin(x / W * Math.PI * 0.9 + 0.2), 2) * -1 + 40 * Math.sin(x * 0.02));
  ctx.lineTo(W, 1100); ctx.fill();
  ctx.restore();
  for (let i = 0; i < 46; i++) {
    const x = 30 + (i % 23) * 46 + hash(i, 1) * 20, row = Math.floor(i / 23);
    const yb = 760 - 160 * Math.pow(Math.sin(x / W * Math.PI * 0.9 + 0.2), 2) + 40 * Math.sin(x * 0.02) + 40 + row * 110;
    const u = clamp(morph * 1.6 - hash(i, 2) * 0.6);
    grassMan(x, yb, 0.85 + row * 0.25, u, i, `rgba(6,8,12,${a})`);
  }
  if (withCity) {
    // 前景城墙（寿阳城头）
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = '#1e1a16'; ctx.fillRect(0, 1300, W, 620);
    for (let x = 0; x < W; x += 90) ctx.fillRect(x, 1250, 55, 60);
    ctx.fillStyle = '#2a241c'; ctx.fillRect(0, 1300, W, 12); ctx.restore();
    txt('八公山', 760, 520, { size: 46, weight: 800, color: '#a9b2bd', alpha: a * 0.9 });
  }
}

// ================= S4 站在两边的人 =================
function sc4(t) {
  const s = 's4', t0 = S0(s);
  const g = ctx.createLinearGradient(0, 0, W, 0); g.addColorStop(0, '#0b1420'); g.addColorStop(0.5, '#0d0d10'); g.addColorStop(1, '#1e0d0a');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = '#121214'; ctx.fillRect(0, 1260, W, 660);
  tent(220, 1260, 1.0, '#244a70'); tent(860, 1260, 1.0, '#7a2a1c');
  banner(330, 1260, 330, C.qinD, '秦', t); banner(970, 1260, 330, C.jinD, '晋', t + 1);
  txt('秦营', 220, 1330, { size: 40, weight: 800, color: C.qinL }); txt('晋营', 860, 1330, { size: 40, weight: 800, color: C.jinL });
  // 朱序：从左走到右
  const walk = eio((t - A('s4_02') - 0.5) / 4);
  const fx = lerp(330, 700, walk), half = P(t, A('s4_05'), 1.0);
  const fc = mix(C.qinL, C.cream, 0.3);
  figure(fx, 1260, 2.3, fc, { noSpear: true, run: 0.2 * (walk > 0 && walk < 1 ? 1 : 0), phase: t * 8 });
  if (half > 0) { ctx.save(); ctx.beginPath(); ctx.rect(fx, 0, 200, H); ctx.clip(); figure(fx, 1260, 2.3, mix(fc, C.jinL, half), { noSpear: true }); ctx.restore(); }
  txt('朱序', fx, 1060, { size: 52, weight: 900, color: C.gold, alpha: P(t, A('s4_02') + 0.8, 0.5) });
  // 襄阳 · 379
  const t3 = A('s4_03');
  if (t > t3 - 0.2 && t < A('s4_05')) {
    const a = fadeIO(t, t3 - 0.2, A('s4_05'), 0.4, 0.5);
    panel(140, 360, 800, 400, a * 0.9);
    txt('三七九年 · 襄阳城破', W / 2, 450, { size: 52, weight: 900, color: C.cream, alpha: a });
    txt('东晋守将朱序被俘', W / 2, 540, { size: 42, weight: 700, color: C.jinL, alpha: a * P(t, t3 + 2, 0.4) });
    txt('→ 在前秦任尚书', W / 2, 620, { size: 42, weight: 700, color: C.qinL, alpha: a * P(t, t3 + 4, 0.4) });
    txt('官位留得住人，留不住心', W / 2, 700, { size: 38, weight: 600, color: C.gold, alpha: a * P(t, A('s4_04') + 3, 0.4) });
  }
  // 当面 / 私下
  const t5 = A('s4_05');
  if (t > t5 && t < A('s4_08')) {
    const a = fadeIO(t, t5, A('s4_08'), 0.4, 0.5);
    panel(80, 380, 430, 200, a * P(t, t5 + 1.2, 0.4), C.qin);
    txt('当面', 295, 430, { size: 36, color: C.qinL, alpha: a * P(t, t5 + 1.2, 0.4) });
    txt('劝降', 295, 510, { size: 72, weight: 900, color: C.cream, alpha: a * P(t, t5 + 1.2, 0.4) });
    panel(570, 380, 430, 200, a * P(t, t5 + 3.0, 0.4), C.jin);
    txt('私下', 785, 430, { size: 36, color: C.jinL, alpha: a * P(t, t5 + 3.0, 0.4) });
    txt('速战', 785, 510, { size: 72, weight: 900, color: C.cream, alpha: a * P(t, t5 + 3.0, 0.4) });
    const t6 = A('s4_06'), d6 = E('s4_06') - t6;
    ['秦军百万到齐 → 难以抵挡', '趁各路未集 → 赶快出击', '打垮前锋 → 士气就没了'].forEach((s0, i) => {
      const ai = a * P(t, t6 + d6 * (0.05 + 0.3 * i), 0.4);
      txt(s0, W / 2, 690 + i * 90, { size: 46, weight: 800, color: i === 1 ? C.gold : C.cream, alpha: ai, glow: 'rgba(0,0,0,1)' });
    });
  }
  // 第一层回扣
  const t8 = A('s4_08');
  if (t > t8 && t < A('s4_09') + 0.3) {
    const a = fadeIO(t, t8, A('s4_09') + 0.3, 0.4, 0.4);
    ctx.save(); ctx.globalAlpha = a * 0.85; ctx.fillStyle = '#07080a'; ctx.fillRect(0, 0, W, H); ctx.restore();
    txt('最大的弱点', W / 2, 640, { size: 56, weight: 700, color: '#bdb4a2', alpha: a });
    txt('不是人少', W / 2, 800, { size: 90, weight: 900, color: '#8f8a80', alpha: a * P(t, t8 + 2, 0.4) });
    txt('是没到齐', W / 2, 960, { size: 110, weight: 900, color: C.gold, alpha: a * P(t, t8 + 3.3, 0.5), glow: rgba(C.gold, 0.4) });
  }
  // 谢石 / 谢琰
  const t9 = A('s4_09');
  if (t > t9 && t < A('s4_10') + 0.3) {
    const a = fadeIO(t, t9, A('s4_10') + 0.3, 0.4, 0.4);
    panel(120, 420, 840, 360, a * 0.9);
    txt('谢石：拖着不打', W / 2, 520, { size: 54, weight: 800, color: '#cfc6b4', alpha: a });
    txt('谢琰：照朱序的话办', W / 2, 650, { size: 60, weight: 900, color: C.jinL, alpha: a * P(t, t9 + 3.5, 0.4) });
  }
  // 裂缝
  const t10 = A('s4_10');
  if (t > t10) {
    const a = P(t, t10, 0.4);
    const u = eout((t - t10 - 1.5) / 2.5);
    ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = C.cream; ctx.lineWidth = 6; ctx.shadowColor = C.gold; ctx.shadowBlur = 25;
    ctx.beginPath(); let x = 560, y = 160; ctx.moveTo(x, y); const n = Math.floor(22 * u);
    for (let i = 0; i < n; i++) { x += (hash(i, 7) - 0.5) * 70; y += 52; ctx.lineTo(x, y); } ctx.stroke(); ctx.restore();
    caption('情报与人心的裂缝', 420, t, t10 + 2.5, S1(s) + 0.6, { size: 64, color: C.gold });
    caption('淝水边上，还会再裂一次', 520, t, A('s4_11') + 0.5, S1(s) + 0.6, { size: 48, color: C.jinL });
  }
  return { act: 1 };
}
