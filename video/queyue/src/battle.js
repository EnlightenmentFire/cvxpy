// 战术层：却月阵、魏骑、舰船。每个点 = 一个人 / 一骑（1:1）。
'use strict';
const R_ARC = 150;          // “去水百余步”：按晋尺一步约1.47米折算 ≈ 150 米（推算）
const NW = 100, NRID0 = 3000, NRID1 = 30000;
let BT = null;              // 关键时刻
let WAG = [], SOL = null, RID = null, SHIPS = [], Y0 = 0;

function initBattle() {
  Y0 = (bankN(-R_ARC) + bankN(R_ARC)) / 2 + 3;
  BT = {
    land: A('s3', 1) + 0.6,            // 丁旿 七百人登岸
    arcDone: A('s3', 2) + 1.0,
    flag: A('s3', 3) + 2.2,            // 竖白毦
    watch: A('s3', 4) - 3.5,           // 魏骑抵近观望
    zhu: A('s3', 6) + 0.6,             // 朱超石二千人入阵
    shields: A('s3', 6) + 6.0,
    adv1: A('s4', 0) + 0.2,            // 进围
    soft: A('s4', 1) + 0.2,            // 软弓小箭
    adv2: A('s4', 1) + 3.2,            // 四面俱至
    mass: A('s4', 3) - 1.3,            // 三万骑至
    volley: A('s4', 4) + 0.15,         // 百弩俱发
    pack: A('s4', 5) - 0.4,            // 弩不能制
    spear: A('s4', 7) + 0.6,           // 断矟锤击
    rout: A('s4', 9) + 0.5,            // 一时奔溃
    chase: A('s4', 10) + 0.3 * (E('s4', 10) - A('s4', 10)),          // 追击
    chaseEnd: E('s4', 10) + 0.9, D: E('s4', 10) - A('s4', 10),
  };
  // 车
  for (let i = 0; i < NW; i++) {
    const th = Math.PI * (i + 0.5) / NW; const x = R_ARC * Math.cos(th), y = Y0 + R_ARC * Math.sin(th);
    WAG.push({ th, x, y, delay: Math.abs(i - 49.5) / 50 });
  }
  // 兵：每车 27 人（7 + 20）
  const n = NW * 27; SOL = { n, w: new Uint8Array(n), s: new Uint8Array(n), sx: new Float32Array(n), sy: new Float32Array(n), ox: new Float32Array(n), oy: new Float32Array(n), d: new Float32Array(n) };
  let k = 0; const r = rng(11);
  for (let i = 0; i < NW; i++) for (let s = 0; s < 27; s++) {
    const row = Math.floor(s / 5), col = s % 5; const rr = R_ARC - 3.4 - 1.55 * row - (r() - 0.5) * 0.3; const th = WAG[i].th + ((col - 2) * 0.93 + (r() - 0.5) * 0.25) / rr;
    SOL.w[k] = i; SOL.s[k] = s; SOL.sx[k] = rr * Math.cos(th); SOL.sy[k] = Y0 + rr * Math.sin(th);
    SOL.ox[k] = (r() - 0.5) * 110; SOL.oy[k] = Y0 - 2 - r() * 6; SOL.d[k] = r(); k++;
  }
  // 魏骑
  const N = NRID0 + NRID1; RID = { n: N, g: new Uint8Array(N), a: new Float32Array(N), r0: new Float32Array(N), r1: new Float32Array(N), r2: new Float32Array(N), h: new Float32Array(N), h2: new Float32Array(N), fall: new Float32Array(N), far: new Float32Array(N), shade: new Uint8Array(N) };
  const q = rng(23);
  for (let i = 0; i < N; i++) {
    const g = i < NRID0 ? 0 : 1; RID.g[i] = g; RID.h[i] = q(); RID.h2[i] = q(); RID.shade[i] = q() < 0.5 ? 0 : 1;
    if (g === 0) { RID.a[i] = lerp(0.42, Math.PI - 0.42, q()); RID.r0[i] = 400 + 190 * q(); RID.r1[i] = 205 + 120 * q(); RID.r2[i] = 164 + 80 * Math.pow(q(), 1.4); RID.far[i] = 1500 + 500 * q(); }
    else { RID.a[i] = lerp(0.035, Math.PI - 0.035, q()); const u = q(); RID.r2[i] = Math.sqrt(lerp(166 * 166, 395 * 395, u)); RID.far[i] = 1300 + 900 * q(); }
    RID.fall[i] = 1e9;
  }
  // 伤亡时刻
  for (let i = 0; i < N; i++) {
    const rp = 160 + (RID.r2[i] - 160) * 0.8;
    if (RID.r2[i] < 240 && hash(i, 7) < 0.2) RID.fall[i] = BT.volley + 0.3 + (RID.r2[i] - 160) / 380 + hash(i, 8) * 2.2;
    else if (rp < 176 && hash(i, 9) < 0.42) RID.fall[i] = lerp(BT.pack + 1, BT.spear, hash(i, 10));          // 丛箭
    else if (rp < 205 && hash(i, 11) < 0.62) RID.fall[i] = lerp(BT.spear + 0.4, BT.rout + 0.6, Math.pow(hash(i, 12), 0.8));   // 断槊
  }
  // 舰船：主队泊于河中，另有登岸小船
  const s = rng(5);
  for (let i = 0; i < 44; i++) { const col = i % 2, row = Math.floor(i / 2); SHIPS.push({ x: -780 + row * 74 + (s() - 0.5) * 16, y: bankN(0) - 170 - col * 62 - (s() - 0.5) * 12, len: 36 + s() * 10, big: i % 9 === 4 }); }
}

