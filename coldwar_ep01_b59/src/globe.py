"""3D globe from Natural Earth (public domain) coastlines + populated places.

Rules baked in: no country borders are ever loaded; nothing east of LON_MAX
(East Asia never enters the data), nothing west of LON_MIN.
"""
import functools
import math
import os

import cv2
import numpy as np
import shapefile

from engine import ASSETS, H, W, blur, mask_polyline, paint

LON_MIN, LON_MAX = -168.0, 62.0
LAT_MIN, LAT_MAX = -58.0, 84.0
R_EARTH = 6371.0


def _in_region(lon, lat):
    return (lon >= LON_MIN) & (lon <= LON_MAX) & (lat >= LAT_MIN) & (lat <= LAT_MAX)


def ll2v(lat, lon):
    lat = np.radians(lat)
    lon = np.radians(lon)
    return np.stack([np.cos(lat) * np.sin(lon), np.sin(lat), np.cos(lat) * np.cos(lon)], -1)


@functools.lru_cache(maxsize=1)
def coastlines():
    """List of (N,3) unit vectors, split wherever the line leaves the allowed region."""
    sf = shapefile.Reader(os.path.join(ASSETS, "data/ne_50m_coastline/ne_50m_coastline.shp"))
    out = []
    for shp in sf.shapes():
        pts = np.asarray(shp.points, np.float64)
        parts = list(shp.parts) + [len(pts)]
        for a, b in zip(parts[:-1], parts[1:]):
            p = pts[a:b]
            ok = _in_region(p[:, 0], p[:, 1])
            # split into runs of ok points
            idx = np.where(ok)[0]
            if len(idx) == 0:
                continue
            breaks = np.where(np.diff(idx) > 1)[0]
            starts = np.r_[0, breaks + 1]
            ends = np.r_[breaks + 1, len(idx)]
            for s, e in zip(starts, ends):
                run = p[idx[s]:idx[e - 1] + 1]
                if len(run) >= 2:
                    out.append(ll2v(run[:, 1], run[:, 0]))
    return out


@functools.lru_cache(maxsize=1)
def cities():
    """(N,3) vectors + weights for populated places inside the allowed region."""
    sf = shapefile.Reader(os.path.join(ASSETS, "data/ne_10m_populated_places_simple/ne_10m_populated_places_simple.shp"))
    fields = [f[0] for f in sf.fields[1:]]
    i_pop = fields.index("pop_max")
    i_lat = fields.index("latitude")
    i_lon = fields.index("longitude")
    lat, lon, pop = [], [], []
    for r in sf.iterRecords():
        la, lo, po = float(r[i_lat]), float(r[i_lon]), float(r[i_pop] or 0)
        if po < 50000:
            continue
        lat.append(la)
        lon.append(lo)
        pop.append(po)
    lat, lon, pop = map(np.asarray, (lat, lon, pop))
    ok = _in_region(lon, lat)
    v = ll2v(lat[ok], lon[ok])
    w = np.clip((np.log10(pop[ok]) - 4.6) / 2.6, 0.05, 1.0)
    return v, w, lat[ok], lon[ok]


def rot_matrix(lat0, lon0, roll=0.0):
    """Rotation taking the point (lat0, lon0) to +z (towards the viewer), north up."""
    lat0, lon0, roll = map(math.radians, (lat0, lon0, roll))
    # rotate about y by -lon0, then about x by lat0
    cy, sy = math.cos(-lon0), math.sin(-lon0)
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    cx, sx = math.cos(lat0), math.sin(lat0)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    cr, sr = math.cos(roll), math.sin(roll)
    Rz = np.array([[cr, -sr, 0], [sr, cr, 0], [0, 0, 1]])
    return Rz @ Rx @ Ry


