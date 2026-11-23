"""逐句合成旁白（CosyVoice2-0.5B, Apache-2.0；音色参考片段由 Kokoro-82M-v1.1-zh, Apache-2.0 生成）。

每句生成后用 Whisper 回读，按拼音比对；不合格就换随机种子重来，保留最好的一条。
用法: python tts_run.py <work_dir> [beat_id ...]
"""
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = sys.argv[1]
sys.path.insert(0, HERE)
sys.path.insert(0, WORK + '/tts/CosyVoice')
sys.path.insert(0, WORK + '/tts/CosyVoice/third_party/Matcha-TTS')

import numpy as np
import torch
import torchaudio
import librosa
import whisper
from pypinyin import lazy_pinyin

from narration import BEATS

torch.set_num_threads(4)
from cosyvoice.cli.cosyvoice import CosyVoice2

PROMPT_TEXT = "这是一段关于历史的讲述。我们从一座山讲起，慢慢地说。"
PROMPT_WAV = WORK + '/audio/prompt/zm_029_prompt.wav'
SPEED = 1.06
OUT = WORK + '/audio/narr'
os.makedirs(OUT, exist_ok=True)


def hanzi(s):
    return re.sub(r'[^一-鿿]', '', s)


def edit(a, b):
    dp = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, len(b) + 1):
            cur = min(dp[j] + 1, dp[j - 1] + 1, prev + (a[i - 1] != b[j - 1]))
            prev, dp[j] = dp[j], cur
    return dp[-1]


cv = CosyVoice2(WORK + '/models/CosyVoice2-0.5B', load_jit=False, load_trt=False, load_vllm=False, fp16=False)
asr = whisper.load_model('medium')
want = set(sys.argv[2:])
log_path = OUT + '/log.jsonl'

for bid, text in BEATS:
    if want and bid not in want:
        continue
    if not want and os.path.exists(f'{OUT}/{bid}.wav'):
        continue
    ref = lazy_pinyin(hanzi(text))
    best = None
    for attempt in range(3):
        seed = 1000 + 97 * attempt + sum(map(ord, bid))
        torch.manual_seed(seed)
        np.random.seed(seed)
        t0 = time.time()
        wav = torch.cat([o['tts_speech'] for o in
                         cv.inference_zero_shot(text, PROMPT_TEXT, PROMPT_WAV, stream=False, speed=SPEED)], dim=1)
        tmp = f'{OUT}/{bid}.try{attempt}.wav'
        torchaudio.save(tmp, wav, cv.sample_rate)
        y = wav[0].numpy()
        yt, idx = librosa.effects.trim(y, top_db=38)
        dur = len(yt) / cv.sample_rate
        cps = len(ref) / max(dur, 0.1)
        hyp = asr.transcribe(tmp, language='zh', initial_prompt='以下是普通话的句子。', fp16=False,
                             condition_on_previous_text=False)['text']
        # 回读比对：数字写法、l/n 混淆（龙场/农场）是识别器的习惯，不算错
        def canon(seq):
            return ['long' if x == 'nong' else x for x in seq]
        import cn2an
        try:
            hyp_cn = cn2an.transform(hyp, 'an2cn')
        except Exception:
            hyp_cn = hyp
        err = edit(canon(ref), canon(lazy_pinyin(hanzi(hyp_cn))))
        rec = dict(id=bid, attempt=attempt, seed=seed, dur=round(dur, 2), cps=round(cps, 2), err=err, n=len(ref),
                   hyp=hyp, text=text, gen_s=round(time.time() - t0, 1))
        with open(log_path, 'a') as f:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        print('BEAT', json.dumps(rec, ensure_ascii=False), flush=True)
        score = err + (2 if not (2.6 <= cps <= 4.6) else 0)
        if best is None or score < best[0]:
            best = (score, tmp, rec)
        if err <= max(1, int(0.07 * len(ref))) and 2.6 <= cps <= 4.6:
            break
    os.replace(best[1], f'{OUT}/{bid}.wav')
    with open(log_path, 'a') as f:
        f.write(json.dumps(dict(id=bid, chosen=best[2]['attempt'], err=best[2]['err'], cps=best[2]['cps']),
                           ensure_ascii=False) + '\n')
print('ALL DONE', flush=True)
