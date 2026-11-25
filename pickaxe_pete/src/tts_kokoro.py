import sys, numpy as np, soundfile as sf
from kokoro import KPipeline
from script_data import LINES
VOICE = {"PETE": ("am_fenrir", 0.92), "ZOE": ("af_bella", 0.98), "RIGGY": ("am_puck", 1.05)}
pipe = KPipeline(lang_code='a')
ids = sys.argv[1:] or None
for lid, sc, spk, sub, tts, gap, style in LINES:
    if ids and lid not in ids: continue
    v, sp = VOICE[spk]
    chunks = [a.numpy() if hasattr(a,'numpy') else a for _,_,a in pipe(tts, voice=v, speed=sp)]
    sf.write(f"tts/kokoro/{lid}.wav", np.concatenate(chunks), 24000)
    print(lid, len(np.concatenate(chunks))/24000)
