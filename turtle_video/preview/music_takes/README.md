# 配乐候选（MusicGen stereo-medium，每段 22 秒）

分数越低越好：人声检测（ASR 能认出词就重罚）、1–4 kHz 能量占比（越低越不抢人声）、响度起伏、断音；高潮段反过来奖励明显的推起。选中的片段已统一移调到 A 小调（或其关系大调）。所有候选的试听文件在本目录。

**授权提醒：MusicGen 权重是 CC-BY-NC-4.0（非商用）。商用发布请用无配乐版，或换可商用曲库。**

| 层 | 片段 | 选用 | 分数 | 1–4kHz 占比 | 起伏 dB | 估计调性 | 移调 | 速度 BPM | 人声检测 |
|---|---|---|---|---|---|---|---|---|---|
| bed | `bed_1` | ✅ | 2.81 | 0.0083 | 2.39 | G major | +0 | 117.2 | 无 |
| bed | `bed_0` | ✅ | 4.83 | 0.0061 | 3.97 | B minor | -2 | 170.5 | 无 |

| build | `build_0` | ✅ | 2.84 | 0.0149 | 2.38 | C major | +0 | 178.6 | 无 |
| build | `build_1` | ✅ | 3.56 | 0.0299 | 2.65 | G major | +0 | 178.6 | 无 |

| climax | `climax_0` | ✅ | -1.16 | 0.0041 | 3.86 | C major | +0 | 178.6 | 无 |
| climax | `climax_1` |  | 2.88 | 0.1469 | 4.53 | D minor | +0 | 121.0 | 无 |

| drop | `drop_0` | ✅ | 6.79 | 0.001 | 6.51 | G minor | +2 | 117.2 | 无 |

| reflect | `reflect_0` | ✅ | 4.58 | 0.0216 | 3.73 | G# major | -1 | 133.9 | 无 |

| end | `end_0` | ✅ | 6.55 | 0.0583 | 4.3 | G major | +0 | 121.0 | 无 |


提示词：

- **bed**：`minimal ambient electronic pad, soft sustained analog synth chords, low warm drone, calm, thoughtful, no drums, no melody, A minor, 80 bpm, no vocals`
- **build**：`minimal modern electronic pulse with soft piano, steady low synth bass pulse, light percussion, thoughtful, slightly tense, A minor, 90 bpm, no vocals`
- **climax**：`cinematic modern electronic, full arrangement, deep pulsing synth bass, steady drums, soft piano, warm strings, emotional, solemn, rising, A minor, 90 bpm, no vocals`
- **drop**：`low frequency synth drone, sparse soft heartbeat-like low drum, tense, dark, minimal, slow, no melody, A minor, no vocals`
- **reflect**：`minimal solo piano, sparse gentle notes, reflective, melancholic, slow, soft reverb, A minor, no drums, no vocals`
- **end**：`solo piano, a few slow gentle single notes, resolving, fading out, long reverb tail, A minor, no drums, no vocals`
