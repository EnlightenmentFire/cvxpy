"""Kokoro-82M v1.1-zh wrapper: text -> 24 kHz mono wav. Apache-2.0 model."""
import sys, json, numpy as np, soundfile as sf, torch
from kokoro import KModel, KPipeline
REPO = 'hexgrad/Kokoro-82M-v1.1-zh'
SR = 24000
_model = None; _zh = None
def pipe():
    global _model, _zh
    if _zh is None:
        torch.set_num_threads(4)
        _model = KModel(repo_id=REPO).to('cpu').eval()
        en = KPipeline(lang_code='a', repo_id=REPO, model=False)
        def en_callable(text):
            return next(en(text)).phonemes
        _zh = KPipeline(lang_code='z', repo_id=REPO, model=_model, en_callable=en_callable)
    return _zh
def synth(text, voice='zm_010', speed=1.0):
    wavs = []
    for r in pipe()(text, voice=voice, speed=speed):
        wavs.append(r.audio.numpy() if hasattr(r.audio, 'numpy') else np.asarray(r.audio))
    return np.concatenate(wavs).astype(np.float32)
if __name__ == '__main__':
    text, voice, speed, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
    sf.write(out, synth(text, voice, speed), SR)
