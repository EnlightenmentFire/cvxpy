// 第 5–7 段场景：淝水对岸的崩溃（全片高潮）、溃退、屐齿
'use strict';

// ---------- 军队粒子：每个兵的运动是“仿真时钟”τ 的解析函数 ----------
// 仿真时钟：讲解图示时几乎暂停，回到战场时按真实速度走
let ARMY, JIN, SIMSEG, EV;
function simTau(t) {
  let tau = 0;
  for (const [a, b, r] of SIMSEG) { if (t <= a) break; tau += (Math.min(t, b) - a) * r; }
  return tau;
}
function initArmy() {
  // 仿真速率分段：[实时起点, 终点, 速率]
  const slow = 0.03;
  SIMSEG = [
    [A('s5_11') + 2.0, A('s5_14'), 1.0],           // 挥旗 → 有序后撤 → 不可复止
    [A('s5_14'), A('s5_22'), slow],                // 讲第一步、信息级联（几乎暂停）
    [A('s5_22'), A('s5_27'), 0.42],                // 单兵视角、级联扩散（慢放）
    [A('s5_27'), A('s5_29'), 0.5],
    [A('s5_29'), A('s5_37'), 0.32],                // 一声喊 → 众遂大奔 → 苻融落马
    [A('s5_37'), A('s5_41'), slow],                // 有序 vs 溃败、小集体（暂停）
    [A('s5_41'), A('s5_44') + 8, 0.8],             // 晋军八千渡河
  ];
  EV = {
    wave: 0, seed1: simTau(A('s5_13') - 1.0), shout: simTau(A('s5_29') + 0.15),
    rongIn: simTau(A('s5_35') + 0.3), rongFall: simTau(A('s5_36') + 1.2), cross: simTau(A('s5_41') + 1.0),
  };
  const r = rng(5);
  ARMY = [];
  const cols = 45, rows = 42;
  for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) {
    const x0 = 64 + i * 19.2 + Math.floor(i / 5) * 9 + (r() - 0.5) * 5, y0 = 790 + j * 14.4 + Math.floor(j / 4) * 7 + (r() - 0.5) * 4;
    ARMY.push({ x0, y0, row: j, col: i, k: r(), k2: r(), k3: r(), ang: (r() - 0.5) * 1.4, vmax: 85 + 70 * r() });
  }
  // 阶段一（局部误读）：多个种子，沿空间慢慢传播；阶段二（溃奔）：阵后一喊、苻融落马
  const s1 = [], s2 = [];
  for (let k = 0; k < 10; k++) s1.push({ x: 120 + r() * 840, y: 860 + r() * 380, t: EV.seed1 + r() * 4, c: 38 + 18 * r() });
  s2.push({ x: 540, y: 1500, t: EV.shout, c: 260 });
  s2.push({ x: 620, y: 1120, t: EV.rongFall, c: 300 });
  for (const p of ARMY) {
    let b1 = 1e9, b2 = 1e9;
    for (const q of s1) b1 = Math.min(b1, q.t + Math.hypot(p.x0 - q.x, p.y0 - q.y) / q.c + p.k2 * 1.2);
    for (const q of s2) b2 = Math.min(b2, q.t + Math.hypot(p.x0 - q.x, p.y0 - q.y) / q.c + p.k2 * 0.8);
    // 一部分人在喊声之后仍未动摇，要等苻融落马
    if (p.k3 < 0.22) b2 = Math.max(b2, EV.rongFall + p.k * 2);
    p.tp1 = Math.min(b1, b2); p.tp2 = b2;
    p.delay = (1490 - p.y0) / 1490 * 2.4 + p.k * 0.6;                // 后排先动（命令从后方传来）
  }
  JIN = [];
  for (let i = 0; i < 420; i++) { const row = Math.floor(Math.sqrt(i)), off = i - row * row - row; JIN.push({ ox: off * 15 + (r() - 0.5) * 6, oy: -row * 15 + (r() - 0.5) * 6, k: r() }); }
}
function soldierPos(p, tau) {
  let x = p.x0, y = p.y0;
  const st = EV.wave + p.delay;
  const e0 = Math.min(tau, p.tp1);
  if (e0 > st) y += 12 * (e0 - st);                                          // 有序后撤
  let panic = 0;
  if (tau > p.tp1) {                                                          // 阶段一：跟着退，越退越快
    const u = Math.min(tau, p.tp2) - p.tp1; panic = 0.45 * clamp(u / 2);
    y += 22 * u; x += Math.sin(p.k * 30) * 10 * clamp(u / 3);
  }
  if (tau > p.tp2) {                                                          // 阶段二：溃奔
    const u = tau - p.tp2, Tr = 4; panic = 0.45 + 0.55 * clamp(u / 1.5);
    const s = u < Tr ? p.vmax * u * u / (2 * Tr) : p.vmax * (u - Tr / 2);
    const a = Math.PI / 2 + p.ang * (0.6 + 0.4 * Math.sin(u * 0.5 + p.k * 6));
    x += Math.cos(a) * s + Math.sin(u * 3 + p.k * 20) * 8; y += Math.sin(a) * s;
  }
  const jit = (tau > st ? 1 : 0) * (1.2 + 3 * panic);
  x += Math.sin(tau * 5 + p.k * 40) * jit; y += Math.cos(tau * 4 + p.k3 * 40) * jit;
  return [x, y, panic];
}
function armyCamY(tau) {
  const tt = Math.min(tau, EV.shout + 0.5);
  let s = 0; for (let i = 0; i < ARMY.length; i += 37) s += soldierPos(ARMY[i], tt)[1] - ARMY[i].y0;
  return clamp(s / Math.ceil(ARMY.length / 37) * 0.85, 0, 520);
}
function drawField(t, tau, o = {}) {
  // 淝水剖面（俯视示意）：上岸晋军，下岸秦军
  ctx.fillStyle = '#1b1f17'; ctx.fillRect(-400, -200, W + 800, H + 1400);
  const gt = ctx.createLinearGradient(0, 0, 0, 500); gt.addColorStop(0, '#23281e'); gt.addColorStop(1, '#2a2e22'); ctx.fillStyle = gt; ctx.fillRect(0, 0, W, 520);
  // 河
  const rg = ctx.createLinearGradient(0, 520, 0, 720); rg.addColorStop(0, '#173045'); rg.addColorStop(0.5, '#1d3a52'); rg.addColorStop(1, '#152a3c');
  ctx.fillStyle = rg; ctx.beginPath(); ctx.moveTo(0, 525); for (let x = 0; x <= W; x += 30) ctx.lineTo(x, 525 + 10 * Math.sin(x * 0.01)); for (let x = W; x >= 0; x -= 30) ctx.lineTo(x, 715 + 12 * Math.sin(x * 0.008 + 2)); ctx.fill();
  for (let i = 0; i < 70; i++) { const x = (hash(i, 1) * (W + 200) + t * 25) % (W + 200) - 100; ctx.fillStyle = 'rgba(190,215,235,0.16)'; ctx.fillRect(x, 545 + hash(i, 2) * 150, 50, 2); }
  // 雾
  for (let i = 0; i < 6; i++) { const x = ((t * 12 + i * 260) % (W + 600)) - 300; const g = ctx.createRadialGradient(x, 620, 10, x, 620, 260); g.addColorStop(0, 'rgba(200,210,220,0.10)'); g.addColorStop(1, 'rgba(200,210,220,0)'); ctx.fillStyle = g; ctx.fillRect(x - 260, 360, 520, 520); }
  txt('淝 水', 900, 620, { size: 40, weight: 700, color: 'rgba(170,205,230,0.7)', ls: 20 });
  // 晋军（上岸）
  const cross = clamp((tau - EV.cross) / 9);
  ctx.save(); ctx.shadowColor = C.jin; ctx.shadowBlur = 12;
  for (let i = 0; i < JIN.length; i++) {
    const q = JIN[i];
    let x = 540 + q.ox, y = 450 + q.oy;
    const myc = clamp((tau - EV.cross - q.k * 0.8) / 6);
    if (o.jin === false) continue;
    y += myc * 1100 * eio(myc);
    ctx.fillStyle = myc > 0 && y > 520 && y < 720 ? C.jinL : C.jin; ctx.fillRect(x - 4.5, y - 4.5, 9, 9);
  }
  // 晋军其余部队（静止横线）
  for (let i = 0; i < 300; i++) { const x = 60 + (i % 60) * 16 + (Math.floor(i / 60) % 2) * 8; const y = 300 + Math.floor(i / 60) * 16 - 20; if (Math.abs(x - 540) < 230 && y > 230) continue; ctx.fillStyle = rgba(C.jin, 0.75); ctx.fillRect(x - 4, y - 4, 8, 8); }
  ctx.restore();
  // 秦军
  for (const p of ARMY) {
    const [x, y, pn] = soldierPos(p, tau);
    if (y > H + 40 || x < -40 || x > W + 40) continue;
    ctx.fillStyle = pn > 0 ? mix(C.qin, '#e8f2ff', pn) : C.qin;
    const sz = 9 + 2 * pn;
    ctx.fillRect(x - sz / 2, y - sz / 2, sz, sz);
  }
  return cross;
}

