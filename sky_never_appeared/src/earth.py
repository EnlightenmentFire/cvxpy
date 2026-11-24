"""Night-side Earth: coastlines + city lights only (no borders, no labels).

East Asia / Siberia are removed from every layer and a guard asserts that no
land from that region is ever visible in a rendered frame.
"""
import os, math
import numpy as np
import cv2
import shapefile
from common import W, H, SCRATCH, hexc, blur

NE = os.path.join(SCRATCH, 'data', 'ne')
CACHE = os.path.join(SCRATCH, 'data', 'earth_cache.npz')
TW, TH = 4096, 2048


def forbidden(lat, lon):
    """Region that must never appear: Asia east of ~70E (Siberia, Central and
    East Asia), Chukotka, and the southern hemisphere. Allowed: Arctic, North
    Atlantic, North America, Europe, western USSR."""
    lat = np.asarray(lat); lon = np.asarray(lon)
    return (lat < -20.0) | (lon >= 70.0) | (lon <= -169.0)


def sample(tex, u, v):
    """bilinear sample of an equirectangular texture at float pixel coords."""
    n = len(u)
    k = 1024
    m = (n + k - 1) // k * k
    uu = np.zeros(m, np.float32); vv = np.zeros(m, np.float32)
    uu[:n] = u; vv[:n] = v
    out = cv2.remap(tex, uu.reshape(-1, k), vv.reshape(-1, k), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    return out.reshape(m, *tex.shape[2:])[:n]


def ll2xyz(lat, lon, r=1.0):
    la, lo = np.radians(lat), np.radians(lon)
    return np.stack([r * np.cos(la) * np.cos(lo), r * np.cos(la) * np.sin(lo), r * np.sin(la)], -1)


def _build_cache():
    # land mask --------------------------------------------------------
    from PIL import Image, ImageDraw
    land = Image.new('L', (TW, TH), 0)
    d = ImageDraw.Draw(land)
    r = shapefile.Reader(os.path.join(NE, 'ne_50m_land', 'ne_50m_land.shp'))
    for shp in r.shapes():
        pts = np.array(shp.points)
        parts = list(shp.parts) + [len(pts)]
        for a, b in zip(parts[:-1], parts[1:]):
            ring = pts[a:b]
            xy = [((lo + 180) / 360 * TW, (90 - la) / 180 * TH) for lo, la in ring]
            d.polygon(xy, fill=255)
    lakes = shapefile.Reader(os.path.join(NE, 'ne_50m_lakes', 'ne_50m_lakes.shp'))
    for shp in lakes.shapes():
        pts = np.array(shp.points)
        parts = list(shp.parts) + [len(pts)]
        for a, b in zip(parts[:-1], parts[1:]):
            ring = pts[a:b]
            d.polygon([((lo + 180) / 360 * TW, (90 - la) / 180 * TH) for lo, la in ring], fill=0)
    land_full = np.asarray(land, np.uint8)
    # coastlines -------------------------------------------------------
    c = shapefile.Reader(os.path.join(NE, 'ne_50m_coastline', 'ne_50m_coastline.shp'))
    segs = []
    for shp in c.shapes():
        pts = np.array(shp.points)
        parts = list(shp.parts) + [len(pts)]
        for a, b in zip(parts[:-1], parts[1:]):
            seg = pts[a:b]
            # densify long edges so curved projection looks right
            out = [seg[0]]
            for p, q in zip(seg[:-1], seg[1:]):
                n = int(max(abs(q[0] - p[0]), abs(q[1] - p[1])) / 0.5)
                for k in range(1, n + 1):
                    out.append(p + (q - p) * k / (n + 1))
                out.append(q)
            seg = np.array(out)
            bad = forbidden(seg[:, 1], seg[:, 0])
            # split at forbidden points
            cur = []
            for p, bflag in zip(seg, bad):
                if bflag:
                    if len(cur) > 1:
                        segs.append(np.array(cur))
                    cur = []
                else:
                    cur.append(p)
            if len(cur) > 1:
                segs.append(np.array(cur))
    lens = np.array([len(s) for s in segs])
    coast = np.concatenate(segs)
    # city lights ------------------------------------------------------
    pp = shapefile.Reader(os.path.join(NE, 'ne_10m_populated_places_simple',
                                       'ne_10m_populated_places_simple.shp'))
    names = [f[0] for f in pp.fields][1:]
    ilat, ilon, ipop = names.index('latitude'), names.index('longitude'), names.index('pop_max')
    rng = np.random.default_rng(3)
    L = []
    for rec in pp.iterRecords():
        la, lo, pop = rec[ilat], rec[ilon], max(rec[ipop], 2000)
        if forbidden(la, lo):
            continue
        n = int(np.clip(pop / 60000, 1, 90))
        sig = 0.04 + 0.32 * math.sqrt(pop / 1.2e7)
        dla = rng.normal(0, sig, n)
        dlo = rng.normal(0, sig, n) / max(0.2, math.cos(math.radians(la)))
        inten = (pop / n) ** 0.5 / 400.0 * rng.uniform(0.4, 1.0, n)
        L.append(np.stack([la + dla, lo + dlo, inten], 1))
        L.append(np.array([[la, lo, min(2.5, pop ** 0.5 / 900.0)]]))
    lights = np.concatenate(L)
    keep = ~forbidden(lights[:, 0], lights[:, 1])
    lights = lights[keep]
    # keep lights on land only (rough)
    u = ((lights[:, 1] + 180) % 360 / 360 * TW).astype(int).clip(0, TW - 1)
    v = ((90 - lights[:, 0]) / 180 * TH).astype(int).clip(0, TH - 1)
    lights = lights[land_full[v, u] > 0]
    np.savez_compressed(CACHE, land_full=land_full, coast=coast, lens=lens, lights=lights)


class EarthData:
    def __init__(self):
        if not os.path.exists(CACHE):
            _build_cache()
        z = np.load(CACHE)
        self.land_full = z['land_full']
        # display texture: forbidden region erased, softened
        lat = 90 - (np.arange(TH) + 0.5) / TH * 180
        lon = (np.arange(TW) + 0.5) / TW * 360 - 180
        LO, LA = np.meshgrid(lon, lat)
        self.forb_tex = forbidden(LA, LO)
        land = self.land_full.astype(np.float32) / 255.0
        land[self.forb_tex] = 0
        self.land = cv2.GaussianBlur(land, (5, 5), 1.2)
        # cheap 'terrain' texture so land is not flat
        rng = np.random.default_rng(11)
        n = np.zeros((TH, TW), np.float32)
        for s, a in ((256, 0.5), (64, 0.3), (16, 0.2)):
            g = rng.normal(0, 1, (TH // s + 2, TW // s + 2)).astype(np.float32)
            n += cv2.resize(g, (TW, TH), interpolation=cv2.INTER_CUBIC) * a
        self.terrain = (n * 0.5 + 0.5).clip(0, 1)
        coast, lens = z['coast'], z['lens']
        self.coast_xyz = ll2xyz(coast[:, 1], coast[:, 0], 1.0003).astype(np.float32)
        self.coast_splits = np.cumsum(lens)[:-1]
        li = z['lights']
        self.light_xyz = ll2xyz(li[:, 0], li[:, 1], 1.0004).astype(np.float32)
        self.light_int = li[:, 2].astype(np.float32)
        # stars
        rng = np.random.default_rng(5)
        v = rng.normal(0, 1, (5200, 3))
        self.star_dir = (v / np.linalg.norm(v, axis=1, keepdims=True)).astype(np.float32)
        mag = rng.pareto(2.2, 5200) + 1
        self.star_int = np.clip(mag ** 1.6 * 0.055, 0, 2.2).astype(np.float32)
        tint = rng.uniform(0, 1, 5200)
        self.star_col = np.where(tint[:, None] < 0.2, [1.0, 0.85, 0.7],
                                 np.where(tint[:, None] > 0.8, [0.75, 0.85, 1.0], [1, 1, 1])).astype(np.float32)


_ED = None
def data():
    global _ED
    if _ED is None:
        _ED = EarthData()
    return _ED


def norm(v):
    v = np.asarray(v, np.float64)
    return v / np.linalg.norm(v)


class Cam:
    def __init__(self, pos, target, up=(0, 0, 1), fov=55.0, w=W, h=H):
        self.pos = np.asarray(pos, np.float64)
        self.f = norm(np.asarray(target, np.float64) - self.pos)
        self.r = norm(np.cross(self.f, up))
        self.u = np.cross(self.r, self.f)
        self.w, self.h = w, h
        self.focal = (h / 2) / math.tan(math.radians(fov) / 2)

    def project(self, P):
        d = np.asarray(P, np.float64) - self.pos
        z = d @ self.f
        x = d @ self.r
        y = d @ self.u
        zz = np.where(np.abs(z) < 1e-9, 1e-9, z)
        return self.w / 2 + x / zz * self.focal, self.h / 2 - y / zz * self.focal, z

    def project1(self, P):
        sx, sy, z = self.project(np.asarray(P)[None])
        return float(sx[0]), float(sy[0]), float(z[0])

    def ray_dirs(self, x0=0, y0=0, x1=None, y1=None, step=1):
        x1 = self.w if x1 is None else x1
        y1 = self.h if y1 is None else y1
        xs = (np.arange(x0, x1, step, dtype=np.float32) + 0.5 - self.w / 2) / self.focal
        ys = -(np.arange(y0, y1, step, dtype=np.float32) + 0.5 - self.h / 2) / self.focal
        X, Y = np.meshgrid(xs, ys)
        f, r, u = (self.f.astype(np.float32), self.r.astype(np.float32), self.u.astype(np.float32))
        d = f[None, None] + X[..., None] * r[None, None] + Y[..., None] * u[None, None]
        d /= np.linalg.norm(d, axis=2, keepdims=True)
        return d


class GuardError(RuntimeError):
    pass


def sphere_hits(cam, step=1, box=None):
    x0, y0, x1, y1 = box if box else (0, 0, cam.w, cam.h)
    d = cam.ray_dirs(x0, y0, x1, y1, step)
    C = cam.pos.astype(np.float32)
    b = d @ C
    c = float(C @ C) - 1.0
    disc = b * b - c
    hit = (disc > 0) & (b < 0)
    t = -b - np.sqrt(np.maximum(disc, 0))
    P = C[None, None] + t[..., None] * d
    dmin = np.sqrt(np.maximum(float(C @ C) - b * b, 0))
    return d, hit, P, dmin, b


def guard(cam):
    """Raise if any land from the forbidden region would be visible."""
    ed = data()
    d, hit, P, dmin, b = sphere_hits(cam, step=6)
    if not hit.any():
        return 0
    Ph = P[hit]
    lat = np.degrees(np.arcsin(np.clip(Ph[:, 2], -1, 1)))
    lon = np.degrees(np.arctan2(Ph[:, 1], Ph[:, 0]))
    u = ((lon + 180) / 360 * TW).astype(int).clip(0, TW - 1)
    v = ((90 - lat) / 180 * TH).astype(int).clip(0, TH - 1)
    bad = forbidden(lat, lon) & (ed.land_full[v, u] > 0)
    n = int(bad.sum())
    if n > 0:
        raise GuardError(f'forbidden land visible: {n} samples, e.g. lat {lat[bad][0]:.1f} lon {lon[bad][0]:.1f}')
    return int(hit.sum())


def render_stars(canvas, cam, amount=1.0, occlude=True):
    ed = data()
    D = ed.star_dir
    z = D @ cam.f.astype(np.float32)
    m = z > 0.2
    Dm = D[m]
    x = Dm @ cam.r.astype(np.float32)
    y = Dm @ cam.u.astype(np.float32)
    sx = cam.w / 2 + x / z[m] * cam.focal
    sy = cam.h / 2 - y / z[m] * cam.focal
    inten = ed.star_int[m] * amount
    col = ed.star_col[m]
    ok = (sx >= 1) & (sx < cam.w - 2) & (sy >= 1) & (sy < cam.h - 2)
    if occlude:
        C = cam.pos.astype(np.float32)
        b = Dm @ C
        disc = b * b - (float(C @ C) - 1.0005)
        ok &= ~((disc > 0) & (b < 0))
    sx, sy, inten, col = sx[ok], sy[ok], inten[ok], col[ok]
    buf = np.zeros((cam.h, cam.w, 3), np.float32)
    ix, iy = sx.astype(int), sy.astype(int)
    fx, fy = sx - ix, sy - iy
    for dx, dy, wgt in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        np.add.at(buf, (iy + dy, ix + dx), (col * (inten * wgt)[:, None]))
    buf = cv2.GaussianBlur(buf, (3, 3), 0.6)
    canvas += buf
    return buf


def render_earth(canvas, emis, cam, sun=(0.3, -0.8, 0.5), style='night', light_amt=1.0, coast_amt=1.0,
                 atm_col=(0.30, 0.55, 1.0), atm_amt=1.0, land_col=None, ocean_col=None, coast_col=None,
                 day_amt=0.0, do_guard=True):
    """Draws the planet into canvas (and city lights into emis)."""
    ed = data()
    if do_guard:
        guard(cam)
    sun = norm(sun).astype(np.float32)
    # bounding box of sphere+atmosphere from coarse pass
    d, hit, P, dmin, b = sphere_hits(cam, step=8)
    near = (dmin < 1.2) & (b < 0)
    if not near.any():
        return
    ys, xs = np.nonzero(near)
    x0, x1 = max(0, xs.min() * 8 - 16), min(cam.w, xs.max() * 8 + 24)
    y0, y1 = max(0, ys.min() * 8 - 16), min(cam.h, ys.max() * 8 + 24)
    d, hit, P, dmin, b = sphere_hits(cam, box=(x0, y0, x1, y1))
    region = canvas[y0:y1, x0:x1]
    land_col = hexc('0d141d') if land_col is None else np.asarray(land_col, np.float32)
    ocean_col = hexc('03070d') if ocean_col is None else np.asarray(ocean_col, np.float32)
    coast_col = hexc('7fa6cc') if coast_col is None else np.asarray(coast_col, np.float32)
    atm = np.asarray(atm_col, np.float32)
    # ---- atmosphere halo (outside the disc)
    C = cam.pos.astype(np.float32)
    closest = C[None, None] + (-b)[..., None] * d
    cl_n = closest / np.maximum(np.linalg.norm(closest, axis=2, keepdims=True), 1e-6)
    sun_side = np.clip(cl_n @ sun * 0.9 + 0.35, 0.08, 1.2)
    h_atm = 0.012
    halo = np.exp(-np.maximum(dmin - 1.0, 0) / h_atm) * (b < 0) * np.clip((1.17 - dmin) / 0.1, 0, 1)
    halo2 = np.exp(-np.maximum(dmin - 1.0, 0) / (h_atm * 4)) * (b < 0) * 0.25 * np.clip((1.17 - dmin) / 0.1, 0, 1)
    out_mask = ~hit
    glow = (halo * 0.85 + halo2)[..., None] * atm[None, None] * sun_side[..., None] * atm_amt
    region += glow * out_mask[..., None]
    # ---- surface
    if hit.any():
        Ph = P[hit]
        lat = np.degrees(np.arcsin(np.clip(Ph[:, 2], -1, 1)))
        lon = np.degrees(np.arctan2(Ph[:, 1], Ph[:, 0]))
        u = ((lon + 180) / 360 * TW - 0.5).astype(np.float32)
        v = ((90 - lat) / 180 * TH - 0.5).astype(np.float32)
        lm = sample(ed.land, u, v)
        tr = sample(ed.terrain, u, v)
        nrm = Ph
        view = -d[hit]
        mu = np.clip((nrm * view).sum(1), 0, 1)
        ndl = nrm @ sun
        base = ocean_col[None] * (1 - lm[:, None]) + land_col[None] * lm[:, None] * (0.75 + 0.5 * tr[:, None])
        # faint day side / terminator
        dayc = (hexc('2b4d7a') * (1 - lm[:, None]) + hexc('4f5a4a') * lm[:, None])
        day = np.clip(ndl * 1.6 + 0.08, 0, 1)[:, None] * day_amt
        col = base * (1 - day) + dayc * day
        rim = (1 - mu) ** 2.6
        col = col + atm[None] * rim[:, None] * 0.55 * atm_amt * np.clip(ndl * 0.8 + 0.45, 0.15, 1)[:, None]
        # specular glint of sun on ocean near terminator
        col = col + hexc('ffcf9a')[None] * (np.clip(ndl, 0, 1) ** 8 * (1 - lm) * 0.4 * day_amt)[:, None]
        region[hit] = region[hit] * 0.0 + col
    # ---- coastlines
    if coast_amt > 0:
        _draw_coast(canvas, cam, coast_col, coast_amt)
    # ---- city lights (night side only)
    if light_amt > 0:
        _draw_lights(emis, cam, sun, light_amt)


def _visible(cam, P):
    C = cam.pos.astype(np.float32)
    v = C[None] - P
    return (P * v).sum(1) > 0.0


def _draw_coast(canvas, cam, col, amt):
    ed = data()
    P = ed.coast_xyz
    vis = _visible(cam, P)
    sx, sy, z = cam.project(P)
    ok = vis & (z > 0) & (sx > -200) & (sx < cam.w + 200) & (sy > -200) & (sy < cam.h + 200)
    pts = np.stack([sx, sy], 1)
    m = np.zeros((cam.h, cam.w), np.uint8)
    polys = []
    start = 0
    for end in list(ed.coast_splits) + [len(P)]:
        okk = ok[start:end]
        if okk.any():
            seg = pts[start:end]
            # split on invisible
            idx = np.nonzero(okk)[0]
            breaks = np.nonzero(np.diff(idx) > 1)[0]
            for a_, b_ in zip(np.r_[0, breaks + 1], np.r_[breaks + 1, len(idx)]):
                ii = idx[a_:b_]
                if len(ii) > 1:
                    polys.append(np.round(seg[ii] * 16).astype(np.int32))
        start = end
    if polys:
        cv2.polylines(m, polys, False, 255, 1, cv2.LINE_AA, shift=4)
        a = m.astype(np.float32) / 255.0 * amt
        canvas += a[..., None] * col[None, None] * 0.55


def _draw_lights(emis, cam, sun, amt):
    ed = data()
    P = ed.light_xyz
    vis = _visible(cam, P)
    nd = P @ sun
    night = np.clip(-nd * 5 + 0.25, 0, 1)
    sx, sy, z = cam.project(P)
    ok = vis & (z > 0) & (sx >= 0) & (sx < cam.w - 1) & (sy >= 0) & (sy < cam.h - 1) & (night > 0)
    if not ok.any():
        return
    # dimmer when seen at grazing angle (atmospheric extinction)
    C = cam.pos.astype(np.float32)
    vv = C[None] - P[ok]
    mu = (P[ok] * vv).sum(1) / np.linalg.norm(vv, axis=1)
    inten = ed.light_int[ok] * night[ok] * amt * (0.35 + 0.65 * np.clip(mu * 2.5, 0, 1))
    buf = np.zeros((cam.h, cam.w), np.float32)
    x, y = sx[ok], sy[ok]
    ix, iy = x.astype(int), y.astype(int)
    fx, fy = x - ix, y - iy
    for dx, dy, wgt in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        np.add.at(buf, (iy + dy, ix + dx), inten * wgt)
    core = cv2.GaussianBlur(buf, (5, 5), 0.8)
    halo = cv2.GaussianBlur(buf, (0, 0), 3.0)
    col = hexc('ffc27a')
    emis += (core * 4.0 + halo * 6.0)[..., None] * col[None, None]


def orbit_cam(lat, lon, alt, look_lat, look_lon, look_alt=0.0, fov=55, roll_up=None):
    """camera above (lat, lon) at altitude alt (earth radii), looking at a point."""
    pos = ll2xyz(lat, lon, 1 + alt)
    tgt = ll2xyz(look_lat, look_lon, 1 + look_alt)
    up = pos / np.linalg.norm(pos) if roll_up is None else roll_up
    return Cam(pos, tgt, up=up, fov=fov)
