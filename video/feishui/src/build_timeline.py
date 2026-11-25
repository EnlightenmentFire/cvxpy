# -*- coding: utf-8 -*-
"""每句旁白时长 → src/timeline.json（全部画面、字幕都挂在这条时间轴上）。
有处理后的音频（WORK/tts/proc/<id>.wav）就用真实时长，否则按 4.4 字/秒估算（开发用）。"""
import os, re, json, sys
sys.path.insert(0, os.path.dirname(__file__))
from script_data import all_lines

W = os.environ.get("WORK", "/tmp/claude-0/work")
PROC = f"{W}/tts/proc"
HERE = os.path.dirname(os.path.abspath(__file__))
SEC_GAP = 0.9      # extra breath between sections
LEAD = 0.12        # first word almost immediately (no black open)
TAIL = 4.0

GLOSS = {
    "s2": {},
}
QUOTE_GLOSS = {
    "東西萬里，水陸齊進。": "从西到东上万里，水路陆路一齐推进。",
    "以吾之眾旅，投鞭于江，足斷其流。": "我这么多兵，把马鞭扔进江里，就能截断江水。",
    "秦步騎崩潰，爭赴淮水，士卒死者萬五千人。": "秦军步骑崩溃，争着跳进淮河，死了一万五千人。",
    "今乘諸軍未集，宜速擊之。": "趁他们各路兵马还没集合，赶快出击。",
    "但引兵少卻，使之半渡，我以鐵騎蹙而殺之，蔑不勝矣！": "只要稍稍后退，等他们渡到一半，铁骑压上去，没有不赢的。",
    "秦兵遂退，不可復止。": "秦军于是后退，再也停不下来。",
    "秦兵敗矣！": "秦军败了！",
    "聞風聲鶴唳，皆以為王師已至。": "听到风声鹤叫，都以为晋军追来了。",
    "歸師勿遏，圍師必闕，窮寇勿迫。": "撤退的军队别硬拦，包围要留缺口，走投无路的敌人别逼太紧。",
    "小兒輩遂已破賊。": "孩子们已经把敌人打败了。",
    "過戶限，心喜甚，不覺屐齒之折。": "跨过门槛，心里太高兴，连木屐的齿撞断了都没察觉。",
}


def dur_of(d):
    p = f"{PROC}/{d['id']}.wav"
    if os.path.exists(p):
        import soundfile as sf
        info = sf.info(p)
        return info.frames / info.samplerate, True
    n = len(re.sub(r"[，。？！：；、“”《》（）·\s]", "", d["say"]))
    return n / (3.6 if d["k"] == "q" else 4.4) + 0.25, False


def split_sub(text, maxc=15):
    """把一句字幕切成若干块（每块 ≤ 2 行 × maxc 字），按标点优先断开。"""
    parts = re.findall(r"[^，。？！：；]+[，。？！：；]?", text)
    chunks, cur = [], ""
    for p in parts:
        core = p
        if len(re.sub(r"[，。？！：；]", "", cur + core)) <= maxc * 2 - 2 or not cur:
            cur += core
        else:
            chunks.append(cur); cur = core
    if cur:
        chunks.append(cur)
    out = []
    for c in chunks:
        c = re.sub(r"[，。；：]$", "", c)
        out.append(c)
    return out


def main():
    L = all_lines()
    t = LEAD
    lines, secs, real = [], {}, 0
    prev_sec = None
    for d in L:
        if prev_sec and d["sec"] != prev_sec:
            t += SEC_GAP
        if d["sec"] not in secs:
            secs[d["sec"]] = dict(start=round(t, 3), title=d["sec_title"])
        dur, ok = dur_of(d); real += ok
        start, end = t, t + dur
        subs = []
        if d["k"] == "n":
            chunks = split_sub(d["text"])
            w = [max(1, len(re.sub(r"[，。？！：；、“”《》（）·\s]", "", c))) for c in chunks]
            s = start
            for c, wi in zip(chunks, w):
                e = s + dur * wi / sum(w)
                subs.append(dict(t0=round(s, 3), t1=round(e, 3), txt=c)); s = e
        lines.append(dict(id=d["id"], sec=d["sec"], k=d["k"], text=d["text"], src=d["src"], cue=d["cue"],
                          gloss=QUOTE_GLOSS.get(d["text"]), start=round(start, 3), end=round(end, 3), subs=subs))
        t = end + d["gap"]
        secs[d["sec"]]["end"] = round(t, 3)
        prev_sec = d["sec"]
    total = t + TAIL
    json.dump(dict(lines=lines, secs=secs, total=round(total, 3)), open(f"{HERE}/timeline.json", "w"), ensure_ascii=False, indent=0)
    print(f"{len(lines)} lines, real audio {real}, total {total:.1f}s ({total/60:.2f} min)")
    for k, v in secs.items():
        print(k, v["title"], f"{v['start']:.1f}-{v['end']:.1f}")


if __name__ == "__main__":
    main()
