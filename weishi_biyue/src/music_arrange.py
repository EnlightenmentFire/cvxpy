# -*- coding: utf-8 -*-
"""按画面节点编配配乐（全部素材来自 MusicGen 生成 + Demucs 分轨，无外部曲库）。

结构（视频时间）：
  0.00        弦乐音型直接中等强度进入（淡入 0.3s 在混音链里做），鼓只留一点底
  ~4.4        鼓加到一半                         —— 第一层
  8.40        大鼓落在「结果城里的人」，鼓全开     —— 第二层（箭头撞墙对拍）
  ~12.6–14.7  弦乐整体再抬一点                   —— 第三层
  14.69–17.39 缺口出现：鼓收一半，D→F→A 的弦乐长音一级级往上走
  17.39–18.95 鼓回满，往上顶
  18.95       全部切掉，只剩一个长音；19.0 起埙冒出一句（落在答案前的空拍里）
  19.62       重鼓（领先人声 90ms，避开侧链压缩）
  19.62–25.0  D 小调长和弦托到最后一帧，不淡出（末尾 15ms 防咔哒）
用法: python music_arrange.py <work> <take> <timeline.json> <out.wav> [offset]
"""
import json
import os
import sys

import numpy as np
import soundfile as sf
import soxr

SR = 48000


def load(path, sr=SR):
    a, r = sf.read(path, dtype="float32", always_2d=True)
    if a.shape[1] == 1:
        a = np.repeat(a, 2, 1)
    if r != sr:
        a = np.stack([soxr.resample(a[:, c], r, sr) for c in range(2)], 1)
    return a


def db(x):
    return 10 ** (x / 20)


def env_points(n, pts):
    """分段线性包络：pts = [(t, dB), ...]"""
    t = np.arange(n) / SR
    ts = np.array([p[0] for p in pts])
    vs = np.array([p[1] for p in pts])
    return db(np.interp(t, ts, vs)).astype(np.float32)[:, None]


def paulstretch(x, stretch, out_len, win=0.30, seed=0):
    """Paulstretch：把一小段和声拉成平稳的长音垫。x: (n, 2)"""
    rng = np.random.default_rng(seed)
    N = int(win * SR) // 2 * 2
    w = (np.hanning(N) ** 1.0).astype(np.float32)
    hop_out = N // 4
    hop_in = hop_out / stretch
    out = np.zeros((out_len + N, 2), np.float32)
    pos_in, pos_out = 0.0, 0
    while pos_out < out_len:
        i = int(pos_in) % max(1, len(x) - N)
        seg = x[i:i + N] * w[:, None]
        for c in range(2):
            F = np.abs(np.fft.rfft(seg[:, c]))
            ph = rng.uniform(0, 2 * np.pi, len(F))
            y = np.fft.irfft(F * np.exp(1j * ph), N).astype(np.float32)
            out[pos_out:pos_out + N, c] += y * w
        pos_in += hop_in
        pos_out += hop_out
    out = out[:out_len]
    return out / (np.sqrt(np.mean(out ** 2)) + 1e-9)


def pitch_shift(x, semis):
    if semis == 0:
        return x
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        sf.write(f"{d}/i.wav", x, SR)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{d}/i.wav", "-af",
                        f"rubberband=pitch={2 ** (semis / 12):.6f}:formant=preserved:pitchq=quality", f"{d}/o.wav"],
                       check=True)
        y = load(f"{d}/o.wav")
    return y[:len(x)] if len(y) >= len(x) else np.pad(y, ((0, len(x) - len(y)), (0, 0)))


def best_chord_window(x, length=0.8, root=2, minor=True):
    """在 x 里找最像 D 小三和弦的一段（色度相关）。"""
    import librosa
    y = x.mean(1)
    hop = 2048
    C = librosa.feature.chroma_stft(y=y, sr=SR, hop_length=hop, n_fft=8192)
    tmpl = np.zeros(12)
    for iv, wt in ((0, 1.0), (3 if minor else 4, 0.8), (7, 0.9)):
        tmpl[(root + iv) % 12] = wt
    L = max(1, int(length * SR / hop))
    best, bi = -9, 0
    rms = librosa.feature.rms(y=y, frame_length=4096, hop_length=hop)[0]
    for i in range(0, C.shape[1] - L):
        c = C[:, i:i + L].mean(1)
        r = np.corrcoef(c, tmpl)[0, 1] + 0.2 * (rms[i:i + L].mean() / (rms.max() + 1e-9))
        if r > best:
            best, bi = r, i
    s = bi * hop
    return x[s:s + int(length * SR)], s / SR, best


