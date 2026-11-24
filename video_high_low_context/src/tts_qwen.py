# -*- coding: utf-8 -*-
"""Narration via Qwen3-TTS-12Hz-1.7B-Base, cloning the VoiceDesign reference.

Per clip: generate -> median F0 check (85-105 Hz) -> ASR read-back (faster-whisper,
pinyin comparison) -> retry with a new seed if either fails. Keeps the best attempt.
Usage: python tts_qwen.py clips.json out_dir [--only kinds]
"""
import json
import os
import re
import sys
import time
import zlib

import numpy as np
import soundfile as sf
import torch

torch.set_num_threads(int(os.environ.get("TTS_THREADS", "4")))

S = "/tmp/claude-0/-home-user-cvxpy/3146234e-c880-5dd6-b7f5-20b7a9aa7973/scratchpad"
REF_WAV = os.environ.get("REF_WAV", f"{S}/tts/design/cand_s71.wav")
REF_TEXT = "同一句话，在不同的地方，意思可能差得很远。人类学家把这件事，叫做高语境和低语境。今天，我们就从一间会议室说起。"
F0_LO, F0_HI = 85.0, 105.0
MAX_TRY = int(os.environ.get("MAX_TRY", "5"))


def median_f0(a, sr):
    import parselmouth
    snd = parselmouth.Sound(a.astype(np.float64), sampling_frequency=sr)
    f = snd.to_pitch(pitch_floor=60, pitch_ceiling=300).selected_array["frequency"]
    f = f[f > 0]
    return float(np.median(f)) if len(f) else 0.0


class Checker:
    def __init__(self):
        from faster_whisper import WhisperModel
        import opencc
        self.m = WhisperModel(f"{S}/models/faster-whisper-medium", device="cpu", compute_type="int8",
                              cpu_threads=int(os.environ.get("TTS_THREADS", "4")))
        self.cc = opencc.OpenCC("t2s")

    def norm_py(self, s, lang):
        from pypinyin import lazy_pinyin
        sys.path.insert(0, os.path.dirname(__file__))
        from clips import tts_text
        s = self.cc.convert(s)
        for pat, rep in ((r"麦克|迈克|邁克|麥克", "Mike"), (r"莎拉|萨拉|沙拉|撒拉", "Sarah")):
            s = re.sub(pat, rep, s)
        if lang == "zh":
            s = tts_text(s)
            s = re.sub(r"[^一-鿿A-Za-z]", " ", s)
            toks = []
            for part in re.findall(r"[A-Za-z]+|[一-鿿]", s):
                toks.extend(lazy_pinyin(part) if not part.isascii() else [part.lower()])
            return toks
        return re.findall(r"[a-z']+|[぀-ヿ一-鿿]", s.lower())

    def asr(self, a, sr, lang):
        import librosa
        a16 = librosa.resample(a.astype(np.float32), orig_sr=sr, target_sr=16000)
        segs, _ = self.m.transcribe(a16, language=lang, beam_size=5)
        return "".join(s.text for s in segs).strip()

    def score(self, ref, hyp, lang):
        import jiwer
        r, h = self.norm_py(ref, lang), self.norm_py(hyp, lang)
        if not r:
            return 0.0
        return jiwer.wer(" ".join(r), " ".join(h) if h else "x")


def main():
    clips = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    kinds = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else {"narr", "quote", "jp"}
    os.makedirs(out, exist_ok=True)
    from qwen_tts import Qwen3TTSModel
    model = Qwen3TTSModel.from_pretrained(f"{S}/models/Qwen3-TTS-12Hz-1.7B-Base", device_map="cpu",
                                          dtype=torch.float32)
    prompt = model.create_voice_clone_prompt(ref_audio=REF_WAV, ref_text=REF_TEXT)
    chk = Checker()
    logp = os.path.join(out, "tts_log.jsonl")
    done = set()
    if os.path.exists(logp):
        for l in open(logp):
            done.add(json.loads(l)["cid"])
    for c in clips:
        if c["kind"] not in kinds or c["cid"] in done:
            continue
        lang = "Japanese" if c["kind"] == "jp" else "Chinese"
        alang = "ja" if c["kind"] == "jp" else "zh"
        best = None
        for att in range(MAX_TRY):
            seed = (zlib.crc32(c["cid"].encode()) + att * 7919) % 100000
            torch.manual_seed(seed)
            np.random.seed(seed)
            t0 = time.time()
            wavs, sr = model.generate_voice_clone(text=c["tts"], language=lang, voice_clone_prompt=prompt)
            a = np.asarray(wavs[0], dtype=np.float32)
            f0 = median_f0(a, sr)
            hyp = chk.asr(a, sr, alang)
            err = chk.score(c["tts"], hyp, alang)
            dur = len(a) / sr
            nchar = len(re.sub(r"[^一-鿿A-Za-z぀-ヿ]", "", c["tts"]))
            cps = nchar / max(dur, 0.1)
            ok = (F0_LO <= f0 <= F0_HI or c["kind"] == "jp") and err <= 0.06 and 1.8 <= cps <= 7.5
            rec = dict(cid=c["cid"], att=att, seed=seed, f0=round(f0, 1), err=round(err, 3),
                       dur=round(dur, 2), cps=round(cps, 2), asr=hyp, ok=ok, gen=round(time.time() - t0, 1))
            print(json.dumps(rec, ensure_ascii=False), flush=True)
            badness = (0 if ok else 1, err, abs(f0 - 95))
            if best is None or badness < best[0]:
                best = (badness, a, sr, rec)
            if ok:
                break
        _, a, sr, rec = best
        sf.write(os.path.join(out, c["cid"] + ".wav"), a, sr)
        with open(logp, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
