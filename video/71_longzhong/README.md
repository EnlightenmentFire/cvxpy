# 71 隆中对与三顾茅庐（乱世起家录｜刘备篇 4）制作工程

竖屏 1080×1920 / 25 fps / H.264 + AAC。画面、配乐、音效全部由代码生成；配音为 Qwen3-TTS（Apache-2.0）托克维尔音色克隆。

| 文件 | 作用 |
| --- | --- |
| `src/script.py` | 旁白稿（数据源）：每句一个 id、所属场景、配音文本、字幕文本、句后停顿 |
| `src/tts_gen.py` | Qwen3-TTS-12Hz-1.7B-Base 以托克维尔参考音 ICL 克隆逐句合成；中位音高须在 85–105 Hz，否则换 seed |
| `src/voice_post.py` | 裁静音、压停顿、rubberband R3 变速 1.18（约 255 字/分）、高通、RMS 归一 |
| `src/asr_check.py` | faster-whisper 回读：拼音错误率 + 字幕块词级对齐（align.json） |
| `src/timeline.py` | 按成品配音时长排时间轴、场景区间、字幕分块 |
| `src/basemap.py` / `data.py` / `geo.py` | DEM 晕渲底图（z6/z8/z9）、烘入河湖；城邑、势力范围、路线（示意） |
| `src/illus.py` | 开场插画：雪后竹林、草庐、门开、将军与青年、发光地图 |
| `src/gfx.py` / `cards.py` | 图元；古文卡（层级角标、出处右下、白话）、现代类比卡＋类比偏差、起家三问卡、演义/史书两行对照 |
| `src/scenes.py` | 分镜与每帧绘制 |
| `src/audio.py` | 旁白拼接、原创合成配乐、音效、闪避混音、两遍 loudnorm 到 −15 LUFS / −1.5 dBTP |
| `src/render.py` / `final.py` / `cover.py` | 并行渲染、两遍编码与音画核对、封面 |
| `史实核对.md` | 引文核对与措辞处理 |

工作目录默认 `/home/user/work`（环境变量 `WORK` 可改），模型、DEM、中间文件都在那里，不入库。

```bash
python3 src/basemap.py                 # 底图（需先下载 terrarium 瓦片到 $WORK/dem/tiles）
NT=2 python3 src/tts_gen.py 0 2 & NT=2 python3 src/tts_gen.py 1 2   # 配音
python3 src/voice_post.py && python3 src/asr_check.py
python3 src/audio.py
python3 src/render.py 4 && python3 src/final.py OUTDIR && python3 src/cover.py OUTDIR/封面.png
```
