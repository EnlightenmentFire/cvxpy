"""封面：1080×1920 竖版 + 1080×1440（3:4）裁切。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import *
from art import *
import scenes as SC_
from PIL import Image
from gfx import put_text as gfx_put

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/work/build"
img = SC_.bridge_scene(0.8)
img = SC_.robe_on(img, 0.8, 3, [20, 20, 20], cy=800)
img = sword_flash(img, (260, 520), (880, 1060), 1.0, width=11, k=1.1, tail=1.0)
fm = figure_layer("strike", 250, 1090, 420)
img = over(img, hexc("#020203"), fm) + rim_light(fm, 4, -3, "#ffd39a", 1.2)
img = torch_glow(img, [(860, 1000), (960, 1030), (120, 1010)], 0.4, 1.0, r=170, seed=9)
img = img * vignette(0.6)
# 上方压暗，放标题
band = np.exp(-((np.arange(H, dtype=np.float32) - 290) / 280) ** 2)[:, None, None]
img = img * (1 - 0.6 * band)
img = gfx_put(img, ["國士遇我"], font("Black", 150, TC), GOLD, (W // 2, 200), glow_col=FIRE, glow_r=30, glow_k=0.6,
                   shadow=14, stroke=2, stroke_fill=(0.05, 0.03, 0.02))
img = gfx_put(img, ["國士報之"], font("Black", 150, TC), GOLD, (W // 2, 370), glow_col=FIRE, glow_r=30, glow_k=0.6,
                   shadow=14, stroke=2, stroke_fill=(0.05, 0.03, 0.02))
img = SC_.put_text(img, ["主公已死，他为何还要毁容报仇？"], font("Bold", 56, SC), (1, 0.97, 0.92), (W // 2, 1340), shadow=12,
                   stroke=3, stroke_fill=(0.02, 0.02, 0.03))
img = SC_.put_text(img, ["豫让 · 刺杀赵襄子"], font("Medium", 44, SC), (0.88, 0.8, 0.62), (W // 2, 1430), shadow=10)
img = SC_.put_text(img, ["历史的关键一局"], font("Medium", 34, SC), (0.86, 0.74, 0.5), (W // 2, 1700), shadow=8)
im = to_img(img)
im.save(f"{OUT}/cover_1080x1920.png")
# 3:4 裁切（保留标题与人物、锦袍）
im.crop((0, 40, 1080, 1480)).save(f"{OUT}/cover_1080x1440.png")
print("cover ok")
