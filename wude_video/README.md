# 命理与正统 · 第一期《五德终始》— 视频号竖屏视频工程

1080×1920 · 30fps · H.264/AAC。画面、配乐、音效全部由代码生成；旁白用开源 TTS 合成。

## 目录
- `script/wude.script` — 结构化讲稿（旁白 / 引文 / 段尾"这说明" / 画面与音效提示 / TTS 读音替换）
- `docs/讲稿.md` — 由讲稿自动生成的可读版；`docs/史料核对.md` — 逐条核对记录
- `src/` — 渲染与音频流水线
  - `script_parser.py` 讲稿解析（字幕正字 + TTS 同音替换）
  - `tts_worker.py` / `tts_batch.py` Qwen3-TTS 合成；逐句测中位音高（85–105Hz）、Whisper 回读比对拼音，不合格换 seed 重录
  - `voice_post.py` 50Hz 高通、变速（rubberband R3，保留共振峰）、停顿压到 0.4s 内、语音 RMS -18 dBFS
  - `audio_synth.py` 编钟 / 磬 / 低鼓 / 埙 / 持续音全部用正弦分音与滤波噪声合成，旁白时自动压低（ducking）
  - `gfx.py` `wheel.py` `stages.py` `timeline.py` `render.py` skia 矢量渲染：五德轮盘、竹简、五色主色调、字幕安全区
- `stills/` 关键静帧；`audio_sample/` 约 1 分钟样音与样片

## 授权
- TTS：Qwen3-TTS-12Hz-1.7B-VoiceDesign / Base（Apache-2.0）。声音由文字描述设计，不克隆任何真人。
- 回读校验：Whisper large-v3-turbo（MIT，CTranslate2 转换版）
- 字体：思源宋体 / 思源黑体（Noto Serif/Sans CJK，SIL OFL 1.1，可商用）
- 配乐与音效：本工程代码合成，无第三方素材

## 运行（概要）
```bash
python src/script_parser.py script/wude.script build/script.json
python src/tts_batch.py build/script.json build/tts_raw          # 合成旁白
python src/voice_post.py build/tts_raw build/voice_post          # 后期
DURATIONS=build/voice_post/durations.json python src/render.py still S2_19+2 out.png
```
