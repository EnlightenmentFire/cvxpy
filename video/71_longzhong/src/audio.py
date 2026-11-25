# -*- coding: utf-8 -*-
"""音频：旁白拼接 + 原创合成配乐（古琴式拨弦、箫、弦乐铺底、战鼓）+ 音效（竹林风、木门吱呀、火）。
全部由本脚本用 numpy 合成，无外部音乐素材，可商用。输出：
  narration.wav（旁白干声） music.wav（配乐） sfx.wav（音效） mix.wav（成片混音） mix_nomusic.wav（无配乐版）
"""
import os, sys, json, subprocess
import numpy as np, soundfile as sf
from scipy import signal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeline import TL, PROC, W as WORK

SR = 48000
T = TL(); N = int((T.total + 0.6) * SR)
S, E = T.S, T.E
def SC(k): return T.sc[k]
OUT = f'{WORK}/audio'; os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)


def add(buf, t0, x, g=1.0):
    i = int(t0 * SR)
    if i >= len(buf) or i + len(x) <= 0: return
    if i < 0: x = x[-i:]; i = 0
    n = min(len(x), len(buf) - i); buf[i:i + n] += x[:n] * g


# ───────── 旁白 ─────────
def narration():
    out = np.zeros(N, np.float32)
    for d in T.L:
        p = f"{PROC}/{d['id']}.wav"
        if not os.path.exists(p): continue
        w, sr = sf.read(p, dtype='float32'); assert sr == SR
        add(out, S(d['id']), w)
    return out


# ───────── 乐器 ─────────
A4 = 440.0
SCALE = [0, 3, 5, 7, 10]       # 羽调式五声（A C D E G）
def midi_f(m): return A4 * 2 ** ((m - 69) / 12)
def pent(base, k):
    o, r = divmod(k, 5); return base + 12 * o + SCALE[r]


def qin(f, dur=4.5, g=1.0, slide=0.0):
    """古琴式拨弦：带非谐的衰减泛音 + 拨奏噪声；slide 为吟猱式滑音（半音数）。"""
    n = int(dur * SR); t = np.arange(n) / SR
    ff = f * 2 ** (slide * np.clip((t - 0.25) / 0.5, 0, 1) / 12) if slide else f
    ph = 2 * np.pi * np.cumsum(np.broadcast_to(ff, t.shape)) / SR
    y = np.zeros(n)
    for h in range(1, 9):
        inh = 1 + 0.0009 * h * h
        y += (0.85 ** (h - 1)) / h ** 0.6 * np.sin(ph * h * inh + h) * np.exp(-t * (0.9 + 0.55 * h))
    nz = signal.lfilter(*signal.butter(2, [800 / (SR / 2), 4000 / (SR / 2)], 'band'), rng.normal(0, 1, n)) * np.exp(-t * 60) * 0.25
    y = (y + nz) * np.minimum(1, t * 300)
    return (y * g * 0.22).astype(np.float32)


def harmonic(f, dur=3.0, g=1.0):
    """泛音：纯净高音，快衰减。"""
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) * np.exp(-t * 1.6) + 0.2 * np.sin(4 * np.pi * f * t) * np.exp(-t * 3)
    return (y * np.minimum(1, t * 200) * g * 0.12).astype(np.float32)


