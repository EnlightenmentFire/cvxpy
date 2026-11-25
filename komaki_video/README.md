# 小牧长久手之战（打输了一仗，怎样赢下整局）· 制作工程

“从无名小卒到天下人”系列。微信视频号竖屏（1080×1920，25 fps）。画面、配乐、音效全部由程序生成；旁白为 Qwen3-TTS（Apache-2.0）克隆的“托克维尔”设计音色（参考音频 A0b，18 秒；与 `claude/tocqueville-america-video-a250yg` 分支同一参考）。工程骨架沿用滑铁卢一期（`claude/cool-hopper-cemgi0`）。

| 文件 | 作用 |
|---|---|
| `script_data.py` | 全片脚本：15 场、105 句，每句带画面 cue；多音字的配音改写（乐田→勒田等）只进 TTS，不进字幕 |
| `tts_clone.py` | Qwen3-TTS 1.7B Base ICL 克隆，逐句合成；中位音高须在 85–105 Hz，不在就换 seed |
| `voice_post.py` | 去头尾静音、句内停顿 ≤0.4 s、rubberband R3 变速 1.13（保共振峰）、50 Hz 高通、−18 dBFS |
| `asr_check.py` | faster-whisper 回读，按无调拼音比对 |
| `fetch_dem.py` | 下载 Terrarium 高程瓦片（AWS 公开数据），拼出全国、近畿—东海、尾张—三河三张 DEM；Natural Earth 10 m 陆地多边形做海岸 |
| `geo.py` | 晕渲沙盘底图、地名坐标（示意）、河流 |
| `gfx.py` / `frame.py` | cairo 绘图工具；版式：系列名、章节标题、1584–1586 时间轴、字幕、引文卡、角标 |
| `illus.py` | 情景示意：足轻/骑马武者剪影、土垒与幟、杉林与雾、铁炮火光与硝烟、金扇马印、天守剪影 |
| `scenes.py` | 15 场动画：对峙齐射钩子、尾张地图推演（砦线、中入长蛇、尾随、截击）、全国盟友网、伊势转向、联盟断裂、引文卡 |
| `render.py` | 时间轴（按旁白实长排）、合成、4 进程并行渲染 |
| `music.py` | 原创配乐：D 小调带都节音阶色彩；太鼓、弦乐、圆号、尺八/筝点缀，外交段换拨弦与钟；fluidsynth + FluidR3_GM（MIT） |
| `sfx.py` | numpy 合成音效：风、旗帜、铁炮齐射、太鼓、法螺、马蹄、水、火、钟 |
| `mix.py` | 旁白轨、配乐侧链压低（说话时约 −21 dB）、音效，两遍 loudnorm 到 −15 LUFS / −1.5 dBTP；含配乐和无配乐两版；mux 时 aresample=async=1 |
| `cover.py` | 封面 9:16 与 3:4 |
| `FACTCHECK.md` / `PUBLISH.md` | 引文与史实核对；标题、简介、话题 |

重建顺序：
```bash
python fetch_dem.py
python tts_clone.py && python voice_post.py 1.13 && python asr_check.py small
python render.py timeline && python render.py video 4
python music.py && python sfx.py && python mix.py stems && python mix.py mix
python mix.py mux out_music.mp4 out_nomusic.mp4
python cover.py
```
