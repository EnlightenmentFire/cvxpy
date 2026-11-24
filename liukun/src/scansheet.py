import glob, os, sys
from PIL import Image, ImageDraw
tag=sys.argv[1]; per=int(sys.argv[2]) if len(sys.argv)>2 else 27; cols=9
d=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','out','scan'); fs=sorted(glob.glob(d+'/%s[0-9]*.jpg'%tag))
for k in range(0,len(fs),per):
    ims=fs[k:k+per]; rows=(len(ims)+cols-1)//cols; sh=Image.new('RGB',(270*cols,400*rows)); dr=ImageDraw.Draw(sh)
    for i,f in enumerate(ims):
        im=Image.open(f).crop((0,40,270,440)); sh.paste(im,((i%cols)*270,(i//cols)*400)); dr.text(((i%cols)*270+6,(i//cols)*400+4),os.path.basename(f).split('_')[1][:-4],fill=(255,220,120))
    sh.save(d+'/S_%s%02d.jpg'%(tag,k//per),quality=85)
print(len(fs))
