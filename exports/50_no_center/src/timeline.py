"""时间线：按逐句配音时长 + 停顿排出每句起止，场景 = 相邻同 scene 的句子。"""
import os, re, json
import soundfile as sf
from script_data import all_lines

PROC = os.environ.get("PROC", "/tmp/claude-0/work/tts/proc")
LEAD = 0.25          # 第一句从 0.25 秒开始（首帧就有画面和标题）
TAIL = 4.0           # 最后一句后留的余音

def nchars(s):
    return len(re.sub(r"[，。？！：；、「」《》“”\s]", "", s))

def dur_of(d):
    p = f"{PROC}/{d['id']}.wav"
    if os.path.exists(p):
        return sf.info(p).duration
    return nchars(d["say"]) / 4.6 + 0.3

def build():
    t = LEAD
    lines = []
    for d in all_lines():
        du = dur_of(d)
        lines.append(dict(d, start=t, end=t + du))
        t += du + d["gap"]
    total = lines[-1]["end"] + TAIL
    scenes = []
    for ln in lines:
        if scenes and scenes[-1]["key"] == ln["scene"]:
            scenes[-1]["lines"].append(ln)
        else:
            scenes.append(dict(key=ln["scene"], lines=[ln]))
    for i, s in enumerate(scenes):
        s["t0"] = 0.0 if i == 0 else scenes[i - 1]["lines"][-1]["end"] + min(0.35, scenes[i - 1]["lines"][-1]["gap"] * 0.6)
    for i, s in enumerate(scenes):
        s["t1"] = scenes[i + 1]["t0"] if i + 1 < len(scenes) else total
    return lines, scenes, total

if __name__ == "__main__":
    lines, scenes, total = build()
    print(f"total {total:.1f}s = {total/60:.2f} min, {len(scenes)} scenes")
    for s in scenes:
        print(f"{s['key']:14s} {s['t0']:7.1f} {s['t1']:7.1f} {s['t1']-s['t0']:5.1f}s")
