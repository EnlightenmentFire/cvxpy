"""自己合成的氛围底乐（纯 numpy 加法合成，无任何采样/第三方素材）+ 旁白混音。
产出 build/music.wav、build/mix.wav（48k 立体声）。旁白出现时底乐自动压低。
"""
import json, sys
from pathlib import Path
import numpy as np, soundfile as sf
from scipy.signal import fftconvolve, resample_poly, butter, sosfiltfilt

ROOT = Path(__file__).parent; BUILD = ROOT / 'build'
SR = 48000
rng = np.random.default_rng(1921)

def midi(n): return 440.0 * 2 ** ((n - 69) / 12)

def pad_note(freq, dur, amp=1.0, pan=0.0):
    n = int(dur * SR); t = np.arange(n) / SR
    out = np.zeros((n, 2), np.float32)
    for det in (-4, 0, 5):                               # 三个轻微失谐的声部
        f = freq * 2 ** (det / 1200)
        ph = rng.uniform(0, 2 * np.pi)
        sig = np.zeros(n)
        for h, a in ((1, 1.0), (2, 0.32), (3, 0.12), (4, 0.05)):
            wob = 1 + 0.25 * np.sin(2 * np.pi * rng.uniform(0.05, 0.13) * t + rng.uniform(0, 6.28))
            sig += a * wob * np.sin(2 * np.pi * f * h * t + ph * h)
        p = np.clip(pan + rng.uniform(-0.35, 0.35), -1, 1)
        out[:, 0] += sig * np.sqrt((1 - p) / 2); out[:, 1] += sig * np.sqrt((1 + p) / 2)
    att, rel = min(5.0, dur * 0.4), min(6.0, dur * 0.45)
    env = np.minimum(1, t / att) ** 1.5 * np.minimum(1, (dur - t) / rel) ** 1.5
    return (out * env[:, None] * amp / 3).astype(np.float32)

def bell(freq, amp=1.0, pan=0.0, dur=7.0):
    n = int(dur * SR); t = np.arange(n) / SR
    sig = np.sin(2 * np.pi * freq * t) * np.exp(-t / 1.6) + 0.25 * np.sin(2 * np.pi * freq * 2.01 * t) * np.exp(-t / 0.7)
    sig *= np.minimum(1, t / 0.02)
    return np.stack([sig * np.sqrt((1 - pan) / 2), sig * np.sqrt((1 + pan) / 2)], 1).astype(np.float32) * amp

def make_music(total):
    n = int((total + 8) * SR); mix = np.zeros((n, 2), np.float32)
    def add(buf, at):
        i = int(at * SR); j = min(n, i + len(buf))
        if i < n: mix[i:j] += buf[:j - i]
    # D 小调上的四个慢和弦，每个 18 秒，互相重叠 6 秒
    chords = [
        [38, 50, 57, 60, 64, 65],     # Dm9   D A C E F
        [34, 46, 53, 57, 62, 65],     # Bbmaj7  Bb F A D F
        [41, 48, 55, 57, 60, 64],     # Fmaj7   F C G A C E
        [33, 45, 52, 55, 60, 64],     # Am7     A E G C E
    ]
    seg, ov = 18.0, 6.0; t = 0.0; k = 0
    while t < total + 2:
        ch = chords[k % 4]
        for i, m in enumerate(ch):
            a = (0.9 if i == 0 else 0.55 if i < 3 else 0.34)
            add(pad_note(midi(m), seg + ov, a, pan=(i - 2.5) / 4), t)
        t += seg; k += 1
    # 稀疏的高音“星点”
    scale = [74, 76, 77, 81, 84, 86, 88]
    t = 5.0
    while t < total - 4:
        add(bell(midi(int(rng.choice(scale))), amp=rng.uniform(0.05, 0.11), pan=rng.uniform(-0.7, 0.7)), t)
        t += rng.uniform(6.0, 11.0)
    # 混响：指数衰减噪声脉冲响应
    L = int(4.5 * SR); tt = np.arange(L) / SR
    wet = np.zeros_like(mix)
    for c in range(2):
        ir = rng.standard_normal(L) * np.exp(-tt / 1.3); ir[:int(0.012 * SR)] = 0
        sos = butter(2, [150, 5200], 'bandpass', fs=SR, output='sos'); ir = sosfiltfilt(sos, ir)
        ir /= np.sqrt((ir ** 2).sum())
        wet[:, c] = fftconvolve(mix[:, c], ir)[:n]
    out = 0.55 * mix + 0.75 * wet
    sos = butter(2, 5500, 'lowpass', fs=SR, output='sos'); out = sosfiltfilt(sos, out, axis=0)
    sos = butter(2, 45, 'highpass', fs=SR, output='sos'); out = sosfiltfilt(sos, out, axis=0)
    out = out[:int(total * SR)]
    return (out / np.abs(out).max()).astype(np.float32)

def duck_env(tl, total):
    """旁白行内底乐压低；行间停顿 >0.9s 或片头片尾时抬起。"""
    n = int(total * SR); g = np.ones(n, np.float32)
    spans = sorted((v['s'], v['e']) for k, v in tl['lines'].items() if 'c' not in k)
    merged = []
    for s, e in spans:
        if merged and s - merged[-1][1] < 0.9: merged[-1][1] = e
        else: merged.append([s, e])
    for s, e in merged: g[max(0, int((s - 0.25) * SR)):int((e + 0.25) * SR)] = 0.0
    # 平滑：0.5 秒移动平均两次 ≈ 柔和的坡
    k = int(0.55 * SR); ker = np.ones(k, np.float32) / k
    for _ in range(2): g = np.convolve(g, ker, 'same')
    return g

def main():
    tl = json.loads((BUILD / 'timeline.json').read_text()); total = tl['duration']
    nar, sr = sf.read(BUILD / 'narration.wav'); assert sr == 24000
    nar = resample_poly(nar, 2, 1).astype(np.float32)
    sos = butter(2, 75, 'highpass', fs=SR, output='sos'); nar = sosfiltfilt(sos, nar)
    # 低频轻微加厚（180Hz 以下 +2dB 的并联低通），让声音更沉一点
    sos = butter(1, 220, 'lowpass', fs=SR, output='sos'); nar = nar + 0.26 * sosfiltfilt(sos, nar)
    nar = nar / np.abs(nar).max() * 0.89
    n = int(total * SR); nar = np.pad(nar, (0, max(0, n - len(nar))))[:n]
    mus = make_music(total)
    g = duck_env(tl, total)
    LOW, HIGH = 10 ** (-27 / 20), 10 ** (-15.5 / 20)       # 旁白下 / 空白处的底乐电平
    gain = LOW + (HIGH - LOW) * g
    fade = np.minimum(1, np.arange(n) / (1.5 * SR)) * np.minimum(1, (n - np.arange(n)) / (2.4 * SR))
    mus = mus * (gain * fade)[:, None]
    sf.write(BUILD / 'music.wav', mus, SR)
    mix = mus + nar[:, None]
    mix = np.tanh(mix * 1.0)                                # 软限幅兜底
    sf.write(BUILD / 'mix.wav', mix.astype(np.float32), SR)
    print('mix', round(total, 2), 's; peak', float(np.abs(mix).max()))

if __name__ == '__main__':
    main()
