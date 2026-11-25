"""音画同步抽查：从成片音轨截取开头/中段/结尾，ASR 词级时间戳，对照 timeline 中各句起点（字幕起点）。"""
import json, subprocess, sys, numpy as np, re
from faster_whisper import WhisperModel
WK = "/tmp/claude-0/work"
J = json.load(open(f"{WK}/timeline.json"))
mp4 = sys.argv[1]
m = WhisperModel("/tmp/claude-0/models/fw-medium", device="cpu", compute_type="int8", cpu_threads=4)
for t0 in (0.0, 300.0, 580.0):
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", "20", "-i", mp4, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], capture_output=True).stdout
    x = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    segs, _ = m.transcribe(x, language="zh", vad_filter=False, word_timestamps=True)
    segs = list(segs)
    print(f"== window {t0:.0f}s")
    for s in segs:
        st = t0 + s.start
        near = min(J["lines"], key=lambda l: abs(l["start"] - st))
        print(f"  ASR {st:7.2f}s  sub {near['start']:7.2f}s  Δ={st - near['start']:+.2f}s | {s.text.strip()[:18]} | {near['sub'][:18]}")
