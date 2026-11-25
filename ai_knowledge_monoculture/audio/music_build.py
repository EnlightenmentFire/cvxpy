"""Arrange the chosen MusicGen pieces along the timeline (three-layer arc) and write music.wav.

Arc (per the music spec):
  铺底  cold open … Athens       – drone / minimal piano / era colours, quiet
  推进  hiring … AI era           – electronic pulse, tension, a little louder
  高潮  1788 → today's remedies  – baroque → full piano+strings+drums, loudest; the narration
                                    stops ~2.6 s after the summary so the music stands alone
  结尾  ending + end card         – solo piano, 2-3 s tail into black
Sections join with 3 s equal-power crossfades; long sections loop a piece on a beat-aligned seam."""
import json
import os
import sys

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "render"))
import timeline  # noqa: E402

SR = 48000

# section -> (piece, gain dB, layer)
SECTIONS = [
    ("coldopen", "open", -3.0, "铺底"),
    ("photocopy", "bed", -2.0, "铺底"),
    ("twoills", "bed", -2.0, "铺底"),
    ("plymouth", "victorian", -2.5, "铺底"),
    ("athens", "lyre", -2.0, "铺底"),
    ("hiring", "push", 0.0, "推进"),
    ("flash", "tension", 0.5, "推进"),
    ("corn", "bed", -0.5, "推进"),
    ("knight", "tension", 0.5, "推进"),
    ("aiera", "push", 0.5, "推进"),
    ("federalist", "baroque", 0.0, "高潮前"),
    ("remedies", "climax", 1.5, "高潮"),
    ("ending", "ending", 0.0, "结尾"),
]


# start offsets (s) for pieces whose first seconds are a near-silent intro (avoids a sudden entrance)
PIECE_OFFSET = {"ending": 3.5}


LEVEL_PIECES = {"open", "bed", "victorian", "lyre", "push", "tension", "baroque"}


