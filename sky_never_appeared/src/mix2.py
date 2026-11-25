"""Soundtrack v2, following the series music spec.

Layers (cold-war / suspense palette: low drone + sparse heartbeat drum):
  bed      title -> early chapter 2      drone only
  push     chapter 2 shield -> physics   + heartbeat drum + low pulse
  climax   Reykjavik                     clock + strings build -> full ensemble at the
                                         narration pause after k12 -> strings
  imagined cold open / ch.3 / ch.7       80s synth (cut back to reality on the white flash)
  ending                                 slowed synth theme -> one soft bell note, 2-3 s tail
Mix: music EQ -4 dB @ 3 kHz; sidechain ducking so music sits ~16 dB under speech and
recovers in pauses (attack 15 ms, release 500 ms); music fade in 2 s / out 3 s;
two-pass loudnorm to -16 LUFS, true peak -1.5 dBTP.

usage: python3 mix2.py <tts_dir> <out_dir>
writes  out_dir/mix.wav (final), out_dir/nomusic.wav (voice + effects, no music),
        out_dir/voice.wav, out_dir/music.wav (stems), out_dir/mix_report.json
"""
import os, sys, json, math, subprocess
import numpy as np
import soundfile as sf
from scipy import signal
import audio as A
import timeline as TL
import scene_sky as SKY
from common import SCRATCH

SR = A.SR
UNDER_VOICE_DB = -19.0        # ducking target; measured speech-to-music gap lands at ~16-17 dB


# ------------------------------------------------------------------ helpers
def peaking(x, f0, gain_db, q):
    a = 10 ** (gain_db / 40)
    w0 = 2 * math.pi * f0 / SR
    alpha = math.sin(w0) / (2 * q)
    b = [1 + alpha * a, -2 * math.cos(w0), 1 - alpha * a]
    den = [1 + alpha / a, -2 * math.cos(w0), 1 - alpha / a]
    return signal.lfilter(np.array(b) / den[0], np.array(den) / den[0], x, axis=0)


def env_follow(x, attack=0.015, release=0.5):
    """peak envelope with separate attack/release (like a compressor detector)."""
    e = np.abs(x).max(1) if x.ndim == 2 else np.abs(x)
    # decimate for speed, follow at 1 kHz
    hop = SR // 1000
    n = len(e) // hop
    e = e[:n * hop].reshape(n, hop).max(1)
    ga = math.exp(-1 / (attack * 1000)); gr = math.exp(-1 / (release * 1000))
    out = np.empty(n); s = 0.0
    for i, v in enumerate(e):
        s = ga * s + (1 - ga) * v if v > s else gr * s + (1 - gr) * v
        out[i] = s
    full = np.repeat(out, hop)
    if len(full) < len(x):
        full = np.concatenate([full, np.full(len(x) - len(full), full[-1] if len(full) else 0.0)])
    return full[:len(x)]


def short_rms_db(x, win=0.4):
    m = x.mean(1) if x.ndim == 2 else x
    k = A.secs(win)
    p = signal.fftconvolve(m ** 2, np.ones(k) / k, mode='same')
    return 10 * np.log10(np.maximum(p, 1e-12))


def duck_to(bus, vact, target_db):
    """while speaking, pull the bus down to target_db (short-term RMS); recover in pauses."""
    lvl = short_rms_db(bus)
    over = np.maximum(lvl - target_db, 0) * vact
    # smooth the gain change (attack 15 ms / release 500 ms behaviour comes from vact)
    over = signal.fftconvolve(over, np.ones(A.secs(0.05)) / A.secs(0.05), mode='same')
    return bus * (10 ** (-over / 20))[:, None]


def place(buf, x, t0, gain=1.0):
    A.place(buf, x, t0, gain)


def xfade_in(x, d):
    n = min(len(x), A.secs(d))
    x[:n] *= np.sin(np.linspace(0, math.pi / 2, n))[:, None] ** 2 if x.ndim == 2 else np.sin(np.linspace(0, math.pi / 2, n)) ** 2
    return x


