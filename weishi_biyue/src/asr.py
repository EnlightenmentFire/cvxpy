import sys, soundfile as sf, soxr, numpy as np
from faster_whisper import WhisperModel
m = WhisperModel("models/faster-whisper-medium", device="cpu", compute_type="int8", cpu_threads=4)
def load(f):
    a, sr = sf.read(f, dtype="float32")
    if a.ndim > 1: a = a.mean(1)
    return soxr.resample(a, sr, 16000)
def transcribe(f, words=False):
    segs, info = m.transcribe(load(f), language="zh", beam_size=5, word_timestamps=words, initial_prompt="以下是普通话的句子。")
    return list(segs)
if __name__ == "__main__":
    for f in sys.argv[1:]:
        print(f, "|", "".join(s.text for s in transcribe(f)), flush=True)
