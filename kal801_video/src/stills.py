# -*- coding: utf-8 -*-
"""渲染关键静帧（与成片同一套代码）。用法：python3 stills.py OUTDIR [名字过滤]"""
import os
import sys

import numpy as np
import skia
from PIL import Image

from compose import build_timeline, load_manifests, render
from render_lib import W, H, to_array

WORK = os.environ.get("KAL_WORK", "/tmp/claude-0/-home-user-cvxpy/44060277-be5b-5d12-bb11-0e70dedfd6d4/scratchpad/work")

STILLS = [
    ("01_冷启动", "s0_05", 2.0),
    ("02_片头", "s0_08", 1.8),
    ("03_驾驶舱_年纪与地位", "s1_08", 2.2),
    ("04_关岛地图_两条距离线", "s2_12", 2.0),
    ("05_剖面_最低高度与假如复飞", "s3_28", 4.0),
    ("06_剖面_复飞", "s3_35", 1.8),
    ("07_瑞士奶酪", "s4_11", 2.4),
    ("08_1978波特兰", "s5_06", 3.0),
    ("09_梯子_六级说法", "s7_09", 2.0),
    ("10_梯子_801的话", "s7_14", 2.6),
    ("11_权力距离尺子", "s8_08", 2.4),
    ("12_核对录音附录", "s9_08", 3.0),
    ("13_安全记录", "s10_05", 3.0),
    ("14_结尾", "s11_04", 2.4),
]


def main(outdir, flt=None):
    os.makedirs(outdir, exist_ok=True)
    m, g = load_manifests(WORK)
    tl, total = build_timeline(m, g)
    print(f"timeline {total/60:.1f} min, {len(tl)} entries")
    surf, surf2 = skia.Surface(W, H), skia.Surface(W, H)
    thumbs = []
    for name, bid, off in STILLS:
        if flt and flt not in name:
            continue
        e = next(x for x in tl if x["id"] == bid)
        t = e["start"] + min(off, e["dur"] - 0.05)
        render(tl, t, surf, surf2)
        arr = to_array(surf)
        im = Image.fromarray(np.ascontiguousarray(arr))
        p = os.path.join(outdir, f"{name}.png")
        im.save(p, optimize=True)
        thumbs.append((name, im))
        print("saved", p)
    if not flt and thumbs:
        cols = 7
        tw, th = 360, 640
        rows = (len(thumbs) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * tw + (cols + 1) * 12, rows * th + (rows + 1) * 12), (20, 20, 24))
        for k, (name, im) in enumerate(thumbs):
            r, cc = divmod(k, cols)
            sheet.paste(im.resize((tw, th), Image.LANCZOS), (12 + cc * (tw + 12), 12 + r * (th + 12)))
        sheet.save(os.path.join(outdir, "00_总览.jpg"), quality=88)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
