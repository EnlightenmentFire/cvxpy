# -*- coding: utf-8 -*-
"""高松城周边的示意地形世界（km 坐标：x 向东，y 向北，城在原点）。
- 高程场（m）、地表纹理（稻田、沼地、村落、城郭、山林、河流）、堤坝、蓄水盆地
- 两种机位：俯视地图 topdown()；斜俯视（航拍感）oblique()
- 水位 level（m，海拔）随旁白上涨；被淹处按水深渐隐
全部为示意，不是测绘数据。
"""
import os, math
import numpy as np
import cairo
from scipy import ndimage
from gfx import *

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
X0, X1, Y0, Y1 = -8.0, 6.0, -7.0, 7.0
N = 2800                          # texture px per side
RES = (X1 - X0) / N               # km per px (~4.3 m); square texture

# ---------------------------------------------------------------- places (示意)
P = {
    "castle": (0.0, 0.0),
    "龙王山": (1.25, 2.15),
    "石井山": (1.55, 0.35),
    "蛙鼻": (1.05, -0.85),
    "门前村": (-1.95, 0.40),
    "岩崎山": (-3.75, 1.35),
    "日差山": (-4.35, -2.75),
}
DIKE = [(-2.05, 1.55), (-1.95, 0.40), (-1.55, -0.75), (-0.55, -1.30), (0.45, -1.25), (1.05, -0.85)]
RIVER = [(-2.9, 7.2), (-2.65, 3.6), (-2.35, 2.3), (-2.2, 1.2), (-2.12, 0.35), (-2.45, -1.0), (-2.35, -2.6),
         (-1.85, -3.8), (-1.1, -5.2), (-0.6, -7.2)]
HILLS = [  # (x, y, height m, sx km, sy km)
    (1.25, 2.15, 120, 0.55, 0.45), (1.55, 0.35, 60, 0.32, 0.55), (1.18, -0.6, 22, 0.18, 0.35),
    (2.7, 0.9, 170, 0.9, 1.1), (3.4, -1.0, 140, 0.8, 0.9), (2.4, 3.2, 160, 1.0, 0.7),
    (0.0, 3.9, 190, 1.6, 0.6), (-1.6, 3.4, 150, 1.0, 0.7), (-2.0, 2.2, 45, 0.35, 0.35), (-3.2, 3.8, 200, 1.2, 0.9),
    (-3.75, 1.35, 90, 0.55, 0.5), (-4.9, 0.6, 140, 0.9, 1.0), (-4.35, -2.75, 160, 0.75, 0.7),
    (-5.4, -1.6, 120, 0.7, 1.0), (-4.9, -4.2, 90, 0.9, 0.7), (3.6, -3.6, 60, 0.9, 0.8), (3.8, 3.8, 180, 0.9, 1.2),
]
L_FIELDS, L_TOWN, L_BAILEY, L_FINAL = 3.55, 4.35, 5.05, 5.35     # three rises + final
LEVEL_DRY = 0.0


def w2i(x, y):
    return (x - X0) / RES, (Y1 - y) / RES


def seg_dist(px, py, pts):
    """distance (km) from grid points to polyline"""
    d = np.full(px.shape, 1e9, np.float32)
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        vx, vy = bx - ax, by - ay
        L2 = vx * vx + vy * vy
        t = np.clip(((px - ax) * vx + (py - ay) * vy) / L2, 0, 1)
        dd = np.hypot(px - (ax + t * vx), py - (ay + t * vy))
        d = np.minimum(d, dd)
    return d