def strongest_hit(drums, around=None):
    import librosa
    y = drums.mean(1)
    env = librosa.onset.onset_strength(y=y, sr=SR, hop_length=256)
    on = librosa.onset.onset_detect(onset_envelope=env, sr=SR, hop_length=256, units="frames")
    k = on[np.argmax(env[on])]
    t = librosa.frames_to_time(k, sr=SR, hop_length=256)
    s = max(0, int((t - 0.015) * SR))
    return drums[s:s + int(1.6 * SR)].copy(), t


def best_xun_phrase(x, length=0.75):
    """埙独奏里能量最集中、起音清楚的一句。"""
    y = x.mean(1)
    hop = 1024
    import librosa
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop)[0]
    on = librosa.onset.onset_detect(y=y, sr=SR, hop_length=hop, units="frames", backtrack=True)
    L = int(length * SR / hop)
    best, bs = -1, 0
    for o in on:
        if o + L >= len(rms):
            continue
        score = rms[o:o + L].mean() - 0.5 * rms[max(0, o - 4):o].mean()
        if score > best:
            best, bs = score, o
    s = bs * hop
    seg = x[s:s + int(length * SR)].copy()
    return seg, s / SR


def fade(x, fin=0.0, fout=0.0):
    x = x.copy()
    if fin > 0:
        n = int(fin * SR)
        x[:n] *= np.linspace(0, 1, n)[:, None]
    if fout > 0:
        n = int(fout * SR)
        x[-n:] *= np.linspace(1, 0, n)[:, None]
    return x


def place(buf, x, t, gain=1.0):
    s = int(round(t * SR))
    e = min(len(buf), s + len(x))
    if e > s:
        buf[s:e] += x[:e - s] * gain


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)


