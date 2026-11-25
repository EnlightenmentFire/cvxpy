# -*- coding: utf-8 -*-
"""州域多边形（示意）与陆地求交，结果缓存到 GEO/polys.json"""
import json, os
GEO = "/tmp/claude-0/work/geo"
XU = [(118.6, 36.1), (119.3, 36.15), (119.9, 36.0), (121.2, 35.9), (121.6, 33.5), (121.3, 31.75), (120.9, 31.75),
      (120.0, 32.02), (119.4, 32.22), (118.9, 32.25), (118.6, 32.6), (118.3, 33.1), (118.0, 33.5), (117.6, 33.85),
      (117.2, 34.1), (117.05, 34.6), (117.10, 35.0), (117.55, 35.35), (118.0, 35.75)]
YAN = [(114.3, 34.5), (115.0, 34.4), (115.8, 34.6), (116.5, 34.8), (117.1, 35.0), (117.55, 35.35), (118.0, 35.75),
       (118.6, 36.1), (117.8, 36.4), (117.0, 36.6), (116.2, 36.9), (115.3, 36.05), (114.35, 35.6), (114.2, 35.1)]


def build():
    from shapely.geometry import shape, Polygon, mapping
    from shapely.ops import unary_union
    d = json.load(open(f"{GEO}/region.json"))
    land = unary_union([shape(g) for _, g in d["ne_10m_land"]]).buffer(0)
    out = {}
    for nm, P in (("徐州", XU), ("兖州", YAN)):
        g = Polygon(P).intersection(land).simplify(0.01)
        polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
        out[nm] = [[list(p.exterior.coords)] for p in polys if p.area > 0.01]
    json.dump(out, open(f"{GEO}/polys.json", "w"))
    return out


def load():
    p = f"{GEO}/polys.json"
    return json.load(open(p)) if os.path.exists(p) else build()


if __name__ == "__main__":
    o = build(); print({k: sum(len(r[0]) for r in v) for k, v in o.items()})
