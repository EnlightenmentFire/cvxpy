"""Step 1 of the voice pipeline: design a reference voice with Qwen3-TTS VoiceDesign.

Generates N candidates from a text description (no real person is cloned),
measures each candidate's median pitch with parselmouth, and reports which is
closest to the target. Run in the qwen312 venv:
    python qwen_design.py out_dir [n] [target_hz]
"""
import os, sys, json, time, glob
import numpy as np
import soundfile as sf
import torch
import parselmouth

INSTRUCT = '四十多岁男中音，醇厚偏低沉，历史纪录片旁白，凝重克制，语速中等偏慢'
REF_TEXT = '一九八三年三月，一位美国总统在电视上描绘了一片天空。四十多年过去了，这片天空从来没有出现过。'


def median_f0(wav, sr):
    snd = parselmouth.Sound(wav.astype(np.float64), sampling_frequency=sr)
    pitch = snd.to_pitch(time_step=0.01, pitch_floor=60, pitch_ceiling=300)
    f = pitch.selected_array['frequency']
    f = f[f > 0]
    return float(np.median(f)) if len(f) else 0.0


def main():
    out = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    target = float(sys.argv[3]) if len(sys.argv) > 3 else 90.0
    os.makedirs(out, exist_ok=True)
    torch.set_num_threads(int(os.environ.get('TTS_THREADS', '4')))
    from qwen_tts import Qwen3TTSModel
    path = os.environ.get('QWEN_VD_PATH') or glob.glob(os.path.expanduser(
        '~/.cache/huggingface/hub/models--Qwen--Qwen3-TTS-12Hz-1.7B-VoiceDesign/snapshots/*'))[0]
    model = Qwen3TTSModel.from_pretrained(path, device_map='cpu', dtype=getattr(torch, os.environ.get('QWEN_DTYPE', 'bfloat16')))
    rows = []
    for k in range(n):
        seed = 1000 + k
        torch.manual_seed(seed); np.random.seed(seed)
        t0 = time.time()
        wavs, sr = model.generate_voice_design(text=REF_TEXT, instruct=INSTRUCT, language='Chinese')
        w = np.asarray(wavs[0], np.float32)
        f0 = median_f0(w, sr)
        path = os.path.join(out, f'design_seed{seed}.wav')
        sf.write(path, w, sr)
        rows.append({'seed': seed, 'path': path, 'f0': f0, 'dur': len(w) / sr, 'sr': sr, 'gen_s': time.time() - t0})
        print(rows[-1], flush=True)
    best = min(rows, key=lambda r: abs(r['f0'] - target))
    json.dump({'instruct': INSTRUCT, 'ref_text': REF_TEXT, 'candidates': rows, 'chosen': best},
              open(os.path.join(out, 'design.json'), 'w'), ensure_ascii=False, indent=1)
    print('chosen', best)


if __name__ == '__main__':
    main()
