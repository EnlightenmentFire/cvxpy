# 《一个法国年轻人看美国小镇》制作工程

微信视频号竖屏视频（1080×1920，30 fps）。全部画面、音乐、音效均为程序生成；配音用 Apache-2.0 的 Qwen3-TTS。

| 文件 | 作用 |
|---|---|
| `script_data.py` | 全片脚本（数据）：每句旁白/引文、法文原文、出处、停顿、画面提示 |
| `SCRIPT.md` | 由 `gen_script_md.py` 生成的可读版脚本 |
| `FACTCHECK.md` | 史料核对记录（"待核"项逐条处理） |
| `art.py` / `layout.py` / `scenes.py` | 画面引擎：羊皮纸、墨线、排线、水彩、剪影；版式（标题、插图版框、字幕、法文引文卡）；各场景 |
| `tts_clone.py` | Qwen3-TTS Base 克隆设计好的旁白声音，逐句合成；中位音高不在 85–105 Hz 就换 seed 重来 |
| `voice_post.py` | 去头尾静音、停顿压到 ≤0.4 s、rubberband R3 变速（保共振峰）、50 Hz 高通、−18 dBFS RMS |
| `asr_check.py` | faster-whisper 回读，按无调拼音比对 |
| `music.py` | 原创室内乐（钢琴/小提琴），fluidsynth + FluidR3_GM（MIT 许可）渲染 |
| `sfx.py` | 全部音效用 numpy 合成（风、浪、锯木、人声嗡嗡、冰块、狗嚎……） |
| `mixlib.py` / `build_sample.py` | 混音工具；约 1 分钟样音 |

声音设计：Qwen3-TTS-12Hz-1.7B-VoiceDesign，描述「四十多岁男中音，醇厚偏低沉，历史纪录片旁白，凝重克制，语速中等偏慢」，6 个候选的中位音高 83.5 / 83.8 / 115.5 / **86.7** / 77.8 / 75.5 Hz，选 86.7 Hz 那个（最接近 90 Hz）作为克隆参考。不克隆任何真人声音。
