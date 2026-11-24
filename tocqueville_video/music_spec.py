"""Background music per 配乐规范.md (思想类: piano + soft strings, warm, quiet).

Three layers (铺底 / 推进 / 高潮) built from CC BY 4.0 library tracks (Kevin MacLeod, incompetech.com),
each section joined with 3 s equal-power crossfades, Memphis left silent (episode brief), the climax
lined up with the 2 s narration pause before "自由不是一句口号", and the piece's own ending decay
landing 2.5 s after the last line.

Writes /tmp/claude-0/work/stems/music.wav (48 kHz stereo, pre-sidechain) and music_credits.txt.
"""
import os, json
import numpy as np, soundfile as sf

SR = 48000
WORK = "/tmp/claude-0/work"
LIB = "/tmp/claude-0/music_lib/wav"
XF = 3.0

CREDIT = ('"{t}" Kevin MacLeod (incompetech.com)\n'
          'Licensed under Creative Commons: By Attribution 4.0 License\n'
          'http://creativecommons.org/licenses/by/4.0/\n')

_cache = {}


def track(name):
    if name not in _cache:
        x, sr = sf.read(f"{LIB}/{name}.wav", always_2d=True)
        assert sr == SR
        _cache[name] = x.astype(np.float32)
    return _cache[name]


def rms_db(x):
    return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-12)


def segment(name, t0, dur, target_db):
    """take `dur` seconds of track from t0, level its RMS (over audible part) to target_db"""
    x = track(name)
    a, b = int(t0 * SR), int((t0 + dur) * SR)
    seg = x[max(0, a):b].copy()
    if a < 0:
        seg = np.concatenate([np.zeros((-a, 2), np.float32), seg])
    if len(seg) < b - a:
        seg = np.concatenate([seg, np.zeros((b - a - len(seg), 2), np.float32)])
    m = seg.mean(1)
    loud = np.abs(m) > 1e-4
    g = target_db - rms_db(m[loud] if loud.any() else m)
    return seg * 10 ** (g / 20)


def movavg(x, w):
    """centred moving average via cumulative sums (O(n))"""
    c = np.concatenate([[0.0], np.cumsum(x)])
    n = len(x)
    i = np.arange(n)
    a = np.clip(i - w // 2, 0, n)
    b = np.clip(i + w // 2 + 1, 0, n)
    return (c[b] - c[a]) / np.maximum(1, b - a)


def place_xf(buf, seg, start, fade_in=XF, fade_out=XF):
    n = len(seg)
    fi, fo = int(fade_in * SR), int(fade_out * SR)
    env = np.ones(n, np.float32)
    if fi:
        env[:fi] = np.sin(np.linspace(0, np.pi / 2, fi)) ** 2 if fi else 1
    if fo:
        env[-fo:] = np.cos(np.linspace(0, np.pi / 2, fo)) ** 2
    i = int(start * SR)
    L = min(n, len(buf) - i)
    buf[i:i + L] += seg[:L] * env[:L, None]


def main():
    tl = json.load(open(f"{WORK}/timeline.json"))
    S = {s["id"]: (s["start"], s["end"]) for s in tl["scenes"]}
    C = {}
    for s in tl["scenes"]:
        for ln in s["lines"]:
            C[ln["id"]] = (ln["start"], ln["end"])
    total = tl["total"]
    buf = np.zeros((int((total + 1) * SR), 2), np.float32)
    used = []

    # plan: (track, track_offset, film_start, film_end, level_dB)
    plan = []
    # Layer 1 铺底: opening + background
    plan.append(("Water Lily", 0.0, 0.0, S["s01"][1] + XF / 2, -18.5))
    # Layer 1+: discovery chapters, warm and quiet
    plan.append(("Reawakening", 0.0, S["s02"][0] - XF / 2, S["s03"][1] + XF / 2, -17.5))
    plan.append(("Simple Duet", 0.0, S["s04"][0] - XF / 2, S["s04"][1] + XF / 2, -17.5))
    plan.append(("Immersed", 100.0, S["s05"][0] - XF / 2, S["s06"][1] + XF / 2, -17.5))
    # Layer 2 推进: France contrast + dark side (rhythm enters, slightly louder)
    trio_end = min(S["s07"][1] + XF / 2, S["s07"][0] - XF / 2 + 84.0)
    plan.append(("Trio for Piano Violin and Viola", 0.0, S["s07"][0] - XF / 2, trio_end, -16.0))
    if trio_end < S["s07"][1] + XF / 2 - 1:
        plan.append(("Promising Relationship", 25.0, trio_end - XF, S["s07"][1] + XF / 2, -16.0))
    plan.append(("Wounded", 30.0, S["s08"][0] - XF / 2, S["s08"][1], -16.0))
    # Memphis: no music (brief). Layer 3 高潮 + ending: Simple Duet's last section, its ending decay aligned
    final_end = C["s10_10"][1]
    music_end = final_end + 2.5
    track_end = 197.0
    s10a = S["s10"][0] + 1.0
    off = track_end - (music_end - s10a)
    plan.append(("Simple Duet", off, s10a, music_end, -15.5))

    for name, off_, a, b, lvl in plan:
        seg = segment(name, off_, b - a, lvl)
        fade_in = XF if a > 0.5 else 2.0           # spec: 2 s fade-in at the very start
        fade_out = XF
        if name == "Wounded":
            fade_out = 3.0                         # fade into Memphis' silence
        if name == "Simple Duet" and off_ > 50:
            fade_out = 3.0                         # spec: 3 s fade-out at the end
        place_xf(buf, seg, a, fade_in, fade_out)
        used.append(name)

    # slow partial level-follower: lift soft passages, hold back swells (+-6 dB, 70 %), so the music is
    # always felt under the voice but never jumps out in pauses
    tgt = np.full(len(buf), -99.0, np.float32)
    for name, off_, a, b, lvl in plan:
        i, j = int(a * SR), min(len(buf), int(b * SR))
        tgt[i:j] = np.maximum(tgt[i:j], lvl)
    win = int(3 * SR)
    mono = buf.mean(1).astype(np.float64)
    pw = movavg(mono ** 2, win)
    cur = 10 * np.log10(pw + 1e-12)
    g = np.clip(tgt - cur, -6, 6) * 0.7
    g[(cur < -60) | (tgt < -90)] = 0.0
    g = movavg(g.astype(np.float64), int(4 * SR)).astype(np.float32)
    buf *= (10 ** (g / 20))[:, None]

    # climax: let the full piece come up during the narration pause before "自由不是一句口号"
    p0, p1 = C["s10_07"][1], C["s10_08"][0]
    i0, i1 = int((p0 - 0.3) * SR), int((p1 + 1.0) * SR)
    ramp = np.ones(i1 - i0, np.float32)
    k = int(0.6 * SR)
    ramp[:k] = np.linspace(1, 1.6, k); ramp[k:-k] = 1.6; ramp[-k:] = np.linspace(1.6, 1, k)
    buf[i0:i1] *= ramp[:, None]

    os.makedirs(f"{WORK}/stems", exist_ok=True)
    sf.write(f"{WORK}/stems/music.wav", buf, SR, subtype="FLOAT")
    with open(f"{WORK}/stems/music_credits.txt", "w") as f:
        f.write("配乐 / Music:\n")
        for t in dict.fromkeys(used):
            f.write(CREDIT.format(t=t) + "\n")
    print("music stem", round(len(buf) / SR, 1), "s;", ", ".join(dict.fromkeys(used)))


if __name__ == "__main__":
    main()
