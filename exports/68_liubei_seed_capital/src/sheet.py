import sys, glob
from PIL import Image
fs=sorted(sum([glob.glob(f'/home/user/work/out/stills/{p}*.jpg') for p in sys.argv[2:]],[]))
n=len(fs); cols=min(5,n); rows=(n+cols-1)//cols
W,H=270,480
sh=Image.new('RGB',(cols*W,rows*H))
for i,f in enumerate(fs):
    sh.paste(Image.open(f).resize((W,H)),((i%cols)*W,(i//cols)*H))
sh.save(sys.argv[1],quality=85)
