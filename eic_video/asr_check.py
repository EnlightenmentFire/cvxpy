"""ASR read-back of processed voice lines with faster-whisper; compares toneless pinyin. usage: python asr_check.py [prefix...]"""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines
from faster_whisper import WhisperModel
from pypinyin import lazy_pinyin

PROC = "/tmp/claude-0/work/tts/proc"
OUT = "/tmp/claude-0/work/asr.json"


def py(s):
    s = re.sub(r"[^一-鿿A-Za-z0-9]", "", s)
    return [p for p in lazy_pinyin(s) if p.strip()]


def ed(a, b):
    dp = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, len(b) + 1):
            cur = dp[j]
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev = cur
    return dp[-1]


def main():
    pre = [a for a in sys.argv[1:] if not a.startswith("-")]
    model = WhisperModel(os.environ.get("ASR_MODEL", "small"), device="cpu", compute_type="int8", cpu_threads=int(os.environ.get("THREADS", 4)))
    res = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for d in all_lines():
        if pre and not any(d["id"].startswith(p) for p in pre):
            continue
        p = f"{PROC}/{d['id']}.wav"
        if not os.path.exists(p):
            continue
        segs, _ = model.transcribe(p, language="zh", beam_size=5, initial_prompt="以下是普通话的句子。东印度公司，纳瓦布，克莱武，普拉西，孟加拉。")
        hyp = "".join(s.text for s in segs)
        a, b = py(d["say"]), py(hyp)
        er = ed(a, b) / max(1, len(a))
        res[d["id"]] = dict(ref=d["say"], hyp=hyp, per=round(er, 3))
        flag = "  <<<" if er > 0.12 else ""
        print(f"{d['id']} {er:.3f}{flag} | {hyp}", flush=True)
    json.dump(res, open(OUT, "w"), ensure_ascii=False, indent=1)
    allp = [v["per"] for v in res.values()]
    print("mean pinyin error", round(sum(allp) / max(1, len(allp)), 4), "flagged", [k for k, v in res.items() if v["per"] > 0.12])


if __name__ == "__main__":
    main()
