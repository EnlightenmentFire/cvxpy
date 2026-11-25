import glob, sys
from PIL import Image
fs = sorted(glob.glob('/tmp/claude-0/work/stills/*.jpg'))
W, H = 216, 384
for s in range(0, len(fs), 12):
    ims = [Image.open(f) for f in fs[s:s + 12]]
    sheet = Image.new('RGB', (W * 6, H * 2))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((W, H)), ((i % 6) * W, (i // 6) * H))
    sheet.save(f'/tmp/claude-0/work/sheet_{s // 12}.jpg')
print(len(fs))
