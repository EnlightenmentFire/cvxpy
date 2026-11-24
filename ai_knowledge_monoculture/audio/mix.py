"""Assemble narration + music beds + sound effects into one 48 kHz stereo track.
Music is ducked under the voice using the known sentence times (smooth attack/release)."""
import os
import sys

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import synth as S  # noqa: E402

SR = S.SR


def load48(path):
    w, sr = sf.read(path, dtype="float32")
    if w.ndim > 1:
        w = w.mean(axis=1)
    if sr != SR:
        g = np.gcd(sr, SR)
        w = resample_poly(w, SR // g, sr // g).astype(np.float32)
    return w


def place(buf, x, t, gain=1.0):
    s = int(round(t * SR))
    if s >= len(buf) or s + len(x) <= 0:
        return
    a = max(0, -s)
    e = min(len(buf), s + len(x))
    buf[max(0, s): e] += x[a: a + (e - max(0, s))] * gain


def db(x):
    return 10 ** (x / 20)


def duck_gain(voice, depth_db=-13.0, attack=0.06, release=0.45):
    """Gain curve for the music: down by depth_db while the voice is present."""
    hop = 480
    n = len(voice) // hop + 1
    env = np.zeros(n)
    for i in range(n):
        seg = voice[i * hop:(i + 1) * hop]
        env[i] = np.sqrt(np.mean(seg ** 2)) if len(seg) else 0
    present = (env > db(-45)).astype(float)
    # smooth with asymmetric one-pole (fast attack, slow release)
    g = np.ones(n)
    target_lo = db(depth_db)
    cur = 1.0
    a_att = np.exp(-hop / (attack * SR))
    a_rel = np.exp(-hop / (release * SR))
    look = int(0.12 * SR / hop)       # start ducking slightly before the voice
    pres = np.convolve(present, np.ones(look + 1), mode="full")[look:look + n] > 0
    for i in range(n):
        tgt = target_lo if pres[i] else 1.0
        a = a_att if tgt < cur else a_rel
        cur = a * cur + (1 - a) * tgt
        g[i] = cur
    return np.repeat(g, hop)[: len(voice)]


def master(mix, peak_db=-1.0):
    lim = db(peak_db)
    return np.tanh(mix / lim) * lim


def mix_track(total, voice_events, music_parts, sfx_events, out_path, music_gain_db=-17.0):
    """voice_events: [(t, path, gain)], music_parts: [(t0, t1, mono array)], sfx_events: [(t, array, gain, pan)]"""
    n = int((total + 0.5) * SR)
    voice = np.zeros(n, np.float32)
    for t, path, g in voice_events:
        place(voice, load48(path), t, g)
    music = np.zeros(n, np.float32)
    for t0, t1, arr in music_parts:
        seg = arr[: int((t1 - t0) * SR)].astype(np.float32)
        fl = min(len(seg) // 4, int(1.2 * SR))
        if fl > 0:
            seg[:fl] *= np.linspace(0, 1, fl)
            seg[-fl:] *= np.linspace(1, 0, fl)
        place(music, seg, t0)
    music *= db(music_gain_db) / (np.sqrt(np.mean(music ** 2)) / db(-18) + 1e-9) if np.any(music) else 1
    music *= duck_gain(voice)
    L = voice + music
    R = voice + music
    for t, arr, g, pan in sfx_events:
        lg, rg = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        tmpL = np.zeros(n, np.float32)
        place(tmpL, arr.astype(np.float32), t, g)
        L += tmpL * lg * 1.41
        R += tmpL * rg * 1.41
    st = np.stack([master(L), master(R)], axis=1)
    sf.write(out_path, st, SR, subtype="PCM_16")
    return out_path