def _build():
    rng = np.random.default_rng(7)
    xs = X0 + (np.arange(N) + 0.5) * RES
    ys = Y1 - (np.arange(N) + 0.5) * RES
    gx, gy = np.meshgrid(xs.astype(np.float32), ys.astype(np.float32))
    # ---- height
    h = 3.35 + 0.15 * np.clip(gy, -7, 0) + 1.0 * np.clip(gy - 0.3, 0, 7) + 0.25 * np.abs(gx + 0.4)
    h += (noise2d(N, N, 220, rng, 3) - 0.5) * 0.5
    hill = np.zeros_like(h)
    for (x, y, z, sx, sy) in HILLS:
        g = np.exp(-(((gx - x) / sx) ** 2 + ((gy - y) / sy) ** 2))
        hill = np.maximum(hill, z * g ** 0.9)
    rough = noise2d(N, N, 40, rng, 4)
    hill *= 0.75 + 0.5 * rough
    h += hill
    r = np.hypot(gx, gy)
    marsh = np.clip(1 - (r - 0.30) / 0.60, 0, 1)
    CS = 2.4                       # castle drawn ~2.4x for legibility (示意)
    gx_, gy_ = gx, gy
    gx, gy = gx / CS, gy / CS
    h -= 0.55 * marsh
    # castle earthworks
    hon = (np.abs(gx) < 0.055) & (np.abs(gy - 0.01) < 0.045)
    ni = (np.abs(gx + 0.02) < 0.13) & (np.abs(gy) < 0.10) & ~hon
    san = (np.abs(gx + 0.04) < 0.21) & (np.abs(gy + 0.01) < 0.16) & ~hon & ~ni
    moat = (((np.abs(gx) < 0.075) & (np.abs(gy - 0.01) < 0.065)) & ~hon) | \
           (((np.abs(gx + 0.02) < 0.15) & (np.abs(gy) < 0.12)) & ~ni & ~hon & ~(((np.abs(gx) < 0.075) & (np.abs(gy - 0.01) < 0.065))))
    h[san] = 4.75 + 0.05 * rough[san]
    h[ni] = 4.95
    h[hon] = 6.9
    h[moat] = 2.4
    gx, gy = gx_, gy_
    # river channel
    rd = seg_dist(gx, gy, RIVER)
    river = rd < 0.035
    h = np.where(river, np.minimum(h, 2.2), h)
    # dike
    dd = seg_dist(gx, gy, DIKE)
    dike = dd < 0.022
    # ---- basin: component of (h < 6.2) & ~dike & ~river containing the castle
    low = (h < 6.2) & ~dike & ~river
    lab, _ = ndimage.label(low)
    ci, cj = w2i(-0.3, 0.3)
    basin = lab == lab[int(cj), int(ci)]
    # ---- colours
    col = np.zeros((N, N, 3), np.float32)
    # paddies: rotated grid cells
    a = math.radians(8)
    u = (gx * math.cos(a) + gy * math.sin(a)) / 0.032
    v = (-gx * math.sin(a) + gy * math.cos(a)) / 0.075
    cu, cv = np.floor(u), np.floor(v)
    hsh = (np.sin(cu * 12.9898 + cv * 78.233) * 43758.5453) % 1.0
    fu, fv = u - cu, v - cv
    bund = (fu < 0.07) | (fv < 0.05)
    base = np.stack([0.31 + 0.05 * hsh, 0.36 + 0.05 * hsh, 0.22 + 0.02 * hsh], -1)
    wet_p = (hsh > 0.55)[..., None]
    base = np.where(wet_p, base * np.array([0.85, 0.95, 1.05]) + np.array([0.0, 0.02, 0.05]), base)
    base = np.where(bund[..., None], base * 0.75 + 0.12, base)
    col[:] = base
    # marsh
    mk = (marsh > 0.05)[..., None]
    pud = noise2d(N, N, 18, rng, 3)
    marsh_c = np.stack([0.20 + 0.08 * pud, 0.23 + 0.08 * pud, 0.14 + 0.04 * pud], -1)
    marsh_c = np.where((pud > 0.62)[..., None], np.array([0.22, 0.27, 0.26]), marsh_c)
    m = marsh[..., None] ** 0.7
    col = np.where(mk, col * (1 - m) + marsh_c * m, col)
    # hills: forest + shade
    hk = np.clip(hill / 25.0, 0, 1)[..., None]
    forest = np.stack([0.10 + 0.08 * rough, 0.17 + 0.10 * rough, 0.10 + 0.05 * rough], -1)
    col = col * (1 - hk) + forest * hk
    # roads
    roads = [[(-6, -0.35), (-2.4, -0.25), (-0.3, -0.12), (0.0, -0.08)], [(0.0, 0.12), (0.4, 0.9), (1.0, 1.6), (2.0, 2.4)],
             [(0.1, -0.1), (0.6, -0.9), (1.6, -2.4), (2.6, -5)], [(-2.2, 0.4), (-1.2, 0.1), (-0.25, 0.0)]]
    for rp in roads:
        rdd = seg_dist(gx, gy, rp)
        k = (rdd < 0.012)[..., None]
        col = np.where(k & (hill[..., None] < 20), np.array([0.52, 0.46, 0.34]), col)
    # villages / town houses
    houses = np.zeros((N, N), bool)
    centres = [(-0.05, -0.62, 0.22, 90), (0.62, 0.1, 0.16, 50), (-0.7, 0.35, 0.15, 40), (-2.3, 0.55, 0.2, 45),
               (-1.0, -0.6, 0.15, 30), (0.7, 0.75, 0.15, 30), (0.45, -0.55, 0.15, 35), (-1.5, 1.2, 0.18, 25)]
    hmask_list = []
    for (cx, cy, rr, n) in centres:
        for _ in range(n):
            x = cx + rng.normal(0, rr * 0.5); y = cy + rng.normal(0, rr * 0.5)
            i, j = w2i(x, y)
            i, j = int(i), int(j)
            ww, hh = rng.integers(3, 6), rng.integers(4, 7)
            if rng.random() < 0.5:
                ww, hh = hh, ww
            sl = (slice(max(j, 0), j + hh), slice(max(i, 0), i + ww))
            if 0 <= i < N - 8 and 0 <= j < N - 8:
                houses[sl] = True
    tone = rng.random((N, N)).astype(np.float32)
    roof = np.stack([0.24 + 0.06 * tone, 0.22 + 0.05 * tone, 0.20 + 0.04 * tone], -1)
    col = np.where(houses[..., None], roof, col)
    edge = houses & ~ndimage.binary_erosion(houses)
    col = np.where(edge[..., None], np.array([0.42, 0.40, 0.36]), col)
    h = np.where(houses, h + 0.15, h)
    # castle colours
    gx, gy = gx / CS, gy / CS
    col[san] = np.array([0.40, 0.38, 0.30])
    col[ni] = np.array([0.46, 0.44, 0.38])
    col[hon] = np.array([0.58, 0.56, 0.50])
    stone = (hon & ~ndimage.binary_erosion(hon, iterations=2)) | (ni & ~ndimage.binary_erosion(ni, iterations=2))
    col[stone] = np.array([0.78, 0.76, 0.70])
    # honmaru buildings (dark roofs, white walls)
    bl = [(-0.03, 0.025, 0.022, 0.016), (0.02, 0.03, 0.016, 0.012), (0.025, -0.01, 0.018, 0.014), (-0.025, -0.015, 0.015, 0.01)]
    for (bx, by, bw, bh) in bl:
        k = (np.abs(gx - bx) < bw) & (np.abs(gy - by) < bh)
        col[k] = np.array([0.20, 0.20, 0.22])
        kk = k & ~ndimage.binary_erosion(k)
        col[kk] = np.array([0.88, 0.86, 0.80])
    # ninomaru buildings
    for (bx, by, bw, bh) in [(-0.10, 0.06, 0.02, 0.012), (-0.11, -0.06, 0.016, 0.012), (0.09, -0.07, 0.014, 0.01)]:
        k = (np.abs(gx - bx) < bw) & (np.abs(gy - by) < bh)
        col[k] = np.array([0.24, 0.22, 0.22])
    gx, gy = gx_, gy_
    # hillshade
    gyh, gxh = np.gradient(h, RES * 1000)
    sh = (-gxh * 0.6 + gyh * 0.8)
    shade = np.clip(1.0 + sh * 1.6, 0.45, 1.5)[..., None]
    col *= shade
    # dike
    dk = (dd < 0.022)[..., None]
    dcol = np.array([0.62, 0.52, 0.36]) * (1.0 + 0.15 * np.clip((0.022 - dd) / 0.022, 0, 1))[..., None]
    col = np.where(dk, dcol, col)
    h = np.where(dike, 9.0, h)
    # permanent water: river + moat
    perm = river | moat
    col = np.clip(col, 0, 1)
    np.savez_compressed(f"{WORK}/world_cache.npz", col=(col * 255).astype(np.uint8), h=h.astype(np.float16),
                        basin=basin, perm=perm, dike_d=dd.astype(np.float16))


