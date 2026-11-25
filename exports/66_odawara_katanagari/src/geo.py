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
        m = json.load(open(f"{W}/od/assets/base_{name}.json"))
        self.name = name; self.z = m["z"]; self.ox = m["x0"] * 256; self.oy = m["y0"] * 256
        self.w = m["w"]; self.h = m["h"]; self.path = f"{W}/od/assets/base_{name}.png"
    def px(self, lon, lat):
        x, y = merc(lon, lat, self.z); return x - self.ox, y - self.oy

# castle / place coordinates (lon, lat)
CITY = {
    "小田原城": (139.1535, 35.2508), "石垣山城": (139.1278, 35.2354), "山中城": (139.0186, 35.1784),
    "韭山城": (138.9554, 35.0537), "下田城": (138.9487, 34.6669), "八王子城": (139.2522, 35.6530),
    "钵形城": (139.1959, 36.1097), "松井田城": (138.7921, 36.3226), "忍城": (139.4528, 36.1372),
    "玉绳城": (139.5150, 35.3534), "江户": (139.7528, 35.6850), "岩槻城": (139.7102, 35.9513),
    "名胡桃城": (139.0186, 36.6719), "沼田城": (139.0434, 36.6445), "骏府": (138.3830, 34.9800),
    "京都": (135.7681, 35.0116), "大坂": (135.5258, 34.6873), "伏见": (135.7712, 34.9330),
    "清水港": (138.5050, 35.0150), "名古屋": (136.90, 35.18), "鹿儿岛": (130.55, 31.60), "博多": (130.40, 33.59),
    "高知": (133.53, 33.56), "伊豆": (138.95, 34.85), "箱根": (139.05, 35.20), "碓冰岭": (138.70, 36.36),
    "会津": (139.93, 37.49), "笠悬山": (139.1278, 35.2354),
}
