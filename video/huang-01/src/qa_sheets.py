# -*- coding: utf-8 -*-
"""自审用：全片每隔 STEP 秒抽一帧，拼成总览图 build/qa/sheet_NN.jpg"""
import os, sys, json
from PIL import Image
here = os.path.dirname(os.path.abspath(__file__)); B = os.path.join(here, '..', 'build')
tl = json.load(open(os.path.join(B, 'timeline.json'))); STEP = float(sys.argv[1]) if len(sys.argv) > 1 else 5.0
os.makedirs(os.path.join(B, 'qa'), exist_ok=True)
ts = []; t = 2.0
while t < tl['duration'] - 0.5: ts.append(t); t += STEP
per = 14
for k in range(0, len(ts), per):
    W = Image.new('RGB', (308 * 7, 548 * 2), '#000')
    for i, t in enumerate(ts[k:k + per]):
        f = os.path.join(B, 'frames', f'{int(round(t * 30)):06}.jpg')
        if os.path.exists(f): W.paste(Image.open(f).resize((308, 548)), (308 * (i % 7), 548 * (i // 7)))
    W.save(os.path.join(B, 'qa', f'sheet_{k // per:02}.jpg'), quality=82)
print(len(ts), 'frames ->', (len(ts) + per - 1) // per, 'sheets')
