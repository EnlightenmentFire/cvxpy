# 交易系列 · 第一期《海龟实验》— 制作工程

微信视频号竖屏视频（1080×1920，30fps，mp4，< 100MB）。本目录是完整的制作源码、讲稿和史料核对。

## 目录

| 路径 | 内容 |
|---|---|
| `script/narration.md` | 旁白稿（由 `src/script_data.py` 导出，字幕文字和配音读法分开列） |
| `research/fact_check.md` | 史料核对表：原稿每条说法 → 查到的出处 → 片中怎么用 |
| `research/raw/` | 三路检索的原始笔记（逐字引文 + 链接） |
| `preview/` | 给你确认风格用的关键静帧、样音、预览片段 |
| `src/` | 全部生成代码（见下） |

## 流水线

1. **讲稿** `src/script_data.py`：每句一行，`text` 是字幕，`tts` 是配音念的写法（数字写成汉字、去掉人名中点）。每句的 `id` 同时是画面动画的触发点。英文原话只上屏幕，不让中文 TTS 念。
2. **配音** `src/tts.py`
   - 声音：Qwen3-TTS-12Hz-1.7B-**VoiceDesign** 按“四十多岁男中音，醇厚偏低沉，历史纪录片旁白，凝重克制，语速中等偏慢”设计；候选 6 个（先出 3 个都不在 90Hz 附近，又补 3 个），选 seed 44（中位音高 97.5Hz，谐噪比最好、克隆后每句都落在 85–105Hz）。
   - 用 Qwen3-TTS-12Hz-1.7B-**Base** 以该候选为参考逐句克隆合成（ICL 模式）。两个模型均为 Apache-2.0，不克隆任何真人声音。
   - 每句：rubberband 保留共振峰提速 1.16×（引文约 1.08–1.10×）→ 超过 0.4 秒的停顿压到 0.4 秒 → 50Hz 高通 → 人声 RMS 统一到 −18 dBFS。
   - 每句自动质检：parselmouth 测中位音高（必须 85–105Hz）、faster-whisper large-v3-turbo 回读（按拼音比对，同音字算对）、语速范围；不合格换 seed 重生，最多 5 次。
3. **画面** `src/theme.py`（配色、字体、安全区）、`src/prims.py`（文字、线描海龟、剪影、图标）、`src/scenes.py`（各段场景）、`src/compose.py`（时间线、字幕、颗粒和暗角）、`src/data.py`（示意用的合成数据）。用 skia 逐帧绘制。
4. **配乐与混音**（按《配乐规范》重做）
   - `src/music.py`：MusicGen（facebook/musicgen-stereo-medium，本地 CPU）按层生成 22 秒片段：铺底（长音 pad）、推进（低调电子脉冲 + 极简钢琴 + 轻打击）、高潮（全编制）、1988 段的低频长音、第七章的独奏钢琴、结尾钢琴余音。每层 2–3 版，按客观指标挑（ASR 查人声、1–4 kHz 能量、响度起伏、断音、调性与速度），再统一移调到 A 小调、对齐速度。**注意：MusicGen 权重是 CC-BY-NC-4.0（非商用）。**
   - `src/mix.py`：三层编排（2–4 秒等功率交叉淡化），高潮落在“这个赌……输在了自己身上”之后 1.8 秒的旁白留白里；ffmpeg 处理音乐：3 kHz −4 dB、2 秒淡入、结尾 3 秒淡出后留 2 秒；`sidechaincompress`（attack 15 ms / release 500 ms）键控信号取自旁白，带 0.65 秒保持，旁白在说话时音乐压到人声以下约 15–18 dB，真正停顿时回升；最后整体 −16 LUFS、真峰值 ≤ −1.5 dBTP。同时导出“无配乐”版（规范第三选项）。音效（打字机、连亏的“嗒”、传真机）不进侧链，单独叠加。
   - `src/qa_audio.py`：分章节对比 ASR 错误率（纯人声 / 成品混音 / 模拟手机外放），并导出高潮片段单听。
5. **渲染** `src/render.py`：多进程出帧 → ffmpeg（libx264 两遍编码，按时长算码率卡在 100MB 内）→ 合入 AAC 音轨。
6. **静帧** `src/stills.py`：按讲稿里的触发点抽关键帧。

## 运行

```bash
# 环境：Python 3.12 venv（torch CPU、qwen-tts、faster-whisper、praat-parselmouth、skia-python、scipy、pyloudnorm）
python src/tts.py OUT/lines                          # 全部旁白（可断点续跑）
python src/music.py gen OUT/takes && python src/music.py score OUT/takes && python src/music.py choose OUT/takes
python src/mix.py OUT/lines OUT/takes OUT/mix           # 混音（含无配乐版）
python src/qa_audio.py OUT/mix OUT/mix/asr.json OUT/climax.m4a
python src/render.py OUT/lines OUT/mix.wav OUT/turtle.mp4 --bitrate 850 --workers 4
python src/stills.py OUT/stills OUT/lines            # 关键静帧
```

## 规矩（制作时逐条执行）

- 价格图、资金曲线全部是合成数据，画面标“示意”；资金曲线另标“非真实学员数据”。
- 人物一律剪影；报纸、传真为示意，不出现真实报头、公司名或地址。
- 说法不一的数字在画面上并列出处，旁白不替它们统一；诉讼只讲到“和解、不承认过错”。
- 不涉及当下市场与任何品种、平台、课程；片尾“本期只讲历史和人性，不构成任何投资建议”。
