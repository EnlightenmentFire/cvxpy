"""Tabulate per-line voice QA (pitch, ASR readback, speaking rate, attempts)."""
import json, os, sys
from script_data import SEGMENTS

def main(lines_dir, out_md, only=None):
    rows, fails = [], []
    for seg in SEGMENTS:
        for ln in seg["lines"]:
            if only and ln["id"] not in only:
                continue
            p = os.path.join(lines_dir, ln["id"] + ".json")
            if not os.path.exists(p):
                continue
            m = json.load(open(p))
            if m.get("tts") != ln["tts"]:
                continue
            ch = m["chosen"]
            rows.append((ln["id"], ch["f0"], ch["per"], ch["cps"], ch["dur"], len(m["tries"]), m["passed"], ch["asr"]))
            if not m["passed"]:
                fails.append(ln["id"])
    f0s = [r[1] for r in rows]
    pitch_ok = sum(1 for r in rows if 85 <= r[1] <= 105)
    asr_ok = sum(1 for r in rows if r[2] <= 0.08)
    slow = [r[0] for r in rows if r[3] < 3.6]
    out = ["# 配音逐句质检", "",
           f"共 {len(rows)} 句；中位音高 {min(f0s):.1f}–{max(f0s):.1f} Hz，{pitch_ok}/{len(rows)} 句在 85–105 Hz；"
           f"ASR 回读合格 {asr_ok}/{len(rows)} 句（拼音错误率为 0 的 {sum(1 for r in rows if r[2] == 0)} 句）。"
           + (f"另有 {len(slow)} 句只是语速低于 3.6 字/秒的内部提示（短句带停顿）：{'、'.join(slow)}。" if slow else ""), "",
           "ASR 回读按拼音比对（同音字算对，数字先换成汉字读法）。", "",
           "| 编号 | 中位音高 Hz | 拼音错误率 | 字/秒 | 时长 s | 生成次数 | ASR 回读 |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| `{r[0]}` | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[7]} |")
    open(out_md, "w").write("\n".join(out) + "\n")
    print(out[2])

if __name__ == "__main__":
    only = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    main(sys.argv[1], sys.argv[2], only)
