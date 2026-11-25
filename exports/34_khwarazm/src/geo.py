import math, json, os
import numpy as np
W = "/tmp/claude-0/work"
def merc(lon, lat, z):
    n = 256 * 2 ** z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y
def inv(x, y, z):
    n = 256 * 2 ** z
    lon = x / n * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    return lon, lat

class View:
    """A basemap image in Mercator pixel space at zoom z, origin at tile (x0,y0)."""
    def __init__(self, name):
        m = json.load(open(f"{W}/kh/assets/base_{name}.json"))
        self.name = name; self.z = m["z"]; self.ox = m["x0"] * 256; self.oy = m["y0"] * 256
        self.w = m["w"]; self.h = m["h"]; self.path = f"{W}/kh/assets/base_{name}.png"
    def px(self, lon, lat):
        x, y = merc(lon, lat, self.z); return x - self.ox, y - self.oy

# city coordinates (lon, lat)
CITY = {
    "讹答剌": (68.30, 42.85), "布哈拉": (64.42, 39.77), "撒马尔罕": (66.98, 39.65),
    "玉龙杰赤": (59.15, 42.32), "巴里黑": (66.90, 36.76), "忽毡": (69.62, 40.28),
    "别纳客忒": (69.20, 40.95), "毡的": (64.0, 44.4), "养吉干": (62.0, 45.6), "昔格纳黑": (66.9, 43.9),
    "讷儿": (65.68, 40.55), "匝儿讷黑": (66.4, 42.0), "忒耳迷": (67.28, 37.22), "你沙不儿": (58.80, 36.21),
    "哥疾宁": (68.42, 33.55), "八鲁湾": (69.25, 35.05), "可疾云": (50.00, 36.27), "剌夷": (51.43, 35.60),
    "阿必思衮岛": (54.0, 36.95), "马鲁": (61.84, 37.60), "也儿的石": (85, 48),
    "阿力麻里": (80.9, 44.0), "八剌沙衮": (75.25, 42.75), "巴格达": (44.37, 33.31),
    "哈拉和林": (102.83, 47.2), "中都": (116.4, 39.9), "伊犁": (81.3, 43.9),
    "印度河渡口": (72.2, 33.9), "白沙瓦": (71.57, 34.0),
}
