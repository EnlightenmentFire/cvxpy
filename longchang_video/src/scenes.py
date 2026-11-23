"""程序生成的抽象场景：夜山与雾、洞中火光、竹、素底。全部自绘，无外部素材。"""
import cv2
import numpy as np

from gfx import W, H, rgb, value_noise, noise1d, add_glow, flicker, smooth


class Plain:
    """近黑素底，带极淡的中心微光。"""

    def __init__(self, tint=(0.030, 0.036, 0.044), seed=3):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.5) / (H * 0.72)) ** 2)
        g = np.exp(-r * r * 1.6)
        rng = np.random.default_rng(seed)
        n = value_noise(H // 4, W // 4, 90, rng, 3)
        n = cv2.resize(n, (W, H), interpolation=cv2.INTER_CUBIC)
        self.base = rgb('#05070a')[None, None] + np.asarray(tint, np.float32) * (g * (0.75 + 0.5 * n))[..., None]

    def render(self, t):
        return self.base.copy()


class NightRidge:
    """层叠山影 + 谷雾，缓慢横移。可在山脊上点火光（山寨、人家）。"""

    def __init__(self, seed=1, n_layers=5, mood='night', extra=420, top=0.44, bottom=0.90):
        rng = np.random.default_rng(seed)
        self.extra = extra
        WL = W + extra
        self.WL = WL
        if mood == 'dawn':
            sky_top, sky_hor = rgb('#0a0f15'), rgb('#3b4650')
            far, near, fog = rgb('#2b353f'), rgb('#07090c'), rgb('#56626c')
        elif mood == 'ember':
            sky_top, sky_hor = rgb('#06080b'), rgb('#141a20')
            far, near, fog = rgb('#151c23'), rgb('#040507'), rgb('#232c35')
        else:
            sky_top, sky_hor = rgb('#06090d'), rgb('#19222b')
            far, near, fog = rgb('#1a232c'), rgb('#05070a'), rgb('#2c3742')
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
        g = smooth(yy / (top + 0.12)) ** 1.5
        sky = sky_top[None, None] * (1 - g[..., None]) + sky_hor[None, None] * g[..., None]
        sky = np.repeat(sky, W, axis=1).astype(np.float32)
        cl = cv2.resize(value_noise(H // 6, W // 6, 70, rng, 4), (W, H), interpolation=cv2.INTER_CUBIC)
        sky *= (0.86 + 0.28 * cl)[..., None]
        # 很稀的星
        n_star = 110 if mood != 'dawn' else 25
        sx = rng.integers(0, W, n_star)
        sy = (rng.random(n_star) ** 1.6 * H * (top - 0.02)).astype(int)
        sb = rng.random(n_star) ** 3 * 0.30 + 0.035
        stars = np.zeros((H, W), np.float32)
        stars[sy, sx] = sb
        stars = cv2.GaussianBlur(stars, (0, 0), 0.8) * 2.6
        sky += stars[..., None] * np.array([0.9, 0.95, 1.0], np.float32)
        self.sky = sky
        self.layers = []
        self.profiles = []
        xs = np.arange(WL)
        for i in range(n_layers):
            d = i / (n_layers - 1)
            base_y = H * (top + (bottom - top) * d ** 1.15)
            amp = 55 + 150 * d
            cell = 300 + 420 * d
            nz = noise1d(WL, cell, rng, octaves=6, persistence=0.52)
            ridged = 1 - np.abs(2 * noise1d(WL, cell * 0.6, rng, octaves=4) - 1)
            prof = base_y - amp * ((nz - 0.5) * 1.7 + (ridged - 0.5) * 0.5 * (1 - d * 0.5))
            col = far * (1 - d ** 0.75) + near * d ** 0.75
            y0 = int(max(prof.min() - 4, 0))
            self.profiles.append(prof)
            self.layers.append(dict(prof=prof, col=col, y0=y0, par=0.18 + 0.82 * d ** 1.4, d=d))
        # 每层只保留会露出来的行；层内向下渐入雾色
        for i, L in enumerate(self.layers):
            y1 = H if i == n_layers - 1 else int(min(self.layers[i + 1]['prof'].max() + 30, H))
            y0 = L['y0']
            hh = max(y1 - y0, 4)
            yy = (np.arange(y0, y0 + hh, dtype=np.float32))[:, None]
            dist = yy - L['prof'][None, :].astype(np.float32)
            alpha = np.clip(dist + 0.5, 0, 1)
            fogmix = smooth(dist / (150 + 160 * (1 - L['d']))) * (0.62 - 0.40 * L['d'])
            rim = np.exp(-np.clip(dist, 0, None) / 22.0) * 0.22 * (1 - L['d'] * 0.6)
            colr = L['col'][None, None] * (1 + rim[..., None]) * (1 - fogmix[..., None]) + fog[None, None] * fogmix[..., None]
            rgba = np.concatenate([colr * alpha[..., None], alpha[..., None]], -1).astype(np.float32)
            L['rgba'] = rgba
            L['hh'] = hh
        self.fog_col = fog
        fn = value_noise(160, 640 + 160, 60, rng, 4)
        u = smooth(np.linspace(0, 1, 160, dtype=np.float32))[None, :]
        fn[:, :160] = fn[:, 640:800] * (1 - u) + fn[:, :160] * u   # 首尾交叠，横向无缝
        fn = fn[:, :640]
        self.fog_tex = np.concatenate([fn, fn, fn[:, :2]], axis=1)  # 横向可循环滚动
        band = np.zeros((H, 1), np.float32)
        ys = np.arange(H, dtype=np.float32) / H
        band[:, 0] = np.exp(-((ys - (top + 0.20)) / 0.16) ** 2) * 0.9 + np.exp(-((ys - (top + 0.02)) / 0.07) ** 2) * 0.5
        self.fog_band = band
        self.n = n_layers

    def ridge_xy(self, layer, xw, cam_x=0.0):
        """世界坐标 xw（0..WL）在某层山脊上的屏幕位置。"""
        L = self.layers[layer]
        sx = xw - (self.extra / 2 + cam_x * L['par'])
        return sx, float(L['prof'][int(np.clip(xw, 0, self.WL - 1))])

    def render(self, t, cam_x=0.0, fog_amt=1.0, embers=(), ember_layer_hook=None):
        """cam_x: 横移像素（±extra/2 以内）。embers: [(layer, xw, dy, radius, intensity, seed)]"""
        img = self.sky.copy()
        by_layer = {}
        for e in embers:
            by_layer.setdefault(e[0], []).append(e)
        for i, L in enumerate(self.layers):
            shift = self.extra / 2 + cam_x * L['par']
            M = np.array([[1, 0, -shift], [0, 1, 0]], np.float32)
            strip = cv2.warpAffine(L['rgba'], M, (W, L['hh']), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            y0 = L['y0']
            reg = img[y0:y0 + L['hh']]
            reg *= (1 - strip[..., 3:4])
            reg += strip[..., :3]
            for (_, xw, dy, radius, inten, seed) in by_layer.get(i, ()):
                sx, ry = self.ridge_xy(i, xw, cam_x)
                f = flicker(t, seed)
                add_glow(img, sx, ry + dy, radius * 5.0, (1.0, 0.50, 0.18), 0.10 * inten * f)
                add_glow(img, sx, ry + dy, radius * 1.6, (1.0, 0.62, 0.28), 0.42 * inten * f)
                add_glow(img, sx, ry + dy, max(radius * 0.5, 0.9), (1.0, 0.88, 0.62), 0.9 * inten * f)
        if fog_amt > 0:
            off = (t * 5.0) % 640
            x0 = int(off)
            fr = off - x0
            f = self.fog_tex[:, x0:x0 + 640] * (1 - fr) + self.fog_tex[:, x0 + 1:x0 + 641] * fr
            f = cv2.resize(f, (W, H), interpolation=cv2.INTER_CUBIC)
            img += (self.fog_col * 0.42)[None, None] * (f * self.fog_band * fog_amt)[..., None]
        return img


class Cave:
    """洞中：画外一堆火，把岩壁照出一点起伏。只有暗、暖光和几粒火星。"""

    def __init__(self, seed=7, fire=(0.66, 1.06)):
        rng = np.random.default_rng(seed)
        h, w = H // 2, W // 2
        hf = value_noise(h, w, 150, rng, 6, 0.56)
        rid = 1 - np.abs(2 * value_noise(h, w, 90, rng, 5, 0.5) - 1)
        hf = cv2.GaussianBlur(hf * 0.72 + rid * 0.28, (0, 0), 1.0)
        gx = cv2.Sobel(hf, cv2.CV_32F, 1, 0, ksize=3) * 7.0
        gy = cv2.Sobel(hf, cv2.CV_32F, 0, 1, ksize=3) * 7.0
        nz = 1.0 / np.sqrt(gx * gx + gy * gy + 1)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        self.lit = []
        for (lx, ly) in ((0.45, 0.62), (0.30, 0.70), (0.58, 0.52)):     # 光从右下方来，方向固定
            lz = float(np.sqrt(max(1 - lx * lx - ly * ly, 0.05)))
            lam = np.clip((-gx * lx - gy * ly + lz) * nz, 0, 1)
            self.lit.append((0.25 + 0.75 * lam ** 1.4).astype(np.float32))
        fx, fy = fire[0] * w, fire[1] * h
        dist = np.sqrt(((xx - fx) / 1.25) ** 2 + (yy - fy) ** 2)
        self.fall = (1.0 / (1.0 + (dist / (h * 0.42)) ** 2.6)).astype(np.float32)
        self.fall2 = (1.0 / (1.0 + (dist / (h * 0.55)) ** 2.6)).astype(np.float32)
        self.amb = (hf * 0.010 + 0.004).astype(np.float32)
        self.fire = (fire[0] * W, fire[1] * H)

    def render(self, t, level=1.0, cool=0.0):
        """level: 火光强度 0..1。cool: 0..1，冷白的光从中心漫开（"悟"）。"""
        a = 0.5 + 0.5 * np.sin(t * 3.1)
        b = 0.5 + 0.5 * np.sin(t * 5.3 + 1.0)
        lit = self.lit[0] * (1 - 0.45 * a - 0.30 * b) + self.lit[1] * 0.45 * a + self.lit[2] * 0.30 * b
        breathe = 0.5 + 0.5 * np.sin(t * 1.7 + 0.6)
        fall = self.fall * (1 - 0.35 * breathe) + self.fall2 * 0.35 * breathe
        f = flicker(t, 0.4) * level
        warm = np.array([1.0, 0.47, 0.17], np.float32)
        img = (lit * fall)[..., None] * warm * (0.80 * f) + self.amb[..., None] * np.array([0.8, 0.9, 1.1], np.float32)
        img = cv2.resize(img, (W, H), interpolation=cv2.INTER_CUBIC)
        fx, fy = self.fire
        add_glow(img, fx, H + 40, 300, (1.0, 0.40, 0.12), 0.16 * f)
        for k in range(8):                                   # 火星
            ph = (t * (0.10 + 0.012 * k) + k * 0.37) % 1.0
            sx = fx + 80 * np.sin(k * 2.4 + t * 0.6 + ph * 3.0) + (k - 4) * 22
            sy = H - 10 - ph * 520
            add_glow(img, sx, sy, 1.6, (1.0, 0.70, 0.36), 0.8 * (1 - ph) ** 1.8 * level * (0.55 + 0.45 * np.sin(k + t * 8)))
        if cool > 0:
            yy, xx = np.mgrid[0:H:4, 0:W:4].astype(np.float32)
            r = np.sqrt(((xx - W / 2) / (W * 0.50)) ** 2 + ((yy - H * 0.47) / (H * 0.62)) ** 2)
            g = cv2.resize(np.exp(-r * r * 1.5), (W, H), interpolation=cv2.INTER_CUBIC)
            img += g[..., None] * np.array([0.21, 0.235, 0.26], np.float32) * cool
        return img


class Bamboo:
    """几竿竹：竿、节，和几簇虚掉的叶，浸在雾里。水墨的浓淡，不求写实。"""

    def __init__(self, seed=11):
        rng = np.random.default_rng(seed)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        bg = np.zeros((H, W, 3), np.float32) + rgb('#080c0c')
        glow = np.exp(-(((xx - W * 0.52) / (W * 0.55)) ** 2 + ((yy - H * 0.42) / (H * 0.70)) ** 2) * 1.4)
        n = cv2.resize(value_noise(H // 6, W // 6, 60, rng, 4), (W, H), interpolation=cv2.INTER_CUBIC)
        bg += rgb('#27322f')[None, None] * (glow * (0.70 + 0.55 * n))[..., None]
        self.bg = bg
        PADX = 120
        specs = [  # x, 宽, 深度(0 远 1 近), 倾斜
            (0.085, 22, 0.12, 0.012), (0.175, 54, 0.62, -0.008), (0.262, 15, 0.05, 0.006),
            (0.335, 30, 0.34, -0.004), (0.690, 18, 0.10, -0.010), (0.775, 84, 0.95, 0.009),
            (0.872, 38, 0.45, -0.006), (0.945, 16, 0.07, 0.011), (0.015, 66, 0.80, 0.004),
        ]
        self.layers = []
        for depth_lo, depth_hi, blur in ((0.0, 0.2, 4.5), (0.2, 0.7, 1.6), (0.7, 1.01, 0.6)):
            lay = np.zeros((H, W + 2 * PADX, 4), np.float32)
            for (fx, wd, d, lean) in specs:
                if not (depth_lo <= d < depth_hi):
                    continue
                body = rgb('#3b4a44') * (1 - d) + rgb('#0b100e') * d        # 远淡近浓
                hl = rgb('#5d6f66') * (1 - d) + rgb('#33423b') * d
                x_c = fx * W + PADX
                y = -int(rng.integers(0, 200))
                while y < H:
                    seg = int(rng.integers(170, 250) * (0.8 + 0.5 * d))
                    y2 = min(y + seg, H)
                    for yy_ in range(max(y, 0), y2):
                        v = (yy_ - y) / max(seg, 1)
                        bulge = 1.0 + 0.10 * (np.exp(-v / 0.04) + np.exp(-(1 - v) / 0.04))   # 近节处略粗
                        xc = x_c + lean * (yy_ - H / 2) * 40 / 40 + 1.5 * np.sin(yy_ / 300.0 + fx * 9)
                        hw = wd / 2 * bulge
                        x0, x1 = int(xc - hw) - 1, int(xc + hw) + 2
                        u = (np.arange(x0, x1) - xc) / hw
                        shade = np.clip(1 - u * u, 0, 1) ** 0.5
                        band = np.exp(-((u + 0.38) / 0.30) ** 2)
                        c = body[None] * (0.50 + 0.50 * shade[:, None]) + (hl - body)[None] * band[:, None] * 0.75
                        a = np.clip((1 - np.abs(u)) * hw, 0, 1)
                        lay[yy_, x0:x1, :3] = c * a[:, None]
                        lay[yy_, x0:x1, 3] = a
                    if 0 < y2 < H - 6:                       # 竹节：留一线空白，上下收一道深边
                        xc = x_c + lean * (y2 - H / 2)
                        x0, x1 = int(xc - wd / 2 - 4), int(xc + wd / 2 + 5)
                        g = max(2, int(wd * 0.07))
                        lay[y2:y2 + g, x0:x1] *= 0.12
                        lay[y2 - 3:y2, x0:x1, :3] *= 0.55
                        lay[y2 + g:y2 + g + 3, x0:x1, :3] *= 0.55
                    y = y2 + max(2, int(wd * 0.07))
            if blur:
                lay = cv2.GaussianBlur(lay, (0, 0), blur)
            self.layers.append((lay, 0.4 + 1.3 * depth_hi))
        # 叶：几簇柳叶形的墨点，放在上方两角，虚掉
        leaf = np.zeros((H, W + 2 * PADX), np.float32)
        for (cx, cy, nleaf, scale) in ((0.20, 0.10, 9, 1.0), (0.80, 0.06, 11, 1.25), (0.36, 0.02, 6, 0.8),
                                       (0.93, 0.24, 6, 0.9), (0.05, 0.30, 5, 0.85)):
            for _ in range(nleaf):
                ang = np.radians(rng.uniform(25, 80)) * rng.choice([-1, 1]) + np.pi / 2
                L = rng.uniform(90, 170) * scale
                wdt = L * rng.uniform(0.085, 0.12)
                ox = cx * W + PADX + rng.uniform(-90, 90) * scale
                oy = cy * H + rng.uniform(-50, 70) * scale
                ts = np.linspace(0, 1, 14)
                wprof = wdt * np.sin(np.pi * ts ** 0.75) * (1 - ts * 0.25)
                ax, ay = np.cos(ang), np.sin(ang)
                left = [(ox + ax * L * u - ay * w_, oy + ay * L * u + ax * w_) for u, w_ in zip(ts, wprof)]
                right = [(ox + ax * L * u + ay * w_, oy + ay * L * u - ax * w_) for u, w_ in zip(ts[::-1], wprof[::-1])]
                poly = np.round(np.array(left + right) * 16).astype(np.int32)
                tmp = np.zeros_like(leaf, dtype=np.uint8)
                cv2.fillPoly(tmp, [poly], 255, cv2.LINE_AA, shift=4)
                leaf = np.maximum(leaf, tmp.astype(np.float32) / 255.0 * rng.uniform(0.55, 0.9))
        leaf = cv2.GaussianBlur(leaf, (0, 0), 3.2)
        self.leaf = leaf
        self.leaf_col = rgb('#0d1311')
        self.PADX = PADX
        self.mist = cv2.resize(value_noise(H // 8, W // 4, 50, rng, 4), (W * 2, H), interpolation=cv2.INTER_CUBIC)

    def render(self, t, light=1.0, blur=0.0):
        img = self.bg * light
        for lay, par in self.layers:
            sway = self.PADX + par * 5.0 * np.sin(t * 0.23 + par) - 30 + t * par * 1.1
            M = np.array([[1, 0, -sway], [0, 1, 0]], np.float32)
            s = cv2.warpAffine(lay, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
            img = img * (1 - s[..., 3:4]) + s[..., :3] * light
        sway = self.PADX + 9.0 * np.sin(t * 0.31) - 30 + t * 2.0
        M = np.array([[1, 0, -sway], [0, 1, 3.0 * np.sin(t * 0.4)]], np.float32)
        lf = cv2.warpAffine(self.leaf, M, (W, H), flags=cv2.INTER_LINEAR)[..., None]
        img = img * (1 - lf) + self.leaf_col * lf * light
        off = int(t * 9) % W
        m = self.mist[:, off:off + W]
        img += rgb('#1f2a28')[None, None] * (m * 0.36 * light)[..., None]
        if blur > 0.3:
            img = cv2.GaussianBlur(img, (0, 0), blur)
        return img


if __name__ == '__main__':
    import os
    import sys
    from PIL import Image
    out = sys.argv[1] + '/out/scenetest'
    os.makedirs(out, exist_ok=True)

    def save(name, img):
        Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(f'{out}/{name}.png')
        print(name, float(img.mean()), float(img.max()))

    r = NightRidge(seed=1)
    save('ridge_night', r.render(3.0, cam_x=0, embers=[(1, 1300, -6, 2.0, 1.0, 0.3)]))
    r2 = NightRidge(seed=5, mood='ember')
    em = [(1, 500 + 190 * k, -5, 1.6, 0.9, k * 1.7) for k in range(8)] + [(2, 420 + 260 * k, -6, 2.0, 1.0, k) for k in range(7)]
    save('ridge_ember', r2.render(2.0, cam_x=40, embers=em))
    r3 = NightRidge(seed=9, mood='dawn')
    save('ridge_dawn', r3.render(2.0, cam_x=-30))
    c = Cave()
    save('cave', c.render(1.3))
    save('cave_cool', c.render(1.3, level=0.15, cool=1.0))
    b = Bamboo()
    save('bamboo', b.render(2.0))
    save('plain', Plain().render(0))
