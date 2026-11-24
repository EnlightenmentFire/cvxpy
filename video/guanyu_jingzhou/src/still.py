import sys, skia, time
from geo import W,H
import scenes
from scenes import T,S,E
from PIL import Image
def still(t,name,small=True):
    s=skia.Surface(W,H); c=s.getCanvas(); t0=time.time()
    scenes.draw_frame(c,t,int(t*30)); dt=time.time()-t0
    s.makeImageSnapshot().save(f'stills/{name}.png',skia.kPNG)
    if small: Image.open(f'stills/{name}.png').convert('RGB').resize((540,960),Image.LANCZOS).save(f'stills/{name}_s.jpg',quality=88)
    return dt
if __name__=='__main__':
    import os; os.makedirs('stills',exist_ok=True)
    for a in sys.argv[1:]:
        name,expr=a.split('=',1); t=eval(expr); print(name,round(t,2),round(still(t,name),3))
