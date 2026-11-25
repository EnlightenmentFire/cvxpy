import sys,glob
from PIL import Image
fs=sys.argv[2:]; n=len(fs); cols=4; rows=(n+cols-1)//cols
S=Image.new('RGB',(cols*432,rows*768),'gray')
for i,f in enumerate(fs):
    S.paste(Image.open(f).resize((432,768)),((i%cols)*432,(i//cols)*768))
S.save(sys.argv[1])
