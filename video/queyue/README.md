# 却月阵（义熙十三年，417）— 视频号竖屏短片

1080×1920 / 30fps / H.264 + AAC，约 5 分 49 秒。成片：`out/queyue_1080x1920.mp4`；逐段旁白稿：`旁白稿.md`。

## 目录
- `src/script.py` 旁白稿（含仅供 TTS 用的同音替换表，字幕不受影响）
- `src/tts.py` 逐句合成旁白 → `audio/lines/`；`src/asr_check.py` 语音识别回检读音
- `src/build_timeline.py` 由每句音频时长生成 `src/timeline.json`（所有画面都挂在这条时间轴上）
- `src/audio.py` 合成配乐、音效并混音 → `audio/mix.wav`
- `src/terrain.py` 生成底图（`assets/macro.jpg` 真实高程晕渲；`assets/tactical.jpg` 程序生成的河岸）
- `src/core.js / geo.js / battle.js / scenes_a.js / scenes_b.js / film.html` Canvas 动画，画面是时间 t 的纯函数
- `src/shoot.js`、`render.sh`、`encode.sh` 抓帧与编码

## 重新生成
```bash
bash fetch_fonts.sh                      # 思源宋体 / 思源黑体（OFL）
python3 src/terrain.py                   # 底图（需联网取高程瓦片）
python src/tts.py zm_034 1.34 1.16       # 需 kokoro>=0.9.4、misaki[zh]（Python 3.12）
python3 src/build_timeline.py && python src/audio.py
./render.sh && ./encode.sh
```
自己录音：按 `旁白稿.md` 的行号录成 `audio/lines/000.wav…`，再从 `build_timeline.py` 起重跑即可，画面会按新的时长自动重排。

## 素材与许可
| 素材 | 来源 | 许可 |
|---|---|---|
| 旁白 | Kokoro-82M-v1.1-zh（hexgrad），音色 `zm_034` | Apache-2.0（模型与音色权重），可商用 |
| 配乐、音效 | `src/audio.py` 用 numpy 合成 | 自制，无第三方素材 |
| 字体 | Noto Serif SC / Noto Sans SC | SIL OFL 1.1，可商用 |
| 地形 | Mapzen/AWS Terrain Tiles（SRTM 等公有领域高程数据）晕渲 | 开放数据；署名见片尾“说明” |
| 动画、图示 | 本仓库代码绘制 | 自制 |

## 史料与取舍
引文、人数、日期均据《宋书》（武帝纪、朱龄石传附朱超石传、刘康祖传、王弘传、庐陵王义真传）、《魏书》（太宗纪、崔浩传、长孙嵩传）、《资治通鉴》卷 117、118、125 原文核对，详见 `史实核对.md`。
