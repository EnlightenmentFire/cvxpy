import sys, glob
from PIL import Image
out=sys.argv[1]; files=sys.argv[2:]
w,h=486,864
im=Image.new('RGB',(w*len(files)+8*(len(files)-1),h),(60,60,60))
for i,f in enumerate(files):
    im.paste(Image.open(f).resize((w,h),Image.LANCZOS),(i*(w+8),0))
im.save(out,quality=88)
