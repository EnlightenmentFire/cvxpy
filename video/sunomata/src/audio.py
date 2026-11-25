"""全部自生成音频：配乐（太鼓、尺八式笛、法螺、弦乐铺底、拨弦）+ 音效（雨、急流、木槌、火箭、雷）+ 旁白拼轨 + 混音。
python audio.py  → WORK/stems/{voice,music,sfx}.wav、mix.wav（有配乐）、mix_nomusic.wav
配乐只用 numpy 合成，无任何第三方采样，可商用。
"""
import os, sys, json, subprocess, re
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, oaconvolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

WORK = "/tmp/claude-0/work"
ST = f"{WORK}/stems"
SR = 48000
R = np.random.default_rng(42)


def env(n, a, r, sus=1.0):
    e = np.ones(n) * sus
    na, nr = int(a * SR), int(r * SR)
    if na: e[:na] = np.linspace(0, sus, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e


def lp(x, f, o=2):
    return sosfilt(butter(o, f, "low", fs=SR, output="sos"), x)


def hp(x, f, o=2):
    return sosfilt(butter(o, f, "high", fs=SR, output="sos"), x)


def bp(x, f0, f1, o=2):
    return sosfilt(butter(o, [f0, f1], "band", fs=SR, output="sos"), x)


def add(buf, x, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i >= len(buf) or i + len(x) <= 0:
        return
    if i < 0:
        x = x[-i:]; i = 0
    x = x[:len(buf) - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[i:i + len(x), 0] += x * g * l * 1.414
    buf[i:i + len(x), 1] += x * g * r * 1.414


def hz(midi):
    return 440 * 2 ** ((midi - 69) / 12)


# ---------- 乐器 ----------
def taiko(big=1.0):
    n = int(1.6 * SR); t = np.arange(n) / SR
    f = 52 + 40 * np.exp(-t * 18) * big
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * (3.2 / big))
    skin = lp(R.normal(0, 1, n), 900) * np.exp(-t * 30)
    return np.tanh(1.6 * (body + 0.5 * skin)) * 0.9


def ka():
    n = int(0.12 * SR); t = np.arange(n) / SR
    return bp(R.normal(0, 1, n), 1500, 4000) * np.exp(-t * 60) * 0.5


def saw(f, n, det=0.0):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for d in (-det, 0, det):
        ph = (f * (1 + d) * t + R.uniform()) % 1
        out += 2 * ph - 1
    return out / 3


def pad(notes, dur, a=2.0, r=2.5, bright=1200):
    n = int(dur * SR)
    x = sum(saw(hz(m), n, 0.004) for m in notes) / len(notes)
    x = lp(x, bright, 2)
    return x * env(n, a, r)


def strings_trem(notes, dur, rate=12):
    n = int(dur * SR); t = np.arange(n) / SR
    x = sum(saw(hz(m), n, 0.003) for m in notes) / len(notes)
    x = lp(x, 2200) * (0.6 + 0.4 * np.abs(np.sin(np.pi * rate * t)))
    return x * env(n, 0.3, 0.8)


def shaku(m, dur, bend=True):
    n = int(dur * SR); t = np.arange(n) / SR
    f0 = hz(m) * (1 - 0.03 * np.exp(-t * 6) if bend else 1)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t / 0.8, 0, 1)
    ph = 2 * np.pi * np.cumsum(f0 * vib) / SR
    tone = np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)
    breath = bp(R.normal(0, 1, n), hz(m) * 1.5, min(9000, hz(m) * 8)) * 0.35
    e = env(n, 0.25, min(0.8, dur * 0.4)) * (1 + 0.2 * np.sin(2 * np.pi * 0.7 * t))
    return (tone * 0.7 + breath) * e