class Cam:
    def __init__(self, lat0, lon0, R, cx=W / 2, cy=H / 2, roll=0.0, dist=None):
        self.M = rot_matrix(lat0, lon0, roll)
        self.R, self.cx, self.cy = R, cx, cy
        self.dist = dist  # None = orthographic, else camera distance in earth radii

    def project(self, v):
        """v: (...,3) points (unit sphere = surface). Returns sx, sy, visible."""
        p = v @ self.M.T
        x, y, z = p[..., 0], p[..., 1], p[..., 2]
        r2 = np.sum(v * v, -1)
        if self.dist is None:
            sx = self.cx + self.R * x
            sy = self.cy - self.R * y
            vis = (z > 0) | ((x * x + y * y) > 1.0)
        else:
            d = self.dist
            f = self.R * math.sqrt(d * d - 1)
            s = f / (d - z)
            sx = self.cx + x * s
            sy = self.cy - y * s
            # surface point visible if beyond horizon: v.c > 1/d ; elevated points: not behind the sphere
            on_surf = np.abs(r2 - 1) < 1e-6
            vis_surf = z > 1.0 / d
            # occlusion test for elevated points: ray from camera to point vs sphere
            cam = np.array([0, 0, d])
            dirv = np.stack([x, y, z], -1) - cam
            L = np.linalg.norm(dirv, axis=-1)
            dn = dirv / L[..., None]
            b = np.sum(dn * cam, -1)
            c = d * d - 1
            disc = b * b - c
            tnear = -b - np.sqrt(np.maximum(disc, 0))
            occl = (disc > 0) & (tnear < L - 1e-6) & (tnear > 0)
            vis = np.where(on_surf, vis_surf, ~occl)
        return sx, sy, vis, z

    def horizon_radius(self):
        if self.dist is None:
            return self.R
        return self.R  # by construction


def draw_polylines_vis(sx, sy, vis, thickness, h=H, w=W):
    pts = []
    n = len(sx)
    if n < 2:
        return pts
    idx = np.where(vis)[0]
    if len(idx) < 2:
        return pts
    breaks = np.where(np.diff(idx) > 1)[0]
    starts = np.r_[0, breaks + 1]
    ends = np.r_[breaks + 1, len(idx)]
    for s, e in zip(starts, ends):
        sel = idx[s:e]
        if len(sel) >= 2:
            pts.append(np.stack([sx[sel], sy[sel]], 1))
    return pts


def coast_mask(cam, thickness=1.6, limb_fade=True):
    polys = []
    for v in coastlines():
        sx, sy, vis, z = cam.project(v)
        # cheap off-screen cull
        inside = vis & (sx > -50) & (sx < W + 50) & (sy > -50) & (sy < H + 50)
        polys += draw_polylines_vis(sx, sy, inside, thickness)
    m = mask_polyline(polys, thickness=thickness)
    if limb_fade:
        m *= limb_factor(cam)
    return m


@functools.lru_cache(maxsize=8)
def _limb(cx, cy, R):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / R
    return np.sqrt(np.clip(1 - r * r, 0, 1)) ** 0.6


def limb_factor(cam):
    return _limb(round(cam.cx, 1), round(cam.cy, 1), round(cam.R, 1))


def disk_mask(cam, soft=1.5):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt((xx - cam.cx) ** 2 + (yy - cam.cy) ** 2)
    return np.clip((cam.R - r) / soft + 0.5, 0, 1)


def graticule_mask(cam, step=15, thickness=1.0):
    polys = []
    for lat in range(-75, 90, step):
        lon = np.linspace(-180, 180, 361)
        v = ll2v(np.full_like(lon, lat), lon)
        sx, sy, vis, _ = cam.project(v)
        polys += draw_polylines_vis(sx, sy, vis, thickness)
    for lon in range(-180, 180, step):
        lat = np.linspace(-89, 89, 179)
        v = ll2v(lat, np.full_like(lat, lon))
        sx, sy, vis, _ = cam.project(v)
        polys += draw_polylines_vis(sx, sy, vis, thickness)
    return mask_polyline(polys, thickness=thickness) * limb_factor(cam)


def splat_points(sx, sy, wts, h=H, w=W):
    buf = np.zeros((h, w), np.float32)
    xi = np.round(sx).astype(int)
    yi = np.round(sy).astype(int)
    ok = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
    np.add.at(buf, (yi[ok], xi[ok]), wts[ok])
    return buf


def city_lights(cam, gain=1.0):
    v, wts, _, _ = cities()
    sx, sy, vis, z = cam.project(v)
    buf = splat_points(sx[vis], sy[vis], wts[vis] * gain)
    core = cv2.GaussianBlur(buf, (0, 0), 1.2) * 3.0
    halo = blur(buf, 6) * 18.0
    return core + halo


