# 34 成吉思汗西征花剌子模（历史的关键一局 · 战争）

微信视频号竖屏视频，1080×1920，25 fps，H.264 + AAC。**未发布、未上传。**

## 交付物

| 文件 | 说明 |
|---|---|
| `成片_一支商队被杀_配乐版.mp4` | 成片（含原创底乐） |
| `成片_一支商队被杀_无配乐版.mp4` | 备用：只有旁白和音效 |
| `封面.png` | 1080×1920 封面 |
| `发布包.md` | 标题、备选标题、简介、话题、声明项 |
| `旁白稿.md` | 成片旁白定稿（按章节） |
| `史料核对.md` | 每条史实、引文的出处与核对结论，及对简报的修正 |
| `sentences/sentences.json`、`sentences.txt` | 逐句旁白稿（可在 box 上重配音用） |
| `subtitles.srt` | 成片字幕（与配音按句对时） |
| `QA.md` | 时长、响度、音画同步、ASR 回读等自检结果 |
| `stills/` | 抽帧检查图 |
| `src/` | 全部生成代码（脚本数据、画面引擎、配乐、音效、混音） |

## 制作方式（全部程序生成，无第三方素材）

- **配音**：托克维尔音色。Qwen3-TTS-12Hz-1.7B-Base（Apache-2.0）用设计音色参考做 ICL 克隆，逐句合成，中位音高 85–105 Hz 门限；rubberband R3 变速（保共振峰）到约 255 字/分钟（含句间停顿）。参考音频取自 `claude/tocqueville-america-video-a250yg` 分支的 `voice_design_reference.m4a`（18 秒，与 VOICE_SPEC 所说 A0b 参考同一段）。
- **画面**：skia 程序绘制。地形底图用 AWS Terrain Tiles（Terrarium，公开数据）晕渲；河流、海岸用 Natural Earth（公共领域）；历史咸海按 1960 年前水位（DEM 53 m 等高线）示意。疆域、行军路线均为示意。
- **配乐**：原创。按章节程序作曲（D 小调，鼓、号角、弦乐、合唱铺底，开场与追击段最强，结尾收），用 FluidSynth + FluidR3_GM 音色库（MIT 许可）渲染。无需署名，可商用。
- **音效**：全部 numpy 合成（战鼓、号角、马蹄、风、驼铃、城门、水声）。开场声音钩子是战鼓三连 + 低音号角，无打字声、无提示音。
- **混音**：旁白 + 底乐（讲话时比人声低约 21 dB，停顿处抬 4 dB）+ 音效；两遍 loudnorm 到 -15 LUFS / 真峰值 -1.5 dBTP。

## 复现

```
python src/basemap.py            # 底图
python src/tts_clone.py --all    # 配音（CPU 约 2 小时）
TN=1.12 python src/voice_post.py a b c d e f g h i
python src/timeline.py
python src/music.py && python src/sfx.py
python src/mix.py voice && python src/mix.py mix
python src/render.py all 4
python src/mix.py mux out.mp4 1
```
