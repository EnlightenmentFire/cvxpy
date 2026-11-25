"""按时间线生成配乐（自制）、音效，并与旁白混音。
输出：build/music.wav、build/sfx.wav、build/voice.wav、build/mix_full.wav（-15 LUFS）、build/mix_nomusic.wav
"""
import sys, os, json, math
import numpy as np, soundfile as sf, pyloudnorm as pyln
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import synth as S
from synth import SR

WK = os.environ.get("WORK", "/tmp/claude-0/work")
TL = json.load(open(f"{WK}/build/timeline.json"))
N = int(TL["total"] * SR) + SR

# 段落强度（0–1）与配器
INT = dict(hook=0.8, names=0.6, charcoal_flash=0.62, palace_flash=0.62, vessel=0.5, question=0.5, guoshi_title=0.9,
           map=0.75, vessel2=0.4, mountain=0.28, quote_big=0.4, palace=0.42, heart=0.45, arrest=0.65, release=0.4,
           mech_release=0.3, charcoal=0.4, market=0.3, friend=0.3, hard_path=0.45, mech_signal=0.28, bridge_ambush=0.75,
           interrogation=0.55, seen=0.32, mech_recip=0.28, org=0.28, zhibo=0.35, surround=0.72, request=0.62,
           robe_given=0.8, strike=1.0, final_words=0.22, fallen=0.18, tears=0.28, legend=0.22, dawn=0.33,
           takeaway=0.45, taishigong=0.5)
DRUMS = {"hook", "names", "charcoal_flash", "palace_flash", "guoshi_title", "map", "arrest", "bridge_ambush",
         "interrogation", "surround", "request", "robe_given", "strike"}
TENSE = {"palace", "heart", "arrest", "bridge_ambush", "interrogation", "surround", "request", "robe_given", "vessel",
         "vessel2"}
QIN = {"mountain", "quote_big", "release", "charcoal", "market", "friend", "hard_path", "mech_signal", "seen",
       "mech_recip", "org", "zhibo", "final_words", "tears", "legend", "dawn", "takeaway", "taishigong", "mech_release"}


def place(buf, x, t, g=1.0):
    i = int(t * SR)
    if i >= len(buf) or i + len(x) <= 0:
        return
    if x.ndim == 1 and buf.ndim == 2:
        x = np.stack([x, x], 1)
    j = min(len(buf), i + len(x))
    buf[max(i, 0):j] += x[max(0, -i):j - i] * g


def shots_of(pred):
    return [s for s in TL["shots"] if pred(s)]


