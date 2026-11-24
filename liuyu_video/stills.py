# -*- coding: utf-8 -*-
"""按时间点出静帧：python stills.py 名字=时间点 ...（时间点可写成 行id[:偏移] 或 行id@词）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeline import Timeline
from scenes import Film

META = os.environ.get("META", "/home/user/work/narr_main/meta.json")
OUT = os.environ.get("OUT", "/home/user/work/stills")


def resolve(T, spec):
    if "@" in spec:
        lid, w = spec.split("@", 1)
        off = 0.0
        if "+" in w:
            w, o = w.split("+"); off = float(o)
        return T.word(lid, w) + off
    if ":" in spec:
        lid, off = spec.split(":")
        return T.start(lid) + float(off)
    try:
        return float(spec)
    except ValueError:
        return T.start(spec) + 0.5


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    T = Timeline(META)
    F = Film(T)
    for arg in sys.argv[1:]:
        name, spec = arg.split("=", 1)
        t = resolve(T, spec)
        surf = F.frame(t, fi=int(t * 30))
        p = f"{OUT}/{name}.png"
        surf.write_to_png(p)
        print(f"{name}: t={t:.2f} -> {p}")
