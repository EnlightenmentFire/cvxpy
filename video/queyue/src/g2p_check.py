import sys, os, warnings; warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import L, tts_text
from kokoro import KPipeline
pipe = KPipeline(lang_code='z', repo_id='hexgrad/Kokoro-82M-v1.1-zh', model=False)
for i, l in enumerate(L):
    t = tts_text(l[2])
    if t == l[2].replace('《','').replace('》',''): continue
    ps = pipe.g2p(t)
    ps = ps[0] if isinstance(ps, tuple) else ps
    print(i, l[2]); print('   ', ps)