def intensity_curve():
    c = np.zeros(N, np.float32)
    for s in TL["shots"]:
        a, b = int(s["start"] * SR), int(s["end"] * SR)
        c[a:b] = INT.get(s["vis"], 0.4)
    # 平滑 2 秒
    k = int(1.5 * SR)
    cs = np.cumsum(np.r_[0, c])
    sm = (cs[k:] - cs[:-k]) / k
    c[k // 2:k // 2 + len(sm)] = sm
    return c


def silence_mask():
    """开场 1.85 秒前、三击后的静音一拍：音乐为 0。"""
    m = np.ones(N, np.float32)
    m[:int(1.8 * SR)] = 0
    st = TL["events"]["strikes"]
    fw = [L for L in TL["lines"] if L["id"] == "s5_11"][0]["start"]
    if st:
        a, b = int((st[-1] + 0.55) * SR), int((fw - 0.05) * SR)
        m[a:b] = 0
        r = int(0.12 * SR); m[a - r:a] *= np.linspace(1, 0, r)
    return m


CHORDS = [[38, 50, 57, 62, 65], [34, 46, 53, 58, 62], [36, 48, 55, 60, 64], [33, 45, 52, 57, 60]]  # Dm Bb C Am


def music():
    ic = intensity_curve()
    pad = np.zeros(N, np.float32)
    trem = np.zeros(N, np.float32)
    drone = np.zeros(N, np.float32)
    step = 4.0
    t = 1.8
    ci = 0
    while t < TL["total"] + 2:
        ch = CHORDS[ci % 4]
        I = float(ic[min(N - 1, int(t * SR))])
        for m in ch[1:]:
            x = S.string_note(S.midi(m), step + 2.0, bright=0.5 + I) * S.env_adsr(int((step + 2.0) * SR), 1.2, 0.5, 0.8, 1.6)
            place(pad, x, t, 0.22)
        x = S.string_note(S.midi(ch[0]), step + 2.0, bright=0.4) * S.env_adsr(int((step + 2.0) * SR), 1.0, 0.5, 0.9, 1.6)
        place(drone, x, t, 0.35)
        # 颤弓（紧张段）
        vis = [s["vis"] for s in TL["shots"] if s["start"] <= t < s["end"]]
        if vis and vis[0] in TENSE:
            for m in ch[2:]:
                n = int((step + 0.5) * SR)
                x = S.string_note(S.midi(m + 12), step + 0.5, bright=1.2) * (0.55 + 0.45 * np.sin(2 * np.pi * 9 * np.arange(n) / SR)) * S.env_adsr(n, 0.4, 0.2, 0.9, 0.6)
                place(trem, x, t, 0.12)
        t += step
        ci += 1
    pad = pad * (0.35 + 0.9 * ic)
    drone = drone * (0.5 + 0.6 * ic)
    # 鼓
    drums = np.zeros(N, np.float32)
    tk_big, tk_mid, rm = S.taiko(1.3, 2.2), S.taiko(0.9, 1.4), S.rim()
    for s in shots_of(lambda s: s["vis"] in DRUMS):
        I = INT[s["vis"]]
        bpm = 104 if s["vis"] in ("bridge_ambush", "surround", "request", "robe_given", "strike") else 86
        beat = 60 / bpm
        t = max(s["start"], 1.85)
        k = 0
        while t < s["end"] - 0.05:
            b = k % 8
            if s["vis"] == "strike":
                break
            if b in (0, 4):
                place(drums, tk_big, t, 0.9 * I)
            if b in (3, 6) and I > 0.6:
                place(drums, tk_mid, t, 0.6 * I)
            if b in (2, 7) and I > 0.7:
                place(drums, tk_mid, t + beat / 2, 0.45 * I)
            if b % 2 == 1:
                place(drums, rm, t, 0.25 * I)
            t += beat
            k += 1
    # 号角
    horn = np.zeros(N, np.float32)
    def horn_phrase(t0, notes=((50, 2.0), (57, 2.0), (62, 3.5)), g=0.25):
        tt = t0
        for m, d in notes:
            place(horn, S.horn_note(S.midi(m), d + 0.6), tt, g)
            place(horn, S.horn_note(S.midi(m - 12), d + 0.6), tt, g * 0.6)
            tt += d
    for vis in ("guoshi_title", "quote_big2", "surround", "robe_given"):
        for s in TL["shots"]:
            if s["vis"] == vis or s.get("key") == vis:
                horn_phrase(s["start"] + 0.2)
    m4 = [s for s in TL["shots"] if s["vis"] == "map"]
    if m4:
        horn_phrase(m4[0]["start"] + m4[0]["marks"][3], ((45, 2.0), (50, 2.5)), 0.22)
    tsg = [s for s in TL["shots"] if s["vis"] == "taishigong"][0]
    horn_phrase(tsg["start"] + tsg["marks"][1], ((50, 3.0), (57, 3.0), (62, 5.0)), 0.18)
    # 古琴
    qin = np.zeros(N, np.float32)
    rng = np.random.default_rng(5)
    scale = [50, 53, 55, 57, 60, 62, 65, 67]
    for s in shots_of(lambda s: s["vis"] in QIN or s.get("key") in QIN):
        t = s["start"] + 0.3
        while t < s["end"] - 1.0:
            m = int(rng.choice(scale))
            place(qin, S.guqin(S.midi(m), 3.0, slide=float(rng.choice([0, 0, 0.03, -0.02]))), t, 0.32)
            if rng.random() < 0.35:
                place(qin, S.guqin(S.midi(m - 12), 3.0), t, 0.2)
            t += float(rng.choice([1.2, 1.6, 2.4, 3.2]))
    mix = pad + drone + trem + drums * 0.9 + horn + qin
    # 三击：最高点
    for st in TL["events"]["strikes"]:
        place(mix, S.taiko(1.5, 2.5), st, 1.3)
        place(mix, S.boom(3.0), st, 0.6)
    for x, g in [(horn_phrase, 0)]:
        pass
    sts = TL["events"]["strikes"]
    if sts:
        for m in (50, 57, 62, 65):
            place(mix, S.string_note(S.midi(m), sts[-1] - sts[0] + 1.2, bright=1.6) * S.env_adsr(int((sts[-1] - sts[0] + 1.2) * SR), 0.3, 0.1, 1.0, 0.2), sts[0] - 0.5, 0.28)
    # 开场鼓
    place(mix, S.taiko(1.5, 2.5), 1.85, 1.2)
    place(mix, S.boom(3.5), 1.85, 0.5)
    mix *= silence_mask()
    # 结尾淡出
    e = int((TL["total"] - 3.0) * SR)
    mix[e:e + 3 * SR] *= np.linspace(1, 0, min(3 * SR, len(mix) - e))
    mix[e + 3 * SR:] = 0
    st = S.reverb(mix, 2.8, 0.32, seed=3)
    return st


def sfx():
    out = np.zeros((N, 2), np.float32)
    place(out, S.sword_ring(3.0), 0.0, 0.55)
    for t in TL["events"]["hook_strikes"]:
        place(out, S.whoosh(0.35), t - 0.12, 0.7)
        place(out, S.cloth_tear(0.35), t + 0.05, 0.6)
    hook = TL["shots"][0]
    e3 = hook["ends"][2]
    for t in (e3 - 1.3, e3 - 0.85, e3 - 0.4):
        place(out, S.whoosh(0.3), t - 0.08, 0.3)
    for t in TL["events"]["strikes"]:
        place(out, S.whoosh(0.5, 400, 5000), t - 0.25, 0.9)
        place(out, S.cloth_tear(0.5), t + 0.05, 0.9)
        place(out, S.sword_ring(1.5), t, 0.18)
    for s in TL["shots"]:
        a, b = s["start"], s["end"]; d = b - a
        v = s["vis"]
        if v in ("hook", "bridge_ambush", "surround", "request", "robe_given", "fallen", "dawn", "taishigong", "takeaway"):
            place(out, S.river(d) * np.minimum(1, np.minimum(np.arange(int(d * SR)) / SR, (d - np.arange(int(d * SR)) / SR)) / 0.4), a, 0.12)
        if v in ("charcoal_flash", "charcoal", "guoshi_title", "quote_big", "surround", "request", "palace"):
            place(out, S.fire(d), a, 0.12 if v != "charcoal" else 0.2)
        if v == "mountain":
            place(out, S.wind(d), a, 0.25)
        if v == "heart":
            t = a + 0.3
            while t < b - 0.3:
                place(out, S.heartbeat(), t, 0.9); t += 1.0
        if v in ("palace", "palace_flash"):
            t = a + 0.5
            while t < b - 0.6:
                place(out, S.scrape(0.6), t, 0.25); t += 1.4
        if v == "bridge_ambush":
            m1 = a + s["marks"][1]
            place(out, S.hooves(2.0), a + 0.3, 0.25)
            place(out, S.neigh(1.3), m1 - 0.1, 0.35)
            place(out, S.hooves(0.8, 12), m1, 0.4)
        if v == "legend":
            place(out, S.stamp(), a + 3.0, 0.6)
        if v == "arrest":
            place(out, S.whoosh(0.3, 300, 2000), a + 0.05, 0.4)
    return S.reverb(out[:, 0], 1.2, 0.18, seed=7) * 0.5 + out * 0.5


def voice():
    v = np.zeros(N, np.float32)
    for L in TL["lines"]:
        x, sr = sf.read(f"{WK}/tts/proc/{L['id']}.wav")
        place(v, x.astype(np.float32), L["start"])
    return v


def act_env(v):
    """旁白活动包络（0–1），起 80 ms、落 600 ms。"""
    a = np.abs(v)
    hop = 480
    m = a[:len(a) // hop * hop].reshape(-1, hop).max(1)
    on = (m > 0.02).astype(np.float32)
    e = np.zeros_like(on); cur = 0.0
    for i, x in enumerate(on):
        k = 0.6 if x > cur else 0.016
        cur += (x - cur) * k
        e[i] = cur
    e = np.repeat(e, hop)
    return np.pad(e, (0, len(v) - len(e)))


def main():
    meter = pyln.Meter(SR)
    v = voice()
    sf.write(f"{WK}/build/voice.wav", v, SR, subtype="PCM_24")
    m = music(); sf.write(f"{WK}/build/music_raw.wav", m, SR, subtype="FLOAT")
    fx = sfx(); sf.write(f"{WK}/build/sfx_raw.wav", fx, SR, subtype="FLOAT")
    vs = np.stack([v, v], 1)
    lv = meter.integrated_loudness(vs)
    env = act_env(v)[:, None]
    duck = 1 - 0.45 * env                      # 说话时再压约 5 dB
    speech = env[:, 0] > 0.5
    # 音乐：说话时比人声低约 21 dB
    lm_sp = meter.integrated_loudness((m * duck)[speech])
    gm = 10 ** ((lv - 21.0 - lm_sp) / 20)
    music_bed = m * duck * gm
    # 音效：说话时比人声低约 14 dB（开场和三击单独更响）
    lf = meter.integrated_loudness(fx[speech] + 1e-6)
    gf = 10 ** ((lv - 14.0 - lf) / 20)
    fxs = fx * gf * (1 - 0.3 * env)
    for name, mix in (("mix_full", vs + music_bed + fxs), ("mix_nomusic", vs + fxs)):
        sf.write(f"{WK}/build/{name}_pre.wav", mix, SR, subtype="FLOAT")
    # 报告
    rep = dict(voice_lufs=lv, music_vs_voice_speech_db=meter.integrated_loudness(music_bed[speech]) - lv,
               music_vs_voice_all_db=meter.integrated_loudness(music_bed) - lv,
               sfx_vs_voice_speech_db=meter.integrated_loudness(fxs[speech]) - lv)
    json.dump(rep, open(f"{WK}/build/mix_report.json", "w"), indent=1)
    print(rep)


if __name__ == "__main__":
    main()
