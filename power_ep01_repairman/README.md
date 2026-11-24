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
| `src/music.py` `src/mix.py` | 程序合成配乐（卷烟机节拍、手风琴、钢琴、停机嗡鸣）与混音（人声下自动压低） |

## 依赖（均为可商用许可）

- 配音：Qwen3-TTS-12Hz-1.7B-VoiceDesign / -Base（Apache-2.0）；备选 Kokoro-82M-v1.1-zh（Apache-2.0）
- 校验：faster-whisper large-v3-turbo（MIT）、praat-parselmouth（GPL，仅本地分析用，不随成片分发）
- 字体：思源宋体 / 思源黑体（SIL OFL）、EB Garamond、Parisienne、Caveat、Courier Prime、Special Elite（OFL / Apache）
- 渲染：skia-python、numpy、Pillow、ffmpeg；变速：rubberband（保留共振峰）

## 构建

```bash
python src/tts.py synth all && python src/tts.py process all     # 配音 + 校验
EP_DURATIONS=<work>/tts/durations.json python src/render.py video out/video.mp4 --jobs=4
python src/mix.py out/audio.wav                                    # 混音
# 最后 ffmpeg 两遍编码 + 合流，控制在 100 MB 以内
```
