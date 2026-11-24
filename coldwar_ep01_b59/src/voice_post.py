"""Post-process QC'd narration lines and assemble a voice track (+ optional score bed).

Per line: trim -> compress pauses (<=0.4 s) -> rubberband tempo (R3, formant-preserving;
narration faster, quotes slower) -> 50 Hz high-pass -> active RMS -18 dBFS.
Lines are joined with gaps <= 0.4 s. Final mix is read back by ASR as a whole.
"""
import json
import os
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(__file__))
import voiceqc as Q  # noqa: E402

SR_OUT = 48000


def resample(x, sr, to=SR_OUT):
    if sr == to:
        return x
    from scipy.signal import resample_poly
    from math import gcd
    g = gcd(sr, to)
    return resample_poly(x, to // g, sr // g).astype(np.float32)


def process_line(x, sr, kind, tempo_n, tempo_q):
    x = Q.trim_silence(x, sr)
    x = Q.compress_pauses(x, sr, Q.MAX_PAUSE)
    x = Q.rubberband_tempo(x, sr, tempo_q if kind == "Q" else tempo_n)
    x = Q.compress_pauses(x, sr, Q.MAX_PAUSE)  # stretching can't lengthen, but keep the guarantee
    x = resample(x, sr)
    x = Q.highpass50(x, SR_OUT)
    x = Q.normalize_rms(x, SR_OUT, Q.TARGET_RMS_DBFS)
    return x


def gap_after(text, nxt_kind):
    if text.endswith("：") and nxt_kind == "Q":
        return 0.22
    if text.endswith(("。", "！", "？", "”")):
        return 0.36
    return 0.18


def assemble(lines, wav_by_id, kinds, tempo_n, tempo_q, lead=0.6, tail=1.2):
    parts = [np.zeros(int(lead * SR_OUT), np.float32)]
    timeline = []
    t = lead
    rows = []
    for i, ln in enumerate(lines):
        x, sr = sf.read(wav_by_id[ln["id"]], dtype="float32")
        y = process_line(x, sr, kinds[ln["id"]], tempo_n, tempo_q)
        parts.append(y)
        timeline.append({"id": ln["id"], "start": round(t, 3), "end": round(t + len(y) / SR_OUT, 3), "text": ln["text"]})
        rows.append({"id": ln["id"], "kind": kinds[ln["id"]], "f0_after": round(float(Q.f0_median(y, SR_OUT)), 1),
                     "rate_after": round(float(Q.speech_rate(ln["tts"], y, SR_OUT)), 2),
                     "longest_pause": round(float(Q.longest_pause(y, SR_OUT)), 2),
                     "rms_dbfs": round(float(Q.active_rms_db(y, SR_OUT)), 1)})
        t += len(y) / SR_OUT
        if i + 1 < len(lines):
            g = gap_after(ln["text"], kinds[lines[i + 1]["id"]])
            parts.append(np.zeros(int(g * SR_OUT), np.float32))
            t += g
    parts.append(np.zeros(int(tail * SR_OUT), np.float32))
    return np.concatenate(parts), timeline, rows


def _fit(x, n):
    return np.pad(x, (0, max(0, n - len(x))))[:n]


def score_bed(dur, voice):
    import sound as S
    n = len(voice)
    music = np.zeros(n)
    d = _fit(S.drone(dur + 0.1, 55.0), n)
    music += d / np.sqrt(np.mean(d ** 2)) * 0.020
    p = _fit(S.string_pad(dur + 0.1, [73.42, 110.0, 174.61], attack=5.0, release=4.0), n)
    music += p / np.sqrt(np.mean(p ** 2) + 1e-9) * 0.009
    ping = S.sonar_ping()
    ping /= np.max(np.abs(ping))
    S.place(music, ping * 0.09, 0.1)
    S.place(music, ping * 0.06, dur * 0.45)
    g = S.metal_groan()
    g /= np.max(np.abs(g))
    S.place(music, g * 0.05, dur * 0.25)
    music = S.duck(music, voice, depth=0.5)
    return music.astype(np.float32)


def main(qc_or_dir, lines_path, out_prefix, tempo_n, tempo_q, source="qwen"):
    lines = json.load(open(lines_path))
    if source == "qwen":
        qc = json.load(open(qc_or_dir))
        wav_by_id = {k: v["path"] for k, v in qc.items()}
    else:  # directory of <id>.wav (kokoro)
        wav_by_id = {ln["id"]: os.path.join(qc_or_dir, ln["id"] + ".wav") for ln in lines}
    kinds = {ln["id"]: ln.get("kind", "N") for ln in lines}
    voice, timeline, rows = assemble(lines, wav_by_id, kinds, tempo_n, tempo_q)
    sf.write(out_prefix + "_voice.wav", voice, SR_OUT)
    music = score_bed(len(voice) / SR_OUT, voice)
    mix = voice + music
    peak = np.max(np.abs(mix))
    if peak > 0.89:
        mix = np.tanh(mix / 0.89) * 0.89
    sf.write(out_prefix + "_mix.wav", mix.astype(np.float32), SR_OUT)
    # whole-mix ASR read-back
    heard = Q.asr(mix, SR_OUT)
    expected = "".join(ln["tts"] for ln in lines)
    ser = Q.syllable_error_rate(expected, heard)
    rep = {"tempo_narration": tempo_n, "tempo_quote": tempo_q, "duration_s": round(len(mix) / SR_OUT, 2),
           "voice_active_rms_dbfs": round(float(Q.active_rms_db(voice, SR_OUT)), 1),
           "music_rms_dbfs": round(float(20 * np.log10(np.sqrt(np.mean(music ** 2)) + 1e-12)), 1),
           "mix_asr": heard, "mix_ser": round(float(ser), 3), "mix_diff": Q.diff_report(expected, heard),
           "lines": rows, "timeline": timeline}
    json.dump(rep, open(out_prefix + "_report.json", "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: rep[k] for k in ("duration_s", "voice_active_rms_dbfs", "music_rms_dbfs", "mix_ser")},
                     ensure_ascii=False))
    for r in rows:
        print(r)
    print("mix diff:", rep["mix_diff"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5]),
         sys.argv[6] if len(sys.argv) > 6 else "qwen")
