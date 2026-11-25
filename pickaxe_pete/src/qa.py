"""QA: transcribe every line out of the FINAL MIX (music+sfx included) and compare with the script."""
import json, sys, warnings, numpy as np, librosa
warnings.filterwarnings("ignore")
from transformers import pipeline
from select_takes import wer
asr = pipeline("automatic-speech-recognition", model="openai/whisper-small.en", device="cpu")
tl = json.load(open("timeline.json"))
y, sr = librosa.load(sys.argv[1] if len(sys.argv) > 1 else "audio/mix_final.wav", sr=16000)
bad = 0
for l in tl["lines"]:
    a, b = int((l["start"] - 0.1) * sr), int((l["end"] + 0.25) * sr)
    hyp = asr(y[a:b].copy())["text"].strip()
    w = wer(l["text"], hyp)
    bad += w > 0.2
    print(f"{l['id']:<11} {l['start']:6.2f} wer={w:.2f} {'OK ' if w <= 0.2 else 'BAD'} | {hyp}")
print("lines with WER>0.2:", bad, "of", len(tl["lines"]))
peak = np.abs(librosa.load(sys.argv[1] if len(sys.argv) > 1 else "audio/mix_final.wav", sr=None)[0]).max()
print("sample peak", round(float(20*np.log10(peak)), 2), "dBFS")
