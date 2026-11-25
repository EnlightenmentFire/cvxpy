"""整理交付物到 exports/51_quantum-eraser-repentance/：逐句旁白稿（json/txt，便于在 box 上重配）、字幕、SCRIPT.md。
usage: python export.py <out_dir>
"""
import sys, os, json, shutil, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script_data import all_lines, SCENES

WORK = os.environ.get("WORK", "/tmp/claude-0/work")


def fmt(t):
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:05.2f}"


def main(out):
    os.makedirs(out, exist_ok=True)
    tl = json.load(open(f"{WORK}/timeline.json"))
    by = {e["id"]: e for e in tl["lines"]}
    sents = []
    for d in all_lines():
        e = by[d["id"]]
        sents.append(dict(id=d["id"], scene=d["scene"], kind=("经文/原句" if d["k"] == "q" else "旁白"), text=d["say"], subtitle=d["sub"],
                          pause_after=d["gap"], start=e["start"], end=e["end"]))
    json.dump(dict(voice="托克维尔声音（Qwen3-TTS-12Hz-1.7B-Base ICL 克隆，参考 voice_design_reference）",
                   tempo={"旁白": 1.06, "经文/原句": 1.0}, sentences=sents),
              open(f"{out}/sentences.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
    with open(f"{out}/sentences.txt", "w", encoding="utf8") as f:
        for s in sents:
            f.write(s["text"] + "\n")
    shutil.copy(f"{WORK}/narration.srt", f"{out}/narration.srt")
    # SCRIPT.md：带时间码的可读稿
    names = dict(SCENES)
    with open(f"{out}/SCRIPT.md", "w", encoding="utf8") as f:
        f.write("# 量子擦除，真的能改写过去吗？——逐句稿（带成片时间码）\n\n")
        cur = None
        for s in sents:
            if s["scene"] != cur:
                cur = s["scene"]
                f.write(f"\n## {names[cur]}\n\n")
            q = "（原句）" if s["kind"] != "旁白" else ""
            shown = f"  \n  上屏：{s['subtitle']}" if s["subtitle"] != s["text"] else ""
            f.write(f"- `{fmt(s['start'])}` {q}{s['text']}{shown}\n")
    n = sum(len(re.sub(r"[，。？！：；、“”《》·…\s]", "", s["text"])) for s in sents)
    print(f"{len(sents)} 句，{n} 字，成片 {tl['total'] / 60:.2f} 分钟")


if __name__ == "__main__":
    main(sys.argv[1])
