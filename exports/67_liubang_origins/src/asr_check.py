# ASR 回读：逐句识别配音，与朗读稿比对
import json, re, sys, difflib, subprocess
import numpy as np
from faster_whisper import WhisperModel
tl = json.load(open(sys.argv[1])); vd = sys.argv[2]
m = WhisperModel('small', device='cpu', compute_type='int8', cpu_threads=4)
P = r'[\s，。、；：！？「」《》（）·…,.!?;:"\'“”]'
bad = []; out = []
for l in tl['lines']:
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f"{vd}/line_{l['i']:04d}.mp3", '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True).stdout
    seg, _ = m.transcribe(np.frombuffer(raw, np.float32), language='zh', beam_size=3, initial_prompt='以下是普通话的句子。')
    hyp = ''.join(s.text for s in seg)
    a = re.sub(P, '', l['say']); b = re.sub(P, '', hyp)
    r = difflib.SequenceMatcher(None, a, b).ratio()
    out.append(dict(i=l['i'], ratio=round(r, 3), say=l['say'], asr=hyp))
    if r < 0.85: bad.append(out[-1])
json.dump(out, open('asr_report.json', 'w'), ensure_ascii=False, indent=1)
print('lines', len(out), 'mean', round(np.mean([o['ratio'] for o in out]), 3), 'below0.85', len(bad))
for b in bad: print(b['i'], b['ratio'], '|', b['say'], '|', b['asr'])
