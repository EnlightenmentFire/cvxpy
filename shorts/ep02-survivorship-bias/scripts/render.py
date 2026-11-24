"""渲染无声画面：python render.py timeline.json out.mp4 [workers]"""
import sys, json, subprocess
from multiprocessing import Pool
sys.path.insert(0, __file__.rsplit('/',1)[0])
import scene
FPS=30
tl=json.load(open(sys.argv[1])); out=sys.argv[2]; nw=int(sys.argv[3]) if len(sys.argv)>3 else 3
sc=None
def init():
    global sc; sc=scene.Scene(tl)
def job(i): return sc.render(i/FPS).tobytes()
n=int(round(tl['end']*FPS))
ff=subprocess.Popen(['ffmpeg','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r',str(FPS),'-i','-',
  '-c:v','libx264','-preset','slow','-crf','16','-pix_fmt','yuv420p','-r',str(FPS),'-movflags','+faststart',out],stdin=subprocess.PIPE)
with Pool(nw,initializer=init) as p:
    for k,b in enumerate(p.imap(job,range(n),chunksize=4)):
        ff.stdin.write(b)
        if k%150==0: print(k,'/',n,flush=True)
ff.stdin.close(); ff.wait(); print('done',n,'frames')
