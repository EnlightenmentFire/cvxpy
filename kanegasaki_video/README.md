# 金崎撤退（1570）制作工程 · 从无名小卒到天下人 第2集

成片是微信视频号竖屏视频，1080×1920，25 fps。画面和音效都是程序生成的。配音用 Qwen3-TTS（Apache-2.0），以设计出来的「托克维尔」旁白音色为参考做克隆。配乐是 Kevin MacLeod 的曲子，授权 CC BY 4.0，发布时必须在简介里署名。

| 文件 | 作用 |
|---|---|
| `script_data.py` | 全片脚本（数据）：每句旁白的配音文字和字幕文字、画面键、引文卡（原文、出处、白话）、停顿 |
| `FACTCHECK.md` | 史料核对记录：brief 里的【待核】项逐条处理 |
| `PUBLISH.md` | 发布包：标题、一句话简介、简介、话题、配乐署名 |
| `tts_clone.py` | Qwen3-TTS Base 的 ICL 克隆，逐句合成；中位音高不在 85–105 Hz，或语速异常，就换 seed 重来 |
| `voice_post.py` | 去掉头尾静音，句内停顿压到 ≤0.32 秒，用 rubberband R3 做 1.12 倍变速，加 50 Hz 高通，响度统一 |
| `asr_check.py` | faster-whisper 回读，按无调拼音逐句比对 |
| `build_maps.py` | 用 AWS Terrain Tiles 渲染暗调晕渲地形，共三层：近畿北部到越前、敦贺湾、若狭到朽木谷。琵琶湖用 Natural Earth 的湖泊轮廓加平面检测 |
| `build_data.py` | 按实际配音时长生成时间线，输出 `render/data.js`、`narration.srt`、`sentences.json/txt` |
| `render/core.js`、`render/scenes.js` | Canvas 画面引擎和各场景：黄昏撤退长龙与孤城、本阵急报、钳形地图、决策门槛、殿军夜战（铁炮齐射、交替掩护、篝火疑兵）、朽木越、史料核对卡、高松城水淹预告 |
| `render/shoot.js` | 用 Playwright 逐帧截取画面，再交给 ffmpeg 编码 |
| `build_audio.py` | 旁白轨 + 合成音效（法螺、马蹄、铁炮齐射、太鼓、雨、火）+ 底乐，带闪避；说话时音乐比人声低约 22 dB |
| `final_render.sh` | 并行渲染 → 两遍 loudnorm 到 −15 LUFS / −1.5 dBTP → 两遍 x264 → 封装带配乐版和无配乐版 |

## 重做流程

```bash
python tts_clone.py && TEMPO=1.12 python voice_post.py && python asr_check.py
TEMPO=1.12 python build_data.py && python build_audio.py && ./final_render.sh
```
