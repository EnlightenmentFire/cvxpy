# 第 51 期《量子擦除，真的能改写过去吗？》制作工程

系列「佛法与心智」。微信视频号竖屏视频 1080×1920，25 fps 恒定帧率，H.264 + AAC。
全部画面、配乐由代码生成；配音为托克维尔声音（Qwen3-TTS 克隆）。交付物在 `../exports/51_quantum-eraser-repentance/`。

| 文件 | 作用 |
|---|---|
| `script_data.py` | 全片逐句稿（数据）：旁白、上屏字幕/原文、停顿、画面提示 |
| `FACTCHECK.md` | 物理与佛典逐条核对（CBETA 原文、Kim 等论文 PDF） |
| `tts_clone.py` | Qwen3-TTS-12Hz-1.7B-Base ICL 克隆，逐句合成；中位音高不在 82–108 Hz 就换 seed |
| `voice_post.py` | 去头尾静音、句内停顿 ≤0.38 s、rubberband R3 变速（旁白 1.12，原句 1.03）、50 Hz 高通；拼时间线，出 timeline.json / narration.srt / voice.wav |
| `asr_check.py` | faster-whisper 回读，按无调拼音与稿子比对 |
| `music.py` | 原创底乐（numpy 合成：磬、类古琴拨弦、箫、玻璃钟、低音持续），开场第 0 秒一声磬作声音钩子 |
| `render.py` | 逐帧画面：双缝、Kim 实验光路（示意）、符合计数分组、经文卡、禅堂灯、云月、书法；字幕烧录 |
| `mix.py` | 底乐比旁白低约 22 dB、停顿处抬 5 dB；两遍 loudnorm 到 −15 LUFS / −1.5 dBTP；两遍 x264 到 100 MB 以内；另出无配乐版 |
| `cover.py` | 封面（9:16、3:4） |
| `export.py` | 导出逐句旁白稿 sentences.json/txt、字幕、带时间码的 SCRIPT.md |

## 重现

```bash
python tts_clone.py                 # 约 1–1.5 小时（4 核 CPU）
python voice_post.py
python asr_check.py
python music.py
for k in 0 1 2 3; do python render.py $k 4 & done; wait
python mix.py mix
python mix.py mux <picture.mp4> <out_dir> <basename>
```

参考音频：`claude/tocqueville-america-video-a250yg` 分支 `tocqueville_video/preview/voice_design_reference.m4a`（18 秒，设计出来的声音，不克隆任何真人），参考文本见 `tts_clone.py`。
