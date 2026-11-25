# -*- coding: utf-8 -*-
"""托克维尔声音：Qwen3-TTS-12Hz-1.7B-Base 以设计参考音 ICL 克隆，逐句合成。
每句换 seed 直到中位音高落在 [85,105] Hz（最多 NSEEDS 次，取最接近 95 Hz 的）。
usage: python tts_gen.py WORKER_INDEX NUM_WORKERS [--force]
"""
import sys, os, json, time, re
import numpy as np, soundfile as sf, torch, parselmouth
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import all_lines
from qwen_tts import Qwen3TTSModel

W = os.environ.get('WORK', '/home/user/work')
OUT = f'{W}/tts/raw'
REF_WAV = f'{W}/voice/ref_voice.wav'
REF_TEXT = "一八三一年的春天，一艘帆船从法国出发，在大西洋上走了三十多天。船上有两个年轻人，他们想亲眼看一看，一个没有国王的国家，究竟是什么样子。"
F0_LO, F0_HI = 85.0, 105.0

# 多音字、生僻字按读音改写（只影响配音，不影响字幕）
SUB = [('结毦而已邪', '结耳而已耶'), ('髀肉', '必肉'), ('沔', '勉'), ('吴会', '吴快'), ('著籍', '注籍'),
       ('《', ''), ('》', ''), ('“', ''), ('”', '')]


def tts_text(s):
    for a, b in SUB:
        s = s.replace(a, b)
    return s


def f0_median(w, sr):
    p = parselmouth.Sound(w.astype(np.float64), sampling_frequency=sr).to_pitch(pitch_floor=75, pitch_ceiling=300)
    v = p.selected_array['frequency']; v = v[v > 0]
    return float(np.median(v)) if len(v) else 0.0


def main():
    k, n = int(sys.argv[1]), int(sys.argv[2])
    force = '--force' in sys.argv
    only = [a for a in sys.argv[3:] if not a.startswith('--')]
    torch.set_num_threads(int(os.environ.get('NT', 2)))
    lines = [d for i, d in enumerate(all_lines()) if i % n == k and (not only or d['id'] in only)]
    os.makedirs(OUT, exist_ok=True)
    m = Qwen3TTSModel.from_pretrained(f'{W}/models/Qwen3-TTS-12Hz-1.7B-Base', dtype=torch.bfloat16, device_map='cpu')
    ref_w, ref_sr = sf.read(REF_WAV)
    prompt = m.create_voice_clone_prompt(ref_audio=(ref_w.astype(np.float32), ref_sr), ref_text=REF_TEXT)
    seeds0 = int(os.environ.get('SEED0', 1000))
    for d in lines:
        meta_p = f"{OUT}/{d['id']}.json"
        if os.path.exists(meta_p) and not force:
            try:
                if json.load(open(meta_p)).get('text') == d['say']:
                    continue
            except Exception:
                pass
        best = None
        for seed in [seeds0 + 7 * i for i in range(int(os.environ.get('NSEEDS', 3)))]:
            torch.manual_seed(seed); np.random.seed(seed)
            t = time.time()
            wavs, sr = m.generate_voice_clone(text=tts_text(d['say']), language='Chinese', voice_clone_prompt=prompt,
                                              temperature=0.8, subtalker_temperature=0.8)
            w = wavs[0].astype(np.float32)
            f0 = f0_median(w, sr); dur = len(w) / sr
            nch = len(re.sub(r'[，。？！：；、“”《》\s]', '', d['say']))
            # 语速异常（卡住、重复）也算失败
            ok = F0_LO <= f0 <= F0_HI and 2.6 <= nch / dur <= 6.0
            print(f"{d['id']} seed={seed} f0={f0:.1f} dur={dur:.1f}s cps={nch/dur:.2f} gen={time.time()-t:.0f}s ok={ok}", flush=True)
            cand = dict(seed=seed, f0=f0, dur=dur, ok=ok, w=w, sr=sr)
            if best is None or (ok and not best['ok']) or (ok == best['ok'] and abs(f0 - 95) < abs(best['f0'] - 95)):
                best = cand
            if ok:
                break
        sf.write(f"{OUT}/{d['id']}.wav", best['w'], best['sr'])
        json.dump(dict(id=d['id'], seed=best['seed'], f0=best['f0'], dur=best['dur'], ok=best['ok'], text=d['say']),
                  open(meta_p, 'w'), ensure_ascii=False)


if __name__ == '__main__':
    main()
