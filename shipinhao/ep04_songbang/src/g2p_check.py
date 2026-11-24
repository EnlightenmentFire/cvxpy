import sys, re, os
sys.path.insert(0,'src')
from script import L
from tts import split_clauses, patch_ps
from kokoro import KPipeline
pipe=KPipeline(lang_code='z', repo_id='hexgrad/Kokoro-82M-v1.1-zh', model=False)
nofix = '--nofix' in sys.argv
for ln in L:
    text="".join(s for _,s in split_clauses(ln['text']))
    ps,_=pipe.g2p(text)
    if not nofix: ps=patch_ps(ps)
    print(ln['id'], text); print('   ', ps)