function sc5(t) {
  const s = 's5', t0 = S0(s);
  const tau = simTau(t);
  // 镜头（单兵视角时推近）
  const focus = ARMY[45 * 20 + 22];
  const zf = fadeIO(t, A('s5_22') + 0.3, A('s5_24') + 1.0, 1.4, 1.4);
  const [fx, fy] = soldierPos(focus, tau);
  const zoom = lerp(1, 1.9, eio(zf));
  ctx.save();
  const camY = armyCamY(tau);
  ctx.translate(W / 2, H / 2); ctx.scale(zoom, zoom); ctx.translate(-lerp(W / 2, fx, eio(zf)), -lerp(H / 2 + camY, fy - 60, eio(zf)));
  drawField(t, tau);
  // 单兵视野圈
  if (zf > 0) {
    ctx.save(); ctx.globalAlpha = zf; ctx.strokeStyle = C.gold; ctx.lineWidth = 3 / zoom * 1.5; ctx.beginPath(); ctx.arc(fx, fy, 70, 0, Math.PI * 2); ctx.stroke();
    ctx.fillStyle = C.gold; ctx.beginPath(); ctx.arc(fx, fy, 7, 0, Math.PI * 2); ctx.fill(); ctx.restore();
  }
  // 苻融
  const rongA = P(t, A('s5_02'), 0.6);
  {
    const inU = clamp((tau - EV.rongIn) / 3), fallen = tau > EV.rongFall;
    let rx = lerp(900, 620, eio(inU)), ry = lerp(1470, 1120, eio(inU)) + camY;
    if (fallen) ry += 0;
    ctx.save(); ctx.globalAlpha = rongA * (fallen ? 1 - clamp((tau - EV.rongFall) / 4) * 0.6 : 1);
    if (!fallen) { banner(rx + 10, ry, 120, C.gold, '融', t, {}); }
    ctx.fillStyle = C.gold; ctx.beginPath(); ctx.arc(rx, ry, 14, 0, Math.PI * 2); ctx.fill();
    if (inU > 0 && !fallen) { ctx.strokeStyle = rgba(C.gold, 0.6); ctx.lineWidth = 4; ctx.setLineDash([10, 8]); ctx.beginPath(); ctx.arc(rx, ry, 150 + 10 * Math.sin(t * 4), 0, Math.PI * 2); ctx.stroke(); }
    if (fallen) { ctx.strokeStyle = C.jin; ctx.lineWidth = 9; ctx.beginPath(); ctx.moveTo(rx - 30, ry - 30); ctx.lineTo(rx + 30, ry + 30); ctx.moveTo(rx + 30, ry - 30); ctx.lineTo(rx - 30, ry + 30); ctx.stroke(); }
    ctx.restore();
    if (t > A('s5_02') && t < A('s5_14')) txt('苻融', rx + 90, ry - 40, { size: 38, weight: 800, color: C.gold, alpha: rongA, stroke: 'rgba(0,0,0,0.8)', sw: 7, align: 'left' });
    if (t > A('s5_35') && t < A('s5_38') + 2) txt(fallen ? '苻融 · 马倒被杀' : '苻融 · 驰骑略阵', rx + 170, ry - 60, { size: 40, weight: 900, color: fallen ? C.jinL : C.gold, stroke: 'rgba(0,0,0,0.85)', sw: 8, align: 'left' });
  }
  ctx.restore();

  // ---------- 叠加：对峙阶段文字与计划示意 ----------
  caption('秦军 · 逼水而陈', 1330, t, A('s5_02') + 1.5, A('s5_04'), { size: 52, color: C.qinL });
  caption('晋军 · 不得渡', 220, t, A('s5_02') + 3, A('s5_04'), { size: 52, color: C.jinL });
  // 使者
  if (t > A('s5_03') && t < A('s5_05')) {
    const u = eio((t - A('s5_03') - 0.3) / 2.5), a = fadeIO(t, A('s5_03'), A('s5_05'), 0.3, 0.4);
    const x = 300, y = lerp(500, 740, u);
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = C.jinL; ctx.beginPath(); ctx.ellipse(x, y, 30, 12, 0, 0, Math.PI * 2); ctx.fill(); ctx.restore();
    strokePath([[x, 500], [x, y]], C.jinL, 3, { alpha: a, dash: [8, 8] });
    if (t > A('s5_04')) { panel(90, 330, 900, 210, a * 0.9, C.jin); txt('谢玄：「移阵小却，使晋兵得渡，', W / 2, 400, { size: 44, weight: 800, color: C.cream, alpha: a }); txt('以决胜负，不亦善乎！」', W / 2, 470, { size: 44, weight: 800, color: C.cream, alpha: a }); }
  }
  // 诸将 vs 苻坚
  if (t > A('s5_05') && t < A('s5_08')) {
    const a = fadeIO(t, A('s5_05'), A('s5_08'), 0.3, 0.4);
    panel(80, 300, 430, 250, a * 0.9, C.goldD); txt('诸将', 295, 360, { size: 38, color: C.gold, alpha: a }); txt('守住河岸', 295, 440, { size: 56, weight: 900, color: C.cream, alpha: a }); txt('万无一失', 295, 505, { size: 40, color: '#c8c0ae', alpha: a });
    const a2 = a * P(t, A('s5_06'), 0.4);
    panel(570, 300, 430, 250, a2 * 0.9, C.qin); txt('苻坚', 785, 360, { size: 38, color: C.qinL, alpha: a2 }); txt('半渡而击', 785, 440, { size: 56, weight: 900, color: C.cream, alpha: a2 }); txt('兵书上的办法', 785, 505, { size: 40, color: '#c8c0ae', alpha: a2 });
  }
  // 计划示意（虚线）
  if (t > A('s5_08') - 0.2 && t < A('s5_11') + 1) {
    const a = fadeIO(t, A('s5_08') - 0.2, A('s5_11') + 1, 0.4, 0.5);
    const d8 = E('s5_08') - A('s5_08');
    bigArrow([[300, 850], [300, 1000]], eout((t - A('s5_08') - d8 * 0.05) / 1), C.qin, 40, { alpha: a * 0.85 }); bigArrow([[780, 850], [780, 1000]], eout((t - A('s5_08') - d8 * 0.05) / 1), C.qin, 40, { alpha: a * 0.85 });
    bigArrow([[540, 470], [540, 640]], eout((t - A('s5_08') - d8 * 0.35) / 1), C.jin, 50, { alpha: a });
    txt('渡到一半', 640, 600, { size: 40, weight: 800, color: C.jinL, alpha: a * P(t, A('s5_08') + d8 * 0.45, 0.4), align: 'left', stroke: 'rgba(0,0,0,0.8)', sw: 7 });
    bigArrow([[120, 1150], [200, 820], [430, 680]], eout((t - A('s5_08') - d8 * 0.6) / 1.2), C.qinL, 46, { alpha: a });
    bigArrow([[960, 1150], [880, 820], [650, 680]], eout((t - A('s5_08') - d8 * 0.6) / 1.2), C.qinL, 46, { alpha: a });
    txt('铁骑夹击', W / 2, 1270, { size: 52, weight: 900, color: C.qinL, alpha: a * P(t, A('s5_08') + d8 * 0.8, 0.4), stroke: 'rgba(0,0,0,0.8)', sw: 8 });
    txt('计划', 90, 1380, { size: 36, align: 'left', color: '#bdb4a2', alpha: a });
    miniQuote(t, A('s5_10') + 1.5, E('s5_10') + 0.3, '令半濟而擊之，利。', '《孫子兵法·行軍篇》', 360);
  }
  // 挥旗
  caption('挥旗 · 后撤', 330, t, A('s5_11') + 2.0, A('s5_13') - 0.2, { size: 72, color: C.gold });
  // 四步
  if (t > A('s5_14') - 0.2 && t < A('s5_15') + 0.5) {
    const a = fadeIO(t, A('s5_14') - 0.2, A('s5_15') + 0.5, 0.4, 0.4);
    ctx.save(); ctx.globalAlpha = a * 0.85; ctx.fillStyle = '#07080a'; ctx.fillRect(0, 0, W, H); ctx.restore();
    const st = ['后撤本身最难', '只能看身边的人', '一个确定的解释', '指挥节点消失'], d = E('s5_14') - A('s5_14');
    st.forEach((s0, i) => { const ai = a * P(t, A('s5_14') + d * (0.45 + 0.12 * i), 0.4); panel(120, 470 + i * 220, 840, 160, ai, i === 2 ? C.jin : C.goldD); txt(`第${'一二三四'[i]}步`, 230, 550 + i * 220, { size: 40, weight: 800, color: C.gold, alpha: ai }); txt(s0, 620, 550 + i * 220, { size: 56, weight: 900, color: C.cream, alpha: ai }); });
  }
  stepTag(t, 's5_15', 's5_18', '第一步 · 后撤最难');
  // 视线：前排看得见，后排看不见
  if (t > A('s5_16') && t < A('s5_18')) {
    const a = fadeIO(t, A('s5_16'), A('s5_18'), 0.4, 0.4);
    caption('前进：敌人在前面', 300, t, A('s5_16') + 0.3, A('s5_16') + (E('s5_16') - A('s5_16')) * 0.5 + 0.3, { size: 54 });
    caption('后退：为什么退？', 300, t, A('s5_16') + (E('s5_16') - A('s5_16')) * 0.5 + 0.3, A('s5_17'), { size: 60, color: C.gold });
    const a17 = a * P(t, A('s5_17'), 0.5);
    if (a17 > 0) {
      ctx.save(); ctx.globalAlpha = a17; const g = ctx.createLinearGradient(0, 850, 0, 1500); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(0.25, 'rgba(0,0,0,0.6)'); g.addColorStop(1, 'rgba(0,0,0,0.85)'); ctx.fillStyle = g; ctx.fillRect(0, 850, W, 900); ctx.restore();
      for (let i = 0; i < 9; i++) txt('？', 120 + i * 105 + (i % 2) * 30, 1050 + (i % 3) * 140, { size: 64, weight: 900, color: C.gold, alpha: a17 * (0.6 + 0.4 * Math.sin(t * 3 + i)) });
      txt('前排：看得见河、看得见晋军', W / 2, 330, { size: 46, weight: 800, color: C.cream, alpha: a17, glow: 'rgba(0,0,0,1)' });
      txt('后面：只看见前面的人往自己这边挤', W / 2, 1420, { size: 44, weight: 800, color: C.gold, alpha: a17 * P(t, A('s5_17') + 4, 0.5), glow: 'rgba(0,0,0,1)' });
    }
  }
  // 第二步：信息级联图示
  stepTag(t, 's5_18', 's5_27', '第二步 · 只能看身边的人');
  if (t > A('s5_19') - 0.3 && t < A('s5_22') + 0.3) cascadeDiagram(t, fadeIO(t, A('s5_19') - 0.3, A('s5_22') + 0.3, 0.5, 0.5));
  if (t > A('s5_22') && t < A('s5_27')) {
    caption('是命令？还是败了？', 330, t, A('s5_22') + 2.5, A('s5_23') + 1, { size: 60, color: C.gold });
    caption('→ 前面恐怕败了', 330, t, A('s5_23') + 3.5, A('s5_24'), { size: 64, color: C.jinL });
    caption('从后面看：一模一样', 330, t, A('s5_24') + 0.3, A('s5_25'), { size: 64, color: C.cream });
    caption('信息级联', 330, t, A('s5_25') + 0.3, A('s5_27'), { size: 76, color: C.gold });
  }
  // 第三步：秦兵败矣
  stepTag(t, 's5_27', 's5_34', '第三步 · 一个确定的解释');
  const tS = A('s5_29');
  if (t > tS - 0.3 && t < A('s5_31')) {
    const a = fadeIO(t, tS - 0.3, A('s5_31'), 0.15, 0.6);
    // 冲击波
    for (let k = 0; k < 3; k++) { const u = clamp((t - tS - k * 0.25) / 1.6); if (u <= 0 || u >= 1) continue; ctx.save(); ctx.globalAlpha = (1 - u) * a; ctx.strokeStyle = C.gold; ctx.lineWidth = 10 * (1 - u) + 2; ctx.beginPath(); ctx.arc(540, 1520, 60 + 1300 * u, 0, Math.PI * 2); ctx.stroke(); ctx.restore(); }
    ctx.save(); ctx.globalAlpha = a * 0.5; ctx.fillStyle = '#000'; ctx.fillRect(0, 300, W, 900); ctx.restore();
    const sh = (1 - P(t, tS, 0.6)) * 14;
    ['秦', '兵', '敗', '矣'].forEach((c, i) => txt(c, 210 + i * 220 + (hash(Math.floor(t * 25), i) - 0.5) * sh, 760, { size: 230, weight: 900, color: '#fff6e4', alpha: a * P(t, tS - 0.15 + i * 0.07, 0.15), glow: rgba(C.jin, 0.9), blur: 40 }));
    txt('—— 《資治通鑑》卷一百五', W - 120, 950, { size: 34, align: 'right', color: C.gold, alpha: a * P(t, tS + 0.8, 0.4) });
  }
  caption('喊话的人：朱序', 330, t, A('s5_30'), A('s5_31') + 0.5, { size: 70, color: C.gold });
  caption('模糊的信号 → 确定的答案', 330, t, A('s5_31') + 0.5, A('s5_33'), { size: 58, color: C.cream });
  caption('「众遂大奔」', 330, t, A('s5_33') + 0.5, A('s5_34') + 0.3, { size: 92, color: C.jinL });
  stepTag(t, 's5_34', 's5_41', '第四步 · 指挥节点消失');
  // 有序 vs 溃败
  if (t > A('s5_37') - 0.3 && t < A('s5_39') + 0.3) orderVsRout(t, fadeIO(t, A('s5_37') - 0.3, A('s5_39') + 0.3, 0.5, 0.5));
  if (t > A('s5_39') - 0.3 && t < A('s5_41') + 0.3) cohesionDiagram(t, fadeIO(t, A('s5_39') - 0.3, A('s5_41') + 0.3, 0.5, 0.5));
  caption('晋军精锐八千 · 渡水', 330, t, A('s5_41') + 1.5, A('s5_43'), { size: 64, color: C.jinL });
  if (t > A('s5_43') - 0.3) oneVsMany(t, P(t, A('s5_43') - 0.3, 0.6));
  // 「秦兵遂退，不可復止」卡片放在画面上部，不遮战场
  return { map: 1 };
}
function stepTag(t, a, b, s) {
  const al = fadeIO(t, A(a), A(b), 0.4, 0.4); if (al <= 0) return;
  ctx.save(); ctx.globalAlpha = al * 0.85; ctx.fillStyle = 'rgba(0,0,0,0.55)'; ctx.beginPath(); ctx.roundRect(40, 120, measure(s, 36, SERIF, 800) + 50, 62, 12); ctx.fill(); ctx.restore();
  txt(s, 65, 152, { size: 36, weight: 800, color: C.gold, align: 'left', alpha: al });
}
function cascadeDiagram(t, a) {
  ctx.save(); ctx.globalAlpha = a * 0.94; ctx.fillStyle = '#08090b'; ctx.fillRect(0, 0, W, H); ctx.restore();
  const t19 = A('s5_19'), t20 = A('s5_20');
  if (t < t20 + 0.2) {
    const b = a * (1 - P(t, t20 - 0.2, 0.4));
    txt('信息级联', W / 2, 360, { size: 92, weight: 900, color: C.gold, alpha: b });
    txt('Informational Cascade', W / 2, 450, { size: 36, font: SANS, weight: 500, color: '#a9a294', alpha: b });
    txt('Bikhchandani, Hirshleifer & Welch, 1992', W / 2, 500, { size: 28, font: SANS, weight: 400, color: '#8f897d', alpha: b });
    const n = 8, d = E('s5_19') - t19;
    for (let i = 0; i < n; i++) {
      const x = 105 + i * 124, y = 960, ti = t19 + d * (0.3 + 0.075 * i), on = P(t, ti, 0.3);
      const priv = hash(i, 3) > 0.5;
      figure(x, y, 1.2, mix('#5a5f68', C.qinL, on), { alpha: b, noSpear: true });
      // 私人信息（小点）
      ctx.save(); ctx.globalAlpha = b * (1 - on * 0.7); ctx.fillStyle = priv ? '#9fd38a' : '#d38a8a'; ctx.beginPath(); ctx.arc(x, y - 130, 12, 0, Math.PI * 2); ctx.fill(); ctx.restore();
      if (i > 0) bigArrow([[x - 110, y - 40], [x - 20, y - 40]], on, C.gold, 14, { alpha: b, blur: 6 });
    }
    txt('自己的一点信息', 200, 760, { size: 32, color: '#9fd38a', alpha: b * P(t, t19 + d * 0.2, 0.4) });
    txt('看前面的人怎么做 → 跟着做', W / 2, 1150, { size: 46, weight: 800, color: C.cream, alpha: b * P(t, t19 + d * 0.55, 0.5) });
  }
  if (t > t20 - 0.2) {
    const b = a * P(t, t20 - 0.2, 0.4);
    // 两家饭馆
    const shop = (x, name, col) => { ctx.save(); ctx.globalAlpha = b; ctx.fillStyle = '#2a2520'; ctx.fillRect(x - 150, 520, 300, 260); ctx.fillStyle = col; ctx.fillRect(x - 170, 490, 340, 60); ctx.fillStyle = '#e8b860'; ctx.fillRect(x - 40, 660, 80, 120); ctx.restore(); txt(name, x, 520, { size: 40, weight: 900, color: C.cream, alpha: b }); };
    shop(270, '左边', '#4a5a3a'); shop(810, '右边', '#7a3a2a');
    const d = E('s5_21') - t20 + (A('s5_21') - E('s5_20'));
    const q = Math.floor(clamp((t - t20 - 1.5) / (d * 0.8)) * 16);
    for (let i = 0; i < q; i++) figure(810 + (i % 2) * 40 - 20, 860 + i * 40, 0.8, i === q - 1 ? C.gold : '#8b9099', { alpha: b * clamp((t - t20 - 1.5 - i * d * 0.8 / 16) / 0.4), noSpear: true });
    figure(270, 860, 0.8, '#8b9099', { alpha: b * (1 - P(t, t20 + 3, 1)), noSpear: true });
    txt('「别人都在排」', 270, 1250, { size: 56, weight: 900, color: C.gold, alpha: b * P(t, A('s5_21') + 1.5, 0.5) });
  }
}
function orderVsRout(t, a) {
  ctx.save(); ctx.globalAlpha = a * 0.94; ctx.fillStyle = '#08090b'; ctx.fillRect(0, 0, W, H); ctx.restore();
  txt('有序后撤', 280, 400, { size: 56, weight: 900, color: C.qinL, alpha: a });
  txt('溃败', 800, 400, { size: 56, weight: 900, color: C.jinL, alpha: a });
  for (let i = 0; i < 48; i++) {
    const c = i % 6, r = Math.floor(i / 6);
    const y1 = 520 + r * 60 + ((t * 30) % 60);
    ctx.fillStyle = rgba(C.qin, a); ctx.fillRect(130 + c * 55, y1, 14, 14);
    const ang = hash(i, 2) * 6.28, d = ((t * 70 + hash(i, 3) * 400) % 500);
    ctx.fillStyle = rgba('#dfeeff', a * (1 - d / 500)); ctx.fillRect(800 + Math.cos(ang) * d * 0.5 + (hash(i, 4) - 0.5) * 120, 560 + Math.abs(Math.sin(ang)) * d + r * 20, 14, 14);
  }
  // 中间一句话
  const d37 = E('s5_37') - A('s5_37');
  const msg = ['我们是在撤', '不是在逃', '退到哪里停'];
  msg.forEach((m, i) => { const ai = a * P(t, A('s5_37') + d37 * (0.45 + 0.17 * i), 0.4); txt(m, 280, 1150 + i * 80, { size: 48, weight: 800, color: C.cream, alpha: ai }); });
  if (t > A('s5_38')) { ctx.save(); ctx.globalAlpha = a * P(t, A('s5_38') + 0.4, 0.4); ctx.strokeStyle = C.jin; ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo(110, 1100); ctx.lineTo(450, 1360); ctx.moveTo(450, 1100); ctx.lineTo(110, 1360); ctx.stroke(); ctx.restore(); txt('说这句话的人，倒下了', W / 2, 1480, { size: 50, weight: 900, color: C.jinL, alpha: a * P(t, A('s5_38') + 0.6, 0.4) }); }
}
function cohesionDiagram(t, a) {
  ctx.save(); ctx.globalAlpha = a * 0.94; ctx.fillStyle = '#08090b'; ctx.fillRect(0, 0, W, H); ctx.restore();
  txt('小集体凝聚力', W / 2, 360, { size: 76, weight: 900, color: C.gold, alpha: a });
  txt('Shils & Janowitz, 1948', W / 2, 440, { size: 32, font: SANS, weight: 500, color: '#a9a294', alpha: a });
  const brk = P(t, A('s5_40'), 2.5);
  for (let g = 0; g < 6; g++) {
    const cx = 230 + (g % 3) * 310, cy = 760 + Math.floor(g / 3) * 380;
    const pts = [];
    for (let i = 0; i < 7; i++) { const an = i / 7 * 6.28 + g; const d = 70 + brk * (200 + 300 * hash(g, i)); const a2 = an + brk * (hash(i, g) - 0.5) * 2; pts.push([cx + Math.cos(a2) * d, cy + Math.sin(a2) * d * 0.8 + brk * 200 * hash(i, g + 3)]); }
    ctx.save(); ctx.globalAlpha = a * (1 - brk); ctx.strokeStyle = rgba(C.gold, 0.8); ctx.lineWidth = 3;
    for (let i = 0; i < 7; i++) for (let j = i + 1; j < 7; j++) if ((i + j) % 2) { ctx.beginPath(); ctx.moveTo(pts[i][0], pts[i][1]); ctx.lineTo(pts[j][0], pts[j][1]); ctx.stroke(); }
    ctx.restore();
    for (const p of pts) figure(p[0], p[1] + 30, 0.55, mix(C.qin, '#dfeeff', brk), { alpha: a, noSpear: brk > 0.5 });
    ctx.save(); ctx.globalAlpha = a * (1 - brk); ctx.fillStyle = C.gold; ctx.beginPath(); ctx.arc(cx, cy, 10, 0, 6.28); ctx.fill(); ctx.restore();
  }
  txt('身边的人还在不在 · 带头的人还在不在', W / 2, 1420, { size: 42, weight: 800, color: C.cream, alpha: a * P(t, A('s5_39') + 6, 0.5) * (1 - brk) });
  txt('只想活命的个人', W / 2, 1420, { size: 60, weight: 900, color: C.jinL, alpha: a * brk });
}
function oneVsMany(t, a) {
  ctx.save(); ctx.globalAlpha = a * 0.95; ctx.fillStyle = '#08090b'; ctx.fillRect(0, 0, W, H); ctx.restore();
  const t44 = A('s5_44');
  const u = P(t, t44, 2.5);
  // 一个“人”
  ctx.save(); ctx.globalAlpha = a * (1 - u); ctx.fillStyle = C.qinD; ctx.strokeStyle = C.qinL; ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(540, 880, 300, 0, 6.28); ctx.fill(); ctx.stroke(); ctx.restore();
  txt('苻坚以为：一支大军 = 一个人', W / 2, 420, { size: 50, weight: 900, color: C.cream, alpha: a * (1 - u) * P(t, A('s5_43') + 3, 0.5) });
  // 几十万个人
  for (let i = 0; i < 260; i++) {
    const x = 120 + hash(i, 1) * 840, y = 560 + hash(i, 2) * 680;
    const sx = lerp(540 + (x - 540) * 0.5, x, u), sy = lerp(880 + (y - 880) * 0.6, y, u);
    ctx.fillStyle = rgba(C.qinL, a * u); ctx.fillRect(sx - 5, sy - 5, 10, 10);
    if (i % 9 === 0) { ctx.save(); ctx.globalAlpha = a * u * 0.5; ctx.strokeStyle = C.gold; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(sx, sy, 34, 0, 6.28); ctx.stroke(); ctx.restore(); }
  }
  txt('其实：几十万个人', W / 2, 420, { size: 60, weight: 900, color: C.qinL, alpha: a * u });
  txt('每个人只看得见身边十几步', W / 2, 1380, { size: 48, weight: 800, color: C.gold, alpha: a * P(t, t44 + 3, 0.6) });
}

