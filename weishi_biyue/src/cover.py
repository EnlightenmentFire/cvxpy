# -*- coding: utf-8 -*-
"""封面 1080x1440（3:4）：红标签 + 三行钩子大字 + 唯一视觉（围城留一个发光缺口）+ 系列角标。"""
import json
import os
import sys

import numpy as np
import skia
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import scene as S

CW, CH = 1080, 1440


def main(timeline_path, out_path):
    T = json.load(open(timeline_path))
    sc = S.Scene(T, bg_scale=1.45)
    t = T["answer"] + 3.0  # 缺口已开、光路已亮、守军已松动
    surf = skia.Surface(CW, CH)
    c = surf.getCanvas()
    c.clear(skia.ColorBLACK)
    # 世界层：城池放在画面下半部
    k = 0.9
    c.save()
    c.translate(CW / 2, 1045)
    c.scale(k, k)
    c.translate(-S.CX, -S.CY)
    bw, bh = sc.bg.shape[1], sc.bg.shape[0]
    c.drawImageRect(sc.bg_img, skia.Rect.MakeXYWH((S.W - bw) / 2, S.CY - bh * (S.CY / S.H), bw, bh),
                    skia.SamplingOptions(skia.FilterMode.kLinear))
    sc.draw_world(c, t)
    # 缺口处再加一点亮，缩略图里也能一眼看到
    S.glow_circle(c, S.CX + S.HALF + 40, S.CY, 70, S.GOLD, 0.45, 34)
    c.restore()
    # 顶部压暗，托住大字
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, 760)],
                                        [skia.Color4f(0, 0, 0, 0.75).toColor(), skia.Color4f(0, 0, 0, 0).toColor()])
    c.drawRect(skia.Rect.MakeXYWH(0, 0, CW, 760), skia.Paint(Shader=sh))
    # 左上红标签
    f_tag = S.font(S.SANS_BLACK, 50)
    tag = "围死了，反而打不下"
    tw = f_tag.measureText(tag)
    c.drawRoundRect(skia.Rect.MakeXYWH(56, 58, tw + 52, 84), 10, 10,
                    skia.Paint(AntiAlias=True, Color4f=S.col((214, 32, 30), 1.0)))
    S.draw_text(c, tag, 82, 117, f_tag, S.WHITE, 1.0, stroke=0, shadow=False)
    # 三行钩子
    f1 = S.font(S.SERIF_BLACK, 132)
    f3 = S.font(S.SERIF_BLACK, 178)
    S.draw_rich_line(c, "包围敌人", CW / 2, 330, f1, 1.0, stroke=14)
    S.draw_rich_line(c, "为什么要", CW / 2, 485, f1, 1.0, stroke=14)
    S.draw_rich_line(c, "**留个口子**", CW / 2, 680, f3, 1.0, stroke=18)
    # 系列角标
    f_s = S.font(S.SERIF_BOLD, 40)
    f_n = S.font(S.SERIF_BLACK, 64)
    lbl = "三十秒一问"
    lw = f_s.measureText(lbl)
    nw = f_n.measureText("01")
    x0 = CW - 56 - lw - 16 - nw
    S.draw_text(c, lbl, x0, CH - 64, f_s, (236, 228, 210), 1.0, stroke=6)
    S.draw_text(c, "01", x0 + lw + 16, CH - 62, f_n, S.YELLOW, 1.0, stroke=8)
    img = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]
    # 颗粒与暗角
    f = img.astype(np.float32)
    yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32)
    r = np.sqrt(((xx - CW / 2) / (CW * 0.62)) ** 2 + ((yy - CH * 0.55) / (CH * 0.62)) ** 2)
    f *= np.clip(1.0 - 0.5 * np.clip(r - 0.5, 0, None) ** 1.6, 0.4, 1.0)[..., None]
    f += np.random.default_rng(1).normal(0, 3.5, f.shape[:2])[..., None]
    Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).save(out_path)
    # 120 像素宽自检图
    Image.open(out_path).resize((120, 160), Image.LANCZOS).save(out_path.replace(".png", "_120px.png"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