function wagonPos(i, tb) {  // 车从登岸点展开到弧位
  const w = WAG[i]; const u = eio(prog(tb, BT.land + 1.2 + w.delay * 4.2, BT.land + 4.4 + w.delay * 5.2));
  const lx = (i - 49.5) * 0.9, ly = Y0 + 4;
  return [lerp(lx, w.x, u), lerp(ly, w.y, u), u];
}

function drawShips(cam, tb, o = {}) {
  const sc = 1 / cam.mpp;
  ctx.save();
  for (const sh of SHIPS) {
    const [x, y] = tw(cam, sh.x, sh.y + Math.sin(tb * 0.5 + sh.x) * 0.6); if (x < -80 || x > W + 80 || y < -40 || y > H + 40) continue;
    drawShip(x, y, sh.len * sc, Math.PI, sh.big);
  }
  ctx.restore();
}
function drawShip(x, y, len, ang, big, alpha = 1, dark = 0) {
  const w = len * 0.24; ctx.save(); ctx.translate(x, y); ctx.rotate(ang); ctx.globalAlpha *= alpha;
  ctx.fillStyle = 'rgba(0,0,0,0.3)'; ctx.beginPath(); ctx.ellipse(len * 0.04, w * 0.35, len * 0.52, w * 0.62, 0, 0, 7); ctx.fill();
  // 船体（船头朝 +x）
  ctx.beginPath(); ctx.moveTo(len / 2, 0); ctx.quadraticCurveTo(len * 0.32, -w / 2, -len * 0.42, -w * 0.46); ctx.lineTo(-len / 2, -w * 0.3); ctx.lineTo(-len / 2, w * 0.3); ctx.lineTo(-len * 0.42, w * 0.46); ctx.quadraticCurveTo(len * 0.32, w / 2, len / 2, 0); ctx.closePath();
  ctx.fillStyle = dark ? '#2a2019' : '#6b4526'; ctx.fill(); ctx.strokeStyle = dark ? '#3a2c22' : '#e6c68c'; ctx.lineWidth = Math.max(1.5, len * 0.04); ctx.stroke();
  // 舱/帆 —— 宋军红
  ctx.fillStyle = dark ? '#3b2a22' : (big ? '#d43c26' : '#c23522'); ctx.fillRect(-len * 0.28, -w * 0.3, len * 0.5, w * 0.6);
  if (!dark) { ctx.fillStyle = '#ff7a5c'; ctx.fillRect(-len * 0.28, -w * 0.3, len * 0.5, w * 0.16); }
  ctx.restore();
}

