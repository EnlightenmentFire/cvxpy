# -*- coding: utf-8 -*-
"""Final mix per 配乐规范 §4 (sidechain ducking, 3 kHz cut, fades, two-pass loudnorm -16 LUFS / -1.5 dBTP).
usage: python final_mix.py <voice.wav> <sfx.wav> <music.wav> <out.wav> [music_volume]
"""
import sys, os, json, subprocess, re
import numpy as np, soundfile as sf

def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)

def chain(vol, total, with_loudnorm=None, duck_only=False):
    fade_out_st = max(0.0, total - 3.0)
    m = (f"[2:a]volume={vol},equalizer=f=3000:t=q:w=1:g=-4,afade=t=in:d=2,"
         f"afade=t=out:st={fade_out_st:.3f}:d=3[m];")
    v = "[0:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[v][sc];"
    sc = "[m][sc]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=500[duck];"
    if duck_only:
        return v + m + sc + "[v]anullsink"
    fx = "[1:a]aformat=sample_rates=48000:channel_layouts=stereo[fx];"
    mix = "[v][fx][duck]amix=inputs=3:duration=first:normalize=0[pre];"
    ln = with_loudnorm or "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json"
    return v + m + sc + fx + mix + f"[pre]{ln}[out]"

def main():
    voice, sfx, music, out = sys.argv[1:5]
    vol = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
    total = sf.info(voice).duration
    ins = ["-i", voice, "-i", sfx, "-i", music]
    # pass 1: measure
    r = run(["ffmpeg", "-y", "-hide_banner", *ins, "-filter_complex", chain(vol, total), "-map", "[out]", "-f", "null", "-"])
    js = json.loads(re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr)[-1])
    ln2 = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
           f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:"
           f"linear=true:print_format=json")
    r = run(["ffmpeg", "-y", "-hide_banner", *ins, "-filter_complex", chain(vol, total, ln2), "-map", "[out]",
             "-ar", "48000", "-c:a", "pcm_s16le", out])
    js2 = json.loads(re.findall(r"\{[^{}]*\"output_i\"[^{}]*\}", r.stderr)[-1])
    # ducked music stem alone (for level checks)
    duck = os.path.splitext(out)[0] + "_music_ducked.wav"
    run(["ffmpeg", "-y", "-hide_banner", *ins, "-filter_complex", chain(vol, total, duck_only=True),
         "-map", "[duck]", "-ar", "48000", duck])
    print(json.dumps(dict(out=out, music_volume=vol, output_I=js2["output_i"], output_TP=js2["output_tp"],
                          output_LRA=js2["output_lra"], normalization=js2.get("normalization_type"))))

if __name__ == "__main__":
    main()
