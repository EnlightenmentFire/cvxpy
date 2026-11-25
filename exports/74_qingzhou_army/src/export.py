# -*- coding: utf-8 -*-
"""导出逐句旁白稿 sentences.json / sentences.txt、字幕 narration.srt、可读旁白稿.md"""
import json, re
from timeline import build
from script import tts_text

D = "/tmp/claude-0/w74/deliver"


def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def main():
    lines, total = build()
    out = []
    for d in lines:
        out.append(dict(id=d["id"], scene=d["scene"], text=d["say"], tts_text=tts_text(d["say"]), subtitle=d["sub"],
                        start=round(d["start"], 3), end=round(d["end"], 3), pause_after=d["pause"] or 0.5))
    json.dump(dict(voice="托克维尔（Qwen3-TTS Base ICL 克隆，参考 A0b_托克维尔设计音色参考_18秒）", tempo=1.1, total=round(total, 2), lines=out),
              open(f"{D}/sentences.json", "w"), ensure_ascii=False, indent=1)
    with open(f"{D}/sentences.txt", "w") as f:
        for d in out:
            f.write(d["tts_text"] + "\n")
    # SRT：与成片字幕同样的切块
    from render import chunks, strip_end
    k = 1
    with open(f"{D}/narration.srt", "w") as f:
        for d in lines:
            ch = chunks(d["sub"]); tot = sum(len(x) for x in ch); acc = 0
            for i, x in enumerate(ch):
                t0 = d["start"] + d["dur"] * acc / tot; acc += len(x)
                t1 = d["start"] + d["dur"] * acc / tot if i < len(ch) - 1 else d["end"] + 0.25
                f.write(f"{k}\n{ts(t0)} --> {ts(t1)}\n{strip_end(x)}\n\n"); k += 1
    names = {"hook": "开场钩子", "bian": "一 · 汴水：输了仗，赢了名声", "yan": "二 · 兖州：地盘是被请来的", "qing": "三 · 青州兵：军队是收编来的",
             "view": "四 · 押地理，还是押人", "novel": "五 · 演义与史书", "end": "收束"}
    with open(f"{D}/旁白稿.md", "w") as f:
        f.write("# 旁白稿｜74 曹操收编青州兵\n\n")
        cur = None
        for d in lines:
            if d["scene"] != cur:
                cur = d["scene"]; f.write(f"\n## {names[cur]}（{int(d['start'] // 60)}:{int(d['start'] % 60):02d}）\n\n")
            f.write(d["say"] + "\n\n")
            if d["card"] and d["card"]["t"] == "q":
                c = d["card"]; f.write(f"> 【卡片】{c['yuan']}　——{c['src']}　｜白话：{c['bai']}\n\n")
            elif d["card"] and d["card"]["t"] == "a":
                c = d["card"]; f.write(f"> 【现代类比】{c['body']}\n> 【类比偏差】{c['bias']}\n\n")
    print("exported", len(out), "lines", round(total, 1), "s")


if __name__ == "__main__":
    main()