def conch(dur, m=45):
    n = int(dur * SR); t = np.arange(n) / SR
    f = hz(m) * (1 + 0.012 * np.clip(t / 1.2, 0, 1)) * (1 + 0.004 * np.sin(2 * np.pi * 4.5 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sign(np.sin(ph)) * 0.5 + np.sin(ph)
    x = bp(x, 200, 1400) + 0.3 * bp(x, 600, 900)
    return np.tanh(2 * x) * env(n, 0.6, 1.0) * 0.6


def pluck(m, dur=2.5, damp=0.996):
    n = int(dur * SR); p = int(SR / hz(m))
    buf = R.uniform(-1, 1, p); out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = damp * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    return lp(out, 5000) * env(n, 0.002, 0.4)


def piano(m, dur=3.0):
    n = int(dur * SR); t = np.arange(n) / SR
    f = hz(m)
    x = sum(np.sin(2 * np.pi * f * k * t * (1 + 0.0004 * k * k)) * (0.6 ** (k - 1)) * np.exp(-t * (1.2 + 0.8 * k)) for k in range(1, 7))
    return x * env(n, 0.004, 0.6) * 0.5


def reverb(x, secs=2.6, mix=0.3):
    n = int(secs * SR); t = np.arange(n) / SR
    ir = R.normal(0, 1, (n, 2)) * np.exp(-t * 6.9 / secs)[:, None]
    ir[:, 0] = lp(ir[:, 0], 6000); ir[:, 1] = lp(ir[:, 1], 6000)
    ir /= np.sqrt((ir ** 2).sum(0))
    out = x * (1 - mix)
    for c in range(2):
        out[:, c] += mix * oaconvolve(x[:, c], ir[:, c].astype(np.float32))[:len(x)].astype(np.float32)
    return out


# ---------- 音效 ----------
def noise_bed(dur, kind):
    n = int(dur * SR)
    w = R.normal(0, 1, n)
    if kind == "rain":
        x = hp(lp(w, 9000), 1200) * 0.5
        drops = np.zeros(n); idx = R.integers(0, n, int(dur * 220))
        drops[idx] = R.uniform(0.3, 1, len(idx))
        x += bp(drops, 2000, 7000) * 0.6
    elif kind == "river":
        b = np.cumsum(w); b -= lp(b, 8); b /= np.abs(b).max() + 1e-9
        x = lp(b, 700) * 1.2 + bp(w, 300, 1500) * 0.15 * (1 + 0.5 * np.sin(np.arange(n) / SR * 0.7))
    elif kind == "wind":
        x = bp(w, 200, 900) * (0.6 + 0.4 * np.sin(np.arange(n) / SR * 0.4))
    return x


def mallet():
    n = int(0.35 * SR); t = np.arange(n) / SR
    thud = np.sin(2 * np.pi * (110 + 60 * np.exp(-t * 40)) * t) * np.exp(-t * 22)
    wood = bp(R.normal(0, 1, n), 600, 1600) * np.exp(-t * 45) * 0.8
    return (thud + wood) * 0.8


def whoosh(dur=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    x = R.normal(0, 1, n)
    out = np.zeros(n); seg = 2048
    for i in range(0, n, seg):
        f = 400 + 3000 * np.sin(np.pi * i / n)
        out[i:i + seg] = bp(x[i:i + seg], f * 0.7, f * 1.3)[:len(out[i:i + seg])]
    return out * np.sin(np.pi * t / dur) ** 2 * 0.6


def thunder(dur=4.0):
    n = int(dur * SR); t = np.arange(n) / SR
    b = np.cumsum(R.normal(0, 1, n)); b -= lp(b, 5); b /= np.abs(b).max()
    return lp(b, 300) * np.exp(-t * 1.2) * (1 + 0.6 * np.sin(t * 9)) * 1.6


def chop():
    n = int(0.25 * SR); t = np.arange(n) / SR
    return (bp(R.normal(0, 1, n), 800, 3000) * np.exp(-t * 50) + np.sin(2 * np.pi * 180 * t) * np.exp(-t * 30)) * 0.7


def stamp_hit():
    n = int(0.6 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * (70 + 50 * np.exp(-t * 30)) * t) * np.exp(-t * 9) + lp(R.normal(0, 1, n), 1500) * np.exp(-t * 40) * 0.5)


def crowd(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n)
    for f in (500, 800, 1100, 1600):
        x += bp(R.normal(0, 1, n), f * 0.85, f * 1.15) * (0.5 + 0.5 * np.sin(t * R.uniform(1, 3) + R.uniform(0, 6)))
    return x * 0.35 * env(n, 0.8, 1.0)


# ---------- 时间线 ----------
def TL():
    tl = json.load(open(f"{WORK}/timeline.json"))
    L = {l["id"]: l for l in tl["lines"]}
    sc = {}
    for l in tl["lines"]:
        sc.setdefault(l["scene"], l["start"])
    return tl, L, sc


SCALE = [50, 51, 55, 57, 58, 62, 63, 67, 69, 70]  # D 都节音阶


def music():
    tl, L, sc = TL()
    T = tl["total"]
    buf = np.zeros((int((T + 4) * SR), 2), np.float32)
    s = lambda i: L[i]["start"]
    # ---- A 钩子：太鼓接黎明；之后悬疑铺底 ----
    add(buf, taiko(1.4), s("A02") - 0.15, 0.9)
    add(buf, taiko(1.0), s("A02") - 0.55, 0.5, -0.3)
    add(buf, stamp_hit(), s("A02") + 1.75, 0.7)
    add(buf, pad([38, 45], s("A05") - s("A02") + 4, 2, 3, 500), s("A02"), 0.28)
    # 地层：每层一声低鼓
    for i in range(4):
        add(buf, taiko(0.8), s("A06") - 0.2 + i * 0.75, 0.45, (i - 1.5) * 0.3)
    add(buf, pad([38, 45, 50], s("A11") - s("A05") + 3, 3, 3, 700), s("A05"), 0.22)
    for k, (m, d) in enumerate([(62, 3.0), (63, 2.0), (62, 4.0), (57, 3.5), (58, 2.5), (57, 4.5)]):
        add(buf, shaku(m, d), s("A05") + 2 + k * 6.5, 0.22, 0.2)
    add(buf, pad([38, 45, 53], s("B01") - s("A11") + 3, 2, 3, 900), s("A11"), 0.26)
    add(buf, taiko(1.3), s("A13") + 0.2, 0.7)
    # ---- B 战略：弦乐+稳定鼓点 ----
    b0, b1 = s("B01"), sc["C"]
    add(buf, pad([38, 45, 50, 57], b1 - b0 + 3, 3, 3, 900), b0, 0.2)
    beat = 60 / 72
    t = b0 + 1
    i = 0
    while t < b1 - 2:
        quiet = s("B12") - 1 < t < b1
        if not quiet:
            add(buf, taiko(0.7 if i % 4 else 1.0), t, 0.32 if i % 4 else 0.45, 0)
            if i % 2:
                add(buf, ka(), t + beat / 2, 0.25, 0.4)
        t += beat; i += 1
    for k, m in enumerate([57, 58, 62, 63, 62, 57, 55, 57]):
        add(buf, shaku(m, 3.5), s("B03") + k * 7.5, 0.16, -0.2)
    for i_, lid in enumerate(["B12", "B15"]):
        add(buf, taiko(1.2), s(lid) - 0.1, 0.5)
    # ---- C 传说一二层：拨弦+尺八，轻 ----
    c0, c1 = sc["C"], sc["D"]
    add(buf, pad([38, 50, 57], c1 - c0 + 2, 3, 3, 700), c0, 0.2)
    t = c0 + 0.5; k = 0
    while t < c1 - 2:
        add(buf, pluck(SCALE[(k * 3) % 7] + 12, 2.0), t, 0.16, (-0.4, 0.4)[k % 2])
        t += 1.6 if k % 4 != 3 else 3.2; k += 1
    for lid in ("C01", "C07"):
        add(buf, taiko(1.2), s(lid) - 0.1, 0.55)
    for lid in ("C10", "C11", "C12"):
        add(buf, taiko(0.9), s(lid) + 1.0, 0.4)
    # ---- D 高燃：鼓点加速、法螺、弦乐震音 ----
    d0, d1 = sc["D"], sc["E"]
    peak = s("D10"); dawn = s("D11") + 1.0
    add(buf, conch(4.0), d0 + 0.2, 0.5, -0.3)
    add(buf, conch(5.0, 43), s("D07") - 0.5, 0.45, 0.3)
    add(buf, strings_trem([38, 45, 50, 53], dawn - s("D05") + 1, 10), s("D05"), 0.26)
    t = d0 + 1.0; i = 0
    while t < dawn:
        prog = np.clip((t - d0) / (peak - d0), 0, 1)
        bpm = 84 + 80 * prog
        bt = 60 / bpm
        g = 0.35 + 0.3 * prog
        add(buf, taiko(1.1 if i % 4 == 0 else 0.75), t, g * (1.15 if i % 4 == 0 else 0.85), (-0.25, 0.25)[i % 2])
        if prog > 0.3:
            add(buf, taiko(0.6), t + bt / 2, g * 0.55, (0.3, -0.3)[i % 2])
        if prog > 0.55:
            add(buf, ka(), t + bt * 0.75, 0.3, 0.5)
        t += bt; i += 1
    for k in range(4):
        add(buf, taiko(1.5), peak - 0.4 + k * 0.33, 0.75)
    add(buf, conch(3.5, 47), peak + 0.2, 0.55)
    add(buf, pad([38, 45, 50, 54, 57], d1 - dawn + 3, 0.5, 4, 2000), dawn, 0.32)  # 黎明大和弦（D 大）
    add(buf, taiko(1.6), dawn, 0.9)
    add(buf, pad([38, 45, 50], d1 - s("D12") + 2, 2, 3, 700), s("D12"), 0.18)
    # ---- E 证据审查：冷静的钢琴/拨弦 ----
    e0, e1 = sc["E"], sc["F"]
    add(buf, pad([38, 45], e1 - e0 + 2, 3, 3, 500), e0, 0.18)
    t = e0 + 1; k = 0
    seq = [62, 57, 58, 55, 62, 57, 53, 55]
    while t < e1 - 2:
        add(buf, piano(seq[k % 8], 3.0), t, 0.2, (-0.3, 0.3)[k % 2])
        if k % 4 == 0:
            add(buf, piano(seq[k % 8] - 12, 4.0), t, 0.12)
        t += 2.2 if k % 2 == 0 else 2.6; k += 1
    add(buf, taiko(1.0), s("E15") - 0.3, 0.4)
    # ---- F：弦乐温暖一些 ----
    f0, f1 = sc["F"], sc["G"]
    add(buf, pad([41, 48, 53, 57], f1 - f0 + 2, 3, 3, 900), f0, 0.2)
    for k, m in enumerate([65, 62, 60, 57, 60, 62]):
        add(buf, shaku(m, 4.0), f0 + 3 + k * 6, 0.14, 0.2)
    t = s("F07")
    for k in range(6):
        add(buf, taiko(0.9 + 0.1 * k), t + k * 0.6, 0.35 + 0.05 * k)
    # ---- G 收束：庄重升华 ----
    g0 = sc["G"]
    add(buf, pad([38, 45, 50, 53], s("G05") - g0 + 3, 3, 3, 800), g0, 0.2)
    add(buf, pad([38, 45, 50, 54, 57, 62], s("G09") - s("G05") + 2, 3, 3, 1400), s("G05"), 0.26)
    add(buf, taiko(1.5), s("G06") - 0.3, 0.6)
    for k, m in enumerate([62, 66, 69, 67, 66, 62]):
        add(buf, shaku(m, 3.5, bend=False), s("G06") + 1 + k * 3.3, 0.14, 0.1)
    add(buf, conch(4.0, 45), s("G09") + 1.5, 0.35)
    tg = s("G09")
    for k in range(8):
        add(buf, taiko(1.0), tg + 2.5 + k * 0.5, 0.35 + 0.04 * k)
    add(buf, taiko(1.7), T - 3.4, 0.8)
    add(buf, pad([38, 45, 50, 57], 4.5, 0.05, 3.5, 1600), T - 3.4, 0.3)
    buf = reverb(buf, 2.8, 0.32)
    fade = np.ones(len(buf)); fe = int((T + 0.5) * SR)
    fade[fe - int(1.5 * SR):fe] = np.linspace(1, 0, int(1.5 * SR)); fade[fe:] = 0
    return buf * fade[:, None]


def sfx():
    tl, L, sc = TL()
    T = tl["total"]
    buf = np.zeros((int((T + 4) * SR), 2), np.float32)
    s = lambda i: L[i]["start"]
    # 开场：夜雨急流，木槌越来越密，0.0 秒即有声
    e = s("A02") + 2.0
    rv = noise_bed(e + 1, "river"); rn = noise_bed(e + 1, "rain")
    fade = env(len(rv), 0.02, 1.0)
    add(buf, rv * fade, 0, 0.55); add(buf, rn * fade, 0, 0.22)
    t = 0.05; gap = 0.55
    while t < s("A02") - 0.2:
        add(buf, mallet(), t, 0.55, R.uniform(-0.6, 0.6))
        t += gap; gap = max(0.13, gap * 0.9)
    # 台风段
    a8, a11 = s("A08"), s("A11")
    seg = a11 - a8 + 0.5
    add(buf, noise_bed(seg, "rain") * env(int(seg * SR), 0.8, 1.0), a8 - 0.4, 0.3)
    add(buf, noise_bed(seg, "wind") * env(int(seg * SR), 1.0, 1.0), a8 - 0.4, 0.25)
    add(buf, thunder(), a8 + 0.5, 0.5)
    add(buf, stamp_hit(), s("A10") + 0.45, 0.6)
    # 盖章/失败
    for lid, off in (("C10", 0.9), ("C10", 3.1), ("C12", 0.9)):
        add(buf, stamp_hit(), s(lid) + off, 0.45)
    # 武功夜话：伐木、放排、夜战
    d5, d6, d7, d11 = s("D05"), s("D06"), s("D07"), s("D11")
    t = d5 + 0.2
    while t < d6:
        add(buf, chop(), t, 0.45, R.uniform(-0.5, 0.5)); t += R.uniform(0.35, 0.6)
    seg = d11 + 3 - d6
    add(buf, noise_bed(seg, "river") * env(int(seg * SR), 1, 2), d6, 0.4)
    add(buf, noise_bed(seg, "rain") * env(int(seg * SR), 1, 2), d6, 0.16)
    t = d7 + 0.3
    while t < d11 + 0.5:
        add(buf, mallet(), t, 0.4, R.uniform(-0.7, 0.7)); t += R.uniform(0.18, 0.4)
    d8 = s("D08")
    seg = d11 + 1.5 - d8
    add(buf, crowd(seg), d8, 0.35)
    t = d8 + 0.2
    while t < d11:
        add(buf, whoosh(R.uniform(0.7, 1.1)), t, 0.35, R.uniform(-0.8, 0.8)); t += R.uniform(0.4, 0.9)
    # 小转场：每个场景开头一声轻扫
    for k in "BCDEFG":
        add(buf, whoosh(0.9) * 0.6, sc[k] - 1.0, 0.25)
    return buf


def voice():
    tl, L, sc = TL()
    buf = np.zeros((int((tl["total"] + 4) * SR), 2), np.float32)
    for l in tl["lines"]:
        p = f"{WORK}/tts/proc/{l['id']}.wav"
        if os.path.exists(p):
            x, _ = sf.read(p)
            add(buf, x.astype(np.float64), l["start"], 1.0)
    return buf


def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1])
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
    return I, float(tp[-1]) if tp else None


