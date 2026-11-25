import sys, numpy as np, librosa
for f in sys.argv[1:]:
    y, sr = librosa.load(f, sr=22050, mono=True)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    bt = librosa.frames_to_time(beats, sr=sr)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(1)
    names = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
    # Krumhansl key estimate
    maj = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88]); mnr = np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17])
    sc = [(np.corrcoef(np.roll(maj,k),chroma)[0,1], names[k]+" maj") for k in range(12)] + [(np.corrcoef(np.roll(mnr,k),chroma)[0,1], names[k]+" min") for k in range(12)]
    sc.sort(reverse=True)
    rms = librosa.feature.rms(y=y, frame_length=22050, hop_length=11025)[0]
    print(f, "tempo", np.round(tempo,1), "key", sc[0][1], "%.2f" % sc[0][0], sc[1][1])
    print("  beats", np.round(bt[:12], 2), "... n=%d" % len(bt))
    print("  rms/0.5s dB", np.round(20*np.log10(rms+1e-6)).astype(int).tolist())