// ================= S6 停不下来 =================
function nightReeds(t, a) {
  ctx.save(); ctx.globalAlpha = a;
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#05070c'); g.addColorStop(0.6, '#121a26'); g.addColorStop(1, '#06080b'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const mg = ctx.createRadialGradient(300, 520, 0, 300, 520, 220); mg.addColorStop(0, 'rgba(225,222,205,0.95)'); mg.addColorStop(0.32, 'rgba(225,222,205,0.9)'); mg.addColorStop(0.36, 'rgba(180,185,190,0.15)'); mg.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = mg; ctx.fillRect(60, 280, 480, 480);
  // 风线
  for (let i = 0; i < 40; i++) { const y = 300 + hash(i, 1) * 1100, x = ((t * (300 + 200 * hash(i, 2)) + hash(i, 3) * 2000) % 2200) - 600; ctx.strokeStyle = 'rgba(180,195,215,0.12)'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x, y); ctx.quadraticCurveTo(x + 150, y - 12, x + 320, y + 4); ctx.stroke(); }
  ctx.restore();
  // 鹤
  for (let i = 0; i < 4; i++) { const u = ((t * 0.07 + i * 0.27) % 1.3) - 0.15; crane(lerp(-150, W + 150, u), 600 + i * 70 + Math.sin(t + i) * 20, 0.9 - i * 0.12, t + i, a); }
  reeds(t, 1500, 120, 520, `rgba(4,6,9,${a})`, 5, 2.2);
}
function sc6(t) {
  const s = 's6', t0 = S0(s);
  let map = 0, act = 0;
  // 夜：风声鹤唳
  if (t < A('s6_05') + 0.5) { nightReeds(t, 1); act = 1;
    // 奔逃的小人影
    if (t > A('s6_03')) for (let i = 0; i < 14; i++) { const u = ((t - A('s6_03')) * 0.09 + hash(i, 1)) % 1; figure(lerp(-80, W + 80, u), 1330 + hash(i, 2) * 60, 0.7, `rgba(10,12,16,1)`, { run: 1, phase: t * 12 + i, noSpear: true }); }
    caption('昼夜不敢息', 1180, t, A('s6_03') + 2.5, A('s6_04') + 0.2, { size: 76, color: C.cream });
    caption('草行露宿 · 饥冻交加 · 死者十之七八', 1180, t, A('s6_04') + 0.3, A('s6_05') + 0.3, { size: 46, color: C.gold });
  }
  // 苻坚单骑
  if (t > A('s6_05') - 0.3 && t < A('s6_07') + 0.3) {
    const a = fadeIO(t, A('s6_05') - 0.3, A('s6_07') + 0.3, 0.5, 0.5);
    const cam = plateCam('region', [116.82, 32.78, 0.6]);
    ctx.save(); ctx.globalAlpha = a; drawPlate(cam, 0.5); regionRivers(cam, 1); ctx.restore();
    const p0 = mw(cam, 116.785, 32.575), p1 = mw(cam, 116.70, 32.98);
    const u = eio((t - A('s6_05') - 0.5) / 5);
    strokePath([p0, [lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u)]], C.gold, 6, { alpha: a, dash: [14, 10] });
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = C.gold; ctx.shadowColor = C.gold; ctx.shadowBlur = 20; ctx.beginPath(); ctx.arc(lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u), 14, 0, 6.28); ctx.fill(); ctx.restore();
    txt('淮北', p1[0], p1[1] - 50, { size: 44, weight: 800, color: C.cream, alpha: a, stroke: 'rgba(0,0,0,0.85)', sw: 8 });
    caption('苻坚 · 中流矢 · 单骑北走', 380, t, A('s6_05') + 0.5, A('s6_06'), { size: 54, color: C.gold });
    caption('出发时 87 万（史载） → 此刻 1 人', 380, t, A('s6_06') + 0.3, A('s6_07'), { size: 50, color: C.cream });
    map = a;
  }
  // 杜皮克：伤亡主要发生在溃逃之后（定性示意）
  if (t > A('s6_07') - 0.3 && t < A('s6_08') + 0.3) {
    const a = fadeIO(t, A('s6_07') - 0.3, A('s6_08') + 0.3, 0.5, 0.4);
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = '#08090b'; ctx.fillRect(0, 0, W, H); ctx.restore();
    txt('阿尔当·杜皮克《战斗研究》', W / 2, 380, { size: 46, weight: 800, color: C.gold, alpha: a });
    txt('Ardant du Picq, Études sur le combat', W / 2, 450, { size: 30, font: SANS, weight: 500, color: '#a9a294', alpha: a });
    const d = E('s6_07') - A('s6_07');
    const h1 = 160 * eout((t - A('s6_07') - d * 0.5) / 1), h2 = 640 * eout((t - A('s6_07') - d * 0.72) / 1.4);
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = '#6b6f76'; ctx.fillRect(220, 1300 - h1, 220, h1); ctx.fillStyle = C.jin; ctx.fillRect(640, 1300 - h2, 220, h2); ctx.fillStyle = '#555'; ctx.fillRect(160, 1300, 760, 4); ctx.restore();
    txt('两军对砍时', 330, 1360, { size: 42, weight: 800, color: C.cream, alpha: a }); txt('转身逃跑后', 750, 1360, { size: 42, weight: 800, color: C.jinL, alpha: a });
    txt('伤亡（定性示意，非数据）', W / 2, 1440, { size: 30, color: '#8f897d', alpha: a });
  }
  // 最后一个
  if (t > A('s6_08') - 0.3 && t < A('s6_10') + 0.3) {
    const a = fadeIO(t, A('s6_08') - 0.3, A('s6_10') + 0.3, 0.5, 0.4);
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = '#0a0b0e'; ctx.fillRect(0, 0, W, H); ctx.fillStyle = '#16181c'; ctx.fillRect(0, 1100, W, 820); ctx.restore();
    const stopT = A('s6_09') + 1.5;
    for (let i = 0; i < 9; i++) {
      const isStop = i === 4;
      let x = 1100 - ((t - A('s6_08')) * 160 + i * 140) % 1500;
      if (isStop && t > stopT) x = 1100 - ((stopT - A('s6_08')) * 160 + i * 140) % 1500;
      figure(x, 1100, 1.4, isStop && t > stopT ? C.gold : '#7d8794', { alpha: a, run: isStop && t > stopT ? 0 : 1, phase: t * 12 + i, noSpear: true });
      if (isStop && t > stopT + 0.5) txt('最后一个', x, 860, { size: 58, weight: 900, color: C.gold, alpha: a * P(t, stopT + 0.5, 0.4) });
    }
    // 追兵（红）从右侧逼近
    if (t > stopT + 1) { const u = clamp((t - stopT - 1) / 3); ctx.save(); ctx.globalAlpha = a * u; const g = ctx.createLinearGradient(W, 0, W - 500, 0); g.addColorStop(0, rgba(C.jin, 0.6)); g.addColorStop(1, rgba(C.jin, 0)); ctx.fillStyle = g; ctx.fillRect(W - 500, 700, 500, 500); ctx.restore(); }
    caption('为什么停不下来？', 420, t, A('s6_08'), A('s6_09'), { size: 64 });
  }
  // 自我强化回路
  const loopOn = (t > A('s6_10') - 0.3 && t < A('s6_11') + 0.3) || (t > A('s6_12') - 0.3 && t < A('s6_13') + 0.3);
  if (loopOn) {
    const a = Math.max(fadeIO(t, A('s6_10') - 0.3, A('s6_11') + 0.3, 0.5, 0.4), fadeIO(t, A('s6_12') - 0.3, A('s6_13') + 0.3, 0.5, 0.4));
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = '#08090b'; ctx.fillRect(0, 0, W, H); ctx.restore();
    const nodes = ['逃的人更多', '追兵像是真的', '没人敢先停下'];
    const R = 330, cx = 540, cy = 900;
    nodes.forEach((n, i) => { const an = -Math.PI / 2 + i * 2 * Math.PI / 3; const x = cx + Math.cos(an) * R, y = cy + Math.sin(an) * R; panel(x - 210, y - 62, 420, 124, a * 0.95, C.jin); txt(n, x, y, { size: 46, weight: 900, color: C.cream, alpha: a }); });
    for (let i = 0; i < 3; i++) {
      const a0 = -Math.PI / 2 + i * 2 * Math.PI / 3 + 0.45, a1 = a0 + 2 * Math.PI / 3 - 0.9, pts = [];
      for (let k = 0; k <= 12; k++) { const an = lerp(a0, a1, k / 12); pts.push([cx + Math.cos(an) * (R + 40), cy + Math.sin(an) * (R + 40)]); }
      bigArrow(pts, 1, C.gold, 22, { alpha: a * (0.5 + 0.5 * Math.sin(t * 4 - i * 2.1)), blur: 10 });
    }
    txt('每个人的害怕', cx, cy - 30, { size: 44, weight: 800, color: C.gold, alpha: a * P(t, A('s6_12') + 2, 0.5) });
    txt('都是别人害怕的理由', cx, cy + 40, { size: 44, weight: 800, color: C.gold, alpha: a * P(t, A('s6_12') + 3, 0.5) });
  }
  // 风声 → 证据：草木与人形
  if (t > A('s6_11') - 0.3 && t < A('s6_12') + 0.3) {
    const a = fadeIO(t, A('s6_11') - 0.3, A('s6_12') + 0.3, 0.5, 0.4);
    const d = E('s6_11') - A('s6_11');
    const m = P(t, A('s6_11') + d * 0.45, 1.2) * (1 - P(t, A('s6_11') + d * 0.95, 1.0));
    drawGrassHill(t, a, m, false);
    caption('风声 · 鹤唳 · 草木', 380, t, A('s6_11'), A('s6_11') + d * 0.5, { size: 60, color: '#cfd6de' });
    caption('都被当成了证据', 380, t, A('s6_11') + d * 0.5, A('s6_12'), { size: 66, color: C.jinL });
    act = 1;
  }
  // 孙子：围师必阙（留缺口）
  if (t > A('s6_15') - 0.3 && t < A('s6_17') + 0.3) {
    const a = fadeIO(t, A('s6_15') - 0.3, A('s6_17') + 0.3, 0.5, 0.4);
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = '#0a0b0d'; ctx.fillRect(0, 0, W, H); ctx.restore();
    const cx = 540, cy = 880;
    ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = C.jin; ctx.lineWidth = 40; ctx.shadowColor = C.jin; ctx.shadowBlur = 20; ctx.beginPath(); ctx.arc(cx, cy, 300, -Math.PI / 2 + 0.45, -Math.PI / 2 - 0.45 + 2 * Math.PI); ctx.stroke(); ctx.restore();
    for (let i = 0; i < 160; i++) {
      const out = clamp((t - A('s6_15') - 1.0 - hash(i, 1) * 5) / 3);
      const r0 = 200 * Math.sqrt(hash(i, 2)), an = hash(i, 3) * 6.28;
      let x = cx + Math.cos(an) * r0, y = cy + Math.sin(an) * r0;
      x = lerp(x, cx + (hash(i, 4) - 0.5) * 80, ein(out) * 0.7); y = lerp(y, cy - 300 - 500 * out, ein(out));
      ctx.fillStyle = rgba(C.qinL, a * (1 - out * 0.5)); ctx.fillRect(x - 5, y - 5, 10, 10);
    }
    txt('围师必阙：留一个缺口', W / 2, 1320, { size: 52, weight: 900, color: C.cream, alpha: a });
    txt('有路可走 → 想的是逃；无路可走 → 才会拼命', W / 2, 1400, { size: 38, weight: 700, color: C.gold, alpha: a * P(t, A('s6_16') + 2, 0.5) });
  }
  // 两个对照
  if (t > A('s6_17') - 0.3 && t < A('s6_18') + 0.3) {
    const a = fadeIO(t, A('s6_17') - 0.3, A('s6_18') + 0.3, 0.5, 0.4);
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = '#0a0b0d'; ctx.fillRect(0, 0, W, H); ctx.restore();
    panel(60, 420, 460, 820, a, C.goldD); panel(560, 420, 460, 820, a, C.goldD);
    txt('洛涧', 290, 500, { size: 60, weight: 900, color: C.cream, alpha: a }); txt('淝水', 790, 500, { size: 60, weight: 900, color: C.cream, alpha: a });
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = C.water; ctx.fillRect(80, 600, 420, 80); ctx.fillRect(580, 600, 420, 80); ctx.restore();
    const u = clamp((t - A('s6_17') - 0.5) / 4);
    for (let i = 0; i < 60; i++) { const x = 120 + (i % 10) * 36, y = 900 + Math.floor(i / 10) * 36; ctx.fillStyle = rgba(C.qin, a * (1 - u * 0.8 * hash(i, 1))); ctx.fillRect(x, lerp(y, 640, ein(u) * hash(i, 2)), 12, 12); }
    strokePath([[90, 760], [500, 760]], C.jin, 10, { alpha: a, glow: C.jin }); txt('退路被截 → 跳河', 290, 1150, { size: 38, weight: 800, color: C.jinL, alpha: a });
    const u2 = P(t, A('s6_17') + 3.5, 3);
    for (let i = 0; i < 60; i++) { const x = 620 + (i % 10) * 36, y = 740 + Math.floor(i / 10) * 36; ctx.fillStyle = rgba(C.qin, a); ctx.fillRect(x + (hash(i, 3) - 0.5) * 120 * u2, y + u2 * (200 + 200 * hash(i, 4)), 12, 12); }
    txt('自己让出阵地 → 散', 790, 1150, { size: 38, weight: 800, color: C.qinL, alpha: a * P(t, A('s6_17') + 3.5, 0.5) });
  }
  // 慕容垂独全、洛阳收拢
  if (t > A('s6_18') - 0.3 && t < A('s6_23') - 0.2) {
    const a = fadeIO(t, A('s6_18') - 0.3, A('s6_23') - 0.2, 0.5, 0.5);
    const cam = plateCam('macro', kf([[A('s6_18'), 114.8, 33.0, 8.5], [A('s6_22'), 114.8, 33.0, 8.5], [A('s6_23'), 112.5, 34.5, 14]], t));
    ctx.save(); ctx.globalAlpha = a; drawPlate(cam, 0.3); drawTerr(cam, 0.6); ctx.restore();
    const [sx, sy] = mw(cam, 116.785, 32.575), [lx, ly] = mw(cam, 112.45, 34.62), [mx, my] = mw(cam, 113.69, 31.26);
    const conv = P(t, A('s6_20') + 0.5, 4);
    for (let i = 0; i < 300; i++) {
      const an = hash(i, 1) * 6.28, d = 60 + 380 * hash(i, 2);
      let x = sx + Math.cos(an) * d * 1.2 - 150 * hash(i, 3), y = sy + Math.sin(an) * d * 0.8 - 120;
      x = lerp(x, lx + (hash(i, 4) - 0.5) * 70, eio(conv * (0.6 + 0.4 * hash(i, 5)))); y = lerp(y, ly + (hash(i, 6) - 0.5) * 50, eio(conv * (0.6 + 0.4 * hash(i, 5))));
      ctx.fillStyle = rgba(C.qinL, a * (0.35 + 0.5 * conv) * (hash(i, 7) > 0.35 || conv > 0.2 ? 1 : 0)); ctx.fillRect(x - 3, y - 3, 6, 6);
    }
    // 慕容垂：完整方阵
    ctx.save(); ctx.globalAlpha = a * P(t, A('s6_18') + 3, 0.6); ctx.fillStyle = C.qin; ctx.shadowColor = C.qinL; ctx.shadowBlur = 20;
    for (let i = 0; i < 36; i++) ctx.fillRect(mx - 45 + (i % 6) * 15, my - 45 + Math.floor(i / 6) * 15, 10, 10); ctx.restore();
    txt('慕容垂 · 三万 · 独全', mx, my + 95, { size: 42, weight: 900, color: C.qinL, alpha: a * P(t, A('s6_18') + 3.5, 0.5), stroke: 'rgba(0,0,0,0.85)', sw: 8 });
    txt('（在郧城，未卷入淝水）', mx, my + 150, { size: 32, weight: 700, color: C.cream, alpha: a * P(t, A('s6_18') + 5, 0.5), stroke: 'rgba(0,0,0,0.85)', sw: 6 });
    placeLabel(lx, ly, '洛阳', { alpha: a, dot: C.gold });
    txt('收拢散兵 · 十余万', lx, ly - 70, { size: 44, weight: 900, color: C.gold, alpha: a * P(t, A('s6_20') + 3, 0.5), stroke: 'rgba(0,0,0,0.85)', sw: 8 });
    caption('打掉的不是人，是组织', 380, t, A('s6_21') + 0.5, A('s6_22'), { size: 68, color: C.gold });
    caption('三八五年 · 苻坚死于姚苌之手', 380, t, A('s6_22') + 0.3, A('s6_23'), { size: 54 });
    caption('北方重新四分五裂', 470, t, A('s6_22') + 2.5, A('s6_23'), { size: 50, color: C.jinL });
    map = a;
  }
  // 可迁移的一句判断：讲给最后一排
  if (t > A('s6_23') - 0.3) {
    const a = P(t, A('s6_23') - 0.3, 0.5);
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = '#0a0a0c'; ctx.fillRect(0, 0, W, H); ctx.restore();
    for (let r = 0; r < 8; r++) {
      const sc = lerp(1.15, 0.45, r / 7), y = lerp(1350, 700, Math.pow(r / 7, 0.8)), n = 5 + r;
      for (let i = 0; i < n; i++) figure(540 + (i - (n - 1) / 2) * 150 * sc, y, sc, mix('#c9c4ba', '#4a4d53', r / 7), { alpha: a, noSpear: true });
    }
    const d = E('s6_23') - A('s6_23');
    const u = eout((t - A('s6_23') - d * 0.35) / (d * 0.5));
    bigArrow([[540, 1450], [540, 1000], [540, 650]], u, C.gold, 30, { alpha: a });
    txt('为什么退 · 退到哪', W / 2, 540, { size: 66, weight: 900, color: C.gold, alpha: a * P(t, A('s6_23') + d * 0.8, 0.5), glow: rgba(C.gold, 0.4) });
    txt('讲给最后一排的人听', W / 2, 400, { size: 50, weight: 800, color: C.cream, alpha: a * P(t, A('s6_23') + d * 0.85, 0.5) });
  }
  return { map, act };
}

