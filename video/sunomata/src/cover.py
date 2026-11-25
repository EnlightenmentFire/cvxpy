"""封面 1080×1920（竖）和 1080×1260（3:4 裁切）。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import *
from illustr import *
from scenes import river_scene, stamp

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/work/cover.png"
surf = skia.Surface(W, H); cv = surf.getCanvas()
river_scene(cv, 3.0, 0.9, 0.35, 0.1)
vgrad(cv, (0, 0, 0), (0, 0, 0), 0, 700, 0.35)
cv.drawRect(skia.Rect.MakeXYWH(0, 1300, W, 620), paint((0, 0, 0), 0.55))
text(cv, "一夜建城", W / 2, 470, "serif_k", 190, (250, 244, 228), 1, "c", ls=12, shadow=30, glow=(ODA, 50, 0.55))
text(cv, "真的发生过吗？", W / 2, 640, "serif_k", 110, ODA_HI, 1, "c", shadow=20)
text(cv, "最可靠的史书 · 一个字都没写", W / 2, 1450, "serif_b", 60, WHITE, 1, "c", shadow=12)
text(cv, "1626 · 1797 · 1959 · 1987", W / 2, 1560, "serif_k", 64, GOLD, 1, "c", ls=4, shadow=10)
text(cv, "丰臣秀吉 · 墨俣一夜城", W / 2, 1680, "sans", 44, (220, 210, 195), 1, "c")
corner_tag(cv, "传说场景 · 情景演绎", 1.0)
vignette(cv, 0.5)
surf.makeImageSnapshot().save(OUT, skia.kPNG)
img = surf.makeImageSnapshot()
s2 = skia.Surface(1080, 1440); c2 = s2.getCanvas()
c2.drawImage(img, 0, -240)
s2.makeImageSnapshot().save(OUT.replace(".png", "_3x4.png"), skia.kPNG)
print(OUT)
