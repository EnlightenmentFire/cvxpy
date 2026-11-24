# 孤城 · 壹　毛德祖守虎牢（417—423）— 视频号竖屏片

1080×1920 / 30fps / H.264 + AAC，11 分 20 秒，约 95MB。成片：`out/gucheng01_hulao_1080x1920.mp4`；逐句旁白稿：`旁白稿.md`；史料核对与取舍：`史实核对.md`；静帧：`out/stills/`。

系列沿用《却月阵》（`video/queyue`，另一分支）的做法：旁白逐句合成 → 由每句时长生成时间轴 → 画面是时间 t 的纯函数 → 抓帧编码。

## 目录
- `src/script.py` 旁白稿。`LEX` 是给 TTS 用的读音表（多音字、文言读法），不影响字幕
- `src/tts.py` 逐句合成 → `audio/lines/`；`src/g2p_check*.py` 列出多音字的实际注音；`src/asr_check.py` 语音识别回检
- `src/build_timeline.py` 由每句音频时长生成 `src/timeline.json`
- `src/audio.py` 合成配乐、环境声并混音 → `audio/mix.wav`
- `src/terrain.py` 生成四张地形底图（全图、关中、河洛、虎牢近景）
- `src/core.js geo.js kit.js scenes_a.js scenes_b.js scenes_c.js main.js film.html` Canvas 动画。场景用句首文字做时间锚点（`AT('……')`），稿子改字数不会串位
- `src/shoot.js`、`render.sh`、`encode.sh` 抓帧与编码；`src/review2.js` 低清巡检
- `sources/` 核对用的史书原文

## 重新生成
```bash
bash fetch_fonts.sh                          # 思源宋体 / 思源黑体（OFL）
python3 src/terrain.py                       # 底图（需联网取高程瓦片）
python src/tts.py zm_034 1.34 1.16           # 需 kokoro>=0.9.4、misaki[zh]（Python 3.12）
python3 src/build_timeline.py && python src/audio.py
./render.sh && ./encode.sh
```
自己录音：按 `旁白稿.md` 的行号录成 `audio/lines/000.wav … 122.wav`，从 `build_timeline.py` 起重跑，画面按新时长自动重排。

## 素材与许可
| 素材 | 来源 | 许可 |
|---|---|---|
| 旁白 | Kokoro-82M-v1.1-zh（hexgrad），音色 `zm_034` | Apache-2.0（模型与音色权重），可商用 |
| 配乐、环境声 | `src/audio.py` 用 numpy 合成 | 自制，无第三方素材 |
| 字体 | Noto Serif SC / Noto Sans SC | SIL OFL 1.1，可商用 |
| 地形 | Mapzen / AWS Terrain Tiles（SRTM 等开放高程数据）晕渲 | 开放数据；署名见片尾 |
| 动画、图示 | 本目录代码绘制 | 自制 |