def xiao(f, dur=4.0, g=1.0):
    """箫：带颤音的近正弦 + 气声。"""
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.0 * t) * np.clip((t - 0.6) / 0.8, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    y = np.sin(ph) + 0.12 * np.sin(2 * ph) + 0.05 * np.sin(3 * ph)
    br = signal.lfilter(*signal.butter(2, [f * 0.8 / (SR / 2), min(0.95, f * 3 / (SR / 2))], 'band'), rng.normal(0, 1, n)) * 0.35
    env = np.minimum(1, t / 0.35) * np.minimum(1, (dur - t) / 0.8).clip(0, 1)
    return ((y + br) * env * g * 0.10).astype(np.float32)


def pad(fs, dur=8.0, g=1.0, bright=1.0):
    """弦乐铺底：多声部失谐锯齿波（加法合成）+ 低通，慢起慢收。"""
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.zeros(n)
    for f in fs:
        for det in (-0.12, 0.0, 0.11):
            fd = f * 2 ** (det / 12)
            for h in range(1, 14):
                if fd * h > 5000 * bright: break
                y += np.sin(2 * np.pi * fd * h * t + h * 1.3 + det) / h * (0.9 ** h)
    y = signal.lfilter(*signal.butter(2, min(0.9, 2200 * bright / (SR / 2))), y)
    env = np.minimum(1, t / 2.0) * np.clip((dur - t) / 2.5, 0, 1)
    return (y * env * g * 0.018 / max(1, len(fs) ** 0.5)).astype(np.float32)


def drum(g=1.0, f0=55, dur=2.4):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (1 + 1.5 * np.exp(-t * 26)); ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * 3.0) + 0.4 * np.sin(ph * 1.52) * np.exp(-t * 6)
    skin = signal.lfilter(*signal.butter(2, [160 / (SR / 2), 1500 / (SR / 2)], 'band'), rng.normal(0, 1, n)) * np.exp(-t * 28) * 0.5
    return ((body + skin) * g * 0.5).astype(np.float32)


