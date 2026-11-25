# 逍遥津：八百人冲阵之前，那封信写了什么？

「历史的关键一局」系列的一集。竖屏 1080×1920，时长约 12 分钟。

## 目录

- `script_data.py`：旁白稿和分镜（每句旁白对应一个场景、一个出处标签，以及送给 TTS 的读音修正）
- `tts.py`：Kokoro-82M-v1.1-zh 的 zm_014 音色，净语速 1.3 倍，降 2 个半音。首尾音节逐 token 放慢，防止高语速下吞字。需要在 Python 3.12 环境里运行
- `render.py`：skia 矢量渲染器，包括全部场景、字幕、标签、章节进度条和封面
- `mix.py`：拼接旁白，加少量合成音效（不含配乐）
- `make.sh`：一键出片，依次做时间线、四路并行渲染、响度双遍归一（-16 LUFS）、x264 两遍编码（目标约 92MB）
- `tools/asr_check.py`：用 Whisper small 做 ASR 回读，按拼音和旁白稿比对
- `out/`：封面、发布包、ASR 回读结果（成片 mp4 体积大，不进 git）

## 重新出片

```bash
source /opt/ttsenv/bin/activate && python tts.py <audio_dir> && deactivate
./make.sh <audio_dir> <work_dir>
python3 render.py cover out/cover_3x4.png
```
