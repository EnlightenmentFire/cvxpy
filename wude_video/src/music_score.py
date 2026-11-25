"""Pick, for each layer, the version that is least likely to fight the narration (配乐规范 §三 1).

Objective proxies (I cannot listen, so these are explicit and reported):
  * speech-band share   : energy 1-4 kHz / total  (lower = leaves room for the voice)
  * loudness steadiness : std of 1 s short-term level (lower = nothing suddenly pops out)
  * peakiness           : 95th pct - median of 100 ms levels (lower = fewer sudden hits)
  * vocal-like content  : Whisper finds words in it -> rejected
  * broken output       : near-silent or clipped -> rejected
Score = 0.6*z(band) + 0.2*z(steadiness) + 0.2*z(peakiness); lowest wins.
usage: music_score.py <clips_dir> <out.json>
"""
import glob
import json
import os
import sys

import numpy as np
import soundfile as sf
from scipy.signal import welch


def metrics(path, asr=None):
    a, sr = sf.read(path)
    m = a.mean(1) if a.ndim == 2 else a
    f, p = welch(m, sr, nperseg=4096)
    band = p[(f >= 1000) & (f <= 4000)].sum() / (p.sum() + 1e-12)
    w1 = sr
    lv1 = [10 * np.log10(np.mean(m[i:i + w1] ** 2) + 1e-12) for i in range(0, len(m) - w1, w1 // 2)]
    w2 = sr // 10
    lv2 = np.array([10 * np.log10(np.mean(m[i:i + w2] ** 2) + 1e-12) for i in range(0, len(m) - w2, w2)])
    rms_db = 10 * np.log10(np.mean(m ** 2) + 1e-12)
    clip = float(np.mean(np.abs(a) > 0.99))
    out = dict(path=path, dur=len(m) / sr, band=float(band), steady=float(np.std(lv1)),
               peaky=float(np.percentile(lv2, 95) - np.median(lv2)), rms_db=float(rms_db), clip=clip)
    out["vocal_text"] = asr(m, sr) if asr else ""
    out["ok"] = (rms_db > -45) and clip < 0.001 and len(out["vocal_text"].strip()) < 4
    return out


def make_asr():
    from faster_whisper import WhisperModel
    import librosa
    mdl = WhisperModel("/home/user/wude_build/models/fw-large-v3-turbo", device="cpu", compute_type="int8",
                       cpu_threads=2)

    def f(m, sr):
        y = librosa.resample(m.astype(np.float32), orig_sr=sr, target_sr=16000)
        segs, _ = mdl.transcribe(y, beam_size=1, vad_filter=True, condition_on_previous_text=False)
        return "".join(s.text for s in segs if s.no_speech_prob < 0.5)
    return f


def main():
    d, out = sys.argv[1], sys.argv[2]
    asr = make_asr()
    res = {}
    for p in sorted(glob.glob(f"{d}/*_v[0-9].wav")):
        layer = os.path.basename(p).rsplit("_v", 1)[0]
        res.setdefault(layer, []).append(metrics(p, asr))
    choice = {}
    for layer, rows in res.items():
        ok = [r for r in rows if r["ok"]] or rows
        for key in ("band", "steady", "peaky"):
            vals = np.array([r[key] for r in ok])
            sd = vals.std() or 1.0
            for r in ok:
                r["z_" + key] = float((r[key] - vals.mean()) / sd)
        for r in ok:
            r["score"] = 0.6 * r["z_band"] + 0.2 * r["z_steady"] + 0.2 * r["z_peaky"]
        ok.sort(key=lambda r: r["score"])
        choice[layer] = [r["path"] for r in ok]
        for r in rows:
            print(f"{layer:13s} {os.path.basename(r['path']):22s} band={r['band']:.3f} steady={r['steady']:.2f} "
                  f"peaky={r['peaky']:.2f} rms={r['rms_db']:.1f} ok={r['ok']} score={r.get('score', float('nan')):.2f} "
                  f"vocal='{r['vocal_text'][:20]}'", flush=True)
    json.dump(dict(choice=choice, metrics=res), open(out, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
