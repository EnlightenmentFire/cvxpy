# -*- coding: utf-8 -*-
"""Export the structured script to Markdown for review."""
import os
import sys
from script_data import SEGMENTS, SPEAKERS

def md():
    out = []
    n = 0
    for seg in SEGMENTS:
        title = seg.get("chapter") or ("片名" if seg["id"] == "title" else "收尾")
        if seg.get("chapter"):
            n += 1
            out.append(f"\n### 第 {n} 章 · {title}" + ("（示意）" if seg.get("shiyi") else "") + ("（真实历史）" if seg.get("history") else ""))
        else:
            out.append(f"\n### {title}")
        for it in seg["items"]:
            k = it["kind"]
            if k == "N":
                pre = "**【这说明什么】** " if it.get("takeaway") else ""
                out.append(f"- 旁白：{pre}{it['text']}")
            elif k == "Q":
                out.append(f"- 引语（{it.get('who','')}）：“{it['text']}”")
            elif k == "E":
                sp = SPEAKERS[it["spk"]]
                out.append(f"- 🔊 英文（{sp['name']} · {sp['role']}，Kokoro {sp['voice']}）：*{it['en']}*")
                out.append(f"    - 字面：{it['lit']}")
                out.append(f"    - 真实意思：{it['real']}")
                if it.get("why"):
                    out.append(f"    - 白话：{it['why']}")
                if it.get("say_lit"):
                    out.append(f"    - 旁白：{it['say_lit']}")
                if it.get("say_real"):
                    out.append(f"    - 旁白：{it['say_real']}")
            elif k == "C":
                out.append(f"- 中文说法：“{it['zh']}”" + ("（旁白念出）" if it.get("quote") else "（只出字幕卡）"))
                out.append(f"    - 字面：{it['lit']}")
                out.append(f"    - 真实意思：{it['real']}")
                if it.get("why"):
                    out.append(f"    - 白话：{it['why']}")
                if it.get("say"):
                    out.append(f"    - 旁白：{it['say']}")
            elif k == "J":
                out.append(f"- 日文读音：{it['text']}（{it['display']}）")
            elif k == "BEAT":
                out.append(f"- （画面停留 {it['sec']} 秒：{it.get('tag','')}）")
    return "\n".join(out)

if __name__ == "__main__":
    print(md())
