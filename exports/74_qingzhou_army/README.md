# 74 曹操收编青州兵 · 制作工程

竖屏 1080×1920 / 25fps。画面、配乐、音效全部为程序生成；配音为 Qwen3-TTS（Apache-2.0）Base 模型 ICL 克隆「托克维尔」设计音色（参考音频 A0b，18 秒）。

| 文件 | 作用 |
|---|---|
| `src/script.py` | 全片脚本数据：旁白、字幕、古文卡、类比卡、画面节拍 |
| `src/tts_run.py` / `src/voice_post.py` / `src/asr_check.py` | 逐句克隆合成；裁静音、停顿 ≤0.35s、rubberband 1.1 倍变速、-18 dBFS；faster-whisper 回读按拼音比对 |
| `src/timeline.py` | 按真实配音时长排时间线（句间 0.5s，换段 +0.55s，开场 0.45s 先出声音钩子） |
| `src/eng.py` / `src/scenes.py` / `src/render.py` | skia 画面引擎；逐镜头动画；字幕、卡片、角标合成；4 进程分段渲染 |
| `src/music.py` | 原创配乐：按时间线写 MIDI，FluidR3_GM（MIT）渲染 |
| `src/sfx.py` | numpy 合成音效：箭雨、马嘶、火、兵器、人潮、重击、风 |
| `src/mix.py` / `src/final_mux.py` | 混音（音乐电平跟随 + 人声闪避）、两遍 loudnorm 到 -15 LUFS；两遍 x264 编码到 <100MB，aresample=async=1 |
| `src/cover.py` | 封面 1080×1440 / 1080×1920 |
| `sentences.json` / `sentences.txt` | 逐句旁白（含 TTS 用改写文本与时间码），供盒子上重配 |
| `narration.srt` | 字幕 |
| `旁白稿.md` / `史实核对.md` / `发布包.md` | 文稿、核对记录、发布信息 |

地形底图：AWS Terrain Tiles（terrarium，公开数据）自行做晕渲。
