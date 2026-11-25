import sys, os, time, torch, numpy as np, soundfile as sf
torch.set_num_threads(4)
from chatterbox.tts import ChatterboxTTS
from script_data import LINES
REF = {"PETE": "refs/pete_ref.wav", "ZOE": "refs/zoe_ref.wav", "RIGGY": "refs/riggy_ref.wav"}
def params(spk, style):
    if spk == "PETE": return dict(exaggeration=0.95 if style == "shout" else 0.72, cfg_weight=0.3 if style == "shout" else 0.38, temperature=0.8)
    if spk == "RIGGY": return dict(exaggeration=0.9, cfg_weight=0.3, temperature=0.8)
    return dict(exaggeration=0.3, cfg_weight=0.5, temperature=0.7)
m = ChatterboxTTS.from_pretrained(device="cpu")
seeds = [int(s) for s in os.environ.get("SEEDS", "7,21,99").split(",")]
ids = sys.argv[1:]
os.makedirs("tts/cb_takes", exist_ok=True)
for lid, sc, spk, sub, tts, gap, style in LINES:
    if ids and lid not in ids: continue
    for s in seeds:
        out = f"tts/cb_takes/{lid}__{s}.wav"
        if os.path.exists(out): continue
        torch.manual_seed(s); t0 = time.time()
        wav = m.generate(tts, audio_prompt_path=REF[spk], **params(spk, style))
        w = wav.squeeze().numpy(); sf.write(out, w, m.sr); print(lid, s, round(len(w)/m.sr, 2), "gen", round(time.time()-t0, 1), flush=True)
