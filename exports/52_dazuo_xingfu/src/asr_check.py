"""faster-whisper read-back; compare toneless pinyin; report per-line error rate.
usage: python asr_check.py proc|raw [ids...]"""
import sys, os, re, json
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
D = os.path.dirname(os.path.abspath(__file__))
src = sys.argv[1]; ids = sys.argv[2:]
NUM = {"0":"零","1":"一","2":"二","3":"三","4":"四","5":"五","6":"六","7":"七","8":"八","9":"九",".":"点","%":"百分之"}
def norm(s):
    s = re.sub(r"[^一-鿿0-9.%]", "", s)
    return s
def py(s):
    return [p for p in lazy_pinyin(norm(s)) if p]
def ed(a, b):
    dp = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, len(b) + 1):
            cur = dp[j]
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev = cur
    return dp[-1]
m = WhisperModel(os.environ.get("ASR", "small"), device="cpu", compute_type="int8", cpu_threads=int(os.environ.get("NT", 2)))
res = []
for d in all_lines():
    if ids and d["id"] not in ids: continue
    p = f"{D}/tts/{src}/{d['id']}.wav"
    if not os.path.exists(p): continue
    x, sr = sf.read(p); x = x.astype(np.float32)
    if sr != 16000:
        g = np.gcd(sr, 16000); x = resample_poly(x, 16000 // g, sr // g).astype(np.float32)
    segs, _ = m.transcribe(x, language="zh", beam_size=5, initial_prompt="以下是普通话的句子。")
    hyp = "".join(s.text for s in segs)
    # convert digits in hyp to hanzi-ish pinyin by dropping (numbers in ASR are often digits)
    import cn2an
    h2 = re.sub(r"(\d),(\d)", r"\1\2", hyp)
    try:
        h2 = cn2an.transform(h2, "an2cn")
    except Exception:
        pass
    a, b = py(d["say"].replace("两", "二")), py(h2.replace("两", "二"))
    has_digit = bool(re.search(r"\d", hyp))
    e = ed(a, b) / max(1, len(a))
    res.append(dict(id=d["id"], err=round(e, 3), digits=has_digit, ref=d["say"], hyp=hyp))
    flag = "  <<<" if e > 0.10 else ""
    print(f"{d['id']} {e:.3f}{flag} | {hyp}", flush=True)
json.dump(res, open(f"{D}/tts/asr_{src}.json", "w"), ensure_ascii=False, indent=1)
