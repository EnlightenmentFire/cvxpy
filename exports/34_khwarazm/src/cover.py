import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import *
import scenes as SC
from PIL import Image
def cover(out):
    surf = skia.Surface(W, H); c = surf.getCanvas(); c.clear(skia.Color(12, 10, 8))
    x = SC.Ctx(3.0, 10.0, 0, {}, 3.0)
    cam = Cam("theater", 65.2, 40.4, 0.86)
    draw_map(c, cam, dim=0.12); draw_rivers(c, cam)
    pts = SC.garrison_pts(cam)
    for i, (px, py) in enumerate(pts): city_marker(c, px, py, None, "siege" if i % 3 == 0 else "lit", 1, i * 0.7, 0.8)
    SC.theater_routes(c, cam, x, ["otrar", "jochi", "upper", "main"], {"otrar": 1, "jochi": 1, "upper": 1, "main": 1}, flow=False)
    X, Y = cam.city("布哈拉"); flash(c, X, Y, 0.35, GOLD, 200)
    for nm, sd in [("讹答剌", "r"), ("布哈拉", "l"), ("撒马尔罕", "r")]:
        X, Y = cam.city(nm); text(c, nm, X + (24 if sd == "r" else -24), Y + 14, 40, "sans", WHITE, 1, "l" if sd == "r" else "r", stroke=7)
    vignette(c, 0.7)
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 1180), skia.Point(0, 1920)], [col(INK, 0), col(INK, 0.95)]))
    c.drawRect(skia.Rect(0, 1180, W, H), p)
    text(c, "历史的关键一局", 72, 150, 42, "sansm", GOLD, 1, "l", spacing=8)
    c.drawRect(skia.Rect(72, 178, 160, 183), paint(GOLD))
    text(c, "一支商队被杀", W / 2, 1400, 104, "serifbk", WHITE, 1, "c", shadow=16, spacing=4)
    text(c, "怎样引来一场灭国之战？", W / 2, 1540, 78, "serifbk", GOLD, 1, "c", shadow=14)
    text(c, "成吉思汗西征花剌子模 · 1219—1221", W / 2, 1650, 40, "sansm", PAPER, 0.9, "c")
    text(c, "兵不少，为什么被一座城一座城地吃掉", W / 2, 1730, 40, "sans", CYAN, 0.95, "c")
    text(c, "地图示意", W - 60, 150, 28, "sansm", (220, 215, 200), 0.7, "r")
    arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
    Image.fromarray(arr[..., :3]).save(out)
if __name__ == "__main__":
    cover(sys.argv[1])
