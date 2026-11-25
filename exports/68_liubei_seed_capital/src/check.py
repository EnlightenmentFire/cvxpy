"""Final checks: stream durations, loudness, 3 sync spot-checks (subtitle on frame vs ASR of audio at that time)."""
import json, subprocess, sys, re, os
import numpy as np, soundfile as sf
from PIL import Image
OUT = "/home/user/work/out"; D = "/home/user/work/deliver"
mp4 = sys.argv[1]
def probe(entries, sel):
    return subprocess.run(["ffprobe", "-v", "error", "-select_streams", sel, "-show_entries", entries, "-of", "json", mp4], capture_output=True, text=True).stdout
v = json.loads(probe("stream=duration,r_frame_rate,avg_frame_rate,width,height,nb_frames", "v:0"))["streams"][0]
a = json.loads(probe("stream=duration,sample_rate", "a:0"))["streams"][0]
size = os.path.getsize(mp4)
ln = subprocess.run(["ffmpeg", "-hide_banner", "-i", mp4, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
I = re.findall(r"I:\s+(-?[\d.]+) LUFS", ln)[-1]; TP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", ln)[-1]
rep = dict(file=os.path.basename(mp4), size_mb=round(size / 1e6, 2), video=v, audio=a, av_diff=round(abs(float(v["duration"]) - float(a["duration"])), 3),
           loudness_I=float(I), true_peak=float(TP))
tl = json.load(open(f"{OUT}/voice_lines.json"))
spots = []
from faster_whisper import WhisperModel
m = WhisperModel("/home/user/work/models/whisper-small", device="cpu", compute_type="int8", cpu_threads=4)
total = float(v["duration"])
for frac in (0.03, 0.5, 0.96):
    target = total * frac
    line = min(tl["lines"], key=lambda d: abs((d["start"] + d["end"]) / 2 - target))
    mid = (line["start"] + line["end"]) / 2
    fr = f"{OUT}/spot_{int(frac*100):02d}.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{mid:.2f}", "-i", mp4, "-frames:v", "1", fr])
    wav = f"{OUT}/spot.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{line['start']:.2f}", "-t", f"{line['end'] - line['start']:.2f}", "-i", mp4, "-ac", "1", "-ar", "16000", wav])
    x, _ = sf.read(wav)
    hyp = "".join(s.text for s in m.transcribe(x.astype(np.float32), language="zh")[0])
    spots.append(dict(t=round(mid, 2), script=line["say"], asr=hyp, frame=os.path.basename(fr)))
rep["spots"] = spots
print(json.dumps(rep, ensure_ascii=False, indent=1))
json.dump(rep, open(f"{OUT}/check_{os.path.basename(mp4)}.json", "w"), ensure_ascii=False, indent=1)