def load_piece(path, offset=0.0, level=False):
    w, sr = sf.read(path, dtype="float32")
    if w.ndim == 1:
        w = np.stack([w, w], axis=1)
    if sr != SR:
        g = np.gcd(sr, SR)
        w = np.stack([resample_poly(w[:, c], SR // g, sr // g) for c in range(2)], axis=1).astype(np.float32)
    # trim MusicGen's first 0.3 s (often a soft attack artefact) plus any listed intro; normalise to -20 dBFS RMS
    w = w[int((0.3 + offset) * SR):]
    if level:
        w = level_slow(w)
    rms = np.sqrt(np.mean(w ** 2)) + 1e-9
    return (w * (10 ** (-20 / 20) / rms)).astype(np.float32)


def level_slow(w, win_s=3.0, max_db=6.0):
    """Gentle leveller for bed layers: follow a 3 s RMS envelope and pull it toward the piece's median,
    at most +/-6 dB, so a continuation that grew louder doesn't creep up under the voice."""
    m = np.sqrt(np.mean(w ** 2, axis=1))
    hop = int(0.1 * SR)
    frames = np.array([np.sqrt(np.mean(m[i:i + hop] ** 2)) for i in range(0, len(m), hop)]) + 1e-6
    k = max(1, int(win_s / 0.1))
    env = np.sqrt(np.convolve(frames ** 2, np.ones(k) / k, mode="same")) + 1e-6
    target = np.median(env)
    g = np.clip(target / env, 10 ** (-max_db / 20), 10 ** (max_db / 20))
    g = np.convolve(g, np.ones(k) / k, mode="same")
    gs = np.interp(np.arange(len(m)), np.arange(len(g)) * hop + hop / 2, g)
    return (w * gs[:, None]).astype(np.float32)


def beat_period(w):
    """Rough beat period (s) from the onset-strength autocorrelation, 60-140 BPM; None if unclear."""
    m = w.mean(axis=1)
    hop = 512
    e = np.array([np.sum(m[i:i + hop] ** 2) for i in range(0, len(m) - hop, hop)])
    on = np.maximum(0, np.diff(np.log(e + 1e-9)))
    on = on - on.mean()
    ac = np.correlate(on, on, mode="full")[len(on) - 1:]
    fps = SR / hop
    lo, hi = int(fps * 60 / 140), int(fps * 60 / 60)
    k = lo + int(np.argmax(ac[lo:hi]))
    strength = ac[k] / (ac[0] + 1e-9)
    return (k / fps) if strength > 0.15 else None


def eq_power_xfade(a, b, n):
    t = np.linspace(0, np.pi / 2, n)[:, None]
    return a * np.cos(t) + b * np.sin(t)


def loop_to(w, length, xfade_s=4.0):
    """Extend piece w to `length` samples by looping on a beat-aligned seam with an equal-power crossfade."""
    if len(w) >= length:
        return w[:length]
    n = int(xfade_s * SR)
    bp = beat_period(w)
    body = len(w) - n
    if bp:
        beats = int(body / (bp * SR))
        body = int(beats * bp * SR)
    out = w[: body + n].copy()
    while len(out) < length:
        nxt = w[: body + n]
        mixed = eq_power_xfade(out[-n:], nxt[:n], n)
        out = np.concatenate([out[:-n], mixed, nxt[n:]])
    return out[:length]


def chain(takes, length, xfade_s=4.0):
    """Fill `length` samples by chaining compatible takes (same prompt, same key/tempo) with
    equal-power crossfades, cycling through them so no single piece repeats back-to-back."""
    if len(takes) == 1:
        return loop_to(takes[0], length, xfade_s)
    n = int(xfade_s * SR)
    out = takes[0].copy()
    k = 1
    while len(out) < length:
        nxt = takes[k % len(takes)]
        out = np.concatenate([out[:-n], eq_power_xfade(out[-n:], nxt[:n], n), nxt[n:]])
        k += 1
    return out[:length]


def build(voice_dir, robot, choices_path, pieces_dir, out_path, brake=True):
    segs, total = timeline.build(voice_dir, robot, None, allow_missing=False)
    ev = timeline.ev_by_id(segs)
    choices = json.load(open(choices_path))
    seg = {s.key: s for s in segs}
    # split the federalist segment: 1788 part / today's remedies (from c10_9)
    bounds = []
    for key, piece, gain, layer in SECTIONS:
        if key == "federalist":
            s0, s1 = seg["federalist"].start, ev["c10_9"].start - 0.3
        elif key == "remedies":
            s0, s1 = ev["c10_9"].start - 0.3, seg["federalist"].end
        else:
            s0, s1 = seg[key].start, seg[key].end
        bounds.append((key, piece, gain, layer, s0, s1))
    n_total = int((total + 0.5) * SR)
    music = np.zeros((n_total, 2), np.float32)
    xf = 3.0
    cache = {}
    for i, (key, piece, gain, layer, s0, s1) in enumerate(bounds):
        files = choices[piece] if isinstance(choices[piece], list) else [choices[piece]]
        takes = []
        for fn in files:
            path = os.path.join(pieces_dir, fn)
            if path not in cache:
                cache[path] = load_piece(path, PIECE_OFFSET.get(piece, 0.0), piece in LEVEL_PIECES)
            takes.append(cache[path])
        w = takes[0]
        a = max(0.0, s0 - (xf / 2 if i > 0 else 0))
        b = min(total + 0.5, s1 + (xf / 2 if i < len(bounds) - 1 else 0.5))
        L = int((b - a) * SR)
        # start each re-use of a piece at a different offset so repeats don't line up
        # a piece used in several sections starts from a different take each time
        rot = sum(1 for (k2, p2, *_r) in bounds[:i] if p2 == piece)
        order = takes[rot % len(takes):] + takes[:rot % len(takes)]
        x = chain(order, L) * (10 ** (gain / 20))
        nf = int(xf * SR)
        env = np.ones(L, np.float32)
        if i > 0:
            env[:nf] = np.sin(np.linspace(0, np.pi / 2, nf)) ** 1
        if i < len(bounds) - 1:
            env[-nf:] = np.cos(np.linspace(0, np.pi / 2, nf))
        st = int(a * SR)
        music[st: st + L] += x[: len(music) - st] * env[: len(music) - st, None]
    # automation: brake — the music stops for a breath when the futures market pauses (c6_12)
    gain = np.ones(n_total, np.float32)
    if brake and "c6_12" in ev:
        tb = ev["c6_12"].start + 0.6
        a, b = int(tb * SR), int((tb + 1.6) * SR)
        gain[a - int(0.25 * SR): a] = np.linspace(1, 0.08, int(0.25 * SR))
        gain[a: b] = 0.08
        gain[b: b + int(1.2 * SR)] = np.linspace(0.08, 1, int(1.2 * SR))
    # climax swell into the music-only moment after c10_14
    if "c10_14" in ev:
        a = int((ev["c10_14"].start - 2.0) * SR)
        b = int((ev["c10_14"].end + 2.0) * SR)
        gain[a:b] *= np.concatenate([np.linspace(1, 1.35, int(2.0 * SR)), np.full(b - a - int(2.0 * SR), 1.35)])
        c = int((ev["c11_1"].start - 0.2) * SR)
        gain[b:c] *= np.linspace(1.35, 1.0, max(1, c - b))
    music *= gain[:, None]
    # fades per spec: in 2 s, out 3 s
    fi, fo = int(2.0 * SR), int(3.0 * SR)
    music[:fi] *= np.linspace(0, 1, fi)[:, None]
    music[-fo:] *= np.linspace(1, 0, fo)[:, None]
    sf.write(out_path, music, SR, subtype="FLOAT")
    plan = [dict(section=k, piece=p, files=choices[p], gain_db=g, layer=l, start=round(a, 2), end=round(b, 2))
            for (k, p, g, l, a, b) in bounds]
    json.dump(plan, open(os.path.splitext(out_path)[0] + "_plan.json", "w"), ensure_ascii=False, indent=1)
    return out_path, total


if __name__ == "__main__":
    p, total = build(*sys.argv[1:6])
    print("music", p, round(total, 2))
