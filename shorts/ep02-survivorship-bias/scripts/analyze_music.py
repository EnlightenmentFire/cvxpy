import sys, numpy as np, soundfile as sf, librosa
for f in sys.argv[1:]:
    y,sr=sf.read(f); m=y.mean(1) if y.ndim>1 else y
    tempo,beats=librosa.beat.beat_track(y=m,sr=sr,start_bpm=115); bt=librosa.frames_to_time(beats,sr=sr)
    rms=librosa.feature.rms(y=m,frame_length=sr,hop_length=sr)[0]
    S=np.abs(librosa.stft(m,n_fft=4096,hop_length=sr))**2; fr=librosa.fft_frequencies(sr=sr,n_fft=4096)
    mid=S[(fr>1500)&(fr<4000)].sum(0)/S.sum(0)
    cent=librosa.feature.spectral_centroid(y=m,sr=sr,hop_length=sr)[0]
    print(f, 'tempo',np.round(tempo,1),'nbeats',len(bt))
    print('  rms dB/s ', ' '.join(f'{20*np.log10(r+1e-9):.0f}' for r in rms))
    print('  centroid ', ' '.join(f'{c/1000:.1f}' for c in cent))
    print('  1.5-4k % ', ' '.join(f'{100*x:.0f}' for x in mid))
    print('  beat iv  ', np.round(np.diff(bt)[:12],3))
