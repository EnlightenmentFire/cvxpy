# 组织里的权力 ·《不敢说的那句话》（大韩航空 801）

视频号竖屏视频（1080×1920，30fps，H.264 + AAC）的全部源码、旁白稿和史料核对。
画面与音效由程序生成；配音为 AI 合成（Qwen3-TTS，Apache-2.0）；配乐按 `docs/配乐规范.md` 用 MusicGen 生成。

> **配乐授权提示**：MusicGen（facebook/musicgen-stereo-medium）的模型权重是 **CC-BY-NC 4.0（非商用）**。
> 若账号有商业变现，请用「无配乐版」+ 视频号自带音乐库（音量 15–25%），或改用 Pixabay / Kevin MacLeod 等可商用曲目。

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
| `src/audio_mix.py` | 程序合成的音效（雨、雨刷、发动机、提示音、闷响、梯子上行音） |
| `src/music_gen.py` | MusicGen 分层生成配乐（铺底 / 推进 / 高潮挽歌 / 分析段钢琴 / 结尾大提琴），D 小调 |
| `src/music_select.py` | 每层多版本按客观指标挑版：人声频段占比、响度突跳、类人声检测、叠旁白后的 ASR 误读率 |
| `src/score.py` | 按三层起伏编排配乐，段落间 3 秒等功率交叉淡化，1978 段加磁带音色 |
| `src/mix_spec.py` | 按规范混音：侧链压缩（实测校准到音乐比人声低约 16 dB）、3 kHz 削 4 dB、两遍 loudnorm（-16 LUFS / -1.5 dBTP） |
| `src/export_final.py` | 全片导出：画面渲一次，两条音轨（配乐版 / 无配乐版） |
| `src/selfcheck.py` | 导出前自检：纯人声 / 配乐版 / 手机外放模拟的 ASR 对比、响度、音乐突跳、高潮段 |
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