// 画阵：tb 为战斗时间（全局时间轴）
function drawFormation(cam, tb, o = {}) {
  const sc = 1 / cam.mpp; const shieldU = P(tb, BT.shields, 2.0);
  // 登岸小船
  const boats = (t0, n, seed) => { for (let b = 0; b < n; b++) { const u0 = prog(tb, t0 - 4.5 + b * 0.25, t0 - 0.6 + b * 0.25), u1 = prog(tb, t0 + 9 + b * 0.3, t0 + 13 + b * 0.3); if (u0 <= 0 || u1 >= 1) continue; const bx = (b - (n - 1) / 2) * 16 + (hash(b, seed) - 0.5) * 6; const y = lerp(bankN(0) - 165, Y0 - 9, eio(u0)) - eio(u1) * 155; const [x, yy] = tw(cam, bx, y); drawShip(x, yy, 15 * sc, u1 > 0 ? Math.PI / 2 : -Math.PI / 2, false); } };
  boats(BT.land, 9, 1); boats(BT.zhu, 14, 2);
  // 兵
  const ps = Math.max(1.7, 0.95 * sc);
  ctx.fillStyle = C.red; ctx.beginPath();
  for (let k = 0; k < SOL.n; k++) {
    const i = SOL.w[k], s = SOL.s[k]; let x, y;
    if (s < 7) { const wp = wagonPos(i, tb); if (tb < BT.land) continue; const u = wp[2]; const lu = P(tb, BT.land + SOL.d[k] * 0.8, 1.2); if (lu <= 0) continue; x = lerp(wp[0] + (SOL.sx[k] - WAG[i].x) * 0.6, SOL.sx[k], u); y = lerp(wp[1] - 2.5 - (s % 3) * 1.2, SOL.sy[k], u); }
    else { const t0 = BT.zhu + SOL.d[k] * 2.6 + WAG[i].delay * 1.4; const u = eio(prog(tb, t0, t0 + 3.6 + WAG[i].delay * 1.6)); if (tb < t0) continue; x = lerp(SOL.ox[k], SOL.sx[k], u); y = lerp(SOL.oy[k], SOL.sy[k], u); x += Math.sin(u * Math.PI) * (SOL.sx[k] > 0 ? 1 : -1) * 6; }
    const [px, py] = tw(cam, x, y); if (px < -4 || px > W + 4 || py < -4 || py > H + 4) continue;
    if (ps >= 5) { ctx.moveTo(px + ps * 0.46, py); ctx.arc(px, py, ps * 0.46, 0, 6.3); } else ctx.rect(px - ps / 2, py - ps / 2, ps, ps);
  }
  ctx.fill(); if (ps >= 5) { ctx.strokeStyle = '#5a1309'; ctx.lineWidth = 1.2; ctx.stroke(); }
  // 追击分队（阵外）
  if (tb > BT.chase - 0.2 && !o.noChase) drawChase(cam, tb);
  // 车
  if (tb >= BT.land + 1.0) {
    for (let i = 0; i < NW; i++) {
      const wp = wagonPos(i, tb); const [px, py] = tw(cam, wp[0], wp[1]); if (px < -20 || px > W + 20 || py < -20 || py > H + 20) continue;
      const th = WAG[i].th; const ang = lerp(Math.PI / 2, th + Math.PI / 2, wp[2]);   // 屏幕角：切向
      ctx.save(); ctx.translate(px, py); ctx.rotate(-ang);
      const L = 4.2 * sc, Wd = 1.9 * sc;
      ctx.fillStyle = '#3a2716'; ctx.fillRect(-L / 2, -Wd / 2, L, Wd); ctx.fillStyle = '#b58a52'; ctx.fillRect(-L / 2 + sc * 0.2, -Wd / 2 + sc * 0.2, L - sc * 0.4, Wd - sc * 0.4);
      if (sc > 3) { ctx.fillStyle = '#1e140b'; ctx.fillRect(-sc * 0.7, -Wd / 2 - sc * 0.32, sc * 1.4, sc * 0.3); ctx.fillRect(-sc * 0.7, Wd / 2 + sc * 0.02, sc * 1.4, sc * 0.3); ctx.strokeStyle = '#6b4a26'; ctx.lineWidth = Math.max(1, sc * 0.12); for (let q = -1; q <= 1; q++) { ctx.beginPath(); ctx.moveTo(q * L * 0.25, -Wd / 2 + sc * 0.2); ctx.lineTo(q * L * 0.25, Wd / 2 - sc * 0.2); ctx.stroke(); } }
      if (shieldU > 0) {   // 彭排：外侧大盾
        const su = clamp(shieldU * 1.6 - WAG[i].delay * 0.6);
        if (su > 0) { ctx.globalAlpha = su; ctx.fillStyle = '#f2dfb4'; ctx.fillRect(-L / 2 - sc * 0.15, -Wd / 2 - sc * 1.25, L + sc * 0.3, Math.max(2, sc * 0.75)); ctx.fillStyle = C.red; ctx.fillRect(-L / 2 - sc * 0.15, -Wd / 2 - sc * 0.5, L + sc * 0.3, Math.max(1, sc * 0.28)); }
      }
      ctx.restore();
    }
  }
  // 白毦
  const fu = P(tb, BT.flag, 0.8);
  if (fu > 0 && !o.noFlag) {
    const [fx, fy] = tw(cam, 0, Y0 + 62); const hgt = 46 * fu * Math.min(1.6, Math.max(1, sc * 0.5));
    ctx.save(); ctx.strokeStyle = '#2b1d12'; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(fx, fy); ctx.lineTo(fx, fy - hgt); ctx.stroke();
    ctx.shadowColor = '#fff'; ctx.shadowBlur = 22 + 8 * Math.sin(tb * 3); ctx.fillStyle = '#ffffff';
    ctx.beginPath(); const fl = hgt * 0.62, wv = Math.sin(tb * 4) * 3; ctx.moveTo(fx, fy - hgt); ctx.quadraticCurveTo(fx + fl * 0.5, fy - hgt - 6 + wv, fx + fl, fy - hgt + 4 - wv); ctx.quadraticCurveTo(fx + fl * 0.5, fy - hgt + 14 + wv, fx, fy - hgt + 16); ctx.closePath(); ctx.fill(); ctx.restore();
  }
}

