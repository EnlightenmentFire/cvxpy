"""多音字核对：用多语种音素识别模型（wav2vec2-xlsr-53-espeak）把配音转成国际音标，人工看关键音节。

文字回读（Whisper）分不出"朝 cháo / zhāo""着 zháo / zhe"这类读法，这里补一道。
用法: python phoneme_check.py <work> <beat_id> ...
"""
import json
import sys

import librosa
import numpy as np
import torch
from huggingface_hub import hf_hub_download
from transformers import Wav2Vec2ForCTC

REPO = 'facebook/wav2vec2-xlsr-53-espeak-cv-ft'
work = sys.argv[1]
vocab = json.load(open(hf_hub_download(REPO, 'vocab.json')))
inv = {v: k for k, v in vocab.items()}
model = Wav2Vec2ForCTC.from_pretrained(REPO).eval()
for bid in sys.argv[2:]:
    y, _ = librosa.load(f'{work}/audio/narr/{bid}.wav', sr=16000)
    y = (y - y.mean()) / (y.std() + 1e-7)
    with torch.no_grad():
        ids = model(torch.tensor(y)[None]).logits[0].argmax(-1).numpy()
    out, prev = [], -1
    for i in ids:
        if i != prev and inv[int(i)] not in ('<pad>', '<s>', '</s>', '<unk>'):
            out.append(inv[int(i)])
        prev = i
    print(bid, ' '.join(out), flush=True)
