# 长平之战（前260年）— 视频号竖屏视频工程

1080×1920 / 30fps。全部画面由代码生成（Canvas + Playwright 逐帧截取），旁白为开源 TTS，音乐为程序合成。

## 目录
- `sources/` 史料原文（维基文库：《史记》卷43、73、81，《资治通鉴》卷5），写稿时逐条核对
- `script/script.py` 结构化旁白稿（唯一来源）；`script/旁白稿.md` 便于阅读的版本
- `build/fetch_dem.py` 下载公开高程数据（AWS Terrain Tiles）；`render_terrain.py` 渲染地形底图；`rivers.py` 由高程推算河流（含丹河主流）
- `build/assemble_audio.py` 拼接逐句旁白、变速、生成时间线；`build/music.py` 合成配乐并混音
- `build/make_data.py` 打包数据给渲染器；`render/` 渲染器（`core.js` 基础绘制，`scenes.js` 各段场景，`shoot.js` 截帧）
- `stills/` 审片静帧与动效预览；`audio/` 样音

## 重建
```
python3 build/fetch_dem.py && python3 build/render_terrain.py && python3 build/rivers.py && python3 build/rivers.py dan
python3 script/script.py                       # -> script/script.json
<tts-venv>/python build/assemble_audio.py <wav目录> 1.3   # -> audio/narration.wav, timeline.json
python3 build/music.py                         # -> audio/mix.wav
python3 build/make_data.py
cd render && node shoot.js still ../stills s4.5@0.9      # 单帧
cd render && node shoot.js frames ../out/part.mp4 0 900  # 帧区间
```
字体：Noto Serif SC / Noto Sans SC（SIL OFL 1.1），放在 `assets/fonts/`（未入库，见 OFL 文本）。
TTS：CosyVoice-300M-SFT「中文男」（Apache-2.0）。地形：AWS Terrain Tiles（SRTM 等公开数据）。河流：高程推算 + Natural Earth（公有领域）。
