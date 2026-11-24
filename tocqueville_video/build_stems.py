"""Build voice and SFX stems on the render timeline (timeline.json). Music is a separate stem (see music spec).
Outputs /tmp/claude-0/work/stems/{voice,sfx}.wav (48 kHz) and voice_activity.npy for side-chaining.
"""
import sys, os, json
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mixlib import SR, load, place
import sfx

WORK = "/tmp/claude-0/work"
PROC = f"{WORK}/tts/proc"
OUT = f"{WORK}/stems"


def reverb(x, rt=1.4, mix=0.25, seed=0):
    rng = np.random.default_rng(seed)
    n = int(rt * SR)
    t = np.arange(n) / SR
    ir = rng.normal(size=n) * np.exp(-6.9 * t / rt)
    ir = sfx.lp(ir, 5000)
    ir /= np.sqrt((ir ** 2).sum())
    from scipy.signal import fftconvolve
    wet = fftconvolve(x, ir)
    out = np.zeros(len(wet), np.float32)
    out[:len(x)] += x * (1 - mix)
    out += wet.astype(np.float32) * mix
    return out


def main():
    tl = json.load(open(f"{WORK}/timeline.json"))
    total = tl["total"]
    N = int(total * SR) + SR
    voice = np.zeros(N, np.float32)
    fx = np.zeros(N, np.float32)
    C = {}
    for s in tl["scenes"]:
        for ln in s["lines"]:
            x = load(f"{PROC}/{ln['id']}.wav")
            place(voice, x, ln["start"])
            C[ln["id"]] = (ln["start"], ln["end"])
            if ln.get("cue"):
                C.setdefault(ln["cue"], (ln["start"], ln["end"]))
    S = {s["id"]: (s["start"], s["end"]) for s in tl["scenes"]}

    def span(sid):
        a, b = S[sid]
        return a, b - a

    # page turns at scene changes
    for s in tl["scenes"][1:]:
        place(fx, sfx.page_turn(seed=int(s["start"] * 10) % 97, level=-34), s["start"] - 0.4)

    # s00: sea, then map (quill), then road ambience
    a, d = span("s00")
    m0 = C["map_route"][0]
    place(fx, sfx.waves(m0 - a + 1.5, level=-31), a)
    place(fx, sfx.wind(m0 - a + 1.5, seed=3, level=-46, bright=900), a)
    place(fx, sfx.quill(C["s00_07"][0] - m0, level=-42), m0 + 0.3)
    r0 = C["s00_07"][0]
    place(fx, sfx.birds(S["s00"][1] - r0 + 1, seed=4, level=-46, n_chirps=4), r0)
    place(fx, sfx.wind(S["s00"][1] - r0 + 1, seed=5, level=-46), r0)

    # s01: cold room tone, harbour waves at the quay, footsteps in the prison
    a, d = span("s01")
    place(fx, sfx.wind(d, seed=6, level=-48, bright=400), a)
    place(fx, sfx.waves(C["prison_corridor"][0] - C["two_judges"][0], seed=7, level=-38), C["two_judges"][0])
    place(fx, sfx.hooves(9.0, seed=8, level=-40, rate=0.9), C["prison_corridor"][0] + 0.2)

    # s02: countryside; creak + crash; murmur; saw; cart; children
    a, d = span("s02")
    place(fx, sfx.wind(d, seed=9, level=-45), a)
    place(fx, sfx.birds(d, seed=10, level=-46, n_chirps=8), a)
    tf = C["tree_falls"][0]
    place(fx, sfx.creak(1.6, level=-32), tf + 2.4)
    place(fx, sfx.crash(level=-22), tf + 3.2 + 1.2)
    ng = C["neighbors_gather"]
    place(fx, sfx.murmur(ng[1] - ng[0] + 2.0, seed=11, level=-38), ng[0] - 0.2)
    sc = C["saw_clear"][0]
    place(fx, sfx.saw(2.8, level=-30), sc)
    place(fx, sfx.crash(seed=20, level=-32), sc + 2.7)
    place(fx, sfx.hooves(4.0, seed=12, level=-36), sc + 3.4)
    pg = C["playground"][0]
    place(fx, sfx.murmur(S["s02"][1] - pg, seed=13, level=-42, voices=9), pg)

    # s03: town birds; hall room tone + murmur; rustle of raised hands; chalk
    a, d = span("s03")
    mh = C["meeting_hall"][0]
    place(fx, sfx.birds(mh - a, seed=14, level=-46, n_chirps=4), a)
    ex = C["excluded"][0]
    place(fx, sfx.hall_room(ex - mh, level=-44), mh)
    place(fx, sfx.murmur(ex - mh, seed=15, level=-44, voices=10), mh)
    place(fx, sfx.rustle(1.6, level=-32), C["hands_up"][0] + 0.2)
    place(fx, sfx.quill(5.0, seed=16, level=-38), C["s03_13"][0])

    # s04: murmur of the gathering crowd; letters like snow
    place(fx, sfx.murmur(6.0, seed=17, level=-42, voices=12), C["dots_gather"][0])
    lf = C["letters_fly"][0]
    place(fx, sfx.paper_flutter(C["split_both"][0] - lf + 2.0, seed=18, level=-36, density=26), lf)

    # s05: forest, hooves, cabin
    a, d = span("s05")
    ce = C["cabin_ext"][0]
    place(fx, sfx.wind(d, seed=19, level=-44), a)
    place(fx, sfx.birds(ce - a + 4, seed=20, level=-44, n_chirps=6), a)
    place(fx, sfx.hooves(ce - a, seed=21, level=-36, rate=1.4), a + 0.5)
    place(fx, sfx.page_turn(seed=22, level=-30), C["shakespeare"][0] + 0.3)

    # s06: waves + quill (compact), block thuds, gears, hammering
    mf = C["mayflower"][0]
    place(fx, sfx.waves(6.0, seed=23, level=-36), mf - 0.5)
    place(fx, sfx.quill(4.0, seed=24, level=-38), mf + 1.0)
    pu = C["pyramid_up"][0]
    for k in range(4):
        place(fx, sfx.hooves(0.5, seed=25 + k, level=-34, rate=4), pu + k * 1.25 + 0.2)
    if "s06_07" in C:  # gears (cut in the 14-min version)
        g0 = C["s06_07"][0]
        clicks = np.zeros(int(8 * SR), np.float32)
        for k in range(int(8 * 3)):
            i = int(k / 3 * SR)
            L = int(0.01 * SR)
            clicks[i:i + L] += np.random.default_rng(k).normal(size=L) * np.exp(-np.arange(L) / 60)
        place(fx, sfx.norm(sfx.bp(clicks, 1500, 6000), -40), g0)
    place(fx, sfx.hooves(6.0, seed=29, level=-36, rate=1.1), C["layer3"][0] + 0.5)

    # s07: archive candle/paper; quill route; calendar flips
    a, d = span("s07")
    place(fx, sfx.paper_flutter(3.0, seed=30, level=-42, density=6), a + 0.5)
    pr = C["paper_route"][0]
    place(fx, sfx.quill(6.0, seed=31, level=-40), pr)
    cal = C["calendar"][0]
    for k in range(3):
        place(fx, sfx.page_turn(seed=32 + k, level=-30), cal + k * 1.6)

    # s08: crowd murmur that stops when backs are turned
    a, d = span("s08")
    tb = C["turn_backs"][0]
    place(fx, sfx.murmur(tb - a + 1.0, seed=33, level=-44, voices=10), a)
    place(fx, sfx.wind(d, seed=34, level=-50, bright=350), a)

    # s09 Memphis: ONLY wind, ice, and one howl
    a, d = span("s09")
    place(fx, sfx.wind(d + 2, seed=35, level=-36, bright=700), a)
    place(fx, sfx.ice(d, seed=36, level=-38, n_hits=int(d / 4)), a)
    hw = C["dogs_howl"][0]
    howl = reverb(sfx.howl(5.5, level=-20), rt=2.2, mix=0.35)
    place(fx, howl, hw + 0.4)

    # s10: departure waves; quiet ending
    sl = C["ship_leave"][0]
    place(fx, sfx.waves(C["books"][0] - sl + 1.0, seed=37, level=-34), sl - 0.6)

    os.makedirs(OUT, exist_ok=True)
    sf.write(f"{OUT}/voice.wav", voice, SR, subtype="FLOAT")
    sf.write(f"{OUT}/sfx.wav", fx, SR, subtype="FLOAT")
    print("stems", total, "s")


if __name__ == "__main__":
    main()
