# -*- coding: utf-8 -*-
"""冷启动约 25 秒样音：同一段稿子、同一版配乐，换不同男声。用法：python tools/sample.py out_dir zm_029,zm_034,zm_014 [speed_n] [speed_q]"""
import sys, os, warnings, subprocess, numpy as np, soundfile as sf, librosa; warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'src'))
from script import L, tts_text
from sound import *
import torch; torch.set_num_threads(4)
from kokoro import KPipeline, KModel

REPO = 'hexgrad/Kokoro-82M-v1.1-zh'
model = KModel(repo_id=REPO).to('cpu').eval(); pipe = KPipeline(lang_code='z', repo_id=REPO, model=model)


def trim(a, sr=24000, th=0.004, pad=0.07):
    e = np.abs(a); w = int(sr * 0.01); env = np.convolve(e, np.ones(w) / w, 'same'); idx = np.where(env > th)[0]
    if len(idx) == 0: return a
    return a[max(0, idx[0] - int(pad * sr)): min(len(a), idx[-1] + int(pad * 2.4 * sr))]


def synth(i, voice, sn, sq):
    l = L[i]; sp = sq if l[1] == 'q' else sn
    a = np.concatenate([r.audio.numpy() for r in pipe(tts_text(l[2]), voice=voice, speed=sp)])
    a = trim(a).astype(np.float32); a[:200] *= np.linspace(0, 1, 200); a[-400:] *= np.linspace(1, 0, 400)
    return librosa.resample(a, orig_sr=24000, target_sr=SR)


def main():
    out = sys.argv[1]; voices = sys.argv[2].split(','); sn = float(sys.argv[3]) if len(sys.argv) > 3 else 1.4; sq = float(sys.argv[4]) if len(sys.argv) > 4 else 1.18
    os.makedirs(out, exist_ok=True)
    for v in voices:
        segs = [synth(i, v, sn, sq) for i in range(5)]
        gaps = [0.32, 0.38, 0.30, 0.45]
        t = 1.35; starts = []
        for k, s in enumerate(segs):
            if L[k][1] == 'q': t += 0.15
            starts.append(t); t += len(s) / SR + (gaps[k] if k < 4 else 0)
        total = t + 2.6; N = int(total * SR)
        nar = np.zeros(N)
        for s, st in zip(segs, starts): i = int(st * SR); nar[i:i + len(s)] += s[:N - i]
        # 轻压缩 + 归一
        w = int(0.03 * SR); e = np.sqrt(np.convolve(nar ** 2, np.ones(w) / w, 'same')) + 1e-6
        g = np.where(e > 0.09, (0.09 / e) ** 0.45, 1.0); g = np.convolve(g, np.ones(w) / w, 'same'); nar = nar * g; nar = nar / np.abs(nar).max() * 0.86
        dry = np.zeros((N, 2)); perc = np.zeros((N, 2)); fx = np.zeros((N, 2))
        # 低音持续 + 弦乐长音（D 小调）
        dr = drone(total) * np.minimum(np.arange(N) / SR / 3, 1); dry[:, 0] += dr * 0.12; dry[:, 1] += dr * 0.12
        for t0, nm, d in ((0.0, 'Dm', 9.5), (8.5, 'Bb', 7.5), (15.0, 'Gm', 6.5), (starts[4] - 0.5, 'Asus', total - starts[4] + 0.5)):
            add(dry, strings([NOTE(s - 12) for s in CH[nm]], d, 800, 1.8, 1.6), t0, 0.9)
        add(dry, strings([NOTE(-24), NOTE(-12)], total, 300, 3, 2), 0, 0.8)
        # 拨弦动机
        for k, nidx in enumerate([0, None, 3, 2, None, 0, None, 5, 3]):
            if nidx is not None: add(dry, pluck(NOTE([0, 3, 5, 7, 10, 12][nidx])), 3.0 + k * 1.15, 0.32, rng.uniform(-0.4, 0.4))
        # 鼓：心跳般的低鼓，悬赏令被射回去时加重
        for tt in np.arange(1.0, starts[2] - 0.3, 2.4): add(perc, taiko(56, 1.4, 0.8), tt, 0.38)
        add(perc, taiko(50, 2.2, 1.2), starts[2] - 0.12, 0.85)
        add(perc, taiko(52, 1.8, 1.0), starts[4] - 0.1, 0.6)
        add(perc, taiko(46, 3.0, 1.3), starts[4] + len(segs[4]) / SR + 0.35, 1.0)
        # 音效：箭射进来、钉住、纸卷展开、射回去、风
        add(fx, wind(total, 0.9), 0, 1.0)
        add(fx, arrow_fly(0.55), 0.35, 0.9, -0.5); add(fx, thunk(), 0.88, 0.9, -0.1)
        add(fx, paper(0.9), 2.4, 0.7, 0.1)
        add(fx, arrow_fly(0.5)[::-1].copy() * 0.6 + arrow_fly(0.5) * 0.4, starts[1] + len(segs[1]) / SR - 0.55, 0.9, 0.4)
        mus = reverb(dry, 3.0, 0.45) + reverb(perc, 2.0, 0.28) * 0.9 + reverb(fx, 1.2, 0.18) * 0.8
        mus /= np.abs(mus).max() + 1e-9
        we = int(0.05 * SR); en = np.sqrt(np.convolve(nar ** 2, np.ones(we) / we, 'same'))
        gate = np.clip(np.convolve((en > 0.02).astype(float), np.ones(int(0.45 * SR)) / int(0.45 * SR), 'same') * 2.2, 0, 1)
        mus = mus * (0.66 - 0.42 * gate)[:, None]
        fade = np.minimum(np.arange(N) / (0.4 * SR), 1) * np.minimum((N - np.arange(N)) / (1.8 * SR), 1); mus *= fade[:, None]
        mix = mus + nar[:, None] * 0.92; mix = np.tanh(mix * 1.1) / np.tanh(1.1); mix = mix / np.abs(mix).max() * 0.89
        wav = f'{out}/样音_{v}.wav'; sf.write(wav, mix, SR, subtype='PCM_16')
        mp3 = wav.replace('.wav', '.mp3')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-af', 'loudnorm=I=-16:TP=-1.5:LRA=9', '-ar', '48000', '-b:a', '192k', mp3], check=True)
        os.remove(wav)
        print(v, 'dur %.1fs' % total, 'lines', [round(len(s) / SR, 2) for s in segs], flush=True)


if __name__ == '__main__':
    main()
