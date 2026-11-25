# -*- coding: utf-8 -*-
"""Build stems, duck music under narration, loudness-normalise, mux with video.
usage: python final_mux.py audio            -> mix_music.wav, mix_nomusic.wav, narration.wav, report
       python final_mux.py video <out_dir>  -> final mp4s (music / no-music), srt
"""
import sys, os, json, subprocess, re, math
import numpy as np, soundfile as sf
from scipy.ndimage import uniform_filter1d, maximum_filter1d

D = os.path.dirname(os.path.abspath(__file__))
SR = 48000
TL = json.load(open(f"{D}/timeline.json"))
TOTAL = TL["total"]
N = int(round(TOTAL * SR))
MUSIC_UNDER = float(os.environ.get("MUSIC_UNDER", 21.0))  # dB below voice during speech
LIFT = 4.0  # dB lift in long pauses


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    i = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)
    return i, float(tp[-1]) if tp else None


def audio():
    voice = np.zeros(N, np.float32)
    for l in TL["lines"]:
        x, sr = sf.read(f"{D}/tts/proc/{l['id']}.wav")
        assert sr == SR
        i = int(round(l["start"] * SR))
        voice[i:i + len(x)] += x[:N - i]
    sf.write(f"{D}/narration.wav", voice, SR, subtype="FLOAT")
    mus, _ = sf.read(f"{D}/music.wav"); mus = mus[:N].T.astype(np.float32)
    if mus.shape[1] < N:
        mus = np.pad(mus, ((0, 0), (0, N - mus.shape[1])))
    sfx, _ = sf.read(f"{D}/sfx.wav"); sfx = sfx[:N].T.astype(np.float32)
    if sfx.shape[1] < N:
        sfx = np.pad(sfx, ((0, 0), (0, N - sfx.shape[1])))
    # speech-activity envelope (10 ms hop)
    hop = SR // 100
    fr = voice[:N // hop * hop].reshape(-1, hop)
    act = (np.sqrt((fr ** 2).mean(1)) > 10 ** (-45 / 20)).astype(np.float32)
    act = maximum_filter1d(act, size=60)  # hold 0.6 s around speech
    act = uniform_filter1d(act, size=40)  # 0.4 s smoothing
    gain_db_rel = -LIFT * (1 - act)  # 0 in speech, -LIFT.. => we use as lift below
    # levels: measure voice LUFS and music LUFS (speech-gated approx: whole-track)
    sf.write(f"{D}/_m.wav", mus.T, SR, subtype="FLOAT")
    vi, _ = lufs(f"{D}/narration.wav")
    mi, _ = lufs(f"{D}/_m.wav")
    base_gain = vi - MUSIC_UNDER - mi  # dB to apply to music in speech
    g = 10 ** ((base_gain + LIFT * (1 - act)) / 20)
    gs = np.repeat(g, hop)
    gs = np.pad(gs, (0, N - len(gs)), mode="edge")
    # opening: let the qing ring a touch, music already present from frame 0
    mus_d = mus * gs[None, :]
    sfx_gain = 10 ** ((vi - 2 - lufs(f"{D}/sfx.wav")[0]) / 20) if True else 1
    sfx_g = sfx * min(sfx_gain, 3.0)
    v2 = np.stack([voice, voice])
    with_music = v2 + mus_d + sfx_g
    no_music = v2 + sfx_g
    for name, x in [("mix_music", with_music), ("mix_nomusic", no_music)]:
        p = f"{D}/_{name}_pre.wav"
        sf.write(p, x.T, SR, subtype="FLOAT")
        # two-pass loudnorm to -15 LUFS / -1.5 dBTP
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", p, "-af", "loudnorm=I=-15:TP=-2.2:LRA=11:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        js = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
        af = (f"loudnorm=I=-15:TP=-2.2:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
              f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true,"
              f"aresample=48000")
        run(["ffmpeg", "-v", "error", "-y", "-i", p, "-af", af, "-ar", "48000", "-c:a", "pcm_s24le", f"{D}/{name}.wav"])
    # report: music vs voice in speech regions
    sf.write(f"{D}/_md.wav", mus_d.T, SR, subtype="FLOAT")
    md, _ = lufs(f"{D}/_md.wav")
    rep = dict(voice_lufs=vi, music_ducked_lufs=md, music_minus_voice_db=round(md - vi, 1), base_gain_db=round(base_gain, 1))
    for name in ["mix_music", "mix_nomusic"]:
        rep[name] = lufs(f"{D}/{name}.wav")
    # per-section music-below-voice (short-term): compute RMS during speech frames
    vs = voice[:N // hop * hop].reshape(-1, hop); ms = mus_d.mean(0)[:N // hop * hop].reshape(-1, hop)
    sp = np.sqrt((vs ** 2).mean(1)) > 10 ** (-40 / 20)
    rep["speech_frames_music_below_voice_rms_db"] = round(float(10 * np.log10((vs[sp] ** 2).mean() / ((ms[sp] ** 2).mean() + 1e-12))), 1)
    json.dump(rep, open(f"{D}/audio_report.json", "w"), indent=1)
    print(json.dumps(rep, indent=1))
    for f in ["_m.wav", "_md.wav", "_mix_music_pre.wav", "_mix_nomusic_pre.wav"]:
        os.remove(f"{D}/{f}")


def srt(path):
    sys.argv = ["x"]
    import render as R
    def ts(t):
        ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    with open(path, "w") as f:
        for i, s in enumerate(R.SUBS, 1):
            f.write(f"{i}\n{ts(s['t0'])} --> {ts(s['t1'])}\n{s['text']}\n\n")


def video(out_dir, stem):
    os.makedirs(out_dir, exist_ok=True)
    chunks = sorted(f for f in os.listdir(f"{D}/out") if f.startswith("chunk_"))
    with open(f"{D}/out/list.txt", "w") as f:
        for c in chunks:
            f.write(f"file '{D}/out/{c}'\n")
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{D}/out/list.txt", "-c", "copy", f"{D}/out/video_cat.mp4"])
    run(["cp", f"{D}/out/video_cat.mp4", f"{D}/out/video_final.mp4"])
    outs = {}
    for name, wav in [(f"{stem}.mp4", "mix_music.wav"), (f"{stem}_无配乐版.mp4", "mix_nomusic.wav")]:
        o = f"{out_dir}/{name}"
        run(["ffmpeg", "-v", "error", "-y", "-i", f"{D}/out/video_final.mp4", "-i", f"{D}/{wav}", "-map", "0:v", "-map", "1:a",
             "-c:v", "copy", "-af", "aresample=async=1", "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
             "-t", f"{TOTAL:.3f}", "-movflags", "+faststart", o])
        outs[name] = o
    return outs


if __name__ == "__main__":
    if sys.argv[1] == "audio":
        audio()
    elif sys.argv[1] == "video":
        outs = video(sys.argv[2], sys.argv[3])
        srt(f"{sys.argv[2]}/{sys.argv[3]}.srt")
        for k, o in outs.items():
            r = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration,r_frame_rate", "-of", "json", o]).stdout
            print(k, os.path.getsize(o) / 1e6, "MB", r.replace("\n", " "))
