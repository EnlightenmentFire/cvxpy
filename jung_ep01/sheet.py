import sys
from PIL import Image
out, files = sys.argv[1], sys.argv[2:]
W=600; ims=[Image.open(f).convert('RGB') for f in files]
ims=[im.resize((W, int(im.height*W/im.width)), Image.LANCZOS) for im in ims]
cols=min(3,len(ims)); rows=(len(ims)+cols-1)//cols
sheet=Image.new('RGB',(cols*W+(cols-1)*8, rows*ims[0].height+(rows-1)*8),(60,60,60))
for i,im in enumerate(ims): sheet.paste(im,((i%cols)*(W+8),(i//cols)*(im.height+8)))
sheet.save(out, quality=88)
