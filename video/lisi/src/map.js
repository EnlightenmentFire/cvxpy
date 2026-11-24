/* 战国示意地图（手工经纬度折线，非精确疆界）。F.makeMap(parent) → 可控相机的 SVG 地图 */
(function () {
  const { el, lerp, clamp } = F;
  const K = 70, C0 = Math.cos(35 * Math.PI / 180);
  const P = (lon, lat) => [(lon - 103) * K * C0, (41.8 - lat) * K];
  const cr = pts => {                                   // Catmull-Rom → 三次贝塞尔
    const p = pts.map(q => P(q[0], q[1])); let d = `M${p[0][0].toFixed(1)} ${p[0][1].toFixed(1)}`;
    for (let i = 0; i < p.length - 1; i++) {
      const p0 = p[Math.max(0, i - 1)], p1 = p[i], p2 = p[i + 1], p3 = p[Math.min(p.length - 1, i + 2)];
      d += ` C${(p1[0] + (p2[0] - p0[0]) / 6).toFixed(1)} ${(p1[1] + (p2[1] - p0[1]) / 6).toFixed(1)},${(p2[0] - (p3[0] - p1[0]) / 6).toFixed(1)} ${(p2[1] - (p3[1] - p1[1]) / 6).toFixed(1)},${p2[0].toFixed(1)} ${p2[1].toFixed(1)}`;
    }
    return d;
  };
  const coast = [[124.5, 62], [124.5, 39.9], [123.3, 39.7], [122.2, 39.2], [121.2, 38.8], [121.6, 39.5], [122.2, 40.4], [121.9, 40.9], [121.0, 40.9], [120.0, 40.0], [119.4, 39.8], [118.9, 39.2], [117.8, 39.2], [117.6, 38.6], [118.3, 38.1], [118.9, 37.7], [119.0, 37.2], [119.9, 37.3], [120.7, 37.8], [121.4, 37.5], [122.5, 37.4], [122.4, 36.9], [121.5, 36.7], [120.7, 36.3], [120.3, 36.0], [119.6, 35.5], [119.2, 34.8], [120.2, 34.3], [120.9, 33.0], [121.7, 32.0], [121.9, 31.5], [121.9, 30.9], [121.0, 30.6], [120.4, 30.3], [121.4, 30.0], [122.0, 29.8], [121.9, 29.0], [121.6, 27.0], [121.0, 2]];
  const rivers = {
    he: [[103.8, 36.0], [104.5, 37.4], [105.9, 38.0], [106.7, 39.4], [107.0, 40.5], [108.5, 40.8], [110.0, 40.5], [111.2, 40.2], [111.0, 39.0], [110.8, 38.0], [110.4, 36.5], [110.5, 35.5], [110.3, 34.6], [111.2, 34.8], [112.4, 34.9], [113.6, 34.95], [114.6, 35.4], [115.2, 36.0], [115.6, 36.8], [116.2, 37.6], [117.0, 38.3], [117.6, 38.6]],
    wei: [[104.6, 35.0], [105.7, 34.6], [107.1, 34.4], [108.72, 34.34], [109.5, 34.5], [110.3, 34.6]],
    jing: [[106.9, 35.6], [107.7, 35.2], [108.3, 34.95], [108.62, 34.74], [109.0, 34.46]],
    luo: [[108.3, 37.0], [109.0, 36.2], [109.5, 35.6], [109.85, 34.95], [110.15, 34.66]],
    jiang: [[104.6, 28.8], [105.4, 28.9], [106.5, 29.6], [108.4, 30.8], [109.5, 31.0], [111.3, 30.7], [112.2, 30.3], [113.1, 29.4], [114.3, 30.6], [115.0, 30.2], [116.0, 29.7], [117.0, 30.5], [118.3, 31.3], [118.8, 32.1], [119.5, 32.2], [120.9, 31.9], [121.9, 31.5]],
    huai: [[113.5, 32.4], [114.9, 32.3], [116.8, 32.6], [117.4, 32.9], [118.5, 33.2], [119.3, 33.8], [120.2, 34.3]],
    han: [[107.0, 33.1], [109.0, 32.7], [110.8, 32.8], [111.7, 32.4], [112.1, 32.0], [112.6, 31.2], [113.4, 30.4], [114.3, 30.6]],
  };
  const states = [['秦', 107.2, 35.4], ['赵', 114.0, 37.9], ['燕', 116.6, 39.7], ['齐', 118.5, 36.5], ['魏', 114.5, 35.35], ['韩', 113.1, 34.15], ['楚', 115.3, 31.6]];
  const cities = { shangcai: ['上蔡', 114.26, 33.27], lanling: ['兰陵', 118.07, 34.86], xianyang: ['咸阳', 108.72, 34.36] };
  const canal = [[108.62, 34.74], [108.95, 34.82], [109.3, 34.86], [109.62, 34.9], [109.85, 34.95]];
  const route1 = [[114.26, 33.27], [115.4, 33.5], [116.7, 34.3], [118.07, 34.86]];
  const route2 = [[118.07, 34.86], [116.6, 35.0], [114.8, 34.75], [113.2, 34.75], [111.6, 34.7], [110.2, 34.55], [108.72, 34.36]];

  F.makeMap = function (parent) {
    const wrap = el(parent, 'abs', 'inset:0;opacity:0');
    const land = cr(coast) + ` L${P(70, 2)[0]} ${P(70, 2)[1]} L${P(70, 62)[0]} ${P(70, 62)[1]} Z`;
    wrap.innerHTML = `<svg viewBox="0 0 1080 1920" width="1080" height="1920" style="position:absolute;inset:0">
      <defs><radialGradient id="seaG" cx="50%" cy="45%" r="70%"><stop offset="0" stop-color="#0d1519"/><stop offset="1" stop-color="#070b0d"/></radialGradient>
      <linearGradient id="landG" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#231c13"/><stop offset="1" stop-color="#191510"/></linearGradient></defs>
      <rect width="1080" height="1920" fill="url(#seaG)"/>
      <g class="cam">
        <path d="${land}" fill="url(#landG)" stroke="#5d4f38" stroke-width="2" vector-effect="non-scaling-stroke" filter="url(#rough)"/>
        <path d="${land}" fill="url(#hatchD)" opacity=".16"/>
        ${Object.entries(rivers).map(([k, r]) => `<path class="rv rv-${k}" d="${cr(r)}" fill="none" stroke="#3f5868" stroke-width="${k === 'he' || k === 'jiang' ? 3.2 : 2}" vector-effect="non-scaling-stroke" stroke-linecap="round" opacity=".85"/>`).join('')}
        <g class="states">${states.map(([n, lo, la]) => `<text class="st st-${n}" x="${P(lo, la)[0]}" y="${P(lo, la)[1]}" text-anchor="middle" dominant-baseline="central" font-size="78" font-weight="900" fill="#8c7a58" opacity=".33">${n}</text>`).join('')}</g>
        <path class="canal" d="${cr(canal)}" fill="none" stroke="#e2b659" stroke-width="5" stroke-linecap="round" opacity="0"/>
        <path class="r1" d="${cr(route1)}" fill="none" stroke="#f0c56a" stroke-width="5" stroke-linecap="round" filter="url(#glow)"/>
        <path class="r2" d="${cr(route2)}" fill="none" stroke="#f0c56a" stroke-width="5" stroke-linecap="round" filter="url(#glow)"/>
        <g class="cities">${Object.entries(cities).map(([k, [n, lo, la]]) => `<g class="ct ct-${k}" transform="translate(${P(lo, la)[0]} ${P(lo, la)[1]})" opacity="0"><circle r="7" fill="#f1e3c0"/><circle r="15" fill="none" stroke="#f1e3c0" stroke-width="1.5" opacity=".6"/><text x="0" y="-26" text-anchor="middle" font-size="34" font-weight="900" fill="#f1e3c0" stroke="#0b0a09" stroke-width="6" paint-order="stroke">${n}</text></g>`).join('')}</g>
        <circle class="head" r="9" fill="#fff3c9" filter="url(#glow)" opacity="0"/>
      </g></svg>`;
    const q = s => wrap.querySelector(s);
    const cam = q('.cam'), r1 = q('.r1'), r2 = q('.r2'), head = q('.head'), canalEl = q('.canal');
    const L1 = r1.getTotalLength(), L2 = r2.getTotalLength(), LC = canalEl.getTotalLength();
    [[r1, L1], [r2, L2], [canalEl, LC]].forEach(([p, L]) => { p.setAttribute('stroke-dasharray', L); p.setAttribute('stroke-dashoffset', L); });
    const api = {
      wrap, P, q,
      /* 相机：把 (lon,lat) 放到屏幕 (cx,cy)，缩放 z */
      cam(lon, lat, z, cx = 540, cy = 800) {
        const [x, y] = P(lon, lat); cam.setAttribute('transform', `translate(${(cx - x * z).toFixed(2)} ${(cy - y * z).toFixed(2)}) scale(${z.toFixed(4)})`);
        wrap.querySelectorAll('.ct').forEach(g => { const tr = g.getAttribute('transform').split(' scale')[0]; g.setAttribute('transform', `${tr} scale(${(1 / z).toFixed(4)})`); });
        head.setAttribute('r', 9 / z); api.z = z;
        [r1, r2, canalEl].forEach(e => e.setAttribute('stroke-width', 5 / z));
        wrap.querySelectorAll('.st').forEach(e => e.setAttribute('font-size', 78 / Math.pow(z, .7)));
      },
      route(p1, p2) {
        r1.setAttribute('stroke-dashoffset', L1 * (1 - clamp(p1))); r2.setAttribute('stroke-dashoffset', L2 * (1 - clamp(p2)));
        let pt = null; if (p2 > 0 && p2 < 1) pt = r2.getPointAtLength(L2 * p2); else if (p1 > 0 && p1 < 1) pt = r1.getPointAtLength(L1 * p1);
        head.setAttribute('opacity', pt ? 1 : 0); if (pt) { head.setAttribute('cx', pt.x); head.setAttribute('cy', pt.y); }
        return pt;
      },
      /* 路线上某进度点的经纬度（给相机跟随用） */
      at(which, p) { const r = which === 1 ? r1 : r2, L = which === 1 ? L1 : L2; const pt = r.getPointAtLength(L * clamp(p)); return [pt.x / (K * C0) + 103, 41.8 - pt.y / K]; },
      canal(p, col) { canalEl.setAttribute('opacity', p > 0 ? 1 : 0); canalEl.setAttribute('stroke-dashoffset', LC * (1 - clamp(p))); if (col) canalEl.setAttribute('stroke', col); },
      city(k, o) { q('.ct-' + k).setAttribute('opacity', o); },
      state(n, o, fill) { const e = q('.st-' + n); e.setAttribute('opacity', o); if (fill) e.setAttribute('fill', fill); },
      rivers(o) { wrap.querySelectorAll('.rv').forEach(e => e.setAttribute('opacity', o)); },
      /* 经纬度 → 当前屏幕坐标 */
      screen(lon, lat) { const m = cam.getCTM(); const [x, y] = P(lon, lat); return [m.a * x + m.e, m.d * y + m.f]; },
    };
    api.cam(112, 34.5, 0.9);
    return api;
  };
})();
