# 67 渲染源码（换托克维尔音色后重渲染用）

全部画面程序绘制（PIL + numpy），底乐和音效 numpy 合成，没有外部素材。

## 依赖
- Python 3.11+：`pip install numpy pillow scipy pyloudnorm edge-tts fonttools brotli`
- ffmpeg
- 字体：Noto Serif CJK / Noto Sans CJK（`apt install fonts-noto-cjk`），马善政毛笔体全量版放在 `../fonts/MaShanZheng-full.ttf`（由 Google Fonts 的分片 woff2 合并而成，OFL）。

## 用托克维尔音色重出
1. 在 box 上按 `../sentences.json` 的 `tts_text` 逐句合成，得到 `line_0001.wav … line_0129.wav`，放进 `src/voice/`。
2. 重排时间轴、生成字幕和 -15 LUFS 旁白：`python tts.py voice`（有 wav 就不会再调 edge-tts）
3. 底乐和音效：`python music.py voice/timeline.json voice/narration.wav audio`
4. 画面：`python render.py voice/timeline.json video video_noaudio.mp4 4`
5. 混音和封装：见下方 mux 命令（与云扬版相同）。

```bash
ffmpeg -i video_noaudio.mp4 -i voice/narration.wav -i audio/music.wav -i audio/sfx.wav -filter_complex "[1:a]aformat=channel_layouts=stereo[v];[v][2:a][3:a]amix=inputs=3:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=11,aresample=async=1[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 128k -ar 48000 -shortest -movflags +faststart out.mp4
```