def rms_db(x):
    return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-12)


def duck(music_, v, depth_db=6.0):
    """旁白处音乐压低 depth_db，旁白停顿处回升（≈ 侧链，攻 80 ms 释 600 ms）。"""
    n = int(0.02 * SR)
    m = len(v) // n
    e = np.sqrt((v[:m * n].mean(1).reshape(m, n) ** 2).mean(1))
    on = (20 * np.log10(e + 1e-9) > -40).astype(float)
    g = np.zeros(m); cur = 0
    for i in range(m):
        tgt = on[i]
        k = 0.25 if tgt > cur else 0.033
        cur += (tgt - cur) * k; g[i] = cur
    gain = 10 ** (-depth_db * np.repeat(g, n) / 20)
    gain = np.concatenate([gain, np.full(len(music_) - len(gain), gain[-1])])[:len(music_)]
    return music_ * gain[:, None], np.repeat(g, n)


def main():
    os.makedirs(ST, exist_ok=True)
    v = voice(); m = music(); fx = sfx()
    L = min(len(v), len(m), len(fx))
    v, m, fx = v[:L], m[:L], fx[:L]
    # 电平：旁白段落里，音乐比旁白低约 22 dB；音效比旁白低约 12 dB（开场声音钩子例外，无旁白）
    speech = np.abs(v[:, 0]) > 1e-4
    vr = rms_db(v[speech]) if speech.any() else -18
    md, g = duck(m, v, 6.0)
    on = g[:L] > 0.5 if len(g) >= L else np.pad(g, (0, L - len(g)))[:L] > 0.5
    mr = rms_db(md[on]) if on.any() else rms_db(md)
    md *= 10 ** ((vr - 22 - mr) / 20)
    fr = rms_db(fx[np.abs(fx[:, 0]) > 1e-4])
    fx *= 10 ** ((vr - 14 - fr) / 20)
    for name, x in (("voice", v), ("music", md), ("sfx", fx)):
        sf.write(f"{ST}/{name}.wav", x.astype(np.float32), SR, subtype="FLOAT")
    for name, x in (("mix_pre", v + md + fx), ("mixnm_pre", v + fx)):
        sf.write(f"{ST}/{name}.wav", x.astype(np.float32), SR, subtype="FLOAT")
        I, tp = lufs(f"{ST}/{name}.wav")
        gain = -15.0 - I
        y = (v + (md if name == "mix_pre" else 0) + fx) * 10 ** (gain / 20)
        # 真峰值限制到 -1.5 dBTP：软限幅
        lim = 10 ** (-1.8 / 20)
        y = np.where(np.abs(y) > lim * 0.8, np.sign(y) * (lim * 0.8 + (lim * 0.2) * np.tanh((np.abs(y) - lim * 0.8) / (lim * 0.2))), y)
        out = f"{ST}/{'mix' if name == 'mix_pre' else 'mix_nomusic'}.wav"
        sf.write(out, y.astype(np.float32), SR, subtype="FLOAT")
        print(out, lufs(out))
    print(f"voice rms {vr:.1f} dB; music under speech {rms_db(md[on]) - vr:.1f} dB rel; music in pauses {rms_db(md[~on & (np.arange(L) > 5 * SR)]) - vr:.1f} dB rel")


if __name__ == "__main__":
    main()