// ================= S7 屐齿 =================
function sc7(t) {
  const s = 's7', t0 = S0(s);
  ctx.fillStyle = '#120e0a'; ctx.fillRect(0, 0, W, H);
  // 建康
  if (t < A('s7_02') + 0.5) {
    const cam = plateCam('macro', [117.0, 32.6, 7]);
    const a = 1 - P(t, A('s7_02'), 0.5);
    ctx.save(); ctx.globalAlpha = a; drawPlate(cam, 0.3); drawTerr(cam, 0.5); ctx.restore();
    const [x, y] = mw(cam, 118.78, 32.04); placeLabel(x, y, '建康', { alpha: a, dot: C.jin, size: 52 });
    const [x2, y2] = mw(cam, 116.785, 32.575); placeLabel(x2, y2, '淝水前线', { alpha: a * 0.8, dot: C.qin, size: 40, dx: -24, align: 'right' });
  }
  // 棋局（情景演绎）
  if (t > A('s7_02') - 0.3) {
    const a = P(t, A('s7_02') - 0.3, 0.6) * (1 - P(t, A('s7_09') - 0.2, 0.6));
    ctx.save(); ctx.globalAlpha = a;
    const g = ctx.createRadialGradient(540, 900, 50, 540, 900, 1100); g.addColorStop(0, '#2a1f14'); g.addColorStop(1, '#0a0806'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    const pt = goBoard(560, 880, 520, -0.12);
    // 落子序列（确定性）
    const moves = [[3, 3, 1], [6, 6, 0], [2, 6, 1], [6, 2, 0], [4, 5, 1], [5, 4, 0], [7, 4, 1], [3, 7, 0], [5, 7, 1], [7, 7, 0], [2, 2, 1], [8, 3, 0], [4, 2, 1], [6, 8, 0], [1, 4, 1], [8, 6, 0], [5, 2, 1], [3, 5, 0], [7, 1, 1], [4, 8, 0]];
    const t2 = A('s7_02'), tEnd = A('s7_09');
    moves.forEach((m, i) => { const ti = t2 + 1 + i * (tEnd - t2 - 4) / moves.length; const ap = P(t, ti, 0.25); if (ap > 0) { const [x, y, st] = pt(m[0], m[1]); stone(x, y - (1 - ap) * 30, st * 0.46, m[2], a * ap); } });
    ctx.restore();
    caption('「已别有旨」', 360, t, A('s7_02') + 3.5, A('s7_03'), { size: 76, color: C.cream });
    caption('以别墅为注 · 谢玄心慌而负', 360, t, A('s7_03') + 1.5, A('s7_04'), { size: 52, color: C.gold });
    // 捷报
    if (t > A('s7_04') + 1) {
      const u = eio((t - A('s7_04') - 1) / 1.6), sett = P(t, A('s7_05') + 1, 1.2);
      letterIcon(lerp(1300, 820, u) + 120 * sett, lerp(300, 450, u) + 1000 * sett, lerp(1.3, 1.0, sett), C.paper, lerp(0.4, 0.1, u), a);
      caption('捷报', 300, t, A('s7_04') + 1.5, A('s7_05') + 0.3, { size: 80, color: C.jinL });
      caption('了无喜色 · 围棋如故', 300, t, A('s7_05') + 1.5, A('s7_06') + 0.3, { size: 60, color: C.cream });
    }
    // 落下一子
    if (t > A('s7_08') - 0.5) { const [x, y, st] = pt(5, 5); const ap = P(t, A('s7_08'), 0.35); stone(x, y - (1 - ap) * 120, st * 0.46 * lerp(1.4, 1, ap), true, a * ap); }
  }
  // 门槛与木屐
  const t9 = A('s7_09');
  if (t > t9 - 0.3) {
    const a = P(t, t9 - 0.3, 0.7);
    ctx.save(); ctx.globalAlpha = a;
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#0d0a07'); g.addColorStop(0.6, '#1f170f'); g.addColorStop(1, '#0a0705'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    // 地面与门槛
    ctx.fillStyle = '#2a2016'; ctx.fillRect(0, 1180, W, 740);
    const thx = 560;
    ctx.fillStyle = '#5a3e22'; ctx.fillRect(thx - 60, 1080, 120, 110); ctx.strokeStyle = '#2a1a0a'; ctx.lineWidth = 4; ctx.strokeRect(thx - 60, 1080, 120, 110);
    ctx.fillStyle = '#3a2814'; ctx.fillRect(thx - 70, 200, 30, 880); ctx.fillRect(thx + 40, 200, 30, 880);  // 门框
    ctx.restore();
    // 木屐跨过门槛，前齿撞断；随后推成特写
    const d = E('s7_09') - t9;
    const tHit = t9 + d * 0.62;
    const walk = eio(clamp((t - t9 - 0.5) / (tHit - t9 - 0.5)));
    const brk = clamp((t - tHit) / 1.2);
    const zoomU = eio(clamp((t - tHit - 0.8) / 3.5));
    const zs = lerp(1, 1.9, zoomU);
    ctx.save(); ctx.globalAlpha = a;
    ctx.translate(540, 1080); ctx.scale(zs, zs); ctx.translate(-lerp(540, 470, zoomU), -1080);
    // 地面、门槛（横在地上的木梁）
    ctx.fillStyle = '#2a2016'; ctx.fillRect(-600, 1180, W + 1200, 900);
    const tg = ctx.createLinearGradient(0, 1110, 0, 1190); tg.addColorStop(0, '#7a5530'); tg.addColorStop(1, '#3e2914');
    ctx.fillStyle = tg; ctx.fillRect(560, 1105, 150, 80); ctx.strokeStyle = '#1e1208'; ctx.lineWidth = 4; ctx.strokeRect(560, 1105, 150, 80);
    ctx.fillStyle = '#3a2814'; ctx.fillRect(570, 120, 36, 990); ctx.fillRect(668, 120, 36, 990);
    // 木屐
    const cxp = lerp(-260, 400, walk), cyp = 1076 - Math.sin(walk * Math.PI) * 30;
    clog(cxp, cyp, 1.0, brk, t);
    if (brk > 0 && brk < 1) { ctx.save(); ctx.globalAlpha = (1 - brk); ctx.strokeStyle = '#fff2d0'; ctx.lineWidth = 3; for (let i = 0; i < 8; i++) { const an = i / 8 * 6.28; ctx.beginPath(); ctx.moveTo(530 + Math.cos(an) * 20, 1120 + Math.sin(an) * 20); ctx.lineTo(530 + Math.cos(an) * (40 + 80 * brk), 1120 + Math.sin(an) * (40 + 80 * brk)); ctx.stroke(); } ctx.restore(); }
    ctx.restore();
    // 暖光
    ctx.save(); ctx.globalAlpha = a * 0.5; const lg = ctx.createRadialGradient(560, 1050, 30, 560, 1050, 700); lg.addColorStop(0, 'rgba(255,190,110,0.35)'); lg.addColorStop(1, 'rgba(0,0,0,0)'); ctx.fillStyle = lg; ctx.fillRect(0, 300, W, 1500); ctx.restore();
  }
  return { act: t > A('s7_02') - 0.3 ? 1 : 0, map: t < A('s7_02') ? 1 : 0 };
}
