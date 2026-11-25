# -*- coding: utf-8 -*-
"""配乐候选的客观质检：时长、响度起伏、2–4 kHz 占比（越低越不抢人声）、有无人声（Whisper no_speech）。"""
import sys, json, numpy as np, soundfile as sf
from scipy.signal import welch

def qc(path, whisper=None):
    x, sr = sf.read(path, dtype="float32")
    if x.ndim == 2:
        m = x.mean(1)
    else:
        m = x
    dur = len(m) / sr
    win = int(0.4 * sr)
    k = len(m) // win
    st = 20 * np.log10(np.sqrt((m[:k * win].reshape(k, win) ** 2).mean(1)) + 1e-9)
    core = st[10:-10] if len(st) > 30 else st   # 去掉首尾各 4 秒（交叉淡化会盖住）
    f, p = welch(m, sr, nperseg=8192)
    tot = p[(f > 40) & (f < 16000)].sum()
    band = p[(f >= 2000) & (f <= 4000)].sum() / tot
    low = p[(f >= 40) & (f <= 250)].sum() / tot
    cent = (f * p).sum() / p.sum()
    out = dict(file=path, dur=round(dur, 1), sr=sr, rms=round(float(20 * np.log10(np.sqrt((m ** 2).mean()) + 1e-9)), 1),
               st_p95_minus_p50=round(float(np.percentile(core, 95) - np.percentile(core, 50)), 1),
               max_jump_db=round(float(np.percentile(np.abs(np.diff(core)), 99)), 1),
               band_2_4k=round(float(band) * 100, 2), low_40_250=round(float(low) * 100, 1), centroid=int(cent))
    if whisper is not None:
        import librosa
        w16 = librosa.resample(m, orig_sr=sr, target_sr=16000)
        # 抽三段各 20 秒检查有没有人声
        L = len(w16)
        picks = [w16[int(L * f): int(L * f) + 20 * 16000] for f in (0.1, 0.45, 0.75)]
        txt, nsp_all = "", []
        for pc in picks:
            segs, info = whisper.transcribe(pc, vad_filter=False, beam_size=1)
            segs = list(segs)
            txt += "".join(s.text for s in segs).strip()
            nsp_all += [s.no_speech_prob for s in segs]
        nsp = float(np.mean(nsp_all)) if nsp_all else 1.0
        out.update(asr_text=txt[:60], no_speech=round(nsp, 2))
    return out

if __name__ == "__main__":
    from faster_whisper import WhisperModel
    wm = WhisperModel("/home/user/work/models/whisper-large-v3-turbo-ct2", device="cpu", compute_type="int8", cpu_threads=2)
    for p in sys.argv[1:]:
        print(json.dumps(qc(p, wm), ensure_ascii=False))
