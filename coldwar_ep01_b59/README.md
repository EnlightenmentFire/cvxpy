# 冷战核按钮 · 第一期《海底那一夜》

微信视频号竖屏片（1080×1920 · 30fps · H.264 · < 100MB）。

## 当前状态：风格确认阶段
- `docs/script.md` 旁白稿 v1（约 2700 字，预计 9.5–10 分钟）
- `docs/factcheck.md` 20 条史料逐条核对表（已对上原文 / 有出入 / 说法不一）
- `stills/` 8 张关键静帧 + `00_contact_sheet.jpg` 总览
- `audio/` 4 个候选男声 20 秒样音 + 1 版带配乐的混音示范

确认风格和声音后再渲染全片。

## 管线
- `src/engine.py` 合成引擎（float32 画布、辉光、字体、胶片质感、「假想」标记、字幕安全区）
- `src/globe.py` 三维地球：Natural Earth 海岸线 + 城市光点；**不加载任何国界数据，东经 62° 以东整体剔除**
- `src/scenes.py` 各场景（真实段冷蓝/琥珀，假想段洋红热成像）
- `src/stills.py` 出静帧：`python3 src/stills.py`
- `src/tts_kokoro.py` 配音（Kokoro-82M v1.1-zh，需 Python 3.12 venv：`kokoro==0.9.4`、`misaki[zh]==0.9.4`）
- `src/sound.py` 配乐与音效，全部程序合成
- `src/fetch_assets.sh` 重新下载地图数据和档案照片

## 素材与许可
| 素材 | 来源 | 许可 |
|---|---|---|
| U-2 侦察照片 | NARA 193926（经 Wikimedia Commons） | 美国政府作品，公有领域 |
| B-59 照片 | NARA RG 428（428-N-711199/200/201），约 1962.10.28–29 | 美国政府作品，公有领域 |
| 海岸线 / 城市 | Natural Earth | 公有领域 |
| 配音模型 | hexgrad/Kokoro-82M-v1.1-zh | Apache-2.0 |
| 字体 | Noto Sans CJK SC、JetBrains Mono | SIL OFL 1.1 |
| 配乐音效 | 本项目代码合成 | — |
