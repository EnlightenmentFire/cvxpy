# Reference clips for Chatterbox voice cloning, generated with Kokoro (no real person's voice used)
import numpy as np, soundfile as sf
from kokoro import KPipeline
p = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M')
R = {"pete": ("am_fenrir", "Well now, I have been digging in this here river since breakfast, and let me tell you, partner, there ain't a lick of gold in it. Not one lick!"),
     "zoe": ("af_bella", "Okay, so, here's the thing. It's actually really simple. I've explained it like a thousand times, and honestly, it's kind of fine."),
     "riggy": ("am_puck", "Ladies and gentlemen! Welcome to the main event! The crowd is on its feet! What a play! Unbelievable!")}
for k,(v,t) in R.items():
    a = np.concatenate([x.numpy() for _,_,x in p(t, voice=v, speed=0.95)])
    sf.write(f"refs/{k}_ref_raw.wav", a, 24000)
