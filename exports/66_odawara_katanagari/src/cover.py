"""Cover images for ep.66: 9:16 (1080x1920) and 3:4 (1080x1440). usage: python cover.py <out_9x16.png> <out_3x4.png>"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import *
import scenes2 as SC
from art import *
from PIL import Image

def draw(c, h=H):
    x = SC.Ctx(8.0, 10.0, 0, {}, 8.0)
    SC.dawn_scene(c, x, 0.9)
    c.drawCircle(600, 900, 360, paint(RED, 0.10, blur=90))
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 1180), skia.Point(0, 1920)], [col(INK, 0), col(INK, 0.96)]))
    c.drawRect(skia.Rect(0, 1180, W, H), p)
    text(c, "从无名小卒到天下人 · 终章", 72, 150, 40, "sansm", GOLD, 1, "l", spacing=6)
    c.drawRect(skia.Rect(72, 178, 160, 183), paint(GOLD))
    text(c, "21万大军围城3个月", W / 2, 1420, 96, "serifbk", WHITE, 1, "c", shadow=16, spacing=2)
    text(c, "为什么几乎没打？", W / 2, 1560, 104, "serifbk", GOLD, 1, "c", shadow=16, spacing=6)
    text(c, "小田原征伐 · 石垣山一夜城 · 刀狩", W / 2, 1670, 42, "sansm", PAPER, 0.95, "c")
    text(c, "情景演绎", W - 60, 150, 28, "sansm", (220, 215, 200), 0.7, "r")

def cover(out916, out34):
    surf = skia.Surface(W, H); c = surf.getCanvas(); c.clear(skia.Color(12, 10, 8))
    draw(c)
    arr = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
    Image.fromarray(arr[..., :3]).save(out916)
    # 3:4 — re-layout: crop the scene band and redraw titles
    s2 = skia.Surface(W, 1440); c2 = s2.getCanvas(); c2.clear(skia.Color(12, 10, 8))
    c2.save(); c2.translate(0, -300)
    x = SC.Ctx(8.0, 10.0, 0, {}, 8.0); SC.dawn_scene(c2, x, 0.9)
    c2.restore()
    p = skia.Paint(); p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 900), skia.Point(0, 1440)], [col(INK, 0), col(INK, 0.96)]))
    c2.drawRect(skia.Rect(0, 900, W, 1440), p)
    text(c2, "从无名小卒到天下人 · 终章", 64, 90, 38, "sansm", GOLD, 1, "l", spacing=6)
    text(c2, "21万大军围城3个月", W / 2, 1150, 92, "serifbk", WHITE, 1, "c", shadow=16, spacing=2)
    text(c2, "为什么几乎没打？", W / 2, 1290, 100, "serifbk", GOLD, 1, "c", shadow=16, spacing=6)
    text(c2, "小田原征伐 · 石垣山一夜城 · 刀狩", W / 2, 1385, 38, "sansm", PAPER, 0.95, "c")
    arr = s2.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
    Image.fromarray(arr[..., :3]).save(out34)

if __name__ == "__main__":
    cover(sys.argv[1], sys.argv[2])
