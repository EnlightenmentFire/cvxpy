# 52 · 打坐让人幸福，证据到底有多硬？（静坐的科学 · 一）

| 文件 | 说明 |
| --- | --- |
| `打坐让人幸福证据到底有多硬.mp4` | 成片（含原创配乐） |
| `打坐让人幸福证据到底有多硬_无配乐版.mp4` | 无配乐版（保留开场磬声与手机提示音） |
| `封面_9x16.png` / `封面_3x4.png` | 封面 |
| `publish.md` | 标题、简介、话题、发布设置与自检数据 |
| `FACTCHECK.md` | 逐条核实记录（论文原文 / PubMed / CBETA） |
| `打坐让人幸福证据到底有多硬.srt` | 字幕 |
| `sentences.json` / `sentences.txt` | 逐句旁白稿（含时间码），可在 box 上重配 |
| `audio_report.json` | 混音测量 |
| `src/` | 全部生成脚本（画面、配乐、配音、混音、封面） |

重做步骤：`tts_clone.py` → `voice_post.py --tempo 1.12` → `build_timeline.py` → `asr_check.py proc` → `music.py` → `final_mux.py audio` → `render.py chunk i 4`（i=0..3）→ `final_mux.py video <dir> <stem>`。依赖：qwen-tts 0.1.1（torch/torchaudio 2.11 CPU）、Qwen3-TTS-12Hz-1.7B-Base、faster-whisper、jieba、cn2an、LXGW WenKai 与 Noto Serif SC 字体。
