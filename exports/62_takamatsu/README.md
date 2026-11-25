# 高松城水攻（不攻城，造一片湖）· 制作工程与交付

从无名小卒到天下人（丰臣秀吉系列）。微信视频号竖屏 1080×1920，25 fps。**只交付，不发布、不上传。**

## 交付文件

| 文件 | 说明 |
| --- | --- |
| `高松城水攻_含配乐.mp4` | 成片（推荐）：旁白 + 原创配乐 + 音效 |
| `高松城水攻_无配乐.mp4` | 备用：旁白 + 音效 |
| `cover_1080x1920.png` / `cover_1080x1440_3x4.png` | 封面 9:16 / 3:4 |
| `PUBLISH.md` | 发布包：标题三选一、一句话简介与话题、简介、声明 |
| `FACTCHECK.md` | 史料核对；【待核】项的处理 |
| `narration.srt` | 字幕（按实际配音时间） |
| `sentences.json` / `sentences.txt` | 逐句旁白稿（含每句起止秒），需要在 box 上重配时用 |
| `src/` | 全部源码（画面、配音、配乐、音效、混音） |

## 源码

| 文件 | 作用 |
| --- | --- |
| `script_data.py` | 全片脚本：16 场、102 句，每句带画面 cue；字幕可单独给阿拉伯数字写法 |
| `tts_clone.py` | Qwen3-TTS 1.7B Base ICL 克隆「托克维尔」设计音色（参考 A0b，18 秒），bf16 在 CPU（AMX）上约 4 倍实时；中位音高须在 85–105 Hz |
| `voice_post.py` | 去头尾静音、句内停顿 ≤0.4 s、rubberband R3 变速 1.15（保共振峰）、50 Hz 高通、−18 dBFS |
| `asr_check.py` | faster-whisper 回读，按无调拼音比对 |
| `world.py` | 高松城周边示意地形：高程、稻田、沼地、村落、城郭、堤、蓄水盆地；俯视与斜俯视（航拍感）两种机位；水位上涨按水深逐渐吞没 |
| `bigmap.py` | 日本西部大图（Natural Earth 海岸线，公有领域） |
| `scenes.py` | 16 场画面：开场洪水、沼城、筑堤、三次涨水、堤坝剖面、援军压境、机制图解、雷雨对峙、请信长亲征、谈判（演绎）、小舟、史料争议、收束 |
| `gfx.py` / `frame.py` / `render.py` | 绘图工具、版式（系列名、章节标题、旧历时间轴、字幕、角标、引文卡）、时间线与 4 进程渲染 |
| `music.py` | 原创配乐：太鼓、尺八、筝、弦乐、低音铜管，D 小调带都节音阶色彩；fluidsynth + FluidR3_GM（MIT） |
| `sfx.py` | numpy 合成音效：暴雨、洪水灌入、雷、铜钱、劳作人声、水声、火、风 |
| `mix.py` | 侧链压低配乐（说话时约 −21 dB），两遍 loudnorm 到 −15 LUFS / −1.5 dBTP；含配乐与无配乐两版；mux 时 aresample=async=1 |
| `cover.py` | 封面 |

重建顺序（WORK 默认 /tmp/claude-0/work）：

```bash
python tts_clone.py && python voice_post.py 1.15 && python asr_check.py small
python render.py timeline && python render.py video 4
python music.py && python sfx.py && python mix.py stems && python mix.py mix
python mix.py mux 高松城水攻_含配乐.mp4 高松城水攻_无配乐.mp4
```

## 自检结果

（见下方，由成片测得后填写）