_W = {}


def world():
    if not _W:
        fn = f"{WORK}/world_cache.npz"
        if not os.path.exists(fn):
            _build()
        z = np.load(fn)
        _W["col"] = z["col"]
        _W["h"] = z["h"].astype(np.float32)
        _W["basin"] = z["basin"]
        _W["perm"] = z["perm"]
        _W["dike_d"] = z["dike_d"].astype(np.float32)
        rng = np.random.default_rng(3)
        _W["wn"] = noise2d(512, 512, 24, rng, 4).astype(np.float32)   # wave tile
        _W["wn2"] = noise2d(512, 512, 9, rng, 3).astype(np.float32)
    return _W


MUD = np.array([0.60, 0.47, 0.28], np.float32)      # 浑黄
MUD_D = np.array([0.30, 0.25, 0.17], np.float32)
RIVER_C = np.array([0.30, 0.34, 0.33], np.float32)


def water_shade(col, h, basin, perm, gxw, gyw, level, t, dike_prog=1.0, sky=None, fres=None, rain=0.0, dikeok=None):
    """col: (...,3) float32 land; returns shaded composite. gxw/gyw: world km for wave sampling"""
    Wd = world()
    depth = level - h
    wet = basin & (depth > 0)
    if dikeok is not None:
        wet &= dikeok
    a = np.clip(depth / 0.9, 0, 1) * wet
    a = np.maximum(a, perm * 0.95)
    if not a.any():
        return col
    # waves: sample tiles by world coords
    ti = (gxw * 60 + t * 3.0).astype(np.int32) % 512; tj = (gyw * 60 + t * 1.3).astype(np.int32) % 512
    w1 = Wd["wn"][tj, ti]
    ti2 = (gxw * 90 - t * 5.0).astype(np.int32) % 512; tj2 = (gyw * 420 + t * 9.0).astype(np.int32) % 512
    w2 = Wd["wn2"][tj2, ti2]
    wv = (w1 * 0.6 + w2 * 0.4)
    dk = np.clip(depth / 2.5, 0, 1)
    wc = MUD[None, :] * (1 - dk[..., None] * 0.45) + MUD_D[None, :] * dk[..., None] * 0.45
    streak = np.clip((w2 - 0.45) * 2.2, 0, 1)
    wc = wc * (0.62 + 0.45 * w1[..., None] + 0.35 * streak[..., None])
    spec = np.clip((w1 - 0.60) * 3, 0, 1) * 0.10
    wc = wc + spec[..., None]
    wc = np.where(perm[..., None] & ~wet[..., None], RIVER_C * (0.85 + 0.3 * wv[..., None]), wc)
    if sky is not None and fres is not None:
        wc = wc * (1 - fres[..., None]) + sky * fres[..., None]
    # foam at shoreline
    foam = (np.clip(1 - np.abs(depth - 0.05) / 0.12, 0, 1) * wet)[..., None] * 0.18
    wc = wc + foam
    if rain > 0:
        sp = np.clip((w2 - 0.74) * 5, 0, 1) * rain * 0.10
        wc = wc + sp[..., None]
    out = col * (1 - a[..., None]) + wc * a[..., None]
    return out


