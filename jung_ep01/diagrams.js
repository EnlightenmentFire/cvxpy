// 三个简图：能量流向（s2d）、意识/无意识互补（s4b）、坐标轴不是盒子（s6e）。
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  const mk = (p, tag, attrs = {}, text) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (text != null) e.textContent = text; p.appendChild(e); return e; };
  const INK = '#ece7db', BLUE = '#9dbbd8', DIM = '#a9a79f';
  const tOr = (expr, fb) => { try { return T(expr); } catch (e) { return fb; } };

  // ───────── s2d 能量流向 ─────────
  (function () {
    const svg = document.getElementById('flow'); if (!svg) return;
    const defs = mk(svg, 'defs');
    const rg = mk(defs, 'radialGradient', { id: 'core' });
    mk(rg, 'stop', { offset: '0', 'stop-color': '#ffffff', 'stop-opacity': '0.95' });
    mk(rg, 'stop', { offset: '0.35', 'stop-color': BLUE, 'stop-opacity': '0.55' });
    mk(rg, 'stop', { offset: '1', 'stop-color': BLUE, 'stop-opacity': '0' });
    const HX = 444, HY = 300, HR = 74;
    // 人形：头 + 肩
    const body = mk(svg, 'g', { fill: 'rgba(236,231,219,0.035)', stroke: INK, 'stroke-width': 3, 'stroke-linecap': 'round' });
    mk(body, 'path', { d: `M 226 620 C 226 462 330 408 444 408 C 558 408 662 462 662 620` });
    mk(body, 'circle', { cx: HX, cy: HY, r: HR });
    const core = mk(svg, 'circle', { cx: HX, cy: HY, r: 70, fill: 'url(#core)', opacity: 0 });
    const inner1 = mk(svg, 'text', { x: HX, y: 520, 'text-anchor': 'middle', 'font-size': 33, fill: INK, opacity: 0, 'letter-spacing': 1 }, '在我心里是什么？');
    const inner2 = mk(svg, 'text', { x: HX, y: 578, 'text-anchor': 'middle', 'font-size': 33, fill: INK, opacity: 0, 'letter-spacing': 1 }, '我自己怎么看？');
    const nodes = [
      { x: 118, y: 150, label: '现在什么情况？', lx: 118, ly: 92, cue: 'L11c2' },
      { x: 444, y: 70, label: '别人怎么做？', lx: 444, ly: 34, cue: 'L11c3' },
      { x: 770, y: 150, label: '结果会怎样？', lx: 770, ly: 92, cue: 'L11c4' },
    ];
    for (const n of nodes) {
      const dx = n.x - HX, dy = n.y - HY, L = Math.hypot(dx, dy), ux = dx / L, uy = dy / L;
      n.ax = HX + ux * (HR + 16); n.ay = HY + uy * (HR + 16);          // 靠头一端
      n.bx = n.x - ux * 30; n.by = n.y - uy * 30;                        // 靠客体一端
      n.ang = Math.atan2(uy, ux) * 180 / Math.PI;
      n.g = mk(svg, 'g', { opacity: 0 });
      n.line = mk(n.g, 'line', { x1: n.ax, y1: n.ay, x2: n.bx, y2: n.by, stroke: BLUE, 'stroke-width': 4, 'stroke-dasharray': '4 18', 'stroke-linecap': 'round' });
      n.headOut = mk(n.g, 'path', { d: 'M 0 0 L -22 -11 L -22 11 Z', fill: BLUE, transform: `translate(${n.bx + ux * 8},${n.by + uy * 8}) rotate(${n.ang})` });
      n.headIn = mk(n.g, 'path', { d: 'M 0 0 L -22 -11 L -22 11 Z', fill: BLUE, opacity: 0, transform: `translate(${n.ax - ux * 8},${n.ay - uy * 8}) rotate(${n.ang + 180})` });
      n.dot = mk(n.g, 'circle', { cx: n.x, cy: n.y, r: 13, fill: 'none', stroke: INK, 'stroke-width': 3 });
      n.dotFill = mk(n.g, 'circle', { cx: n.x, cy: n.y, r: 6, fill: INK });
      n.txt = mk(n.g, 'text', { x: n.lx, y: n.ly, 'text-anchor': 'middle', 'font-size': 34, fill: INK, 'letter-spacing': 1 }, n.label);
    }
    const ext = document.getElementById('d-ext'), int = document.getElementById('d-int');
    const cap1 = document.getElementById('d-cap1'), cap2 = document.getElementById('d-cap2');
    registerAnim('s2d', (t) => {
      const t0 = T('L11'), sw = T('L12') - 0.25;
      const k = smooth((t - sw) / 0.8);                 // 0 外向 → 1 内向
      ext.style.opacity = (ease((t - t0) / 0.7) * (1 - smooth((t - sw) / 0.4))).toFixed(3);
      int.style.opacity = smooth((t - sw - 0.3) / 0.5).toFixed(3);
      cap1.style.opacity = (ease((t - T('L11c1')) / 0.7) * (1 - smooth((t - sw) / 0.4))).toFixed(3);
      cap2.style.opacity = smooth((t - T('L12c1')) / 0.6).toFixed(3);
      for (const n of nodes) {
        const a = ease((t - T(n.cue)) / 0.7);
        n.g.setAttribute('opacity', a.toFixed(3));
        const dir = 1 - 2 * k;                          // +1 向外流，-1 向内流
        // 虚线流动：分两段积分，换向时不跳
        const off = t < sw ? -(t - t0) * 46 : -(sw - t0) * 46 + (t - sw) * 46;
        n.line.setAttribute('stroke-dashoffset', off.toFixed(2));
        n.headOut.setAttribute('opacity', (1 - k).toFixed(3));
        n.headIn.setAttribute('opacity', k.toFixed(3));
        n.dot.setAttribute('opacity', (1 - 0.55 * k).toFixed(3));
        n.dotFill.setAttribute('opacity', (1 - 0.8 * k).toFixed(3));
        n.txt.setAttribute('opacity', (1 - 0.62 * k).toFixed(3));
      }
      const pulse = 0.82 + 0.18 * Math.sin((t - sw) * 2.2);
      core.setAttribute('opacity', (k * pulse).toFixed(3));
      inner1.setAttribute('opacity', ease((t - T('L12c1')) / 0.7).toFixed(3));
      inner2.setAttribute('opacity', ease((t - T('L12c2')) / 0.7).toFixed(3));
    });
  })();

  // ───────── s4b 互补 ─────────
  (function () {
    const svg = document.getElementById('comp'); if (!svg) return;
    const X0 = 150, X1 = 738, CX = 444, YT = 150, YB = 430, YW = 290;
    mk(svg, 'rect', { x: 0, y: 20, width: 888, height: 250, rx: 10, fill: 'rgba(236,231,219,0.055)' });
    mk(svg, 'rect', { x: 0, y: 310, width: 888, height: 250, rx: 10, fill: 'rgba(20,28,48,0.55)' });
    mk(svg, 'line', { x1: 0, y1: YW, x2: 888, y2: YW, stroke: DIM, 'stroke-width': 2, 'stroke-dasharray': '10 12', opacity: 0.6 });
    mk(svg, 'text', { x: 28, y: 72, 'font-size': 36, fill: INK, 'font-weight': 700, 'letter-spacing': 6 }, '意识');
    mk(svg, 'text', { x: 28, y: 362, 'font-size': 36, fill: DIM, 'font-weight': 700, 'letter-spacing': 6 }, '无意识');
    for (const [y, op] of [[YT, 0.9], [YB, 0.55]]) {
      mk(svg, 'line', { x1: X0, y1: y, x2: X1, y2: y, stroke: INK, 'stroke-width': 2.5, opacity: op });
      mk(svg, 'line', { x1: CX, y1: y - 12, x2: CX, y2: y + 12, stroke: INK, 'stroke-width': 2.5, opacity: op });
      mk(svg, 'text', { x: X0 - 22, y: y + 12, 'text-anchor': 'end', 'font-size': 32, fill: INK, opacity: op }, '内向');
      mk(svg, 'text', { x: X1 + 22, y: y + 12, 'font-size': 32, fill: INK, opacity: op }, '外向');
    }
    const rod = mk(svg, 'line', { stroke: BLUE, 'stroke-width': 3, opacity: 0.75 });
    mk(svg, 'path', { d: `M ${CX} ${YW - 13} L ${CX + 13} ${YW} L ${CX} ${YW + 13} L ${CX - 13} ${YW} Z`, fill: BLUE });
    const dT = mk(svg, 'circle', { r: 19, fill: INK }), dB = mk(svg, 'circle', { r: 19, fill: 'none', stroke: INK, 'stroke-width': 4 });
    const lbl = mk(svg, 'text', { x: CX + 26, y: YW + 46, 'font-size': 30, fill: BLUE, 'letter-spacing': 4 }, '补偿');
    registerAnim('s4b', (t) => {
      const a = T('L29c2'), b = T('L30');
      let d = 235 * smooth((t - a) / 1.6);
      d -= 470 * smooth((t - b + 0.2) / 1.8);
      d += 7 * Math.sin(t * 1.3);
      dT.setAttribute('cx', CX + d); dT.setAttribute('cy', YT);
      dB.setAttribute('cx', CX - d); dB.setAttribute('cy', YB);
      rod.setAttribute('x1', CX + d); rod.setAttribute('y1', YT); rod.setAttribute('x2', CX - d); rod.setAttribute('y2', YB);
      lbl.setAttribute('opacity', ease((t - T('L29c2') - 0.6) / 0.8).toFixed(3));
    });
  })();

  // ───────── s6e 坐标轴，不是盒子 ─────────
  (function () {
    const svg = document.getElementById('axis'); if (!svg) return;
    const boxes = mk(svg, 'g');
    for (const [x, name] of [[150, '内向'], [498, '外向']]) {
      mk(boxes, 'rect', { x, y: 8, width: 240, height: 116, rx: 8, fill: 'none', stroke: DIM, 'stroke-width': 3, 'stroke-dasharray': '14 12' });
      mk(boxes, 'text', { x: x + 120, y: 82, 'text-anchor': 'middle', 'font-size': 44, fill: DIM, 'font-weight': 700, 'letter-spacing': 6 }, name);
    }
    const cross = mk(svg, 'line', { x1: 130, y1: 66, x2: 130, y2: 66, stroke: INK, 'stroke-width': 4, 'stroke-linecap': 'round', opacity: 0.85 });
    const ax = mk(svg, 'g');
    const Y = 222;
    mk(ax, 'line', { x1: 60, y1: Y, x2: 828, y2: Y, stroke: INK, 'stroke-width': 4, 'stroke-linecap': 'round' });
    mk(ax, 'path', { d: `M 60 ${Y} L 84 ${Y - 13} L 84 ${Y + 13} Z`, fill: INK });
    mk(ax, 'path', { d: `M 828 ${Y} L 804 ${Y - 13} L 804 ${Y + 13} Z`, fill: INK });
    for (let i = 1; i < 8; i++) { const x = 60 + i * 96; mk(ax, 'line', { x1: x, y1: i === 4 ? Y - 20 : Y - 11, x2: x, y2: i === 4 ? Y + 20 : Y + 11, stroke: INK, 'stroke-width': 2.5, opacity: 0.7 }); }
    mk(ax, 'text', { x: 60, y: Y + 84, 'font-size': 40, fill: INK, 'font-weight': 500, 'letter-spacing': 4 }, '内向');
    mk(ax, 'text', { x: 828, y: Y + 84, 'text-anchor': 'end', 'font-size': 40, fill: INK, 'font-weight': 500, 'letter-spacing': 4 }, '外向');
    const lack = mk(ax, 'line', { x1: 560, x2: 790, y1: Y, y2: Y, stroke: BLUE, 'stroke-width': 12, 'stroke-linecap': 'round', opacity: 0 });
    const dot = mk(ax, 'circle', { cy: Y, r: 21, fill: BLUE, stroke: '#0a0e1a', 'stroke-width': 4 });
    registerAnim('s6e', (t, lt) => {
      const a = T('L41'), b = T('L41c1'), c = T('L41c2'), d = T('L41c3');
      const k = smooth((t - b - 0.1) / 0.7);                       // “不是盒子”：划掉、变暗
      boxes.setAttribute('opacity', (smooth(lt / 0.5) * (1 - 0.72 * k)).toFixed(3));
      cross.setAttribute('x2', (130 + 628 * k).toFixed(1)); cross.setAttribute('opacity', (0.85 * Math.min(1, k * 4)).toFixed(3));
      ax.setAttribute('opacity', ease((t - a - 0.15) / 0.9).toFixed(3));
      const x = 444 - 170 * smooth((t - c) / 1.4) + 5 * Math.sin(t * 1.5);
      dot.setAttribute('cx', x.toFixed(2));
      lack.setAttribute('opacity', (0.5 * smooth((t - d) / 0.6) * (0.8 + 0.2 * Math.sin((t - d) * 3))).toFixed(3));
    });
  })();
})();
