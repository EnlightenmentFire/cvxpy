# -*- coding: utf-8 -*-
"""成片自检：规格、音视频流时长差（≤0.1 s）、响度、首/中/尾三处字幕与配音对齐抽查（抽帧 + 该时刻 ASR）。
usage: python qa.py <mp4> <outdir>"""
import sys, os, json, subprocess, re
HERE = os.path.dirname(os.path.abspath(__file__))
mp4, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", mp4], capture_output=True, text=True).stdout)
v = next(s for s in pr["streams"] if s["codec_type"] == "video"); a = next(s for s in pr["streams"] if s["codec_type"] == "audio")
dv, da = float(v["duration"]), float(a["duration"])
size = int(pr["format"]["size"])
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", mp4, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1]); TP = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])
rep = dict(file=os.path.basename(mp4), width=v["width"], height=v["height"], fps=v["r_frame_rate"], avg_fps=v["avg_frame_rate"], vcodec=v["codec_name"], acodec=a["codec_name"],
           a_bitrate=a.get("bit_rate"), video_dur=dv, audio_dur=da, av_diff=round(abs(dv - da), 3), size_mb=round(size / 1e6, 2), lufs=I, true_peak_dbtp=TP)
# 三处抽查：开头、中段、结尾各取一句
tl = json.load(open(f"{HERE}/timeline.json")); Ls = [l for l in tl["lines"] if l["k"] == "n"]
picks = [Ls[0], Ls[len(Ls) // 2], Ls[-3]]
from faster_whisper import WhisperModel
m = WhisperModel("small", device="cpu", compute_type="int8")
checks = []
for l in picks:
    t0, t1 = l["start"], l["end"]
    wav = f"{out}/chk_{l['id']}.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t0 - 0.3:.3f}", "-t", f"{t1 - t0 + 0.6:.3f}", "-i", mp4, "-ac", "1", "-ar", "16000", wav], check=True)
    segs, _ = m.transcribe(wav, language="zh", word_timestamps=False)
    segs = list(segs)
    hyp = "".join(s.text for s in segs)
    onset = segs[0].start - 0.3 if segs else None   # 相对句子起点（字幕起点）的语音起点
    sub = l["subs"][0]
    tm = (sub["t0"] + sub["t1"]) / 2
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{tm:.3f}", "-i", mp4, "-frames:v", "1", f"{out}/chk_{l['id']}.jpg"], check=True)
    checks.append(dict(id=l["id"], t=round(t0, 2), subtitle_first_chunk=sub["txt"], asr=hyp, speech_onset_vs_subtitle_s=None if onset is None else round(onset, 2)))
rep["sync_checks"] = checks
json.dump(rep, open(f"{out}/qa.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(rep, ensure_ascii=False, indent=1))
