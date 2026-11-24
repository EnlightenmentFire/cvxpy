"""Builds the master timeline from narration durations.

Produces absolute times for every narration line, subtitle chunk, English clip,
section boundary and cue tag. Pure data; no rendering here.
"""
import os, re, json
import script_data as S
from common import SCRATCH

COLD_OPEN_SILENT = 13.4      # imagined sky runs before the first word
TITLE_HOLD = 4.2             # title card after o4
CHAPTER_GAP = 1.6            # breath + chapter card between sections
EN_GAP = 0.35
END_TAIL = 6.0

SUB_MAX = 17                 # max characters per subtitle line


def _split_long(tk, limit):
    """split an over-long token at the word boundary nearest its middle (jieba)."""
    import sys
    lib = os.path.join(SCRATCH, 'pylib')
    if lib not in sys.path:
        sys.path.append(lib)
    import jieba
    jieba.setLogLevel(60)
    words = list(jieba.cut(tk))
    if len(words) < 2:
        k = len(tk) // 2
        return [tk[:k], tk[k:]]
    best, pos, acc = None, 0, 0
    for w in words[:-1]:
        acc += len(w)
        score = abs(acc - len(tk) / 2)
        if best is None or score < best:
            best, pos = score, acc
    return [tk[:pos], tk[pos:]]


def split_chunks(text, limit=16):
    """greedy subtitle chunks: split at punctuation, never across a sentence end or a dash."""
    text = text.replace('——', '‖')
    toks = [x for x in re.split(r'(?<=[，。；：？！、‖])(?![”’])|(?<=[。？！][”’])', text) if x and x.strip()]
    fixed = []
    stack = list(toks)
    while stack:
        tk = stack.pop(0)
        if len(clean_sub(tk)) > limit + 1:
            a, b = _split_long(tk, limit)
            stack[0:0] = [a + '‖', b] if not a.endswith(('，', '‖')) else [a, b]
            continue
        fixed.append(tk)
    out, cur = [], ''
    for tk in fixed:
        if cur and (len(clean_sub(cur + tk)) > limit or cur.rstrip()[-1:] in '。？！‖' or cur.rstrip()[-2:] in ('。”', '？”', '！”')):
            out.append(cur); cur = ''
        cur += tk
    if cur:
        out.append(cur)
    return [clean_sub(c) for c in out if clean_sub(c)]


def clean_sub(c):
    c = c.strip()
    c = c.replace('‖', '').replace('。”', '”').replace('。’', '’')
    c = re.sub(r'[，。；：、]+$', '', c)
    c = c.replace('——', ' ')
    return c


def weight(s):
    return max(1, len(re.sub(r'[，。；：？！“”‘’《》、\s]', '', s)))


def build(meta_dir):
    mp = os.path.join(meta_dir, 'meta.json')
    meta = {m['id']: m['dur'] for m in json.load(open(mp))} if os.path.exists(mp) else {}
    for ln in S.all_lines():
        lid = ln[2]
        if lid not in meta:
            wav = os.path.join(meta_dir, lid + '.wav')
            if os.path.exists(wav):
                import soundfile as _sf
                info = _sf.info(wav)
                meta[lid] = info.frames / info.samplerate
            else:
                meta[lid] = len(re.sub(r'[^\u4e00-\u9fff]', '', ln[3])) / 4.2
    en_dur = {'EN1': 16.95, 'EN2': 5.9}
    t = 0.0
    lines, subs, clips, sections, cues = [], [], [], [], {}
    for si, (sec, chapter, items) in enumerate(S.SECTIONS):
        if si == 0:
            t = COLD_OPEN_SILENT
        else:
            t += CHAPTER_GAP
        sec_start = t if si else 0.0
        for lid, text, pause, tags in items:
            d = meta[lid]
            lines.append({'id': lid, 'sec': sec, 'start': t, 'dur': d, 'text': text, 'tags': tags})
            for tg in tags.split(','):
                if tg:
                    cues[tg] = t
            cues[lid] = t
            ch = split_chunks(text)
            wts = [weight(c) for c in ch]
            tot = sum(wts)
            tc = t
            for c, wgt in zip(ch, wts):
                dd = d * wgt / tot
                subs.append({'start': tc, 'end': tc + dd, 'text': c})
                tc += dd
            t += d + pause
            for k in ('EN1', 'EN2'):
                if k in tags:
                    t += EN_GAP
                    clips.append({'id': k, 'start': t, 'dur': en_dur[k]})
                    zh = S.EN_CLIPS[k]['zh']
                    wts = [weight(z) for z in zh]
                    tot = sum(wts)
                    tc = t
                    for z, wgt in zip(zh, wts):
                        dd = en_dur[k] * wgt / tot
                        subs.append({'start': tc, 'end': tc + dd, 'text': z, 'en': True})
                        tc += dd
                    cues[k + '_end'] = t + en_dur[k]
                    t += en_dur[k] + 0.5
            if 'TITLE' in tags:
                cues['TITLE_START'] = t
                t += TITLE_HOLD
        sections.append({'sec': sec, 'chapter': chapter, 'start': sec_start, 'end': t, 'index': si})
    total = t + END_TAIL
    sections[-1]['end'] = total
    return {'lines': lines, 'subs': subs, 'clips': clips, 'sections': sections, 'cues': cues, 'total': total}


if __name__ == '__main__':
    import sys
    md = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SCRATCH, 'tts', 'full', 'zm_098')
    tl = build(md)
    for s in tl['sections']:
        print(f"{s['sec']:10s} {s['start']:7.1f} {s['end']:7.1f} {s['end'] - s['start']:6.1f}")
    print('total', round(tl['total'], 1), 's =', round(tl['total'] / 60, 2), 'min;', len(tl['subs']), 'subtitle chunks')
    print(max(len(s['text']) for s in tl['subs']), 'max chunk chars')