# ---------------------------------------------------------------- top-down
def topdown(level, t, cx=-0.6, cy=0.0, s=120.0, cy_screen=860, tint=0.0, rain=0.0, dim=0.0, w=W, h=H, dikeok=None, step=2):
    """returns cairo surface (W x H) of the world seen from above. s = px per km. computed at 1/step res."""
    Wd = world()
    sx = np.arange(0, w, step, dtype=np.float32) + step / 2; sy = np.arange(0, h, step, dtype=np.float32) + step / 2
    gxw = cx + (sx - w / 2) / s
    gyw = cy - (sy - cy_screen) / s
    ii = np.clip(((gxw - X0) / RES).astype(np.int32), 0, N - 1)
    jj = np.clip(((Y1 - gyw) / RES).astype(np.int32), 0, N - 1)
    J, I = np.meshgrid(jj, ii, indexing="ij")
    GX, GY = np.meshgrid(gxw, gyw)
    col = Wd["col"][J, I].astype(np.float32) / 255
    hh = Wd["h"][J, I]
    out = water_shade(col, hh, Wd["basin"][J, I], Wd["perm"][J, I], GX, GY, level, t, rain=rain,
                      dikeok=None if dikeok is None else dikeok(GX, GY))
    if tint > 0:
        g = out.mean(-1, keepdims=True)
        out = out * (1 - tint) + (g * np.array([0.95, 0.9, 0.8]) * 0.85) * tint
    if dim > 0:
        out *= (1 - dim)
    return upscale(surface_from_rgb(out), step)


