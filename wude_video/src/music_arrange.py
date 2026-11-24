"""Arrange the score along the film's timeline (配乐规范 §二).

Three layers + ending: 铺底 (base) -> 推进 (push_*) -> 高潮 (climax) -> 结尾 (ending).
Sections change at story beats with 2-4 s equal-power crossfades; a layer never restarts the
same material it has just used (a per-layer cursor walks through all generated material).
Two deliberate breaks requested in the episode brief:
  * 秦段 drum_stop: the music drops out before 「刚毅戾深……」
  * 新垣平 被诛: 音乐骤停一拍, then the base comes back in.
"""
import json
import os
import sys

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

SR = 48000
CLIPS = "/home/user/wude_build/music/clips"

LAYER_GAIN_DB = {"base": -6.0, "push_cold": -3.0, "push_tension": -4.0, "push_warm": -3.5,
                 "climax": 0.0, "ending": -3.0}


def load_material(choice):
    """choice: {layer: [wav paths in order of use]} -> {layer: np.array (n,2) @48k}"""
    mat = {}
    for layer, paths in choice.items():
        parts = []
        for p in paths:
            a, sr = sf.read(p)
            if a.ndim == 1:
                a = np.stack([a, a], 1)
            if sr != SR:
                a = resample_poly(a, SR, sr, axis=0)
            parts.append(a)
        # join the alternates with 3 s crossfades
        out = parts[0]
        for b in parts[1:]:
            out = xfade_concat(out, b, 3.0)
        # loudness-match the layer material (rough RMS normalisation, per layer)
        rms = np.sqrt(np.mean(out ** 2)) + 1e-9
        out = out * (10 ** (-20 / 20) / rms)
        mat[layer] = out
    return mat


def xfade_concat(a, b, secs):
    n = int(secs * SR)
    n = min(n, len(a), len(b))
    t = np.linspace(0, np.pi / 2, n)[:, None]
    mid = a[-n:] * np.cos(t) + b[:n] * np.sin(t)
    return np.concatenate([a[:-n], mid, b[n:]])


class Cursor:
    def __init__(self, mat):
        self.mat = mat
        self.pos = {k: 0 for k in mat}

    def take(self, layer, n):
        src = self.mat[layer]
        out = np.zeros((n, 2))
        i = 0
        while i < n:
            p = self.pos[layer]
            k = min(n - i, len(src) - p)
            out[i:i + k] = src[p:p + k]
            i += k
            self.pos[layer] = (p + k) % len(src)
            if self.pos[layer] == 0 and i < n:
                # wrapped around: start again a little later to avoid an exact loop point
                self.pos[layer] = int(7.3 * SR) % len(src)
        return out


def build(sections, total, mat, stops=()):
    """sections: list of (t_start, layer, gain_db_extra, xfade_s). Returns (n,2) music @48k."""
    n_total = int(total * SR)
    music = np.zeros((n_total, 2))
    cur = Cursor(mat)
    sections = sorted(sections, key=lambda s: s[0])
    for i, (t0, layer, extra_db, xf) in enumerate(sections):
        t1 = sections[i + 1][0] if i + 1 < len(sections) else total
        xf_next = sections[i + 1][3] if i + 1 < len(sections) else 0.0
        if layer in ("DROP", "STOP"):
            continue
        a = max(0.0, t0 - xf / 2)
        b = min(total, t1 + xf_next / 2)
        na, nb = int(a * SR), int(b * SR)
        seg = cur.take(layer, nb - na)
        g = 10 ** ((LAYER_GAIN_DB[layer] + extra_db) / 20)
        env = np.ones(nb - na)
        fi = int(xf * SR)
        fo = int(xf_next * SR)
        if fi > 0:
            env[:fi] = np.sin(np.linspace(0, np.pi / 2, fi))
        if fo > 0 and i + 1 < len(sections) and sections[i + 1][1] not in ("STOP",):
            env[-fo:] *= np.cos(np.linspace(0, np.pi / 2, fo))
        if i + 1 < len(sections) and sections[i + 1][1] == "STOP":
            # hard stop (20 ms) exactly at the next section start
            cut = int((t1 - a) * SR)
            env[cut:] = 0
            r = int(0.02 * SR)
            env[max(0, cut - r):cut] *= np.linspace(1, 0, min(r, cut))
        if i + 1 < len(sections) and sections[i + 1][1] == "DROP":
            cut = int((t1 - a) * SR)
            env[cut:] = 0
            r = int(0.6 * SR)
            env[max(0, cut - r):cut] *= np.linspace(1, 0, min(r, cut)) ** 2
        music[na:nb] += seg * (g * env)[:, None]
    return music
