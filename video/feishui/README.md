# 淝水之战（八十万为什么一哄而散）— 视频号竖屏

1080×1920 / 25 fps / H.264 + AAC 128k，约 14 分 35 秒。成片与发布包在仓库 `exports/30_feishui/`。

## 流程

```bash
bash fetch_fonts.sh                                   # 思源宋体/黑体（OFL）
python3 src/terrain.py                                # 高程晕渲底图（AWS Terrain Tiles）+ Natural Earth 河流
python src/tts.py                                     # Qwen3-TTS-12Hz-1.7B-Base ICL 克隆「托克维尔」旁白，逐句；音高 82–108 Hz 门限
python src/regen.py id:必含词 ...                     # 个别句换 seed 重配，ASR 通过才保留
python src/voice_post.py                              # 去静音、停顿≤0.4 s、rubberband 变速（旁白 1.12×、古文 1.02×）、-18 dBFS
python src/asr_check.py proc                          # faster-whisper 回读，按无调拼音比对
python src/build_timeline.py                          # 每句真实时长 → src/timeline.json（画面、字幕全挂在上面）
python3 src/music.py                                  # 原创配乐：按时间轴生成 MIDI，FluidSynth + FluidR3_GM 渲染
python src/mix.py                                     # 旁白 + 配乐（说话时低 21 dB）+ 合成音效 → -15 LUFS / -1.5 dBTP；另出无配乐版
./render.sh                                           # Playwright 抓帧（Canvas，画面是时间 t 的纯函数）
./encode.sh mix.wav out.mp4                           # 两遍编码，CFR，aresample=async=1
python src/qa.py out.mp4 qa/                          # 规格、音画时长差、响度、首/中/尾对齐抽查
```

## 文件

| 文件 | 作用 |
|---|---|
| `src/script_data.py` | 全片旁白（数据）：字幕文本、朗读文本、出处、停顿、画面提示 |
| `src/core.js` `props.js` `geo.js` `scenes_a.js` `scenes_b.js` `main.js` | 画面引擎与 7 段场景；`scenes_b.js` 里是淝水崩溃的粒子仿真（有序后撤 → 局部误读的级联 → 「秦兵敗矣」后的溃奔） |
| `史实核对.md` | 引文逐字核对与史料差异 |
| `发布包.md` | 标题、简介、话题、标识说明 |

## 素材与许可

| 素材 | 来源 | 许可 |
|---|---|---|
| 旁白 | Qwen3-TTS（Apache-2.0）克隆设计音色（非真人） | 可商用；发布时勾选 AI 生成内容 |
| 配乐 | 本项目代码作曲，FluidR3_GM 音色库渲染 | 音色库 MIT；乐曲原创 |
| 音效 | numpy 合成 | 自制 |
| 字体 | Noto Serif SC / Noto Sans SC | SIL OFL 1.1 |
| 地形 | AWS Terrain Tiles（SRTM 等公有领域数据）；Natural Earth 河流（公有领域） | 开放数据 |
