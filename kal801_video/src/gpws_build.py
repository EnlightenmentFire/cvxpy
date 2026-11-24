# -*- coding: utf-8 -*-
"""近地警告（GPWS）机械人声：Qwen3-TTS VoiceDesign 生成平直的合成男声 → 机械化处理。
不使用任何真实 GPWS 录音。产物：$WORK/gpws/<key>.wav（48 kHz）与 gpws_manifest.json
"""
import json, os, sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt, resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
WORK = os.environ.get("KAL_WORK", "/tmp/claude-0/-home-user-cvxpy/44060277-be5b-5d12-bb11-0e70dedfd6d4/scratchpad/work")
OUT = os.path.join(WORK, "gpws")
os.makedirs(OUT, exist_ok=True)
SR = 48000

INSTR = ("A flat, emotionless synthetic male voice of an automated aircraft warning computer. "
         "Mechanical, monotone, clipped, very clear, mid-low pitch, no breathing, no emotion.")
WORDS = ["five hundred", "one thousand", "minimums", "sink rate", "one hundred", "fifty", "forty", "thirty", "twenty"]
# 组合短语：按 NTSB 附录的时间间隔拼接
COMBOS = {
    "five hundred": [("five hundred", 0.0)],
    "one thousand": [("one thousand", 0.0)],
    "minimums. minimums.": [("minimums", 0.0), ("minimums", 0.78)],
    "sink rate.": [("sink rate", 0.0)],
    "one hundred. fifty. forty. thirty. twenty.": [("one hundred", 0.0), ("fifty", 0.79), ("forty", 1.14),
                                                   ("thirty", 1.45), ("twenty", 1.76)],
}


def mechanize(w, sr):
    """窄带 + 轻失真 + 降采样保持 + 环形调制 + 短驻留，做成机器喊话的质感。"""
    w = w / (np.max(np.abs(w)) + 1e-9)
    # 降采样到 11.025k 再回升（采样保持感）
    lo = resample_poly(w, 11025, sr)
    q = np.round(lo * 64) / 64.0          # 6-bit 量化
    w2 = np.repeat(q, int(np.ceil(sr / 11025)))[: int(len(lo) * sr / 11025)]
    w2 = 0.65 * w2 + 0.35 * resample_poly(lo, sr, 11025)[: len(w2)]
    sos = butter(4, [420, 3300], btype="bandpass", fs=sr, output="sos")
    w2 = sosfilt(sos, w2)
    t = np.arange(len(w2)) / sr
    w2 = w2 * (0.82 + 0.18 * np.sin(2 * np.pi * 70 * t))   # 轻微金属感
    w2 = np.tanh(w2 * 2.2) / np.tanh(2.2)
    d = int(0.011 * sr)
    out = w2.copy()
    out[d:] += 0.22 * w2[:-d]                               # 小喇叭的短驻留
    out = out / (np.max(np.abs(out)) + 1e-9) * 0.9
    return out.astype(np.float32)


def trim(w, sr, thr_db=-38):
    a = np.abs(w)
    k = int(0.01 * sr)
    env = np.convolve(a, np.ones(k) / k, mode="same")
    idx = np.where(20 * np.log10(env + 1e-9) > 20 * np.log10(env.max() + 1e-9) + thr_db)[0]
    if len(idx) == 0:
        return w
    return w[max(0, idx[0] - int(0.01 * sr)): idx[-1] + int(0.03 * sr)]


NUM = {"500": "five hundred", "1,000": "one thousand", "1000": "one thousand", "100": "one hundred", "50": "fifty",
       "40": "forty", "30": "thirty", "20": "twenty"}
# 倒数里每个词的最长时长（按 NTSB 附录的间隔）
MAXDUR = {"one hundred": 0.74, "fifty": 0.33, "forty": 0.30, "thirty": 0.30, "twenty": 0.40, "five hundred": 0.85,
          "one thousand": 0.95, "minimums": 0.72, "sink rate": 0.85}


def norm(h):
    h = h.lower().strip(" .!,")
    return NUM.get(h, h).replace("-", " ")


