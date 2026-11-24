# 冷战核按钮 · 第一期《海底那一夜》

微信视频号竖屏片（1080×1920 · 30fps · H.264 · < 100MB）。

## 当前状态：成片完成（8 分钟版）

成片：`output/coldwar_ep01_haidi_naye.mp4`（1080×1920 · 30fps · 7:56 · 90.3 MiB）。自审记录见 `docs/self_review.md`。
- `docs/script.md` 旁白稿 v1（约 2700 字，预计 9.5–10 分钟）
- `docs/factcheck.md` 20 条史料逐条核对表（已对上原文 / 有出入 / 说法不一）
- `stills/` 8 张关键静帧 + `00_contact_sheet.jpg` 总览
- `audio/sample60/` 1 分钟样音（首选 Qwen3-TTS 版 + 备选 Kokoro 版）和逐句质检报告 `qc_report.md`
- `audio/voice_ref/` 用 VoiceDesign 按文字描述生成的参考声音（不是任何真人的声音）

确认风格和声音后再渲染全片。

## 管线
- `src/engine.py` 合成引擎（float32 画布、辉光、字体、胶片质感、「假想」标记、字幕安全区）
- `src/globe.py` 三维地球：Natural Earth 海岸线 + 城市光点；**不加载任何国界数据，东经 62° 以东整体剔除**
- `src/scenes.py` 各场景（真实段冷蓝/琥珀，假想段洋红热成像）
- `src/stills.py` 出静帧：`python3 src/stills.py`
- `src/script_v2.py` 8 分钟版旁白（64 句，字幕文本 + 配音文本）→ `audio/full/lines.json`、`docs/script_v2.md`
- `src/scenes2.py` 全片 35 个镜头；`src/edit.py` 按配音时长排镜头、切字幕、拼人声；`src/score.py` 配乐与音效；`src/render.py` 并行渲染；`src/finalize.py` 两遍编码（< 100MB）+ 整片 ASR 与响度复核
- `src/tts_qwen3.py` 首选配音：Qwen3-TTS-12Hz-1.7B-VoiceDesign 按描述设计参考音 → 1.7B-Base 克隆，逐句合成；每句测音高（85–105 Hz）+ ASR 回读，不合格换 seed 重做（Python 3.12 venv：`qwen-tts==0.1.1`，CPU bf16）
- `src/voiceqc.py` 质检工具：parselmouth 测音高、faster-whisper 回读（按拼音比对，标出声调可疑处）、压停顿（≤0.38 s）、rubberband 变速（R3 引擎，保留共振峰）、50 Hz 高通、-18 dBFS RMS
- `src/voice_post.py` 后期与拼接：旁白 ×1.3、引文 ×1.16，句间停顿 ≤0.4 s，配乐自动避让，成片整段 ASR 回读
- `src/tts_kokoro.py` 备选配音（Kokoro-82M v1.1-zh，需 Python 3.12 venv：`kokoro==0.9.4`、`misaki[zh]==0.9.4`）
- `src/sound.py` 配乐与音效，全部程序合成
- `src/fetch_assets.sh` 重新下载地图数据和档案照片

## 素材与许可
| 素材 | 来源 | 许可 |
|---|---|---|
| U-2 侦察照片 | NARA 193926（经 Wikimedia Commons） | 美国政府作品，公有领域 |
| B-59 照片 | NARA RG 428（428-N-711199/200/201），约 1962.10.28–29 | 美国政府作品，公有领域 |
| 海岸线 / 城市 | Natural Earth | 公有领域 |
| 配音模型（首选） | Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign、-1.7B-Base | Apache-2.0 |
| 配音模型（备选） | hexgrad/Kokoro-82M-v1.1-zh | Apache-2.0 |
| ASR 校验 | Systran/faster-whisper-medium | MIT |
| 字体 | Noto Sans CJK SC、JetBrains Mono | SIL OFL 1.1 |
| 配乐音效 | 本项目代码合成 | — |
