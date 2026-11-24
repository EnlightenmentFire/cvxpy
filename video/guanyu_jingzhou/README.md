# 关羽失荆州：麋芳为什么开城（竖屏纪录短片）

微信视频号竖屏视频，1080×1920 / 30fps / H.264 + AAC，成片 7 分 31 秒、约 92MB。全部画面由代码渲染，旁白为开源 TTS 合成，音乐鼓点为程序合成。

- `旁白稿.md`：逐段旁白 + 每条引文的出处与层级（正史／裴注／通鉴／后人论说／解读）
- `史实核对.md`：对提纲所做的按原文修正、解读的边界、素材许可
- `stills/`：关键静帧
- `src/`：渲染代码
  - `script.py` 旁白稿（数据源） · `timeline.py` 时间轴与字幕分块 · `scenes.py` 分镜 · `gfx.py` 图元 · `geo.py` 投影与底图 · `data.py` 地理数据
  - `basemap.py` 高程 → 晕渲底图 · `flood_pre.py` 樊城一带淹没高度预计算
  - `audio.py` 旁白拼接 + 鼓/垫音合成 + 闪避混音 · `render.py` 分段并行渲染 · `encode.sh` 两遍编码
- `tts/design.py` 设计参考音色 · `tts/gen2.py` 以参考音克隆合成并逐段卡音高（Qwen3-TTS，Apache-2.0） · `tts/compact.py` 压缩过长停顿 · `tts/qc.py` 回听质检与字幕对齐（`tts/gen.py` 为已弃用的第一版）
- `dem/dl.py`、`dem/mosaic.py` 地形瓦片下载与拼接

## 重新生成

```bash
pip install skia-python soundfile scipy pillow numpy qwen-tts faster-whisper pypinyin
apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra libegl1 ffmpeg
# 代码里的工作目录是 /home/user/work/{vid,tts,dem}
python3 dem/dl.py && python3 dem/mosaic.py          # 地形
python3 src/basemap.py && python3 src/flood_pre.py  # 底图
python3 tts/gen.py && python3 tts/qc.py             # 配音 + 质检/对齐
python3 src/audio.py                                # 混音
python3 src/render.py 4 && bash src/encode.sh out.mp4
```

成片 mp4 体积较大，未入库。
