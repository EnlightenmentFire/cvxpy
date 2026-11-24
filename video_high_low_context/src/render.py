# -*- coding: utf-8 -*-
"""Build timeline from clip durations and render frames / stills / video."""
import json
import os
import sys

import timeline as TL
import engine
import scenes
from script_data import SEGMENTS

HERE = os.path.dirname(os.path.abspath(__file__))


def load_durations(path):
    if path and os.path.exists(path):
        return json.load(open(path))
    return {}


def make(dur_path=None):
    dur = load_durations(dur_path)
    tl = TL.build(SEGMENTS, dur)
    scenes._TL = tl
    comp = engine.Composer(tl, scenes)
    return tl, comp


if __name__ == "__main__":
    tl, comp = make(sys.argv[1] if len(sys.argv) > 1 else None)
    print("total", round(tl["total"], 1))
    for s in tl["segs"]:
        print(s["id"], round(s["t0"], 1), round(s["t1"], 1), sorted(s["trig"].keys()))
