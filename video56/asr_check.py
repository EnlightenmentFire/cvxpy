"""ASR 回读：faster-whisper（small）逐句识别，按无调拼音比对，输出错误率与可疑句。
usage: python asr_check.py [proc|mix]"""
import os, sys, json, re
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
from pypinyin import lazy_pinyin
from faster_whisper import WhisperModel
WORK = os.environ.get("WORK", "/tmp/claude-0/work")

def py(s):
    s = re.sub(r"[^一-鿿0-9]", "", s)
    return lazy_pinyin(s)

def ed(a, b):
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        p, d[0] = d[0], i
        for j, y in enumerate(b, 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (x != y))
    return d[-1]

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "proc"
    tl = json.load(open(f"{WORK}/timeline.json"))
    m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
    if mode == "mix":
        x, sr = sf.read(f"{WORK}/mix_music.wav"); x = x.mean(1)
    tot_e = tot_n = 0; bad = []
    for l in tl["lines"]:
        if mode == "proc":
            w, sr = sf.read(f"{WORK}/tts/proc/{l['id']}.wav")
        else:
            w = x[int(l["start"] * sr): int(l["end"] * sr)]
        w = resample_poly(w, 1, sr // 16000).astype(np.float32)
        segs, _ = m.transcribe(w, language="zh", beam_size=5, initial_prompt="以下是普通话的句子。")
        hyp = "".join(s.text for s in segs)
        a, b = py(l["text"]), py(hyp)
        e = ed(a, b); tot_e += e; tot_n += len(a)
        r = e / max(1, len(a))
        if r > 0.12:
            bad.append(dict(id=l["id"], ref=l["text"], hyp=hyp, err=round(r, 3)))
    rep = dict(mode=mode, pinyin_err=tot_e / tot_n, n_lines=len(tl["lines"]), suspicious=bad)
    json.dump(rep, open(f"{WORK}/asr_{mode}.json", "w"), ensure_ascii=False, indent=1)
    print(f"pinyin error rate {tot_e/tot_n:.3%}; suspicious {len(bad)}")
    for b in bad: print(b)

if __name__ == "__main__":
    main()
