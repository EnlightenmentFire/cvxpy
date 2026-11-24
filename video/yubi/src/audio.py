# -*- coding: utf-8 -*-
"""旁白拼接 + 配乐与音效合成（全部 numpy 生成）+ 混音。输出 audio/narration.wav、audio/music.wav、audio/mix.wav（48 kHz 立体声）。
配乐：D 小调，低音鼓 + 弦乐长音；肆段鼓点加紧；柒段《敕勒歌》处音乐收掉，只留风声。"""
import json, os, sys, subprocess, numpy as np, soundfile as sf, librosa
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sound import *
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TL = json.load(open(f"{ROOT}/src/timeline.json"))
TOTAL = TL['total'] + 0.6
N = int(TOTAL * SR)
LN = lambda s, k: [l for l in TL['lines'] if l['sec'] == s and l['k'] == k][0]
A = lambda s, k: LN(s, k)['start']
E = lambda s, k: LN(s, k)['end']
CK = lambda s, k, j: LN(s, k)['chunks'][min(j, len(LN(s, k)['chunks']) - 1)]['start']
S = TL['secs']


def narration():
    buf = np.zeros(N)
    for l in TL['lines']:
        a, sr = sf.read(os.path.join(os.environ.get("LINES_DIR", f"{ROOT}/audio/lines"), f"{l['i']:03d}.wav")); a = librosa.resample(a.astype(np.float32), orig_sr=sr, target_sr=SR)
        i = int(l['start'] * SR); buf[i:i + len(a)] += a[: N - i]
    buf = fft_filter(buf, 70, None, 2)
    # 轻微加厚低频（男声更沉）
    low = fft_filter(buf, 90, 260, 2); buf = buf + 0.18 * low
    w = int(0.03 * SR); e = np.sqrt(np.convolve(buf ** 2, np.ones(w) / w, 'same')) + 1e-6
    thr = 0.09; g = np.where(e > thr, (thr / e) ** 0.45, 1.0); g = np.convolve(g, np.ones(w) / w, 'same')
    buf = buf * g; return buf / np.abs(buf).max() * 0.86


