"""Render a QA grid of frames at many cue points."""
import sys, os
import soundfile as sf
from PIL import Image, ImageDraw
from compose import build_timeline, Renderer

PICKS = sys.argv[3].split(",")   # entries like seg:cue:offset  or  seg:@sec (scene-local seconds)

def main():
    out, d = sys.argv[1], sys.argv[2]
    durs = {f[:-4]: sf.info(os.path.join(d, f)).duration for f in os.listdir(d) if f.endswith(".wav") and not f.startswith(".")}
    items, lines, total = build_timeline(durs)
    r = Renderer(items, lines, total)
    thumbs = []
    for p in PICKS:
        seg, cue, off = p.split(":")
        it = next(i for i in items if i["seg"] == seg and (i["kind"] == "scene" or cue == "@card"))
        if cue.startswith("@"):
            T = it["start"] + float(off)
        else:
            T = it["start"] + it["cues"][cue][0] + float(off)
        im = Image.fromarray(r.frame_rgb(T, int(T * 30))).resize((270, 480))
        ImageDraw.Draw(im).text((6, 4), p, fill=(255, 80, 80))
        thumbs.append(im)
    cols = 6
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 274, rows * 484), (60, 0, 0))
    for i, im in enumerate(thumbs):
        sheet.paste(im, ((i % cols) * 274, (i // cols) * 484))
    sheet.save(out)

main()
