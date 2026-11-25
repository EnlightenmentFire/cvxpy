"""ASR read-back of TTS lines: faster-whisper small, compare toneless pinyin with the TTS input text.
usage: python asr_check.py [ids...]"""
import sys, os, json, re, difflib, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import all_lines, tts_text
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
import cn2an
RAW = "/home/user/work/tts/raw"
def py(s):
    s = re.sub(r"\d+", lambda m: cn2an.an2cn(m.group(0), "low"), s)
    return [p for p in lazy_pinyin(re.sub(r"[^一-鿿0-9]", "", s))]
m = WhisperModel("/home/user/work/models/whisper-small", device="cpu", compute_type="int8", cpu_threads=int(os.environ.get("THREADS", 2)))
args = sys.argv[1:]
res = {}
p_out = "/home/user/work/tts/asr.json"
if os.path.exists(p_out): res = json.load(open(p_out))
for d in all_lines():
    if args and not any(d["id"].startswith(a) for a in args): continue
    w = f"{RAW}/{d['id']}.wav"
    if not os.path.exists(w): continue
    meta = json.load(open(f"{RAW}/{d['id']}.json"))
    if d["id"] in res and res[d["id"]].get("seed") == meta["seed"] and res[d["id"]].get("tts") == meta["tts"]: continue
    import soundfile as sf, numpy as np
    from scipy.signal import resample_poly
    x, sr = sf.read(w); x = x.astype(np.float32)
    x = resample_poly(x, 16000, sr).astype(np.float32) if sr != 16000 else x
    segs, _ = m.transcribe(x, language="zh", beam_size=5, initial_prompt="以下是三国历史纪录片旁白。")
    hyp = "".join(s.text for s in segs)
    a, b = py(meta["tts"]), py(hyp)
    r = difflib.SequenceMatcher(None, a, b).ratio()
    res[d["id"]] = dict(seed=meta["seed"], tts=meta["tts"], hyp=hyp, ratio=round(r, 3))
    print(f"{d['id']} {r:.2f} | {meta['tts']} | {hyp}", flush=True)
    json.dump(res, open(p_out, "w"), ensure_ascii=False, indent=1)
