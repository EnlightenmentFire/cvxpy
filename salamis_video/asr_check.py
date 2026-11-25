"""ASR read-back (faster-whisper small, CPU int8) of processed lines; compares toneless pinyin.
usage: python asr_check.py [id_prefix ...]  -> prints per-line pinyin error rate, writes asr_report.json
"""
import os, sys, re, json
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
PROC = "/tmp/claude-0/work/tts/proc"
def py(s): return [p for p in lazy_pinyin(re.sub(r"[^一-鿿0-9]", "", s)) if p.strip()]
def ed(a, b):
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(b) + 1):
            cur = d[j]; d[j] = min(d[j] + 1, d[j - 1] + 1, prev + (a[i - 1] != b[j - 1])); prev = cur
    return d[len(b)]
m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=int(os.environ.get("THREADS", 2)))
args = sys.argv[1:]; rep = []
for d in all_lines():
    if args and not any(d["id"].startswith(a) for a in args): continue
    p = f"{PROC}/{d['id']}.wav"
    if not os.path.exists(p): continue
    import soundfile as sf, numpy as np; from scipy.signal import resample_poly
    x, sr = sf.read(p); x = resample_poly(x, 1, 3).astype(np.float32) if sr == 48000 else x.astype(np.float32)
    segs, _ = m.transcribe(x, language="zh", beam_size=5, initial_prompt="以下是普通话的句子。萨拉米斯，地米斯托克利，薛西斯，希罗多德，埃斯库罗斯。")
    hyp = "".join(s.text for s in segs)
    a, b = py(d["say"]), py(hyp); e = ed(a, b) / max(1, len(a))
    rep.append(dict(id=d["id"], err=round(e, 3), ref=d["say"], hyp=hyp)); print(f"{d['id']} {e:.2f} {hyp}", flush=True)
json.dump(rep, open("/tmp/claude-0/work/asr_report.json", "w"), ensure_ascii=False, indent=1)
tot = sum(r["err"] * len(py(r["ref"])) for r in rep) / max(1, sum(len(py(r["ref"])) for r in rep))
print(f"overall pinyin error {tot:.3f}; lines > 0.12: {[r['id'] for r in rep if r['err'] > 0.12]}")
