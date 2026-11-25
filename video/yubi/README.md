# 孤城 · 第二集《玉璧》（韦孝宽守玉璧，546）— 视频号竖屏短片

1080×1920 / 30fps / H.264 + AAC，8 分 09 秒（按用户要求保留全部细节）。成片：`out/yubi_1080x1920.mp4`（含配乐，95.7 MB）；无配乐版用 `out/yubi_无配乐_音轨.m4a` 换音轨即得（见下）；逐段旁白稿：`旁白稿.md`；史料核对：`史实核对.md`。

## 目录
- `src/script.py` 旁白稿（含仅供 TTS 用的同音替换表，字幕不受影响）
- 旁白（Qwen3-TTS）：`tools/qwen_design.py` 按文字描述设计参考音（3 个候选，选中位音高约 90 Hz 的）→ `tools/qwen_clone.py` 用 Base 模型克隆、逐句合成，逐句量音高（85–105 Hz，超出换 seed）、句内停顿压到 0.4 秒、50 Hz 高通 → `tools/stretch_lines.py` 旁白用 rubberband 保留共振峰提速 1.12 倍 → `audio/lines_qwen_s/`；`tools/asr_lines.py` 逐句语音识别回读
- 备选（Kokoro）：`tools/kokoro_stretch.py` 按 1.0 倍合成再用 rubberband 拉速；早期版本用的 `src/tts.py`（Kokoro 自带变速）已不再使用
- `tools/excerpt.py` 1 分钟样音；`tools/voice_scan.py` Kokoro 45 个男声的音高与读音对比
- `src/build_timeline.py` 由每句音频时长生成 `src/timeline.json`（全部画面都挂在这条时间轴上）
- 配乐（按《配乐规范》）：`tools/musicgen_gen.py` 用 MusicGen（facebook/musicgen-stereo-medium）按层生成候选（铺底 / 推进 / 紧鼓 / 哀段 / 沉思 / 尾声，每层 2–3 版；伍段高潮由推进段“续写”出 2 版、玖段 1 版），同一段内用续写接长、不循环（续写接缝与重新解码的提示段做 0.5 秒交叉）；`tools/music_pick.py` 给候选打分（响度、1–4 kHz 占比、调性、有无人声）并出梅尔谱总览；`src/score.py` 按时间轴拼接（段落之间 2–4 秒交叉淡化，高潮最响处对准旁白留白）→ `audio/music.wav`
- `src/sound.py` 音效库（鼓、风、箭、纸、火、塌墙，全部 numpy 合成）；`src/audio.py` 旁白 + 音效 + 配乐，按规范侧链混音 → `audio/mix.wav`（-16 LUFS、真峰值 ≤ -1.5 dBTP；有旁白时音乐约低 15–18 dB，停顿时回升；音乐与音效整体晚 80 毫秒进压缩器，相当于侧链前瞻，句首第一个字不被盖住）；另出无配乐版 `audio/mix_nomusic.wav`；`tools/mix_sections.py` 分段核对电平
- `tools/asr_mix.py` 成片整体语音识别回读（可模拟手机外放），对比纯人声与加配乐后的误读率
- `src/terrain.py` 底图：`assets/macro.jpg`（东西魏形势，真实高程晕渲）、`assets/local.jpg`（玉璧一带真实高程）；`src/rivers.py` 河道（Natural Earth；本地汾河取谷底线）
- `src/core.js / geo.js / scenes_a.js / scenes_b.js / scenes_c.js / film.html` Canvas 动画，画面是时间 t 的纯函数
- `src/shoot.js`、`render.sh`、`encode.sh` 抓帧与两遍编码

## 重新生成
```bash
bash fetch_fonts.sh                          # 思源宋体 / 思源黑体（OFL）
python3 src/terrain.py && python3 src/rivers.py   # 底图（需联网取高程瓦片）
python tools/qwen_design.py cache/qwen_ref    # 需 qwen-tts、praat-parselmouth（Python 3.12）
LINES_DIR=audio/lines_qwen python tools/qwen_clone.py cache/qwen_ref
python tools/stretch_lines.py audio/lines_qwen audio/lines_qwen_s 1.12 1.0
export LINES_DIR=audio/lines_qwen_s && python3 src/build_timeline.py
# 配乐：按下面的顺序（批次组成和 seed 不变，CPU 上结果可复现），每条的提示词、seed、续写来源记在 cache/music/log.json
python tools/musicgen_gen.py gen bed:3,coda:2,reflect:2 30 1
python tools/musicgen_gen.py gen build:5,drive:2 30 2
python tools/musicgen_gen.py gen lament:3 30 3
python tools/musicgen_gen.py cont "build_s2_4.wav:build:25,build_s2_0.wav:build:22,bed_s1_1.wav:bed:27,drive_s2_1.wav:drive:30" 4 6
python tools/musicgen_gen.py cont "build_s2_4+build4.wav:climax:30,build_s2_4+build4.wav:climax:30,build_s2_0+build4.wav:climax:30,build_s2_3.wav:build:20" 5 6
ffmpeg -i cache/music/lament_s3_1.wav -af "rubberband=tempo=0.75:window=long:transients=smooth:detector=soft:pitchq=quality" -c:a pcm_f32le cache/music/lament_s3_1_x075.wav
python tools/music_pick.py bed_ build_ …                         # 打分挑版本，选定的写进 src/score_clips.json
MUSIC_DB=4.5 python src/score.py && MUSIC_DB=4.5 python src/audio.py nomusic   # 拼配乐 → 侧链混音（含无配乐版）
python tools/mix_sections.py && python tools/asr_mix.py audio/mix.wav && python tools/asr_mix.py audio/mix.wav phone
./render.sh && ./encode.sh                   # 码率按时长自动算，控制在 100MB 以内
# 无配乐版（发布时可用视频号音乐库另配）：
ffmpeg -i out/yubi_1080x1920.mp4 -i out/yubi_无配乐_音轨.m4a -map 0:v -map 1:a -c copy -movflags +faststart out/yubi_1080x1920_无配乐.mp4
```