def main(work, take, tl_path, out, offset=0.47, xun_path=None, end_path=None):
    T = json.load(open(tl_path))
    dur = T["end"]
    n = int(round(dur * SR))
    st = f"{work}/stems/htdemucs/{take}"
    other = load(f"{st}/other.wav")
    drums = load(f"{st}/drums.wav")
    # 音乐时间 = 视频时间 + offset
    o = int(round(offset * SR))

    def seg(x):
        y = x[o:o + n]
        return np.pad(y, ((0, n - len(y)), (0, 0)))

    other_v, drums_v = seg(other), seg(drums)
    t_strike = T["slips_strike"]
    t_freeze = T["freeze"]
    t_ans = T["answer"]
    t_cut = round(t_ans - 0.76, 3)
    t_mai = T.get("word_mai", 7.72)          # 人声 S5 结束后切掉整个乐队
    t_hit = round(t_ans - 0.09, 3)

    # ---- 层次包络
    e_other = env_points(n, [(0, -1.5), (4.3, -1.5), (4.6, 0.5), (8.3, 0.5), (12.6, 1.0), (t_strike, 1.0),
                             (t_freeze, 1.5), (t_freeze + 0.3, 4.0), (t_cut - 0.02, 5.0), (t_cut + 0.05, -60), (dur, -60)])
    # 「全部活埋」的「埋」（约 7.7–8.1s）正好压着一下鼓点：这里把鼓挖一个坑，保字清楚
    e_drums = env_points(n, [(0, -11), (4.3, -11), (4.5, -6), (t_mai - 0.25, -6), (t_mai - 0.1, -16), (t_mai + 0.42, -16),
                             (8.35, 0), (t_strike - 0.1, 0),
                             (t_strike + 0.4, -6.5), (t_freeze - 0.2, -6.5), (t_freeze + 0.15, 3.0),
                             (t_cut - 0.02, 4.0), (t_cut + 0.04, -60), (dur, -60)])
    # 第 2 句（地名「壶关」+「全部活埋」）信息最密，乐队在这一句底下再让 3dB
    s2a, s2b = T["subs"][0]["t0"], T["subs"][1]["t1"]
    # 「全部活埋」这一下乐队整个抽空（也让「埋」的二声听得清），8.4s 鼓全开砸回来
    e_s2 = env_points(n, [(0, 0), (s2a - 0.3, 0), (s2a - 0.05, -3.0), (t_mai - 0.38, -3.0), (t_mai - 0.2, -60),
                          (8.30, -60), (8.36, 0), (dur, 0)])
    bed = (other_v * e_other + drums_v * e_drums) * e_s2
    bed_ref = rms_db(bed[: int(2.7 * SR)])

    # ---- 弦乐长音一级级往上走（D → F → A），缺口出现时
    chord_src, t_src, score = best_chord_window(other, 0.8)
    pad = paulstretch(chord_src, 12.0, int(9 * SR), seed=1)
    pad_lo = paulstretch(chord_src, 12.0, int(9 * SR), seed=2)
    riser = np.zeros((n, 2), np.float32)
    steps = [(t_strike, 0), (t_strike + (t_freeze - t_strike) / 3, 3), (t_strike + 2 * (t_freeze - t_strike) / 3, 7)]
    for i, (ts, semi) in enumerate(steps):
        te = steps[i + 1][0] if i + 1 < len(steps) else t_cut
        L = int((te - ts + 0.35) * SR)
        p = pitch_shift(pad[:L], semi)
        p = fade(p, 0.25, 0.35)
        place(riser, p, ts)
    riser_gain = db(bed_ref - 9.0)  # 托在乐队下面
    riser *= env_points(n, [(0, 0), (t_strike, -6), (t_freeze, 0), (t_cut, 1), (t_cut + 0.05, -60), (dur, -60)])

    # ---- 空拍：只剩一个长音 + 埙一句
    hold = paulstretch(chord_src, 14.0, int(1.4 * SR), seed=3)
    hold = pitch_shift(hold, 7)  # A：属音，悬着
    hold = fade(hold, 0.18, 0.06)
    lone = np.zeros((n, 2), np.float32)
    place(lone, hold[: int((t_hit - t_cut + 0.25) * SR)], t_cut - 0.20)
    lone *= db(bed_ref - 4.0)
    xun_info = None
    if xun_path and os.path.exists(xun_path):
        xun = load(xun_path)
        L = t_hit - t_cut - 0.03
        xs = os.environ.get("XUN_SRC_T")
        if xs:  # 人工挑的一句：D4 长音一跃到 A4（属音），答案落在 D 小调上正好解决
            xt = float(xs)
            phrase = xun[int(xt * SR): int((xt + L) * SR)].copy()
        else:
            phrase, xt = best_xun_phrase(xun, length=L)
        phrase = fade(phrase, 0.03, 0.10)
        phrase = phrase / (np.sqrt(np.mean(phrase ** 2)) + 1e-9) * db(bed_ref + 1.0)
        place(lone, phrase, t_cut + 0.03)
        xun_info = round(float(xt), 2)

    # ---- 答案重鼓 + 长和弦托到底
    hit, ht = strongest_hit(drums)
    hit = fade(hit, 0.0, 0.5)
    hit = hit / (np.abs(hit).max() + 1e-9) * db(-6.0)
    tt = np.arange(int(1.2 * SR)) / SR
    boom = (np.sin(2 * np.pi * 55 * tt) * np.exp(-tt / 0.32) * 0.5).astype(np.float32)[:, None].repeat(2, 1)
    end_len = n - int(round(t_hit * SR))
    if end_path and os.path.exists(end_path):
        ec = load(end_path)
        csrc, _, _ = best_chord_window(ec, 0.8)
        endpad = paulstretch(csrc, 12.0, end_len, seed=4)
    else:
        endpad = paulstretch(chord_src, 12.0, end_len, seed=4)
    lowpad = pitch_shift(paulstretch(chord_src, 12.0, end_len, seed=5), -12)
    chord = endpad + 0.55 * lowpad
    chord = chord / (np.sqrt(np.mean(chord ** 2)) + 1e-9)
    # 重拍后和弦稍微涨一下再稳住；末尾电平对齐开头，重播接得上
    ce = env_points(end_len, [(0, -9), (0.08, -2), (0.9, 0.5), (2.5, 0), (end_len / SR, -0.5)])
    chord = fade(chord * ce * db(bed_ref - 0.5), 0.03, 0.0)
    final = np.zeros((n, 2), np.float32)
    place(final, chord, t_hit)
    hit_rms = np.sqrt(np.mean(hit[: int(0.3 * SR)] ** 2)) + 1e-9
    place(final, hit, t_hit, gain=db(bed_ref + 8.0) / hit_rms)
    place(final, boom, t_hit, gain=db(bed_ref + 6))

    music = bed + riser * riser_gain + lone + final
    # 末尾 15ms 防咔哒（听感上不是淡出）
    k = int(0.015 * SR)
    music[-k:] *= np.linspace(1, 0, k)[:, None]
    peak = np.abs(music).max()
    if peak > 0.95:
        music *= 0.95 / peak
    sf.write(out, music, SR, subtype="PCM_24")
    info = dict(take=take, offset=offset, chord_src_t=round(float(t_src), 2), chord_score=round(float(score), 2),
                hit_src_t=round(float(ht), 2), xun_src_t=xun_info, t_cut=float(t_cut), t_hit=float(t_hit), bed_ref_db=round(float(bed_ref), 1))
    json.dump(info, open(out.replace(".wav", "_info.json"), "w"), indent=1)
    print(info)


if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], a[3], a[4], float(a[5]) if len(a) > 5 else 0.47,
         a[6] if len(a) > 6 else None, a[7] if len(a) > 7 else None)