def fit(w, sr, maxdur, tag):
    import subprocess
    d = len(w) / sr
    if d <= maxdur:
        return w
    a, b = os.path.join(OUT, f"_fit_{tag}_a.wav"), os.path.join(OUT, f"_fit_{tag}_b.wav")
    sf.write(a, w, sr)
    subprocess.run(["rubberband", "-q", "-3", "-t", f"{maxdur / d:.4f}", a, b], check=True)
    y, _ = sf.read(b, dtype="float32")
    return y


def reselect():
    import glob
    from asr_check import transcribe
    words = {}
    for wd in WORDS:
        cands = []
        for p in sorted(glob.glob(os.path.join(OUT, f"_raw_{wd.replace(' ', '_')}_*.wav"))):
            w, sr = sf.read(p, dtype="float32")
            hyp = norm(transcribe(p, lang="en"))
            cands.append((0 if hyp == wd else 1, len(w) / sr, p, hyp))
        cands.sort()
        ok, dur, p, hyp = cands[0]
        print(wd, "->", os.path.basename(p), f"{dur:.2f}s", hyp, flush=True)
        w, sr = sf.read(p, dtype="float32")
        w = resample_poly(w, SR, sr).astype(np.float32)
        w = fit(w, SR, MAXDUR[wd], wd.replace(" ", "_"))
        words[wd] = mechanize(w, SR)
    build_combos(words)


def build_combos(words):
    man = {}
    for key, parts in COMBOS.items():
        total = max(off + len(words[wd]) / SR for wd, off in parts)
        buf = np.zeros(int(total * SR) + 10, np.float32)
        for wd, off in parts:
            s = int(off * SR)
            buf[s:s + len(words[wd])] += words[wd]
        fn = os.path.join(OUT, key.replace(" ", "_").replace(".", "") + ".wav")
        sf.write(fn, buf, SR)
        man[key] = dict(file=fn, dur=round(len(buf) / SR, 3))
        print("combo", key, man[key]["dur"])
    json.dump(man, open(os.path.join(WORK, "gpws_manifest.json"), "w"), indent=1)


def main():
    import torch
    torch.set_num_threads(4)
    from qwen_tts import Qwen3TTSModel
    from asr_check import transcribe
    m = Qwen3TTSModel.from_pretrained("/opt/models/Qwen3-TTS-12Hz-1.7B-VoiceDesign", dtype=torch.bfloat16,
                                      device_map="cpu", attn_implementation="sdpa")
    words = {}
    for wd in WORDS:
        best = None
        for k in range(5):
            torch.manual_seed(500 + k * 31 + len(wd))
            wavs, sr = m.generate_voice_design(text=wd.capitalize() + ".", instruct=INSTR, language="English")
            w = trim(np.asarray(wavs[0], np.float32), sr)
            p = os.path.join(OUT, f"_raw_{wd.replace(' ', '_')}_{k}.wav")
            sf.write(p, w, sr)
            hyp = transcribe(p, lang="en").lower().strip(" .!,")
            ok = hyp.replace("-", " ") == wd
            dur = len(w) / sr
            print(wd, k, f"{dur:.2f}s", hyp, ok, flush=True)
            score = (0 if ok else 10) + dur
            if best is None or score < best[0]:
                best = (score, w, sr)
            if ok and dur < 0.9:
                break
        w = resample_poly(best[1], SR, best[2]).astype(np.float32)
        words[wd] = mechanize(w, SR)
    man = {}
    for key, parts in COMBOS.items():
        total = max(off + len(words[wd]) / SR for wd, off in parts)
        buf = np.zeros(int(total * SR) + 10, np.float32)
        for wd, off in parts:
            s = int(off * SR)
            buf[s:s + len(words[wd])] += words[wd]
        fn = os.path.join(OUT, key.replace(" ", "_").replace(".", "") + ".wav")
        sf.write(fn, buf, SR)
        man[key] = dict(file=fn, dur=round(len(buf) / SR, 3))
        print("combo", key, man[key]["dur"])
    json.dump(man, open(os.path.join(WORK, "gpws_manifest.json"), "w"), indent=1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--reselect":
        reselect()
    else:
        main()
        reselect()
