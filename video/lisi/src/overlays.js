/* 全局叠层：暗角、字幕、章节签、官阶条（换仓 HUD）、片名 */
(function () {
  const { TL, SEG, SCN, clamp, ramp, eo, eio, lerp, vis, S, E, el, overlay } = F;

  /* 暗角 + 字幕底部压暗 */
  overlay((st) => {
    el(st, 'abs', 'inset:0;pointer-events:none;background:radial-gradient(ellipse 78% 62% at 50% 44%, rgba(0,0,0,0) 55%, rgba(0,0,0,.55) 100%)');
    el(st, 'abs', 'left:0;right:0;top:1250px;height:670px;pointer-events:none;background:linear-gradient(180deg, rgba(5,4,4,0) 0%, rgba(5,4,4,.82) 34%, rgba(5,4,4,.96) 100%)');
    el(st, 'abs', 'left:0;right:0;top:0;height:230px;pointer-events:none;background:linear-gradient(180deg, rgba(5,4,4,.9) 0%, rgba(5,4,4,0) 100%)');
  });

  /* 章节签（左上，避开顶部遮挡区） */
  overlay((st, add) => {
    const d = el(st, 'abs serif', 'left:72px;top:182px;font-size:30px;font-weight:700;color:#c9a45c;letter-spacing:.22em;opacity:0;display:flex;align-items:center;gap:18px');
    const bar = el(d, '', 'width:44px;height:2px;background:#c9a45c'); const tx = el(d, '', '');
    const list = TL.scenes.filter(s => s.id !== 'cold');
    add(t => {
      const sc = list.find(s => t >= s.cut_in && t < s.cut_out);
      if (!sc) { d.style.opacity = 0; return; }
      if (tx.textContent !== sc.title) tx.textContent = sc.title.replace(' ', ' · ');
      d.style.opacity = vis(t, sc.cut_in + .5, sc.cut_out - .1, .6, .5) * .92;
    });
  });

  /* 官阶条：每一步都是换个更大的仓 */
  overlay((st, add) => {
    const ranks = ['小吏', '舍人', '郎', '长史', '客卿', '廷尉', '丞相'];
    const X0 = 96, X1 = 984, Y = 322;
    const wrap = el(st, 'abs', 'left:0;top:0;width:1080px;height:420px;opacity:0;pointer-events:none');
    el(wrap, 'abs', `left:${X0}px;top:${Y}px;width:${X1 - X0}px;height:2px;background:#4a4132`);
    const prog = el(wrap, 'abs', `left:${X0}px;top:${Y}px;width:0;height:2px;background:#c9a45c`);
    const nodes = ranks.map((r, i) => {
      const x = lerp(X0, X1, i / (ranks.length - 1)), h = 16 + i * 5.5, w = 20 + i * 4.5;
      const g = el(wrap, 'abs', `left:${x - 60}px;top:${Y - 70}px;width:120px;height:130px`);
      g.innerHTML = `<svg viewBox="-60 -70 120 130" style="position:absolute;inset:0;overflow:visible">
        <path class="b" d="M ${-w / 2} 0 V ${-h} L 0 ${-h - w * .55} L ${w / 2} ${-h} V 0 Z" fill="#17140f" stroke="#6b5f49" stroke-width="2"/>
        <path class="r" d="M ${-w / 2 - 5} ${-h} L 0 ${-h - w * .55 - 4} L ${w / 2 + 5} ${-h}" fill="none" stroke="#6b5f49" stroke-width="2.5"/></svg>`;
      const lb = el(g, 'abs serif', `left:0;width:120px;top:82px;text-align:center;font-size:24px;font-weight:700;color:#7d7158;letter-spacing:.08em`, r);
      return { x, g, lb, b: g.querySelector('.b'), r: g.querySelector('.r') };
    });
    const qiu = el(wrap, 'abs serif', `left:${X1 - 60}px;top:${Y + 44}px;width:120px;text-align:center;font-size:40px;font-weight:900;color:#c8372d;opacity:0`, '囚');
    /* 关键时刻：到达各级的时间 */
    const at = [S('q1'), S('q2') + 2.2, E('q2') - .6, S('q5'), S('q6') + 1.2, S('z8') + 2.6, S('p1') + 1.2];
    const showA = S('q1') + .3, showB = E('j11') + .6, fall = S('j1');
    const zk0 = S('z2') + 1.2, zk1 = S('z8');
    add(t => {
      const v = vis(t, showA, showB, .8, .8); wrap.style.opacity = v; if (v <= 0) return;
      let lvl = 0, frac = 0;
      for (let i = 0; i < at.length; i++) if (t >= at[i]) lvl = i;
      const nx = lvl + 1 < at.length ? ramp(t, at[lvl + 1] - .9, at[lvl + 1]) : 0;
      const pos = lvl + eio(nx);
      const fallen = ramp(t, fall, fall + .8);
      const danger = (t > zk0 && t < zk1) ? (.5 + .5 * Math.sin((t - zk0) * 9)) : 0;
      prog.style.width = ((X1 - X0) * pos / (ranks.length - 1)) + 'px';
      prog.style.background = fallen > 0 ? '#5a4a33' : (danger > .5 ? '#c8372d' : '#c9a45c');
      nodes.forEach((n, i) => {
        const on = clamp(pos - i + 1) * (1 - fallen * .85), cur = clamp(1 - Math.abs(pos - i)) * (1 - fallen);
        const col = (cur > .5 && danger > .5) ? '#c8372d' : `rgb(${lerp(107, 233, on)},${lerp(95, 201, on)},${lerp(73, 138, on)})`;
        n.b.setAttribute('stroke', col); n.r.setAttribute('stroke', col);
        n.b.setAttribute('fill', cur > .5 ? (danger > .5 ? '#3a1410' : '#6b4d1c') : '#17140f');
        n.lb.style.color = cur > .5 ? '#f1dfb0' : (on > .5 ? '#b9a67c' : '#6e634e');
        n.lb.style.fontSize = (cur > .5 ? 30 : 24) + 'px';
        n.g.style.transform = `scale(${1 + cur * .28})`;
      });
      qiu.style.opacity = fallen; qiu.style.transform = `translateY(${lerp(-60, 0, eo(fallen))}px)`;
    });
  });

  /* 片名 */
  overlay((st, add) => {
    const a = E('c5') + .25, b = S('r1') - .25;
    const d = el(st, 'abs', 'inset:0;background:#070605;opacity:0');
    const big = el(d, 'abs serif', 'left:0;right:0;top:560px;text-align:center;font-size:300px;font-weight:900;letter-spacing:.14em;text-indent:.14em;color:#f1e3c0;line-height:1', '李斯');
    const rule = el(d, 'abs', 'left:50%;top:920px;height:3px;width:0;background:#c9a45c;transform:translateX(-50%)');
    const sub = el(d, 'abs serif', 'left:0;right:0;top:970px;text-align:center;font-size:62px;font-weight:700;letter-spacing:.2em;text-indent:.2em;color:#c9a45c', '一只选对了粮仓的老鼠');
    const src = el(d, 'abs sans', 'left:0;right:0;top:1090px;text-align:center;font-size:28px;letter-spacing:.3em;text-indent:.3em;color:#7d7158', '据《史记·李斯列传》');
    add(t => {
      const v = vis(t, a, b, .5, .6); d.style.opacity = v; if (v <= 0) return;
      const p = ramp(t, a, b);
      big.style.transform = `scale(${lerp(1.06, 1, eo(ramp(t, a, a + 2.5)))})`; big.style.opacity = ramp(t, a + .1, a + .8);
      rule.style.width = (eo(ramp(t, a + .5, a + 1.5)) * 520) + 'px';
      sub.style.opacity = ramp(t, a + .8, a + 1.5); src.style.opacity = ramp(t, a + 1.3, a + 2) * .9;
    });
  });

  /* 字幕（最上层） */
  overlay((st, add) => {
    const d = el(st, 'abs', 'left:70px;width:940px;top:1392px;height:120px;display:flex;align-items:center;justify-content:center;text-align:center;opacity:0');
    const tx = el(d, '', 'white-space:nowrap');
    const subs = TL.segs.flatMap(s => s.subs.map(u => ({ ...u, kind: s.kind })));
    let cur = null;
    add(t => {
      const u = subs.find(x => t >= x.s - .04 && t < x.e + .1);
      if (!u) { d.style.opacity = 0; cur = null; return; }
      if (cur !== u) {
        cur = u; tx.textContent = u.kind === 'q' ? `「${u.text.replace(/[。]$/, '')}」` : u.text;
        tx.className = u.kind === 'q' ? 'serif' : 'sans';
        const n = [...tx.textContent].length; const fs = Math.min(u.kind === 'q' ? 54 : 50, Math.floor(920 / n));
        tx.style.cssText = `white-space:nowrap;font-size:${fs}px;font-weight:${u.kind === 'q' ? 700 : 500};color:${u.kind === 'q' ? '#ecd08f' : '#f6f1e6'};letter-spacing:.03em;text-shadow:0 0 14px rgba(0,0,0,.95),0 2px 4px rgba(0,0,0,.9),0 0 3px #000`;
      }
      d.style.opacity = Math.min(ramp(t, u.s - .04, u.s + .08), 1);
    });
  });
})();
