"""Builds the full soundtrack (narration + Reagan clips + score + sfx) from the timeline.

usage: python3 mix.py <tts_dir> <out.wav> [t0 t1]
"""
import os, sys, json, math
import numpy as np
import soundfile as sf
import audio as A
import timeline as TL
import scene_sky as SKY
from common import SCRATCH

SR = A.SR


def load_wav(path):
    w, sr = sf.read(path)
    if w.ndim == 2:
        w = w.mean(1)
    return w, sr


def build(tts_dir, t0=0.0, t1=None):
    tl = TL.build(tts_dir)
    total = tl['total'] if t1 is None else t1
    n = A.secs(total) + A.SR
    voice = np.zeros((n, 2))
    music = np.zeros((n, 2))
    sfx = np.zeros((n, 2))
    cue = tl['cues']
    sec = {s['sec']: s for s in tl['sections']}

    # ---------------- narration
    for ln in tl['lines']:
        if ln['start'] > total:
            continue
        w, sr = load_wav(os.path.join(tts_dir, ln['id'] + '.wav'))
        v = A.voice_chain(w, sr)
        A.place(voice, A.norm(v, 0.85), ln['start'])
    # ---------------- Reagan clips (WHCA recording, public domain)
    for c in tl['clips']:
        if c['start'] > total:
            continue
        w, sr = load_wav(os.path.join(SCRATCH, 'reagan', c['id'].lower() + '.wav'))
        if sr != SR:
            from scipy.signal import resample_poly
            w = resample_poly(w, SR, sr)
        w = A.bp(w, 160, 6500)
        A.place(voice, A.norm(w, 0.8), c['start'])

    # ---------------- score
    title_t = cue.get('TITLE_START', 40.0)
    freeze = 12.70
    # cold open synth theme: fade in, full drums, cut hard at the white flash
    theme = A.synth_theme(freeze + 1.0, bpm=104, intensity=1.0, drums=True, arp=True, dark=0.0)
    theme[:A.secs(1.2)] *= np.linspace(0, 1, A.secs(1.2))[:, None]
    lead = A.lead_line(freeze, bpm=104)
    theme[:len(lead)] += lead * 0.8
    A.place(music, theme[:A.secs(freeze + 0.15)] * 0.75, 0.0)
    # freeze: suspended pad under narration until the title flash
    padlen = title_t - freeze + 0.2
    pad = A.pad([57, 64, 71, 72], padlen + 2.0, cutoff=1600, attack=0.6, release=1.5) * 0.9
    pad = A.reverb(pad, 3.0, 0.4)
    pad = A.tape_stop(pad[:A.secs(padlen)], 0.45)
    A.place(music, pad * 0.55, freeze)
    # title: impact + cold drone begins
    A.place(sfx, A.impact(4.0) * 0.9, title_t)
    # reality drone through the rest of the film (sections add their own colour)
    reality_end = sec['end']['start']
    dr = A.drone(reality_end - title_t + 3.0, root='E1')
    dr[:A.secs(2.0)] *= np.linspace(0, 1, A.secs(2.0))[:, None]
    A.place(music, dr * 0.45, title_t + 0.5)

    # ---------------- cold-open sfx
    for kt, si, mi in SKY.KILLS:
        A.place(sfx, A.pan(A.zap(0.4)[:, 0], -0.4 + 0.4 * si) * 0.35, kt - 0.45)
        A.place(sfx, A.boom(1.6, 0.6) * 0.18, kt)
    A.place(sfx, A.reverse_swell(1.6) * 0.6, SKY.XRAY_T - 1.6)
    A.place(sfx, A.impact(3.5) * 0.85, SKY.XRAY_T)
    for k in range(10):
        A.place(sfx, A.boom(1.2, 0.5) * 0.08, SKY.XRAY_T + 0.06 + 0.035 * k)

    # ---------------- per-section colour (cue based)
    def at(tag):
        return cue.get(tag)
    if at('LETTER'):
        times = list(np.cumsum(np.random.default_rng(3).uniform(0.06, 0.16, 40)) + at('LETTER') + 0.4)
        A.place(sfx, A.typewriter(times) * 0.35, 0.0)
    if at('NEVADA'):
        A.place(sfx, A.rumble(7.0) * 0.5, at('NEVADA') + 1.0)
    if at('HIT'):
        A.place(sfx, A.impact(3.0) * 0.6, at('HIT') + 2.0)
    if at('LAB'):
        A.place(sfx, A.crack(1.5) * 0.8, at('LAB') + 1.0)
    if at('HOUSE'):
        clk = A.clock(sec['reykjavik']['end'] - at('HOUSE'), 1.0, 0.35)
        A.place(music, clk, at('HOUSE'))
        A.place(music, A.strings([50, 57, 62, 65], sec['reykjavik']['end'] - at('HOUSE'), 0.5), at('HOUSE'))
    if at('TUMBLE'):
        A.place(sfx, A.descending_tone(8.0) * 0.6, at('TUMBLE') + 2.0)
    if at('LAUNCH'):
        A.place(sfx, A.rumble(9.0) * 0.7, at('LAUNCH'))
    if at('REPLAY'):
        end_t = sec['end']['start']
        slow = A.synth_theme(sec['end']['end'] - end_t + 2, bpm=72, intensity=0.6, drums=False, arp=True, dark=0.7,
                             octave_shift=-1)
        L = len(slow)
        slow *= np.clip(np.linspace(1.4, -0.2, L), 0, 1)[:, None]
        A.place(music, slow * 0.6, end_t)

    # ---------------- duck + master
    g = A.duck_curve(voice, depth_db=11)
    mix = voice + music * g[:, None] * 0.9 + sfx * (0.55 + 0.45 * g[:, None])
    i0, i1 = A.secs(t0), A.secs(total)
    mix = mix[i0:i1]
    return A.master(mix, 0.95)


if __name__ == '__main__':
    tts_dir, out = sys.argv[1], sys.argv[2]
    t0 = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    t1 = float(sys.argv[4]) if len(sys.argv) > 4 else None
    m = build(tts_dir, t0, t1)
    sf.write(out, m.astype(np.float32), SR)
    print('wrote', out, round(len(m) / SR, 2), 's')
