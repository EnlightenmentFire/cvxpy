"""比较各版配乐「抢不抢人声」：人声主频带（1–4 kHz）能量占比、音量起伏、调性。"""
import sys, numpy as np, soundfile as sf, librosa
for f in sys.argv[1:]:
    y, sr = sf.read(f); y = y.mean(1) if y.ndim > 1 else y
    S = np.abs(librosa.stft(y, n_fft=4096, hop_length=1024)) ** 2
    fr = librosa.fft_frequencies(sr=sr, n_fft=4096)
    tot = S.sum()
    band = S[(fr >= 1000) & (fr <= 4000)].sum() / tot
    low = S[fr < 250].sum() / tot
    rms = librosa.feature.rms(y=y, frame_length=sr // 2, hop_length=sr // 4)[0]
    rd = 20 * np.log10(rms + 1e-9)
    flux = np.mean(np.abs(np.diff(rd)))
    print(f"{f}: 1-4kHz share {band*100:.1f}%  <250Hz share {low*100:.1f}%  loudness swing {flux:.2f} dB/0.25s  range {np.percentile(rd,95)-np.percentile(rd,5):.1f} dB")
