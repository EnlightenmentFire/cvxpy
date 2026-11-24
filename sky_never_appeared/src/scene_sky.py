"""The imagined 1983 sky: orbital laser stations, rising missiles, X-ray laser.

Used for the cold open (sec. 1) and for the ending replay (sec. 10), where
beams go out one by one and the stations dissolve into wireframes.
"""
import math
import numpy as np
from common import *
import earth as E
import models3d as M3
import fx

RNG = np.random.default_rng(42)
SUN = E.ll2xyz(-8, 100)


def cam_at(t, drift=1.0):
    k = t / 20.0 * drift
    return E.orbit_cam(26 + 0.05 * k, -79 + 0.12 * k, 0.22 - 0.0015 * k, 56, -76 + 0.05 * k, look_alt=0.07, fov=58)


# ---------------------------------------------------------------- missiles
class Missile:
    def __init__(self, i, rng):
        self.t0 = 0.3 + i * 0.16 + rng.uniform(0, 0.6)
        self.lat0 = rng.uniform(70, 80)
        self.lon0 = rng.uniform(-118, -34)
        self.dlat = -rng.uniform(14, 22)
        self.dlon = rng.uniform(-5, 5)
        self.hmax = rng.uniform(0.13, 0.2)
        self.dur = rng.uniform(7.0, 9.0)
        self.kill = None    # time of kill (set by scenario)

    def pos(self, t):
        s = clamp((t - self.t0) / self.dur, 0, 1.4)
        h = self.hmax * math.sin(min(s, 1.0) * math.pi / 2) ** 0.75 + max(0, s - 1) * 0.01
        return E.ll2xyz(self.lat0 + self.dlat * s, self.lon0 + self.dlon * s, 1 + h)

    def trail(self, t, n=30, length=4.0):
        ts = np.linspace(max(self.t0, t - length), t, n)
        return np.stack([self.pos(x) for x in ts])


MISSILES = [Missile(i, RNG) for i in range(34)]


def setup_station(cam0, fwd, right, up, scale):
    C = cam0.pos
    return C + cam0.f * fwd + cam0.r * right + cam0.u * up, scale


CAM0 = cam_at(0)
STATIONS = [
    # (position, scale, base yaw offset)
    setup_station(CAM0, 0.030, -0.0040, 0.0060, 0.00140),
    setup_station(CAM0, 0.085, 0.020, 0.012, 0.0011),
    setup_station(CAM0, 0.140, -0.030, 0.022, 0.0011),
]

# kill schedule: (time, station index, missile index)
KILLS = [(6.2, 0, 3), (6.9, 1, 9), (7.5, 0, 14), (8.0, 2, 1), (8.4, 1, 20), (8.9, 0, 6),
         (9.3, 2, 25), (9.7, 1, 12), (10.1, 0, 17), (10.5, 2, 28), (10.8, 1, 4), (11.2, 0, 22)]
for kt, si, mi in KILLS:
    MISSILES[mi].kill = kt
XRAY_T = 12.4
XRAY_POS = CAM0.pos + CAM0.f * 0.16 + CAM0.r * 0.035 + CAM0.u * 0.05
XRAY_TARGETS = [0, 2, 5, 7, 8, 10, 11, 13, 15, 16, 18, 19, 21, 23, 24, 26, 27, 29, 30, 31, 32, 33]
for mi in XRAY_TARGETS:
    if MISSILES[mi].kill is None:
        MISSILES[mi].kill = XRAY_T + 0.06 + 0.035 * (mi % 7)
BURSTS = {i: fx.Burst(seed=100 + i, n=26) for i in range(len(MISSILES))}
XBURST = fx.Burst(seed=999, n=60)
XMOD, XDIRS = M3.xray_module(n_rods=26)


def station_mesh(open_amt, charge=0.0):
    return M3.battle_station(mirror_open=open_amt, panels_open=open_amt, charge=charge)


_MESH_CACHE = {}
def station_mesh_cached(open_amt, charge=0.0):
    k = (round(open_amt, 2), round(charge, 1))
    if k not in _MESH_CACHE:
        _MESH_CACHE[k] = station_mesh(*k)
    return _MESH_CACHE[k]


def station_charge(si, tt):
    c = 0.0
    for kt, s, mi in KILLS:
        if s == si:
            c = max(c, pulse(tt, kt - 0.9, 0.45, 0.4, 0.25))
    return c


def aim_dir(si, t):
    """station orientation: turns toward its current/next target, then holds on its last one."""
    pos, _ = STATIONS[si]
    mine = [(kt, mi) for kt, s, mi in KILLS if s == si]
    tgt = None
    for kt, mi in mine:
        if kt + 0.4 >= t:
            tgt = MISSILES[mi].pos(min(t, kt))
            break
    if tgt is None and mine:
        kt, mi = mine[-1]
        tgt = MISSILES[mi].pos(kt)
    if tgt is None:
        tgt = pos + np.array([0.0, 0.3, 1.0])
    d = tgt - pos
    return d / np.linalg.norm(d)


