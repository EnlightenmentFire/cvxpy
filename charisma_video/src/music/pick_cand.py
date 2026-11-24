# -*- coding: utf-8 -*-
"""Score MusicGen candidates: least competition with the voice (1-4 kHz share), calmness (onset density),
tonal fit to D minor (so sections crossfade cleanly), noisiness, and vocal-like content (ASR check)."""
import sys, os, glob, json
import numpy as np, librosa

KS_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

def key_fit(y, sr):
    ch = librosa.feature.chroma_cqt(y=y, sr=sr).mean(1)
    prof = np.roll(KS_MINOR, 2)          # D minor (tonic index 2)
    return float(np.corrcoef(ch, prof)[0, 1])

def analyse(path, asr=None):
    y, sr = librosa.load(path, sr=32000, mono=True)
    S = np.abs(librosa.stft(y, n_fft=2048)) ** 2
    f = librosa.fft_frequencies(sr=sr, n_fft=2048)
    band = S[(f >= 1000) & (f <= 4000)].sum() / (S.sum() + 1e-9)
    onset = float(librosa.onset.onset_strength(y=y, sr=sr).mean())
    flat = float(librosa.feature.spectral_flatness(y=y).mean())
    rms = librosa.feature.rms(y=y)[0]
    dyn = float(20 * np.log10((np.percentile(rms, 95) + 1e-9) / (np.percentile(rms, 20) + 1e-9)))
    words = ""
    if asr is not None:
        import soundfile as sf
        y16 = librosa.resample(y, orig_sr=sr, target_sr=16000)
        segs, info = asr.transcribe(y16, beam_size=1, vad_filter=True)
        words = "".join(s.text for s in segs if s.no_speech_prob < 0.5).strip()
    return dict(file=os.path.basename(path), vocal_band=round(float(band), 3), onset=round(onset, 3),
                flatness=round(flat, 4), dyn_db=round(dyn, 1), dminor=round(key_fit(y, sr), 3), asr=words)

def score(m, layer):
    s = 0.0
    s -= 6.0 * m["vocal_band"]                 # leave room for the voice
    s -= (1.5 if layer == "L1" else 0.8) * m["onset"]
    s -= 20 * m["flatness"]                    # noisy / hissy
    s += 1.5 * m["dminor"]                     # tonal centre for clean crossfades
    s -= 0.03 * max(0, m["dyn_db"] - 14)       # sudden jumps poke out
    s -= 2.0 if len(m["asr"]) > 3 else 0.0     # vocal-like content
    return round(s, 3)

if __name__ == "__main__":
    cand_dir, fw = sys.argv[1], sys.argv[2]
    from faster_whisper import WhisperModel
    asr = WhisperModel(fw, device="cpu", compute_type="int8", cpu_threads=2)
    res = {}
    for layer in ("L1", "L2", "L3"):
        rows = []
        for p in sorted(glob.glob(os.path.join(cand_dir, f"{layer}_seed*.wav"))):
            m = analyse(p, asr); m["score"] = score(m, layer); rows.append(m)
        rows.sort(key=lambda r: -r["score"])
        res[layer] = rows
        for r in rows:
            print(layer, r)
    json.dump(res, open(os.path.join(cand_dir, "scores.json"), "w"), ensure_ascii=False, indent=1)
    choice = {l: "cand/" + rows[0]["file"] for l, rows in res.items() if rows}
    json.dump(choice, open(os.path.join(os.path.dirname(cand_dir.rstrip("/")), "choice.json"), "w"), indent=1)
    print("choice", choice)
