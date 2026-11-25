# -*- coding: utf-8 -*-
"""坐标与地点。城、湖坐标取自日文维基百科；各砦无公开坐标，按 DEM 峰顶示意定位（地图标「示意」）。"""
import math

W = "/tmp/claude-0/work"

PLACES = {
    # 区域图
    "北之庄": (136.2209, 36.0655), "长浜": (136.2611, 35.3775), "大垣": (136.6161, 35.3620),
    "岐阜": (136.7822, 35.4341), "清洲": (136.8436, 35.2166), "坂本": (135.8772, 35.0598),
    "木之本": (136.2223, 35.5023), "海津": (136.0615, 35.4617), "柳濑": (136.1853, 35.5965),
    "关原": (136.4669, 35.3655), "余吴湖": (136.1939, 35.5222),
    # 战场（砦为 DEM 峰顶示意）
    "内中尾山": (136.1764, 35.5984), "行市山": (136.1694, 35.5684), "别所山": (136.1750, 35.5780),
    "茂山": (136.1984, 35.5447), "堂木山": (136.2114, 35.5508), "神明山": (136.2185, 35.5554),
    "大岩山": (136.2037, 35.5153), "岩崎山": (136.2191, 35.5213), "贱岳": (136.1927, 35.5061),
    "田上山": (136.2339, 35.5194), "饭浦": (136.1745, 35.5035),
}


def merc(lon, lat, z):
    n = 2 ** z
    return (lon + 180) / 360 * n * 256, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n * 256


class MapGeo:
    """basemap pixel space: mosaic at zoom z, origin tile (x0,y0), upscaled by s."""
    def __init__(self, z, x0, y0, s=1.0):
        self.z, self.x0, self.y0, self.s = z, x0, y0, s

    def __call__(self, lon, lat):
        X, Y = merc(lon, lat, self.z)
        return (X - self.x0 * 256) * self.s, (Y - self.y0 * 256) * self.s

    def p(self, name):
        return self(*PLACES[name])

    def km(self, lat=35.5):
        """pixels per km"""
        return 2 ** self.z * 256 / (40075.0 * math.cos(math.radians(lat))) * self.s
