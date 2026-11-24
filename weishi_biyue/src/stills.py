import json, sys, os, time
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import scene
T = json.load(open(sys.argv[1]))
out = sys.argv[2]
os.makedirs(out, exist_ok=True)
t0 = time.time()
S = scene.Scene(T)
print("init", time.time() - t0)
for name, t in [(n, float(v)) for n, v in (a.split("=") for a in sys.argv[3:])]:
    t1 = time.time()
    img = S.render(t)
    Image.fromarray(img).save(f"{out}/{name}.png")
    print(name, t, "%.2fs" % (time.time() - t1))
