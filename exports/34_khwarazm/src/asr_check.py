"""ASR read-back of each processed line (faster-whisper), compare toneless pinyin; report CER per line.
usage: python asr_check.py [ids...]"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin
W = "/tmp/claude-0/work"
def norm(s): return re.sub(r"[^一-鿿0-9A-Za-z]", "", s)
def py(s): return lazy_pinyin(norm(s))
def ed(a, b):
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(b) + 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (a[i - 1] != b[j - 1]))
    return d[-1]
def main():
    ids = sys.argv[1:]
    m = WhisperModel("/tmp/claude-0/models/fw-medium", device="cpu", compute_type="int8", cpu_threads=int(os.environ.get("NT", 4)))
    res = {}
    for d in all_lines():
        if ids and d["id"] not in ids: continue
        p = f"{W}/tts/proc/{d['id']}.wav"
        if not os.path.exists(p): continue
        segs, _ = m.transcribe(p, language="zh", beam_size=5, initial_prompt="以下是普通话的历史纪录片旁白。")
        hyp = "".join(s.text for s in segs)
        ref = d["say"]
        a, b = py(ref), py(hyp)
        e = ed(a, b) / max(1, len(a))
        res[d["id"]] = dict(ref=ref, hyp=hyp, per=round(e, 3))
        flag = "  <<<" if e > 0.12 else ""
        print(f"{d['id']} {e:.2f} | {hyp}{flag}", flush=True)
    old = json.load(open(f"{W}/asr.json")) if os.path.exists(f"{W}/asr.json") else {}
    old.update(res); json.dump(old, open(f"{W}/asr.json", "w"), ensure_ascii=False, indent=1)
    tot = [v["per"] for v in old.values()]
    print(f"lines {len(tot)}, mean pinyin err {sum(tot)/len(tot):.3f}, flagged {sum(t > 0.12 for t in tot)}")
if __name__ == "__main__":
    main()