def draw_sky(t, mode='open', fade_beams=0.0, dissolve=0.0, freeze=None, show_missiles=True):
    """returns (canvas, emis, cam). mode 'open' = cold open; 'end' = ending replay.
    dissolve 0..1: stations -> wireframe -> gone. fade_beams 0..1: beams/explosions out."""
    tt = t if freeze is None else freeze
    cam = cam_at(tt)
    canvas = new_canvas(hexc('020308'))
    emis = np.zeros_like(canvas)
    E.render_stars(canvas, cam, amount=1.4)
    E.render_earth(canvas, emis, cam, sun=SUN, atm_amt=1.3, light_amt=1.0)
    beams_on = 1.0 - fade_beams
    # ---- missiles
    if show_missiles:
        for i, m in enumerate(MISSILES):
            if tt < m.t0:
                continue
            alive_until = m.kill if m.kill is not None else 1e9
            tcur = min(tt, alive_until)
            tr = m.trail(tcur)
            sx, sy, z = cam.project(tr)
            pts = list(zip(sx, sy))
            fade = 1.0 if tt < alive_until else math.exp(-(tt - alive_until) / 0.5)
            fade *= (1 - fade_beams * 0.7)
            fx.plume(emis, pts, color=(1.0, 0.55, 0.22), head=1.0 if tt < alive_until else 0.0, width=1.6, fade=fade)
            # heating before kill
            if m.kill is not None and m.kill - 0.35 < tt < m.kill:
                hx, hy = pts[-1]
                k = (tt - (m.kill - 0.35)) / 0.35
                splat(emis, hx, hy, 5 + 6 * k, (1.0, 0.15, 0.08), 1.8 * k * beams_on)
            if m.kill is not None and tt >= m.kill:
                hx, hy, _ = cam.project1(m.pos(m.kill))
                BURSTS[i].draw(emis, hx, hy, tt - m.kill, scale=0.32 + 0.12 * ((i * 7) % 5) / 4, power=beams_on * 0.85)
    # ---- stations
    order = sorted(range(len(STATIONS)), key=lambda i: -np.linalg.norm(STATIONS[i][0] - cam.pos))
    for si in order:
        pos, sc = STATIONS[si]
        open_amt = smooth(remap(tt, 1.0 + si * 0.4, 4.5 + si * 0.4)) if mode == 'open' else 1.0
        mesh = station_mesh_cached(open_amt, station_charge(si, tt) * (1 - fade_beams))
        d = aim_dir(si, tt)
        R = M3.look_rot(d, up=pos / np.linalg.norm(pos))
        key = cam.r * 0.55 + cam.u * 0.6 - cam.f * 0.55
        if dissolve < 0.999:
            alpha = 1.0 - smooth(remap(dissolve, 0.55, 1.0))
            wire = smooth(remap(dissolve, 0.0, 0.5))
            if alpha > 0:
                M3.render_mesh(canvas, emis, mesh, cam, M=R, t=pos, scale=sc, light=key,
                               ambient=0.16, rim_col=(0.55, 0.6, 1.0), alpha=alpha * (1 - wire * 0.6),
                               wire=0.0, emis_mul=0.35)
                if wire > 0:
                    M3.wire_mesh(canvas, mesh, cam, M=R, t=pos, scale=sc, color=(0.45, 0.8, 1.0),
                                 alpha=wire * alpha * 0.7)
        # firing
        for kt, s, mi in KILLS:
            if s != si:
                continue
            on = pulse(tt, kt - 0.45, 0.05, 0.35, 0.12) * beams_on
            if on > 0:
                p0 = pos + R @ np.array([2.2, 0, 0]) * sc
                p1 = MISSILES[mi].pos(min(tt, kt))
                a = cam.project1(p0); b = cam.project1(p1)
                fx.beam(emis, a[:2], b[:2], (0.35, 0.85, 1.0), width=2.2 if si == 0 else 1.6, intensity=on * 1.2)
                splat(emis, a[0], a[1], 9 if si == 0 else 4, (0.6, 0.9, 1.0), 1.6 * on)
    # ---- X-ray laser module and burst
    if mode == 'open' or dissolve < 0.5:
        xs, ys, xz = cam.project1(XRAY_POS)
        if tt < XRAY_T:
            Rx = M3.rot_z(tt * 0.2) @ M3.rot_y(0.3)
            M3.render_mesh(canvas, emis, XMOD, cam, M=Rx, t=XRAY_POS, scale=0.0016, light=SUN + np.array([0, 0, 0.4]),
                           ambient=0.12, alpha=1 - dissolve)
        else:
            tau = tt - XRAY_T
            XBURST.draw(emis, xs, ys, tau, scale=0.7, color=(0.9, 0.95, 1.0), power=1.2 * beams_on)
            fl = math.exp(-tau / 0.5) * beams_on
            for k in range(6):
                a = k * math.pi / 3 + 0.3
                L = 380 * fl + 40
                fx.beam(emis, (xs - math.cos(a) * L, ys - math.sin(a) * L), (xs + math.cos(a) * L, ys + math.sin(a) * L),
                        (0.8, 0.85, 1.0), width=1.0, intensity=0.35 * fl)
            # radial beams to targets + to empty space
            on = math.exp(-max(tau - 0.15, 0) / 0.35) * beams_on
            if on > 0.01:
                for mi in XRAY_TARGETS:
                    b = cam.project1(MISSILES[mi].pos(XRAY_T))
                    fx.beam(emis, (xs, ys), b[:2], (0.75, 0.55, 1.0), width=1.1, intensity=on * 0.9)
                for k, dd in enumerate(XDIRS):
                    p1 = XRAY_POS + dd * 0.5
                    b = cam.project1(p1)
                    if b[2] > 0:
                        fx.beam(emis, (xs, ys), b[:2], (0.75, 0.55, 1.0), width=1.0, intensity=on * 0.55)
    return canvas, emis, cam


def finish(canvas, emis, fi, hypo=1.0, bloom_amt=1.0, grain_amt=0.016, extra_vig=0.0):
    out = canvas + emis + bloom(emis, 0.95 * bloom_amt) + bloom(canvas.clip(0.6, 5) - 0.6, 0.25)
    if hypo > 0:
        out = grade_hypo(out, hypo)
    else:
        out = grade_reality(out)
    out = tonemap(out)
    out = vignette(out, 0.5 + extra_vig)
    out = grain(out, fi, grain_amt)
    return out
