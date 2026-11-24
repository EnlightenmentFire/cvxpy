"""Make reference clips with Kokoro-82M-v1.1-zh (Apache-2.0) voices: a timbre prompt + direct renditions."""
import os
import sys

import numpy as np
import soundfile as sf
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = 'hexgrad/Kokoro-82M-v1.1-zh'
from kokoro import KModel, KPipeline

torch.set_num_threads(4)
model = KModel(repo_id=REPO).to('cpu').eval()
zh = KPipeline(lang_code='z', repo_id=REPO, model=model)

PROMPT_TEXT = "这是一段关于历史的讲述。我们从一座山讲起，慢慢地说。"
TESTS = [
    "教科书上说，王阳明在龙场，一夜顿悟。",
    "正德三年春，他抵达贵州龙场。那里是水西安氏土司的地盘，朝廷的法，几乎不存在。",
    "圣人之道，吾性自足。向之求理于事物者，误也。",
]
out = ROOT + '/audio/prompt'
os.makedirs(out, exist_ok=True)
for v in sys.argv[1:]:
    for speed in (0.85,):
        a = np.concatenate([r.audio.numpy() for r in zh(PROMPT_TEXT, voice=v, speed=speed)])
        sf.write(f'{out}/{v}_prompt.wav', a, 24000)
        print(v, 'prompt dur %.2f' % (len(a) / 24000))
        for i, t in enumerate(TESTS):
            a = np.concatenate([r.audio.numpy() for r in zh(t, voice=v, speed=speed)])
            sf.write(f'{out}/{v}_k{i}.wav', a, 24000)
            print(v, i, 'dur %.2f' % (len(a) / 24000), flush=True)
