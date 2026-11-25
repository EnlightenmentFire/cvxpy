import sys, json, cv2, time
from film import Film
from engine import to_u8
f = Film()
ts = [float(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else None
if ts is None:
    ts = []
    for s in f.tl["scenes"]:
        ts.append(s["start"] + (s["end"] - s["start"]) * 0.85)
for t in ts:
    t0 = time.time(); img = f.frame(t)
    sid = f.order[f.scene_at(t)]
    cv2.imwrite(f"/tmp/claude-0/work/preview/st_{t:07.2f}_{sid}.jpg", cv2.cvtColor(to_u8(img), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(f"{t:.2f} {sid} {time.time()-t0:.2f}s", flush=True)