def xfade_out(x, d):
    n = min(len(x), A.secs(d))
    x[-n:] *= np.cos(np.linspace(0, math.pi / 2, n))[:, None] ** 2 if x.ndim == 2 else np.cos(np.linspace(0, math.pi / 2, n)) ** 2
    return x


def seg(fn, t0, t1, fin=3.0, fout=3.0):
    """render a layer for [t0, t1] with crossfade tails (2-4 s overlap with neighbours)."""
    d = max(0.5, t1 - t0 + fout)
    x = A.stereo(fn(d))[:A.secs(d)]
    x = xfade_in(x.copy(), fin)
    x = xfade_out(x, fout)
    return x


def heartbeat(d, bpm=60, every=2, level=1.0):
    """sparse 'lub-dub' low drum."""
    n = A.secs(d)
    out = np.zeros(n)
    beat = 60.0 / bpm
    t = 0.0
    k = 0
    while t < d:
        if k % every == 0:
            for dt, amp in ((0.0, 1.0), (0.17, 0.6)):
                m = A.secs(0.35)
                tt = np.arange(m) / SR
                x = A.sine(42 + 28 * np.exp(-tt / 0.05), m) * np.exp(-tt / 0.12) * amp
                x += A.lp(A.noise(m), 180) * np.exp(-tt / 0.03) * 0.25 * amp
                i = A.secs(t + dt)
                out[i:i + m] += x[:max(0, min(m, n - i))]
        t += beat
        k += 1
    return A.reverb(out * level, 1.8, 0.25)


def low_pulse(d, bpm=76, root='D2'):
    n = A.secs(d)
    out = np.zeros(n)
    beat = 60.0 / bpm / 2
    f = A.midi(A.nm(root))
    t = 0.0
    while t < d:
        m = A.secs(beat * 0.9)
        x = A.lp(A.saw(f, m), 260) * A.perc(m, 0.004, 0.18)
        i = A.secs(t)
        out[i:i + m] += x[:max(0, min(m, n - i))]
        t += beat
    return A.stereo(out * 0.6)


def ensemble_swell(d, peak_at):
    """full ensemble for the climax: low strings + brass-like swell + timpani hits."""
    n = A.secs(d)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    # strings: D minor, two octaves, slow swell to peak then long decay
    chord = [38, 45, 50, 53, 57, 62]
    s = A.pad(chord, d, detune=0.1, cutoff=2200, attack=0.1, release=0.2, vib=0.8)
    env = np.clip(t / peak_at, 0, 1) ** 2 * (t <= peak_at) + np.exp(-(t - peak_at) / 3.5) * (t > peak_at)
    out += s * env[:, None] * 1.6
    # brass-like: saw stack, low-mid, filtered, entering on the peak
    b = np.zeros(n)
    for m_ in (50, 57, 62):
        b += A.saw(A.midi(m_), n) + A.saw(A.midi(m_) * 1.004, n)
    b = A.lp(b, 1400) * (np.clip((t - (peak_at - 1.2)) / 1.2, 0, 1) * np.exp(-np.maximum(t - peak_at, 0) / 2.5))
    out += A.stereo(b) * 0.22
    # timpani-like hits on the peak
    for k, dt in enumerate((0.0, 0.42, 0.84)):
        m = A.secs(2.5)
        tt = np.arange(m) / SR
        x = A.sine(62 * (1 + 0.15 * np.exp(-tt / 0.08)), m) * np.exp(-tt / (0.9 if k == 0 else 0.5)) * (1.0 if k == 0 else 0.55)
        x += A.lp(A.noise(m), 400) * np.exp(-tt / 0.06) * 0.4
        place(out, A.reverb(x, 2.5, 0.3) * 1.1, peak_at + dt)
    # cymbal swell into the peak
    place(out, A.reverse_swell(1.6) * 0.8, peak_at - 1.6)
    return A.reverb(out, 3.2, 0.25)


def bell(d=4.0, note='D5'):
    n = A.secs(d)
    t = np.arange(n) / SR
    f = A.midi(A.nm(note))
    x = (A.sine(f, n) + 0.35 * A.sine(f * 2.01, n) + 0.12 * A.sine(f * 3.02, n)) * np.exp(-t / 1.4)
    return A.reverb(x * 0.6, 3.5, 0.45)