function drawChase(cam, tb) {   // 朱超石率胡藩、刘荣祖追击：出阵北追，被围，奋击尽日
  const u = eio(prog(tb, BT.chase, BT.chase + 0.3 * BT.D)); const cx = 30, cy = Y0 + R_ARC + 14 + u * 330; const sc = 1 / cam.mpp;
  const n = 420, ps = Math.max(1.7, 0.95 * sc); ctx.fillStyle = C.redL; ctx.beginPath();
  for (let k = 0; k < n; k++) { const a = hash(k, 31) * 6.283, rr = Math.sqrt(hash(k, 32)) * (16 + 22 * u); const [px, py] = tw(cam, cx + Math.cos(a) * rr * 1.3, cy + Math.sin(a) * rr - (1 - u) * hash(k, 33) * 30); ctx.rect(px - ps / 2, py - ps / 2, ps, ps); }
  ctx.fill();
}

function riderPos(i, tb, out) {
  const a = RID.a[i], h = RID.h[i], h2 = RID.h2[i]; let r, dead = false;
  const rp = 160 + (RID.r2[i] - 160) * 0.8;
  if (RID.g[i] === 0) {
    const u0 = eio(prog(tb, BT.watch + h * 2.5, BT.watch + 5 + h * 3)); r = lerp(RID.far[i], RID.r0[i], u0);
    const u1 = eio(prog(tb, BT.adv1 + h2 * 1.5, BT.adv1 + 3.5 + h2 * 2)); r = lerp(r, RID.r1[i], u1);
    const u2 = eio(prog(tb, BT.adv2 + h * 1.2, BT.adv2 + 3 + h * 1.5)); r = lerp(r, RID.r2[i], u2);
  } else {
    const t0 = BT.mass + h * 2.0 + (RID.r2[i] - 166) / 230 * 1.6; const u = eout(prog(tb, t0, t0 + 3.2)); if (u <= 0) { out[2] = -1; return; }
    r = lerp(RID.far[i], RID.r2[i], u);
  }
  const up = eio(prog(tb, BT.pack + h2 * 1.5, BT.pack + 3 + h2 * 1.5)); r = lerp(r, Math.min(r, rp), up);
  let ang = a + Math.sin(tb * (0.5 + h) + h2 * 20) * 0.9 / Math.max(160, r);     // 游动
  r += Math.sin(tb * (0.8 + h2) + h * 30) * 1.3;
  const ft = RID.fall[i];
  if (tb >= ft) { dead = true; }
  else if (tb > BT.rout) {
    const d = (rp - 160) / 240 * 1.6 + 0.9 * h; const dt = tb - BT.rout - d;
    if (dt > 0) { r += (26 + 30 * h2) * dt * Math.min(1, dt / 1.2); ang += (h - 0.5) * 0.25 * Math.min(1, dt / 3); }
  }
  out[0] = r * Math.cos(ang); out[1] = Y0 + r * Math.sin(ang); out[2] = dead ? 1 : 0;
}

