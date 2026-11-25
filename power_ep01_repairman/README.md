# 「组织里的权力」第一期《维修工》— 视频号竖屏视频工程

1080×1920 · 30 fps · H.264/AAC · 目标 < 100 MB。全部画面、配乐、音效由本目录代码生成；配音用可商用开源模型合成。

## 目录

| 路径 | 内容 |
|---|---|
| `script/讲稿_v1.md` | 讲稿（由 `src/script_data.py` 导出），含【示意】【转述】【推论】标注 |
| `script/核对记录.md` | 史料与引文核对记录（每条的证据强度和处理方式） |
| `keyframes/` | 关键静帧（风格确认用） |
| `samples/` | 样音、预览片段 |
| `src/script_data.py` | 逐句讲稿（配音文本、字幕文本、语言、停顿） |
| `src/timeline.py` | 时间轴：每句起止、章节卡、停机事件；字幕切分 |
| `src/gfx.py` `src/icons.py` | 画面基础：纸张、配色（唯一警示色橙红）、无脸扁平人物、机器、卡片 |
| `src/scenes_a.py` `src/scenes_b.py` | 各段动画（冷启动、规章铺满工厂、组织图变形、三条件打分、恶性循环、盾牌……） |
| `src/render.py` | 合成每一帧，多进程渲染，ffmpeg 编码 |
| `src/tts.py` | 配音流水线：Qwen3-TTS VoiceDesign 设计参考音 → Base 克隆逐句合成 → 音高/ASR 校验 → 变速、限停顿、高通、电平 |
| `src/music_gen.py` | 按《配乐规范》用 MusicGen（facebook/musicgen-stereo-medium）分层生成配乐：铺底 / 推进 / 高潮 / 收束 / 结尾，每层两版择优，用音频续写保持调性连贯 |
| `src/music.py` `src/mix.py` | 音效（冷启动的卷烟机节拍、停机：咔—静半秒—低频嗡鸣）与混音：配乐 3 kHz 削 4 dB、侧链压缩避让人声、两遍 loudnorm 到 -16 LUFS / -1.5 dBTP |
| `src/final_check.py` | 导出前自检：响度与真峰值、人声下配乐电平、逐句 ASR（纯人声 / 成片 / 模拟手机外放） |

## 依赖与许可（配乐模型除外，均可商用）

- 配音：Qwen3-TTS-12Hz-1.7B-VoiceDesign / -Base（Apache-2.0）；备选 Kokoro-82M-v1.1-zh（Apache-2.0）
- 配乐：MusicGen stereo medium —— **模型权重为 CC-BY-NC 4.0（非商用）**。账号如有商业变现，请用同时导出的“无配乐版”，发布时用视频号曲库配乐（规范三之 3）
- 校验：faster-whisper large-v3-turbo（MIT）、praat-parselmouth（GPL，仅本地分析用，不随成片分发）
- 字体：思源宋体 / 思源黑体（SIL OFL）、EB Garamond、Parisienne、Caveat、Courier Prime、Special Elite（OFL / Apache）
- 渲染：skia-python、numpy、Pillow、ffmpeg；变速：rubberband（保留共振峰）

## 构建

```bash
python src/tts.py synth all && python src/tts.py process all        # 配音 + 音高/ASR 校验 + 后期
python src/music_gen.py a && python src/music_gen.py b && python src/music_gen.py ext   # MusicGen 分层配乐
EP_DURATIONS=<work>/tts/durations.json python src/render.py video <work>/final/video_noaudio.mp4 --jobs=4
python src/mix.py <work>/final/audio_nomusic.wav --no-music        # 无配乐版音轨
python src/finish.py   # 校准配乐电平 → 混音 → 限幅 → 两遍编码 → 封装两版 → 高潮试听片段 → 自检
```

成片规格：1080×1920，30 fps，H.264 High@4.1 两遍编码约 830 kbps + AAC 128 kbps，整体响度 -16 LUFS，真峰值 ≤ -1.5 dBTP，旁白时配乐比人声低约 16.7 dB（侧链压缩），文件 < 100 MB。
