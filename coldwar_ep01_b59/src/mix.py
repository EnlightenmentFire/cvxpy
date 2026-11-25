"""Final mix per 配乐规范: voice + score (MusicGen layers by default; sidechain-ducked, 2-4 kHz carve) + sound design,
two-pass loudnorm to -16 LUFS / -1.5 dBTP, then self-checks (levels, ASR on mix and phone-speaker sim).

Run in the qwen312 venv:  python mix.py build   |   python mix.py check
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy import signal

sys.path.insert(0, os.path.dirname(__file__))
SCR = "/tmp/claude-0/-home-user-cvxpy/c6f191ba-c6fe-598c-beeb-d3aef80994fb/scratchpad"
EDIT = os.path.join(SCR, "edit")
SR = 48000


def loudnorm_two_pass(src, dst, I=-16.0, TP=-1.5, LRA=11.0):
    p1 = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-af",
                         f"loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    m = json.loads(p1[p1.rindex("{"): p1.rindex("}") + 1])
    af = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
          f"linear=true:print_format=json")
    p2 = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-y", "-i", src, "-af", af, "-ar", str(SR), dst],
                        capture_output=True, text=True).stderr
    m2 = json.loads(p2[p2.rindex("{"): p2.rindex("}") + 1])
    return m, m2


def measure(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])
    tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])
    lra = float(re.findall(r"LRA:\s+(-?[\d.]+) LU", r)[-1])
    return I, tp, lra


def build():
    import music
    import score
    tl = json.load(open(os.path.join(EDIT, "timeline.json")))
    voice, sr = sf.read(os.path.join(EDIT, "voice.wav"), dtype="float32")
    assert sr == SR
    mus, key, depth, log = music.build(tl, voice)
    sfx = score.build_sfx(tl, voice, SR)
    n = len(voice)
    mix = np.stack([voice, voice], 1) + mus[:n] + np.stack([sfx[:n], sfx[:n]], 1)
    pre = os.path.join(EDIT, "premix_v2.wav")
    sf.write(pre, mix.astype(np.float32), SR, subtype="FLOAT")
    sf.write(os.path.join(EDIT, "music_v2.wav"), mus[:n].astype(np.float32), SR, subtype="FLOAT")
    np.save(os.path.join(EDIT, "sc_key.npy"), key[::480])
    lim = os.path.join(EDIT, "premix_v2_lim.wav")
    # tame transient SFX peaks first so loudnorm can stay in linear (non-pumping) mode
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", pre, "-af",
                    "alimiter=limit=0.6:attack=3:release=60:level=false:asc=1", "-c:a", "pcm_f32le", lim], check=True)
    m1, m2 = loudnorm_two_pass(lim, os.path.join(EDIT, "mix_v2.wav"))
    json.dump({"segments": log, "loudnorm_pass1": m1, "loudnorm_pass2": m2},
              open(os.path.join(EDIT, "music_log.json"), "w"), ensure_ascii=False, indent=1)
    print("loudnorm in:", m1["input_i"], "LUFS,", m1["input_tp"], "dBTP -> out:", m2["output_i"], "LUFS,",
          m2["output_tp"], "dBTP (", m2["normalization_type"], ")")


def _frames_db(x, hop):
    n = len(x) // hop
    fr = x[: n * hop].reshape(n, hop, -1) if x.ndim == 2 else x[: n * hop].reshape(n, hop)
    return 20 * np.log10(np.sqrt(np.mean(fr ** 2, axis=tuple(range(1, fr.ndim)))) + 1e-12)


def check():
    import voiceqc as Q
    tl = json.load(open(os.path.join(EDIT, "timeline.json")))
    T = {s["id"]: s["start"] for s in tl["shots"]}
    voice, _ = sf.read(os.path.join(EDIT, "voice.wav"), dtype="float32")
    mus, _ = sf.read(os.path.join(EDIT, "music_v2.wav"), dtype="float32")
    mix, _ = sf.read(os.path.join(EDIT, "mix_v2.wav"), dtype="float32")
    I, tp, lra = measure(os.path.join(EDIT, "mix_v2.wav"))
    rep = {"integrated_lufs": I, "true_peak_dbtp": tp, "lra": lra}
    # music under narration vs voice (200 ms frames, before final loudnorm: same gain applies to both)
    hop = int(0.2 * SR)
    vdb = _frames_db(voice, hop)
    mdb = _frames_db(mus, hop)
    speaking = vdb > -30
    gap = (vdb - mdb)[speaking]
    rep["music_under_voice_db"] = {"median": round(float(np.median(gap)), 1), "p10": round(float(np.percentile(gap, 10)), 1),
                                   "p90": round(float(np.percentile(gap, 90)), 1)}
    sections = [("铺底 片头→扎进海底", 0, T["dive"]), ("推进1 海底→声呐（无鼓）", T["dive"], T["sonar"]),
                ("推进2 声呐→命令（心跳低鼓）", T["sonar"], T["hypo_launch"]),
                ("高潮 假想段", T["hypo_burst"] + 0.5, T["hypo_out"] + 1.1), ("变稀 浮上来→门外", T["surfacing"], T["ending"]),
                ("收尾 单件乐器", T["ending"], T["credits"] + 4.4)]
    secs = []
    for name, a, b in sections:
        i0, i1 = int(a / 0.2), int(b / 0.2)
        sp = speaking[i0:i1]
        md = mdb[i0:i1]
        vd = vdb[i0:i1]
        secs.append({"section": name, "music_rms_in_pauses_db": round(float(np.median(md[~sp])) if (~sp).any() else -99, 1),
                     "music_rms_under_voice_db": round(float(np.median(md[sp])) if sp.any() else -99, 1),
                     "voice_rms_db": round(float(np.median(vd[sp])) if sp.any() else -99, 1),
                     "gap_db_median": round(float(np.median((vd - md)[sp])) if sp.any() else -99, 1)})
    rep["sections"] = secs
    # climax: music alone after the last hypothetical line
    e04_end = T["hypo_globe"] + [s for s in tl["shots"] if s["id"] == "hypo_globe"][0]["cues"]["e04"][1]
    a, b = e04_end + 0.6, T["hypo_out"] + 1.05
    rep["climax_music_alone"] = {"from": round(e04_end, 2), "to": round(T["hypo_out"] + 1.1, 2),
                                 "music_rms_db": round(float(_frames_db(mus[int(a * SR):int(b * SR)], int((b - a) * SR))[0]), 1)}
    # sudden jumps in the music bus (400 ms short-term, rise within 1 s), ignoring designed hits
    st = _frames_db(mus, int(0.1 * SR))
    st = np.convolve(st, np.ones(4) / 4, "same")
    rise = st[10:] - st[:-10]
    e04_end_ = T["hypo_globe"] + [s for s in tl["shots"] if s["id"] == "hypo_globe"][0]["cues"]["e04"][1]
    designed = [T["hypo_burst"] + 0.5, T["surfacing"] - 2.0, 0.0, e04_end_]
    big = [(round(i * 0.1, 1), round(float(r), 1)) for i, r in enumerate(rise) if r > 9
           and min(abs(i * 0.1 - d) for d in designed) > 2.5 and st[i + 10] > -40]
    rep["music_jumps_over_9db_per_s"] = big[:20]
    if "noasr" in sys.argv:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
        return
    # ASR: each line on voice-only, on the final mix, and on a phone-speaker simulation of the mix
    lines = {ln["id"]: ln for ln in json.load(open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "audio/full/lines.json")))}
    mono = mix.mean(1)
    sos = signal.butter(4, [300 / (SR / 2), 7000 / (SR / 2)], "band", output="sos")
    phone = signal.sosfilt(sos, mono).astype(np.float32)
    worse = []
    tot = {"voice": 0, "mix": 0, "phone": 0}
    nsyl = 0
    for sh in tl["shots"]:
        for lid, (s0, s1) in sh["cues"].items():
            a, b = int((sh["start"] + s0 - 0.15) * SR), int((sh["start"] + s1 + 0.15) * SR)
            exp = lines[lid]["tts"]
            n_ = len(Q.to_syllables(exp))
            nsyl += n_
            r = {}
            for k, sig in (("voice", voice), ("mix", mono), ("phone", phone)):
                h = Q.asr(sig[a:b], SR)
                e = Q.syllable_error_rate(exp, h)
                tot[k] += e * n_
                r[k] = (round(e, 3), h)
            if r["mix"][0] > r["voice"][0] or r["phone"][0] > r["voice"][0]:
                worse.append({"id": lid, "voice": r["voice"], "mix": r["mix"], "phone": r["phone"]})
    rep["asr_syllable_error_rate"] = {k: round(v / nsyl, 4) for k, v in tot.items()}
    rep["asr_lines_worse_than_voice"] = worse
    json.dump(rep, open(os.path.join(EDIT, "mix_v2_check.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != "asr_lines_worse_than_voice"}, ensure_ascii=False, indent=1))
    print("lines worse than voice-only:", len(worse))
    for w in worse:
        print(w)


if __name__ == "__main__":
    {"build": build, "check": check}[sys.argv[1]]()
