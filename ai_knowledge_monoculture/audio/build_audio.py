"""Build the soundtrack for a timeline: narration + per-segment music beds + effects."""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "render"))
import mix  # noqa: E402
import plan  # noqa: E402
import timeline  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", required=True)
    ap.add_argument("--robot", default=None)
    ap.add_argument("--segs", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--voice-only", action="store_true")
    a = ap.parse_args()
    segs, total = timeline.build(a.voice, a.robot, a.segs.split(",") if a.segs else None, allow_missing=True)
    evmap = timeline.ev_by_id(segs)
    voice = []
    for s in segs:
        for e in s.events:
            if getattr(e, "audio", None):
                voice.append((e.start, e.audio, 0.9 if e.kind == "robot" else 1.0))
    sfx, music = [], []
    if not a.voice_only:
        for s in segs:
            fn = plan.PLANS.get(s.key)
            if fn:
                sx, mu = fn(s, {e.id: e for e in s.events})
                sfx += sx
                music += mu
    mix.mix_track(total, voice, music, sfx, a.out)
    print("audio", a.out, round(total, 2), "s")
