# 黄仁勋 01——先认错，再活下来

「黄仁勋的商业决断」第一期。视频号竖屏 1080x1920 / 30fps。

- `旁白稿.md` 旁白全文（含英文原话和出处）
- `出处核对.md` 逐条出处核对，以及和最初清单不一致的地方
- `stills/` 静帧；`samples/` 男声样音和 34 秒样片
- `src/script.py` 唯一的稿子来源；`src/tts.py` 配音；`src/music.py` 配乐与混音；`src/render/` 画面；`src/render.mjs` 逐帧渲染

## 重新生成

```bash
bash src/fetch_fonts.sh                       # 字体（OFL 许可）
python src/tts.py zm_011 1.08                 # 配音 + 时间轴（需要 kokoro、misaki[zh]、soundfile）
python src/music.py                           # 配乐 + 混音
node src/render.mjs                           # 逐帧截图到 build/frames
bash src/encode.sh                            # 合成 mp4
```

## 许可

- 配音模型：hexgrad/Kokoro-82M-v1.1-zh，Apache-2.0。
- 字体：Noto Sans SC、Noto Serif SC、Inter、IBM Plex Mono，均为 SIL OFL 1.1。
- 配乐：`src/music.py` 用 numpy 合成，没有使用任何外部素材。
