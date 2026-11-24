"""CosyVoice-300M-SFT wrapper (Apache-2.0 code + weights). text -> 24 kHz mono float32."""
import sys, os, numpy as np
sys.path.insert(0, '/opt/cosy/CosyVoice'); sys.path.insert(0, '/opt/cosy/CosyVoice/third_party/Matcha-TTS')
import torch, torchaudio
torch.set_num_threads(4)
_m = None
def model():
    global _m
    if _m is None:
        from cosyvoice.cli.cosyvoice import CosyVoice
        _m = CosyVoice('/opt/cosy/models/CosyVoice-300M-SFT-hf', load_jit=False, load_trt=False, fp16=False)
    return _m
def synth(text, voice='中文男', speed=1.0, seed=7):
    m = model(); outs = []
    torch.manual_seed(seed); np.random.seed(seed)
    import random; random.seed(seed)
    for o in m.inference_sft(text, voice, stream=False, speed=speed):
        outs.append(o['tts_speech'])
    x = torch.cat(outs, dim=1)
    if m.sample_rate != 24000: x = torchaudio.functional.resample(x, m.sample_rate, 24000)
    return x.squeeze(0).numpy().astype(np.float32)
if __name__ == '__main__':
    import soundfile as sf, time
    t = time.time(); x = synth(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else '中文男', float(sys.argv[3]) if len(sys.argv) > 3 else 1.0)
    sf.write(sys.argv[4] if len(sys.argv) > 4 else 'build/cosy_test.wav', x, 24000)
    print(f'dur={len(x)/24000:.1f}s gen={time.time()-t:.1f}s spk={model().list_available_spks()}')
