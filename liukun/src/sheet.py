import sys, glob, os
from PIL import Image
d=os.path.join(os.path.dirname(__file__),'..','out','stills')
names=sys.argv[1].split(','); cols=int(sys.argv[3]) if len(sys.argv)>3 else 4
fs=[os.path.join(d,'t%s.jpg'%('%.1f'%float(n)).rjust(6,'0')) for n in names]
ims=[Image.open(f).resize((405,720)) for f in fs]; rows=(len(ims)+cols-1)//cols
sheet=Image.new('RGB',(405*cols,720*rows))
for i,im in enumerate(ims): sheet.paste(im,((i%cols)*405,(i//cols)*720))
sheet.save(os.path.join(d,sys.argv[2]),quality=88)