def reverb(x, sec=2.8, wet=0.32):
    n = int(sec * SR); t = np.arange(n) / SR
    ir = rng.normal(0, 1, n) * np.exp(-t * 6.9 / sec)
    ir = signal.lfilter(*signal.butter(1, 5000 / (SR / 2)), ir); ir[:int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
    ir /= np.sqrt((ir ** 2).sum())
    y = signal.oaconvolve(x, ir)[:len(x)]
    return (x * (1 - wet) + y * wet * 2.2).astype(np.float32)


# ───────── 配乐编排 ─────────
def music():
    out = np.zeros(N, np.float32)
    r = np.random.default_rng(3)

    def qin_phrase(t0, t1, density=0.45, base=45, g=1.0, harm=0.2):
        t = t0; k = 5
        while t < t1 - 1:
            k = int(np.clip(k + r.choice([-2, -1, -1, 0, 1, 1, 2]), 2, 11))
            f = midi_f(pent(base, k))
            if r.random() < harm: add(out, t, harmonic(f * 2, 3.0, g))
            else: add(out, t, qin(f, 4.5, g * r.uniform(0.75, 1.0), slide=r.choice([0, 0, 0, 1, -1, 2])))
            if r.random() < 0.3: add(out, t + 0.18, qin(midi_f(pent(base, k - 2)), 4.0, g * 0.6))
            t += r.uniform(1.2, 2.6) / density
    def xiao_line(t0, t1, base=57, g=1.0):
        t = t0 + r.uniform(0, 2); k = 5
        while t < t1 - 3:
            k = int(np.clip(k + r.choice([-1, 0, 1, 2, -2]), 2, 9)); d = r.uniform(3.0, 5.5)
            add(out, t, xiao(midi_f(pent(base, k)), d, g)); t += d + r.uniform(1.5, 4.0)
    def pads(t0, t1, chords, g=1.0, bright=1.0, step=8.0):
        t = t0; i = 0
        while t < t1 - 2:
            d = min(step + 2.5, t1 - t)
            add(out, t, pad([midi_f(m) for m in chords[i % len(chords)]], d, g, bright)); t += step; i += 1
    def drums(t0, t1, period=2.0, g=1.0, f0=55):
        t = t0
        while t < t1:
            add(out, t, drum(g, f0)); add(out, t + period * 0.75, drum(g * 0.45, f0 * 1.3)); t += period

    CH_CALM = [(45, 52, 57), (43, 50, 55), (41, 48, 57), (40, 47, 55)]
    CH_WAR = [(33, 45, 52, 57), (31, 43, 50, 55), (29, 41, 48, 57), (28, 40, 47, 55)]
    end = T.total
    # 开场到钩子结束：古琴 + 箫
    qin_phrase(0.3, SC('wander')[0], 0.55, g=1.0)
    xiao_line(4.0, SC('wander')[0], g=0.9)
    pads(0.0, SC('wander')[0], CH_CALM, 0.6)
    # 新野、史料段：古琴稀疏 + 铺底
    qin_phrase(SC('wander')[0], SC('lz0')[0], 0.32, g=0.8, harm=0.3)
    pads(SC('wander')[0], SC('lz0')[0], CH_CALM, 0.7)
    xiao_line(SC('src1')[0], SC('src3')[0], g=0.6)
    # 隆中对：弦乐推起来 + 鼓
    pads(SC('lz0')[0], SC('rank')[1], CH_WAR, 1.2, bright=1.4, step=6.0)
    qin_phrase(SC('lz0')[0], SC('rank')[1], 0.5, base=45, g=0.9)
    drums(SC('lz1')[0], SC('rank')[0], 2.0, 0.8)
    for k in ('d03', 'd05', 'd08', 'd10', 'd11', 'd12'):
        add(out, S(k) - 0.05, drum(1.5, 48, 3.0))
    # 关系网、鱼水：回到古琴 + 箫
    qin_phrase(SC('ana3')[0], SC('chibi')[0], 0.4, g=0.8, harm=0.3)
    xiao_line(SC('fish')[0], SC('chibi')[0], g=0.7)
    pads(SC('ana3')[0], SC('chibi')[0], CH_CALM, 0.7)
    # 赤壁：鼓 + 弦乐
    drums(SC('chibi')[0], SC('chibi')[1] - 1.0, 1.0, 1.0, 50)
    pads(SC('chibi')[0], SC('chibi')[1], CH_WAR, 1.4, bright=1.6, step=5.0)
    # 收束
    pads(SC('end')[0], end, CH_CALM, 0.8, step=9.0)
    qin_phrase(SC('end')[0], end - 2.0, 0.4, g=0.9, harm=0.35)
    xiao_line(SC('end')[0], end - 4.0, g=0.8)
    out = reverb(out)
    # 段落之间 1.5 秒交叉的整体包络：尾声淡出
    fe = int(3.0 * SR); out[-fe:] *= np.linspace(1, 0, fe)
    return out


# ───────── 音效 ─────────
def wind(dur, g=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    nz = rng.normal(0, 1, n)
    lo = signal.lfilter(*signal.butter(2, [180 / (SR / 2), 900 / (SR / 2)], 'band'), nz)
    hi = signal.lfilter(*signal.butter(2, [2500 / (SR / 2), 7000 / (SR / 2)], 'band'), rng.normal(0, 1, n))
    mod = 0.55 + 0.45 * np.sin(2 * np.pi * 0.17 * t + 1) * np.sin(2 * np.pi * 0.05 * t)
    rus = np.clip(signal.lfilter([1], [1, -0.9995], rng.normal(0, 1, n)) / 60, 0, None)   # 竹叶沙沙的起伏
    y = lo * mod * 0.6 + hi * (0.2 + rus) * 0.35
    return (y * g * 0.12).astype(np.float32)


def creak(dur=1.1, g=1.0):
    """木门吱呀：一串变周期的摩擦脉冲激励共鸣体。"""
    n = int(dur * SR); t = np.arange(n) / SR
    f = 95 + 70 * np.sin(np.pi * t / dur) + 25 * np.sin(2 * np.pi * 3.1 * t)
    ph = np.cumsum(f) / SR
    pulses = (np.diff(np.floor(ph), prepend=0) > 0).astype(float) * (0.6 + 0.4 * rng.random(n))
    y = np.zeros(n)
    for fr, q in ((620, 18), (1350, 22), (2300, 26)):
        b, a = signal.iirpeak(fr / (SR / 2), q); y += signal.lfilter(b, a, pulses)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.6
    y = y * env * g * 0.9
    y = np.tanh(y / (np.abs(y).max() + 1e-9) * 2.0) * 0.5
    return y.astype(np.float32)


def crackle(dur, g=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    y = signal.lfilter(*signal.butter(2, [300 / (SR / 2), 2000 / (SR / 2)], 'band'), rng.normal(0, 1, n)) * 0.3
    pops = (rng.random(n) < 30 / SR) * rng.normal(0, 3, n)
    y += signal.lfilter(*signal.butter(2, 3000 / (SR / 2), 'high'), pops)
    env = np.minimum(1, t / 0.6) * np.clip((dur - t) / 1.5, 0, 1)
    return (y * env * g * 0.18).astype(np.float32)


def whoosh(g=1.0, dur=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    y = signal.lfilter(*signal.butter(2, [400 / (SR / 2), 2400 / (SR / 2)], 'band'), rng.normal(0, 1, n))
    return (y * np.sin(np.pi * t / dur) ** 2 * g * 0.15).astype(np.float32)


def sfx():
    out = np.zeros(N, np.float32)
    add(out, 0.0, wind(SC('hook1')[0] + 2.0, 1.6))      # 开场：竹林风声（第一帧即响）
    add(out, 0.02, creak(1.25, 0.9))                     # 木门吱呀
    add(out, SC('lz0')[0], wind(SC('lz1')[0] - SC('lz0')[0] + 1.0, 0.8))
    add(out, SC('end')[0], wind(SC('takeaway')[0] - SC('end')[0] + 1.0, 0.8))
    for k in ('wander', 'xinye', 'caonorth', 'lz1', 'chibi', 'next'):
        add(out, SC(k)[0] - 0.5, whoosh(0.8))
    add(out, S('f03') + 4.2, crackle(6.0, 1.0))
    # 首尾淡
    f = int(0.004 * SR); out[:f] *= np.linspace(0, 1, f)
    return out


def lufs(x):
    import pyloudnorm as pyln
    return pyln.Meter(SR).integrated_loudness(x.astype(np.float64))


def duck_env(nar, att=0.08, rel=0.6):
    """旁白包络：说话时 1，停顿处随释放时间回落到 0。"""
    hop = 480; m = len(nar) // hop
    e = np.sqrt((nar[:m * hop].reshape(m, hop) ** 2).mean(1)); on = (20 * np.log10(e + 1e-9) > -45).astype(float)
    out = np.zeros(m); v = 0.0
    ka = 1 - np.exp(-hop / (att * SR)); kr = 1 - np.exp(-hop / (rel * SR))
    for i in range(m):
        v += (on[i] - v) * (ka if on[i] > v else kr); out[i] = v
    return np.interp(np.arange(len(nar)), np.arange(m) * hop + hop / 2, out).astype(np.float32)


def main():
    nar = narration(); mus = music(); fx = sfx()
    Ln = lufs(nar)
    # 配乐在人声下约 22 dB（说话时），停顿处抬 5 dB
    sp = duck_env(nar) > 0.5
    Lm = lufs(mus[sp[:len(mus)]]) if sp.any() else lufs(mus)
    g_m = 10 ** ((Ln - 22.0 - Lm) / 20)
    env = duck_env(nar)
    mus_d = mus * g_m * (10 ** (5.0 / 20) * (1 - env) + env)
    # 开场 3 秒音效抬头（声音钩子）
    fxg = 10 ** ((Ln - 14.0 - lufs(fx[:int(3 * SR)])) / 20)
    fx = fx * fxg
    sf.write(f'{OUT}/narration.wav', nar, SR, subtype='PCM_24')
    sf.write(f'{OUT}/music.wav', mus_d, SR, subtype='PCM_24')
    sf.write(f'{OUT}/sfx.wav', fx, SR, subtype='PCM_24')
    for name, x in (('mix', nar + mus_d + fx), ('mix_nomusic', nar + fx)):
        sf.write(f'{OUT}/{name}_pre.wav', x, SR, subtype='FLOAT')
        loudnorm(f'{OUT}/{name}_pre.wav', f'{OUT}/{name}.wav')
    # 报告：说话段音乐比人声低多少
    rep = dict(nar_lufs=Ln, music_under_voice_db=Ln - lufs(mus_d[sp]), total=T.total)
    json.dump(rep, open(f'{OUT}/report.json', 'w'), indent=1); print(rep)


def loudnorm(a, b, I=-15.0, TP=-1.5):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', a, '-af', f'loudnorm=I={I}:TP={TP}:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True).stderr
    j = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
    af = (f"loudnorm=I={I}:TP={TP}:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
          f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,aresample=48000")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', a, '-af', af, '-ar', '48000', '-c:a', 'pcm_s24le', b], check=True)


if __name__ == '__main__':
    main()
