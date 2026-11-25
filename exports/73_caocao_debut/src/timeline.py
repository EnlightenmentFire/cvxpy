# -*- coding: utf-8 -*-
"""Master timeline: lines, overlays, titles, beats, visuals, strikes, subtitles."""
import os, json, re
from script import SCENES, all_lines
from visplan import PLAN
from overlays import sub_chunks

W_ = "/tmp/claude-0/w73"
GAP = 0.5
TITLE_HOLD = 1.8
LEAD = 0.25
MAXN = {"card": 2, "ana": 2, "q3": 3, "yy": 2}


def nch(s):
    return len(re.sub(r"[，。？！：；、“”《》「」\s·]", "", s))


def durations():
    p = f"{W_}/tts/proc/meta.json"
    m = json.load(open(p))["dur"] if os.path.exists(p) else {}
    return {d["id"]: m.get(d["id"], nch(d["sub"]) / 4.6 + 0.2) for d in all_lines()}, len(m)


def need_time(o):
    d = o["data"]
    if o["kind"] == "card":
        return 2.6 + 0.11 * (len(d["text"]) + len(d["bh"]))
    if o["kind"] == "ana":
        return 3.0 + 0.085 * (len(d["ana"]) + len(d["bias"]))
    if o["kind"] == "yy":
        return 2.5 + 0.09 * (len(d["yy"]) + len(d["sx"]))
    return 0.0


def _pass(extra):
    dur, _ = durations()
    order = [d for d in all_lines()]
    t, k = 0.0, 0
    L, ovs, titles, beats, pending = [], [], [], [], []
    for sc in SCENES:
        if sc.get("title"):
            titles.append(dict(text=sc["title"], scene=sc["id"], t0=t, t1=t + TITLE_HOLD)); t += TITLE_HOLD
        for it in sc["items"]:
            if it[0] == "beat":
                beats.append((t, t + it[1])); t += it[1]
            elif it[0] in MAXN:
                pending.append(it)
            elif it[0] == "n":
                d = order[k]; k += 1
                for it2 in pending:
                    ovs.append(dict(kind=it2[0], data=it2[1], s=len(L)))
                pending = []
                L.append(dict(id=d["id"], scene=sc["id"], sub=d["sub"], say=d["say"], t0=t, t1=t + dur[d["id"]]))
                t = L[-1]["t1"] + GAP + extra.get(len(L) - 1, 0.0)
        t += 0.4
    starts = [o["s"] for o in ovs]
    need = {}
    for i, o in enumerate(ovs):
        s = o["s"]
        e = min(s + o["data"].get("keep", MAXN[o["kind"]]), starts[i + 1] if i + 1 < len(starts) else len(L))
        e = max(j for j in range(s, e) if L[j]["scene"] == L[s]["scene"]) + 1
        if o["kind"] == "card" and not o["data"].get("big"):
            for j in range(s + 1, e):      # stop before a line that starts a new visual
                if any(L[j]["sub"].startswith(pr) for pr, _, _ in PLAN):
                    e = j; break
        o["lines"] = list(range(s, e))
        o["t0"] = L[s]["t0"] - LEAD
        o["t1"] = L[e - 1]["t1"] + 0.35 + extra.get(e - 1, 0.0) * 0.9
        lack = need_time(o) - (o["t1"] - o["t0"])
        if lack > 0.05:
            need[e - 1] = max(need.get(e - 1, 0), lack)
    total = max(L[-1]["t1"], beats[-1][1] if beats else 0) + 0.3
    return L, ovs, titles, beats, total, need


def build():
    extra = {}
    for _ in range(4):
        L, ovs, titles, beats, total, need = _pass(extra)
        if not need:
            break
        for j, v in need.items():
            extra[j] = extra.get(j, 0) + v
    vis = []
    for (prefix, name, params) in PLAN:
        j = next((i for i, r in enumerate(L) if r["sub"].startswith(prefix)), None)
        if j is None:
            raise SystemExit(f"visplan prefix not found: {prefix}")
        t0 = 0.0 if j == 0 else L[j]["t0"] - 0.3
        for ti in titles:
            if ti["t0"] <= L[j]["t0"] <= ti["t1"] + 0.6:
                t0 = ti["t0"]
        vis.append(dict(name=name, p=params, t0=t0, line=j))
    vis.sort(key=lambda v: v["t0"])
    for i, v in enumerate(vis):
        v["t1"] = vis[i + 1]["t0"] if i + 1 < len(vis) else total
        v["lines"] = [(r["t0"] - v["t0"], r["t1"] - v["t0"]) for r in L if v["t0"] - 0.05 <= r["t0"] < v["t1"]]
    strikes = [0.85]
    for r in L:
        s = r["sub"]
        if s.startswith("皇帝宠臣的叔父"): strikes.append(r["t1"] - 0.35)
        if s.startswith("几个月后，蹇硕的叔父"): strikes.append(r["t1"] - 0.3)
        if s.startswith("他又是怎样"): strikes += [r["t0"] + 0.95, r["t0"] + 1.55]
        if s.startswith("然后，他用一根五色棒"): strikes.append(r["t0"] + 1.7)
    subs = []
    for r in L:
        ch = sub_chunks(r["sub"]); w = [max(1, nch(c)) for c in ch]
        t, span = r["t0"], r["t1"] - r["t0"]
        for c, ww in zip(ch, w):
            dd = span * ww / sum(w); subs.append(dict(text=c, t0=t, t1=t + dd)); t += dd
    return dict(lines=L, overlays=ovs, titles=titles, beats=beats, total=total, visuals=vis, strikes=strikes, subs=subs, extra=extra)


if __name__ == "__main__":
    tl = build()
    print(f"total {tl['total']:.1f}s = {tl['total']/60:.2f} min; lines {len(tl['lines'])}; overlays {len(tl['overlays'])}; visuals {len(tl['visuals'])}")
    print("extra holds:", {k: round(v, 1) for k, v in tl["extra"].items()})
    for v in tl["visuals"][:12]:
        print(f"{v['t0']:7.1f} {v['name']}")