def upscale(surf, step):
    if step == 1:
        return surf
    s2, c2 = new_surface()
    c2.scale(step, step)
    c2.set_source_surface(surf, 0, 0)
    c2.get_source().set_filter(cairo.FILTER_BILINEAR)
    c2.paint()
    return s2


def to_screen_td(x, y, cx=-0.6, cy=0.0, s=120.0, cy_screen=860):
    return W / 2 + (x - cx) * s, cy_screen - (y - cy) * s


# ---------------------------------------------------------------- oblique
class Cam:
    def __init__(self, x, y, z, yaw, pitch, F=1150.0, hy=None):
        self.x, self.y, self.z = x, y, z
        self.yaw, self.pitch, self.F = math.radians(yaw), math.radians(pitch), F
        cy, sy = math.cos(self.yaw), math.sin(self.yaw)
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        self.f = np.array([sy * cp, cy * cp, -sp])
        self.r = np.array([cy, -sy, 0.0])
        self.u = np.cross(self.r, self.f)

    def project(self, x, y, z=0.0):
        d = np.array([x - self.x, y - self.y, z - self.z])
        zc = d @ self.f
        if zc <= 0.01:
            return None
        return W / 2 + self.F * (d @ self.r) / zc, H / 2 - self.F * (d @ self.u) / zc, self.F / zc


SKY_TOP = np.array([0.10, 0.11, 0.13], np.float32)
SKY_HOR = np.array([0.33, 0.34, 0.34], np.float32)
FOG = np.array([0.33, 0.34, 0.34], np.float32)


def oblique(cam, level, t, rain=1.0, fogd=4.0, flash=0.0, sky_top=SKY_TOP, sky_hor=SKY_HOR, fog=FOG, step=1):
    """perspective ground render -> float rgb (H, W, 3)"""
    Wd = world()
    hs, ws = H // step, W // step
    u = (np.arange(ws, dtype=np.float32) * step + step / 2 - W / 2)
    v = (np.arange(hs, dtype=np.float32) * step + step / 2 - H / 2)
    U, V = np.meshgrid(u, v)
    F = cam.F
    dx = cam.f[0] + U / F * cam.r[0] - V / F * cam.u[0]
    dy = cam.f[1] + U / F * cam.r[1] - V / F * cam.u[1]
    dz = cam.f[2] + U / F * cam.r[2] - V / F * cam.u[2]
    ground = dz < -1e-4
    tt = np.where(ground, cam.z / np.maximum(-dz, 1e-4), 0)
    GX = cam.x + tt * dx; GY = cam.y + tt * dy
    fi = (GX - X0) / RES; fj = (Y1 - GY) / RES
    inside = ground & (fi >= 0) & (fi < N - 1) & (fj >= 0) & (fj < N - 1)
    i0 = np.clip(fi.astype(np.int32), 0, N - 2); j0 = np.clip(fj.astype(np.int32), 0, N - 2)
    ax = np.clip(fi - i0, 0, 1)[..., None]; ay = np.clip(fj - j0, 0, 1)[..., None]
    C = Wd["col"]
    col = ((C[j0, i0] * (1 - ax) + C[j0, i0 + 1] * ax) * (1 - ay) + (C[j0 + 1, i0] * (1 - ax) + C[j0 + 1, i0 + 1] * ax) * ay) / 255.0
    col = col.astype(np.float32)
    hh = Wd["h"][j0, i0]
    dist = tt * np.sqrt(dx * dx + dy * dy + dz * dz)
    # sky reflection / fresnel for water
    grazing = np.clip(1 - (-dz) / np.sqrt(dx * dx + dy * dy + dz * dz) * 2.2, 0, 1) ** 2
    sky_ref = (sky_hor * 1.25 + 0.3 * flash)
    out = water_shade(col, hh, Wd["basin"][j0, i0] & inside, Wd["perm"][j0, i0] & inside, GX, GY, level, t,
                      sky=sky_ref, fres=0.25 + grazing * 0.55, rain=rain)
    # fog by distance
    edge = np.minimum(np.minimum(GX - X0, X1 - GX), np.minimum(GY - Y0, Y1 - GY))
    fk = np.maximum(1 - np.exp(-dist / fogd), 1 - np.clip(edge / 2.5, 0, 1))[..., None]
    out = out * (1 - fk) + fog * fk
    # outside texture -> distant plain/fog
    out = np.where(inside[..., None], out, fog)
    # sky
    vv = (V - (-H / 2)) / H
    hor_v = np.where(ground, 0, 1)
    sky = sky_top[None, None, :] * (1 - np.clip(vv * 2.2, 0, 1)[..., None]) + sky_hor[None, None, :] * np.clip(vv * 2.2, 0, 1)[..., None]
    out = np.where(ground[..., None], out, sky)
    if flash > 0:
        out = out + flash * 0.35
    return np.clip(out, 0, 1)


