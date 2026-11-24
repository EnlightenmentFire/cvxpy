# 组织里的权力 ·《不敢说的那句话》（大韩航空 801）

视频号竖屏视频（1080×1920，30fps，H.264 + AAC）的全部源码、旁白稿和史料核对。
画面、音乐、音效全部由程序生成；配音为 AI 合成（Qwen3-TTS，Apache-2.0）。

## 目录

| 路径 | 内容 |
|---|---|
| `docs/fact_check.md` | 史料核对报告：清单逐条结果、四处更正、黑匣子原话逐句对照 NTSB 附录 B |
| `docs/script.md` | 完整旁白稿 + 字幕卡 + 场景说明（由 `src/script_data.py` 自动导出） |
| `stills/` | 关键静帧（与成片同一套渲染代码） |
| `audio/` | 样音（冷启动 + 第 1 段，约 100 秒） |
| `src/script_data.py` | 唯一的稿件数据源：每句旁白、字幕卡、近地警告、场景事件 |
| `src/tts_build.py` | 逐句配音：克隆 → 音高检查（85–105 Hz，超出换 seed 重来）→ ASR 回读（拼音比对）→ 50 Hz 高通、停顿压到 0.4 秒内、rubberband 拉速、电平统一 |
| `src/gpws_build.py` | 近地警告机械人声（VoiceDesign 合成 + 窄带/降采样/失真处理，不用真实录音） |
| `src/render_lib.py` `src/scenes.py` `src/compose.py` | skia 逐帧绘制：配色、字体、字幕、字幕卡；各场景；时间线与转场 |
| `src/audio_mix.py` | 程序合成的底噪音乐与音效、人声下压背景、撞击后两秒静音 |
| `src/make_segment.py` | 渲染一段或全片：混音 + 逐帧画面 → mp4 |
| `src/stills.py` | 渲染关键静帧 |

## 配音流程

1. VoiceDesign 按描述「四十多岁男中音，醇厚偏低沉，历史纪录片旁白，凝重克制，语速中等偏慢」生成 5 个候选，
   中位音高 95 / 102 / 76 / 94 / 89 Hz，选 89 Hz 的一个做参考音。
2. Base 模型用参考音克隆，逐句合成；每句测中位音高，超出 85–105 Hz 换 seed 重来（最多 6 次）。
3. faster-whisper large-v3-turbo 逐句回读，按无声调拼音算错误率，> 10% 重来。
4. 旁白 1.16 倍、引文 1.06 倍（rubberband R3 引擎），句内停顿压到 0.4 秒以内，加 50 Hz 高通，人声约 -18 dBFS RMS。

## 渲染

```bash
cd src
python3 tts_build.py            # 全部旁白（可加段落号只做某几段）
python3 gpws_build.py           # 近地警告
python3 stills.py OUTDIR        # 关键静帧
python3 make_segment.py OUT s0_01 s12_01 --crf 26   # 全片
```

依赖：skia-python、numpy、scipy、soundfile、praat-parselmouth、qwen-tts、faster-whisper、pypinyin、cn2an、
ffmpeg、rubberband-cli、Noto Sans/Serif CJK 字体。
