"""Render the key style frames for review (before the full render)."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scenes  # noqa: E402
from engine import H, W, new_canvas, save_png  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "stills")
os.makedirs(OUT, exist_ok=True)

STILLS = [
    ("01_jackrabbits", lambda c: scenes.scene_coldopen(c, 0, sub="黑尾、白尾、蓝尾、红尾……各种颜色尾巴的长耳大野兔")),
    ("02_photocopy", lambda c: scenes.scene_photocopy(c, 0, sub="最先丢掉的，是那些少见的东西")),
    ("03_plymouth_ox", lambda c: scenes.scene_plymouth(c, 0, sub="中位数 1207 磅，实际 1198 磅：只差 9 磅")),
    ("04_athens", lambda c: scenes.scene_athens(c, 0, sub="只要再有三十票投到另一边，我就无罪了")),
    ("05_flash_crash", lambda c: scenes.scene_flash(c, 0, sub="芝加哥的期货市场按规则自动暂停了五秒钟")),
    ("06_corn_1970", lambda c: scenes.scene_corn(c, 0, sub="每一株都是好玉米。问题是，全国八成以上的玉米，身上都带着同一样东西")),
    ("07_parchment_1788", lambda c: scenes.scene_parchment(c, 0, sub="别指望谁天生就是好人，要让不同的力量互相牵制")),
    ("08_gears_ending", lambda c: scenes.scene_gears(c, 0, rot=0.2,
                                                       lines=[("不指望一个完美的模型", "#EEF3F8"),
                                                              ("让许多不一样的东西互相盯着", "#EEF3F8"),
                                                              ("永远给真实世界留一个位子", "#9BE3A6")])),
]

only = sys.argv[2].split(",") if len(sys.argv) > 2 else None
paths = []
for name, fn in STILLS:
    if only and not any(name.startswith(o) for o in only):
        paths.append(os.path.join(OUT, name + ".png"))
        continue
    surf, ctx = new_canvas()
    fn(ctx)
    p = os.path.join(OUT, name + ".png")
    save_png(surf, p)
    paths.append(p)
    print("wrote", p)

# contact sheet (4 x 2)
th_w, th_h = 360, 640
sheet = Image.new("RGB", (4 * th_w + 5 * 16, 2 * th_h + 3 * 16 + 60), (18, 20, 26))
d = ImageDraw.Draw(sheet)
f = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc", 26, index=2)
for i, p in enumerate(paths):
    if not os.path.exists(p):
        continue
    im = Image.open(p).resize((th_w, th_h), Image.Resampling.LANCZOS)
    x = 16 + (i % 4) * (th_w + 16)
    y = 16 + (i // 4) * (th_h + 46)
    sheet.paste(im, (x, y))
    d.text((x, y + th_h + 6), os.path.basename(p)[:-4], font=f, fill=(200, 205, 215))
sheet.save(os.path.join(OUT, "00_contact_sheet.jpg"), quality=90)
print("contact sheet done")
