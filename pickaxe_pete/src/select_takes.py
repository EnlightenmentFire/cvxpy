"""Director pass: transcribe every take, reject garbled ones, pick the liveliest accurate take per line,
trim silence, then apply per-character post FX. Writes audio/voice/<id>.wav (44.1k mono) + takes.json"""
import glob, json, os, re, subprocess, sys, warnings
import numpy as np, librosa, soundfile as sf
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))
from script_data import LINES
from transformers import pipeline

asr = pipeline("automatic-speech-recognition", model="openai/whisper-small.en", device="cpu")
NUM = {"100": "one hundred", "200": "two hundred", "40": "forty", "10": "ten", "1000": "thousand", "1,000": "thousand"}


def norm(s):
    s = s.lower().replace("-", " ")
    for k, v in NUM.items():
        s = re.sub(rf"\b{re.escape(k)}\b", v, s)
    s = re.sub(r"[^a-z' ]", " ", s)
    s = s.replace("riggies", "riggys").replace("ziggy", "riggy").replace("rigi", "riggy")
    return s.split()


def wer(ref, hyp):
    r, h = norm(ref), norm(hyp)
    d = np.zeros((len(r) + 1, len(h) + 1), int)
    d[:, 0] = range(len(r) + 1)
    d[0, :] = range(len(h) + 1)
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (r[i - 1] != h[j - 1]))
    return d[-1, -1] / max(1, len(r))


def prosody(y, sr):
    f0, _, _ = librosa.pyin(y, fmin=60, fmax=500, sr=sr, frame_length=1024)
    f0 = f0[~np.isnan(f0)]
    if len(f0) < 5:
        return 0.0
    st = 12 * np.log2(f0 / np.median(f0))
    return float(np.percentile(st, 90) - np.percentile(st, 10))


def squeeze_pauses(y, sr, max_gap):
    """Cap silences inside a line (keeps intended '...' beats when max_gap is larger)."""
    iv = librosa.effects.split(y, top_db=34, frame_length=512, hop_length=128)
    if len(iv) < 2:
        return y
    out = [y[iv[0][0]:iv[0][1]]]
    for (a0, a1), (b0, b1) in zip(iv[:-1], iv[1:]):
        gap = b0 - a1
        keep = min(gap, int(max_gap * sr))
        out.append(y[a1:a1 + keep // 2])
        out.append(y[b0 - (keep - keep // 2):b0])
        out.append(y[b0:b1])
    return np.concatenate(out)


def trim(y, sr, top_db=38):
    yt, idx = librosa.effects.trim(y, top_db=top_db, frame_length=512, hop_length=128)
    a = max(0, idx[0] - int(0.03 * sr))
    b = min(len(y), idx[1] + int(0.08 * sr))
    return y[a:b]


FX = {
    # gravel: slower, warm low end, light saturation; shouts get louder (he's a bit hard of hearing)
    "PETE": "highpass=f=70,lowshelf=g=4:f=180,equalizer=f=2500:t=q:w=1:g=2,asoftclip=type=tanh:threshold=0.6,acompressor=threshold=-20dB:ratio=3:attack=5:release=80",
    # dry and close
    "ZOE": "highpass=f=90,equalizer=f=4000:t=q:w=1:g=1.5,acompressor=threshold=-22dB:ratio=2.5:attack=8:release=120",
    # arcade announcer robot: slight pitch up, bitcrush, flange, big echo
    "RIGGY": "rubberband=pitch=1.07:tempo=1.1,acrusher=bits=9:mix=0.22:mode=log:aa=1,flanger=delay=2:depth=2:speed=0.6:width=60,"
             "equalizer=f=180:t=q:w=1:g=3,equalizer=f=3000:t=q:w=1:g=3,acompressor=threshold=-20dB:ratio=4:attack=3:release=60,"
             "aecho=0.85:0.6:45|95|160:0.32|0.22|0.14",
}
GAIN = {"PETE": 0.0, "ZOE": -1.0, "RIGGY": 1.0}
NO_STRETCH = {"s5_pete1"}  # tempo-up blurred "I'd build" -> "I built"; keep natural speed


def main():
    engine_dir = sys.argv[1] if len(sys.argv) > 1 else "tts/cb_takes"
    os.makedirs("audio/voice", exist_ok=True)
    only = set(sys.argv[2:])
    report = json.load(open("takes.json")) if only and os.path.exists("takes.json") else {}
    for lid, sc, spk, sub, tts, gap, style in LINES:
        if only and lid not in only:
            continue
        takes = sorted(glob.glob(f"{engine_dir}/{lid}__*.wav"))
        if not takes:
            print("MISSING", lid)
            continue
        scored = []
        for f in takes:
            y, sr = librosa.load(f, sr=24000)
            y = trim(y, sr)
            y = squeeze_pauses(y, sr, 0.42 if "..." in tts else 0.2)
            y16 = librosa.resample(y, orig_sr=sr, target_sr=16000)
            hyp = asr(y16.copy())["text"].strip()
            w = wer(tts, hyp)
            pr = prosody(y16, 16000)
            dur = len(y) / sr
            # words-per-second sanity (rejects stretched / rushed takes)
            wps = len(norm(tts)) / max(0.3, dur)
            ok_rate = 1.2 < wps < 4.6
            liveliness = pr if spk != "ZOE" else -abs(pr - 7.0)
            score = -w * 10 + liveliness * 0.15 - (0 if ok_rate else 3)
            scored.append((score, f, hyp, w, pr, dur, y, sr))
        scored.sort(key=lambda x: -x[0])
        best = scored[0]
        _, f, hyp, w, pr, dur, y, sr = best
        tmp = f"audio/voice/{lid}_raw.wav"
        sf.write(tmp, y, sr)
        g = GAIN[spk] + (3.0 if style == "shout" and spk == "PETE" else 0.0)
        tempo = {"PETE": ",rubberband=tempo=1.09", "ZOE": ",rubberband=tempo=1.07", "RIGGY": ""}[spk]
        if lid in NO_STRETCH:
            tempo = ""
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-af",
                        (tempo.lstrip(",") + "," if tempo else "") + FX[spk] + f",volume={g}dB,aresample=44100", "-ac", "1", f"audio/voice/{lid}.wav"], check=True)
        os.remove(tmp)
        out_dur = sf.info(f"audio/voice/{lid}.wav").duration
        report[lid] = dict(take=os.path.basename(f), wer=round(w, 3), pitch_range=round(pr, 1), dur=round(out_dur, 2), asr=hyp,
                           all=[(os.path.basename(s[1]), round(s[3], 2), round(s[4], 1)) for s in scored])
        flag = "  <-- CHECK" if w > 0.15 else ""
        print(f"{lid:<11} {os.path.basename(f):<20} wer={w:.2f} range={pr:4.1f} dur={out_dur:5.2f} | {hyp}{flag}", flush=True)
    json.dump(report, open("takes.json", "w"), indent=1)


if __name__ == "__main__":
    main()