def music():
    dry = np.zeros((N, 2)); perc = np.zeros((N, 2)); fx = np.zeros((N, 2)); amb = np.zeros((N, 2))
    t = np.arange(N) / SR
    # 1) 低音持续（全片，强度随段落）
    keys_t = [0, S['title']['start'], S['s1']['start'], S['s2']['start'], S['s3']['start'], S['s4']['start'], A('s4', 7), S['s5']['start'], A('s5', 11), S['s6']['start'], S['s7']['start'], S['s7']['hush'] - 0.3, S['s8']['card'][0], S['s9']['start'], A('s9', 8), S['s10']['start'], TOTAL - 3, TOTAL]
    keys_v = [0.6, 0.9, 0.55, 0.65, 0.75, 0.9, 1.0, 0.5, 0.75, 0.6, 0.6, 0.0, 0.6, 0.65, 0.9, 0.7, 0.4, 0.0]
    inten = np.interp(t, keys_t, keys_v)
    dr = drone(TOTAL) * inten; dry[:, 0] += dr * 0.15; dry[:, 1] += dr * 0.15
    # 2) 弦乐长音：每段一组和声
    def seq(t0, t1, names, step=8.0, gain=1.0, bright=800, octv=-12):
        k = 0; tt = t0
        while tt < t1 - 1:
            d = min(step, t1 - tt) + 2.6
            add(dry, strings([NOTE(s + octv) for s in CH[names[k % len(names)]]], d, bright, 1.6, 1.8), tt - 0.8, 0.55 * gain, rng.uniform(-0.2, 0.2)); tt += step; k += 1
    seq(0, S['title']['start'], ['Dm', 'Bb', 'Gm', 'Asus'], 6.5, 0.8)
    seq(S['title']['start'], S['s1']['start'], ['Dm'], 4, 1.2, 1000)
    seq(S['s1']['start'], S['s2']['start'], ['Dm', 'Gm', 'Bb', 'Asus'], 8.5, 0.75, 700)
    seq(S['s2']['start'], S['s3']['start'], ['Dm', 'Bb', 'Em7b5', 'Asus'], 7, 0.85, 760)
    seq(S['s3']['start'], S['s4']['start'], ['Dm', 'Em7b5', 'Asus', 'Dm'], 5, 0.85, 600, -24)
    seq(S['s4']['start'], S['s5']['start'], ['Dm', 'Dm', 'Bb', 'Asus'], 5.5, 0.9, 900)
    seq(S['s5']['start'], A('s5', 11), ['Dm', 'Gm', 'Dsus', 'F', 'C', 'Dm'], 9, 0.7, 650)
    seq(A('s5', 11), S['s6']['start'], ['Em7b5', 'Asus', 'Bb', 'F', 'Dm'], 4.2, 0.9, 900)
    seq(S['s6']['start'], S['s7']['start'], ['Dm', 'Bb', 'Gm', 'Em7b5'], 7, 0.7, 520, -24)
    seq(S['s7']['start'], S['s7']['hush'] - 1.2, ['Gm', 'Dm', 'Asus'], 6.5, 0.6, 520)
    seq(S['s8']['start'], S['s9']['start'], ['Dm', 'Bb', 'F', 'C'], 6.5, 0.8, 700)
    seq(S['s9']['start'], A('s9', 8), ['Dm', 'Em7b5', 'Bb', 'Asus'], 6, 0.8, 700)
    seq(A('s9', 8), A('s9', 9), ['Gm'], 5, 0.5, 400, -24)
    seq(A('s9', 9), S['s10']['start'], ['Dm', 'Bb', 'F', 'Asus'], 3.5, 1.0, 1000)
    seq(S['s10']['start'], TOTAL - 1.5, ['Bb', 'F', 'Dm', 'Dm'], 4.5, 1.0, 800)
    # 3) 拨弦动机（五声）
    PENT = [0, 3, 5, 7, 10, 12, 15, 17]
    def motif(t0, notes, step=0.9, gain=0.5, octave=0):
        for k, nidx in enumerate(notes):
            if nidx is None: continue
            add(dry, pluck(NOTE(PENT[nidx] + octave), 3.2), t0 + k * step + rng.uniform(-0.012, 0.012), gain * rng.uniform(0.8, 1.0), rng.uniform(-0.4, 0.4))
    motif(2.0, [0, None, 3, 2, None, 0, None, 5, 3], 1.15, 0.32)
    motif(S['s1']['body'], [3, 2, 0, None, 1, 2, None, None, 3, 4, 3, None, 2, 0], 1.3, 0.34)
    motif(S['s2']['body'] + 12, [0, 2, 3, None, 3, 4, 5, None, 4, 3, 2, None], 1.0, 0.32)
    motif(S['s5']['body'] + 2, [0, None, None, 2, 1, None, None, 0], 1.7, 0.3)
    motif(A('s8', 3), [0, 2, 4, 5, None, 4, 5, 7], 0.8, 0.36, 12)
    motif(S['s9']['body'] + 8, [5, None, 4, 3, None, None, 2, None, 0, None, 1, 2], 0.75, 0.3, 12)
    motif(A('s10', 2), [0, None, 2, 3, None, None, 4, 3, None, 0], 1.0, 0.4)
    # 4) 鼓
    def beat(t0, t1, bpm, pattern, gain=1.0):
        st = 60 / bpm / 2; k = 0; tt = t0
        while tt < t1:
            p = pattern[k % len(pattern)]
            if p == 'X': add(perc, taiko(56, 1.4), tt, 0.85 * gain, 0)
            elif p == 'x': add(perc, taiko(72, 0.9, 0.7), tt, 0.42 * gain, rng.uniform(-0.3, 0.3))
            elif p == 'o': add(perc, tom(116, 0.4), tt, 0.3 * gain, rng.uniform(-0.5, 0.5))
            elif p == 'i': add(perc, tom(156, 0.3), tt, 0.2 * gain, rng.uniform(-0.6, 0.6))
            elif p == 'r': add(perc, rim(), tt, 0.25 * gain, rng.uniform(-0.6, 0.6))
            tt += st; k += 1
    beat(1.0, A('cold', 2) - 0.4, 52, 'X.......x.......', 0.55)
    add(perc, taiko(50, 2.2, 1.2), A('cold', 2) - 0.12, 0.85)
    beat(A('cold', 3), S['title']['start'] - 0.8, 60, 'X...x...X..ox...', 0.5)
    add(perc, taiko(46, 2.8, 1.3), S['title']['start'] + 0.1, 1.25)
    for sid in ('s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9'):
        g = 0.55 if sid == 's8' else 1.0
        add(perc, taiko(52, 2.2, 1.1), S[sid]['card'][0] + 0.1, 0.95 * g); add(fx, whoosh(1.1, 200, 1500)[::-1].copy(), S[sid]['card'][0] - 1.0, 0.22 * g)
    beat(S['s1']['body'], S['s2']['start'] - 1, 56, 'X.......x...o...', 0.4)
    beat(S['s2']['body'], A('s2', 3), 66, 'X..ox.o.X..ox.oi', 0.55)
    beat(A('s2', 3), S['s3']['start'] - 1, 66, 'X...x...X..ox...', 0.45)
    beat(S['s3']['body'], S['s4']['start'] - 1, 50, 'X.......x.......', 0.45)
    # 肆：紧鼓 + 低音弦乐固定音型
    beat(S['s4']['body'], A('s4', 11) - 0.3, 92, 'X.oxX.oix.oxXooi', 0.75)
    beat(A('s4', 11) - 0.3, S['s5']['start'] - 1, 92, 'X...x...X..ox...', 0.5)
    st = 60 / 92 / 2; tt = S['s4']['body']; k = 0
    while tt < A('s4', 11) - 0.3:
        add(dry, cello_note(NOTE([0, 0, 12, 0, 1, 0, 12, 3][k % 8] - 24), st * 1.6, 1.0 if k % 4 == 0 else 0.6), tt, 0.55, -0.2); tt += st; k += 1
    # 伍：几乎无鼓；关键句各一记低鼓
    for tt in (A('s5', 4) - 0.1, A('s5', 8) - 0.1): add(perc, taiko(46, 3.0, 1.0), tt, 0.85)
    beat(A('s5', 11), E('s5', 13), 60, 'X.......x.......', 0.45)
    # 陆：慢脉
    beat(S['s6']['body'], S['s7']['start'] - 1, 44, 'X...............', 0.5)
    # 柒：撤军段轻鼓，之后全停
    beat(S['s7']['body'], S['s7']['hush'] - 2.5, 50, 'X.......x.......', 0.4)
    # 捌：547 一记；侯景
    add(perc, taiko(44, 3.2, 1.2), CK('s8', 0, 1) + 0.3, 0.9)
    beat(A('s8', 1), S['s9']['start'] - 1, 54, 'X.......x...o...', 0.4)
    # 玖：童谣段轻、死讯一击、北周东征行军鼓
    beat(S['s9']['body'], A('s9', 8), 58, 'X.....r.x.....r.', 0.45)
    add(perc, taiko(42, 3.5, 1.3), CK('s9', 8, 1), 1.0)
    beat(A('s9', 9) + 0.3, A('s9', 10) - 0.2, 76, 'X.oix.o.X.oix.oo', 0.6)
    add(perc, taiko(46, 3.0, 1.2), A('s9', 10) - 0.1, 0.9)
    for k in (0, 1, 2): add(perc, taiko(48 - k * 2, 2.6, 1.1), A('s10', k) - 0.06, 0.95)
    # 5) 音效
    # 冷启动：箭入、钉住、纸卷、翻面、射出
    add(fx, arrow_fly(0.6), 0.28, 0.95, -0.6); add(fx, thunk(), 0.88, 1.0, 0.1)
    add(fx, paper(1.2), 1.15, 0.7, 0.0); add(fx, paper(0.7), A('cold', 1) + 0.3, 0.6, 0.1)
    add(fx, paper(0.6), A('cold', 3) + 0.3, 0.6, 0.0); add(fx, arrow_fly(0.6)[::-1].copy() * 0.5 + arrow_fly(0.6) * 0.5, A('cold', 3) + 0.8, 0.95, -0.5)
    # 壹：542 大雪的风
    add(amb, wind(6, 1.6, 0.2), A('s1', 2) + 1.8, 1.0)
    # 贰：大军南下、挖河、堆山
    add(fx, rumble(A('s2', 3) - A('s2', 1) + 1, 36, 1.0), A('s2', 1) - 0.2, 0.8)
    for k in range(10): add(fx, dig(), CK('s2', 3, 2) - 0.2 + k * 0.22, 0.5, rng.uniform(-0.4, 0.4))
    for k in range(14): add(fx, taiko(84, 0.35, 0.2) * 0.4, A('s2', 4) + 0.6 + k * 0.42, 0.45, rng.uniform(-0.5, 0.5))
    # 叁：挖地道、火
    for k in range(18): add(fx, taiko(70, 0.3, 0.3) * 0.35, A('s3', 0) + 1.0 + k * 0.6, 0.4, rng.uniform(-0.5, 0.5))
    f0 = CK('s3', 1, 2) + 0.2; add(fx, whoosh(1.4, 200, 1400), f0 - 0.2, 0.7); add(fx, fire(A('s3', 4) + 0.6 - f0, 1.0), f0, 0.9)
    for k in range(5): add(fx, whoosh(0.5, 150, 700), f0 + 0.2 + k * 0.8, 0.45)
    # 肆：四组对招
    T = lambda k: A('s4', k)
    hit1 = T(1) + 0.9; curtain = CK('s4', 1, 1) + 0.1; hit2 = curtain + 0.9; hit3 = A('s4', 2) + 0.8
    add(fx, rumble(1.2, 50, 0.8), T(1) - 0.2, 0.8); add(fx, psum(crash(1.0) * 0.6, thunk()), hit1, 0.9)
    add(fx, whoosh(0.6, 300, 1800), curtain, 0.5); add(fx, thunk(0.3) * 0.3, hit2, 0.5); add(fx, thunk(0.3) * 0.3, hit3, 0.5)
    add(fx, whoosh(1.4, 200, 1200), T(4) + 0.2, 0.6); add(fx, fire(2.0, 0.8), T(4) + 0.4, 0.6)
    cut = A('s4', 5) - 0.25; add(fx, whoosh(0.3, 2000, 7000), cut, 0.8, 0.3); add(fx, clank_lite(), cut + 0.05, 0.5, 0.3); add(fx, whoosh(0.9, 800, 200), cut + 0.15, 0.6); add(fx, thunk(0.4) * 0.6, cut + 1.1, 0.6)
    burn = T(7) + 1.4; fallT = CK('s4', 7, 2) + 0.4; add(fx, fire(fallT - burn + 0.6, 0.7), burn, 0.6); add(fx, crash(2.4), fallT, 1.0)
    for k in range(6): add(fx, thunk(0.25) * 0.5, A('s4', 8) + 0.3 + k * 0.22, 0.6, rng.uniform(-0.3, 0.3))
    add(fx, rumble(2.6, 60, 1.0), T(10) + 0.5, 0.8)
    for k in range(2): add(fx, arrow_fly(0.4), CK('s4', 11, 2) + k * 0.5 - 0.2, 0.6, -0.4); add(fx, clank_lite(0.3), CK('s4', 11, 2) + k * 0.5 + 0.2, 0.35, 0.3)
    # 伍：夜风；悬赏令再射入
    add(amb, wind(S['s6']['start'] - S['s5']['start'], 1.0, 0.09), S['s5']['start'], 0.8)
    add(fx, arrow_fly(0.6), CK('s5', 10, 2) - 0.25, 0.8, -0.4); add(fx, thunk(), CK('s5', 10, 2) + 0.45, 0.7)
    # 陆：风
    add(amb, wind(S['s7']['start'] - S['s6']['start'] + 1, 1.0, 0.12), S['s6']['start'], 0.9)
    # 柒：风声贯穿，歌词处只剩风
    add(amb, wind(S['s8']['card'][0] - S['s7']['start'] + 1.5, 1.4, 0.1), S['s7']['start'], 1.0)
    # 捌：侯景
    add(fx, whoosh(1.0, 300, 1600), CK('s8', 0, 2) + 0.3, 0.5)
    # 玖：北周东征
    add(fx, rumble(A('s9', 10) - A('s9', 9), 40, 0.9), A('s9', 9) + 0.3, 0.8)
    # 收尾：雪夜的风
    add(amb, wind(TOTAL - S['s10']['start'], 1.0, 0.08), S['s10']['start'], 0.8)
    mix = reverb(dry, 3.2, 0.45) + reverb(perc, 2.0, 0.28) * 0.95 + reverb(fx, 1.4, 0.2) * 0.8
    # 柒：歌词前后音乐收掉（风声 amb 不受影响）
    h0, h1 = S['s7']['hush'] - 0.6, S['s8']['card'][0] - 0.3
    g = 1 - np.clip((t - h0) / 0.9, 0, 1) * np.clip((h1 - t) / 0.6, 0, 1)
    mix *= g[:, None]
    return mix, amb


