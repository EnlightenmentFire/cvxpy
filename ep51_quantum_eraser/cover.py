"""封面：符合计数分组画面（全片最核心的物理图）+ 大标题。输出 9:16 与 3:4 两版。
usage: python cover.py <out_dir> <basename>
"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R


def main(out_dir, base):
    t = R.CUE_T["f2_r34"] + 3.5  # 四组都已展开、D3/D4 高亮之后
    cv = R.bg("phys").copy()
    ov = Image.new("RGBA", (R.W, R.H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(ov)
    # 只画面板，不画说明字
    R.draw_panel(cv, dr, R.F_TOP, R.KIM_G > 0, color_mode="col", label="D0 总图：一团，无条纹", curve=True)
    for g in (1, 2, 3, 4):
        R.draw_panel(cv, dr, R.F_SUB[g], R.KIM_G == g, color_mode="col", label=f"与 D{g} 配对", curve=True, curve_col=R.DCOL[g])
    img = Image.fromarray(np.clip(cv, 0, 255).astype(np.uint8)).convert("RGBA")
    img.alpha_composite(ov)
    # 标题区
    top = Image.new("RGBA", (R.W, R.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(top)
    d.rectangle((0, 0, R.W, 360), fill=(4, 7, 14, 235))
    R.text(d, (R.W // 2, 150), "量子擦除", R.font("serif_bk", 120), R.CREAM)
    R.text(d, (R.W // 2, 285), "真的能改写过去吗？", R.font("serif_b", 76), R.hexc("ff8a7a"))
    d.rectangle((0, 1330, R.W, 1700), fill=(4, 7, 14, 235))
    R.text(d, (R.W // 2, 1420), "过去的记录，一个点都没动", R.font("serif_b", 62), R.CREAM)
    R.text(d, (R.W // 2, 1520), "做过的事擦不掉，忏悔有什么用？", R.font("serif", 50), R.GOLD)
    R.text(d, (R.W // 2, 1620), "物理 · 佛法 | 类比，不是证明", R.font("sans_r", 34), R.GREY)
    img.alpha_composite(top)
    img = img.convert("RGB")
    os.makedirs(out_dir, exist_ok=True)
    img.save(os.path.join(out_dir, f"{base}_封面_9x16.png"))
    # 3:4（1080×1440）：取中间偏上，标题重排
    c34 = Image.new("RGB", (1080, 1440))
    c34.paste(img.crop((0, 0, 1080, 360)), (0, 0))
    c34.paste(img.crop((0, 360, 1080, 1260)), (0, 380))
    d2 = ImageDraw.Draw(c34)
    d2.rectangle((0, 1280, 1080, 1440), fill=(4, 7, 14))
    R.text(d2, (540, 1360), "过去的记录，一个点都没动", R.font("serif_b", 58), R.CREAM)
    c34.save(os.path.join(out_dir, f"{base}_封面_3x4.png"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
