# -*- coding: utf-8 -*-
"""Cover images: 1080x1920 and 3:4 (1080x1440) from the rain-window scene."""
import sys, os
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import W, H, SERIF_SC, BRUSH, SANS_SC, GOLD, to_u8, text_sprite, blit
from rain import RainWindow

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/work/render"
rw = RainWindow(40, seed=1, rain=1.0, push=(1.06, 1.06))
img = rw.render(18.0)
img[:1000] *= np.linspace(0.55, 1.0, 1000, dtype=np.float32)[:, None, None]


def T(s, x, y, size, color, path=SERIF_SC, weight=700, shadow=8, maxw=1000):
    spr = text_sprite(s, path, size, color, weight, maxw, "center", 1.3, shadow, 0, (0, 0, 0), True, 0)
    blit(img, spr, x, y, 1.0)


T("静坐的科学 · 二", W / 2, 150, 38, GOLD, SERIF_SC, 500, 4)
T("抑郁好了以后", W / 2, 330, 112, (248, 244, 236))
T("为什么还会回来？", W / 2, 480, 112, (248, 244, 236))
T("正念能防复发吗？证据怎么说", W / 2, 640, 50, (244, 214, 160), SERIF_SC, 600, 5)
T("不被第二毒箭", W / 2, 1640, 96, (244, 214, 160), BRUSH, None, 6)
os.makedirs(OUT, exist_ok=True)
full = to_u8(img)
cv2.imwrite(f"{OUT}/cover.png", cv2.cvtColor(full, cv2.COLOR_RGB2BGR))
# 3:4 crop centred on the title + figure; re-place the bottom line inside the crop
c = full[90:90 + 1440].copy()
cv2.imwrite(f"{OUT}/cover_3x4.png", cv2.cvtColor(c, cv2.COLOR_RGB2BGR))
print("covers ->", OUT)
