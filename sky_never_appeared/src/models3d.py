"""Tiny flat-shaded polygon renderer (painter's algorithm) + procedural models.

Models are lists of faces; each face = (vertex array (k,3), base colour, emissive flag).
Rendering is done at 2x into a local box and downsampled for anti-aliasing.
"""
import math
import numpy as np
import cv2
from common import hexc


# ------------------------------------------------------------------ math
def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

def look_rot(direction, up=(0, 0, 1)):
    """rotation matrix whose local +x axis points along direction."""
    x = np.asarray(direction, float); x = x / np.linalg.norm(x)
    up = np.asarray(up, float)
    if abs(np.dot(x, up)) > 0.98:
        up = np.array([0, 1, 0.0]) if abs(x[1]) < 0.9 else np.array([1, 0, 0.0])
    y = np.cross(up, x); y /= np.linalg.norm(y)
    z = np.cross(x, y)
    return np.stack([x, y, z], 1)


class Mesh:
    def __init__(self):
        self.faces = []   # (verts (k,3), color(3), kind) kind: 0 lit, 1 emissive, 2 lit+wire

    def add(self, verts, color, kind=0):
        self.faces.append((np.asarray(verts, np.float64), np.asarray(color, np.float32), kind))
        return self

    def extend(self, other, M=np.eye(3), t=(0, 0, 0)):
        t = np.asarray(t, float)
        for v, c, k in other.faces:
            self.faces.append((v @ M.T + t, c, k))
        return self


# ------------------------------------------------------------------ primitives
def box(sx, sy, sz, color, center=(0, 0, 0), kind=0):
    cx, cy, cz = center
    x, y, z = sx / 2, sy / 2, sz / 2
    V = np.array([[-x, -y, -z], [x, -y, -z], [x, y, -z], [-x, y, -z],
                  [-x, -y, z], [x, -y, z], [x, y, z], [-x, y, z]]) + [cx, cy, cz]
    F = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3)]
    m = Mesh()
    for f in F:
        m.add(V[list(f)], color, kind)
    return m

def cylinder(r, length, color, n=18, caps=True, axis='x', r2=None, kind=0, cap_color=None):
    """cylinder (or frustum if r2) along +axis from 0 to length."""
    r2 = r if r2 is None else r2
    m = Mesh()
    ang = np.linspace(0, 2 * math.pi, n, endpoint=False)
    c0 = np.stack([np.zeros(n), r * np.cos(ang), r * np.sin(ang)], 1)
    c1 = np.stack([np.full(n, length), r2 * np.cos(ang), r2 * np.sin(ang)], 1)
    for i in range(n):
        j = (i + 1) % n
        m.add([c0[i], c1[i], c1[j], c0[j]], color, kind)
    if caps:
        cc = color if cap_color is None else cap_color
        m.add(c0[::-1], cc, kind)
        if r2 > 1e-6:
            m.add(c1, cc, kind)
    if axis != 'x':
        R = {'y': rot_z(math.pi / 2), 'z': rot_y(-math.pi / 2)}[axis]
        m.faces = [(v @ R.T, c, k) for v, c, k in m.faces]
    return m

def cone(r, length, color, n=18, kind=0):
    return cylinder(r, length, color, n=n, r2=0.0, kind=kind)

def disk(r, color, n=28, kind=0, axis='x', segments=1):
    m = Mesh()
    ang = np.linspace(0, 2 * math.pi, n, endpoint=False)
    if segments == 1:
        ring = np.stack([np.zeros(n), r * np.cos(ang), r * np.sin(ang)], 1)
        m.add(ring, color, kind)
        m.add(ring[::-1], color, kind)
    else:
        for s in range(segments):
            r0, r1 = r * s / segments, r * (s + 1) / segments
            for i in range(n):
                j = (i + 1) % n
                p = [[0, r0 * math.cos(ang[i]), r0 * math.sin(ang[i])], [0, r1 * math.cos(ang[i]), r1 * math.sin(ang[i])],
                     [0, r1 * math.cos(ang[j]), r1 * math.sin(ang[j])], [0, r0 * math.cos(ang[j]), r0 * math.sin(ang[j])]]
                m.add(p, color, kind)
                m.add(p[::-1], color, kind)
    if axis != 'x':
        R = {'y': rot_z(math.pi / 2), 'z': rot_y(-math.pi / 2)}[axis]
        m.faces = [(v @ R.T, c, k) for v, c, k in m.faces]
    return m

