# 一个厂和一个国家——君津与宝钢（改革开放系列第 1 期）

微信视频号竖屏短片（1080×1920，30fps）的全部源文件。

- `script/旁白稿与史料核对.md`：旁白稿、出处、20 条史料核对表。先看这个。
- `script/script.py`：旁白定稿（字幕文本、停顿、出处），配音和画面都从这里取。
- `stills/`：送审静帧。`samples/`：样音和 30 秒样片。
- `tts/synth.py`：逐句合成旁白并生成时间轴 `render/timeline.js`。
- `audio/music.py`：合成配乐、环境声并混音。
- `render/`：画面（HTML + JS，每一帧都是时间的函数），`render.js` 逐帧截图送 ffmpeg。

## 重建

```bash
# 依赖：ffmpeg、Node + Playwright(Chromium)、Python 3.11（kokoro、misaki[zh]、soundfile、scipy）
# 字体（SIL OFL）：Noto Serif/Sans CJK SC、Barlow Condensed、IBM Plex Mono，装进系统字体目录
# 地图：Natural Earth ne_10m_land / ne_10m_rivers_lake_centerlines（公有领域）放 assets/geo/，再跑：
python3 assets/geo/make_map.py
python tts/synth.py voice=zm_033 speed=1.1     # 旁白 + 时间轴
python audio/music.py                          # 配乐 + 混音
node render/render.js stills 19.8,102 out/     # 出静帧
node render/render.js frames 0 12652 out.mp4   # 出全片画面
```
