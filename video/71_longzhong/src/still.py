# -*- coding: utf-8 -*-
"""渲染指定时刻的静帧：python still.py out_dir t1 t2 ... 或 场景名（取场景中点）"""
import sys, os, skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenes
from geo import W, H
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
s = skia.Surface(W, H); c = s.getCanvas()
for a in sys.argv[2:]:
    if a in scenes.T.sc:
        t0, t1 = scenes.T.sc[a]; t = t0 + (t1 - t0) * 0.6; name = a
    else:
        t = float(a); name = f'{t:07.2f}'
    scenes.draw_frame(c, t, int(t * 25))
    s.makeImageSnapshot().save(f'{out}/{name}.png')
    print(name, round(t, 2))
