"""由逐句配音时长排出全片时间线：每句起止、镜头、字幕分段、原文卡；同时拼出整条旁白 narration.wav 与 SRT。
usage: python timeline.py [--raw]   （--raw 用未处理的原始时长，只为预览）
"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import all_lines
from scenes import LINE_VIS, ALIAS, NO_CARD, NO_CARD_LINES

W = os.environ.get("WORK", "/tmp/claude-0/work")
LEAD = 2.0          # 开场：剑鸣 + 三声劈斩之后，旁白进
TAIL = 4.0
STRIKE_OFFS = (-0.35, 0.45, 1.25)   # 三击相对 s5_10 句末


def chunks(say, n=15):
    """字幕切段：按标点断，单段不超过 n 字（太长再均分）。"""
    parts = re.findall(r"[^，。；：！？、]+[，。；：！？、]?", say)
    out, cur = [], ""
    for p in parts:
        core = p
        if len(cur) + len(core) <= n and not (cur and cur[-1] in "。！？"):
            cur += core
        else:
            if cur:
                out.append(cur)
            cur = core
    if cur:
        out.append(cur)
    res = []
    for c in out:
        while len(re.sub(r"[，。；：！？、]", "", c)) > n + 2:
            k = n
            res.append(c[:k]); c = c[k:]
        res.append(c)
    return [r for r in res if r.strip("，。；：！？、")]


def clean(s):
    s = s.strip()
    return re.sub(r"[，。；、：]$", "", s)


def nch(s):
    return len(re.sub(r"[^一-鿿A-Za-z0-9]", "", s))


def build(raw=False):
    durs = {}
    if raw:
        for d in all_lines():
            p = f"{W}/tts/raw/{d['id']}.json"
            durs[d["id"]] = json.load(open(p))["dur"] / 1.18 if os.path.exists(p) else nch(d["say"]) / 4.5
    else:
        meta = json.load(open(f"{W}/tts/proc/meta.json"))["lines"]
        durs = {k: v["dur"] for k, v in meta.items()}
    align = {}
    ap = f"{W}/tts/align.json"
    if os.path.exists(ap) and not raw:
        align = json.load(open(ap))
    t = LEAD
    lines = []
    for d in all_lines():
        dur = durs[d["id"]]
        L = dict(id=d["id"], say=d["say"], start=round(t, 3), end=round(t + dur, 3), card=d["card"], k=d["k"],
                 vis=LINE_VIS[d["id"]])
        # 字幕分段
        cs = chunks(d["say"])
        tot = sum(nch(c) for c in cs)
        al = align.get(d["id"])
        subs, acc = [], 0
        for c in cs:
            n0, n1 = acc, acc + nch(c)
            if al and len(al) >= tot:
                a0 = al[min(n0, len(al) - 1)][0]; a1 = al[min(n1, len(al)) - 1][1]
                s0, s1 = t + a0, t + a1
            else:
                s0, s1 = t + dur * n0 / tot, t + dur * n1 / tot
            subs.append(dict(text=clean(c), start=round(s0, 3), end=round(s1, 3)))
            acc = n1
        for i in range(len(subs) - 1):          # 首尾相接，避免闪烁
            subs[i]["end"] = subs[i + 1]["start"]
        subs[0]["start"] = L["start"]; subs[-1]["end"] = L["end"]
        L["subs"] = subs
        lines.append(L)
        t += dur + d["pause"]
    total = t + TAIL
    # 镜头
    shots = []
    for L in lines:
        if shots and shots[-1]["key"] == L["vis"]:
            shots[-1]["lines"].append(L["id"])
        else:
            shots.append(dict(key=L["vis"], vis=ALIAS.get(L["vis"], L["vis"]), lines=[L["id"]]))
    byid = {L["id"]: L for L in lines}
    for i, s in enumerate(shots):
        s["start"] = 0.0 if i == 0 else byid[s["lines"][0]]["start"] - 0.25
        s["end"] = total if i == len(shots) - 1 else None
    for i in range(len(shots) - 1):
        shots[i]["end"] = shots[i + 1]["start"]
    for s in shots:
        s["marks"] = [round(byid[x]["start"] - s["start"], 3) for x in s["lines"]]
        s["ends"] = [round(byid[x]["end"] - s["start"], 3) for x in s["lines"]]
        if s["vis"] == "quote_big":
            d = byid[s["lines"][0]]
            s["quote"] = d["card"][:2]
            s["qstyle"] = "fire" if s["lines"][0] != "s1_11" else "mountain"
        if s["vis"] == "strike":
            e = s["ends"][0]
            s["strikes"] = [round(e + o, 3) for o in STRIKE_OFFS]
    # 原文卡
    cards = []
    for i, L in enumerate(lines):
        if not L["card"] or L["id"] in NO_CARD_LINES or L["vis"] in NO_CARD or ALIAS.get(L["vis"]) in NO_CARD:
            continue
        e = max(L["end"] + 1.5, L["start"] + 5.0)
        nxt = [M["start"] for M in lines[i + 1:] if M["card"]]
        if nxt:
            e = min(e, nxt[0] - 0.3)
        # 不跨镜头
        sh = [s for s in shots if L["id"] in s["lines"]][0]
        e = min(e, sh["end"] - 0.15)
        cards.append(dict(id=L["id"], orig=L["card"][0], src=L["card"][1], bai=L["card"][2], start=L["start"], end=round(e, 3)))
    strike_abs = [s for s in shots if s["vis"] == "strike"]
    events = dict(hook_strikes=[0.42, 0.92, 1.42],
                  strikes=[round(strike_abs[0]["start"] + x, 3) for x in strike_abs[0]["strikes"]] if strike_abs else [])
    return dict(total=round(total, 3), lead=LEAD, lines=lines, shots=shots, cards=cards, events=events)


def srt_time(x):
    h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def main():
    raw = "--raw" in sys.argv
    tl = build(raw)
    os.makedirs(f"{W}/build", exist_ok=True)
    json.dump(tl, open(f"{W}/build/timeline.json", "w"), ensure_ascii=False, indent=1)
    with open(f"{W}/build/narration.srt", "w") as f:
        k = 1
        for L in tl["lines"]:
            for s in L["subs"]:
                f.write(f"{k}\n{srt_time(s['start'])} --> {srt_time(s['end'])}\n{s['text']}\n\n"); k += 1
    print(f"total {tl['total']:.1f}s = {tl['total'] / 60:.2f} min, {len(tl['shots'])} shots, {len(tl['cards'])} cards")
    for s in tl["shots"]:
        print(f"  {s['start']:7.2f}-{s['end']:7.2f} {s['vis']:<14} {len(s['lines'])} lines")


if __name__ == "__main__":
    main()
