import sys, skia, time
import scenes
from geo import W, H
from timeline import FPS
ts = [float(x) for x in sys.argv[1:]]
s = skia.Surface(W, H); c = s.getCanvas()
for t in ts:
    t0 = time.time(); scenes.draw_frame(c, t, int(t * FPS))
    s.makeImageSnapshot().save(f'/tmp/claude-0/work/stills/f_{t:07.2f}.jpg', skia.kJPEG); print(t, round(time.time() - t0, 2))
