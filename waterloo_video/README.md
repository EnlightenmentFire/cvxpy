# 滑铁卢（拿破仑最后一天的调兵）· 制作工程

微信视频号竖屏（1080×1920，25 fps）。画面、配乐、音效全部由程序生成；旁白为 Qwen3-TTS（Apache-2.0）克隆的“托克维尔”设计音色（参考音频 A0b，18 秒；与 `claude/tocqueville-america-video-a250yg` 分支同一参考）。

| 文件 | 作用 |
|---|---|
| `script_data.py` | 全片脚本：19 场、144 句，每句带画面 cue |
| `tts_clone.py` | Qwen3-TTS 1.7B Base ICL 克隆，逐句合成，中位音高须在 85–105 Hz，不在就换 seed |
| `voice_post.py` | 去头尾静音、句内停顿 ≤0.4 s、rubberband R3 变速 1.15（保共振峰）、50 Hz 高通、−18 dBFS |
| `asr_check.py` | faster-whisper 回读，按无调拼音比对 |
| `gfx.py` / `frame.py` | cairo 绘图工具；版式：标题、贯穿全片的时间轴、字幕、引文卡、角标 |
| `geo.py` | 地图数据（经纬度近似，示意）和晕渲底图：比利时战役图、圣让山战场图 |
| `illus.py` | 情景示意：黄昏山坡与近卫军剪影、雨夜泥地炮车、信使、空山 |
| `scenes.py` | 19 场的动画（地图推演箭头、方阵俯视、士气网络、机制图解、引文卡） |
| `render.py` | 时间轴（按旁白实长排）、合成、4 进程并行渲染 |
| `music.py` | 原创配乐：D 小调，鼓、号角、弦乐，每场按情绪生成，fluidsynth + FluidR3_GM（MIT） |
| `sfx.py` | numpy 合成音效：开场鼓+炮、雨、马蹄、齐射、炮声、风 |
| `mix.py` | 旁白轨、配乐侧链压低（说话时约 −21 dB）、音效，两遍 loudnorm 到 −15 LUFS / −1.5 dBTP；含配乐和无配乐两版；mux 时 aresample=async=1 |
| `cover.py` | 封面 9:16 与 3:4 |
| `FACTCHECK.md` | 引文与史实核对 |
| `PUBLISH.md` | 标题、简介、话题 |

成片与封面在仓库 `exports/32_waterloo/`。

重建顺序：
```bash
python tts_clone.py && python voice_post.py 1.15 && python asr_check.py small
python render.py timeline && python render.py video 4
python music.py && python sfx.py && python mix.py stems && python mix.py mix
python mix.py mux out_music.mp4 out_nomusic.mp4
```