# ------------------------------------------------------------------ build
def build(tts_dir):
    tl = TL.build(tts_dir)
    total = tl['total']
    cue = tl['cues']
    sec = {s['sec']: s for s in tl['sections']}
    n = A.secs(total) + SR
    voice = np.zeros((n, 2)); music = np.zeros((n, 2)); sfx = np.zeros((n, 2))
    at = cue.get

    # ---- voice bus: narration (-18 dBFS RMS per line) + Reagan originals at the same level
    for ln in tl['lines']:
        w, sr = sf.read(os.path.join(tts_dir, ln['id'] + '.wav'))
        place(voice, A.voice_place(w, sr), ln['start'])
    for c in tl['clips']:
        w, sr = sf.read(os.path.join(SCRATCH, 'reagan', c['id'].lower() + '.wav'))
        w = w.mean(1) if w.ndim == 2 else w
        if sr != SR:
            w = signal.resample_poly(w, SR, sr)
        place(voice, A.to_rms(A.bp(w, 160, 6500), -18.0), c['start'])
    voice = A.to_rms(voice, -18.0)

    # ---- music layers. Each layer is pre-normalised to a reference loudness and then
    # given a 'free' level (dBFS RMS when no one is speaking).
    free = []                                   # (t0, t1, free_level_db)
    def put(x, t0, t1, level_db):
        x = A.to_rms(x, level_db)
        place(music, x, t0)
        free.append((t0, t1, level_db))

    freeze = 12.70
    title_t = at('TITLE_START')
    # cold open (imagined): synth theme in, fade-in 2 s, then held pad under the narration
    th = A.synth_theme(freeze + 1.2, bpm=104, intensity=1.0, drums=True, arp=True)
    th[:len(A.lead_line(freeze))] += A.lead_line(freeze) * 0.8
    th = xfade_in(th[:A.secs(freeze + 0.6)].copy(), 2.0)
    th = xfade_out(th, 0.9)
    put(th, 0.0, freeze + 0.6, -17.0)
    padlen = title_t - freeze + 0.3
    pad = A.reverb(A.pad([57, 64, 71, 72], padlen + 2.0, cutoff=1600, attack=0.6, release=1.5), 3.0, 0.4)
    pad = A.tape_stop(pad[:A.secs(padlen)], 0.45)          # the synth cuts on the white flash
    put(pad, freeze, title_t + 0.3, -24.0)
    # bed: drone from the title to the shield moment (chapter 2)
    t_push = at('SHIELD')
    put(seg(lambda d: A.drone(d, root='E1'), title_t, t_push, fin=2.0, fout=3.0), title_t, t_push + 3, -27.0)
    # push: drone + heartbeat + low pulse until the Reykjavik section, except the imagined insert
    t_boost, t_nev = at('BOOST'), at('NEVADA')
    t_rk = sec['reykjavik']['start']
    def push_layer(d):
        x = A.stereo(A.drone(d, root='D1')) * 0.8
        hb = A.stereo(heartbeat(d, bpm=60, every=2))
        lp_ = low_pulse(d, bpm=76)
        L = min(len(x), len(hb), len(lp_))
        return x[:L] + hb[:L] * 0.9 + lp_[:L] * 0.35
    put(seg(push_layer, t_push - 1.5, t_boost, fin=3.0, fout=2.0), t_push - 1.5, t_boost, -25.0)
    # imagined insert (ch.3): synth, cut with tape stop at the reality flash
    syn = A.synth_theme(t_nev - t_boost + 0.8, bpm=104, intensity=0.6, drums=False, arp=True, dark=0.15, seed=1)
    syn = A.tape_stop(xfade_in(syn[:A.secs(t_nev - t_boost)].copy(), 1.0), 0.35)
    put(syn, t_boost - 0.3, t_nev - 0.25, -23.0)
    put(seg(push_layer, t_nev - 0.3, t_rk, fin=2.0, fout=3.0), t_nev - 0.3, t_rk, -24.5)
    # climax: clock + strings build through Reykjavik, full ensemble on the pause after k12
    t_cl = at('CLIMAX')
    t_build0 = at('HOUSE') - 0.5
    rk_end = sec['reykjavik']['end']
    def rk_layer(d):
        L = A.secs(d)
        ck = A.stereo(A.clock(d, 1.0, 0.5))[:L]
        st = A.strings([50, 57, 62, 65], d, 0.5)[:L]
        ramp = np.clip((np.arange(L) / SR) / max(1.0, t_cl - t_build0), 0, 1)[:, None]
        return ck + st * (0.6 + 0.8 * ramp)
    put(seg(rk_layer, t_build0, rk_end, fin=3.0, fout=3.0), t_build0, t_cl - 3.0, -25.0)
    sw = ensemble_swell(9.0, peak_at=3.2)
    put(sw, t_cl - 3.2, t_cl + 1.6, -14.0)                  # music alone for 1.6 s
    # imagined Soviet station (ch.7) then reality: low drone
    t_su, t_launch = at('HYPO_SU'), at('LAUNCH')
    syn2 = A.synth_theme(t_launch - t_su + 0.8, bpm=96, intensity=0.55, drums=False, arp=True, dark=0.6, seed=2)
    syn2 = A.tape_stop(xfade_in(syn2[:A.secs(t_launch - t_su)].copy(), 1.0), 0.35)
    put(syn2, t_su - 0.3, t_launch - 0.25, -24.0)
    t_myth = sec['myth']['start']
    put(seg(lambda d: A.drone(d, root='C1'), t_launch - 0.3, t_myth, fin=2.0, fout=3.0), t_launch - 0.3, t_myth, -26.0)
    # myth: reflective strings, no drums
    t_end = sec['end']['start']
    put(seg(lambda d: A.strings([50, 57, 62, 65, 69], d, 0.6), t_myth - 1.0, t_end, fin=3.0, fout=3.0), t_myth - 1.0, t_end, -27.0)
    # ending: slowed, darker synth theme -> one bell note -> 2-3 s tail -> black
    t_last = tl['lines'][-1]['start'] + tl['lines'][-1]['dur']
    slow = A.synth_theme(t_last - t_end + 3.0, bpm=72, intensity=0.6, drums=False, arp=True, dark=0.7, octave_shift=-1)
    slow = xfade_out(xfade_in(slow.copy(), 3.0), 3.0)
    put(slow, t_end - 1.0, t_last + 2.0, -24.0)
    put(bell(5.0), t_last + 0.3, total, -26.0)

    # ---- effects
    for kt, si, mi in SKY.KILLS:
        place(sfx, A.pan(A.zap(0.4)[:, 0], -0.4 + 0.4 * si) * 0.35, kt - 0.45)
        place(sfx, A.boom(1.6, 0.6) * 0.18, kt)
    place(sfx, A.reverse_swell(1.6) * 0.6, SKY.XRAY_T - 1.6)
    place(sfx, A.impact(3.5) * 0.85, SKY.XRAY_T)
    place(sfx, A.impact(4.0) * 0.9, title_t)
    if at('LETTER'):
        times = list(np.cumsum(np.random.default_rng(3).uniform(0.06, 0.16, 40)) + at('LETTER') + 0.4)
        place(sfx, A.typewriter(times) * 0.35, 0.0)
    if t_nev:
        place(sfx, A.impact(2.5) * 0.5, t_nev - 0.25)
        place(sfx, A.rumble(7.0) * 0.4, t_nev + 1.0)
        place(sfx, A.boom(3.0, 1.3) * 0.8, t_nev + 4.55)
    if at('HIT'):
        place(sfx, A.impact(3.0) * 0.6, at('HIT') + 3.25)
    if at('LAB'):
        place(sfx, A.crack(1.5) * 0.8, at('LAB') + 1.15)
    if t_launch:
        place(sfx, A.impact(2.5) * 0.5, t_launch - 0.25)
        place(sfx, A.rumble(9.0) * 0.7, t_launch)
    if at('TUMBLE'):
        place(sfx, A.descending_tone(7.5) * 0.6, at('TUMBLE') + 0.75)
    if at('FALL'):
        place(sfx, A.lp(A.whoosh(2.5, up=False), 2500) * 0.4, at('FALL') + 0.2)
    sfx = A.to_rms(sfx, -26.0)

    # ---- music processing: EQ, ducking, fades
    music = peaking(music, 3000, -4.0, 1.0)
    venv = env_follow(voice, 0.015, 0.5)                    # attack 15 ms, release 500 ms
    vact = np.clip(venv / 0.03, 0, 1)                       # 0 = silent, 1 = speaking
    target_under = -18.0 + UNDER_VOICE_DB                   # voice sits at -18 dBFS RMS
    music = duck_to(music, vact, target_under)
    sfx = duck_to(sfx, vact, target_under - 2.0)
    music = xfade_in(music, 2.0)
    music[A.secs(total - 3.0):] *= np.linspace(1, 0, len(music) - A.secs(total - 3.0))[:, None]
    voice, music, sfx = voice[:A.secs(total)], music[:A.secs(total)], sfx[:A.secs(total)]
    return tl, voice, music, sfx


