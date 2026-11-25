# 66 小田原征伐与刀狩（从无名小卒到天下人 · 第 7 集 · 终章）

微信视频号竖屏视频，1080×1920，25 fps 恒定帧率，H.264 + AAC。**未发布、未上传。**

## 交付物

| 文件 | 说明 |
|---|---|
| `成片_配乐版.mp4` | 成片（旁白 + 原创底乐 + 音效），推荐 |
| `成片_无配乐版.mp4` | 备用：只有旁白和音效 |
| `封面_1080x1920.png`、`封面_3x4_1080x1440.png` | 封面 |
| `发布包.md` | 标题三选一、一句话简介与话题、长简介、声明项 |
| `旁白稿.md` | 成片旁白定稿（按章节，引文标原文与出处） |
| `史料核对.md` | 每条史实、引文的出处与核对结论，及对简报的处理 |
| `QA.md` | 时长、响度、音画同步、ASR 回读等自检结果 |
| `subtitles.srt` | 成片字幕（按句与配音对时） |
| `sentences/sentences.json`、`sentences.txt` | 逐句旁白稿（一行一句，可在 box 上重配音） |
| `stills/` | 开头 / 中段 / 结尾抽帧 |
| `src/` | 全部生成代码 |

## 制作方式（全部程序生成，无第三方素材）

- **配音**：托克维尔音色。Qwen3-TTS-12Hz-1.7B-Base（Apache-2.0）在云端 CPU 上用设计音色参考做 ICL 克隆，逐句合成，中位音高 85–105 Hz 门限；rubberband R3 变速（保共振峰）。参考音频取自 `claude/tocqueville-america-video-a250yg` 分支的 `voice_design_reference.m4a`（18 秒，即 VOICE_SPEC 所说 A0b 参考）。
- **画面**：skia 程序绘制。地形底图用 AWS Terrain Tiles（Terrarium，公开数据）晕渲，海岸线用 Natural Earth（公共领域）；北条领国、总构、行军与海路均为示意。剪影情景（一夜城、筑城、茶会、开城、刀狩、检地、大坂夜景）为情景演绎。
- **配乐**：原创，程序作曲，FluidSynth + FluidR3_GM 音色库（MIT 许可）渲染，可商用、无需署名。前半段太鼓、圆号、弦乐推进；石垣山段推到全片最强，开城一刻断成寂静；制度篇转古筝、尺八、低音弦乐；辞世处只留一支尺八。
- **音效**：全部 numpy 合成。开场声音钩子：巨木一棵接一棵断裂、倒下的回响，静一拍，一声太鼓；无打字声、无提示音。
- **混音**：旁白 + 底乐（讲话时比人声低约 21 dB，停顿处抬 4 dB）+ 音效；两遍 loudnorm 到 -15 LUFS / 真峰值 -1.5 dBTP；`aresample=async=1`。

## 复现（工作目录 /tmp/claude-0/work）

```
python src/basemap.py                 # 底图（需先下载 DEM 瓦片与 Natural Earth，见 basemap.py）
python src/tts_clone.py --all         # 配音（CPU 约 2 小时）
TN=1.15 python src/voice_post.py a b c d e f
python src/timeline.py
python src/music.py && python src/sfx.py
python src/mix.py voice && python src/mix.py mix
python src/render.py all 4
python src/mix.py mux 成片_配乐版.mp4 1 && python src/mix.py mux 成片_无配乐版.mp4 0
python src/cover.py 封面_1080x1920.png 封面_3x4_1080x1440.png
python src/export_text.py
```
