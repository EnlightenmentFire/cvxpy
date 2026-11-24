"""Render the key style frames for review."""
import os
import sys
import time

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import scenes as SC  # noqa: E402
from engine import ROOT, finish, save_png  # noqa: E402

OUT = os.path.join(ROOT, "stills")

STILLS = [
    ("01_title", lambda: SC.title_card(3.0)),
    ("02_u2_photo", lambda: SC.u2_scene(7.0, sub="照片上这些车辆和帐篷，\n属于苏联的中程导弹阵地。")),
    ("03_globe_range", lambda: SC.globe_range(7.0, sub="从古巴打出去，\n这种导弹够得着华盛顿。")),
    ("04_timeline", lambda: SC.timeline(4.0, sub="这一天，三个地方亮起了红灯。")),
    ("05_sonar", lambda: SC.sonar_scene(3.18, sub="在艇里，就像坐在一个汽油桶里，\n外面有人抡着大锤砸。")),
    ("06_hypo_burst", lambda: SC.hypo_explosion(0, tb=0.66, sub="假设，那枚核鱼雷射了出去。")),
    ("07_hypo_globe", lambda: SC.hypo_globe(5.2, sub="一枚。然后两枚。\n然后，没有人能停下来。")),
    ("08_surface", lambda: SC.surface_topdown(2.0, plane_t=3.25, sub="在美国人那边，\n这是照程序打信号、照明、拍照。")),
]


def main(only=None):
    os.makedirs(OUT, exist_ok=True)
    for name, fn in STILLS:
        if only and not any(o in name for o in only):
            continue
        t0 = time.time()
        img = fn()
        img = finish(img, grain_amt=0.010, seed=1)
        save_png(img, os.path.join(OUT, name + ".png"))
        print(name, f"{time.time() - t0:.2f}s", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
