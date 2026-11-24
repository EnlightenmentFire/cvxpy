# -*- coding: utf-8 -*-
"""Enumerate every audio clip in the script, with TTS-ready text."""
import re

from script_data import SEGMENTS, SPEAKERS

CN_DIG = "零一二三四五六七八九"


def num_to_cn(n):
    n = int(n)
    if n < 10:
        return CN_DIG[n]
    if n < 20:
        return "十" + (CN_DIG[n % 10] if n % 10 else "")
    if n < 100:
        return CN_DIG[n // 10] + "十" + (CN_DIG[n % 10] if n % 10 else "")
    if n < 1000:
        h, r = divmod(n, 100)
        s = CN_DIG[h] + "百"
        if r == 0:
            return s
        if r < 10:
            return s + "零" + CN_DIG[r]
        return s + (num_to_cn(r) if r >= 20 else "一" + num_to_cn(r))
    return "".join(CN_DIG[int(c)] for c in str(n))


def tts_text(s):
    s = s.replace("——", "，").replace("…", "，")
    s = s.replace("黙殺", "默杀")  # Japanese kanji form -> Chinese reading mò shā for the Chinese TTS
    # 4-digit years: digit by digit
    s = re.sub(r"(1[89]\d\d|20\d\d)", lambda m: "".join(CN_DIG[int(c)] for c in m.group(1)), s)
    s = re.sub(r"(\d+)", lambda m: num_to_cn(m.group(1)), s)
    s = re.sub(r"\s+", "", s) if not re.search(r"[A-Za-z]", s) else re.sub(r"\s*([，。：；！？、“”])\s*", r"\1", s)
    s = s.replace("“", "").replace("”", "")
    return s.strip()


def all_clips():
    out = []
    for seg in SEGMENTS:
        for ii, it in enumerate(seg["items"]):
            cid = f"{seg['id']}_{ii:02d}"
            k = it["kind"]
            if k == "N":
                out.append(dict(cid=cid, kind="narr", text=it["text"], tts=tts_text(it["text"]), seg=seg["id"]))
            elif k == "Q":
                out.append(dict(cid=cid, kind="quote", text=it["text"], tts=tts_text(it["text"]), seg=seg["id"]))
            elif k == "E":
                sp = SPEAKERS[it["spk"]]
                out.append(dict(cid=cid + "_en", kind="en", text=it["en"], tts=it["en"].replace("…", "..."),
                                voice=sp["voice"], lang=sp["lang"], seg=seg["id"]))
                if it.get("say_lit"):
                    out.append(dict(cid=cid + "_lit", kind="narr", text=it["say_lit"], tts=tts_text(it["say_lit"]), seg=seg["id"]))
                if it.get("say_real"):
                    out.append(dict(cid=cid + "_real", kind="narr", text=it["say_real"], tts=tts_text(it["say_real"]), seg=seg["id"]))
            elif k == "C":
                if it.get("quote"):
                    out.append(dict(cid=cid + "_q", kind="quote", text=it["zh"], tts=tts_text(it["zh"]), seg=seg["id"]))
                if it.get("say"):
                    out.append(dict(cid=cid + "_say", kind="narr", text=it["say"], tts=tts_text(it["say"]), seg=seg["id"]))
            elif k == "J":
                out.append(dict(cid=cid + "_jp", kind="jp", text=it["text"], tts=it["text"], seg=seg["id"]))
    return out


if __name__ == "__main__":
    import json
    import sys
    segs = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
    cl = [c for c in all_clips() if segs is None or c["seg"] in segs]
    json.dump(cl, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
    for c in cl:
        print(c["cid"], c["kind"], c["tts"])
