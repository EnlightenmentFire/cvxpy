# 龙场不是书斋顿悟

「思想与启蒙」第一集。1920×1080，30 帧/秒，H.264 + AAC。

| 文件 | 内容 |
|---|---|
| `龙场不是书斋顿悟.mp4` | 成片 |
| `01_史实清单.md` | 片中每一句史实的出处与原文，以及与流行说法不符之处 |
| `02_脚本与分镜.md` | 逐句的时间、画面、旁白、屏幕文字、出处标注（由程序从分镜数据生成，与成片一致） |
| `src/` | 全部制作脚本 |

## 素材与授权

全片没有使用任何外部图片、视频、音乐或人声采样。

| 部分 | 来源 | 授权 |
|---|---|---|
| 旁白 | CosyVoice2-0.5B 合成；音色参考片段由 Kokoro-82M-v1.1-zh 的预置男声生成 | 两个模型均为 Apache-2.0，可商用 |
| 配乐、音效 | `src/music.py` 逐个采样点合成（加法合成的和弦、模态合成的拨弦与磬、鼓、柴火声） | 自制 |
| 山、雾、竹、洞中火光 | `src/scenes.py` 程序生成 | 自制 |
| 地形 | Terrain Tiles（本区域为 SRTM，公有领域） | 开放数据，片尾署名 |
| 海岸线、河流 | Natural Earth | 公有领域 |
| 字体 | 思源宋体、思源黑体 | SIL OFL 1.1，可商用 |

旁白是 AI 合成语音，片尾已注明；发布时请在平台上勾选"内容由 AI 生成"的声明。

## 画面上的三种话

每一屏左上角都有标记：**史实**（附出处）、**理论**（署名 James C. Scott）、**解读**（我们自己的）。
地图只画山、海岸和大河，不画任何界线；路线、"赞米亚"的范围、低地上的细网都标了"示意"。

## 质量检查做了什么

- 配音逐句用语音识别回读，按拼音比对；全片混音后再整轨回读一次。
- 多音字（朝廷、重建、重新、长出来、够不着、贬为）另用基频走向和音素识别核对读音。
- 生僻字在送去合成时换成同音字（畲→奢、浰→利、椁→果、俟→寺），屏幕上仍是原字。
- 成片按每一句抽帧检查文字、地名位置、遮挡与转场；暗部放大检查色带。

## 重新生成

需要 Python 3.12、ffmpeg（带 libx264、librubberband）。字体放到 `<work>/fonts/`。

```bash
python src/fetch_map.py  <work>                 # 抓高程瓦片与 Natural Earth
python src/tts_run.py    <work>                 # 逐句合成旁白（需要 CosyVoice2 模型与参考音色）
python src/prep_narr.py  <work> 1.09            # 裁静音、统一响度、整体提速 9%
python src/make_timeline.py <work>              # 由配音时长生成时间线
python src/music.py      <work> <work>/timeline.json <work>/audio/music.wav
python src/mix.py        <work> <work>/timeline.json <work>/audio/music.wav <work>/audio/final_audio.wav
python src/render_all.py <work> <work>/timeline.json <work>/audio/final_audio.wav out.mp4
python src/docgen.py     <work>/timeline.json 02_脚本与分镜.md
```

改文字只需要动两个文件：`src/narration.py`（念什么）和 `src/storyboard.py`（屏幕上显示什么、出处怎么标、停多久）。
