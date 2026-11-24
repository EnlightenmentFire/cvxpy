# -*- coding: utf-8 -*-
"""ASR 回读（faster-whisper large-v3-turbo，int8，CPU）。"""
import numpy as np, soundfile as sf
_m = None


def _model():
    global _m
    if _m is None:
        from faster_whisper import WhisperModel
        _m = WhisperModel("/opt/models/whisper-turbo", device="cpu", compute_type="int8", cpu_threads=4)
    return _m


def load16k(path_or_wav, sr=None):
    if isinstance(path_or_wav, str):
        w, sr = sf.read(path_or_wav, dtype="float32")
    else:
        w = path_or_wav
    if w.ndim > 1:
        w = w.mean(1)
    if sr != 16000:
        import librosa
        w = librosa.resample(w, orig_sr=sr, target_sr=16000)
    return w.astype(np.float32)


def transcribe(path, lang="zh", words=False):
    segs, _ = _model().transcribe(load16k(path), language=lang, beam_size=5, word_timestamps=words,
                                   initial_prompt="以下是普通话的句子。" if lang == "zh" else None)
    segs = list(segs)
    if words:
        return segs
    return "".join(s.text for s in segs)
