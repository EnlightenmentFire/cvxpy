import subprocess, sys
def meas(f):
    e = subprocess.run(["ffmpeg","-hide_banner","-i",f,"-vn","-af","ebur128=peak=true","-f","null","-"],capture_output=True,text=True).stderr
    return float(e[e.rindex("I:"):].split()[1]), float(e[e.rindex("Peak:"):].split()[1])
comp = "acompressor=threshold=0.05:ratio=3.5:attack=4:release=120:knee=4:makeup=1"
src, out = sys.argv[1], sys.argv[2]
g = 19.0; best = None
for it in range(7):
    af = f"{comp},volume={g:.2f}dB,alimiter=limit=0.74:attack=5:release=80:level=false:asc=1"
    subprocess.run(["ffmpeg","-loglevel","error","-y","-i",src,"-af",af,"-ar","48000","-c:a","pcm_s16le",out + ".wav"],check=True)
    subprocess.run(["ffmpeg","-loglevel","error","-y","-i",out + ".wav","-c:a","aac","-b:a","128k",out + ".m4a"],check=True)
    i, tp = meas(out + ".m4a"); print(it, round(g, 2), i, tp, flush=True)
    if abs(i + 15.0) <= 0.1 and tp <= -0.5: break
    g += (-15.0 - i)
