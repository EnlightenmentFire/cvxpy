"""Whisper sanity check of every narration line: flags dropped/garbled words (pinyin-level similarity)."""
import sys, json, re, difflib, whisper
from pypinyin import lazy_pinyin
man = json.load(open(sys.argv[1]))
m = whisper.load_model(sys.argv[2] if len(sys.argv) > 2 else 'small')
import cn2an
def norm(s):
    s = re.sub(r'\d+(\.\d+)?', lambda g: cn2an.an2cn(g.group(0)), s)
    s = re.sub(r'[^一-鿿]', '', s)
    return [p.replace('ng', 'n') for p in lazy_pinyin(s)]
bad = 0
for text, p in man.items():
    r = m.transcribe(p, language='zh', initial_prompt='以下是普通话的句子。', fp16=False, temperature=0)
    hyp = r['text']
    a, b = norm(text), norm(hyp)
    sim = difflib.SequenceMatcher(None, a, b).ratio()
    flag = '' if sim >= 0.9 else '  <<<<'
    if flag: bad += 1
    print(f'{sim:.2f}{flag} | {text}\n       => {hyp}', flush=True)
print('lines below 0.90:', bad)
