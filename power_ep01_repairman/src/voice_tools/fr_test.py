import sys, os, torch, soundfile as sf
torch.set_num_threads(4)
sys.path.insert(0, os.path.dirname(__file__))
from qwen_tts import Qwen3TTSModel
from asr import transcribe
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
m = Qwen3TTSModel.from_pretrained(f"{W}/models/Qwen3-TTS-12Hz-1.7B-Base", device_map="cpu", dtype=torch.bfloat16)
prompt = m.create_voice_clone_prompt(ref_audio=f"{W}/voice/design_seed3.wav",
    ref_text="上世纪五十年代，法国一家国营烟草厂里，组织图上最不起眼的一群人，成了车间里真正说了算的人。")
tests = ["zone d'incertitude.", "C'est une zone d'incertitude.", "cercle vicieux.", "C'est un cercle vicieux."]
os.makedirs(f"{W}/voice/fr", exist_ok=True)
for seed in (11, 12, 13):
    torch.manual_seed(seed)
    wavs, sr = m.generate_voice_clone(text=tests, language=["French"] * len(tests), voice_clone_prompt=prompt * len(tests))
    for k, w in enumerate(wavs):
        p = f"{W}/voice/fr/fr_{k}_s{seed}.wav"
        sf.write(p, w, sr)
        print(seed, k, repr(tests[k]), "->", repr(transcribe(p, lang="fr")), flush=True)
