# -*- coding: utf-8 -*-
"""地理数据与底图叠加层（河流、湖泊、势力范围示意）。地名坐标为今地近似，州郡范围均为示意。"""
import json, math, os, sys
import numpy as np
import skia
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gfx import merc, WORK, col, paint, YELLOW, BLACK, GOLD, GREEN, GREY, RED

DEM = f"{WORK}/dem"

PLACES = {
    "许": (113.83, 34.04), "下邳": (117.95, 34.27), "小沛": (116.93, 34.73), "彭城": (117.18, 34.26),
    "盱眙": (118.52, 33.0), "淮阴": (119.02, 33.6), "海西": (119.6, 34.25), "广陵": (119.43, 32.39),
    "寿春": (116.78, 32.57), "邺": (114.38, 36.32), "平原": (116.43, 37.17), "官渡": (114.07, 34.72),
    "洛阳": (112.45, 34.68), "长安": (108.93, 34.27), "陈留": (114.38, 34.8), "汝南": (114.62, 32.97),
    "新野": (112.36, 32.52), "襄阳": (112.14, 32.02), "隆中": (112.06, 31.98), "成都": (104.06, 30.66),
    "汉中": (107.03, 33.07), "沛国": (116.78, 33.73), "梁国": (115.65, 34.42), "宛": (112.53, 33.0),
    "东海": (118.36, 34.6), "江陵": (112.19, 30.35), "濮阳": (115.03, 35.76),
}

# 势力范围（公元 200 年前后，示意）
TERR = {
    "袁绍": (YELLOW, [(110.8, 40.6), (119.5, 40.8), (119.9, 39.3), (118.4, 38.3), (120.7, 37.6), (120.6, 36.6), (118.8, 36.1),
                     (116.5, 35.7), (115.0, 35.4), (113.5, 35.5), (112.2, 35.2), (110.6, 36.0)]),
    "曹操": (BLACK, [(110.4, 35.9), (112.2, 35.2), (113.5, 35.45), (115.0, 35.35), (116.5, 35.65), (118.8, 36.0), (119.9, 35.0),
                    (120.3, 34.3), (119.5, 33.1), (117.5, 32.8), (116.2, 32.5), (115.5, 32.3), (114.0, 32.6), (112.8, 33.2),
                    (111.2, 33.8), (110.3, 34.6)]),
    "刘表": (GREEN, [(110.2, 33.0), (112.0, 33.3), (113.8, 32.4), (114.6, 31.2), (114.2, 29.5), (113.5, 27.0), (112.0, 25.6),
                    (110.0, 26.0), (109.0, 28.0), (109.3, 30.5)]),
    "孙氏": (GREY, [(116.2, 32.4), (117.5, 32.75), (119.5, 32.95), (121.2, 32.0), (121.6, 30.8), (120.8, 28.5), (118.5, 27.5),
                   (116.5, 28.5), (115.0, 29.6), (114.6, 31.2), (115.5, 32.0)]),
    "刘璋": (GREY, [(101.8, 33.5), (106.5, 33.4), (108.6, 32.5), (109.5, 30.5), (109.0, 28.0), (106.0, 27.0), (103.0, 26.2), (101.5, 29.0)]),
}


def base_px(meta, lon, lat):
    z = meta["z"]; n = 256 * 2 ** z
    mx, my = merc(lon, lat)
    return mx * n - meta["x0"] * 256, my * n - meta["y0"] * 256


def load_lines(path, bbox):
    d = json.load(open(path)); out = []
    for f in d["features"]:
        g = f["geometry"]
        if not g:
            continue
        ls = [g["coordinates"]] if g["type"] == "LineString" else g["coordinates"] if g["type"] == "MultiLineString" else []
        if g["type"] in ("Polygon",):
            ls = g["coordinates"]
        if g["type"] == "MultiPolygon":
            ls = [r for poly in g["coordinates"] for r in poly]
        for l in ls:
            if any(bbox[0] < c[0] < bbox[2] and bbox[1] < c[1] < bbox[3] for c in l):
                out.append((f["properties"].get("scalerank", 9) or 9, [(c[0], c[1]) for c in l], f["properties"].get("name") or ""))
    return out


def bake(base_name, river_w):
    """在底图上叠画河流湖泊，输出 <base>_r.png（同网格）。"""
    from PIL import Image
    meta = json.load(open(f"{DEM}/{base_name}.png.json"))
    im = np.asarray(Image.open(f"{DEM}/{base_name}.png").convert("RGBA")).copy()
    surf = skia.Surface(im.shape[1], im.shape[0])
    c = surf.getCanvas()
    c.drawImage(skia.Image.fromarray(im, skia.kRGBA_8888_ColorType), 0, 0)
    bbox = (100, 24, 125, 43)
    rivers = load_lines(f"{DEM}/rivers.geojson", bbox)
    for rank, pts, name in rivers:
        big = name in ("Huang", "Yangtze", "Huai", "Han", "Chang Jiang", "Huang He")
        w = river_w * (2.2 if big else 1.0 if rank <= 6 else 0.6)
        path = skia.Path()
        for i, (lo, la) in enumerate(pts):
            x, y = base_px(meta, lo, la)
            path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
        c.drawPath(path, paint((60, 96, 120), 0.55, stroke=w * 2.2, blur=w))
        c.drawPath(path, paint((92, 136, 160), 0.9, stroke=w))
    lakes = []  # 今日湖泊（洪泽湖、微山湖等）多为后世形成，不画
    for rank, pts, name in lakes:
        path = skia.Path()
        for i, (lo, la) in enumerate(pts):
            x, y = base_px(meta, lo, la)
            path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
        path.close()
        c.drawPath(path, paint((52, 80, 100), 0.95))
    out = surf.makeImageSnapshot().toarray()
    Image.fromarray(np.ascontiguousarray(out[..., [2, 1, 0, 3]])).save(f"{DEM}/{base_name}_r.png")
    print("baked", base_name)


def terr_layer(names=None, blur=6.0):
    """势力范围层：与 base7 同网格的 RGBA 图。"""
    from PIL import Image
    meta = json.load(open(f"{DEM}/base7.png.json"))
    surf = skia.Surface(meta["w"], meta["h"])
    c = surf.getCanvas(); c.clear(skia.Color4f(0, 0, 0, 0))
    for k, (cc, poly) in TERR.items():
        if names and k not in names:
            continue
        path = skia.Path()
        for i, (lo, la) in enumerate(poly):
            x, y = base_px(meta, lo, la)
            path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
        path.close()
        fill = (40, 36, 34) if k == "曹操" else cc
        p = paint(fill, 0.55 if k == "曹操" else 0.42); p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
        c.drawPath(path, p)
        edge = GOLD if k == "曹操" else cc
        pe = paint(edge, 0.85, stroke=2.2); pe.setPathEffect(skia.DashPathEffect.Make([10, 7], 0))
        c.drawPath(path, pe)
    return surf.makeImageSnapshot(), meta


if __name__ == "__main__":
    bake("base7", 1.6)
    bake("base9", 2.4)
