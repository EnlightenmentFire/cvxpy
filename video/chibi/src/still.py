import sys, skia, time
import scenes
from geo import W, H
s = skia.Surface(W, H); c = s.getCanvas()
for a in sys.argv[1:]:
    if a.startswith('s'):
        i = int(a[1:]); t = scenes.S(i) + scenes.D(i) * 0.65
    else: t = float(a)
    t0 = time.time(); scenes.draw_frame(c, t, int(t * 25)); dt = time.time() - t0
    s.makeImageSnapshot().save(f'../stills/{a}.png', skia.kPNG)
    print(a, round(t, 2), 'ms', int(dt * 1000))
