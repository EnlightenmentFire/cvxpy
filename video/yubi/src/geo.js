// 地理数据：今地经纬度。疆界为示意（546 年前后大致形势），古城址取通行考证位置。
'use strict';
const G = {
  yubi: [110.9418, 35.5631], jinyang: [112.47, 37.72], changan: [108.93, 34.30], ye: [114.38, 36.33], luoyang: [112.62, 34.72],
  tongguan: [110.25, 34.55], puban: [110.33, 34.85], pingyang: [111.52, 36.08], rangcheng: [112.09, 32.68], duling: [109.0, 34.2],
  yingchuan: [113.8, 34.12], yiyang: [112.15, 34.52], jishan: [110.98, 35.60],
  fengyi: [109.94, 34.80], fufeng: [108.2, 34.42], jingzhao: [109.05, 34.18],
  // 西魏（暖红）：关中、陇东、陕北，河东西南一角，弘农、南阳西部（示意）
  west: [[103.8, 35.4], [104.0, 36.8], [104.6, 37.9], [106.0, 38.6], [107.2, 39.3], [108.6, 39.3], [109.7, 39.0], [110.45, 38.4], [110.55, 37.4], [110.45, 36.4], [110.5, 35.95], [110.75, 35.88], [111.05, 35.76], [111.25, 35.6], [111.35, 35.3], [111.2, 35.05], [111.1, 34.85], [111.35, 34.55], [111.7, 34.2], [112.0, 33.6], [112.4, 33.1], [112.5, 32.7], [112.0, 32.3], [111.0, 32.55], [110.0, 33.05], [108.5, 33.35], [106.8, 33.5], [105.5, 33.8], [104.3, 34.3]],
  // 东魏（冷黑）：西魏以东、梁以北（示意）
  east: [[109.8, 41.8], [114.0, 42.3], [118.5, 41.4], [120.6, 39.6], [120.6, 33.9], [119.5, 33.8], [118.0, 33.2], [116.5, 32.7], [115.0, 32.45], [113.5, 32.35], [112.5, 32.7], [112.4, 33.1], [112.0, 33.6], [111.7, 34.2], [111.35, 34.55], [111.1, 34.85], [111.2, 35.05], [111.35, 35.3], [111.25, 35.6], [111.05, 35.76], [110.75, 35.88], [110.5, 35.95], [110.45, 36.4], [110.55, 37.4], [110.45, 38.4], [109.7, 39.0], [109.9, 40.3]],
  // 梁（灰）
  liang: [[103.5, 30.0], [103.5, 32.6], [105.5, 33.2], [106.8, 33.4], [108.5, 33.25], [110.0, 32.95], [111.0, 32.45], [112.0, 32.2], [113.5, 32.25], [115.0, 32.35], [116.5, 32.6], [118.0, 33.1], [119.5, 33.7], [120.6, 33.8], [120.6, 30.0]],
  // 关中（渭河盆地）示意范围
  guanzhong: [[106.9, 34.45], [107.6, 34.62], [108.4, 34.75], [109.2, 34.85], [109.9, 35.0], [110.3, 34.85], [110.2, 34.5], [109.4, 34.25], [108.5, 34.05], [107.6, 34.15]],
};
// 填充一块经纬度多边形（大尺度镜头）
function geoPoly(cam, poly, fill, stroke, o = {}) {
  ctx.save(); ctx.beginPath();
  poly.forEach((p, i) => { const [x, y] = mw(cam, p[0], p[1]); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }); ctx.closePath();
  ctx.globalAlpha *= o.alpha === undefined ? 1 : o.alpha;
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.lineJoin = 'round'; ctx.strokeStyle = stroke; ctx.lineWidth = o.w || 3; if (o.dash) ctx.setLineDash(o.dash); if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = 18; } ctx.stroke(); }
  ctx.restore();
}
// 东西魏形势（a: 整体透明度；wa/ea: 各自出现进度）
function realms(cam, a = 1, wa = 1, ea = 1, la = 1, names = ['西 魏', '东 魏', '梁']) {
  if (a <= 0) return;
  geoPoly(cam, G.liang, 'rgba(70,68,60,0.38)', 'rgba(170,160,140,0.35)', { alpha: a * la, w: 2, dash: [8, 8] });
  geoPoly(cam, G.east, 'rgba(8,12,18,0.42)', 'rgba(150,170,195,0.5)', { alpha: a * ea, w: 3 });
  geoPoly(cam, G.west, 'rgba(160,40,22,0.10)', 'rgba(255,120,90,0.9)', { alpha: a * wa, w: 3.5, glow: 'rgba(226,69,46,0.45)' });
  const R = (s, lon, lat, col, al, sz = 64) => { const [x, y] = mw(cam, lon, lat); text(s, x, y, { size: sz, fam: SERIF, wt: 900, color: col, alpha: al * 0.85, align: 'center', ls: sz * 0.35, stroke: 0, glow: 'rgba(0,0,0,0.9)', blur: 18 }); };
  R(names[0], 107.6, 36.1, '#ff9a7c', a * wa); R(names[1], 115.0, 37.7, '#b9c8d8', a * ea); R(names[2], 115.2, 31.2, '#bdb39c', a * la, 46);
}
// 玉璧一带示意城形（公里坐标，原点为 OSM 遗址点；按高程取台塬舌部）
const CITY = [[-0.22, 0.43], [0.05, 0.49], [0.26, 0.38], [0.31, 0.14], [0.28, -0.2], [0.22, -0.5], [0.0, -0.57], [-0.2, -0.5], [-0.27, -0.2], [-0.3, 0.12]];
const TOWERS = [[-0.07, -0.555], [0.12, -0.535]];
const MOUND = [0.03, -0.78];
function cityPath(cam, inset = 0) {
  ctx.beginPath();
  CITY.forEach((p, i) => { const q = lk(cam, p[0] * (1 - inset), p[1] * (1 - inset)); i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); }); ctx.closePath();
}
function drawCity(cam, o = {}) {
  const a = o.alpha === undefined ? 1 : o.alpha; if (a <= 0) return;
  ctx.save(); ctx.globalAlpha *= a;
  cityPath(cam); ctx.fillStyle = o.fill || 'rgba(226,69,46,0.16)'; ctx.fill();
  ctx.lineJoin = 'round'; ctx.shadowColor = 'rgba(255,110,80,0.8)'; ctx.shadowBlur = o.glow === undefined ? 18 : o.glow;
  ctx.strokeStyle = o.stroke || '#ff6a4a'; ctx.lineWidth = o.w || 5; ctx.stroke(); ctx.shadowBlur = 0;
  // 城垛（短刻度）
  if (o.crenel !== false && cam.km < 6) {
    ctx.strokeStyle = 'rgba(255,190,170,0.75)'; ctx.lineWidth = 2;
    for (let i = 0; i < CITY.length; i++) {
      const p = lk(cam, ...CITY[i]), q = lk(cam, ...CITY[(i + 1) % CITY.length]); const L = Math.hypot(q[0] - p[0], q[1] - p[1]); const n = Math.floor(L / 14);
      const nx = -(q[1] - p[1]) / L, ny = (q[0] - p[0]) / L;
      for (let k = 1; k < n; k++) { const x = lerp(p[0], q[0], k / n), y = lerp(p[1], q[1], k / n); ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + nx * 6, y + ny * 6); ctx.stroke(); }
    }
  }
  ctx.restore();
}
