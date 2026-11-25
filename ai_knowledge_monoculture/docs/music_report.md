# 配乐报告（按《配乐规范》）

## 题材与三层起伏

题材属“商业、组织、AI、交易”：低调电子脉冲 / 极简钢琴 + 轻打击，有推进感但不打鸡血；历史段按原简报换时代音色（普利茅斯手风琴、雅典里拉琴、1788 羽管键琴）。

| 段落 | 层 | 用的片段 | 相对增益 | 起止（秒） |
|---|---|---|---|---|
| coldopen | 铺底 | open_v2.wav | -3.0 dB | 0.0–45.93 |
| photocopy | 铺底 | bed_ext.wav | -2.0 dB | 45.93–113.41 |
| twoills | 铺底 | bed_ext.wav | -2.0 dB | 113.41–144.9 |
| plymouth | 铺底 | victorian_ext.wav | -2.5 dB | 144.9–270.87 |
| athens | 铺底 | lyre_v0.wav | -2.0 dB | 270.87–321.45 |
| hiring | 推进 | push_ext.wav | +0.0 dB | 321.45–389.08 |
| flash | 推进 | tension_ext.wav | +0.5 dB | 389.08–487.65 |
| corn | 推进 | bed_ext.wav | -0.5 dB | 487.65–558.28 |
| knight | 推进 | tension_ext.wav | +0.5 dB | 558.28–605.78 |
| aiera | 推进 | push_ext.wav | +0.5 dB | 605.78–679.86 |
| federalist | 高潮前 | baroque_v0.wav | +0.0 dB | 679.86–725.48 |
| remedies | 高潮 | climax_ext.wav | +1.5 dB | 725.48–759.23 |
| ending | 结尾 | ending_ext.wav | +0.0 dB | 759.23–780.71 |

高潮：“老人的答案”之后的总结句（c10_14）音乐抬高约 2.6 dB，旁白停 2 秒让音乐单独出来；闪电崩盘“暂停 5 秒”处音乐停 1.6 秒当作刹车；结尾收成钢琴独奏，黑场前留余音，整体淡入 2 秒、淡出 3 秒。

## 生成（MusicGen · facebook/musicgen-stereo-medium）

> 注意：MusicGen 权重授权为 CC-BY-NC-4.0（不可商用）。商业发布请用无配乐版 + 视频号音乐库。

**open**（铺底）：`dark ambient soundscape, deep sustained synth drone, subtle low pulse, mysterious, cinematic, sparse, no drums, no melody, no vocals`

| 版本 | 抢人声分数（越低越好） | 1–4kHz 能量占比 | 瞬态密度 | 响度起伏 | 疑似人声 | 选用 |
|---|---|---|---|---|---|---|
| v0 | 0.883 | 0.012 | 0.011 | 12.5 dB | 无 |  |
| v1 | 1.398 | 0.003 | 0.031 | 8.9 dB | 无 |  |
| v2 | 0.331 | 0.001 | 0.032 | 7.2 dB | 无 | ✅ 主用 |

**bed**（铺底）：`minimal soft piano with warm synth pad, reflective, calm, slow, sparse notes, A minor, 70 bpm, no drums, no vocals`

| 版本 | 抢人声分数（越低越好） | 1–4kHz 能量占比 | 瞬态密度 | 响度起伏 | 疑似人声 | 选用 |
|---|---|---|---|---|---|---|
| v0 | 0.334 | 0.006 | 0.028 | 4.0 dB | 无 | ✅ 主用（续写延长） |
| v1 | 0.948 | 0.025 | 0.016 | 11.7 dB | 无 |  |
| v2 | 1.862 | 0.089 | 0.024 | 5.2 dB | 无 |  |

**push**（推进）：`minimal modern electronic pulse with soft piano, steady, thoughtful, light percussion, 90 bpm, A minor, no vocals`

| 版本 | 抢人声分数（越低越好） | 1–4kHz 能量占比 | 瞬态密度 | 响度起伏 | 疑似人声 | 选用 |
|---|---|---|---|---|---|---|
| v0 | 0.806 | 0.009 | 0.052 | 9.2 dB | 无 |  |
| v1 | 0.804 | 0.03 | 0.063 | 7.1 dB | 无 |  |
| v2 | 0.54 | 0.005 | 0.06 | 3.8 dB | 无 | ✅ 主用（续写延长） |

**tension**（推进）：`tense minimal electronic pulse, soft ticking hi-hat, low synth drone, suspenseful but restrained, steady, 100 bpm, D minor, no vocals`

