"""《龙场不是书斋顿悟》成片渲染。

用法:
  python film.py still <work> <timeline.json> <out_dir> t1 t2 ...     # 抽帧看效果
  python film.py render <work> <timeline.json> <out.mp4> [t0 t1]      # 渲染一段（无声），供并行
"""
import json
import os
import subprocess
import sys

import cv2
import numpy as np

import gfx
from gfx import (W, H, FPS, rgb, PAPER, BRIGHT, GREY, DIM, EMBER, COOL, FACT, text_sprite, blit, blit_blur,
                 add_glow, smooth, ease, ramp, window, flicker)
import maps
from maps import Camera, PLACES, NINE_POSTS
from scenes import Plain, NightRidge, Cave, Bamboo
import storyboard as sb

KIND = {'fact': ('史实', FACT), 'theory': ('理论', COOL), 'view': ('解读', EMBER)}
T3 = lambda c: tuple(float(x) for x in c)
WARM = (1.0, 0.66, 0.34)
PALE = (0.93, 0.88, 0.76)


class Film:
    def __init__(self, work, tl):
        self.work = work
        self.tl = tl
        self.B = tl['beats']
        self.total = tl['total']
        self._scenes = {}
        self._md = None
        self._build_schedule()
        self._build_cameras()
        self._build_tags()
        self.rng = np.random.default_rng(2024)
        self.dither = (np.random.default_rng(7).random((H, W, 1), dtype=np.float32) - 0.5) / 255.0
        self._lights = None

    # ── 时间 ──
    def t0(self, b):
        return self.B[b][0]

    def t1(self, b):
        return self.B[b][1]

    def tn(self, b):
        return self.B[b][2]

    def seg(self, b, i):
        return sb.seg_times(b, self.B[b][0], self.B[b][1])[i]

    # ── 场景调度 ──
    def _build_schedule(self):
        t0 = self.t0
        s = [(0.0, 'open'), (t0('b01'), 'map'), (t0('d03'), 'bamboo'), (t0('e01'), 'dark'), (t0('e02'), 'map'),
             (t0('e04'), 'cave'), (t0('e10'), 'dawn'), (t0('e12'), 'map'), (t0('e15'), 'dawn'), (t0('f01'), 'map'),
             (t0('f02'), 'pai'), (t0('f03'), 'map'), (t0('f04'), 'ember'), (t0('f07'), 'map'), (t0('f08'), 'dawn2'),
             (t0('g01'), 'map'), (t0('g06'), 'last'), (t0('h01'), 'dark2'), (t0('h03'), 'ridge3'),
             (t0('h04'), 'map'), (self.tl['end'][0], 'endcard')]
        # 新场景比那句话早 0.55 秒到位
        self.schedule = [(max(t - 0.55, 0.0), k) for t, k in s]

    def scene(self, key):
        if key not in self._scenes:
            if key == 'open':
                self._scenes[key] = NightRidge(seed=1, mood='night')
            elif key in ('dawn', 'dawn2'):
                self._scenes[key] = self._scenes.get('dawn') or self._scenes.get('dawn2') or NightRidge(seed=9, mood='dawn')
            elif key == 'ember':
                self._scenes[key] = NightRidge(seed=5, mood='ember')
            elif key == 'ridge3':
                self._scenes[key] = NightRidge(seed=23, mood='night')
            elif key == 'cave':
                self._scenes[key] = Cave()
            elif key == 'bamboo':
                self._scenes[key] = Bamboo()
            else:
                self._scenes[key] = self._scenes.get('_plain') or Plain()
                self._scenes['_plain'] = self._scenes[key]
        return self._scenes[key]

    @property
    def md(self):
        if self._md is None:
            self._md = maps.MapData(self.work)
        return self._md

    # ── 地图镜头 ──
    def _build_cameras(self):
        t0, tn = self.t0, self.tn
        WIDE0, WIDE1 = Camera(104.5, 21.5, 38, .50), Camera(105.3, 22.5, 35, .50)
        GZ, GZb = Camera(108.2, 25.4, 23.5, .45), Camera(108.6, 25.5, 23.0, .45)
        SOUTH, SOUTHb = Camera(113.6, 25.5, 26.5, .40), Camera(113.85, 25.45, 25.8, .40)
        LC0, LC, LCb = Camera(109.6, 27.2, 15.0, .44), Camera(106.75, 26.95, 8.4, .40), Camera(106.6, 27.0, 8.0, .40)
        LC2, LC2b = Camera(106.1, 27.05, 7.4, .26), Camera(105.95, 27.08, 7.1, .26)
        NG0, NG, NGb = Camera(114.2, 25.9, 13.5, .42), Camera(114.95, 25.25, 8.6, .38), Camera(115.0, 25.2, 8.3, .38)
        NG2, NG2b = Camera(114.75, 25.15, 7.4, .36), Camera(114.8, 25.12, 7.2, .36)
        NG3, NG3b = Camera(114.7, 25.1, 7.2, .36), Camera(114.74, 25.08, 7.0, .36)
        GX0, GX, GXb = Camera(110.6, 24.6, 14.0, .40), Camera(108.9, 23.75, 9.8, .36), Camera(108.95, 23.72, 9.6, .36)
        NA, NAb = Camera(113.3, 24.75, 9.4, .36), Camera(113.4, 24.78, 9.1, .36)
        END0, END1 = Camera(113.6, 25.9, 25.6, .40), Camera(113.4, 25.8, 27.0, .40)
        C = 'cut'
        self.cams = [
            (t0('b01') - 1.5, WIDE0, C), (t0('b05') + 0.1, WIDE1, 0), (t0('b05') + 3.4, GZ, 0),
            (t0('b06') + 0.1, GZb, 0), (t0('b06') + 3.6, SOUTH, 0), (tn('d02') + 1.0, SOUTHb, 0),
            (t0('e02') - 1.5, LC0, C), (t0('e02') + 0.2, LC0, 0), (t0('e02') + 4.4, LC, 0), (tn('e03') + 1.0, LCb, 0),
            (t0('e12') - 1.5, LC2, C), (tn('e14') + 1.0, LC2b, 0),
            (t0('f01') - 1.5, NG0, C), (t0('f01') + 0.2, NG0, 0), (t0('f01') + 4.2, NG, 0), (tn('f01') + 1.0, NGb, 0),
            (t0('f03') - 1.5, NG2, C), (tn('f03') + 1.0, NG2b, 0),
            (t0('f07') - 1.5, NG3, C), (tn('f07') + 1.0, NG3b, 0),
            (t0('g01') - 1.5, GX0, C), (t0('g01') + 0.2, GX0, 0), (t0('g01') + 3.8, GX, 0), (t0('g05') - 0.2, GXb, 0),
            (t0('g05') + 2.8, NA, 0), (tn('g05') + 1.0, NAb, 0),
            (t0('h04') - 1.5, END0, C), (tn('h08') + 2.0, END1, 0),
        ]

    def cam(self, t):
        ks = self.cams
        if t <= ks[0][0]:
            return ks[0][1]
        for i in range(len(ks) - 1):
            ta, ca, _ = ks[i]
            tb, cb, cut = ks[i + 1]
            if ta <= t < tb:
                if cut == 'cut':
                    return ca
                return Camera.lerp(ca, cb, float(ease((t - ta) / (tb - ta))))
        return ks[-1][1]

    # ── 出处角标 ──
    def _build_tags(self):
        runs = []
        for bid in sb.ORDER:
            b = sb.BOARD[bid]
            tg = b['tag']
            t0, _, tnx = self.B[bid]
            if tg is None:
                continue
            if runs and runs[-1][0] == tg and abs(runs[-1][2] - t0) < 0.05:
                runs[-1][2] = tnx
            else:
                runs.append([tg, t0, tnx])
        self.tag_runs = runs
        secs = []
        for i, (bid, name) in enumerate(sb.SECTIONS):
            ta = self.t0(bid)
            tb = self.t0(sb.SECTIONS[i + 1][0]) if i + 1 < len(sb.SECTIONS) else self.tl['end'][0]
            secs.append((name, ta, tb))
        self.sections = secs

    # ════════════════ 背景 ════════════════
    def bg(self, key, t):
        return getattr(self, 'bg_' + key)(t)

    def bg_open(self, t):
        r = self.scene('open')
        cam_x = -70 + 140 * (t / max(self.t0('b01'), 1))
        e_on = ramp(t, self.t0('a01') + 1.0, self.t0('a01') + 3.5)
        pulse = 1.0 + 0.5 * window(t, self.t0('a03'), self.tn('a03') + 0.5, 0.8, 1.2)
        img = r.render(t, cam_x, embers=[(3, 1905, -7, 2.4, 0.95 * e_on * pulse, 0.3)])
        # 片名与图例出现时把山压暗
        tt0, tt1 = self.tl['title']
        dim = 1 - 0.55 * window(t, tt0 - 0.4, tt1 + 0.2, 1.0, 1.0) - 0.62 * window(t, self.t0('a05') - 0.5, self.tn('a05') + 0.3, 0.8, 0.8)
        return img * max(dim, 0.2)

    def bg_dark(self, t):
        return self.scene('dark').render(t) * 0.9

    def bg_dark2(self, t):
        return self.scene('dark2').render(t)

    def bg_bamboo(self, t):
        b = self.scene('bamboo')
        tl = t - self.t0('d03')
        blur = 7.0 * ramp(t, self.t1('d04') - 0.6, self.t1('d04') + 1.6)
        light = 1.0 - 0.45 * ramp(t, self.t1('d04') - 0.6, self.t1('d04') + 2.0)
        img = b.render(tl, light=light, blur=blur)
        # 七日：七道刻痕，随"到七日"逐一亮起
        ta, tb = self.seg('d04', 1), self.t1('d04')
        for k in range(7):
            a = ramp(t, ta + (tb - ta) * (0.10 + 0.105 * k), ta + (tb - ta) * (0.10 + 0.105 * k) + 0.35)
            a *= 1 - ramp(t, self.tn('d04') - 0.5, self.tn('d04'))
            if a > 0.01:
                x = W / 2 - 3 * 34 + k * 34
                cv2.line(img, (int(x), 846), (int(x), 884), T3(np.array(PALE) * (0.25 + 0.6 * a)), 2, cv2.LINE_AA)
        return img

    def bg_cave(self, t):
        c = self.scene('cave')
        tl = t - self.t0('e04')
        level = 1.0 - 0.90 * ramp(t, self.t0('e08') + 0.3, self.tn('e08') - 0.2)
        cool = ramp(t, self.t0('e09') - 0.3, self.t0('e09') + 3.0)
        level = level * (1 - 0.6 * cool)
        return c.render(tl, level=level, cool=cool * 0.95)

    def _dawn(self, t, tref, cam0, houses, brighten=0.0):
        r = self.scene('dawn')
        return r.render(t - tref, cam0 + (t - tref) * 3.2, embers=houses) * (1.0 + brighten)

    def bg_dawn(self, t):
        if t < self.t0('e12'):
            a = ramp(t, self.seg('e11', 0) + 1.2, self.seg('e11', 0) + 3.2)          # 盖起一间屋
            return self._dawn(t, self.t0('e10'), -90, [(2, 1180, -6, 2.3, 1.0 * a, 1.1)])
        return self._dawn(t, self.t0('e15'), 20, [(2, 1180 + 0, -6, 2.3, 0.9, 1.1), (1, 760, -5, 1.6, 0.7, 2.2)])

    def bg_dawn2(self, t):
        tref = self.t0('f08')
        pts = [(1, 520, -5, 1.5, 0.8, 0.5), (1, 905, -5, 1.4, 0.7, 1.9), (2, 700, -6, 1.9, 0.9, 2.7), (2, 1290, -6, 2.0, 0.95, 3.3),
               (2, 1660, -6, 1.8, 0.8, 4.1), (3, 1050, -7, 2.4, 1.0, 5.2), (1, 1510, -5, 1.4, 0.7, 6.0), (3, 400, -7, 2.2, 0.9, 6.6)]
        hs = []
        for k, (L, x, dy, r_, i_, sd) in enumerate(pts):
            a = ramp(t, tref + 0.5 + k * 1.3, tref + 2.0 + k * 1.3)
            hs.append((L, x, dy, r_, i_ * a, sd))
        return self._dawn(t, tref, -40, hs, brighten=0.04)

    def bg_ember(self, t):
        r = self.scene('ember')
        tref = self.t0('f04')
        if not hasattr(self, '_embers'):
            g = np.random.default_rng(31)
            E = []
            for L, n in ((1, 9), (2, 9), (3, 6)):
                xs = np.sort(g.uniform(260, r.WL - 260, n))
                for x in xs:
                    E.append((L, float(x), -5 - L, 1.3 + 0.35 * L, float(g.uniform(0.7, 1.0)), float(g.uniform(0, 9))))
            order = g.permutation(len(E))
            self._embers = (E, order)
        E, order = self._embers
        # f05 一拍里，火一处处灭掉
        ta, tb = self.t0('f05') - 0.5, self.tn('f05') - 0.4
        em = []
        for rank, idx in enumerate(order):
            L, x, dy, rr, inten, sd = E[idx]
            toff = ta + (tb - ta) * (rank / len(E)) ** 0.9
            a = 1 - ramp(t, toff, toff + 0.9)
            em.append((L, x, dy, rr, inten * a, sd))
        return r.render(t - tref, -60 + (t - tref) * 3.0, embers=em)

    def bg_ridge3(self, t):
        r = self.scene('ridge3')
        return r.render(t - self.t0('h03'), -30 + (t - self.t0('h03')) * 3.5)

    def bg_last(self, t):
        img = self.scene('last').render(t)
        a = ramp(t, self.t0('g06') - 0.4, self.t0('g06') + 0.8) * (1 - ramp(t, self.t1('g06') + 0.6, self.tn('g06') - 0.3))
        f = flicker(t, 1.7)
        add_glow(img, W / 2, 770, 60, (1.0, 0.50, 0.18), 0.05 * a * f)
        add_glow(img, W / 2, 770, 9, (1.0, 0.62, 0.28), 0.40 * a * f)
        add_glow(img, W / 2, 770, 2.6, (1.0, 0.90, 0.66), 0.95 * a * f)
        return img

    def bg_endcard(self, t):
        return self.scene('endcard').render(t)

    def bg_pai(self, t):
        """十家牌：十块牌，轮着亮。"""
        img = self.scene('pai').render(t)
        ta = self.t0('f02')
        app = ramp(t, ta - 0.2, ta + 0.8) * (1 - ramp(t, self.tn('f02') - 0.5, self.tn('f02')))
        if app <= 0.01:
            return img
        tw, th, gx = 124, 176, 50
        x0 = W / 2 - (5 * tw + 4 * gx) / 2
        turn = (t - self.seg('f02', 1)) / 0.42
        for k in range(10):
            r_, c_ = divmod(k, 5)
            x = x0 + c_ * (tw + gx)
            y = 190 + r_ * (th + 56)
            lit = float(np.clip(1 - abs(turn - k), 0, 1)) if turn > -0.5 else 0.0
            col = np.array(PALE, np.float32) * (0.36 + 0.50 * lit) + np.array(WARM, np.float32) * 0.25 * lit
            ov = np.zeros((th + 8, tw + 8), np.uint8)
            cv2.rectangle(ov, (4, 4), (tw + 3, th + 3), 255, 1, cv2.LINE_AA)
            for j in range(4):                              # 牌上的字：几道短竖线示意
                xx = 4 + int(tw * (0.24 + 0.17 * j))
                cv2.line(ov, (xx, 30), (xx, 30 + int(th * (0.40 + 0.12 * ((j * 7 + k * 3) % 4) / 3))), 170, 1, cv2.LINE_AA)
            a = ov.astype(np.float32)[..., None] / 255.0 * app
            reg = img[int(y):int(y) + th + 8, int(x):int(x) + tw + 8]
            reg *= (1 - a)
            reg += col * a
            if lit > 0.05:
                add_glow(img, x + tw / 2, y + th / 2, 70, WARM, 0.035 * lit * app)
        return img

    # ── 地图 ──
    def bg_map(self, t):
        t0, t1, tn, seg = self.t0, self.t1, self.tn, self.seg
        cam = self.cam(t)
        md = self.md
        in_bc = t < t0('d03')
        in_lc = t0('e02') - 2 <= t < t0('e15')
        in_ng = t0('f01') - 2 <= t < t0('f08')
        in_gx = t0('g01') - 2 <= t < t0('g06')
        in_end = t >= t0('h04') - 2

        # 海拔 300 米以上的提亮
        if in_bc:
            zom = ramp(t, seg('b02', 1) + 0.3, seg('b02', 1) + 2.6)
            gen = ramp(t, t0('b06') + 0.5, t0('b06') + 3.5)
            hi = max(zom * (1 - gen), 0) * 1.0 + gen * (0.62 + 0.25 * ramp(t, t0('b09'), t0('b09') + 2) - 0.42 * ramp(t, t0('c01') - 0.5, t0('c01') + 2.0))
            region = zom * (1 - gen)
        elif in_lc:
            hi, region = 0.72, 0.0
        elif in_ng:
            hi, region = 0.70, 0.0
        elif in_gx:
            hi, region = 0.66, 0.0
        else:
            hi, region = 0.40 + 0.38 * ramp(t, t0('h06'), t0('h07') + 1.0), 0.0
        img = maps.render_base(md, cam, 0.0)
        if hi > 0.004:
            m = maps.warp_mask(md, cam, 'hi')
            if region > 0.004:
                zw = self._zomia_weight(cam)
                m = m * (1 - region * (1 - zw))
                img *= (1 - 0.45 * region * (1 - zw))[..., None]
            lum = img.mean(-1, keepdims=True)
            img += (np.array([0.085, 0.092, 0.095], np.float32) * (0.35 + lum * 9.0)) * (m[..., None] * hi)
        img = maps.draw_vectors(img, md, cam, coast=0.55, rivers=0.30)

        # 经界之网：只落在低地上
        grid = 0.0
        origins = None
        if in_bc and t >= t0('c04') - 0.3:
            grid = 0.40 * (1 - ramp(t, t0('d01') - 0.3, t0('d01') + 2.5))
            origins = [(PLACES['白鹿洞'], t0('c04') - 0.2), (PLACES['漳州'], t0('c04') + 0.6)]
        elif in_end and t >= t0('h05') - 0.2:
            grid = 0.38 * ramp(t, t0('h05'), t0('h05') + 3.5) * (1 - 0.45 * ramp(t, t0('h08'), t0('h08') + 4))
        if grid > 0.01:
            self._draw_grid(img, cam, grid, t, origins)

        mk, lb = maps.marker, maps.label

        def place(name, a, text=None, color=PALE, size=38, anchor='l', dx=20, dy=-3, glow=1.0, square=False, r=5.0):
            if a <= 0.004:
                return
            lo, la = PLACES[name]
            x, y = mk(img, cam, lo, la, a, color=color, glow=glow, square=square, r=r)
            lb(img, x, y, text or name, a, size=size, color=color if color != PALE else (0.87, 0.84, 0.77), anchor=anchor, dx=dx, dy=dy)

        def region_label(lon, lat, text, a, size=38, color=(0.66, 0.69, 0.72), spacing=16.0, fontname='serif-l'):
            if a <= 0.004:
                return
            x, y = cam.to_screen(lon, lat)
            lb(img, float(x), float(y), text, a, size=size, color=color, anchor='c', dx=0, dy=0, fontname=fontname, spacing=spacing)

        if in_bc:
            # 赞米亚
            a = ramp(t, seg('b02', 1) + 1.6, seg('b02', 1) + 3.0) * (1 - ramp(t, t0('b06') + 0.2, t0('b06') + 1.8))
            region_label(100.6, 22.4, '赞　米　亚', a, size=70, color=(0.82, 0.86, 0.89), spacing=10)
            region_label(100.6, 20.0, 'ZOMIA', a * 0.9, size=28, color=(0.58, 0.65, 0.71), spacing=16, fontname='sans-l')
            # 贵州 / 龙场
            a = ramp(t, t0('b05') + 0.8, t0('b05') + 2.0) * (1 - ramp(t, t0('b06') + 1.0, t0('b06') + 2.5))
            region_label(107.3, 28.3, '贵　州', a, size=38)
            a_lc = ramp(t, seg('b05', 1) - 0.2, seg('b05', 1) + 0.8) * (1 - ramp(t, tn('d02') - 0.4, tn('d02') + 0.6))
            place('龙场', a_lc, color=WARM, glow=1.6)
            # 四省
            a = ramp(t, t0('b06') + 2.2, t0('b06') + 3.8) * (1 - ramp(t, t0('c01') - 0.4, t0('c01') + 1.0))
            for (lo, la, nm) in ((115.75, 27.55, '江　西'), (117.9, 26.05, '福　建'), (113.3, 24.3, '广　东'), (111.75, 27.6, '湖　南')):
                region_label(lo, la, nm, a * 0.95, size=36)
            # 朱熹
            a = ramp(t, seg('c02', 0) + 0.8, seg('c02', 0) + 1.8) * (1 - ramp(t, t0('d01') + 2.0, t0('d01') + 3.5))
            place('白鹿洞', a, '白鹿洞书院')
            a = ramp(t, seg('c03', 0) - 0.1, seg('c03', 0) + 0.9) * (1 - ramp(t, t0('d01') + 2.0, t0('d01') + 3.5))
            place('漳州', a)
            # 早年：余姚 → 南昌 → 广信 → 余姚（示意）
            td = t0('d01')
            a_out = 1 - ramp(t, tn('d02') - 0.5, tn('d02') + 0.5)
            a = ramp(t, seg('d01', 0) + 0.3, seg('d01', 0) + 1.2) * a_out
            place('余姚', a, color=WARM, glow=1.4, anchor='r')
            a2 = ramp(t, seg('d01', 1) + 0.2, seg('d01', 1) + 1.0) * a_out
            if a2 > 0.004:
                f = ramp(t, seg('d01', 1), seg('d01', 1) + 1.8)
                maps.polyline(img, cam, [PLACES['余姚'], (118.6, 29.3), PLACES['南昌']], 0.55 * a2, (0.86, 0.72, 0.52), f)
            place('南昌', ramp(t, seg('d01', 1) + 1.3, seg('d01', 1) + 2.0) * a_out, anchor='r')
            a3 = ramp(t, seg('d01', 2) + 0.2, seg('d01', 2) + 1.0) * a_out
            if a3 > 0.004:
                f = ramp(t, seg('d01', 2) + 0.2, seg('d01', 2) + 2.8)
                maps.polyline(img, cam, [PLACES['南昌'], PLACES['广信'], (119.6, 29.25), PLACES['余姚']], 0.55 * a3, (0.86, 0.72, 0.52), f)
            place('广信', ramp(t, seg('d01', 2) + 0.9, seg('d01', 2) + 1.7) * a_out, dx=0, dy=38, anchor='c')
            # 图例
            a = ramp(t, t0('b06') + 3.0, t0('b06') + 4.5) * (1 - ramp(t, t0('c04') - 0.5, t0('c04') + 0.8))
            self._caption(img, '亮处：海拔 300 米以上', a)
            a = ramp(t, t0('c04') + 1.5, t0('c04') + 3.0) * (1 - ramp(t, t0('d01') - 0.3, t0('d01') + 1.0))
            self._caption(img, '细网只落在低地：示意，非实测', a)
        elif in_lc:
            first = t < t0('e12') - 2
            a = ramp(t, t0('e02') + 2.6, t0('e02') + 3.8) if first else 1.0
            place('龙场', a, '龙场驿', color=WARM, glow=1.7, size=42)
            place('贵阳', a * 0.8, size=30, r=3.5, dx=0, dy=34, anchor='c')
            ta = seg('e03', 0) if first else t0('e12') - 3
            a2 = ramp(t, ta + 0.3, ta + 1.6)
            region_label(105.1, 26.35, '贵州宣慰司　水西安氏', a2 * 0.95, size=34, spacing=8)
            tr = seg('e03', 1) if first else t0('e12') - 3
            a3 = ramp(t, tr - 0.1, tr + 0.6)
            if a3 > 0.004:
                f = ramp(t, tr, tr + 3.2)
                maps.polyline(img, cam, NINE_POSTS, 0.9 * a3, (0.90, 0.80, 0.62), f, dotted=True)
                x, y = cam.to_screen(*NINE_POSTS[5])
                lb(img, float(x), float(y), '龙场九驿', a3 * ramp(t, tr + 1.8, tr + 2.8), size=32, color=(0.84, 0.78, 0.66), anchor='c', dx=-40, dy=-44)
            self._caption(img, '亮处：海拔 300 米以上', a * 0.9)
        elif in_ng:
            a_all = 1.0
            if t < t0('f02'):
                a = ramp(t, t0('f01') + 2.8, t0('f01') + 4.0)
                for (lo, la, nm) in ((115.95, 26.25, '江　西'), (117.5, 25.6, '福　建'), (114.6, 23.85, '广　东'), (111.95, 25.7, '湖　广')):
                    region_label(lo, la, nm, a * 0.95, size=38)
                a = ramp(t, seg('f01', 1) - 0.1, seg('f01', 1) + 1.0)
                place('赣州', a, size=38)
                region_label(114.75, 24.72, '南　赣', a, size=68, color=(0.86, 0.88, 0.89), spacing=12)
            elif t < t0('f04'):
                place('赣州', 1.0, size=34)
                a = ramp(t, seg('f03', 1) - 0.2, seg('f03', 1) + 0.5)
                place('横水', a, '横水 · 桶冈', color=WARM, glow=1.8, anchor='r')
                a = ramp(t, seg('f03', 1) + 0.9, seg('f03', 1) + 1.5)
                place('浰头', a, color=WARM, glow=1.8)
            else:
                place('赣州', 1.0, size=34)
                a = ramp(t, seg('f07', 1) + 0.2, seg('f07', 1) + 0.9)
                place('崇义', a, '崇义县', square=True, anchor='r')
                a = ramp(t, seg('f07', 1) + 0.8, seg('f07', 1) + 1.5)
                place('和平', a, '和平县', square=True)
        elif in_gx:
            a = ramp(t, t0('g01') + 2.6, t0('g01') + 3.6)
            fade_w = 1 - ramp(t, t0('g05') + 0.3, t0('g05') + 1.8)
            place('田州', a * ramp(t, seg('g01', 1) + 0.9, seg('g01', 1) + 1.6) * fade_w, color=WARM, glow=1.5)
            place('思恩', a * ramp(t, seg('g01', 1) + 0.1, seg('g01', 1) + 0.8) * fade_w, color=WARM, glow=1.5)
            place('南宁', a * 0.8 * fade_w, size=30, r=3.5)
            a4 = ramp(t, t0('g04') + 1.6, t0('g04') + 2.4) * fade_w
            place('八寨', a4, anchor='c', dx=0, dy=-38)
            place('断藤峡', ramp(t, t0('g04') + 2.4, t0('g04') + 3.2) * fade_w)
            a5 = ramp(t, t0('g05') + 1.5, t0('g05') + 2.5)
            dying = 1 - 0.55 * ramp(t, t1('g05') + 0.3, tn('g05') + 0.4)
            place('南安', a5, '南安 · 青龙铺', color=WARM, glow=1.9 * dying, anchor='r')
            place('赣州', a5 * 0.85, size=32, r=3.5)
        else:
            a = ramp(t, t0('h06') + 0.3, t0('h06') + 1.5)
            place('龙场', a, color=WARM, glow=1.7)
            place('赣州', a * ramp(t, t0('h06') + 0.9, t0('h06') + 2.0), '南赣', color=WARM, glow=1.7)
            place('思恩', a * ramp(t, t0('h06') + 1.5, t0('h06') + 2.6), '思田', color=WARM, glow=1.7)
            self._lights_draw(img, cam, t)
            self._caption(img, '画面为示意', ramp(t, t0('h05') + 1.0, t0('h05') + 2.5))
        return img

    def _zomia_weight(self, cam):
        """Scott 所指高地的大致范围（示意）：几团柔和的椭圆。"""
        yy, xx = np.mgrid[0:H:8, 0:W:8].astype(np.float32)
        gx = (xx - W / 2) / cam.scale + cam.gx
        gy = (yy - H * cam.cy_frac) / cam.scale + cam.gy
        lon = gx / maps.Z8 * 360 - 180
        lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * gy / maps.Z8))))
        w = np.zeros_like(lon)
        for (cl, ct, rl, rt) in ((100.2, 23.2, 7.6, 6.4), (106.4, 16.8, 3.2, 5.6), (106.6, 26.0, 3.8, 3.2), (95.5, 25.0, 3.0, 4.0)):
            d = ((lon - cl) / rl) ** 2 + ((lat - ct) / rt) ** 2
            w = np.maximum(w, np.exp(-np.clip(d - 0.55, 0, None) * 1.6))
        return cv2.resize(w, (W, H), interpolation=cv2.INTER_CUBIC)

    def _draw_grid(self, img, cam, alpha, t, origins=None, step=0.25):
        low = maps.warp_mask(self.md, cam, 'low')
        ov = np.zeros((H, W), np.uint8)
        s = cam.scale
        lon0 = (0 - W / 2) / s + cam.gx
        lon1 = (W - W / 2) / s + cam.gx
        lo_a, lo_b = lon0 / maps.Z8 * 360 - 180, lon1 / maps.Z8 * 360 - 180
        for lo in np.arange(np.floor(lo_a / step) * step, lo_b + step, step):
            x = float(cam.to_screen(lo, 25.0)[0])
            cv2.line(ov, (int(round(x * 16)), 0), (int(round(x * 16)), H * 16), 255, 1, cv2.LINE_AA, shift=4)
        la_top = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * ((0 - H * cam.cy_frac) / s + cam.gy) / maps.Z8))))
        la_bot = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * ((H - H * cam.cy_frac) / s + cam.gy) / maps.Z8))))
        lstep = step * 0.9
        for la in np.arange(np.floor(la_bot / lstep) * lstep, la_top + lstep, lstep):
            y = float(cam.to_screen(110.0, la)[1])
            cv2.line(ov, (0, int(round(y * 16))), (W * 16, int(round(y * 16))), 255, 1, cv2.LINE_AA, shift=4)
        a = ov.astype(np.float32) / 255.0 * low * alpha
        if origins:
            yy, xx = np.mgrid[0:H:6, 0:W:6].astype(np.float32)
            reach = np.zeros_like(xx)
            for (lo, la), ts in origins:
                ox, oy = cam.to_screen(lo, la)
                d = np.sqrt((xx - float(ox)) ** 2 + (yy - float(oy)) ** 2)
                rad = max(t - ts, 0) * 80.0
                reach = np.maximum(reach, np.clip((rad - d) / 140.0, 0, 1))
            a *= cv2.resize(reach, (W, H), interpolation=cv2.INTER_LINEAR)
        img += (np.array([0.62, 0.66, 0.70], np.float32) - img) * a[..., None]

    def _lights_draw(self, img, cam, t):
        """片尾：山里一点一点亮起来的灯。"""
        ta = self.t0('h08') + 0.4
        if t < ta:
            return
        if self._lights is None:
            g = np.random.default_rng(99)
            hi = self.md.hi['z8'][0]
            ox, oy, _ = maps.ORIGIN['z8']
            lo0, la0 = 103.5, 21.8
            lo1, la1 = 121.0, 30.8
            pts = []
            while len(pts) < 380:
                lo, la = g.uniform(lo0, lo1), g.uniform(la0, la1)
                gx, gy = maps.lonlat_to_g(lo, la)
                u, v = int(gx - ox), int(gy - oy)
                if 0 <= u < hi.shape[1] and 0 <= v < hi.shape[0] and hi[v, u] > 200:
                    pts.append((lo, la, g.uniform(0, 1) ** 0.8, g.uniform(1.4, 2.4), g.uniform(0.6, 1.0), g.uniform(0, 9)))
            self._lights = pts
        span = (self.tn('h08') - ta) + 1.5
        for (lo, la, u, rr, inten, sd) in self._lights:
            a = ramp(t, ta + u * span * 0.82, ta + u * span * 0.82 + 1.4)
            if a <= 0.01:
                continue
            x, y = cam.to_screen(lo, la)
            f = 0.85 + 0.15 * np.sin(t * 2.3 + sd)
            add_glow(img, float(x), float(y), rr * 3.2, (1.0, 0.56, 0.22), 0.12 * a * inten * f)
            add_glow(img, float(x), float(y), rr * 0.8, (1.0, 0.86, 0.58), 0.85 * a * inten * f)

    def _caption(self, img, text, a):
        if a <= 0.004:
            return
        sp, sw, sh = text_sprite(text, 'sans-l', 27, T3(GREY * 0.92), 2.0, shadow=5.0)
        blit(img, sp, W - 82 + 31, H - 60, a, 'r')

    # ════════════════ 文字 ════════════════
    def draw_text(self, img, t):
        self._draw_scrim(img, t)
        for bid in sb.ORDER:
            t0, t1, tnx = self.B[bid]
            if t < t0 - 0.4 or t > tnx + 0.1:
                continue
            if bid == 'a05':
                self._legend(img, t)
                continue
            self._draw_beat(img, bid, t)
        self._draw_tags(img, t)
        self._title(img, t)
        self._endcard(img, t)

    def _layout(self, bid):
        b = sb.BOARD[bid]
        low = b['pos'] == 'low'
        items = []
        y = 0.0
        prev = None
        for (k, txt) in b['segs']:
            n_lines = txt.count('\n') + 1
            longest = max(len(l) for l in txt.split('\n'))
            if k == 'N':
                size = 56 if low else 60
                if longest > 25:
                    size = int(size * 25 / longest)
                st = dict(fontname='serif', size=size, color=T3(PAPER), spacing=2.0, line_gap=1.62)
                gap_before = 14 if prev == 'N' else 40
            elif k == 'Q':
                size = 72 if low else 80
                if bid == 'e09':
                    size = 88
                if bid == 'h01':
                    size = 128
                if longest > 16:
                    size = int(size * 16 / longest)
                st = dict(fontname='serif-sb', size=size, color=T3(BRIGHT), spacing=5.0 if bid != 'h01' else 26.0, line_gap=1.55)
                gap_before = 40 if prev else 0
            else:
                size = 38 if low else 40
                st = dict(fontname='serif-l', size=size, color=T3(GREY * 1.06), spacing=1.5, line_gap=1.55)
                gap_before = 30
            h_txt = st['size'] * st['line_gap'] * (n_lines - 1) + st['size'] * 1.18
            if prev is not None:
                y += gap_before
            items.append(dict(kind=k, text=txt, st=st, y=y + h_txt / 2, h=h_txt))
            y += h_txt
            prev = k
        total = y
        if low:
            top = 980 - total
        else:
            top = 548 - total / 2
        for it in items:
            it['cy'] = top + it['y']
        return items

    def _draw_beat(self, img, bid, t):
        t0, t1, tnx = self.B[bid]
        if not hasattr(self, '_layouts'):
            self._layouts = {}
        if bid not in self._layouts:
            self._layouts[bid] = self._layout(bid)
        times = sb.seg_times(bid, t0, t1)
        out = smooth((tnx - 0.04 - t) / 0.36)
        for it, ts in zip(self._layouts[bid], times):
            a_in = smooth((t - ts) / 0.55)
            a = float(a_in * out)
            if a <= 0.004:
                continue
            sp, sw, sh = text_sprite(it['text'], shadow=6.0 if sb.BOARD[bid]['pos'] == 'low' else 0.0, **it['st'])
            rise = (1 - a_in) * 7.0
            blit_blur(img, sp, W / 2, it['cy'] + rise, a, (1 - a_in) * 3.0)

    def _draw_scrim(self, img, t):
        """地图镜头下部压暗，托住字。"""
        a = 0.0
        for bid in sb.ORDER:
            if sb.BOARD[bid]['pos'] != 'low':
                continue
            t0, t1, tnx = self.B[bid]
            if t0 - 0.6 < t < tnx + 0.4:
                a = max(a, float(smooth((t - t0 + 0.6) / 0.6) * smooth((tnx + 0.4 - t) / 0.6)))
        if a <= 0.004:
            return
        if not hasattr(self, '_scrim'):
            yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
            self._scrim = smooth((yy - 0.40) / 0.40) * 0.84
        img *= (1 - self._scrim * a)

    def _draw_tags(self, img, t):
        for tg, ta, tb in self.tag_runs:
            a = window(t, ta - 0.1, tb - 0.05, 0.5, 0.4)
            if a <= 0.004:
                continue
            kind, src = tg
            name, col = KIND[kind]
            x, y = 92, 82
            cv2.circle(img, (int(x), int(y)), 7, T3(np.asarray(col) * a + img[int(y), int(x)] * (1 - a)), -1, cv2.LINE_AA)
            sp, sw, sh = text_sprite(name, 'sans-r', 31, T3(col), 6.0, shadow=5.0)
            pad = int(31 * 0.6) + 15
            blit(img, sp, x + 24 - pad, y - 2, a, 'l')
            sp2, sw2, _ = text_sprite(src, 'sans-l', 30, T3(GREY * 1.12), 1.5, shadow=5.0)
            blit(img, sp2, x + 24 - pad + (sw - 2 * pad) + 30, y - 2, a, 'l')
        for bid in sb.ORDER:
            note = sb.BOARD[bid]['note']
            if not note:
                continue
            t0, t1, tnx = self.B[bid]
            a = window(t, t0 + 0.9, tnx - 0.05, 0.6, 0.4)
            if a <= 0.004:
                continue
            sp, sw, sh = text_sprite(note, 'sans-l', 28, T3(DIM * 1.5), 1.5, shadow=5.0)
            pad = int(28 * 0.6) + 15
            yy = 138 if sb.BOARD[bid]['tag'] else 82
            blit(img, sp, 82 - pad + 0, yy, a, 'l')
        for name, ta, tb in self.sections:
            a = window(t, ta + 0.2, tb - 0.3, 0.8, 0.6) * 0.9
            if a <= 0.004:
                continue
            sp, sw, sh = text_sprite(name, 'serif-l', 29, T3(GREY * 0.85), 4.0, shadow=5.0)
            pad = int(29 * 0.6) + 15
            blit(img, sp, 82 - pad, H - 60, a, 'l')

    def _legend(self, img, t):
        t0, t1, tnx = self.B['a05']
        rows = [('史实', FACT, '注明出处'), ('理论', COOL, '署名'), ('解读', EMBER, '我们自己的，单独标出')]
        d = t1 - t0
        starts = [t0 + d * 0.22, t0 + d * 0.47, t0 + d * 0.66]
        out = smooth((tnx - 0.12 - t) / 0.5)
        a0 = float(smooth((t - t0 + 0.1) / 0.5) * out)
        sp, _, _ = text_sprite('片中的话，分三种', 'serif-l', 40, T3(GREY), 8.0)
        blit(img, sp, W / 2, 330, a0)
        for i, ((name, col, desc), ts) in enumerate(zip(rows, starts)):
            a = float(smooth((t - ts) / 0.5) * out)
            if a <= 0.004:
                continue
            y = 474 + i * 124
            x = W / 2 - 400
            cv2.circle(img, (int(x), int(y)), 9, T3(np.asarray(col) * a + img[int(y), int(x)] * (1 - a)), -1, cv2.LINE_AA)
            sp, sw, sh = text_sprite(name, 'serif-m', 62, T3(col), 12.0)
            pad = int(62 * 0.6)
            blit(img, sp, x + 44 - pad, y - 3, a, 'l')
            sp2, _, _ = text_sprite(desc, 'serif-l', 50, T3(PAPER), 3.0)
            blit(img, sp2, x + 44 + 210 - int(50 * 0.6), y - 2, a, 'l')

    def _title(self, img, t):
        ta, tb = self.tl['title']
        a = window(t, ta + 0.3, tb - 0.1, 1.3, 0.9)
        if a <= 0.004:
            return
        a_in = smooth((t - ta - 0.3) / 1.3)
        sp, _, _ = text_sprite('龙场不是书斋顿悟', 'serif-sb', 116, T3(BRIGHT), 14.0)
        blit_blur(img, sp, W / 2, 520, a, (1 - a_in) * 5.0)
        a2 = window(t, ta + 1.3, tb - 0.1, 1.0, 0.9)
        cv2.line(img, (W // 2 - 60, 640), (W // 2 + 60, 640), T3(DIM * a2 + rgb('#06080b') * (1 - a2)), 1, cv2.LINE_AA)
        sp2, _, _ = text_sprite('思想与启蒙　·　第一集', 'serif-l', 38, T3(GREY), 12.0)
        blit(img, sp2, W / 2, 706, a2)

    def _endcard(self, img, t):
        ta, tb = self.tl['end']
        if t < ta - 0.2:
            return
        a = window(t, ta + 0.5, tb - 0.6, 1.4, 1.2)
        a_in = smooth((t - ta - 0.5) / 1.4)
        sp, _, _ = text_sprite('龙场不是书斋顿悟', 'serif-sb', 84, T3(BRIGHT), 12.0)
        blit_blur(img, sp, W / 2, 300, a, (1 - a_in) * 4.0)
        sp2, _, _ = text_sprite('思想与启蒙　·　第一集', 'serif-l', 34, T3(GREY), 12.0)
        blit(img, sp2, W / 2, 410, a)
        a3 = window(t, ta + 2.6, tb - 0.6, 1.2, 1.2)
        lines = [
            '史料　钱德洪《王阳明年谱》 · 《传习录》 · 《与安宣慰》 · 《何陋轩记》 · 《象祠记》',
            '《南赣乡约》 · 《立崇义县治疏》 · 《宋史·朱熹传》 · 刘克庄《漳州谕畲》',
            '理论　James C. Scott, The Art of Not Being Governed, Yale University Press, 2009',
            '地形　SRTM / Terrain Tiles　　海岸与河流　Natural Earth　　地图只画山川，路线与范围为示意',
            '旁白为 AI 合成语音　　配乐与画面由程序生成　　字体　思源宋体 · 思源黑体',
        ]
        for i, ln in enumerate(lines):
            sp3, _, _ = text_sprite(ln, 'sans-l', 28, T3(DIM * 1.5), 1.2)
            blit(img, sp3, W / 2, 596 + i * 62, a3)

    # ════════════════ 一帧 ════════════════
    def frame(self, t):
        sch = self.schedule
        idx = 0
        for i, (ts, k) in enumerate(sch):
            if t >= ts:
                idx = i
        key = sch[idx][1]
        img = self.bg(key, t)
        XF = 1.1
        if idx + 1 < len(sch) and sch[idx + 1][0] - t < XF / 2 and sch[idx + 1][1] != key:
            u = 0.5 - (sch[idx + 1][0] - t) / XF
            img = img * (1 - smooth(u)) + self.bg(sch[idx + 1][1], t) * smooth(u)
        elif idx > 0 and t - sch[idx][0] < XF / 2 and sch[idx - 1][1] != key:
            u = 0.5 + (t - sch[idx][0]) / XF
            img = self.bg(sch[idx - 1][1], t) * (1 - smooth(u)) + img * smooth(u)
        self.draw_text(img, t)
        g = ramp(t, 0.15, 1.9) * (1 - ramp(t, self.total - 1.6, self.total - 0.1))
        img *= g
        img += self.dither
        return np.clip(img * 255.0 + 0.5, 0, 255).astype(np.uint8)


def main():
    mode, work, tlp = sys.argv[1:4]
    gfx.FONT_DIR = work + '/fonts'
    tl = json.load(open(tlp))
    film = Film(work, tl)
    if mode == 'still':
        out = sys.argv[4]
        os.makedirs(out, exist_ok=True)
        for ts in sys.argv[5:]:
            t = float(ts)
            fr = film.frame(t)
            cv2.imwrite(f'{out}/f_{t:07.2f}.png', cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
            print('still', ts, flush=True)
    else:
        out = sys.argv[4]
        ta = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
        tb = float(sys.argv[6]) if len(sys.argv) > 6 else film.total
        n0, n1 = int(round(ta * FPS)), int(round(tb * FPS))
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
               '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '10', '-pix_fmt', 'yuv420p',
               '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', out]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        import time
        tt = time.time()
        for n in range(n0, n1):
            p.stdin.write(film.frame(n / FPS).tobytes())
            if (n - n0) % 150 == 0:
                print('frame', n, '/', n1, '%.1f fps' % ((n - n0 + 1) / (time.time() - tt)), flush=True)
        p.stdin.close()
        p.wait()
        print('done', out, flush=True)


if __name__ == '__main__':
    main()