function drawRiders(cam, tb, o = {}) {
  if (tb < BT.watch) return;
  const sc = 1 / cam.mpp, ps = tb < BT.mass ? Math.max(3.3, 2.1 * sc) : Math.max(2.3, 1.55 * sc), out = [0, 0, 0];
  const paths = [new Path2D(), new Path2D(), new Path2D()];
  for (let i = 0; i < RID.n; i++) {
    riderPos(i, tb, out); if (out[2] < 0) continue;
    // 追击阶段：部分溃骑回头围住追兵
    if (out[2] === 0 && tb > BT.chase + 0.1 * BT.D && i % 5 === 0 && RID.g[i] === 1 && Math.abs(RID.a[i] - Math.PI / 2) < 0.75 && !o.noChase) {
      const u = eio(prog(tb, BT.chase + (0.1 + RID.h[i] * 0.1) * BT.D, BT.chase + (0.38 + RID.h[i] * 0.1) * BT.D)), v = eio(prog(tb, BT.chaseEnd - 1.6 + RID.h2[i] * 0.6, BT.chaseEnd + 1));
      const ca = RID.h2[i] * 6.283, cr = 70 + 60 * RID.h[i]; const tx = 30 + Math.cos(ca) * cr * 1.25, ty = Y0 + R_ARC + 344 + Math.sin(ca) * cr;
      out[0] = lerp(out[0], tx, u * (1 - v)); out[1] = lerp(out[1], ty, u * (1 - v)) + v * 500;
    }
    const [px, py] = tw(cam, out[0], out[1]); if (px < -4 || px > W + 4 || py < -4 || py > H + 4) continue;
    const pth = out[2] === 1 ? paths[2] : paths[RID.shade[i]];
    if (ps >= 5) { const an = Math.atan2(out[1] - Y0, out[0]); pth.moveTo(px + ps * 0.8, py); pth.ellipse(px, py, ps * 0.8, ps * 0.36, -an, 0, 6.3); }
    else pth.rect(px - ps / 2, py - ps / 2, ps, ps * 0.9);
  }
  ctx.fillStyle = '#3d2f2b'; ctx.fill(paths[2]);
  if (ps > 2.6) { ctx.save(); ctx.translate(1.2, 1.4); ctx.fillStyle = 'rgba(12,22,30,0.5)'; ctx.fill(paths[0]); ctx.fill(paths[1]); ctx.restore(); }
  ctx.fillStyle = '#5db9f2'; ctx.fill(paths[0]); ctx.fillStyle = '#e2f5ff'; ctx.fill(paths[1]);
}

