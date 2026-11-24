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
| `audio/` | 声音：`synth.py` 合成乐器与音效、`plan.py` 每段的声音设计、`mix.py` 混音与压低音乐、`build_audio.py` |
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

## 授权

- Qwen3-TTS（VoiceDesign / Base）：Apache-2.0；Kokoro-82M：Apache-2.0；faster-whisper / Whisper large-v3：MIT。
- 字体：Noto Sans/Serif CJK、IM Fell English、JetBrains Mono，均为 SIL Open Font License。
