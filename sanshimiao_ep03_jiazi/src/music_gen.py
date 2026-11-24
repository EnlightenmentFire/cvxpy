"""Generate candidate beds with MusicGen (facebook/musicgen-stereo-medium, CC-BY-NC weights? see README note).
Usage: python music_gen.py out_dir seeds [seconds]"""
import os, sys, time, json
import numpy as np, soundfile as sf, torch

PROMPT = ("bright ticking clockwork ostinato, pizzicato strings and marimba, light percussion, "
          "building and accelerating, uplifting, major key, 120 bpm, no vocals")


def main(out, seeds, secs=30.0):
    os.makedirs(out, exist_ok=True)
    torch.set_num_threads(4)
    from transformers import AutoProcessor, MusicgenForConditionalGeneration
    path = "/opt/models/musicgen-stereo-medium"
    proc = AutoProcessor.from_pretrained(path)
    m = MusicgenForConditionalGeneration.from_pretrained(path, torch_dtype=torch.float32)
    m.eval()
    sr = m.config.audio_encoder.sampling_rate
    inputs = proc(text=[PROMPT], padding=True, return_tensors="pt")
    ntok = int(secs * m.config.audio_encoder.frame_rate) + 4
    for s in seeds:
        torch.manual_seed(s)
        t0 = time.time()
        with torch.inference_mode():
            a = m.generate(**inputs, do_sample=True, guidance_scale=3.0, max_new_tokens=ntok)
        w = a[0].float().cpu().numpy().T          # (T, 2)
        p = f"{out}/music_seed{s}.wav"
        sf.write(p, w, sr)
        print(json.dumps(dict(seed=s, path=p, dur=len(w) / sr, gen_s=round(time.time() - t0, 1))), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], [int(x) for x in sys.argv[2].split(",")], float(sys.argv[3]) if len(sys.argv) > 3 else 30.0)
