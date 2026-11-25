"""封面 png：1080×1920 竖版 + 1080×1440（3:4）版。开场客店夜景 + 标题。"""
import os
from PIL import Image
from base import *
import scenes

WK = os.environ.get("WORK", "/tmp/claude-0/work")


def compose(y_title, y_bottom):
    img = scenes.scene_inn(6.0, 14.0, {}, 0).convert("RGB")
    img = Image.blend(img, Image.new("RGB", img.size, (0, 0, 0)), 0.12)
    band = vgrad((0, 0, 0), (0, 0, 0)).copy()
    m = radial_mask(W, H, W / 2, y_bottom + 40, 900, 1.2)
    img = Image.composite(band, img, m.point(lambda v: int(v * 0.75)))
    img = img.convert("RGBA")
    img = draw_text(img, (W / 2, y_title), "商鞅变法", font("serif", 64, "Bold"), fill=GOLD2, shadow=8)
    img = draw_text(img, (W / 2, y_title + 140), "一个人改出了最强的国家", font("serif", 76, "Black"), fill=PAPER, shadow=10)
    img = draw_text(img, (W / 2, y_title + 260), "却死在自己的法里", font("serif", 100, "Black"), fill=RED2, shadow=10)
    img = draw_text(img, (W / 2, y_bottom), "信用 · 激励 · 信息：三根杠杆", font("serif", 52, "Bold"), fill=GOLD2, shadow=8)
    img = draw_text(img, (W / 2, y_bottom + 84), "他走了，法为什么还在？", font("serif", 56, "Black"), fill=PAPER, shadow=8)
    return Image.fromarray(finish(img.convert("RGB"), 0, grain=False))


if __name__ == "__main__":
    compose(330, 1640).save(f"{WK}/cover_1080x1920.png")
    compose(420, 1420).crop((0, 180, 1080, 1620)).save(f"{WK}/cover_1080x1440.png")
    print("cover ok")