def psum(*xs):
    n = max(len(x) for x in xs); out = np.zeros(n)
    for x in xs: out[:len(x)] += x
    return out


def dig(dur=0.4):
    n = int(dur * SR); tt = np.arange(n) / SR
    return taiko(90, dur, 0.2)[:n] * 0.4 + fft_filter(rng.normal(size=n) * np.exp(-tt / 0.04), 200, 1500, 2) * 0.4


def clank_lite(dur=0.35):
    n = int(dur * SR); tt = np.arange(n) / SR; x = np.zeros(n)
    for f, d in ((1310, 0.06), (2140, 0.05), (3370, 0.035)): x += np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) * np.exp(-tt / d)
    return x * 0.3


def main():
    os.makedirs(f"{ROOT}/audio", exist_ok=True)
    nar = narration(); sf.write(f"{ROOT}/audio/narration.wav", nar, SR, subtype='PCM_16')
    mus, amb = music(); mus /= np.abs(mus).max() + 1e-9; amb /= np.abs(amb).max() + 1e-9
    w = int(0.05 * SR); e = np.sqrt(np.convolve(nar ** 2, np.ones(w) / w, 'same'))
    gate = (e > 0.02).astype(np.float64); k = int(0.45 * SR); gate = np.convolve(gate, np.ones(k) / k, 'same'); gate = np.clip(gate * 2.2, 0, 1)
    k2 = int(0.25 * SR); gate = np.convolve(gate, np.hanning(k2) / np.hanning(k2).sum(), 'same')
    g = 0.66 - 0.42 * gate                     # 无旁白约 0.66，有旁白约 0.24（约 -9 dB）
    mus = mus * g[:, None] + amb * (0.22 - 0.08 * gate)[:, None]
    fade = np.minimum(np.arange(N) / (0.25 * SR), 1) * np.minimum((N - np.arange(N)) / (3.0 * SR), 1); mus *= fade[:, None]
    sf.write(f"{ROOT}/audio/music.wav", mus, SR, subtype='PCM_16')
    mix = mus + nar[:, None] * 0.92
    mix = np.tanh(mix * 1.1) / np.tanh(1.1); mix = mix / np.abs(mix).max() * 0.89
    sf.write(f"{ROOT}/audio/mix_raw.wav", mix, SR, subtype='PCM_16')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f"{ROOT}/audio/mix_raw.wav", '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '48000', f"{ROOT}/audio/mix.wav"], check=True)
    def db(x): return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
    print("dur %.1f  nar %.1f dB  music %.1f dB" % (N / SR, db(nar[np.abs(nar) > 0.01]), db(mus)))


if __name__ == "__main__":
    main()
