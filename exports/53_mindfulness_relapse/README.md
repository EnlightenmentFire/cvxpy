# 第 53 期《抑郁好了以后，为什么还会回来？》（佛法与心智 · 静坐的科学之二）

微信视频号竖屏视频，1080×1920，25 fps，H.264 + AAC。画面、配乐、音效全部由代码生成；旁白为托克维尔声音（Qwen3-TTS-12Hz-1.7B-Base，ICL 克隆设计音色参考 `voice_design_reference`，与 tocqueville 分支同一参考与同一参考文本），在本云端会话 CPU 上逐句生成。

## 目录

| 文件 | 说明 |
|---|---|
| `53_抑郁好了以后为什么还会回来.mp4` | 成片（含底乐，-15 LUFS） |
| `53_抑郁好了以后为什么还会回来_无配乐.mp4` | 无配乐备用版（旁白＋音效） |
| `cover.png` / `cover_3x4.png` | 封面 |
| `PUBLISH.md` | 发布包：标题候选、简介、话题、标识与授权说明 |
| `FACTCHECK.md` | 逐条核对（PubMed 摘要、CBETA 经文、NICE 原页） |
| `QC.md` | 自检结果：时长、响度、音画同步、ASR 回读 |
| `narration.srt` | 字幕（成片时间轴） |
| `sentences.json` / `sentences.txt` | 逐句旁白稿（含每句起止时间），可在 box 上重配后按时间轴回填 |
| `src/` | 全部制作脚本 |

## 制作脚本（src/）

| 脚本 | 作用 |
|---|---|
| `script_data.py` | 全片旁白（送 TTS 文字 / 字幕文字 / 场景） |
| `tts_clone.py` | Qwen3-TTS 逐句克隆；中位音高须在 85–105 Hz，否则换 seed |
| `voice_post.py` | 去首尾静音、句内停顿 ≤0.42 s、rubberband 变速（旁白 1.16×、古文 1.0×，保共振峰）、50 Hz 高通、RMS 归一 |
| `asr_check.py` | faster-whisper large-v3-turbo 回读，按无调拼音比对 |
| `timeline.py` | 按实际句长排时间轴：句间 0.50 s，换场多停 0.45 s |
| `engine.py` `rain.py` `water.py` `scenes.py` `scenes_ep.py` | 画面：雨窗（折射水珠、细流、剪影呼吸、台灯）、水面涟漪、宣纸立轴、水墨箭、森林图等 |
| `film.py` `render.py` | 合成每帧（转场、字幕、AI 配音角标），4 进程并行渲染 |
| `music.py` | 原创配乐（古琴式拨弦、磬、箫、低音铺底＋合成混响）与音效（雨声、水滴） |
| `mix.py` | 按时间轴压低底乐（说话时低于人声约 21 dB，长停顿处抬 4 dB），两遍 loudnorm 到 -15 LUFS / -1.5 dBTP |
| `final_mux.py` | 两遍 x264 控制体积 <100 MB；`aresample=async=1`；ffprobe 核对音视频时长差 ≤0.1 s |
| `cover.py` `export_text.py` | 封面、字幕与逐句稿导出 |

复现顺序：`tts_clone.py → voice_post.py 1.16 1.0 → timeline.py → music.py → mix.py → render.py 4 → final_mux.py`。
