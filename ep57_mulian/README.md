# 第 57 期 目连救母与盂兰盆 · 制作工程

微信视频号竖屏视频（1080×1920，25 fps）。画面、配乐、音效全部由本目录代码生成；配音用 Qwen3-TTS（Apache-2.0）克隆托克维尔设计音色（参考音频即 A0b，18 秒，与 tocqueville 分支 `preview/voice_design_reference.m4a` 同一条）。

| 文件 | 作用 |
|---|---|
| `src/script_data.py` | 全片旁白（每句：朗读文本、字幕、所属镜头、停顿） |
| `src/tts_clone.py` | Qwen3-TTS Base ICL 克隆，逐句合成，中位音高须在 82–108 Hz（CPU） |
| `src/voice_post.py` | 去头尾静音、句内停顿 ≤0.38 s、rubberband R3 保共振峰变速（旁白 1.10、经文 1.00）、高通、归一 |
| `src/asr_check.py` | faster-whisper small 逐句回读，按无调拼音比对 |
| `src/art.py` / `src/scenes.py` | 程序绘画工具与 50 余个镜头（水墨夜景、敦煌矿物色、剪影、灯火、经文竖排卡） |
| `src/render.py` | 时间线、字幕切分、转场、四进程分段渲染 |
| `src/music.py` | 原创配乐（古琴拨弦合成、泛音、箫、磬、低音铺底，D 羽调五声）＋音效（开场磬声钩子、火、雨、水） |
| `src/mix.py` | 人声下 −21 dB（说话时）/ −17 dB（停顿 ≥0.8 s）的配乐跟随混音 |
| `src/build_final.sh` | 两遍 loudnorm 到 −15 LUFS / −1.5 dBTP；两遍 x264 控制在 100 MB 内；带配乐版与无配乐版 |
| `src/cover.py` / `src/make_exports.py` | 封面、sentences.json/txt、SRT、脚本、发布包 |
| `FACTCHECK.md` | 核实记录 |

字体（SIL OFL）：思源宋体 Noto Serif CJK SC、霞鹜文楷 LXGW WenKai、马善政 Ma Shan Zheng。