def small_circle(lat0, lon0, radius_km, n=240):
    """Points of a circle of given great-circle radius around (lat0, lon0)."""
    d = radius_km / R_EARTH
    la1, lo1 = math.radians(lat0), math.radians(lon0)
    brg = np.linspace(0, 2 * math.pi, n)
    la2 = np.arcsin(math.sin(la1) * math.cos(d) + math.cos(la1) * math.sin(d) * np.cos(brg))
    lo2 = lo1 + np.arctan2(np.sin(brg) * math.sin(d) * math.cos(la1), math.cos(d) - math.sin(la1) * np.sin(la2))
    return ll2v(np.degrees(la2), np.degrees(lo2))


def gc_distance_km(lat1, lon1, lat2, lon2):
    a = ll2v(np.array(lat1), np.array(lon1))
    b = ll2v(np.array(lat2), np.array(lon2))
    return float(np.arccos(np.clip(np.dot(a, b), -1, 1)) * R_EARTH)


def arc_points(lat1, lon1, lat2, lon2, height=0.15, n=160, t_end=1.0):
    a = ll2v(np.array(lat1), np.array(lon1))
    b = ll2v(np.array(lat2), np.array(lon2))
    om = math.acos(float(np.clip(np.dot(a, b), -1, 1)))
    ts = np.linspace(0, t_end, max(2, int(n * t_end)))
    if om < 1e-6:
        p = np.repeat(a[None], len(ts), 0)
    else:
        p = (np.sin((1 - ts) * om)[:, None] * a + np.sin(ts * om)[:, None] * b) / math.sin(om)
    alt = 1 + height * np.sin(np.pi * ts)
    return p * alt[:, None], ts


def atmosphere(cam, color, strength=1.0, width=0.06):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt((xx - cam.cx) ** 2 + (yy - cam.cy) ** 2) / cam.R
    inner = np.exp(-((r - 1.0) / (width * 0.6)) ** 2) * (r < 1.0)
    outer = np.exp(-np.clip(r - 1.0, 0, None) / width) * (r >= 1.0)
    a = (inner * 0.55 + outer) * strength
    return a[..., None] * np.asarray(color, np.float32)


# ----------------------------------------------------------------------------
# equirectangular land texture (culled to the allowed region) + inverse projection
# ----------------------------------------------------------------------------
TEX_W, TEX_H = 4096, 2048


@functools.lru_cache(maxsize=1)
def land_texture():
    sf = shapefile.Reader(os.path.join(ASSETS, "data/ne_50m_land/ne_50m_land.shp"))
    tex = np.zeros((TEX_H, TEX_W), np.uint8)
    for shp in sf.shapes():
        pts = np.asarray(shp.points, np.float64)
        parts = list(shp.parts) + [len(pts)]
        polys = []
        for a, b in zip(parts[:-1], parts[1:]):
            p = pts[a:b]
            if np.ptp(p[:, 0]) > 300:  # antimeridian-crossing ring: skip (outside region anyway)
                continue
            q = np.stack([(p[:, 0] + 180) / 360 * TEX_W, (90 - p[:, 1]) / 180 * TEX_H], 1)
            polys.append(np.round(q * 16).astype(np.int32).reshape(-1, 1, 2))
        if polys:
            cv2.fillPoly(tex, polys, 255, cv2.LINE_AA, 4)
    t = tex.astype(np.float32) / 255.0
    lon = np.linspace(-180, 180, TEX_W, endpoint=False)
    lat = np.linspace(90, -90, TEX_H, endpoint=False)
    ok = ((lon >= LON_MIN) & (lon <= LON_MAX))[None, :] & ((lat >= LAT_MIN) & (lat <= LAT_MAX))[:, None]
    t *= ok
    return t


def inverse_lonlat(cam):
    """Per-pixel (lon, lat) for an orthographic cam; NaN outside the disk."""
    xx, yy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    x = (xx - cam.cx) / cam.R
    y = -(yy - cam.cy) / cam.R
    r2 = x * x + y * y
    inside = r2 < 1
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    v = np.stack([x, y, z], -1) @ cam.M  # inverse rotation (M orthonormal)
    lat = np.degrees(np.arcsin(np.clip(v[..., 1], -1, 1)))
    lon = np.degrees(np.arctan2(v[..., 0], v[..., 2]))
    return lon, lat, inside, z


def land_mask(cam):
    lon, lat, inside, z = inverse_lonlat(cam)
    mx = ((lon + 180) / 360 * TEX_W).astype(np.float32)
    my = ((90 - lat) / 180 * TEX_H).astype(np.float32)
    m = cv2.remap(land_texture(), mx, my, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    return m * inside, z * inside
