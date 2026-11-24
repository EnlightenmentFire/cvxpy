"""Render key stills at named cue moments (uses real durations if available)."""
import sys, os
from PIL import Image
from compose import build_timeline, Renderer, load_durations

STILLS = [
    ("01_newspaper", "cold", "c_apps", 1.2),
    ("02_bet", "bet", "b_exp", 5.4),
    ("03_outsiders", "out", "o_jobs", 5.2),
    ("04_paper_breakout", "rules", "r3_buy", 2.2),
    ("05_paper_stop", "rules", "r5_pct", 3.2),
    ("06_loss_streak", "hard", "d_seventh", 1.6),
    ("07_divergence", "div", "v_cut", 1.6),
    ("08_1988", "t88", "t_turtles", 2.6),
]

def still_times(items):
    out = []
    for name, seg, cue, off in STILLS:
        it = next(i for i in items if i["seg"] == seg and i["kind"] == "scene")
        out.append((name, it["start"] + it["cues"][cue][0] + off))
    return out

if __name__ == "__main__":
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    durs = None
    if len(sys.argv) > 2:
        import soundfile as sf
        d = sys.argv[2]
        durs = {f[:-4]: sf.info(os.path.join(d, f)).duration for f in os.listdir(d) if f.endswith(".wav") and not f.startswith(".")}
    items, lines, total = build_timeline(durs)
    r = Renderer(items, lines, total)
    print(f"total {total:.1f}s")
    for name, T in still_times(items):
        Image.fromarray(r.frame_rgb(T, int(T * 30))).save(f"{outdir}/{name}.png")
        print(name, round(T, 2))
