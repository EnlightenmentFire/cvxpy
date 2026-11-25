# 冷战核按钮 · 第二期《一片没有出现的天空》

竖屏 1080×1920 / 30fps 视频号成片的全部工程：解说稿、史料核对、渲染代码、样张、样音。

**成片**（按配乐规范重做声音）：
- `final/一片没有出现的天空_冷战核按钮02.mp4` — 有配乐（12 分 52 秒，1080×1920，30fps，H.264 + AAC，小于 100 MB）
- `final/一片没有出现的天空_冷战核按钮02_无配乐.mp4` — 只有人声和音效，可用视频号音乐库配乐

配乐说明见 `audio/music_report.md`，配音检测见 `audio/voice_report_full.md`，
ASR 回读见 `final/asr_lines.txt`（逐句：纯人声 vs 成片混音）和 `final/asr_film.txt`（整片连续识别），抽帧检查见 `final/qa_sheet.jpg`。

- `script/script.md` — 解说稿 v1（逐段旁白 + 画面说明）
- `script/notes_sources.md` — 史料核对表、对原提纲的更正、主要来源
- `stills/` — 风格确认用的关键静帧（`00_contact_sheet.jpg` 为总览）
- `audio/qwen_sample_1min_*.m4a` — 1 分钟配音样音（Qwen3-TTS 设计音色 + 克隆，纯人声 / 带配乐），检测数据见 `audio/voice_report.md`
- `audio/sample_*.m4a` — 上一轮 Kokoro 样音（备选方案）
- `preview/preview_cold_open.mp4` — 冷启动 + 片名的动态预览（约 38 秒，按成片码率编码）
- `src/` — 渲染代码（numpy + OpenCV 逐帧合成，ffmpeg 编码）

## 渲染

```
# 旁白（Qwen3-TTS，Apache-2.0，Python 3.12 venv）：先设计音色，再克隆逐句合成
python src/qwen_design.py design_dir 3 90
python src/qwen_narrate.py lines.json design_dir/design.json out_dir
# 备选：Kokoro-82M v1.1-zh
python src/tts.py lines.json out_dir zm_014 1.0
# 画面（并行渲染，按时间段）
NPROC=4 python3 src/render.py <tts_dir> video.mp4 [t0 t1]
# 声音（配乐与音效全部程序合成；分层、侧链压低、两遍 loudnorm，同时输出无配乐版）
python3 src/mix2.py <tts_dir> <out_dir>
# 检查：整片 ASR、逐句 ASR（纯人声 vs 成片混音）
python src/asr_film.py final_audio.wav timeline.json asr_film.txt
python src/asr_lines.py voice.wav final_audio.wav timeline.json asr_lines.txt
```

素材版权：地图数据为 Natural Earth（公有领域）；里根 1983-03-23 讲话原声为白宫通讯局录音（里根图书馆注明公有领域，NARA 7087573）；
当年官方想象图为美国空军 1984 年作品（公有领域，NARA 6386997）；字体为 Noto Sans CJK 与 Courier Prime（SIL OFL）；
配音为 Qwen3-TTS-12Hz-1.7B（先用 VoiceDesign 按文字描述设计音色，再用 Base 克隆逐句合成；Apache-2.0；没有克隆任何真人的声音），
备选方案 Kokoro-82M v1.1-zh（Apache-2.0）；配乐、音效均为代码合成。