def speech_vs_music(voice, music, vact_thr=0.5):
    """median of (voice dB - music dB) over 400 ms windows where narration is present."""
    hop = A.secs(0.4)
    diffs = []
    for i in range(0, len(voice) - hop, hop):
        v = voice[i:i + hop]; m = music[i:i + hop]
        vr = np.sqrt(np.mean(v ** 2)); mr = np.sqrt(np.mean(m ** 2))
        if vr > 10 ** (-30 / 20) and mr > 1e-6:
            diffs.append(20 * np.log10(vr / mr))
    d = np.array(diffs)
    return float(np.median(d)), float(np.percentile(d, 10)), len(d)


def loudnorm(inp, out, I=-16.0, TP=-1.5, LRA=11.0):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', inp, '-af',
                        f'loudnorm=I={I}:TP={TP}:LRA={LRA}:print_format=json', '-f', 'null', '-'],
                       capture_output=True, text=True)
    txt = r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1]
    m = json.loads(txt)
    af = (f"loudnorm=I={I}:TP={TP}:LRA={LRA}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', inp, '-af', af, '-ar', '48000', out], check=True)
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', out, '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                       capture_output=True, text=True)
    s = r.stderr
    I_out = float(s[s.rindex('I:'):].split()[1])
    tp = float(s[s.rindex('Peak:'):].split()[1])
    return {'measured_in': m, 'I': I_out, 'true_peak': tp}