## 配乐（按《配乐规范》）
题材情绪：战争 / 守城一类——低音弦乐长音铺底 + 太鼓 + 埙（或古琴）主音色，D 小调一带，60–80 BPM。三层起伏与选用片段：

| 段落 | 层 | 片段（cache/music/） | 来源 |
|---|---|---|---|
| 冷启动 | 铺底 | `coda_s1_0` | 埙独奏提示词生成 30 秒（与片尾的埙首尾呼应） |
| 片名—壹 | 铺底 | `bed_s1_1+bed4` | 暗色长音 pad 生成 30 秒 + 续写 27 秒 |
| 贰 | 推进 | `build_s2_3+build5` | 低音弦乐固定音型 + 慢太鼓（A 小调）生成 30 秒 + 续写 20 秒 |
| 叁 | 推进 | `build_s2_1` | 同上提示词另一版（C） |
| 肆 | 紧鼓 | `drive_s2_1+drive4` | 80 BPM 紧太鼓 + 快速低音弦乐（F）30 秒 + 续写 30 秒 |
| 伍 | 推进→高潮 | `build_s2_4+build4+climax5v1` | 推进（D 小调）30 + 续写 25 秒，再用规范的“悲壮战争”提示词续写 30 秒（2 版取 v1）；最响处对准“人人有了拼死的心”后的 2 秒留白 |
| 陆 | 回落（哀段） | `lament_s3_1` 放慢 0.75 倍 | 低音弦乐 + 埙的哀段（G 小调），无鼓，rubberband 拉长到 40 秒 |
| 柒 | 回落 | `lament_s3_2` | 哀段另一版；《敕勒歌》前 0.6 秒收掉，只留风声，直到捌的章节卡 |
| 捌 | 回落（沉思） | `reflect_s1_0` | 低音弦乐 pad + 古琴（D 小调） |
| 玖 | 再起 | `build_s2_0+build4+climax5` | 推进（C）30 + 续写 22 秒，再用“悲壮战争”提示词续写 30 秒；“此人若在”后的约 2.8 秒留白处抬起 |
| 拾—片尾 | 收尾 | `coda_s1_1` | 埙独奏，余音进片尾，结尾淡出 3 秒后黑场 |

段落之间 2–3 秒等功率交叉淡化（多在章节卡的鼓点上）；片段先各自统一到 -20 LUFS，再把 3 秒短时响度向 -20 LUFS 拉回 60%，层次由 `src/score.py` 里的段落增益曲线给出；玖段约 441–444 秒片段里的一次镲声局部压低 5 dB。

混音实测（`cache/mix_report.json`；成片 AAC 解码后复测）：整体 -16.0 LUFS、真峰值 -1.8 dBTP（无配乐版 -2.1）、LRA 3.6；有旁白时音乐（含音效）比人声低：中位 18.0 dB（推进 / 高潮各段约 16.5–18 dB，铺底各段 17.7–20.7 dB）；伍段高潮留白处音乐比人声整体响度低 3.1 dB（比压在旁白下时抬起约 15 dB），拾前留白低 3.4 dB。
整片语音识别（faster-whisper small，按拼音比对，成片音轨）：纯人声 1.02%，成片 0.97%；模拟手机外放（单声道、300 Hz–7 kHz）纯人声 0.86%，成片 1.08%。
换声音：任何逐句音频目录都可以通过 `LINES_DIR` 接进来，画面按新时长自动重排。
自己录音：按 `旁白稿.md` 的行号录成 `audio/lines/000.wav…`，从 `build_timeline.py` 起重跑。

## 素材与许可
| 素材 | 来源 | 许可 |
|---|---|---|
| 旁白 | Qwen3-TTS-12Hz-1.7B-VoiceDesign 按文字描述设计参考音，Qwen3-TTS-12Hz-1.7B-Base 克隆合成（不克隆任何真人） | Apache-2.0，可商用 |
| 配乐 | MusicGen（facebook/musicgen-stereo-medium，本地生成，见 `cache/music/log.json`） | **模型权重为 CC BY-NC 4.0（非商用）**。账号如有商业用途，请用无配乐版，发布时从视频号音乐库另配（音量 15–25%） |
| 音效 | `src/audio.py`、`src/sound.py` 用 numpy 合成 | 自制，无第三方素材 |
| 字体 | Noto Serif SC / Noto Sans SC | SIL OFL 1.1，可商用 |
| 地形 | AWS Terrain Tiles（SRTM 等公有领域高程数据） | 开放数据 |
| 河道 | Natural Earth 10m | 公有领域 |
| 遗址位置 | OpenStreetMap「玉壁城遗址」 | ODbL（仅取坐标） |
| 动画、图示 | 本目录代码绘制 | 自制 |

## 史料
《周书》卷三十一（今本据《北史》补）、卷十八；《北齐书》卷一、二、十七、三十九；《资治通鉴》卷一百五十八至一百六十、一百七十一；《乐府诗集》卷八十六。逐条对照见 `史实核对.md`。