| 版本 | 抢人声分数（越低越好） | 1–4kHz 能量占比 | 瞬态密度 | 响度起伏 | 疑似人声 | 选用 |
|---|---|---|---|---|---|---|
| v0 | 1.781 | 0.007 | 0.042 | 13.5 dB | 无 |  |
| v1 | 0.406 | 0.002 | 0.042 | 5.1 dB | 无 | ✅ 主用（续写延长） |
| v2 | 1.061 | 0.006 | 0.042 | 9.7 dB | 无 |  |

**climax**（高潮）：`cinematic uplifting piano and strings with soft electronic pulse and deep drums, building, hopeful, emotional, D major, 80 bpm, no vocals`

| 版本 | 抢人声分数（越低越好） | 1–4kHz 能量占比 | 瞬态密度 | 响度起伏 | 疑似人声 | 选用 |
|---|---|---|---|---|---|---|
| v0 | 0.647 | 0.017 | 0.049 | 3.6 dB | 无 |  |
| v1 | 0.39 | 0.011 | 0.03 | 4.4 dB | 无 | ✅ 主用（续写延长） |
| v2 | 1.378 | 0.089 | 0.061 | 4.8 dB | 无 |  |

**ending**（结尾）：`solo piano, warm, gentle, resolving, slow, sparse, reflective ending, D major, no drums, no vocals`

| 版本 | 抢人声分数（越低越好） | 1–4kHz 能量占比 | 瞬态密度 | 响度起伏 | 疑似人声 | 选用 |
|---|---|---|---|---|---|---|
| v0 | 3.782 | 0.278 | 0.004 | 5.6 dB | 无 |  |
| v1 | 1.442 | 0.015 | 0.034 | 9.8 dB | 无 | ✅ 主用（续写延长） |

**victorian**（铺底·时代色）：`solo accordion, gentle old english folk waltz, quiet, sparse, nostalgic, slow, 3/4 time, no drums, no vocals`

| 版本 | 抢人声分数（越低越好） | 1–4kHz 能量占比 | 瞬态密度 | 响度起伏 | 疑似人声 | 选用 |
|---|---|---|---|---|---|---|
| v0 | 0.38 | 0.014 | 0.03 | 5.6 dB | 无 | ✅ 主用（续写延长） |
| v1 | 0.502 | 0.035 | 0.019 | 7.6 dB | 无 |  |

**lyre**（铺底·时代色）：`ancient greek lyre and harp plucks with low cello drone, solemn, tragic, slow, sparse, D minor, no drums, no vocals`

| 版本 | 抢人声分数（越低越好） | 1–4kHz 能量占比 | 瞬态密度 | 响度起伏 | 疑似人声 | 选用 |
|---|---|---|---|---|---|---|
| v0 | 0.468 | 0.025 | 0.026 | 7.5 dB | 无 | ✅ 主用 |
| v1 | 1.194 | 0.007 | 0.028 | 6.0 dB | 无 |  |

**baroque**（高潮前·时代色）：`harpsichord with soft string ensemble, stately baroque, calm, measured, D major, 80 bpm, no drums, no vocals`

| 版本 | 抢人声分数（越低越好） | 1–4kHz 能量占比 | 瞬态密度 | 响度起伏 | 疑似人声 | 选用 |
|---|---|---|---|---|---|---|
| v0 | 0.414 | 0.014 | 0.033 | 6.8 dB | 无 | ✅ 主用 |
| v1 | 0.834 | 0.031 | 0.043 | 6.8 dB | 无 |  |

## 混音实测

- 有旁白时音乐比人声低：中位 17.3 dB（10%–90% 分位 10.1–21.4 dB），目标 15–18 dB
- 侧链按“句子”触发：整句之内音乐稳住不动（不会在句中换气时冒头），句与句、段与段之间回升；音乐总线另加温和压缩（3:1）削掉片段本身的起伏
- 旁白停顿时音乐回升：约 16.5 dB（侧链 release 500 ms）
- 成片响度 -16.0 LUFS，真峰值 -2.0 dBTP，LRA 2.6 LU（目标 −16 LUFS / ≤ −1.5 dBTP）
- 音乐 3 kHz 处削 4 dB（q=1），给人声让出清晰度
- 封装成 mp4（AAC 约 128 kbps）后再测：主版本 −16.0 LUFS / 真峰值 −1.7 dBTP；无配乐版 −16.1 LUFS / −2.0 dBTP

## 导出前自检

- ASR 音节错误率（按段平均）：纯人声 0.37% → 加配乐 0.37% → 模拟手机外放 0.11%
- 有旁白时音乐突然冒出来（0.4 秒内 >6 dB 跳变）：只有 [459.2, 459.6, 460.0] 秒 —— 这是闪电崩盘“暂停 5 秒”后音乐有意从静默里回来，其余没有
- 高潮段单独导出：output/climax_excerpt.mp3（成片 744.78–764.03 秒）

