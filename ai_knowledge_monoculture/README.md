# 「AI 知识」·《防暴君，也防暴民》制作工程

竖屏 1080×1920、30fps，微信视频号。所有画面由程序绘制（pycairo + Pillow），配乐和音效由 numpy 合成，
旁白用 Apache-2.0 开源模型合成；不使用任何第三方素材、真实公司标志或真人声音。

## 目录

| 路径 | 内容 |
|---|---|
| `script_data.py` | 全片唯一的文本源：旁白（TTS 读的）、字幕（屏幕显示的）、英文原文、语气标记 |
| `docs/script.md` | 分镜稿（由 `docs/make_script_md.py` 生成） |
| `docs/factcheck.md` | 史料核对表：每条数字、引文对应的原文和链接 |
| `stills/` | 风格静帧（确认用） |
| `samples/` | 样音、声音候选、冷启动动画小样 |
| `render/` | 画面：`engine.py` 基础绘制、`art.py` 插画、`scenes.py` 场景、`segments.py` 动画段落、`timeline.py` 时间轴与字幕切分、`video.py` 逐帧渲染 |
| `audio/` | 声音：`musicgen_gen.py` 用 MusicGen 生成配乐片段（`music_plan.json` 是提示词）、`music_select.py` 给每个版本打“抢人声”分并检测人声、`music_build.py` 按三层起伏编排、`final_mix.py` 按《配乐规范》侧链混音与两遍 loudnorm、`checks.py` 导出前自检、`synth.py`/`plan.py` 音效 |
| `tts/` | 配音：`voice_design.py` 设计声音、`narrate.py` 克隆并逐句合成（音高 + ASR 校验）、`postprocess.py` 后期、`robot_voice.py` 英文机器腔 |

## 配音流程

1. `voice_design.py`：Qwen3-TTS-12Hz-1.7B-VoiceDesign，按"四十多岁男中音，醇厚偏低沉，历史纪录片旁白，凝重克制，语速中等偏慢"出候选，parselmouth 测中位音高，选最接近 90Hz 的。
2. `narrate.py`：Qwen3-TTS-12Hz-1.7B-Base 用选中的候选做参考音（ICL 模式）逐句合成；每句换 seed 重试，直到去掉多余停顿后中位音高在 85–105Hz 之内（留 1.5Hz 余量），并且 faster-whisper large-v3 回读按"拼音 + 声调"比对无误。
3. `postprocess.py`：停顿压到 ≤0.4 秒 → rubberband 保留共振峰拉速到目标语速（旁白约 4.9 字/秒，引文约 4.3 字/秒）→ 50Hz 高通 → 人声有效段 RMS 统一到 −18 dBFS → 再跑一遍 ASR。
4. `robot_voice.py`：Kokoro-82M 英文男声读第 9 代野兔原文，WORLD 声码器把音高压成一条直线，加一点数字感，做成"机器在念"。

## 渲染

```bash
source /home/user/.venvs/tts/bin/activate
python render/stills.py stills                                  # 风格静帧
python audio/build_audio.py --voice <voice_dir> --robot <robot.wav> --out mix.wav
python render/video.py --voice <voice_dir> --robot <robot.wav> --out video.mp4 --workers 4
```

## 配乐与混音（按《配乐规范》）

1. `musicgen_gen.py`：facebook/musicgen-stereo-medium，按层生成 22–25 秒片段，每层 2–3 版（同一批次）。
2. `music_select.py --asr`：1–4 kHz 能量占比、瞬态密度、响度起伏、断音/削波，以及“音乐里有没有人声”（ASR），选最不抢人声的一版；同调性的其他版本用来轮换，避免听出循环。
3. `music_build.py`：铺底（开场—雅典）→ 推进（招聘机器—AI 时代）→ 高潮（1788—今天的办法，总结句后旁白停 2 秒）→ 结尾钢琴独奏；段落间 3 秒等功率交叉淡化，淡入 2 秒、淡出 3 秒。
4. `final_mix.py`：音乐 volume → 3 kHz −4 dB → 侧链压缩（threshold 0.02 / ratio 10 / attack 15 ms / release 500 ms，由旁白触发）→ 与旁白、音效 amix → 两遍 loudnorm（−16 LUFS，TP −1.5 dBTP，LRA 11）。音乐音量自动迭代到“有旁白时比人声低 16.5 dB 左右”。
5. `checks.py`：纯人声 / 加配乐 / 模拟手机外放三种情况的 ASR 对比，音乐突然冒出来的位置，导出高潮段单听。

**授权提醒**：MusicGen 权重是 CC-BY-NC-4.0（不可商用）。商业发布请用 `*_nomusic.mp4`，再在视频号里加音乐库配乐（音量 15–25%）。

## 授权

- Qwen3-TTS（VoiceDesign / Base）：Apache-2.0；Kokoro-82M：Apache-2.0；faster-whisper / Whisper large-v3：MIT。
- 字体：Noto Sans/Serif CJK、IM Fell English、JetBrains Mono，均为 SIL Open Font License。
