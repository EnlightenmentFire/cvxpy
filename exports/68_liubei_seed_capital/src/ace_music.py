"""ACE-Step 1.5 turbo (MIT; model card: generated music usable commercially) local music layers. DiT only, no LM.
python ace_music.py OUTDIR layer=secs ..."""
import json, os, sys, time
ACE = "/home/user/work/acestep/code"
sys.path.insert(0, ACE)
PROMPTS = {
    "base": ("solemn ancient chinese documentary underscore, chinese bamboo flute dizi melody, low cellos and double basses holding long notes, "
             "soft guzheng plucks, calm, spacious, noble, A minor, 66 bpm, no drums, no vocals, instrumental film score"),
    "rise": ("ancient chinese historical documentary underscore, dizi flute melody over warm low strings, gentle pulse of low strings, hopeful and noble, "
             "light frame drum, A minor, 72 bpm, no vocals, instrumental film score"),
    "push": ("epic cinematic orchestral build, galloping low strings ostinato, deep taiko drums driving rhythm, chinese dizi flute heroic melody, "
             "horses charging, ancient chinese war, A minor, 92 bpm, no vocals, instrumental film score"),
    "war": ("tense cinematic underscore for war map, low strings ostinato, steady war drums, low brass swells, chinese flute, ancient battle, "
            "A minor, 80 bpm, no vocals, instrumental film score"),
    "coda": ("noble reflective ending, solo chinese dizi flute over sustained low strings, slow, warm, long reverb, A minor, 60 bpm, no drums, no vocals, instrumental"),
}
PROMPTS["base2"] = PROMPTS["base"]
BPM = {"base2": 66, "base": 66, "rise": 72, "push": 92, "war": 80, "coda": 60}
def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    jobs = [(a.split("=")[0], float(a.split("=")[1])) for a in sys.argv[2:]]
    import torch
    torch.set_num_threads(int(os.environ.get("ACE_THREADS", "4")))
    from acestep.handler import AceStepHandler
    from acestep.llm_inference import LLMHandler
    from acestep.inference import GenerationParams, GenerationConfig, generate_music
    t0 = time.time()
    dit = AceStepHandler()
    msg, ok = dit.initialize_service(project_root=ACE, config_path="acestep-v15-turbo", device="cpu")
    print("init", ok, msg, round(time.time() - t0, 1), flush=True)
    llm = LLMHandler()
    log = []
    for layer, dur in jobs:
        seed = 2026 + len(layer) * 13
        p = GenerationParams(caption=PROMPTS[layer], lyrics="[Instrumental]", instrumental=True, bpm=BPM[layer], keyscale="A minor",
                             timesignature="4", duration=dur, inference_steps=8, seed=seed, thinking=False, use_cot_metas=False,
                             use_cot_caption=False, use_cot_language=False)
        c = GenerationConfig(batch_size=1, use_random_seed=False, seeds=[seed], audio_format="wav")
        t1 = time.time()
        res = generate_music(dit, llm, p, c, save_dir=os.path.join(out, layer))
        files = [os.path.join(r, f) for r, _, fs in os.walk(os.path.join(out, layer)) for f in fs if f.endswith((".wav", ".flac", ".mp3"))]
        print(layer, dur, round(time.time() - t1), files, flush=True)
        log.append(dict(layer=layer, seed=seed, dur=dur, files=files, prompt=PROMPTS[layer]))
        json.dump(log, open(os.path.join(out, "gen_log.json"), "w"), indent=1)
if __name__ == "__main__":
    main()
