# 64 · 贱岳之战（五个小时，五十二公里）

竖屏 1080×1920，25 fps，H.264 + AAC 128k。画面、地图动画、音效全部程序生成；旁白为托克维尔音色（Qwen3-TTS-12Hz-1.7B Base 克隆设计音色，Apache-2.0）；配乐为 Kevin MacLeod 曲目（CC BY 4.0，简介需署名）。

## 交付文件

| 文件 | 说明 |
| --- | --- |
| `贱岳之战_成片.mp4` | 成片（含淡配乐） |
| `贱岳之战_无配乐版.mp4` | 只有旁白与音效，备用 |
| `封面_1080x1920.png` / `封面_3x4_1080x1440.png` | 封面 |
| `发布包.md` | 标题三选一、一句话简介与话题、简介正文（含配乐署名）、发布设置提醒 |
| `史料核对.md` | 逐条史料依据、史料冲突、引文、地图来源 |
| `旁白稿.md` | 全片逐句旁白与时间码 |
| `sentences.json` / `sentences.txt` | 逐句旁白稿（如需在 box 上重配别的声音） |
| `narration.srt` | 字幕 |
| `stills/` | 抽帧检查图 |
| `src/` | 全部源码 |

## 制作流程（src/）

1. `script_data.py` 脚本数据 → `tts_clone.py` 逐句克隆配音（每句音高中位数需在 85–105 Hz，否则换 seed）→ `voice_post.py` 裁静音、限停顿、rubberband 变速、响度归一 → `asr_check.py` faster-whisper 回读比对拼音。
2. `timeline.py` 按实际句长排时间线与字幕。
3. `basemap.py` 生成晕渲底图（地形 Mapzen/AWS Terrain Tiles；水系提取自 OpenStreetMap 栅格图）；`gfx.py` / `film.py` 绘图与各场景；`render.py` 4 进程渲染。
4. `sfx.py` 合成音效；`audio.py` 旁白、音效、配乐三轨，配乐按旁白自动压低；`final_mux.py` 两遍 loudnorm 到 −15 LUFS / −1.5 dBTP，两遍 x264 压到 100 MB 内，核对音视频流时长差。
