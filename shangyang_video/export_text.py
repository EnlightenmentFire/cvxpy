"""导出字幕 SRT、逐句配音稿（带时间码）与完整讲稿。
python export_text.py <outdir>
"""
import sys, os, re
from render import sub_events, timeline
from script_data import all_lines


def ts(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main(out):
    os.makedirs(out, exist_ok=True)
    with open(f"{out}/subtitles.srt", "w", encoding="utf-8") as f:
        for i, (a, b, c) in enumerate(sub_events(), 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{c}\n\n")
    lines, _, total = timeline()
    with open(f"{out}/sentences.txt", "w", encoding="utf-8") as f:
        f.write("# 逐句配音稿：id\t起始\t时长\t字幕\t[念法（与字幕不同时）]\n")
        for d in lines:
            say = "" if d["say"] == d["sub"] else "\t念：" + d["say"]
            f.write(f"{d['id']}\t{d['start']:.2f}\t{d['dur']:.2f}\t{d['sub']}{say}\n")
    with open(f"{out}/SCRIPT.md", "w", encoding="utf-8") as f:
        f.write(f"# 第 35 期 商鞅变法 · 讲稿（成片 {total/60:.1f} 分钟）\n\n")
        cur = None
        heads = {"a": "开场", "b": "壹 · 入秦", "c": "贰 · 杠杆一：信用", "d": "叁 · 杠杆二：激励",
                 "e": "肆 · 杠杆三：信息", "f": "伍 · 改革者之死", "g": "陆 · 余论"}
        for d in lines:
            if d["id"][0] != cur:
                cur = d["id"][0]; f.write(f"\n## {heads[cur]}\n\n")
            f.write(d["sub"] + "\n")
            if d["card"]:
                o, s, b = d["card"]
                f.write(f"\n> 【引文卡】{o}\n> —— {s}\n> 白话：{b}\n\n")
    print("ok", out)


if __name__ == "__main__":
    main(sys.argv[1])
