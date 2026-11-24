"""Voice QC beyond the per-line gate:
 1) final narration: ASR again with a vocabulary prompt (so isolated 干支 characters aren't replaced by
    common homophones) and compare WITH tones;
 2) a test read of all 22 干支 characters in the cloned voice, ASR'd with and without the prompt,
    compared syllable-by-syllable with tones (the narration itself only says 甲子戌申午丑).
Usage: python qc_voice.py lines.json voice.wav ref.wav out.json"""
import json, os, sys
import numpy as np, soundfile as sf, torch
sys.path.insert(0, os.path.dirname(__file__))
import asrcheck as A
from voice_design import REF_TEXT

PROMPT = "天干地支：甲乙丙丁戊己庚辛壬癸，子丑寅卯辰巳午未申酉戌亥。甲子，甲戌，甲申，甲午，纪年，配对。"
LIST = "天干：甲、乙、丙、丁、戊、己、庚、辛、壬、癸。地支：子、丑、寅、卯、辰、巳、午、未、申、酉、戌、亥。"


def tone_diff(ref, hyp):
    import jiwer
    r, _ = A.norm_py(ref, tone=True)
    h, _ = A.norm_py(hyp, tone=True)
    out = jiwer.process_words(" ".join(r), " ".join(h) if h else "x")
    return out.wer, [(a.type, " ".join(r[a.ref_start_idx:a.ref_end_idx]), " ".join(h[a.hyp_start_idx:a.hyp_end_idx]))
                     for a in out.alignments[0] if a.type != "equal"]


def main():
    lines = json.load(open(sys.argv[1]))
    ref_all = "".join(L["tts"] for L in lines)
    v, sr = sf.read(sys.argv[2], dtype="float32")
    rep = {}
    for name, pr in (("plain", None), ("primed", PROMPT)):
        hyp = A.transcribe(v, sr, prompt=pr)
        w, diffs = tone_diff(ref_all, hyp)
        rep[f"narration_{name}"] = dict(asr=hyp, per_toneless=round(A.per(ref_all, hyp), 4), per_tone=round(w, 4), diffs=diffs)
        print(name, hyp, rep[f"narration_{name}"]["per_toneless"], round(w, 4), diffs, flush=True)
    torch.set_num_threads(4)
    from qwen_tts import Qwen3TTSModel
    m = Qwen3TTSModel.from_pretrained("/opt/models/Qwen3-TTS-12Hz-1.7B-Base", device_map="cpu", dtype=torch.bfloat16)
    prompt = m.create_voice_clone_prompt(ref_audio=sys.argv[3], ref_text=REF_TEXT)
    torch.manual_seed(7); np.random.seed(7)
    wavs, sr2 = m.generate_voice_clone(text=LIST, language="Chinese", voice_clone_prompt=prompt)
    a = np.asarray(wavs[0], np.float32)
    sf.write(os.path.splitext(sys.argv[4])[0] + "_ganzhi_list.wav", a, sr2)
    for name, pr in (("plain", None), ("primed", PROMPT)):
        hyp = A.transcribe(a, sr2, prompt=pr)
        w, diffs = tone_diff(LIST, hyp)
        rep[f"ganzhi_list_{name}"] = dict(asr=hyp, per_tone=round(w, 4), diffs=diffs)
        print("list", name, hyp, round(w, 4), diffs, flush=True)
    json.dump(rep, open(sys.argv[4], "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