def oblique_surface(cam, level, t, step=2, **kw):
    return upscale(surface_from_rgb(oblique(cam, level, t, step=step, **kw)), step)


def horizon_y(cam):
    """screen y of the horizon line"""
    # direction with dz = 0: v such that f_z - v/F*u_z = 0
    if abs(cam.u[2]) < 1e-6:
        return -1e9
    return H / 2 + cam.F * cam.f[2] / cam.u[2]


def ridges(ctx, cam, t, alpha=1.0, seed=0, color=(0.16, 0.17, 0.18), fog=FOG):
    """distant mountain silhouettes standing on the far edge of the texture (hides the sky/fog seam)"""
    hy = horizon_y(cam)
    if hy < -200 or hy > H:
        return
    d = 6.5
    p = cam.project(cam.x + cam.f[0] / math.hypot(cam.f[0], cam.f[1]) * d, cam.y + cam.f[1] / math.hypot(cam.f[0], cam.f[1]) * d, 0)
    yf = p[1] if p else hy + 40
    yf = max(yf, hy + 4)
    gap = yf - hy
    rng = np.random.default_rng(seed)
    g = cairo.LinearGradient(0, hy - 10, 0, yf + 60)
    g.add_color_stop_rgba(0, *fog, 0.0); g.add_color_stop_rgba(0.5, *fog, 0.9 * alpha); g.add_color_stop_rgba(1, *fog, 0.0)
    ctx.rectangle(0, hy - 10, W, gap + 70); ctx.set_source(g); ctx.fill()
    for layer, (amp, a_, c) in enumerate([(120, 0.55, (0.22, 0.23, 0.24)), (70, 0.85, color)]):
        ph = rng.random(6) * 10
        base = yf + 6 - layer * 0
        ctx.move_to(-10, base)
        off = math.degrees(cam.yaw) * (6 + layer * 4)
        for x in range(-10, W + 20, 12):
            xx = (x + off) / W
            yv = sum(math.sin(xx * (k + 1.7) * 3.1 + ph[k]) / (k + 1) for k in range(6))
            ctx.line_to(x, base - gap - amp * (0.55 + 0.35 * yv) * (1 + layer * 0.2))
        ctx.line_to(W + 20, base); ctx.close_path()
        ctx.set_source_rgba(*c, a_ * alpha); ctx.fill()
    g = cairo.LinearGradient(0, yf - 30, 0, yf + 50)
    g.add_color_stop_rgba(0, *fog, 0.0); g.add_color_stop_rgba(0.5, *fog, 0.85 * alpha); g.add_color_stop_rgba(1, *fog, 0.0)
    ctx.rectangle(0, yf - 30, W, 80); ctx.set_source(g); ctx.fill()


# ---------------------------------------------------------------- sprites in oblique view
def banner(ctx, p, color, alpha=1.0, t=0.0, ph=0.0, size=1.0):
    """nobori banner (tall vertical flag) at projected point p=(sx, sy, scale)"""
    if p is None or alpha <= 0:
        return
    x, y, k = p
    hgt = 0.022 * k * size        # pole ~22 m (exaggerated for legibility)
    if hgt < 2:
        return
    wv = 0.006 * k * size
    ctx.set_source_rgba(0.08, 0.07, 0.06, alpha); ctx.set_line_width(max(1, hgt * 0.03))
    ctx.move_to(x, y); ctx.line_to(x, y - hgt); ctx.stroke()
    sway = math.sin(t * 3.0 + ph) * wv * 0.25
    ctx.move_to(x, y - hgt); ctx.line_to(x + wv + sway, y - hgt + wv * 0.1)
    ctx.line_to(x + wv + sway * 1.4, y - hgt * 0.38); ctx.line_to(x, y - hgt * 0.40); ctx.close_path()
    ctx.set_source_rgba(*color, 0.95 * alpha); ctx.fill()


