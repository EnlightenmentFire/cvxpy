# 李斯——一只选对了粮仓的老鼠（视频号竖屏，1080×1920 / 30fps）

全片由代码生成，没有任何外部图片、音乐或视频素材。

| 部分 | 做法 | 许可 |
|---|---|---|
| 旁白 | Kokoro-82M v1.1-zh，男声 `zm_029`，逐句合成（`src/tts.py`） | 模型 Apache-2.0 |
| 画面 | HTML/SVG 动态图形，时间线驱动，Playwright 逐帧截图（`src/film.html` 等） | 原创；字体 Noto Serif/Sans SC（OFL） |
| 配乐音效 | numpy 现场合成：拨弦、钟、鼓、低音（`src/music.py`） | 原创 |

## 文件

- `旁白稿.md`　成片旁白；`src/script_data.py` 是唯一事实来源（含只影响读音的替换字）
- `SOURCES.md`　史料逐条核对，以及与任务单不一致之处
- `src/scenes_*.js`　十二段场景；`src/overlays.js` 字幕/章节签/官阶条；`src/map.js` 战国示意地图；`src/art.js` 手绘剪影
- `out/preview/`　样音与静帧

## 重建

```bash
npm i                      # 字体（@fontsource）
pip install "kokoro>=0.9" "misaki[zh]" soundfile scipy   # 另需 CPU 版 torch、ffmpeg、playwright+chromium
./build.sh                 # VOICE=zm_009 ./build.sh 可换声线；SKIP_TTS=1 只重渲画面
```

换成真人录音：按 `src/script_data.py` 的句子 id 存成 `build/tts/<名字>/<id>.wav`（24kHz 单声道），再 `SKIP_TTS=1 VOICE=<名字> ./build.sh`，画面和字幕会自动按新的时长对齐。
