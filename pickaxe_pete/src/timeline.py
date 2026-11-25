"""Builds the master timeline from the final voice clip lengths (visuals are retimed to the audio)."""
import json
import soundfile as sf
from script_data import LINES

# extra visual time after a scene's last line (gags, transitions)
TAIL = {1: 2.3, 2: 0.5, 3: 0.6, 4: 0.9, 5: 0.45, 6: 0.45, 7: 1.0, 8: 3.0}
# scene intro overrides (time before the scene's first line)
INTRO = {1: 2.4, 2: 1.2, 3: 0.9, 4: 0.7, 5: 0.8, 6: 0.6, 7: 1.0, 8: 0.8}


def build(voice_dir="audio/voice"):
    lines, scenes = [], []
    T = 0.0
    cur_scene = None
    scene_start = 0.0
    for lid, sc, spk, sub, tts, gap, style in LINES:
        dur = sf.info(f"{voice_dir}/{lid}.wav").duration
        if sc != cur_scene:
            if cur_scene is not None:
                T += TAIL[cur_scene]
                scenes.append(dict(scene=cur_scene, start=scene_start, end=T))
            cur_scene = sc
            scene_start = T
            T += INTRO[sc]
        else:
            T += gap
        # Riggy's echo tail is part of the file; speech ends ~0.35s earlier
        speech_end = T + dur - (0.35 if spk == "RIGGY" else 0.0)
        lines.append(dict(id=lid, scene=sc, speaker=spk, text=sub, start=round(T, 3), end=round(speech_end, 3), style=style))
        T = speech_end
    T += TAIL[cur_scene]
    scenes.append(dict(scene=cur_scene, start=scene_start, end=T))
    tl = dict(lines=lines, scenes=scenes, total=round(T, 3))
    tl["line_index"] = {l["id"]: (l["start"], l["end"]) for l in lines}
    return tl


if __name__ == "__main__":
    tl = build()
    json.dump(tl, open("timeline.json", "w"), indent=1)
    for s in tl["scenes"]:
        print("scene", s["scene"], round(s["start"], 2), "->", round(s["end"], 2), f"({s['end'] - s['start']:.1f}s)")
    print("TOTAL", tl["total"])