def hut(ctx, p, alpha=1.0, sub=0.0, w=1.0, color=(0.20, 0.19, 0.20)):
    """simple building: white wall + dark roof; sub 0..1 = fraction under water (drawn tinted)"""
    if p is None or alpha <= 0:
        return
    x, y, k = p
    bw = 0.012 * k * w; bh = 0.006 * k * w; rh = 0.006 * k * w
    if bw < 1.5:
        return
    ctx.rectangle(x - bw / 2, y - bh, bw, bh); ctx.set_source_rgba(0.85, 0.83, 0.77, alpha); ctx.fill()
    ctx.move_to(x - bw * 0.62, y - bh); ctx.line_to(x - bw * 0.3, y - bh - rh); ctx.line_to(x + bw * 0.3, y - bh - rh)
    ctx.line_to(x + bw * 0.62, y - bh); ctx.close_path(); ctx.set_source_rgba(*color, alpha); ctx.fill()
    if sub > 0:
        hh = (bh + rh) * min(sub, 1.0)
        ctx.rectangle(x - bw * 0.65, y - hh, bw * 1.3, hh)
        ctx.set_source_rgba(*MUD * 0.85, 0.92 * alpha); ctx.fill()


def boat(ctx, p, alpha=1.0, color=(0.12, 0.10, 0.08), people=2):
    if p is None or alpha <= 0:
        return
    x, y, k = p
    L = 0.016 * k
    if L < 2:
        return
    ctx.move_to(x - L, y - L * 0.08); ctx.line_to(x + L, y - L * 0.08); ctx.line_to(x + L * 0.75, y + L * 0.12)
    ctx.line_to(x - L * 0.8, y + L * 0.12); ctx.close_path(); ctx.set_source_rgba(*color, alpha); ctx.fill()
    for i in range(people):
        px = x - L * 0.3 + i * L * 0.5
        ctx.rectangle(px - L * 0.06, y - L * 0.42, L * 0.12, L * 0.34); ctx.set_source_rgba(0.06, 0.05, 0.05, alpha); ctx.fill()
        ctx.arc(px, y - L * 0.5, L * 0.08, 0, 2 * math.pi); ctx.fill()


def rain_overlay(ctx, t, density=1.0, alpha=0.45, seed=3, slant=0.22, length=60):
    rng = np.random.default_rng(seed)
    n = int(420 * density)
    xs = rng.random(n) * (W + 400) - 200
    ys0 = rng.random(n) * H
    sp = rng.uniform(1700, 2600, n)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for i in range(n):
        y = (ys0[i] + t * sp[i]) % (H + 200) - 100
        x = xs[i] + (y * slant)
        L = length * (0.6 + 0.6 * (sp[i] - 1700) / 900)
        ctx.move_to(x, y); ctx.line_to(x - L * slant, y - L)
        ctx.set_source_rgba(0.78, 0.80, 0.84, alpha * (0.35 + 0.65 * (sp[i] - 1700) / 900))
        ctx.set_line_width(1.2 + 1.3 * (sp[i] - 1700) / 900); ctx.stroke()


def lightning(ctx, x0, t_local, seed=0, alpha=1.0, y1=700):
    """bolt drawn for ~0.25 s after a strike (t_local from strike)"""
    if t_local < 0 or t_local > 0.35:
        return
    rng = np.random.default_rng(seed)
    a = alpha * (1 - t_local / 0.35) * (0.6 + 0.4 * (rng.random() > 0.3))
    pts = [(x0, -20)]
    y = -20; x = x0
    while y < y1:
        y += rng.uniform(30, 80); x += rng.uniform(-45, 45)
        pts.append((x, y))
    for wdt, al in ((16, 0.12), (7, 0.3), (2.5, 1.0)):
        path(ctx, pts); ctx.set_source_rgba(0.92, 0.94, 1.0, al * a); ctx.set_line_width(wdt); ctx.stroke()
