"""faster-whisper small 回读，按无调拼音比对（逐句字错率）"""
import sys, os, re, json
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import all_lines, tts_text
PROC = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/w74/tts/proc"
def py(s):
    s = re.sub(r"[^一-鿿0-9]", "", s)
    return lazy_pinyin(s)
def ed(a, b):
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(b) + 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (a[i - 1] != b[j - 1]))
    return d[len(b)]
wm = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=int(os.environ.get("NT", 2)))
res = {}
tot_e = tot_n = 0
for d in all_lines():
    p = f"{PROC}/{d['id']}.wav"
    if not os.path.exists(p): continue
    x, sr = sf.read(p); x = x if x.ndim == 1 else x.mean(1)
    x = resample_poly(x, 1, sr // 16000).astype(np.float32)
    segs, _ = wm.transcribe(x, language="zh", beam_size=3, initial_prompt="以下是普通话的句子。")
    hyp = "".join(s.text for s in segs)
    ref = tts_text(d["say"]).replace("一八九", "189").replace("一九一", "191").replace("一九二", "192")
    a, b = py(ref), py(hyp)
    a2 = py(tts_text(d["say"]))
    e = min(ed(a, b), ed(a2, b)); n = len(a2)
    tot_e += e; tot_n += n
    res[d["id"]] = dict(cer=e / max(n, 1), hyp=hyp, ref=d["say"])
    flag = " <<<" if e / max(n, 1) > 0.08 else ""
    print(f"{d['id']} {e/max(n,1):.2f} {hyp}{flag}", flush=True)
json.dump(res, open(os.path.join(PROC, "..", "asr.json"), "w"), ensure_ascii=False, indent=1)
print("TOTAL pinyin error rate %.3f" % (tot_e / max(tot_n, 1)))