def panel(w, h, color, nx=4, ny=2, frame_color=None, kind=0):
    """flat two-sided panel in the y-z plane centred at origin, subdivided into cells."""
    m = Mesh()
    gap = 0.04 * min(w / nx, h / ny)
    for i in range(nx):
        for j in range(ny):
            y0 = -w / 2 + i * w / nx + gap; y1 = -w / 2 + (i + 1) * w / nx - gap
            z0 = -h / 2 + j * h / ny + gap; z1 = -h / 2 + (j + 1) * h / ny - gap
            q = [[0, y0, z0], [0, y1, z0], [0, y1, z1], [0, y0, z1]]
            m.add(q, color, kind)
            m.add(q[::-1], color * 0.6, kind)
    return m


# ------------------------------------------------------------------ models
STEEL = hexc('c9d0d8')
WHITE = hexc('e4e7ea')
DARK = hexc('3a4350')
GOLD = hexc('d4a640')
PANEL = hexc('1d3566')
MIRROR = hexc('9fc4ff')

def battle_station(mirror_open=1.0, panels_open=1.0, charge=0.0):
    """space-based laser battle station (after 1980s official concept art, simplified):
    long body, gold-foil sections, a large beam-director mirror at the front, solar wings.
    local frame: +x = firing direction (mirror normal)."""
    m = Mesh()
    m.extend(cylinder(0.55, 3.0, WHITE, n=18, cap_color=DARK), t=(-2.6, 0, 0))
    m.extend(cylinder(0.6, 0.7, GOLD, n=18), t=(-1.9, 0, 0))
    m.extend(cylinder(0.75, 0.6, DARK, n=18), t=(-0.6, 0, 0))
    m.extend(cylinder(0.45, 0.9, GOLD, n=16, cap_color=DARK), t=(-3.5, 0, 0))
    # radiator fins
    for k in range(4):
        R = rot_x(k * math.pi / 2 + math.pi / 4)
        m.extend(box(1.4, 0.04, 0.8, hexc('6b7482'), center=(-2.9, 0, 0.9)), M=R)
    # beam director: a large dish at the front, on a short neck
    m.extend(cylinder(0.3, 0.5, DARK, n=12), t=(0.0, 0, 0))
    rr = 1.6 * (0.35 + 0.65 * mirror_open)
    m.extend(cylinder(rr * 1.05, 0.16, STEEL, n=36, caps=False), t=(0.5, 0, 0))
    back = disk(rr * 1.05, hexc('8d96a3'), n=36)
    m.faces += [(v + [0.5, 0, 0], c, k) for v, c, k in back.faces[1:]]
    mir_col = MIRROR * (0.6 + 0.4 * charge) + np.array([0.3, 0.5, 0.6], np.float32) * charge
    face = disk(rr, mir_col, n=36, segments=3, kind=1)
    m.faces += [(v + [0.66, 0, 0], c * (0.55 + 0.45 * (i // 72) / 2), k) for i, (v, c, k) in enumerate(face.faces) if i % 2 == 0]
    # tripod struts holding a secondary mirror
    for k in range(3):
        a = k * 2 * math.pi / 3 + math.pi / 2
        p0 = np.array([0.7, rr * 0.95 * math.cos(a), rr * 0.95 * math.sin(a)])
        p1 = np.array([2.0, 0.14 * math.cos(a), 0.14 * math.sin(a)])
        d = p1 - p0
        strut = cylinder(0.04, np.linalg.norm(d), STEEL, n=5)
        m.extend(strut, M=look_rot(d), t=p0)
    m.extend(cylinder(0.24, 0.14, STEEL, n=14, cap_color=MIRROR), t=(1.95, 0, 0))
    # solar wings (fold out)
    for side in (-1, 1):
        ang = (1 - panels_open) * math.pi / 2 * 0.98
        wing = Mesh()
        wing.extend(cylinder(0.05, 1.0, STEEL, n=5, axis='y'))
        span = 3.6 * (0.12 + 0.88 * panels_open)
        wing.extend(panel(span, 1.4, PANEL, nx=8, ny=2), t=(0, 1.0 + span / 2, 0))
        Rf = rot_x(ang * side)
        if side < 0:
            Rf = Rf @ rot_z(math.pi)
        m.extend(wing, M=Rf, t=(-2.4, 0, 0))
    return m

def warhead(color=hexc('7a7f88')):
    """re-entry vehicle: cone along +x."""
    m = Mesh()
    m.extend(cylinder(0.3, 1.25, color, n=14, r2=0.07, cap_color=hexc('2c2f35')))
    return m

def interceptor_umbrella(open_amt=1.0):
    """HOE-style kill vehicle with an unfurled rib 'umbrella' (approx 4 m wide).
    +x = flight direction."""
    m = Mesh()
    m.extend(cylinder(0.25, 1.4, STEEL, n=12, cap_color=DARK), t=(-1.2, 0, 0))
    m.extend(cone(0.25, 0.45, hexc('c8ccd2'), n=12), t=(0.2, 0, 0))
    n = 18
    R = 2.0 * (0.1 + 0.9 * open_amt)
    for k in range(n):
        a = 2 * math.pi * k / n
        tip = np.array([-0.4 - 0.5 * (1 - open_amt), R * math.cos(a), R * math.sin(a)])
        base = np.array([-0.5, 0.2 * math.cos(a), 0.2 * math.sin(a)])
        d = tip - base
        rib = cylinder(0.03, np.linalg.norm(d), hexc('b9c0c8'), n=4)
        m.extend(rib, M=look_rot(d), t=base)
        m.extend(box(0.14, 0.14, 0.14, hexc('d0d4da'), center=(0, 0, 0)), t=tip)
    return m

def xray_module(rods=1.0, n_rods=24, seed=2):
    """'battle station' of the nuclear-pumped X-ray laser concept: a canister with many
    rods pointing in different directions (schematic, not an engineering design)."""
    rng = np.random.default_rng(seed)
    m = Mesh()
    m.extend(cylinder(0.55, 1.6, hexc('6f7680'), n=16, cap_color=DARK), t=(-0.8, 0, 0))
    dirs = rng.normal(0, 1, (n_rods, 3))
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    for d in dirs:
        rod = cylinder(0.035, 2.6 * rods, hexc('c9ced6'), n=5)
        m.extend(rod, M=look_rot(d), t=d * 0.5)
    return m, dirs

def satellite_simple(color=hexc('8c96a3')):
    m = Mesh()
    m.extend(box(0.8, 0.8, 0.8, color))
    m.extend(panel(2.6, 0.7, PANEL, nx=4, ny=1), M=rot_z(math.pi / 2), t=(0, 0, 0))
    return m

def energia_stack():
    """Energia core + 4 strap-on boosters + Polyus on the side (silhouette-level detail).
    +x = up (nose)."""
    m = Mesh()
    core = cylinder(0.39, 5.9, hexc('cdbb98'), n=18, cap_color=DARK)
    m.extend(core)
    m.extend(cone(0.39, 0.55, hexc('cdbb98'), n=18), t=(5.9, 0, 0))
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        off = np.array([0, 0.75 * math.cos(a), 0.75 * math.sin(a)])
        b = cylinder(0.2, 3.9, hexc('d9d4c8'), n=12, cap_color=DARK)
        m.extend(b, t=off + [0.0, 0, 0])
        m.extend(cone(0.2, 0.45, hexc('d9d4c8'), n=12), t=off + [3.9, 0, 0])
    # payload (Polyus) on the side, black
    m.extend(cylinder(0.41, 3.7, hexc('15171b'), n=16, cap_color=hexc('15171b')), t=(1.4, 0, -0.85))
    m.extend(cone(0.41, 0.5, hexc('15171b'), n=16), t=(5.1, 0, -0.85))
    return m

def polyus():
    """Polyus: long black cylinder; engine end marked with a nozzle. +x = engine end."""
    m = Mesh()
    m.extend(cylinder(0.41, 3.7, hexc('17191d'), n=18, cap_color=hexc('22262c')), t=(-1.85, 0, 0))
    m.extend(cone(0.41, 0.55, hexc('17191d'), n=18), M=rot_z(math.pi), t=(-1.85, 0, 0))
    m.extend(cylinder(0.12, 0.25, hexc('4a4f57'), n=10, r2=0.2), t=(1.85, 0, 0.0))
    m.extend(box(1.2, 0.02, 0.5, hexc('2a2f36'), center=(0.9, 0.42, 0)))
    return m


# ------------------------------------------------------------------ renderer
def render_mesh(canvas, emis, mesh, cam, M=np.eye(3), t=(0, 0, 0), scale=1.0,
                light=(0.5, -0.6, 0.6), ambient=0.12, rim_col=(0.35, 0.5, 0.8), alpha=1.0,
                wire=0.0, wire_col=(0.5, 0.8, 1.0), tint=None, emis_mul=1.0, ss=2):
    """Draw mesh into canvas (float RGB) using a 2x supersampled local box.
    wire: 0..1 blend toward wireframe look (for the 'dissolve' ending)."""
    light = np.asarray(light, float); light /= np.linalg.norm(light)
    t = np.asarray(t, float)
    polys = []
    camp = cam.pos
    for v, col, kind in mesh.faces:
        wv = (v * scale) @ M.T + t
        n = np.cross(wv[1] - wv[0], wv[2] - wv[0])
        nn = np.linalg.norm(n)
        if nn < 1e-12:
            continue
        n /= nn
        cen = wv.mean(0)
        view = camp - cen
        dist = np.linalg.norm(view)
        if np.dot(n, view) <= 0:
            continue  # back face
        sx, sy, z = cam.project(wv)
        if (z <= 1e-4).any():
            continue
        polys.append((dist, np.stack([sx, sy], 1), n, col, kind, view / dist))
    if not polys:
        return None
    allp = np.concatenate([p[1] for p in polys])
    x0, y0 = np.floor(allp.min(0)).astype(int) - 3
    x1, y1 = np.ceil(allp.max(0)).astype(int) + 3
    Hh, Ww = canvas.shape[:2]
    x0, y0 = max(x0, 0), max(y0, 0)
    x1, y1 = min(x1, Ww), min(y1, Hh)
    if x1 <= x0 or y1 <= y0:
        return None
    bw, bh = (x1 - x0) * ss, (y1 - y0) * ss
    if bw * bh > 4200 * 4200:
        ss = 1
        bw, bh = (x1 - x0), (y1 - y0)
    col_buf = np.zeros((bh, bw, 3), np.float32)
    a_buf = np.zeros((bh, bw), np.float32)
    e_buf = np.zeros((bh, bw, 3), np.float32)
    polys.sort(key=lambda p: -p[0])
    rim_col = np.asarray(rim_col, np.float32)
    for dist, pts, n, col, kind, vdir in polys:
        P = np.round((pts - [x0, y0]) * ss * 4).astype(np.int32)
        if kind == 1:
            c = col
        else:
            diff = max(0.0, float(np.dot(n, light)))
            rim = (1 - abs(float(np.dot(n, vdir)))) ** 2
            spec = max(0.0, float(np.dot(vdir, 2 * np.dot(n, light) * n - light))) ** 24
            c = col * (ambient + 0.95 * diff) + rim_col * rim * 0.35 + spec * 0.6
            if tint is not None:
                c = c * np.asarray(tint, np.float32)
        cc = tuple(float(x) for x in c)
        cv2.fillPoly(col_buf, [P], cc, cv2.LINE_8, shift=2)
        cv2.fillPoly(a_buf, [P], 1.0, cv2.LINE_8, shift=2)
        if kind == 1:
            cv2.fillPoly(e_buf, [P], tuple(float(x) * emis_mul for x in col), cv2.LINE_8, shift=2)
        if wire > 0:
            cv2.polylines(col_buf, [P], True, tuple(float(x) for x in wire_col), max(1, ss), cv2.LINE_8, shift=2)
    if ss > 1:
        col_buf = cv2.resize(col_buf, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
        a_buf = cv2.resize(a_buf, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
        e_buf = cv2.resize(e_buf, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    a = a_buf[..., None] * alpha
    reg = canvas[y0:y1, x0:x1]
    if wire > 0:
        # fade solid fill, keep edges
        a = a * (1 - wire * 0.85)
    reg *= (1 - a)
    reg += col_buf * alpha
    if emis is not None:
        emis[y0:y1, x0:x1] += e_buf * alpha
    return (x0, y0, x1, y1)


def wire_mesh(canvas, mesh, cam, M=np.eye(3), t=(0, 0, 0), scale=1.0, color=(0.5, 0.85, 1.0), alpha=1.0, width=1):
    """pure wireframe (all edges, no culling) on float canvas."""
    t = np.asarray(t, float)
    m = np.zeros(canvas.shape[:2], np.uint8)
    polys = []
    for v, col, kind in mesh.faces:
        wv = (v * scale) @ M.T + t
        sx, sy, z = cam.project(wv)
        if (z <= 1e-4).any():
            continue
        polys.append(np.round(np.stack([sx, sy], 1) * 16).astype(np.int32))
    if polys:
        cv2.polylines(m, polys, True, 255, width, cv2.LINE_AA, shift=4)
        a = m.astype(np.float32)[..., None] / 255.0 * alpha
        canvas *= (1 - a * 0.3)
        canvas += a * np.asarray(color, np.float32)
