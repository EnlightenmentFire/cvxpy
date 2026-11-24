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
| `music.py` | （早期样音用）原创钢琴小品，fluidsynth + FluidR3_GM 渲染；成片不再使用 |
| `music_spec.py` | 按《配乐规范》生成成片配乐：思想类（钢琴＋柔和弦乐），铺底→推进→高潮三层，3 秒交叉淡化，孟菲斯段留空，高潮对准 2 秒旁白留白，曲尾余音落在最后一句后 2.5 秒 |
| `final_mux.py` | 规范里的侧链混音链（volume 0.5、3 kHz −4 dB、2 秒淡入、sidechaincompress 0.02/10/15/500），两遍 loudnorm 到 −16 LUFS / −1.5 dBTP，并逐章测量音乐比人声低多少；两遍 x264 编码到 100 MB 以内 |
| `render.py` / `anim.py` | 时间线、逐场景动画（静态层缓存＋动态层 15 fps）、字幕切分、法文引文卡、4 进程并行渲染 |
| `build_stems.py` | 旁白轨和音效轨（孟菲斯段只有风、冰、一声狗嚎） |
| `verify_voice.py` | 全片逐句：音高（Praat，75–300 Hz 范围，中位数须在 85–105 Hz）＋ ASR 回读 |
| `sfx.py` | 全部音效用 numpy 合成（风、浪、锯木、人声嗡嗡、冰块、狗嚎……） |
| `mixlib.py` / `build_sample.py` | 混音工具；约 1 分钟样音 |

声音设计：Qwen3-TTS-12Hz-1.7B-VoiceDesign，描述「四十多岁男中音，醇厚偏低沉，历史纪录片旁白，凝重克制，语速中等偏慢」，6 个候选的中位音高 83.5 / 83.8 / 115.5 / **86.7** / 77.8 / 75.5 Hz，选 86.7 Hz 那个（最接近 90 Hz）作为克隆参考。不克隆任何真人声音。

## 配乐来源与授权

成片配乐用的是 Kevin MacLeod（incompetech.com）的曲子，授权 CC BY 4.0，可商用，但**发布时必须在简介里署名**（见 `MUSIC_CREDITS.txt`）。

没有用《配乐规范》第一优先的 MusicGen：facebook/musicgen-* 的模型权重是 CC-BY-NC-4.0（非商用），和本期"只用确认可商用的素材"冲突。可商用的本地生成模型 ACE-Step（Apache-2.0）在 PyPI 上的包缺了主体代码，本环境拿不到 GitHub 源码，所以按规范第二优先改用免版税曲库。

## 时长

最初完整稿约 16.7 分钟；按"10–12 分钟左右、不超过 20 分钟、内容决定"的要求删去次要细节后，成片约 14 分钟。被删的句子在 `script_data.py` 里标了 `cut=True`，`FULL=1` 可以恢复完整稿。
