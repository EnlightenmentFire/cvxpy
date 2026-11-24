# 孤城 · 第二集《玉璧》（韦孝宽守玉璧，546）— 视频号竖屏短片

1080×1920 / 30fps / H.264 + AAC，约 8 分钟（按用户要求保留全部细节）。成片：`out/yubi_1080x1920.mp4`；逐段旁白稿：`旁白稿.md`；史料核对：`史实核对.md`。

## 目录
- `src/script.py` 旁白稿（含仅供 TTS 用的同音替换表，字幕不受影响）
- 旁白（Qwen3-TTS）：`tools/qwen_design.py` 按文字描述设计参考音（3 个候选，选中位音高约 90 Hz 的）→ `tools/qwen_clone.py` 用 Base 模型克隆、逐句合成，逐句量音高（85–105 Hz，超出换 seed）、句内停顿压到 0.4 秒、50 Hz 高通 → `tools/stretch_lines.py` 旁白用 rubberband 保留共振峰提速 1.12 倍 → `audio/lines_qwen_s/`；`tools/asr_lines.py` 逐句语音识别回读
- 备选（Kokoro）：`tools/kokoro_stretch.py` 按 1.0 倍合成再用 rubberband 拉速；早期版本用的 `src/tts.py`（Kokoro 自带变速）已不再使用
- `tools/excerpt.py` 1 分钟样音；`tools/voice_scan.py` Kokoro 45 个男声的音高与读音对比
- `src/build_timeline.py` 由每句音频时长生成 `src/timeline.json`（全部画面都挂在这条时间轴上）
- `src/sound.py` 音色库（鼓、弦乐、拨弦、风、箭、纸、火、塌墙，全部 numpy 合成）；`src/audio.py` 配乐、音效与混音 → `audio/mix.wav`（人声约 −18 dBFS RMS，音乐在人声下自动压低）
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
export LINES_DIR=audio/lines_qwen_s && python3 src/build_timeline.py && python src/audio.py
./render.sh && ./encode.sh                   # 码率按时长自动算，控制在 100MB 以内
```
换声音：任何逐句音频目录都可以通过 `LINES_DIR` 接进来，画面按新时长自动重排。
自己录音：按 `旁白稿.md` 的行号录成 `audio/lines/000.wav…`，从 `build_timeline.py` 起重跑。

## 素材与许可
| 素材 | 来源 | 许可 |
|---|---|---|
| 旁白 | Qwen3-TTS-12Hz-1.7B-VoiceDesign 按文字描述设计参考音，Qwen3-TTS-12Hz-1.7B-Base 克隆合成（不克隆任何真人） | Apache-2.0，可商用 |
| 配乐、音效 | `src/audio.py`、`src/sound.py` 用 numpy 合成 | 自制，无第三方素材 |
| 字体 | Noto Serif SC / Noto Sans SC | SIL OFL 1.1，可商用 |
| 地形 | AWS Terrain Tiles（SRTM 等公有领域高程数据） | 开放数据 |
| 河道 | Natural Earth 10m | 公有领域 |
| 遗址位置 | OpenStreetMap「玉壁城遗址」 | ODbL（仅取坐标） |
| 动画、图示 | 本目录代码绘制 | 自制 |

## 史料
《周书》卷三十一（今本据《北史》补）、卷十八；《北齐书》卷一、二、十七、三十九；《资治通鉴》卷一百五十八至一百六十、一百七十一；《乐府诗集》卷八十六。逐条对照见 `史实核对.md`。
