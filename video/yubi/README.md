# 孤城 · 第二集《玉璧》（韦孝宽守玉璧，546）— 视频号竖屏短片

1080×1920 / 30fps / H.264 + AAC，约 6 分 22 秒。成片：`out/yubi_1080x1920.mp4`；逐段旁白稿：`旁白稿.md`；史料核对：`史实核对.md`。

## 目录
- `src/script.py` 旁白稿（含仅供 TTS 用的同音替换表，字幕不受影响）
- `src/tts.py` 逐句合成旁白 → `audio/lines/`；`tools/asr_check.py` 用语音识别回检读音；`tools/g2p_dump.py` 打印注音；`tools/voice_scan.py` 45 个男声的音高与读音对比；`tools/sample.py` 冷启动样音
- `src/build_timeline.py` 由每句音频时长生成 `src/timeline.json`（全部画面都挂在这条时间轴上）
- `src/sound.py` 音色库（鼓、弦乐、拨弦、风、箭、纸、火、塌墙，全部 numpy 合成）；`src/audio.py` 配乐、音效与混音 → `audio/mix.wav`（−16 LUFS）
- `src/terrain.py` 底图：`assets/macro.jpg`（东西魏形势，真实高程晕渲）、`assets/local.jpg`（玉璧一带真实高程）；`src/rivers.py` 河道（Natural Earth；本地汾河取谷底线）
- `src/core.js / geo.js / scenes_a.js / scenes_b.js / scenes_c.js / film.html` Canvas 动画，画面是时间 t 的纯函数
- `src/shoot.js`、`render.sh`、`encode.sh` 抓帧与两遍编码

## 重新生成
```bash
bash fetch_fonts.sh                          # 思源宋体 / 思源黑体（OFL）
python3 src/terrain.py && python3 src/rivers.py   # 底图（需联网取高程瓦片）
python src/tts.py zm_029 1.4 1.18            # 需 kokoro>=0.9.4、misaki[zh]（Python 3.12）
python3 src/build_timeline.py && python src/audio.py
./render.sh && BR=1650k ./encode.sh
```
换声音：把 `zm_029` 换成 `zm_034`（「却月阵」同款）或 `zm_014`（兵法系列同款），语速相应调高一点即可，画面按新时长自动重排。
自己录音：按 `旁白稿.md` 的行号录成 `audio/lines/000.wav…`，从 `build_timeline.py` 起重跑。

## 素材与许可
| 素材 | 来源 | 许可 |
|---|---|---|
| 旁白 | Kokoro-82M-v1.1-zh（hexgrad），音色 `zm_029` | Apache-2.0，可商用 |
| 配乐、音效 | `src/audio.py`、`src/sound.py` 用 numpy 合成 | 自制，无第三方素材 |
| 字体 | Noto Serif SC / Noto Sans SC | SIL OFL 1.1，可商用 |
| 地形 | AWS Terrain Tiles（SRTM 等公有领域高程数据） | 开放数据 |
| 河道 | Natural Earth 10m | 公有领域 |
| 遗址位置 | OpenStreetMap「玉壁城遗址」 | ODbL（仅取坐标） |
| 动画、图示 | 本目录代码绘制 | 自制 |

## 史料
《周书》卷三十一（今本据《北史》补）、卷十八；《北齐书》卷一、二、十七、三十九；《资治通鉴》卷一百五十八至一百六十、一百七十一；《乐府诗集》卷八十六。逐条对照见 `史实核对.md`。