// 箭矢 / 弩矢 / 断槊
function drawMissiles(cam, tb) {
  const sc = 1 / cam.mpp; ctx.save(); ctx.lineCap = 'round';
  // 软弓小箭：稀疏、无力、落在阵前
  if (tb > BT.soft && tb < BT.volley) {
    for (let k = 0; k < 90; k++) { const per = 1.5 + hash(k, 1); const u = ((tb - BT.soft) / per + hash(k, 2)) % 1; const th = lerp(0.15, Math.PI - 0.15, hash(k + Math.floor((tb - BT.soft) / per + hash(k, 2)) * 7, 3)); const r0 = R_ARC + 2, r1 = R_ARC + 34 + 30 * hash(k, 4); const r = lerp(r0, r1, u); const [x0, y0] = tw(cam, r * Math.cos(th), Y0 + r * Math.sin(th)), [x1, y1] = tw(cam, (r - 7) * Math.cos(th), Y0 + (r - 7) * Math.sin(th)); ctx.strokeStyle = `rgba(255,235,200,${0.5 * (1 - u)})`; ctx.lineWidth = 1.4; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke(); }
  }
  // 百弩齐发：三轮
  for (let v = 0; v < 4; v++) {
    const tv = BT.volley + v * 1.7; if (tv > BT.pack + 2.5) break; const u = (tb - tv) / 0.55; if (u < 0 || u > 1.25) continue;
    for (let i = 0; i < NW; i++) { const th = WAG[i].th + (hash(i, v) - 0.5) * 0.05; const r1 = R_ARC + 6 + u * 190, r0 = Math.max(R_ARC + 4, r1 - 60); if (u > 1) continue; const [x0, y0] = tw(cam, r0 * Math.cos(th), Y0 + r0 * Math.sin(th)), [x1, y1] = tw(cam, r1 * Math.cos(th), Y0 + r1 * Math.sin(th)); const g = ctx.createLinearGradient(x0, y0, x1, y1); g.addColorStop(0, 'rgba(255,220,150,0)'); g.addColorStop(1, 'rgba(255,244,214,0.95)'); ctx.strokeStyle = g; ctx.lineWidth = Math.max(2, 1.2 * sc); ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke(); }
    // 齐射闪光
    if (u < 0.3) { ctx.strokeStyle = `rgba(255,236,190,${0.55 * (1 - u / 0.3)})`; ctx.lineWidth = 8 * sc; ctx.beginPath(); const [cx, cy] = tw(cam, 0, Y0); ctx.arc(cx, cy, (R_ARC + 3) * sc, Math.PI, 2 * Math.PI); ctx.stroke(); }
  }
  // 丛箭
  if (tb > BT.volley + 1 && tb < BT.rout) {
    for (let k = 0; k < 160; k++) { const per = 0.7 + hash(k, 5) * 0.6; const ph = (tb - BT.volley) / per + hash(k, 6); const u = ph % 1; const th = lerp(0.06, Math.PI - 0.06, hash(k + Math.floor(ph) * 13, 7)); const r1 = R_ARC + 4 + u * 70, r0 = r1 - 12; const [x0, y0] = tw(cam, r0 * Math.cos(th), Y0 + r0 * Math.sin(th)), [x1, y1] = tw(cam, r1 * Math.cos(th), Y0 + r1 * Math.sin(th)); ctx.strokeStyle = `rgba(255,236,200,${0.7 * (1 - u)})`; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke(); }
  }
  // 断槊：短促、粗重的贯穿（分三档透明度合批，避免逐条阴影）
  if (tb > BT.spear && tb < BT.rout + 1.2) {
    const P3 = [new Path2D(), new Path2D(), new Path2D()], F3 = [new Path2D(), new Path2D()];
    for (let k = 0; k < 64; k++) { const per = 0.55 + hash(k, 8) * 0.5; const ph = (tb - BT.spear) / per + hash(k, 9); const u = ph % 1; if (u > 0.5) continue; const wi = Math.floor(hash(k + Math.floor(ph) * 17, 10) * NW); const th = WAG[wi].th; const uu = u / 0.5; const r0 = R_ARC + 2.5, r1 = r0 + 13 * eout(uu); const [x0, y0] = tw(cam, r0 * Math.cos(th), Y0 + r0 * Math.sin(th)), [x1, y1] = tw(cam, r1 * Math.cos(th), Y0 + r1 * Math.sin(th)); if (x0 < -40 || x0 > W + 40 || y0 < -40 || y0 > H + 40) continue; const pb = P3[Math.min(2, Math.floor(uu * 3))]; pb.moveTo(x0, y0); pb.lineTo(x1, y1); if (uu < 0.25) { const fb = F3[uu < 0.12 ? 0 : 1]; fb.moveTo(x0 + 10, y0); fb.arc(x0, y0, Math.min(14, 2.2 * sc), 0, 7); } }
    ctx.shadowColor = '#ffb070'; ctx.shadowBlur = 12; ctx.lineWidth = Math.max(3, 0.9 * sc);
    [1, 0.72, 0.4].forEach((al, q) => { ctx.strokeStyle = `rgba(255,240,215,${al})`; ctx.stroke(P3[q]); });
    ctx.shadowBlur = 0; ctx.fillStyle = 'rgba(255,214,150,0.85)'; ctx.fill(F3[0]); ctx.fillStyle = 'rgba(255,214,150,0.4)'; ctx.fill(F3[1]);
  }
  ctx.restore();
}
// 一整套战术画面
function drawBattle(cam, tb, o = {}) {
  drawTac(cam, o.dim === undefined ? 0.1 : o.dim); drawFlow(cam, tb);
  drawShips(cam, tb);
  drawRiders(cam, tb, o);
  drawFormation(cam, tb, o);
  if (!o.noMissiles) drawMissiles(cam, tb);
}
