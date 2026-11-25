"""Mix voice + music + sfx. Music sits ~21 dB under the voice while it speaks, ~17 dB in pauses >= 0.8 s.
Writes WORK/audio/mix_music.wav and mix_nomusic.wav (pre-loudnorm) + narration.wav and a report."""
import os, json
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.ndimage import uniform_filter1d

WORK = os.environ.get("WORK", "/tmp/claude-0/work")
SR = 48000
UNDER_SPEECH, UNDER_PAUSE = -21.0, -17.0


def main():
    tl = json.load(open(f"{WORK}/timeline.json"))
    n = int((tl["total"] + 0.5) * SR)
    V = np.zeros(n)
    speech = np.zeros(n, bool)
    for d in tl["lines"]:
        x, sr = sf.read(f"{WORK}/tts/proc/{d['id']}.wav")
        assert sr == SR
        i = int(d["t0"] * SR)
        V[i:i + len(x)] += x[: n - i]
        speech[i:i + len(x)] = True
    meter = pyln.Meter(SR)
    lv = meter.integrated_loudness(V)
    V *= 10 ** ((-17.0 - lv) / 20)
    lv = -17.0
    sf.write(f"{WORK}/audio/narration.wav", V.astype(np.float32), SR)
    # pause mask: fill short gaps (< 0.8 s) as speech
    sp = speech.copy()
    idx = np.flatnonzero(np.diff(sp.astype(int)))
    starts = list(np.flatnonzero(np.diff(np.r_[0, sp.astype(int)]) == -1))
    ends = list(np.flatnonzero(np.diff(np.r_[sp.astype(int), 0]) == 1))
    for a in starts:
        b = next((e for e in ends if e >= a), None)
        if b is not None and (b - a) / SR < 0.8:
            sp[a:b + 1] = True
    M, _ = sf.read(f"{WORK}/audio/music.wav")
    S, _ = sf.read(f"{WORK}/audio/sfx.wav")
    M = np.pad(M, ((0, max(0, n - len(M))), (0, 0)))[:n]
    S = np.pad(S, ((0, max(0, n - len(S))), (0, 0)))[:n]
    # level-follow the music: 3 s window loudness proxy (K-weighting ignored; RMS is fine for a slow leveller)
    ms = (M ** 2).mean(1)
    rms = np.sqrt(uniform_filter1d(ms, 3 * SR) + 1e-12)
    ref = meter.integrated_loudness(M)
    glob = np.sqrt(ms.mean())
    lev = np.clip(glob / rms, 10 ** (-6 / 20), 10 ** (8 / 20)) ** 0.7       # partial levelling
    target = np.where(sp, UNDER_SPEECH, UNDER_PAUSE)
    target = uniform_filter1d(target.astype(float), int(0.6 * SR))           # ~0.6 s ramps
    g = 10 ** ((lv + target - ref) / 20) * lev
    g = uniform_filter1d(g, int(0.3 * SR))
    Mg = M * g[:, None]
    # sfx: about 16 dB under voice (hook bell is louder by design; it was set in music.py)
    sref = meter.integrated_loudness(S[int(12 * SR):]) if n > 20 * SR else meter.integrated_loudness(S)
    Sg = S * 10 ** ((lv - 16 - sref) / 20)
    Vs = np.stack([V, V], 1)
    mixm = Vs + Mg + Sg
    mixn = Vs + Sg
    sf.write(f"{WORK}/audio/mix_music.wav", mixm.astype(np.float32), SR)
    sf.write(f"{WORK}/audio/mix_nomusic.wav", mixn.astype(np.float32), SR)
    # report: music vs voice in speech segments
    rep = {}
    for name, a, b in (("open_0_60", 0, 60), ("mid_300_360", 300, 360), ("end_last60", tl["total"] - 62, tl["total"] - 2)):
        i, j = int(a * SR), int(b * SR)
        rep[name] = dict(voice=round(meter.integrated_loudness(Vs[i:j]), 1), music=round(meter.integrated_loudness(Mg[i:j]), 1))
        rep[name]["diff_db"] = round(rep[name]["voice"] - rep[name]["music"], 1)
    rep["voice_integrated"] = round(meter.integrated_loudness(Vs), 1)
    rep["music_integrated"] = round(meter.integrated_loudness(Mg), 1)
    json.dump(rep, open(f"{WORK}/audio/mix_report.json", "w"), indent=1)
    print(rep)


if __name__ == "__main__":
    main()