def main():
    tts_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    tl, voice, music, sfx = build(tts_dir)
    med, p10, nwin = speech_vs_music(voice, music + sfx)
    sf.write(os.path.join(out_dir, 'voice.wav'), voice.astype(np.float32), SR)
    sf.write(os.path.join(out_dir, 'music.wav'), music.astype(np.float32), SR)
    pre = voice + music + sfx
    sf.write(os.path.join(out_dir, 'pre_mix.wav'), pre.astype(np.float32), SR)
    sf.write(os.path.join(out_dir, 'pre_nomusic.wav'), (voice + sfx).astype(np.float32), SR)
    rep = {'speech_minus_music_db_median': round(med, 1), 'speech_minus_music_db_p10': round(p10, 1),
           'windows': nwin, 'total_s': round(tl['total'], 2)}
    rep['mix'] = loudnorm(os.path.join(out_dir, 'pre_mix.wav'), os.path.join(out_dir, 'mix.wav'))
    rep['nomusic'] = loudnorm(os.path.join(out_dir, 'pre_nomusic.wav'), os.path.join(out_dir, 'nomusic.wav'))
    json.dump(tl, open(os.path.join(out_dir, 'timeline.json'), 'w'), ensure_ascii=False)
    json.dump(rep, open(os.path.join(out_dir, 'mix_report.json'), 'w'), indent=1, default=str)
    print(json.dumps({k: v for k, v in rep.items() if k not in ('mix', 'nomusic')}, ensure_ascii=False))
    print('mix', rep['mix']['I'], 'LUFS', rep['mix']['true_peak'], 'dBTP;', 'nomusic', rep['nomusic']['I'], rep['nomusic']['true_peak'])


if __name__ == '__main__':
    main()
