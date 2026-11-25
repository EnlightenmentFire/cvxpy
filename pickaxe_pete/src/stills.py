import sys, numpy as np, json
from PIL import Image
import render as R
vertical = sys.argv[1] == "vertical"
R.init(vertical)
L = R._L
times = [float(x) for x in sys.argv[2:]]
ims = []
for T in times:
    b = R.render_frame(int(T * 30))
    ims.append(np.frombuffer(b, np.uint8).reshape(L.H * 4, L.W * 4, 3))
cols = 4 if vertical else 3
rows = (len(ims) + cols - 1) // cols
h, w = ims[0].shape[:2]
sheet = np.zeros((rows * h, cols * w, 3), np.uint8)
for i, im in enumerate(ims):
    sheet[(i // cols) * h:(i // cols + 1) * h, (i % cols) * w:(i % cols + 1) * w] = im
Image.fromarray(sheet).resize((sheet.shape[1] // 2, sheet.shape[0] // 2), Image.NEAREST).save(f"stills_{sys.argv[1]}.png")
print("ok")
