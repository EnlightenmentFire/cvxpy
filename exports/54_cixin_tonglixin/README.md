# 54 慈心禅与同理心 ·《太能共情的人，为什么最容易累垮？》制作工程

微信视频号竖屏（1080×1920，25 fps）。全部画面、音乐、音效均为程序生成（Python + Pillow + numpy），无第三方素材；
配音用 Qwen3-TTS-12Hz-1.7B-Base（Apache-2.0）克隆「托克维尔」设计音色（参考音频即托克维尔分支 `preview/voice_design_reference.m4a`，18 秒），CPU 合成。

| 文件 | 作用 |
| --- | --- |
| `script_data.py` | 全片脚本（场景、旁白、句后停顿） |
| `SCRIPT.md` | 带时间码的旁白稿（`gen_docs.py` 生成） |
| `sentences.json / .txt` | 逐句旁白稿（如需在盒子上重配） |
| `FACTCHECK.md` | 论文、数字、经文逐条核实记录 |
| `PUBLISH.md` | 发布包：标题、简介、话题、规格自检 |
| `art.py` / `scenes.py` | 画面引擎（宣纸、水墨、脑区示意、文字排版）与 33 个场景 |
| `render.py` | 时间线（由逐句配音时长生成）、字幕切分、合成、4 进程渲染 |
| `tts_clone.py` | Qwen3-TTS 克隆逐句合成；中位音高须在 85–105 Hz，否则换 seed |
| `voice_post.py` | 裁静音、句内停顿 ≤0.4 s、rubberband 统一变速（保共振峰）、-18 dBFS RMS |
| `asr_check.py` | faster-whisper medium 回读，按无调拼音逐句比对 |
| `music.py` | 原创底乐：古琴式拨弦、磬、箫、低音铺底（numpy 合成），开头一声磬作声音钩子 |
| `mix.py` | 旁白摆放、底乐随人声自动压低（约 -21 dB，停顿处抬 4 dB）、两遍 loudnorm 到 -15 LUFS / -1.5 dBTP |
| `final_mux.py` | 编码与合成两个版本（有配乐 / 无配乐），核对音画时长差 |
| `cover.py` | 封面 |

重建顺序：`tts_clone.py → voice_post.py → asr_check.py → render.py timeline → music.py → mix.py → render.py video → final_mux.py → cover.py → gen_docs.py`。
字体：Noto Serif SC / Noto Serif TC / Noto Sans SC（OFL），放在 `/tmp/claude-0/work/fonts/`。
