import sys
from PIL import Image
out=sys.argv[1]; fs=sys.argv[2:]
ims=[Image.open(f'build/stills/{f}.png').crop((0,200,1080,1520)).resize((540,660)) for f in fs]
W=Image.new('RGB',(540*len(ims),660)); [W.paste(im,(i*540,0)) for i,im in enumerate(ims)]; W.save(f'build/stills/{out}.jpg',quality=88)
