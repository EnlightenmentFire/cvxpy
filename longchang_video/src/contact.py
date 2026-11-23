"""把若干帧拼成一张联络表，便于逐段审片。用法: python contact.py out.png cols img1 img2 ..."""
import sys

import cv2
import numpy as np

out, cols = sys.argv[1], int(sys.argv[2])
files = sys.argv[3:]
tw, th = 640, 360
rows = (len(files) + cols - 1) // cols
sheet = np.zeros((rows * (th + 6), cols * (tw + 6), 3), np.uint8) + 40
for i, f in enumerate(files):
    im = cv2.imread(f)
    if im is None:
        continue
    im = cv2.resize(im, (tw, th), interpolation=cv2.INTER_AREA)
    label = f.split('/')[-1].replace('f_', '').replace('.png', '')
    cv2.putText(im, label, (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (90, 200, 255), 1, cv2.LINE_AA)
    r, c = divmod(i, cols)
    sheet[r * (th + 6) + 3:r * (th + 6) + 3 + th, c * (tw + 6) + 3:c * (tw + 6) + 3 + tw] = im
cv2.imwrite(out, sheet)
