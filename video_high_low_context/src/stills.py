# -*- coding: utf-8 -*-
import os
import sys
import time

import render

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "stills")


def card(tl, seg, idx=0, kind=None):
    cs = [c for c in tl["cards"] if c["seg"] == seg and (kind is None or c["kind"] == kind)]
    return cs[idx]


def seg(tl, sid):
    return next(s for s in tl["segs"] if s["id"] == sid)


def picks(tl):
    s01, s02, s03, s04, s05, s06, s08, s10 = (seg(tl, x) for x in ("s01", "s02", "s03", "s04", "s05", "s06", "s08", "s10"))
    c1 = card(tl, "s01")
    return [
        ("01_cold_open_translating", s01["trig"]["calendar"] + 2.9),
        ("02_cold_open_real_meaning", c1["t_why"] + 1.2),
        ("03_reverse_china", s02["trig"]["schedule"] + 2.2),
        ("04_title", seg(tl, "title")["t0"] + 2.6),
        ("05_soup_table", s03["trig"]["guest_confused"] + 2.2),
        ("06_soup_defs", s03["trig"]["def_low"] + 1.5),
        ("07_ruler", s04["trig"]["countries"] + 2.6),
        ("08_room_strangers", s04["trig"]["bubbles"] + 2.5),
        ("09_room_split", s04["trig"]["shared_cloud"] + 2.5),
        ("10_dict_park_that", card(tl, "s05", 3)["t_why"] + 0.8),
        ("11_dict_review", card(tl, "s05", 6)["t_why"] + 0.6),
        ("12_ruler2_france", s06["trig"]["france"] + 2.0),
        ("13_sandwich_words", s06["trig"]["upgraders"] + 2.2),
        ("14_sandwich_story", s06["trig"]["bread_only"] + 3.2),
        ("15_newspaper_pick", s08["trig"]["pick"] + 1.8),
        ("16_newspaper_caveat", s08["trig"]["order"] + 1.5),
        ("17_usmap_stats", s10["trig"]["tenure"] + 1.5),
        ("18_rules", s10["trig"]["not_written"] + 1.5),
        ("19_takeaway", next(l for l in tl["takeaways"] if l["seg"] == "s06")["t0"] + 1.0),
        ("20_cn_phrases", next(c for c in tl["cards"] if c["kind"] == "CQ" and c["slot"] == 3)["t_real"] + 1.0),
        ("21_ending", seg(tl, "s11")["trig"]["l3"] + 1.5),
    ]


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    tl, comp = render.make(sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "-" else None)
    only = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
    for name, t in picks(tl):
        if only and not any(name.startswith(o) for o in only):
            continue
        t0 = time.time()
        im = comp.frame(t)
        im.save(os.path.join(OUT, name + ".png"))
        print(name, round(t, 2), "%.2fs" % (time.time() - t0), flush=True)
