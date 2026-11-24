from PIL import Image
import sys
names=sys.argv[2:]
ims=[Image.open(f'/home/user/work/vid/stills/{n}_s.jpg').resize((405,720)) for n in names]
s=Image.new('RGB',(405*len(ims)+6*(len(ims)-1),720),(0,0,0))
for i,im in enumerate(ims): s.paste(im,(i*411,0))
s.save(f'/home/user/work/vid/stills/{sys.argv[1]}.jpg',quality=88)
