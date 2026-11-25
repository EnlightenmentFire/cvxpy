# -*- coding: utf-8 -*-
"""从 script.py 和成片时间轴生成 docs/旁白稿.md（时间码＝成片里这一句开始的位置）。
python make_script_doc.py META.json"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import script  # noqa: E402
from timeline import Timeline  # noqa: E402

NAMES = {"S0": "冷启动", "S9": "收尾"}
try:
    import opencc
    T2S = opencc.OpenCC("t2s")
except Exception:  # noqa: BLE001
    class _Same:
        @staticmethod
        def convert(x):
            return x
    T2S = _Same()


def tc(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def main(meta):
    T = Timeline(meta)
    tot, wy = script.stats()
    out = [f"# {script.TITLE} · 旁白稿（含出处）", "",
           f"> {script.SUBTITLE}", "",
           f"成片时长 **{int(T.total // 60)} 分 {T.total % 60:.1f} 秒**（含片头、片尾卡）。"
           f"正文 {tot} 字，其中文言 {wy} 字，约占 {wy / tot:.0%}。", "",
           "「」里的是史书原文；画面上原文用繁体竖排，字幕用简体。时间码是成片里这一句开始的位置。", ""]
    num = {k: i for i, (k, _) in enumerate(script.SECTIONS)}
    for sec, title in script.SECTIONS:
        out += ["", f"## {num[sec]} · {title or NAMES[sec]}", ""]
        for d in script.LINES:
            if d["sec"] != sec:
                continue
            s = f"- `{tc(T.start(d['id']))}` {d['text']}"
            if d.get("quote"):
                q, src = d["quote"]
                qs = T2S.convert(q).replace("，", "").replace("！", "")
                said = d["text"].replace("，", "")
                if qs[:4] in said:
                    label = "原文卡"
                elif any(x.replace("，", "") in qs for x in re.findall(r"「([^」]+)」", d["text"])):
                    label = "原文卡（画面引全句）"
                else:
                    label = "画面原文卡（旁白为转述）"
                s += f"　〔{label}：{q} —— {src}〕"
            out.append(s)
    path = os.path.join(HERE, "docs", "旁白稿.md")
    open(path, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("wrote", path, f"total {T.total:.2f}s")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/home/user/work/qnarr_full/meta.json")
